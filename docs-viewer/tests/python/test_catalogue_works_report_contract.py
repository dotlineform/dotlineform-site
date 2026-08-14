#!/usr/bin/env python3
"""Focused registry, host, input, public-boundary, and route-retirement checks for Catalogue Works."""

from __future__ import annotations

import json
from pathlib import Path

from studio.shared.python import local_env


REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_DOC_ID = "d-20260401-000000-ebf14a"
REPORT_DOC_ID = "d-20260810-222148-99daec"


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def dotlineform_scope_root() -> Path:
    projects_base = Path(
        local_env.runtime_env(repo_root=REPO_ROOT)["DOTLINEFORM_PROJECTS_BASE_DIR"]
    )
    assert projects_base.is_absolute()
    return projects_base / "docs-viewer/scopes/dotlineform"


def test_manage_registry_and_loader_own_one_local_catalogue_works_report() -> None:
    payload = read_json(REPO_ROOT / "docs-viewer/config/reports/reports.json")
    records = {
        str(record.get("report_id") or ""): record
        for record in payload["reports"]
        if isinstance(record, dict)
    }

    assert records["catalogue_works"] == {
        "report_id": "catalogue_works",
        "title": "Catalogue Works",
        "description": (
            "Searches every published canonical Work with exact Series and "
            "storage context."
        ),
        "default_access": "local",
        "loader_id": "catalogue_works",
        "presets": [],
    }

    loader_source = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/docs-viewer-reports.js"
    ).read_text(encoding="utf-8")
    assert loader_source.count('import("./catalogue-works-report.js")') == 1
    assert loader_source.count("return module.mountCatalogueWorksReport;") == 1
    assert (
        REPO_ROOT / "docs-viewer/runtime/js/reports/catalogue-works-report.js"
    ).is_file()


def test_module_uses_only_existing_studio_inputs_and_exact_catalogue_targets() -> None:
    source = (
        REPO_ROOT / "docs-viewer/runtime/js/reports/catalogue-works-report.js"
    ).read_text(encoding="utf-8")

    for fragment in (
        'studioReadUrl(context, "catalogue_works")',
        'studioReadUrl(context, "catalogue_series")',
        "value.storage_location",
        "value.medium_type",
        "value.medium_caption",
        'visibility: "expanded"',
        'kind: "semantic-table"',
        'const path = kind === "work" ? "/works/" : "/series/";',
    ):
        assert fragment in source
    for forbidden in (
        "works_index.json",
        "/assets/data/series_index",
        "site/assets/data",
        "catalogue_lookup_work_search",
        "docsViewerReportService",
    ):
        assert forbidden not in source

    local_css = (
        REPO_ROOT / "docs-viewer/static/css/docs-viewer-local-reports.css"
    ).read_text(encoding="utf-8")
    assert '[data-report-column-visibility="expanded"]' in local_css
    assert (
        ".docsViewerReport__expandedViewport .catalogueWorksReport__table "
        '[data-report-column-visibility="expanded"]'
    ) in local_css


def test_exact_dotlineform_report_host_projects_one_inert_host() -> None:
    studio_source = (
        REPO_ROOT
        / f"docs-viewer/scopes/studio/source/documents/{STUDIO_DOC_ID}.md"
    ).read_text(encoding="utf-8")
    studio_payload = read_json(
        REPO_ROOT
        / f"docs-viewer/scopes/studio/published/documents/by-id/{STUDIO_DOC_ID}.json"
    )
    scope_root = dotlineform_scope_root()
    source = (scope_root / f"source/documents/{REPORT_DOC_ID}.md").read_text(
        encoding="utf-8"
    )
    payload = read_json(
        scope_root / f"published/documents/by-id/{REPORT_DOC_ID}.json"
    )

    assert ":::report" not in studio_source
    assert "data-docs-viewer-report-host" not in str(studio_payload["content_html"])
    assert (
        f"/docs/?scope=dotlineform&doc={REPORT_DOC_ID}" in studio_source
    )
    assert source.count(":::report\nid: catalogue_works\naccess: local\n:::") == 1
    assert payload["report"] == {
        "id": "catalogue_works",
        "access": "local",
        "scope": None,
        "preset": None,
        "sub_scope": None,
    }
    assert str(payload["content_html"]).count("data-docs-viewer-report-host") == 1


def test_public_registry_loader_and_data_do_not_expose_catalogue_works() -> None:
    public_registry = read_json(REPO_ROOT / "site/assets/data/docs/public-reports.json")
    public_report_ids = {
        str(record.get("report_id") or "")
        for record in public_registry["reports"]
        if isinstance(record, dict)
    }
    public_loader = (
        REPO_ROOT / "site/docs-viewer/runtime/js/reports/docs-viewer-public-reports.js"
    ).read_text(encoding="utf-8")
    public_css = (
        REPO_ROOT / "site/docs-viewer/static/css/docs-viewer-reports.css"
    ).read_text(encoding="utf-8")

    assert "catalogue_works" not in public_report_ids
    assert "catalogue-works-report.js" not in public_loader
    assert "catalogueWorksReport" not in public_css


def test_retired_studio_works_route_and_dedicated_owners_are_absent() -> None:
    studio_config = read_json(
        REPO_ROOT / "studio/app/frontend/config/studio-config.json"
    )
    routes = studio_config["app"]["routes"]

    assert "studio_works" not in routes
    for relative_path in (
        "studio/app/frontend/routes/studio-works.html",
        "studio/app/frontend/js/studio-works.js",
        "studio/app/frontend/js/studio-ui.js",
        "studio/tests/smoke/local_studio_app_studio_works_route.py",
    ):
        assert not (REPO_ROOT / relative_path).exists()

    home_source = (
        REPO_ROOT / "studio/app/frontend/js/studio-home.js"
    ).read_text(encoding="utf-8")
    assert (
        'href: "/docs/?scope=dotlineform&doc=d-20260810-222148-99daec"'
        in home_source
    )
    assert 'siteKey: "docs_viewer"' in home_source
    assert "http://127.0.0.1:8776" not in home_source
    assert "studio_works" not in home_source


def test_catalogue_drafts_and_exact_editors_remain_registered() -> None:
    studio_config = read_json(
        REPO_ROOT / "studio/app/frontend/config/studio-config.json"
    )
    routes = studio_config["app"]["routes"]

    assert routes["catalogue_status"]["path"] == "/studio/catalogue-status/"
    assert routes["catalogue_series_editor"]["path"] == "/studio/catalogue-series/"
    assert routes["catalogue_work_editor"]["path"] == "/studio/catalogue-work/"
