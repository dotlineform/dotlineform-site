"""Shared context and plumbing for Local Studio catalogue service routes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Mapping

from catalogue import catalogue_activity as activity
from catalogue.catalogue_lookup import DEFAULT_LOOKUP_DIR
from catalogue import catalogue_lookup_refresh as lookup_refresh
from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, SOURCE_FILES, load_json_file
from script_logging import append_script_log
from studio_activity import append_studio_activity


LOGS_REL_DIR = Path("var/studio/catalogue/logs")


@dataclass(frozen=True)
class CatalogueWriteContext:
    repo_root: Path
    source_dir: Path
    lookup_dir: Path
    works_path: Path
    work_details_path: Path
    series_path: Path
    allowed_write_paths: set[Path]
    allowed_write_roots: set[Path]
    dry_run: bool = False

    def rel_path(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.repo_root.resolve()))
        except ValueError:
            return path.name


def build_catalogue_write_context(repo_root: Path, *, dry_run: bool = False) -> CatalogueWriteContext:
    resolved_root = repo_root.resolve()
    source_dir = (resolved_root / DEFAULT_SOURCE_DIR).resolve()
    return CatalogueWriteContext(
        repo_root=resolved_root,
        source_dir=source_dir,
        lookup_dir=(resolved_root / DEFAULT_LOOKUP_DIR).resolve(),
        works_path=(source_dir / SOURCE_FILES["works"]).resolve(),
        work_details_path=(source_dir / SOURCE_FILES["work_details"]).resolve(),
        series_path=(source_dir / SOURCE_FILES["series"]).resolve(),
        allowed_write_paths={
            (source_dir / filename).resolve()
            for kind, filename in SOURCE_FILES.items()
            if kind != "meta"
        },
        allowed_write_roots=set(),
        dry_run=dry_run,
    )


def load_works_payload(path: Path) -> dict[str, Any]:
    payload = load_json_file(path)
    works = payload.get("works")
    if not isinstance(works, dict):
        raise ValueError("works source file must include a works object")
    return payload


def load_work_details_payload(path: Path) -> dict[str, Any]:
    payload = load_json_file(path)
    work_details = payload.get("work_details")
    if not isinstance(work_details, dict):
        raise ValueError("work details source file must include a work_details object")
    return payload


def load_series_payload(path: Path) -> dict[str, Any]:
    payload = load_json_file(path)
    series = payload.get("series")
    if not isinstance(series, dict):
        raise ValueError("series source file must include a series object")
    return payload


def refresh_lookup_payloads(context: CatalogueWriteContext) -> dict[str, Any]:
    result = lookup_refresh.full_lookup_refresh(context.source_dir, context.lookup_dir, context.repo_root)
    result["semantic_target_lookup"] = refresh_semantic_target_lookup(context)
    log_event(
        context.repo_root,
        "catalogue_lookup_refresh",
        {
            "lookup_dir": context.rel_path(context.lookup_dir),
            "mode": result["mode"],
            "artifacts": result["artifacts"],
            "written_count": result["written_count"],
        },
    )
    return result


def refresh_lookup_payloads_for_work_change(
    context: CatalogueWriteContext,
    work_id: str,
    current_record: Mapping[str, Any],
    updated_record: Mapping[str, Any],
    build_plan: Mapping[str, Any],
) -> dict[str, Any]:
    lookup_plan = lookup_refresh.derive_lookup_refresh_plan(
        record_family="work",
        changed_field_names=list(build_plan.get("fields") or []),
        build_plan=build_plan,
    )
    result = lookup_refresh.work_change_lookup_refresh(
        context.source_dir,
        context.lookup_dir,
        context.repo_root,
        work_id=work_id,
        current_record=current_record,
        updated_record=updated_record,
        lookup_plan=lookup_plan,
    )
    result["semantic_target_lookup"] = refresh_semantic_target_lookup(context)
    log_event(
        context.repo_root,
        "catalogue_lookup_refresh",
        {
            "lookup_dir": context.rel_path(context.lookup_dir),
            "mode": result["mode"],
            "work_id": work_id,
            "artifacts": result["artifacts"],
            "written_count": result["written_count"],
        },
    )
    return result


def refresh_lookup_payloads_for_detail_change(
    context: CatalogueWriteContext,
    detail_uid: str,
    current_record: Mapping[str, Any],
    updated_record: Mapping[str, Any],
    build_plan: Mapping[str, Any],
) -> dict[str, Any]:
    lookup_plan = lookup_refresh.derive_lookup_refresh_plan(
        record_family="work_detail",
        changed_field_names=list(build_plan.get("fields") or []),
        build_plan=build_plan,
    )
    result = lookup_refresh.detail_change_lookup_refresh(
        context.source_dir,
        context.lookup_dir,
        context.repo_root,
        detail_uid=detail_uid,
        updated_record=updated_record,
        lookup_plan=lookup_plan,
    )
    result["semantic_target_lookup"] = refresh_semantic_target_lookup(context)
    log_event(
        context.repo_root,
        "catalogue_lookup_refresh",
        {
            "lookup_dir": context.rel_path(context.lookup_dir),
            "mode": result["mode"],
            "detail_uid": detail_uid,
            "artifacts": result["artifacts"],
            "written_count": result["written_count"],
        },
    )
    return result


def refresh_lookup_payloads_for_series_change(
    context: CatalogueWriteContext,
    series_id: str,
    fields_changed: list[str],
    build_plan: Mapping[str, Any],
) -> dict[str, Any]:
    lookup_plan = lookup_refresh.derive_lookup_refresh_plan(
        record_family="series",
        changed_field_names=list(build_plan.get("fields") or fields_changed),
        build_plan=build_plan,
    )
    result = lookup_refresh.series_change_lookup_refresh(
        context.source_dir,
        context.lookup_dir,
        context.repo_root,
        series_id=series_id,
        lookup_plan=lookup_plan,
    )
    result["semantic_target_lookup"] = refresh_semantic_target_lookup(context)
    log_event(
        context.repo_root,
        "catalogue_lookup_refresh",
        {
            "lookup_dir": context.rel_path(context.lookup_dir),
            "mode": result["mode"],
            "series_id": series_id,
            "artifacts": result["artifacts"],
            "written_count": result["written_count"],
        },
    )
    return result


def refresh_semantic_target_lookup(context: CatalogueWriteContext) -> dict[str, Any]:
    build_dir = context.repo_root / "docs-viewer" / "build"
    if str(build_dir) not in sys.path:
        sys.path.insert(0, str(build_dir))
    from docs_builder.semantic_target_lookup import SemanticTargetLookupBuilder  # noqa: PLC0415

    result = SemanticTargetLookupBuilder(repo_root=context.repo_root).run(write=not context.dry_run)
    diagnostics = dict(result["diagnostics"])
    log_event(
        context.repo_root,
        "semantic_target_lookup_refresh",
        diagnostics,
    )
    return diagnostics


def lookup_refresh_response_for_plan(lookup_plan: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "mode": lookup_plan["mode"],
        "invalidation_class": lookup_plan["class"],
        "artifacts": lookup_plan["artifacts"],
        "unknown_fields": lookup_plan["unknown_fields"],
    }


def focused_lookup_refresh_response(refresh_result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "mode": refresh_result["mode"],
        "invalidation_class": refresh_result["invalidation_class"],
        "artifacts": refresh_result["artifacts"],
        "unknown_fields": refresh_result["unknown_fields"],
        "written_count": refresh_result["written_count"],
    }


def extract_apply_build(body: Mapping[str, Any]) -> bool:
    return bool(body.get("apply_build"))


def log_event(repo_root: Path, event: str, details: Mapping[str, Any] | None = None) -> None:
    try:
        append_script_log(
            Path(__file__),
            event=event,
            details=details,
            repo_root=repo_root,
            log_dir_rel=LOGS_REL_DIR,
        )
    except Exception:
        pass


def append_activity_rows(repo_root: Path, response_payload: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    try:
        append_studio_activity(repo_root, rows)
    except Exception:
        pass
    activity.increment_studio_activity_count(response_payload, len(rows))
