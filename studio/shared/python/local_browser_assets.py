"""Shared browser icon contract for local app shells and servers."""

from __future__ import annotations


LOCAL_BROWSER_ASSET_PATHS = frozenset(
    {
        "/favicon.ico",
        "/favicon-16x16.png",
        "/favicon-32x32.png",
        "/apple-touch-icon.png",
        "/apple-touch-icon-precomposed.png",
        "/safari-pinned-tab.svg",
        "/site.webmanifest",
    }
)

LOCAL_BROWSER_ICON_LINKS_TOKEN = "__LOCAL_BROWSER_ICON_LINKS__"
LOCAL_BROWSER_ICON_LINKS = """\
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <link rel="manifest" href="/site.webmanifest">
  <link rel="mask-icon" href="/safari-pinned-tab.svg" color="#111111">"""


def render_local_browser_icon_links(shell: str) -> str:
    """Replace the one local-shell icon token with the shared declarations."""
    token_count = shell.count(LOCAL_BROWSER_ICON_LINKS_TOKEN)
    if token_count != 1:
        raise ValueError(
            f"Local app shell must contain {LOCAL_BROWSER_ICON_LINKS_TOKEN} exactly once; "
            f"found {token_count}"
        )
    return shell.replace(LOCAL_BROWSER_ICON_LINKS_TOKEN, LOCAL_BROWSER_ICON_LINKS)
