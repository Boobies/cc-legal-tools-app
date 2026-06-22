# Standard library
import re
from urllib.parse import urlsplit

LEGAL_CODE_LINK_BASE_URL = "https://creativecommons.org"

_DOMAIN_LIKE_URL_RE = re.compile(
    r"^[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?::\d+)?(?=[/?#]|$)"
)


def absolute_link_url(href, base_url=LEGAL_CODE_LINK_BASE_URL):
    href = (href or "").strip()
    if not href or href.startswith("#"):
        return href
    if href.startswith("//"):
        return f"{_base_scheme(base_url)}:{href}"
    if _DOMAIN_LIKE_URL_RE.match(href):
        return f"{_base_scheme(base_url)}://{href}"

    parts = urlsplit(href)
    if parts.scheme:
        return href
    if href.startswith("/"):
        return f"{_base_origin(base_url)}{href}"
    return f"{_base_origin(base_url)}/{href}"


def _base_scheme(base_url):
    return urlsplit(base_url).scheme or "https"


def _base_origin(base_url):
    parts = urlsplit(base_url)
    return f"{parts.scheme}://{parts.netloc}"
