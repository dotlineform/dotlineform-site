"""Runtime config for the local Studio app server."""

from __future__ import annotations

import json
import os
from pathlib import Path


STUDIO_VIEWS: dict[str, dict[str, str]] = {
    "docs": {
        "label": "docs",
        "title": "Docs",
        "path": "/docs/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=docs-viewer&mode=manage",
        "script": "/studio/docs-viewer/runtime/js/docs-viewer.js",
    },
    "studio_catalogue": {
        "label": "catalogue",
        "title": "Catalogue Dashboard",
        "path": "/studio/catalogue/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=new-pipeline-studio-implementation-plan&mode=manage",
        "script": "/studio/app/frontend/js/studio-dashboard.js",
    },
    "studio_analytics": {
        "label": "analytics",
        "title": "Analytics Dashboard",
        "path": "/studio/analytics/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=tag-groups&mode=manage",
        "script": "/studio/app/frontend/js/studio-dashboard.js",
    },
    "tag_groups": {
        "label": "tag groups",
        "title": "Tag Groups",
        "path": "/studio/analytics/tag-groups/",
        "doc_href": "/docs/?scope=studio&doc=tag-groups&mode=manage",
        "script": "/studio/app/frontend/js/tag-groups.js",
    },
    "tag_registry": {
        "label": "registry",
        "title": "Tag Registry",
        "path": "/studio/analytics/tag-registry/",
        "doc_href": "/docs/?scope=studio&doc=tag-registry&mode=manage",
        "script": "/studio/app/frontend/js/tag-registry.js",
    },
    "tag_aliases": {
        "label": "aliases",
        "title": "Tag Aliases",
        "path": "/studio/analytics/tag-aliases/",
        "doc_href": "/docs/?scope=studio&doc=tag-aliases&mode=manage",
        "script": "/studio/app/frontend/js/tag-aliases.js",
    },
    "series_tags": {
        "label": "series tags",
        "title": "Series Tags",
        "path": "/studio/analytics/series-tags/",
        "doc_href": "/docs/?scope=studio&doc=series-tags&mode=manage",
        "script": "/studio/app/frontend/js/series-tags.js",
    },
    "series_tag_editor": {
        "label": "tag editor",
        "title": "Series Tag Editor",
        "path": "/studio/analytics/series-tag-editor/",
        "doc_href": "/docs/?scope=studio&doc=tag-editor&mode=manage",
        "script": "/studio/app/frontend/js/series-tag-editor-page.js",
        "nav": "false",
    },
    "studio_audits": {
        "label": "audits",
        "title": "Studio Audits",
        "path": "/studio/audits/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=studio-audits&mode=manage",
        "script": "/studio/app/frontend/js/studio-audits.js",
    },
    "project_state": {
        "label": "project state",
        "title": "Project State",
        "path": "/studio/project-state/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=project-state-page&mode=manage",
        "script": "/studio/app/frontend/js/project-state.js",
    },
    "thumbnail_quality": {
        "label": "thumbnail quality",
        "title": "Thumbnail Quality",
        "path": "/studio/thumbnail-quality/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=thumbnail-quality-page&mode=manage",
        "script": "/studio/app/frontend/js/thumbnail-quality.js",
    },
    "bulk_add_work": {
        "label": "bulk add",
        "title": "Bulk Add Work",
        "path": "/studio/bulk-add-work/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=bulk-add-work&mode=manage",
        "script": "/studio/app/frontend/js/bulk-add-work.js",
    },
    "activity": {
        "label": "activity",
        "title": "Studio Activity",
        "path": "/studio/activity/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=studio-activity&mode=manage",
        "script": "/studio/app/frontend/js/activity-log.js",
    },
    "data_sharing": {
        "label": "data sharing",
        "title": "Data Sharing",
        "path": "/studio/data-sharing/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=studio-data-sharing&mode=manage",
        "script": "/studio/app/frontend/js/studio-static-route.js",
    },
    "data_sharing_prepare": {
        "label": "prepare share",
        "title": "Prepare Share Package",
        "path": "/studio/data-sharing/prepare/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=studio-data-sharing&mode=manage",
        "script": "/studio/app/frontend/js/data-sharing-prepare.js",
    },
    "data_sharing_review": {
        "label": "review share",
        "title": "Review Returned Package",
        "path": "/studio/data-sharing/review/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=studio-data-sharing&mode=manage",
        "script": "/studio/app/frontend/js/data-sharing-review.js",
    },
    "catalogue_field_registry": {
        "label": "field registry",
        "title": "Catalogue Field Registry",
        "path": "/studio/catalogue-field-registry/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=catalogue-field-registry-review&mode=manage",
        "script": "/studio/app/frontend/js/catalogue-field-registry-review.js",
    },
    "catalogue_status": {
        "label": "drafts",
        "title": "Catalogue Drafts",
        "path": "/studio/catalogue-status/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=catalogue-status&mode=manage",
        "script": "/studio/app/frontend/js/catalogue-status.js",
    },
    "studio_works": {
        "label": "works",
        "title": "Studio Works",
        "path": "/studio/studio-works/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=studio-works&mode=manage",
        "script": "/studio/app/frontend/js/studio-works.js",
    },
    "catalogue_series_editor": {
        "label": "series editor",
        "title": "Catalogue Series Editor",
        "path": "/studio/catalogue-series/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=catalogue-series-editor&mode=manage",
        "script": "/studio/app/frontend/js/catalogue-series-editor.js",
    },
    "catalogue_work_editor": {
        "label": "work editor",
        "title": "Catalogue Work Editor",
        "path": "/studio/catalogue-work/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=catalogue-work-editor&mode=manage",
        "script": "/studio/app/frontend/js/catalogue-work-editor.js",
    },
    "catalogue_work_detail_editor": {
        "label": "detail editor",
        "title": "Catalogue Work Detail Editor",
        "path": "/studio/catalogue-work-detail/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=catalogue-work-detail-editor&mode=manage",
        "script": "/studio/app/frontend/js/catalogue-work-detail-editor.js",
    },
    "catalogue_moment_editor": {
        "label": "moment editor",
        "title": "Catalogue Moment Editor",
        "path": "/studio/catalogue-moment/?mode=manage",
        "doc_href": "/docs/?scope=studio&doc=catalogue-moment-editor&mode=manage",
        "script": "/studio/app/frontend/js/catalogue-moment-editor.js",
    },
    "ui_catalogue_demos": {
        "label": "ui catalogue",
        "title": "UI Catalogue Demos",
        "path": "/studio/ui-catalogue/demos/",
        "doc_href": "/docs/?scope=studio&doc=ui-catalogue&mode=manage",
        "script": "/assets/ui-catalogue/js/ui-catalogue-demo.js",
    },
    "ui_catalogue_demo_button": {
        "label": "button",
        "title": "UI Demo Primitive: Button",
        "path": "/studio/ui-catalogue/demos/primitives/button/",
        "doc_href": "/docs/?scope=studio&doc=ui-primitive-button&mode=manage",
        "script": "/assets/ui-catalogue/js/ui-catalogue-demo.js",
        "nav": "false",
    },
    "ui_catalogue_demo_input": {
        "label": "input",
        "title": "UI Demo Primitive: Input",
        "path": "/studio/ui-catalogue/demos/primitives/input/",
        "doc_href": "/docs/?scope=studio&doc=ui-primitive-input&mode=manage",
        "script": "/assets/ui-catalogue/js/ui-catalogue-demo.js",
        "nav": "false",
    },
    "ui_catalogue_demo_list": {
        "label": "list",
        "title": "UI Demo Primitive: List",
        "path": "/studio/ui-catalogue/demos/primitives/list/",
        "doc_href": "/docs/?scope=studio&doc=ui-primitive-list&mode=manage",
        "script": "/assets/ui-catalogue/js/ui-catalogue-demo.js",
        "nav": "false",
    },
    "ui_catalogue_demo_modal_shell": {
        "label": "modal shell",
        "title": "UI Demo Primitive: Modal Shell",
        "path": "/studio/ui-catalogue/demos/primitives/modal-shell/",
        "doc_href": "/docs/?scope=studio&doc=ui-primitive-modal-shell&mode=manage",
        "script": "/assets/ui-catalogue/js/ui-catalogue-demo.js",
        "nav": "false",
    },
    "ui_catalogue_demo_panel": {
        "label": "panel",
        "title": "UI Demo Primitive: Panel",
        "path": "/studio/ui-catalogue/demos/primitives/panel/",
        "doc_href": "/docs/?scope=studio&doc=ui-primitive-panel&mode=manage",
        "script": "/assets/ui-catalogue/js/ui-catalogue-demo.js",
        "nav": "false",
    },
    "ui_catalogue_demo_reopenable_command_result": {
        "label": "reopenable result",
        "title": "UI Demo Pattern: Reopenable Command Result",
        "path": "/studio/ui-catalogue/demos/patterns/reopenable-command-result/",
        "doc_href": "/docs/?scope=studio&doc=ui-pattern-reopenable-command-result&mode=manage",
        "script": "/assets/ui-catalogue/js/ui-catalogue-demo.js",
        "nav": "false",
    },
    "ui_catalogue_demo_column_links": {
        "label": "column links",
        "title": "UI Demo Pattern: Column Links",
        "path": "/studio/ui-catalogue/demos/patterns/column-links/",
        "doc_href": "/docs/?scope=studio&doc=ui-pattern-column-links&mode=manage",
        "script": "/assets/ui-catalogue/js/ui-catalogue-demo.js",
        "nav": "false",
    },
}

STUDIO_TOP_NAV_VIEW_IDS: tuple[str, ...] = (
    "docs",
    "studio_catalogue",
    "studio_analytics",
    "data_sharing",
)

STUDIO_MEDIA: dict[str, object] = {
    "thumbs": {
        "base": "",
        "works": "/assets/works/img",
        "work_details": "/assets/work_details/img",
        "moments": "/assets/moments/img",
    },
    "media": {
        "base": "https://media.dotlineform.com",
        "works_images": "/works/img",
        "works_files": "/works/files",
        "work_details_images": "/work_details/img",
        "moments_images": "/moments/img",
    },
}

STUDIO_SERVICE_ENDPOINTS: dict[str, object] = {
    "analytics": {
        "base": "/studio/api/analytics",
        "health": "/studio/api/analytics/health",
        "delete_tag_alias": "/studio/api/analytics/delete-tag-alias",
        "demote_tag": "/studio/api/analytics/demote-tag",
        "demote_tag_preview": "/studio/api/analytics/demote-tag-preview",
        "import_tag_assignments": "/studio/api/analytics/import-tag-assignments",
        "import_tag_assignments_preview": "/studio/api/analytics/import-tag-assignments-preview",
        "import_tag_aliases": "/studio/api/analytics/import-tag-aliases",
        "import_tag_registry": "/studio/api/analytics/import-tag-registry",
        "mutate_tag_alias": "/studio/api/analytics/mutate-tag-alias",
        "mutate_tag_alias_preview": "/studio/api/analytics/mutate-tag-alias-preview",
        "mutate_tag": "/studio/api/analytics/mutate-tag",
        "mutate_tag_preview": "/studio/api/analytics/mutate-tag-preview",
        "promote_tag_alias": "/studio/api/analytics/promote-tag-alias",
        "promote_tag_alias_preview": "/studio/api/analytics/promote-tag-alias-preview",
        "tag_aliases": "/studio/api/analytics/tag-aliases",
        "tag_assignments": "/studio/api/analytics/tag-assignments",
        "tag_groups": "/studio/api/analytics/tag-groups",
        "tag_registry": "/studio/api/analytics/tag-registry",
        "save_tags": "/studio/api/analytics/save-tags",
    },
    "docs": {
        "base": "/studio/api/docs",
        "health": "/studio/api/docs/health",
        "capabilities": "/studio/api/docs/capabilities",
        "generated_index": "/studio/api/docs/docs/generated/index",
        "generated_search": "/studio/api/docs/docs/generated/search",
        "import_source": "/studio/api/docs/docs/import-source",
        "import_source_files": "/studio/api/docs/docs/import-source-files",
        "import_html": "/studio/api/docs/docs/import-html",
        "import_html_files": "/studio/api/docs/docs/import-html-files",
        "open_source": "/studio/api/docs/docs/open-source",
        "data_sharing_prepare": "/studio/api/docs/data-sharing/prepare",
        "data_sharing_returned_packages": "/studio/api/docs/data-sharing/returned-packages",
        "data_sharing_review": "/studio/api/docs/data-sharing/review",
        "data_sharing_apply": "/studio/api/docs/data-sharing/apply",
    },
    "audits": {
        "base": "/studio/api/audits",
        "health": "/studio/api/audits/health",
        "audits": "/studio/api/audits/audits",
        "run": "/studio/api/audits/audits/run",
    },
    "catalogue": {
        "base": "/studio/api/catalogue",
        "health": "/studio/api/catalogue/health",
        "read": "/studio/api/catalogue/read",
        "bulk_save": "/studio/api/catalogue/bulk-save",
        "delete_preview": "/studio/api/catalogue/delete-preview",
        "delete_apply": "/studio/api/catalogue/delete-apply",
        "publication_preview": "/studio/api/catalogue/publication-preview",
        "publication_apply": "/studio/api/catalogue/publication-apply",
        "create_work": "/studio/api/catalogue/work/create",
        "save_work": "/studio/api/catalogue/work/save",
        "create_work_detail": "/studio/api/catalogue/work-detail/create",
        "save_work_detail": "/studio/api/catalogue/work-detail/save",
        "import_preview": "/studio/api/catalogue/import-preview",
        "import_apply": "/studio/api/catalogue/import-apply",
        "create_series": "/studio/api/catalogue/series/create",
        "save_series": "/studio/api/catalogue/series/save",
        "build_preview": "/studio/api/catalogue/build-preview",
        "build_apply": "/studio/api/catalogue/build-apply",
        "prose_import_preview": "/studio/api/catalogue/prose/import-preview",
        "prose_import_apply": "/studio/api/catalogue/prose/import-apply",
        "moment_import_preview": "/studio/api/catalogue/moment/import-preview",
        "moment_import_apply": "/studio/api/catalogue/moment/import-apply",
        "moment_preview": "/studio/api/catalogue/moment/preview",
        "save_moment": "/studio/api/catalogue/moment/save",
        "project_state_report": "/studio/api/catalogue/project-state-report",
        "thumbnail_quality_preview": "/studio/api/catalogue/thumbnail-quality-preview",
    },
}

STUDIO_MODAL_EVENT = "studio:open-modal"

PRODUCTION_SITE_BASE = "https://dotlineform.com"


def asset_version(repo_root: Path) -> str:
    candidates = [
        repo_root / "_includes" / "docs_viewer_shell.html",
        repo_root / "assets" / "css" / "main.css",
        repo_root / "studio" / "docs-viewer" / "runtime" / "js" / "docs-viewer.js",
        repo_root / "studio" / "docs-viewer" / "assets" / "css" / "docs-viewer.css",
        repo_root / "studio" / "docs-viewer" / "assets" / "css" / "docs-viewer-management.css",
        repo_root / "studio" / "docs-viewer" / "config" / "runtime" / "docs-viewer-config.json",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-navigation.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "tag-groups.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "tag-registry.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "tag-aliases.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "series-tags.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "series-tag-editor-page.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-audits.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "project-state.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "thumbnail-quality.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "bulk-add-work.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "activity-log.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "activity-log-modals.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "data-sharing-prepare.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "data-sharing-review.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-field-registry-review.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "studio-works.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-series-editor.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-work-editor.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-work-detail-editor.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "catalogue-moment-editor.js",
        repo_root / "studio" / "app" / "frontend" / "js" / "tag-studio.js",
        repo_root / "studio" / "app" / "assets" / "css" / "studio.css",
        repo_root / "studio" / "app" / "frontend" / "config" / "studio-config.json",
        repo_root / "assets" / "ui-catalogue" / "js" / "ui-catalogue-demo.js",
        repo_root / "assets" / "ui-catalogue" / "css" / "ui-catalogue-demo.css",
    ]
    mtimes = [path.stat().st_mtime for path in candidates if path.exists()]
    return str(int(max(mtimes))) if mtimes else "1"


def runtime_config(repo_root: Path, version: str) -> dict[str, object]:
    config_path = repo_root / "studio" / "app" / "frontend" / "config" / "studio-config.json"
    pipeline_path = repo_root / "_data" / "pipeline.json"
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read Studio config: {config_path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Studio config must be a JSON object: {config_path}")
    try:
        pipeline_payload = json.loads(pipeline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pipeline_payload = {}
    pipeline_variants = pipeline_payload.get("variants") if isinstance(pipeline_payload, dict) else {}
    if not isinstance(pipeline_variants, dict):
        pipeline_variants = {}

    payload.setdefault("app", {})
    app_config = payload["app"]
    if not isinstance(app_config, dict):
        app_config = {}
        payload["app"] = app_config
    paths_config = payload.get("paths") if isinstance(payload.get("paths"), dict) else {}
    data_paths = paths_config.get("data") if isinstance(paths_config, dict) and isinstance(paths_config.get("data"), dict) else {}
    app_config["runtime"] = {
        "host": "local-studio-app",
        "asset_version": version,
        "routes": {
            "health": "/health",
            "runtime_config": "/studio/runtime-config.json",
        },
        "services": STUDIO_SERVICE_ENDPOINTS,
        "sites": runtime_site_bases(),
        "data_paths": data_paths,
        "media": STUDIO_MEDIA,
        "pipeline": {
            "variants": pipeline_variants,
        },
        "views": [
            {"id": view_id, **view}
            for view_id, view in STUDIO_VIEWS.items()
        ],
        "navigation": {
            "primary": list(STUDIO_TOP_NAV_VIEW_IDS),
        },
        "modals": {
            "event": STUDIO_MODAL_EVENT,
            "registered": [],
        },
    }
    return payload


def runtime_site_bases() -> dict[str, object]:
    jekyll_host = os.environ.get("JEKYLL_HOST", "127.0.0.1").strip() or "127.0.0.1"
    jekyll_port = os.environ.get("JEKYLL_PORT", "4000").strip() or "4000"
    public_preview_base = os.environ.get("PUBLIC_SITE_PREVIEW_BASE", "").strip()
    if not public_preview_base:
        public_preview_base = f"http://{jekyll_host}:{jekyll_port}"
    production_base = os.environ.get("PRODUCTION_SITE_BASE", PRODUCTION_SITE_BASE).strip() or PRODUCTION_SITE_BASE

    return {
        "public_preview": {
            "base": normalize_base_url(public_preview_base),
        },
        "production": {
            "base": normalize_base_url(production_base),
        },
    }


def normalize_base_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    return normalized or "/"
