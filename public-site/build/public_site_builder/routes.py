from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalogue_routes import (
    render_catalogue_search,
    render_moments,
    render_recent,
    render_series,
    render_work_details,
    render_works,
)
from .config import PublicSiteConfig
from .docs_routes import render_docs_route
from .static_routes import render_404, render_about, render_home_redirect


def render_routes(repo_root: Path, config: PublicSiteConfig) -> dict[str, str]:
    pipeline = _load_pipeline(repo_root)
    return {
        "index.html": render_home_redirect(config),
        "about/index.html": render_about(config),
        "recent/index.html": render_recent(config, pipeline),
        "series/index.html": render_series(config, pipeline),
        "works/index.html": render_works(config, pipeline),
        "work-details/index.html": render_work_details(config, pipeline),
        "moments/index.html": render_moments(config, pipeline),
        "catalogue/search/index.html": render_catalogue_search(config),
        "library/index.html": render_docs_route(
            config,
            title="Library",
            section="library",
            path="/library/",
            route_id="library",
            search_placeholder="search library",
            search_aria_label="Search library",
        ),
        "analysis/index.html": render_docs_route(
            config,
            title="Analysis",
            section="analysis",
            path="/analysis/",
            route_id="analysis",
            search_placeholder="search analysis",
            search_aria_label="Search analysis",
        ),
        "404.html": render_404(config),
    }


def _load_pipeline(repo_root: Path) -> dict[str, Any]:
    return json.loads((repo_root / "_data" / "pipeline.json").read_text(encoding="utf-8"))
