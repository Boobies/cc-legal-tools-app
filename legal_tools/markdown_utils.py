# Standard library
import re

# Third-party
from bs4 import BeautifulSoup, NavigableString, Tag
from bs4.element import Comment

BLOCK_TAGS = {
    "article",
    "blockquote",
    "div",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "ol",
    "p",
    "section",
    "ul",
}


def legal_code_html_to_markdown(html):
    """
    Convert rendered legalcode body HTML to Markdown.

    The converter is intentionally small and legalcode-focused. It preserves
    browser-rendered ordered-list markers such as a/A/i as explicit text
    because Markdown ordered lists only standardize decimal markers.
    """
    soup = BeautifulSoup(html, "lxml")
    legal_code_body = soup.find(id="legal-code-body")
    root = legal_code_body or soup.body or soup
    markdown = _render_block(root).strip()
    if not markdown:
        return ""
    return f"{markdown}\n"


def _render_block(node):
    if _is_ignorable(node):
        return ""
    if isinstance(node, NavigableString):
        return _clean_inline(str(node))
    if not isinstance(node, Tag):
        return ""

    tag_name = node.name.lower()
    if tag_name in {"script", "style"}:
        return ""
    if tag_name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(tag_name[1])
        content = _render_inline_children(node)
        if content:
            return f"{'#' * level} {content}"
        return ""
    if tag_name == "p":
        return _render_inline_children(node)
    if tag_name == "ol" or tag_name == "ul":
        return _render_list(node)
    if _has_direct_block_child(node):
        return _render_block_children(node)
    return _render_inline_children(node)


def _render_block_children(node):
    chunks = []
    for child in node.children:
        rendered = _render_block(child).strip()
        if rendered:
            chunks.append(rendered)
    return "\n\n".join(chunks)


def _render_list(list_tag, indent=0, force_separate_items=False):
    lines = []
    start = _get_start(list_tag)
    list_items = _direct_children(list_tag, "li")
    separate_items = (
        force_separate_items or _uses_explicit_ordered_markers(list_tag)
    )
    for offset, list_item in enumerate(list_items):
        number = start + offset
        marker = _get_list_marker(list_tag, number)
        content = _render_list_item(list_item).strip()
        prefix = _get_indent(indent)
        if not content:
            lines.append(f"{prefix}{marker}")
        else:
            content_lines = content.splitlines()
            lines.append(f"{prefix}{marker} {content_lines[0].strip()}")
            continuation_prefix = _get_indent(indent + 4)
            for line in content_lines[1:]:
                if line.strip():
                    lines.append(f"{continuation_prefix}{line}")
                else:
                    lines.append("")

        if separate_items and offset < len(list_items) - 1:
            lines.append("")
    return "\n".join(lines)


def _get_indent(indent):
    if not indent:
        return ""
    return "&nbsp;" * indent


def _render_list_item(list_item):
    chunks = []
    inline_nodes = []

    def flush_inline_nodes():
        if not inline_nodes:
            return
        content = _clean_inline(
            "".join(_render_inline(n) for n in inline_nodes)
        )
        inline_nodes.clear()
        if content:
            chunks.append(content)

    for child in list_item.children:
        if _is_ignorable(child):
            continue
        if isinstance(child, Tag) and child.name.lower() in {"ol", "ul"}:
            flush_inline_nodes()
            rendered = _render_list(
                child, force_separate_items=True
            ).strip()
            if rendered:
                chunks.append(rendered)
        elif isinstance(child, Tag) and child.name.lower() in BLOCK_TAGS:
            flush_inline_nodes()
            rendered = _render_block(child).strip()
            if rendered:
                chunks.append(rendered)
        else:
            inline_nodes.append(child)
    flush_inline_nodes()
    return "\n\n".join(chunks)


def _render_inline(node):
    if _is_ignorable(node):
        return ""
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""

    tag_name = node.name.lower()
    if tag_name == "br":
        return "\n"

    content = _render_inline_children(node)
    if not content:
        return ""

    if tag_name in {"b", "strong"}:
        return f"**{content}**"
    if tag_name in {"em", "i"}:
        return f"*{content}*"
    if tag_name == "code":
        return f"`{content}`"
    if tag_name == "a":
        href = node.get("href")
        if href:
            return f"[{content}]({href})"
        return content
    if tag_name == "u" or _is_underline_span(node):
        return f"<u>{content}</u>"
    if tag_name in {"sub", "sup"}:
        return f"<{tag_name}>{content}</{tag_name}>"
    return content


def _render_inline_children(node):
    return _clean_inline(
        "".join(_render_inline(child) for child in node.children)
    )


def _clean_inline(value):
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+([,.;:!?%)\]])", r"\1", value)
    value = re.sub(r"([(\[])\s+", r"\1", value)
    return value.strip()


def _has_direct_block_child(node):
    return any(
        isinstance(child, Tag) and child.name.lower() in BLOCK_TAGS
        for child in node.children
    )


def _direct_children(node, tag_name):
    return [
        child
        for child in node.children
        if isinstance(child, Tag) and child.name.lower() == tag_name
    ]


def _get_start(list_tag):
    try:
        return int(list_tag.get("start", 1))
    except ValueError:
        return 1


def _uses_explicit_ordered_markers(list_tag):
    if list_tag.name.lower() != "ol":
        return False
    return list_tag.get("type") in {"a", "A", "i", "I"}


def _get_list_marker(list_tag, number):
    if list_tag.name.lower() == "ul":
        return "-"

    list_type = list_tag.get("type", "1")
    if list_type in {"1", ""}:
        return f"{number}."
    if list_type == "a":
        return f"({_alpha(number).lower()})"
    if list_type == "A":
        return f"({_alpha(number).upper()})"
    if list_type == "i":
        return f"({_roman(number).lower()})"
    if list_type == "I":
        return f"({_roman(number).upper()})"
    return f"{number}."


def _alpha(number):
    chars = []
    while number > 0:
        number -= 1
        number, remainder = divmod(number, 26)
        chars.append(chr(ord("a") + remainder))
    return "".join(reversed(chars))


def _roman(number):
    numerals = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    result = []
    for value, symbol in numerals:
        while number >= value:
            result.append(symbol)
            number -= value
    return "".join(result)


def _is_underline_span(node):
    if node.name.lower() != "span":
        return False
    style = node.get("style", "").lower().replace(" ", "")
    return "text-decoration:underline" in style


def _is_ignorable(node):
    if isinstance(node, Comment):
        return True
    if isinstance(node, NavigableString):
        return not str(node).strip()
    return False
