# Standard library
import re
import textwrap

# Third-party
from bs4 import BeautifulSoup, NavigableString, Tag
from bs4.element import Comment

PLAIN_TEXT_LINE_LENGTH = 70
PLAIN_TEXT_SEPARATOR = "=" * PLAIN_TEXT_LINE_LENGTH
LIST_INDENT = 5
LIST_MARKER_WIDTH = 3

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


class PlainTextRenderError(ValueError):
    pass


def legal_code_html_to_plain_text(html):
    """
    Convert rendered legalcode document/body HTML to plain text.

    The converter is legalcode-focused. It uses the same document regions that
    HTML/CSS use for visual separation, and it renders ordered-list markers
    explicitly because plain text has no list semantics.
    """
    soup = BeautifulSoup(html, "lxml")
    legal_code_document = soup.find(id="legal-code-document")
    legal_code_body = soup.find(id="legal-code-body")
    root = legal_code_document or legal_code_body or soup.body or soup
    if legal_code_document:
        plain_text = _render_document(root).strip("\n")
    else:
        plain_text = _render_block(root).strip("\n")
    if not plain_text:
        return ""
    return f"{plain_text}\n"


def _render_document(document):
    sections = []
    current_region = None
    current_chunks = []

    def flush_region():
        nonlocal current_region, current_chunks
        rendered = "\n\n".join(chunk for chunk in current_chunks if chunk)
        if rendered:
            sections.append(rendered)
        current_region = None
        current_chunks = []

    for child in document.children:
        if _is_ignorable(child):
            continue
        region = _document_region(child)
        rendered = _render_block(child).strip("\n")
        if not rendered.strip():
            continue
        if current_region is not None and region != current_region:
            flush_region()
        current_region = region
        current_chunks.append(rendered)
    flush_region()
    return f"\n\n{PLAIN_TEXT_SEPARATOR}\n\n".join(sections)


def _document_region(node):
    if isinstance(node, Tag):
        tag_name = node.name.lower()
        if tag_name == "h1":
            return "title"
        if _has_class(node, "notice-top"):
            return "preface"
        if node.get("id") == "legal-code-body":
            return "body"
        if _has_class(node, "notice-bottom"):
            return "footer"
    return "other"


def _render_block(node, indent=0):
    if _is_ignorable(node):
        return ""
    if isinstance(node, NavigableString):
        return _wrap_text(_clean_inline(str(node)), indent=indent)
    if not isinstance(node, Tag):
        return ""

    tag_name = node.name.lower()
    if tag_name in {"script", "style", "hr"}:
        return ""
    if tag_name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        return _wrap_text(_render_inline_children(node), indent=indent)
    if tag_name == "p":
        return _wrap_text(_render_inline_children(node), indent=indent)
    if tag_name in {"ol", "ul"}:
        return _render_list(node, indent=indent)
    if _has_direct_block_child(node):
        return _render_block_children(node, indent=indent)
    return _wrap_text(_render_inline_children(node), indent=indent)


def _render_block_children(node, indent=0):
    chunks = []
    for child in node.children:
        rendered = _render_block(child, indent=indent).strip("\n")
        if rendered.strip():
            chunks.append(rendered)
    return "\n\n".join(chunks)


def _render_list(list_tag, indent=0):
    rendered_items = []
    list_items = _direct_children(list_tag, "li")
    start = _get_start(list_tag, len(list_items))
    for offset, list_item in enumerate(list_items):
        number = start - offset if _is_reversed(list_tag) else start + offset
        marker = _get_list_marker(list_tag, number)
        prefix = f"{' ' * indent}{_format_marker(marker)}"
        content_indent = max(indent + LIST_INDENT, len(prefix))
        chunks = _render_list_item_chunks(list_item, content_indent)
        if not chunks:
            rendered_items.append(prefix.rstrip())
        else:
            rendered_items.append(
                "\n".join(_render_list_item(prefix, content_indent, chunks))
            )
    separator = "\n\n" if list_tag.name.lower() == "ol" else "\n"
    return separator.join(rendered_items)


def _render_list_item(prefix, content_indent, chunks):
    lines = []
    for index, (kind, content) in enumerate(chunks):
        if kind == "text":
            if index == 0:
                rendered = _wrap_text(
                    content,
                    initial_indent=prefix,
                    subsequent_indent=" " * content_indent,
                )
            else:
                rendered = _wrap_text(content, indent=content_indent)
            lines.extend(rendered.splitlines())
        else:
            if index == 0:
                lines.append(prefix.rstrip())
            lines.extend(content.splitlines())
    return lines


def _render_list_item_chunks(list_item, content_indent):
    chunks = []
    inline_nodes = []

    def flush_inline_nodes():
        if not inline_nodes:
            return
        content = _render_inline_nodes(inline_nodes)
        inline_nodes.clear()
        if content:
            chunks.append(("text", content))

    for child in list_item.children:
        if _is_ignorable(child):
            continue
        if isinstance(child, Tag) and child.name.lower() in {"ol", "ul"}:
            flush_inline_nodes()
            rendered = _render_list(child, indent=content_indent).strip("\n")
            if rendered.strip():
                chunks.append(("block", rendered))
        elif isinstance(child, Tag) and child.name.lower() in BLOCK_TAGS:
            flush_inline_nodes()
            if child.name.lower() == "p" and not _has_direct_block_child(
                child
            ):
                rendered = _render_inline_children(child)
                if rendered:
                    chunks.append(("text", rendered))
            else:
                rendered = _render_block(
                    child, indent=content_indent
                ).strip("\n")
                if rendered.strip():
                    chunks.append(("block", rendered))
        else:
            inline_nodes.append(child)
    flush_inline_nodes()
    return chunks


def _format_marker(marker):
    if len(marker) <= LIST_MARKER_WIDTH:
        marker = marker.rjust(LIST_MARKER_WIDTH)
    return f"{marker}. "


def _get_start(list_tag, list_length):
    if _is_reversed(list_tag):
        default = list_length
    else:
        default = 1
    try:
        return int(list_tag.get("start", default))
    except ValueError:
        return default


def _is_reversed(list_tag):
    return list_tag.name.lower() == "ol" and list_tag.has_attr("reversed")


def _get_list_marker(list_tag, number):
    if list_tag.name.lower() == "ul":
        return "-"

    list_type = list_tag.get("type", "1")
    if list_type in {"1", ""}:
        return str(number)
    if list_type == "a":
        return _alpha(number).lower()
    if list_type == "A":
        return _alpha(number).upper()
    if list_type == "i":
        return _roman(number).lower()
    if list_type == "I":
        return _roman(number).upper()
    return str(number)


def _alpha(number):
    if number < 1:
        raise PlainTextRenderError(
            f"Alpha list marker requires positive number: {number}"
        )
    chars = []
    while number > 0:
        number -= 1
        number, remainder = divmod(number, 26)
        chars.append(chr(ord("a") + remainder))
    return "".join(reversed(chars))


def _roman(number):
    if number < 1:
        raise PlainTextRenderError(
            f"Roman list marker requires positive number: {number}"
        )
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


def _render_inline_nodes(nodes):
    return _clean_inline("".join(_render_inline(node) for node in nodes))


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

    if tag_name == "a":
        href = node.get("href")
        if href and not href.startswith("#"):
            if content[-1] in ".!?":
                return f"{content} {href}"
            return f"{content}: {href}"
        return content
    return content


def _render_inline_children(node):
    return _render_inline_nodes(node.children)


def _wrap_text(
    value,
    indent=0,
    initial_indent=None,
    subsequent_indent=None,
):
    if not value:
        return ""
    if initial_indent is None:
        initial_indent = " " * indent
    if subsequent_indent is None:
        subsequent_indent = " " * indent
    return textwrap.fill(
        value,
        width=PLAIN_TEXT_LINE_LENGTH,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
        break_long_words=False,
        break_on_hyphens=False,
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


def _has_class(node, class_name):
    return class_name in node.get("class", [])


def _is_ignorable(node):
    if isinstance(node, Comment):
        return True
    if isinstance(node, NavigableString):
        return not str(node).strip()
    return False
