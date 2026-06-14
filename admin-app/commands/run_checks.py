#!/usr/bin/env python3
"""Run optional repo check profiles and write local run logs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "var" / "admin" / "test-runs"
PUBLIC_SITE_ROOT = REPO_ROOT / "site"
SOURCE_MODULE_SITE_ROOT = Path(".")


@dataclass(frozen=True)
class CheckCommand:
    name: str
    argv: tuple[str, ...]
    description: str


def site_validate_argv() -> tuple[str, ...]:
    return (
        sys.executable,
        "site-tools/site_validate.py",
    )


def pytest_argv(*paths: str) -> tuple[str, ...]:
    return (sys.executable, "-m", "pytest", "-q", *paths)


PROFILE_COMMANDS: dict[str, tuple[CheckCommand, ...]] = {
    "quick": (
        CheckCommand("git-diff-check", ("git", "diff", "--check"), "Check staged and unstaged diff whitespace."),
        CheckCommand(
            "python-syntax",
            (
                sys.executable,
                "-m",
                "py_compile",
                "admin-app/commands/run_checks.py",
                "studio/shared/python/local_env.py",
                "studio/shared/python/pipeline_config.py",
                "studio/shared/python/studio_python_paths.py",
                "studio/shared/python/display_paths.py",
                "studio/shared/python/script_logging.py",
                "studio/shared/python/studio_activity.py",
                "admin-app/checks/audit_site_consistency.py",
                "admin-app/checks/audit_projection_contract.py",
                "admin-app/checks/audit_public_build_surface.py",
                "admin-app/checks/css_token_audit.py",
                "studio/services/media/publish_media_to_r2.py",
                "studio/services/media/build_palette_data.py",
                "studio/services/catalogue/catalogue_json_build.py",
                "studio/services/catalogue/catalogue_build_commands.py",
                "studio/services/catalogue/catalogue_build_field_plan.py",
                "studio/services/catalogue/catalogue_build_media.py",
                "studio/services/catalogue/catalogue_public_paths.py",
                "studio/services/catalogue/catalogue_build_scopes.py",
                "studio/services/catalogue/generate_work_pages.py",
                "studio/services/catalogue/catalogue_generation_common.py",
                "studio/services/catalogue/catalogue_generation_indexes.py",
                "studio/services/catalogue/catalogue_generation_moments.py",
                "studio/services/catalogue/catalogue_generation_recent.py",
                "studio/services/catalogue/catalogue_generation_records.py",
                "studio/services/catalogue/catalogue_generation_source_updates.py",
                "studio/services/catalogue/catalogue_generation_writes.py",
                "studio/services/media/make_srcset_images.py",
                "studio/services/catalogue/project_state_report.py",
                "studio/services/catalogue/catalogue_bulk_service.py",
                "studio/services/catalogue/catalogue_build_service.py",
                "studio/services/catalogue/catalogue_delete_service.py",
                "studio/services/catalogue/catalogue_moment_service.py",
                "studio/services/catalogue/catalogue_publication_service.py",
                "studio/services/catalogue/catalogue_prose_import_service.py",
                "studio/services/catalogue/catalogue_series_service.py",
                "studio/services/catalogue/catalogue_service_context.py",
                "studio/services/catalogue/catalogue_work_detail_service.py",
                "studio/services/catalogue/catalogue_work_service.py",
                "studio/services/catalogue/catalogue_write_service.py",
                "studio/app/server/studio/studio_app_config.py",
                "studio/app/server/studio/studio_app_views.py",
                "studio/app/server/studio/studio_app_server.py",
                "analytics-app/app/server/analytics_app/analytics_api.py",
                "analytics-app/app/server/analytics_app/analytics_app_config.py",
                "analytics-app/app/server/analytics_app/analytics_app_views.py",
                "analytics-app/app/server/analytics_app/analytics_app_server.py",
                "analytics-app/app/server/analytics_app/analytics_data_sharing_api.py",
                "analytics-app/app/server/analytics_app/data_sharing_adapters.py",
                "analytics-app/app/server/analytics_app/data_sharing_routes.py",
                "analytics-app/app/server/analytics_app/data_sharing_service.py",
                "admin-app/app/server/admin_app/ui_catalogue_config.py",
                "admin-app/app/server/admin_app/ui_catalogue_views.py",
                "admin-app/app/server/admin_app/admin_app_config.py",
                "admin-app/app/server/admin_app/admin_app_views.py",
                "admin-app/app/server/admin_app/admin_app_server.py",
                "admin-app/app/server/admin_app/admin_testing_api.py",
                "admin-app/checks/audit_studio_ready_state.py",
                "admin-app/checks/verify_activity_contract.py",
                "docs-viewer/services/docs_activity.py",
                "analytics-app/app/server/analytics_app/tag_services/tag_activity.py",
                "analytics-app/app/server/analytics_app/tag_services/tag_alias_mutations.py",
                "analytics-app/app/server/analytics_app/tag_services/tag_assignment_service.py",
                "analytics-app/app/server/analytics_app/tag_services/tag_promotion_mutations.py",
                "analytics-app/app/server/analytics_app/tag_services/tag_registry_mutations.py",
                "analytics-app/app/server/analytics_app/tag_services/tag_source_paths.py",
                "analytics-app/app/server/analytics_app/tag_services/tag_source_model.py",
                "analytics-app/app/server/analytics_app/tag_services/tag_write_transactions.py",
                "docs-viewer/services/docs_import_source_service.py",
                "docs-viewer/services/docs_live_rebuild_watcher.py",
                "docs-viewer/services/docs_management_broken_links_service.py",
                "docs-viewer/services/docs_management_capabilities_service.py",
                "docs-viewer/services/docs_management_context.py",
                "docs-viewer/services/docs_management_import_service.py",
                "docs-viewer/services/docs_management_mutation_service.py",
                "docs-viewer/services/docs_management_read_service.py",
                "docs-viewer/services/docs_management_source_service.py",
                "docs-viewer/services/docs_management_service.py",
                "docs-viewer/services/docs_management_mutations.py",
                "docs-viewer/services/docs_scope_manifest.py",
                "docs-viewer/services/docs_viewer_service.py",
                "analytics-app/app/server/analytics_app/tag_services/tag_routes.py",
                "studio/services/catalogue/catalogue_source.py",
                "studio/services/catalogue/catalogue_cleanup.py",
                "studio/services/catalogue/catalogue_delete_plans.py",
                "studio/services/catalogue/catalogue_invalidation.py",
                "studio/services/catalogue/catalogue_lookup_refresh.py",
                "studio/services/catalogue/catalogue_publication.py",
                "studio/services/catalogue/catalogue_prose_import.py",
                "studio/services/catalogue/catalogue_routes.py",
                "studio/services/catalogue/catalogue_save_build.py",
                "studio/services/catalogue/catalogue_source_mutation.py",
                "studio/services/catalogue/catalogue_transactions.py",
                "admin-app/app/server/admin_app/audit_runner.py",
                "docs-viewer/tests/smoke/docs_viewer_route_index_panel.py",
                "docs-viewer/tests/smoke/docs_viewer_route_navigation.py",
                "docs-viewer/tests/smoke/docs_viewer_route_search_missing_hash.py",
                "docs-viewer/tests/smoke/docs_viewer_route_smoke_helpers.py",
                "docs-viewer/tests/smoke/docs_viewer_routes.py",
                "docs-viewer/tests/smoke/docs_viewer_service_manage.py",
                "docs-viewer/tests/smoke/docs_viewer_manage_dark_theme.py",
                "docs-viewer/tests/python/test_docs_viewer_v2_custom_token_fixtures.py",
                "docs-viewer/tests/python/test_generated_output_contract_fixtures.py",
                "studio/tests/smoke/local_studio_app_docs_viewer.py",
                "docs-viewer/tests/smoke/docs_viewer_management_modal.py",
                "docs-viewer/tests/smoke/docs_viewer_index_panel_modules.py",
                "docs-viewer/tests/smoke/docs_viewer_index_panel_route.py",
                "docs-viewer/tests/smoke/docs_viewer_management_action_workflow_modules.py",
                "docs-viewer/tests/smoke/docs_html_import_modules.py",
                "analytics-app/tests/smoke/data_sharing_prepare_modules.py",
                "analytics-app/tests/smoke/data_sharing_prepare.py",
                "analytics-app/tests/smoke/data_sharing_review.py",
                "analytics-app/tests/smoke/local_analytics_app_alias_apis.py",
                "analytics-app/tests/smoke/local_analytics_app_promotion_apis.py",
                "analytics-app/tests/smoke/local_analytics_app_registry_apis.py",
                "analytics-app/tests/smoke/local_analytics_app_tag_assignment_apis.py",
                "analytics-app/tests/smoke/local_analytics_app_tag_groups.py",
                "analytics-app/tests/smoke/series_tag_editor_modal.py",
                "analytics-app/tests/smoke/series_tag_editor_ready_state.py",
                "analytics-app/tests/smoke/series_tags_modal.py",
                "analytics-app/tests/smoke/series_tags_render.py",
                "analytics-app/tests/smoke/tag_aliases_modal.py",
                "analytics-app/tests/smoke/tag_aliases_ready_state.py",
                "analytics-app/tests/smoke/local_analytics_app_tag_routes.py",
                "analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py",
                "analytics-app/tests/smoke/tag_registry_modal.py",
                "analytics-app/tests/smoke/tag_registry_modules.py",
                "analytics-app/tests/smoke/tag_route_shell_modules.py",
                "admin-app/tests/smoke/ui_catalogue_search_list_modules.py",
                "admin-app/tests/smoke/admin_ui_catalogue_modal_demo.py",
                "admin-app/tests/smoke/admin_ui_catalogue_routes.py",
                "studio/tests/smoke/public_site_theme_toggle.py",
                "admin-app/tests/smoke/admin_home_route.py",
                "admin-app/tests/smoke/admin_operations_routes.py",
                "studio/tests/python/test_studio_app_server.py",
                "analytics-app/tests/python/test_analytics_app_server.py",
                "analytics-app/tests/python/test_analytics_data_sharing_api.py",
                "analytics-app/tests/python/test_data_sharing_adapters.py",
                "analytics-app/tests/python/test_data_sharing_service.py",
                "analytics-app/tests/python/test_data_sharing_subsystem_scaffold.py",
                "analytics-app/tests/python/test_tags_data_sharing_adapter.py",
                "admin-app/tests/python/test_admin_app_server.py",
                "admin-app/tests/python/test_admin_runner_contract.py",
                "admin-app/tests/python/test_admin_ui_catalogue.py",
                "admin-app/tests/python/test_activity_contract.py",
                "studio/tests/python/test_local_env.py",
                "studio/tests/python/test_publish_media_to_r2.py",
                "docs-viewer/tests/python/test_docs_activity.py",
                "analytics-app/tests/python/test_tag_activity.py",
                "analytics-app/tests/python/test_tag_alias_mutations.py",
                "analytics-app/tests/python/test_tag_assignment_service.py",
                "analytics-app/tests/python/test_tag_promotion_mutations.py",
                "analytics-app/tests/python/test_tag_registry_mutations.py",
                "analytics-app/tests/python/test_tag_source_model.py",
                "analytics-app/tests/python/test_tag_write_transactions.py",
                "docs-viewer/tests/python/test_docs_live_rebuild_watcher.py",
                "docs-viewer/tests/python/test_docs_management_mutations.py",
                "docs-viewer/tests/python/test_docs_source_model.py",
                "docs-viewer/tests/python/test_docs_viewer_service.py",
                "analytics-app/tests/python/test_tag_routes.py",
                "studio/tests/python/test_catalogue_cleanup.py",
                "studio/tests/python/test_catalogue_delete_plans.py",
                "studio/tests/python/test_catalogue_invalidation.py",
                "studio/tests/python/test_catalogue_lookup_refresh.py",
                "studio/tests/python/test_catalogue_publication.py",
                "studio/tests/python/test_catalogue_prose_import.py",
                "studio/tests/python/test_catalogue_routes.py",
                "studio/tests/python/test_catalogue_save_build.py",
                "studio/tests/python/test_catalogue_source_mutation.py",
                "studio/tests/python/test_catalogue_transactions.py",
                "studio/tests/python/test_studio_activity_context.py",
                "studio/tests/python/test_studio_activity_feed.py",
                "studio/tests/python/test_catalogue_field_registry.py",
                "studio/tests/python/test_catalogue_build_commands.py",
                "studio/tests/python/test_catalogue_build_field_plan.py",
                "studio/tests/python/test_catalogue_build_media.py",
                "studio/tests/python/test_catalogue_build_scopes.py",
                "studio/tests/python/test_catalogue_generation_indexes.py",
                "studio/tests/python/test_catalogue_generation_moments.py",
                "studio/tests/python/test_catalogue_generation_recent.py",
                "studio/tests/python/test_catalogue_generation_records.py",
                "studio/tests/python/test_catalogue_generation_source_updates.py",
                "studio/tests/python/test_catalogue_generation_writes.py",
            ),
            "Compile lightweight Python check scripts.",
        ),
        CheckCommand(
            "quick-python-pytest",
            pytest_argv(
                "admin-app/tests/python/test_activity_contract.py",
                "studio/tests/python/test_local_env.py",
                "studio/tests/python/test_publish_media_to_r2.py",
                "studio/tests/python/test_catalogue_invalidation.py",
                "studio/tests/python/test_catalogue_lookup_refresh.py",
                "studio/tests/python/test_catalogue_cleanup.py",
                "studio/tests/python/test_catalogue_delete_plans.py",
                "studio/tests/python/test_catalogue_publication.py",
                "studio/tests/python/test_catalogue_prose_import.py",
                "studio/tests/python/test_catalogue_transactions.py",
                "studio/tests/python/test_catalogue_routes.py",
                "analytics-app/tests/python/test_tag_routes.py",
                "analytics-app/tests/python/test_tag_activity.py",
                "analytics-app/tests/python/test_tag_alias_mutations.py",
                "analytics-app/tests/python/test_tag_assignment_service.py",
                "analytics-app/tests/python/test_tag_promotion_mutations.py",
                "analytics-app/tests/python/test_tag_registry_mutations.py",
                "analytics-app/tests/python/test_tag_source_model.py",
                "analytics-app/tests/python/test_tag_write_transactions.py",
                "analytics-app/tests/python/test_analytics_app_server.py",
                "analytics-app/tests/python/test_analytics_data_sharing_api.py",
                "admin-app/tests/python/test_admin_ui_catalogue.py",
                "studio/tests/python/test_catalogue_save_build.py",
                "studio/tests/python/test_catalogue_source_mutation.py",
                "studio/tests/python/test_studio_activity_context.py",
                "studio/tests/python/test_studio_activity_feed.py",
                "studio/tests/python/test_catalogue_build_commands.py",
                "studio/tests/python/test_catalogue_build_scopes.py",
                "studio/tests/python/test_catalogue_build_field_plan.py",
                "studio/tests/python/test_catalogue_build_media.py",
                "studio/tests/python/test_catalogue_generation_moments.py",
                "studio/tests/python/test_catalogue_generation_recent.py",
                "studio/tests/python/test_catalogue_generation_writes.py",
                "studio/tests/python/test_catalogue_generation_source_updates.py",
            ),
            "Run quick-profile Python tests through pytest collection.",
        ),
        CheckCommand(
            "projection-contract",
            (sys.executable, "admin-app/checks/audit_projection_contract.py"),
            "Validate the projection contract manifest and checked-in public projections.",
        ),
        CheckCommand(
            "studio-ready-state-audit",
            (sys.executable, "admin-app/checks/audit_studio_ready_state.py", "--strict"),
            "Audit Studio route-ready template contracts.",
        ),
        CheckCommand(
            "studio-config-json",
            (sys.executable, "-m", "json.tool", "studio/app/frontend/config/studio-config.json"),
            "Parse Studio config JSON.",
        ),
        CheckCommand(
            "activity-contract-json",
            (sys.executable, "-m", "json.tool", "studio/data/config/runtime/activity-contract.json"),
            "Parse Studio activity contract JSON.",
        ),
    ),
    "admin-checks": (
        CheckCommand(
            "admin-checks-python-pytest",
            pytest_argv(
                "admin-app/tests/python/test_target_map_resolver.py",
                "admin-app/tests/python/test_admin_checks_config.py",
                "admin-app/tests/python/test_run_reports.py",
                "admin-app/tests/python/test_files_report.py",
                "admin-app/tests/python/test_target_map_report.py",
                "admin-app/tests/python/test_admin_checks_api.py",
            ),
            "Run focused Admin checks config, resolver, orchestrator, producer, and API tests.",
        ),
    ),
    "catalogue": (
        CheckCommand(
            "catalogue-python-pytest",
            pytest_argv(
                "studio/tests/python/test_catalogue_field_registry.py",
                "studio/tests/python/test_catalogue_media_cleanup.py",
            ),
            "Run catalogue-profile Python tests through pytest collection.",
        ),
        CheckCommand(
            "catalogue-build-preview-downloads",
            ("./studio/services/catalogue/catalogue_json_build.py", "--work-id", "00001", "--changed-fields", "downloads"),
            "Preview a narrow field-aware catalogue build plan.",
        ),
    ),
    "docs": (
        CheckCommand(
            "docs-python-pytest",
            pytest_argv(
                "docs-viewer/tests/python/test_docs_export.py",
                "analytics-app/tests/python/test_data_sharing_adapters.py",
                "analytics-app/tests/python/test_data_sharing_service.py",
                "docs-viewer/tests/python/test_docs_import.py",
                "docs-viewer/tests/python/test_docs_import_service.py",
                "docs-viewer/tests/python/test_docs_generated_reads.py",
                "docs-viewer/tests/python/test_docs_activity.py",
                "docs-viewer/tests/python/test_docs_live_rebuild_watcher.py",
                "docs-viewer/tests/python/test_docs_write_rebuild.py",
                "docs-viewer/tests/python/test_docs_management_mutations.py",
                "docs-viewer/tests/python/test_docs_management_service.py",
                "docs-viewer/tests/python/test_docs_management_routes.py",
                "docs-viewer/tests/python/test_docs_source_model.py",
                "docs-viewer/tests/python/test_docs_broken_links.py",
                "docs-viewer/tests/python/test_docs_viewer_service.py",
                "docs-viewer/tests/python/test_docs_viewer_v2_custom_token_fixtures.py",
                "docs-viewer/tests/python/test_generated_output_contract_fixtures.py",
            ),
            "Run docs-profile Python tests through pytest collection.",
        ),
        CheckCommand(
            "studio-docs-build",
            (sys.executable, "docs-viewer/build/build_docs.py", "--scope", "studio", "--write"),
            "Regenerate Studio docs-viewer payloads.",
        ),
        CheckCommand(
            "studio-search-build",
            (sys.executable, "docs-viewer/build/build_search.py", "--scope", "studio", "--write"),
            "Regenerate Studio docs search payload.",
        ),
    ),
    "docs-viewer-smoke": (
        CheckCommand(
            "site-validate",
            site_validate_argv(),
            "Validate the checked-in static site root before browser smoke tests.",
        ),
        CheckCommand(
            "docs-viewer-service-manage-smoke",
            (
                sys.executable,
                "docs-viewer/tests/smoke/docs_viewer_service_manage.py",
            ),
            "Smoke-check the standalone Docs Viewer service manage shell and API base.",
        ),
        CheckCommand(
            "public-docs-viewer-readonly-smoke",
            (
                sys.executable,
                "docs-viewer/tests/smoke/public_docs_viewer_readonly.py",
                "--site-root",
                str(PUBLIC_SITE_ROOT),
            ),
            "Smoke-check public Library and Analysis Docs Viewer installs stay read-only.",
        ),
    ),
    "ui-catalogue-smoke": (
        CheckCommand(
            "ui-catalogue-python-pytest",
            pytest_argv("admin-app/tests/python/test_admin_ui_catalogue.py"),
            "Run Admin-hosted UI Catalogue tests through pytest collection.",
        ),
        CheckCommand(
            "ui-catalogue-routes-smoke",
            (
                sys.executable,
                "admin-app/tests/smoke/admin_ui_catalogue_routes.py",
            ),
            "Smoke-check Admin-hosted UI Catalogue demo routes, assets, docs links, and dark theme.",
        ),
        CheckCommand(
            "ui-catalogue-search-list-modules-smoke",
            (
                sys.executable,
                "admin-app/tests/smoke/ui_catalogue_search_list_modules.py",
                "--site-root",
                str(SOURCE_MODULE_SITE_ROOT),
            ),
            "Smoke-check the shared Search List component contract used by UI Catalogue patterns and app adapters.",
        ),
        CheckCommand(
            "ui-catalogue-modal-demo-smoke",
            (
                sys.executable,
                "admin-app/tests/smoke/admin_ui_catalogue_modal_demo.py",
            ),
            "Smoke-check the Admin-hosted UI Catalogue modal shell demo semantics, focus behavior, validation, and mobile sizing.",
        ),
    ),
    "admin-smoke": (
        CheckCommand(
            "admin-home-route-smoke",
            (
                sys.executable,
                "admin-app/tests/smoke/admin_home_route.py",
            ),
            "Smoke-check the local Admin home route and runtime config.",
        ),
        CheckCommand(
            "admin-operations-routes-smoke",
            (
                sys.executable,
                "admin-app/tests/smoke/admin_operations_routes.py",
            ),
            "Smoke-check Admin audits, risk, and activity routes.",
        ),
    ),
    "studio-smoke": (
        CheckCommand(
            "site-validate",
            site_validate_argv(),
            "Validate the checked-in static site root before browser smoke tests.",
        ),
        CheckCommand(
            "public-site-theme-toggle-smoke",
            (
                sys.executable,
                "studio/tests/smoke/public_site_theme_toggle.py",
                "--site-root",
                str(PUBLIC_SITE_ROOT),
            ),
            "Smoke-check the public /series/ header theme toggle.",
        ),
        CheckCommand(
            "public-route-simplification-smoke",
            (
                sys.executable,
                "studio/tests/smoke/public_route_simplification.py",
                "--site-root",
                str(PUBLIC_SITE_ROOT),
            ),
            "Smoke-check the simplified public route contract for series, works, details, moments, search, and 404 recovery.",
        ),
        CheckCommand(
            "catalogue-series-modal-smoke",
            (
                sys.executable,
                "studio/tests/smoke/catalogue_series_modal.py",
            ),
            "Smoke-check the Catalogue Series confirmation modal shell behavior.",
        ),
        CheckCommand(
            "catalogue-editor-route-boot-module-smoke",
            (
                sys.executable,
                "studio/tests/smoke/catalogue_editor_route_boot_modules.py",
                "--site-root",
                str(SOURCE_MODULE_SITE_ROOT),
            ),
            "Smoke-check shared Catalogue editor route boot, readiness, and lookup helpers.",
        ),
    ),
    "analytics-smoke": (
        CheckCommand(
            "local-analytics-registry-api-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/local_analytics_app_registry_apis.py",
            ),
            "Smoke-check local Analytics tag registry write APIs against a fixture repo.",
        ),
        CheckCommand(
            "local-analytics-alias-api-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/local_analytics_app_alias_apis.py",
            ),
            "Smoke-check local Analytics tag alias write APIs against a fixture repo.",
        ),
        CheckCommand(
            "local-analytics-tag-assignment-api-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/local_analytics_app_tag_assignment_apis.py",
            ),
            "Smoke-check local Analytics tag assignment write APIs against a fixture repo.",
        ),
        CheckCommand(
            "local-analytics-promotion-api-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/local_analytics_app_promotion_apis.py",
            ),
            "Smoke-check local Analytics tag promote/demote APIs against a fixture repo.",
        ),
        CheckCommand(
            "local-analytics-tag-routes-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/local_analytics_app_tag_routes.py",
            ),
            "Smoke-check the local Analytics tag route shells and API reads.",
        ),
        CheckCommand(
            "local-analytics-tag-groups-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/local_analytics_app_tag_groups.py",
            ),
            "Smoke-check the local Analytics Tag Groups shell and API read path.",
        ),
        CheckCommand(
            "analytics-data-sharing-prepare-module-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/data_sharing_prepare_modules.py",
                "--site-root",
                str(SOURCE_MODULE_SITE_ROOT),
            ),
            "Smoke-check Analytics Data Sharing prepare module contracts.",
        ),
        CheckCommand(
            "analytics-tag-registry-module-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/tag_registry_modules.py",
                "--site-root",
                str(SOURCE_MODULE_SITE_ROOT),
            ),
            "Smoke-check Analytics tag registry module contracts.",
        ),
        CheckCommand(
            "analytics-tag-registry-modal-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/tag_registry_modal.py",
                "--site-root",
                str(SOURCE_MODULE_SITE_ROOT),
            ),
            "Smoke-check Analytics tag registry modal contracts.",
        ),
        CheckCommand(
            "analytics-tag-aliases-modal-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/tag_aliases_modal.py",
                "--site-root",
                str(SOURCE_MODULE_SITE_ROOT),
            ),
            "Smoke-check Analytics tag aliases modal contracts.",
        ),
        CheckCommand(
            "analytics-series-tags-render-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/series_tags_render.py",
                "--site-root",
                str(SOURCE_MODULE_SITE_ROOT),
            ),
            "Smoke-check Analytics series tags render contracts.",
        ),
        CheckCommand(
            "analytics-series-tags-modal-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/series_tags_modal.py",
                "--site-root",
                str(SOURCE_MODULE_SITE_ROOT),
            ),
            "Smoke-check Analytics series tags modal contracts.",
        ),
        CheckCommand(
            "analytics-series-tag-editor-modal-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/series_tag_editor_modal.py",
                "--site-root",
                str(SOURCE_MODULE_SITE_ROOT),
            ),
            "Smoke-check Analytics series tag editor modal contracts.",
        ),
        CheckCommand(
            "analytics-tag-route-shell-module-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/tag_route_shell_modules.py",
                "--site-root",
                str(SOURCE_MODULE_SITE_ROOT),
            ),
            "Smoke-check Analytics shared tag route shell modules.",
        ),
        CheckCommand(
            "analytics-tag-aliases-ready-state-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/tag_aliases_ready_state.py",
            ),
            "Smoke-check Analytics tag aliases route readiness.",
        ),
        CheckCommand(
            "analytics-series-tag-editor-ready-state-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/series_tag_editor_ready_state.py",
            ),
            "Smoke-check Analytics series tag editor route readiness.",
        ),
        CheckCommand(
            "local-analytics-data-sharing-prepare-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/data_sharing_prepare.py",
                "--mock-data-sharing-api",
            ),
            "Smoke-check the local Analytics Data Sharing prepare route shell and result modal.",
        ),
        CheckCommand(
            "local-analytics-data-sharing-review-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/data_sharing_review.py",
                "--mock-data-sharing-api",
            ),
            "Smoke-check the local Analytics Data Sharing review route shell and apply modals.",
        ),
        CheckCommand(
            "local-analytics-data-sharing-routes-smoke",
            (
                sys.executable,
                "analytics-app/tests/smoke/local_analytics_app_data_sharing_routes.py",
            ),
            "Smoke-check the local Analytics Data Sharing prepare and review route shells.",
        ),
    ),
}

FULL_PROFILE_ORDER = ("quick", "catalogue", "docs", "admin-smoke", "studio-smoke")


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip().lower())
    return value.strip("-") or "check"


def command_text(argv: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in argv)


def create_run_dir(run_id: str | None) -> Path:
    if run_id:
        safe_id = slugify(run_id)
    else:
        safe_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / safe_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def expand_profiles(profile_names: Iterable[str]) -> list[CheckCommand]:
    commands: list[CheckCommand] = []
    seen: set[str] = set()
    for profile in profile_names:
        profile_commands = []
        if profile == "full":
            for child in FULL_PROFILE_ORDER:
                profile_commands.extend(PROFILE_COMMANDS[child])
        else:
            profile_commands.extend(PROFILE_COMMANDS[profile])
        for command in profile_commands:
            if command.name in seen:
                continue
            seen.add(command.name)
            commands.append(command)
    return commands


def run_command(command: CheckCommand, log_path: Path) -> dict[str, object]:
    started = time.monotonic()
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    header = [
        f"name: {command.name}",
        f"description: {command.description}",
        f"cwd: {REPO_ROOT}",
        f"command: {command_text(command.argv)}",
        f"started_at_utc: {started_at}",
        "",
    ]

    try:
        result = subprocess.run(
            command.argv,
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        output = result.stdout or ""
        exit_code = result.returncode
    except FileNotFoundError as error:
        output = f"{error}\n"
        exit_code = 127

    duration = time.monotonic() - started
    footer = [
        "",
        f"exit_code: {exit_code}",
        f"duration_seconds: {duration:.2f}",
    ]
    log_path.write_text("\n".join(header) + output + "\n".join(footer) + "\n", encoding="utf-8")

    return {
        "name": command.name,
        "description": command.description,
        "command": list(command.argv),
        "exit_code": exit_code,
        "duration_seconds": round(duration, 2),
        "log": str(log_path.relative_to(REPO_ROOT)),
    }


def write_summaries(run_dir: Path, profiles: list[str], results: list[dict[str, object]]) -> None:
    failed = [result for result in results if result["exit_code"] != 0]
    summary = {
        "profiles": profiles,
        "status": "failed" if failed else "passed",
        "run_dir": str(run_dir.relative_to(REPO_ROOT)),
        "results": results,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Check Run Summary",
        "",
        f"- Status: {summary['status']}",
        f"- Profiles: {', '.join(profiles)}",
        f"- Run directory: `{summary['run_dir']}`",
        "",
        "## Results",
        "",
    ]
    for result in results:
        status = "pass" if result["exit_code"] == 0 else "fail"
        lines.append(f"- {status}: `{result['name']}` ({result['duration_seconds']}s) - `{result['log']}`")
    lines.append("")
    (run_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        action="append",
        choices=sorted([*PROFILE_COMMANDS.keys(), "full"]),
        default=[],
        help="Check profile to run. Repeat to combine profiles. Defaults to quick.",
    )
    parser.add_argument("--run-id", help="Optional local run id for var/admin/test-runs/.")
    parser.add_argument("--list", action="store_true", help="List available profiles and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list:
        for name in sorted([*PROFILE_COMMANDS.keys(), "full"]):
            if name == "full":
                descriptions = ", ".join(FULL_PROFILE_ORDER)
            else:
                descriptions = ", ".join(command.name for command in PROFILE_COMMANDS[name])
            print(f"{name}: {descriptions}")
        return 0

    profiles = args.profile or ["quick"]
    commands = expand_profiles(profiles)
    run_dir = create_run_dir(args.run_id)

    results: list[dict[str, object]] = []
    total = len(commands)
    for index, command in enumerate(commands, start=1):
        log_path = run_dir / f"{index:03d}-{slugify(command.name)}.log"
        print(f"[{index}/{total}] {command.name}")
        result = run_command(command, log_path)
        results.append(result)
        status = "pass" if result["exit_code"] == 0 else "fail"
        print(f"  {status}: {result['log']}")

    write_summaries(run_dir, profiles, results)
    failed = [result for result in results if result["exit_code"] != 0]
    print(f"summary: {run_dir.relative_to(REPO_ROOT) / 'summary.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
