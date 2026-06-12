from __future__ import annotations

from html import escape
from typing import Any

from .config import PublicSiteConfig


def render_initial_page(config: PublicSiteConfig, page: dict[str, Any]) -> str:
    site_title = str(config.site.get("title", "dotlineform"))
    page_title = str(page.get("title", site_title))
    body_class = str(page.get("body_class", "page"))
    heading = str(page.get("heading", page_title))
    message = str(page.get("message", ""))
    link_href = str(page.get("link_href", "/"))
    link_label = str(page.get("link_label", "home"))

    document_title = site_title if page_title == site_title else f"{page_title} | {site_title}"
    return "\n".join(
        (
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>{escape(document_title)}</title>",
            '  <link rel="icon" href="/favicon.ico" sizes="any">',
            '  <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">',
            '  <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">',
            '  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">',
            '  <link rel="manifest" href="/site.webmanifest">',
            '  <link rel="mask-icon" href="/safari-pinned-tab.svg" color="#111111">',
            "</head>",
            f'<body class="{escape(body_class, quote=True)}">',
            "  <main class=\"page page--error\">",
            f"    <h1>{escape(heading)}</h1>",
            f"    <p>{escape(message)}</p>",
            f'    <p><a href="{escape(link_href, quote=True)}">{escape(link_label)}</a></p>',
            "  </main>",
            "</body>",
            "</html>",
            "",
        )
    )
