from __future__ import annotations

from .config import PublicSiteConfig
from .render import docs_viewer_shell, render_page, stylesheet_tag


def render_docs_route(
    config: PublicSiteConfig,
    *,
    title: str,
    section: str,
    path: str,
    route_id: str,
    search_placeholder: str,
    search_aria_label: str,
) -> str:
    return render_page(
        config,
        title=title,
        section=section,
        path=path,
        extra_head=(stylesheet_tag(config.docs_viewer["stylesheet"], config),),
        body=docs_viewer_shell(
            config,
            route_id=route_id,
            search_placeholder=search_placeholder,
            search_aria_label=search_aria_label,
        ),
    )
