# Standard library
import re
import textwrap
from html import escape

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
MARKDOWN_LINE_LENGTH = 70


def legal_code_html_to_markdown(html):
    """
    Convert rendered legalcode document/body HTML to Markdown.

    The converter is intentionally small and legalcode-focused. It emits lists
    as raw HTML blocks so CommonMark preserves ordered-list semantics such as
    alpha and roman markers without us recreating list numbering.
    """
    soup = BeautifulSoup(html, "lxml")
    legal_code_document = soup.find(id="legal-code-document")
    legal_code_body = soup.find(id="legal-code-body")
    root = legal_code_document or legal_code_body or soup.body or soup
    markdown = _render_block(root).strip()
    if not markdown:
        return ""
    return f"{markdown}\n"


def _render_block(node):
    if _is_ignorable(node):
        return ""
    if isinstance(node, NavigableString):
        return _wrap_markdown_text(_clean_inline(str(node)))
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
        return _wrap_markdown_text(_render_inline_children(node))
    if tag_name == "ol" or tag_name == "ul":
        return _render_list(node)
    if _has_direct_block_child(node):
        return _render_block_children(node)
    return _wrap_markdown_text(_render_inline_children(node))


def _render_block_children(node):
    chunks = []
    for child in node.children:
        rendered = _render_block(child).strip()
        if rendered:
            chunks.append(rendered)
    return "\n\n".join(chunks)


def _render_list(list_tag):
    tag_name = list_tag.name.lower()
    attrs = _render_list_attrs(list_tag)
    lines = [f"<{tag_name}{attrs}>"]
    for list_item in _direct_children(list_tag, "li"):
        content = _render_html_list_item(list_item)
        if not content:
            lines.append("<li></li>")
        elif "\n" in content or len(f"<li>{content}</li>") > (
            MARKDOWN_LINE_LENGTH
        ):
            lines.append("<li>")
            lines.extend(content.splitlines())
            lines.append("</li>")
        else:
            lines.append(f"<li>{content}</li>")
    lines.append(f"</{tag_name}>")
    return "\n".join(lines)


def _render_list_attrs(list_tag):
    allowed_attrs = {
        "ol": ("type", "start", "reversed"),
        "ul": ("type",),
    }
    attrs = []
    for attr in allowed_attrs[list_tag.name.lower()]:
        if attr not in list_tag.attrs:
            continue
        value = list_tag.get(attr)
        if attr == "reversed":
            attrs.append(attr)
        else:
            attrs.append(f'{attr}="{escape(str(value), quote=True)}"')
    if not attrs:
        return ""
    return f" {' '.join(attrs)}"


def _render_html_list_item(list_item):
    chunks = []
    inline_nodes = []

    def flush_inline_nodes():
        if not inline_nodes:
            return
        content = _render_html_inline_nodes(inline_nodes)
        inline_nodes.clear()
        if content:
            chunks.append(_wrap_html_text(content))

    for child in list_item.children:
        if _is_ignorable(child):
            continue
        if isinstance(child, Tag) and child.name.lower() in {"ol", "ul"}:
            flush_inline_nodes()
            rendered = _render_list(child).strip()
            if rendered:
                chunks.append(rendered)
        elif isinstance(child, Tag) and child.name.lower() in BLOCK_TAGS:
            flush_inline_nodes()
            rendered = _render_html_block(child).strip()
            if rendered:
                chunks.append(rendered)
        else:
            inline_nodes.append(child)
    flush_inline_nodes()
    return "\n".join(chunks)


def _render_html_block(node):
    if _is_ignorable(node):
        return ""
    if isinstance(node, NavigableString):
        return _wrap_html_text(escape(_clean_inline(str(node)), quote=False))
    if not isinstance(node, Tag):
        return ""

    tag_name = node.name.lower()
    if tag_name in {"script", "style"}:
        return ""
    if tag_name in {"ol", "ul"}:
        return _render_list(node)
    if tag_name == "li":
        return _render_html_list_item(node)

    if _has_direct_block_child(node):
        content = "\n".join(
            rendered
            for child in node.children
            if (rendered := _render_html_block(child).strip())
        )
    else:
        content = _wrap_html_text(_render_html_inline_children(node))
    return _wrap_html_tag(tag_name, content)


def _wrap_html_tag(tag_name, content):
    tag_content = f"<{tag_name}>{content}</{tag_name}>"
    if "\n" in content or len(tag_content) > MARKDOWN_LINE_LENGTH:
        return f"<{tag_name}>\n{content}\n</{tag_name}>"
    return tag_content


def _render_html_inline_nodes(nodes):
    return _clean_inline("".join(_render_html_inline(node) for node in nodes))


def _render_html_inline(node):
    if _is_ignorable(node):
        return ""
    if isinstance(node, NavigableString):
        return escape(str(node), quote=False)
    if not isinstance(node, Tag):
        return ""

    tag_name = node.name.lower()
    if tag_name == "br":
        return "<br>"

    content = _render_html_inline_children(node)
    if not content:
        return ""

    if tag_name in {"b", "strong"}:
        return f"<strong>{content}</strong>"
    if tag_name in {"em", "i"}:
        return f"<em>{content}</em>"
    if tag_name == "code":
        return f"<code>{content}</code>"
    if tag_name == "a":
        href = node.get("href")
        if href:
            href = escape(href, quote=True)
            return f'<a href="{href}">{content}</a>'
        return content
    if tag_name == "u" or _is_underline_span(node):
        return f"<u>{content}</u>"
    if tag_name in {"sub", "sup"}:
        return f"<{tag_name}>{content}</{tag_name}>"
    return content


def _render_html_inline_children(node):
    return _render_html_inline_nodes(node.children)


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


def _wrap_markdown_text(value):
    return _wrap_text(value)


def _wrap_html_text(value):
    return _wrap_text(value)


def _wrap_text(value):
    return textwrap.fill(
        value,
        width=MARKDOWN_LINE_LENGTH,
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
