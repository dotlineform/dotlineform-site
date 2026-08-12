#!/usr/bin/env python3
"""Plan, apply, and validate the one-time Apple Notes Projects migration."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import urlsplit


MIGRATIONS_DIR = Path(__file__).resolve().parent
REPO_ROOT = MIGRATIONS_DIR.parents[1]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
for module_dir in (SERVICES_DIR, SHARED_PYTHON_DIR):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

import docs_source_model as source_model  # noqa: E402
import docs_write_rebuild as write_rebuild  # noqa: E402
from docs_artifact_locations import local_artifact_path  # noqa: E402
from docs_document_identity import allocate_doc_id, current_doc_timestamp  # noqa: E402
from docs_import_content import (  # noqa: E402
    CONTENT_FORMAT_MARKDOWN,
    CONTENT_INTENT_REPLACE,
    ImportContent,
)
from docs_import_document import (  # noqa: E402
    IMPORT_DOCUMENT_CREATE,
    ImportDocumentMediaContext,
    ImportDocumentPlan,
    materialize_import_document_media,
    plan_import_document,
)
from docs_import_markdown_package import (  # noqa: E402
    MARKDOWN_IMAGE_REWRITE_PATTERN,
    MARKDOWN_LINK_REWRITE_PATTERN,
    normalize_apple_notes_caption_spans,
    rewrite_markdown_package_media_links,
)
from docs_import_media import convert_package_image_to_webp  # noqa: E402
from docs_import_preview import (  # noqa: E402
    build_markdown_summary,
    normalize_ordinary_markdown_front_matter,
    validate_markdown_preview,
)
from docs_management_document_target import (  # noqa: E402
    ManagedDocumentCollection,
    resolve_managed_document_collection,
    source_doc_from_path,
)
from docs_media_storage import docs_media_file, publish_docs_media_files  # noqa: E402
from docs_scope_config import (  # noqa: E402
    DOCS_SCOPE_CONFIGS,
    DOCUMENT_SOURCE_ROOTS,
    document_source_path,
    load_docs_scope_configs,
    publication_documents_path,
    managed_media_config,
    resolve_scope_path,
)
from local_env import runtime_env  # noqa: E402


SCOPE = "dotlineform"
SUB_SCOPE = "projects"
PLAN_SCHEMA = "dotlineform_project_notes_migration_v1"
MAPPING_SCHEMA = "dotlineform_project_notes_folder_mapping_v1"
RECEIPT_SCHEMA = "dotlineform_project_notes_migration_receipt_v1"
EXPORT_RELATIVE_PATH = Path(
    "Notes export - 2026-05-18/iCloud/dotlineform/projects"
)
CURRENT_FOLDERS_RELATIVE_PATH = Path("projects")
DEFAULT_ARTIFACTS_PATH = Path("var/docs/dotlineform-project-notes-migration")
MAPPING_DECISIONS = {"exact_match", "mapped", "no_current_folder", "review_required"}
MARKDOWN_SUFFIXES = {".md", ".markdown"}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
MEDIA_TOKEN_PATTERN = re.compile(r"\[\[media:[^\]]+\]\]")


@dataclass(frozen=True)
class MigrationPaths:
    repo_root: Path
    projects_base: Path
    export_root: Path
    current_folders_root: Path
    artifacts_dir: Path
    mapping_path: Path
    plan_path: Path
    plan_report_path: Path
    receipt_path: Path
    result_report_path: Path

    @classmethod
    def resolve(
        cls,
        repo_root: Path,
        *,
        projects_base: Path | None = None,
        artifacts_dir: Path | None = None,
    ) -> "MigrationPaths":
        base = projects_base
        if base is None:
            raw_base = os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR", "").strip()
            if not raw_base:
                raise ValueError("DOTLINEFORM_PROJECTS_BASE_DIR is required")
            base = Path(raw_base)
        resolved_repo = repo_root.resolve()
        resolved_base = base.resolve()
        resolved_artifacts = (
            artifacts_dir.resolve()
            if artifacts_dir is not None
            else (resolved_repo / DEFAULT_ARTIFACTS_PATH).resolve()
        )
        return cls(
            repo_root=resolved_repo,
            projects_base=resolved_base,
            export_root=resolved_base / EXPORT_RELATIVE_PATH,
            current_folders_root=resolved_base / CURRENT_FOLDERS_RELATIVE_PATH,
            artifacts_dir=resolved_artifacts,
            mapping_path=resolved_artifacts / "folder-mapping.json",
            plan_path=resolved_artifacts / "plan.json",
            plan_report_path=resolved_artifacts / "plan-report.md",
            receipt_path=resolved_artifacts / "receipt.json",
            result_report_path=resolved_artifacts / "result-report.md",
        )


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(payload: str) -> str:
    return _sha256_bytes(payload.encode("utf-8"))


def _canonical_sha256(payload: Any) -> str:
    return _sha256_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must contain one JSON object")
    return payload


def _write_text(path: Path, text: str) -> None:
    source_model.write_text_atomic(path, text)


def _write_new_or_exact(path: Path, text: str) -> None:
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise FileExistsError(f"refusing to replace existing {path.name}")
        return
    source_model.write_text_atomic_new(path, text)


def _marker_path(paths: MigrationPaths, path: Path) -> str:
    resolved = path.resolve()
    if resolved == paths.projects_base:
        return "$DOTLINEFORM_PROJECTS_BASE_DIR"
    if resolved.is_relative_to(paths.projects_base):
        relative = resolved.relative_to(paths.projects_base).as_posix()
        return f"$DOTLINEFORM_PROJECTS_BASE_DIR/{relative}"
    if resolved.is_relative_to(paths.repo_root):
        return resolved.relative_to(paths.repo_root).as_posix()
    raise ValueError(f"migration path is outside its allowed roots: {path}")


def _resolve_marker_path(paths: MigrationPaths, marker: str) -> Path:
    prefix = "$DOTLINEFORM_PROJECTS_BASE_DIR/"
    if marker == "$DOTLINEFORM_PROJECTS_BASE_DIR":
        return paths.projects_base
    if marker.startswith(prefix):
        candidate = (paths.projects_base / marker[len(prefix) :]).resolve()
        if candidate.is_relative_to(paths.projects_base):
            return candidate
    candidate = (paths.repo_root / marker).resolve()
    if candidate.is_relative_to(paths.repo_root):
        return candidate
    raise ValueError(f"invalid migration marker path: {marker!r}")


def _refresh_scope_registry(repo_root: Path) -> None:
    configs = load_docs_scope_configs(repo_root)
    DOCS_SCOPE_CONFIGS.clear()
    DOCS_SCOPE_CONFIGS.update(configs)
    DOCUMENT_SOURCE_ROOTS.clear()
    DOCUMENT_SOURCE_ROOTS.update(
        {scope: document_source_path(config) for scope, config in configs.items()}
    )


def _require_roots(paths: MigrationPaths) -> None:
    if not paths.export_root.is_dir():
        raise FileNotFoundError(f"Apple Notes export root was not found: {paths.export_root}")
    if not paths.current_folders_root.is_dir():
        raise FileNotFoundError(
            f"current Projects folder root was not found: {paths.current_folders_root}"
        )
    for root in (paths.export_root, paths.current_folders_root):
        if root.is_symlink():
            raise ValueError(f"migration root must not be a symlink: {root}")


def _file_inventory(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise ValueError(
                f"migration input must not contain symlinks: {candidate.relative_to(root)}"
            )
        if not candidate.is_file():
            continue
        payload = candidate.read_bytes()
        records.append(
            {
                "relative_path": candidate.relative_to(root).as_posix(),
                "size_bytes": len(payload),
                "sha256": _sha256_bytes(payload),
            }
        )
    return sorted(records, key=lambda row: (str(row["relative_path"]).casefold(), str(row["relative_path"])))


def _current_folder_inventory(paths: MigrationPaths) -> list[str]:
    folders: list[str] = []
    for candidate in paths.current_folders_root.iterdir():
        if candidate.is_symlink():
            raise ValueError(f"current Project folder must not be a symlink: {candidate.name}")
        if candidate.is_dir():
            folders.append(candidate.name)
    return sorted(folders, key=lambda name: (name.casefold(), name))


def _markdown_records(paths: MigrationPaths, export_inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for inventory in export_inventory:
        relative = Path(str(inventory["relative_path"]))
        if relative.suffix.lower() not in MARKDOWN_SUFFIXES:
            continue
        if len(relative.parts) < 2:
            raise ValueError(
                f"Markdown source is not beneath one exported Project folder: {relative.as_posix()}"
            )
        records.append(
            {
                **inventory,
                "export_folder": relative.parts[0],
                "source_path": _marker_path(paths, paths.export_root / relative),
            }
        )
    if not records:
        raise ValueError("Apple Notes export contains no Markdown files")
    return records


def _collection_docs(collection: ManagedDocumentCollection) -> list[source_model.ScopeDoc]:
    return [
        source_doc_from_path(path=path, scope=collection.scope)
        for path in source_model.scope_markdown_paths(collection.source_root)
    ]


def _source_inventory(paths: MigrationPaths, collection: ManagedDocumentCollection) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for doc in _collection_docs(collection):
        payload = doc.path.read_bytes()
        records.append(
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "folder_path": str(doc.front_matter.get("folder_path") or "").strip(),
                "source_path": _marker_path(paths, doc.path),
                "source_sha256": _sha256_bytes(payload),
            }
        )
    return sorted(records, key=lambda row: str(row["doc_id"]))


def _mapping_seed(
    markdown_records: list[dict[str, Any]],
    current_folders: list[str],
    *,
    export_sha256: str,
    current_folders_sha256: str,
) -> dict[str, Any]:
    current = set(current_folders)
    export_folders = sorted(
        {str(record["export_folder"]) for record in markdown_records},
        key=lambda name: (name.casefold(), name),
    )
    return {
        "schema": MAPPING_SCHEMA,
        "export_inventory_sha256": export_sha256,
        "current_folders_inventory_sha256": current_folders_sha256,
        "folders": [
            {
                "export_folder": folder,
                "decision": "exact_match" if folder in current else "review_required",
                "folder_path": f"projects/{folder}" if folder in current else "",
            }
            for folder in export_folders
        ],
    }


def _validate_mapping(
    payload: dict[str, Any],
    markdown_records: list[dict[str, Any]],
    current_folders: list[str],
    *,
    export_sha256: str,
    current_folders_sha256: str,
) -> dict[str, str]:
    if payload.get("schema") != MAPPING_SCHEMA:
        raise ValueError(f"folder mapping must use schema {MAPPING_SCHEMA}")
    if payload.get("export_inventory_sha256") != export_sha256:
        raise ValueError("folder mapping export inventory hash no longer matches")
    if payload.get("current_folders_inventory_sha256") != current_folders_sha256:
        raise ValueError("folder mapping current-folder inventory hash no longer matches")
    rows = payload.get("folders")
    if not isinstance(rows, list):
        raise ValueError("folder mapping folders must be an array")
    expected = {str(record["export_folder"]) for record in markdown_records}
    current = set(current_folders)
    decisions: dict[str, str] = {}
    seen: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict) or set(raw) != {"export_folder", "decision", "folder_path"}:
            raise ValueError(f"folder mapping folders[{index}] has unexpected fields")
        folder = raw.get("export_folder")
        decision = raw.get("decision")
        folder_path = raw.get("folder_path")
        if not all(isinstance(value, str) for value in (folder, decision, folder_path)):
            raise ValueError(f"folder mapping folders[{index}] values must be strings")
        assert isinstance(folder, str) and isinstance(decision, str) and isinstance(folder_path, str)
        if folder in seen or folder not in expected:
            raise ValueError(f"folder mapping has unexpected or duplicate export folder {folder!r}")
        seen.add(folder)
        if decision not in MAPPING_DECISIONS:
            raise ValueError(f"folder mapping decision is invalid for {folder!r}")
        exact_path = f"projects/{folder}"
        if decision == "exact_match":
            if folder not in current or folder_path != exact_path:
                raise ValueError(f"exact_match is no longer exact for {folder!r}")
        elif decision == "mapped":
            if not folder_path.startswith("projects/") or folder_path[9:] not in current:
                raise ValueError(f"mapped folder_path is not a current direct Project folder for {folder!r}")
        elif decision in {"no_current_folder", "review_required"} and folder_path:
            raise ValueError(f"{decision} requires a blank folder_path for {folder!r}")
        decisions[folder] = folder_path if decision != "review_required" else "__REVIEW_REQUIRED__"
    if seen != expected:
        raise ValueError("folder mapping does not exactly cover exported Project folders")
    return decisions


def _link_exceptions(markdown: str) -> list[dict[str, str]]:
    exceptions: list[dict[str, str]] = [
        {"kind": "media_token", "target": match.group(0), "scheme": "media"}
        for match in MEDIA_TOKEN_PATTERN.finditer(markdown)
    ]
    matches = [
        ("image", match.group("target"))
        for match in MARKDOWN_IMAGE_REWRITE_PATTERN.finditer(markdown)
    ] + [
        ("link", match.group("target"))
        for match in MARKDOWN_LINK_REWRITE_PATTERN.finditer(markdown)
    ]
    for kind, raw_target in matches:
        target = str(raw_target or "").strip()
        scheme = urlsplit(target).scheme.lower()
        if not scheme or scheme in {"http", "https"} or target.startswith("#"):
            continue
        exceptions.append({"kind": kind, "target": target, "scheme": scheme})
    return exceptions


def _import_content_from_dict(payload: dict[str, Any]) -> ImportContent:
    values = copy.deepcopy(payload)
    for field in ("links", "assets", "diagnostics"):
        raw = values.get(field, [])
        if not isinstance(raw, list) or any(not isinstance(item, dict) for item in raw):
            raise ValueError(f"stored ImportContent {field} must be an array of objects")
        values[field] = tuple(raw)
    return ImportContent(**values)


def _prepare_media_output(package_root: Path, media_plan: dict[str, Any], target: Path) -> None:
    relative = str(media_plan.get("package_relative_source_path") or "")
    source_path = (package_root / relative).resolve()
    if not relative or not source_path.is_relative_to(package_root.resolve()) or not source_path.is_file():
        raise ValueError(f"planned media source is unavailable: {relative!r}")
    target.parent.mkdir(parents=True, exist_ok=True)
    source_kind = str(media_plan.get("source") or "")
    if source_kind == "markdown_package_image":
        conversion = media_plan.get("conversion")
        if not isinstance(conversion, dict):
            raise ValueError("planned image conversion is missing")
        convert_package_image_to_webp(
            source_path,
            target,
            max_width=int(conversion.get("max_width") or 800),
        )
    elif source_kind == "markdown_package_attachment":
        target.write_bytes(source_path.read_bytes())
    else:
        raise ValueError(f"unsupported migration media source kind: {source_kind!r}")


def _plan_document(
    paths: MigrationPaths,
    collection: ManagedDocumentCollection,
    docs: list[source_model.ScopeDoc],
    markdown_record: dict[str, Any],
    *,
    folder_path: str,
    doc_id: str,
    added_date: str,
) -> dict[str, Any]:
    markdown_path = _resolve_marker_path(paths, str(markdown_record["source_path"]))
    relative = markdown_path.relative_to(paths.export_root)
    package_root = paths.export_root / relative.parts[0]
    raw_markdown = markdown_path.read_text(encoding="utf-8", errors="replace")
    caption_normalized = normalize_apple_notes_caption_spans(raw_markdown)
    normalized, front_matter_title, diagnostics, warnings = normalize_ordinary_markdown_front_matter(
        caption_normalized,
        source_name=relative.as_posix(),
    )
    summary = build_markdown_summary(
        normalized,
        markdown_path.stem,
        front_matter_title=front_matter_title,
    )
    summary["warnings"].extend(warnings)
    if diagnostics is not None:
        diagnostics["title_used"] = summary["title_source"] == "front_matter"
        summary["front_matter"] = diagnostics
    summary.update(
        {
            "scope": SCOPE,
            "source_format": "markdown_package",
            "source_path": str(markdown_record["source_path"]),
            "proposed_doc_id": doc_id,
            "proposed_doc_id_source": "migration-plan",
        }
    )
    provenance_label = (
        "$DOTLINEFORM_PROJECTS_BASE_DIR/"
        + (EXPORT_RELATIVE_PATH / relative.parts[0]).as_posix()
    )
    rewrite_markdown_package_media_links(
        paths.repo_root,
        staging_root=paths.export_root,
        workspace_root=paths.projects_base,
        package_root=package_root,
        markdown_path=markdown_path,
        summary=summary,
        scope=SCOPE,
        provenance_label=provenance_label,
    )
    summary["validation"] = validate_markdown_preview(
        str(summary["markdown_preview"]),
        title=str(summary["title"]),
    )
    raw_media_plans = summary.get("media_plans", [])
    if not isinstance(raw_media_plans, list) or any(not isinstance(item, dict) for item in raw_media_plans):
        raise ValueError(f"media plan is malformed for {relative.as_posix()}")
    media_plans = [copy.deepcopy(item) for item in raw_media_plans]
    record = ImportContent(
        source_kind="apple-notes-project-export",
        source_identity=str(markdown_record["source_path"]),
        record_identity=relative.as_posix(),
        doc_id=doc_id,
        title=str(summary["title"]),
        content_intent=CONTENT_INTENT_REPLACE,
        content_format=CONTENT_FORMAT_MARKDOWN,
        content=str(summary["markdown_preview"]),
        front_matter={"title": str(summary["title"])},
        assets=tuple(copy.deepcopy(media_plans)),
        diagnostics=tuple(
            {"level": "warning", "message": warning}
            for warning in summary.get("warnings", [])
            if isinstance(warning, str)
        ),
        provenance={
            "source_path": str(markdown_record["source_path"]),
            "source_sha256": str(markdown_record["sha256"]),
        },
    )
    document_plan = plan_import_document(
        paths.repo_root,
        SCOPE,
        record,
        operation=IMPORT_DOCUMENT_CREATE,
        docs=docs,
        import_preview=summary,
        create_doc_id=doc_id,
        create_added_date=added_date,
        collection=collection,
        custom_front_matter={"folder_path": folder_path} if folder_path else {},
    )
    media_records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="project-notes-plan-media-") as temp_dir:
        temp_root = Path(temp_dir)
        for media_plan in media_plans:
            filename = str(media_plan.get("source_path") or "")
            media_class = str(media_plan.get("media_class") or "")
            target = temp_root / media_class / filename
            _prepare_media_output(package_root, media_plan, target)
            input_relative = str(media_plan.get("package_relative_source_path") or "")
            input_path = (package_root / input_relative).resolve()
            media_records.append(
                {
                    "plan": media_plan,
                    "input_relative_path": input_relative,
                    "input_sha256": _sha256_bytes(input_path.read_bytes()),
                    "input_size_bytes": input_path.stat().st_size,
                    "output_sha256": _sha256_bytes(target.read_bytes()),
                    "output_size_bytes": target.stat().st_size,
                }
            )
    return {
        "export_relative_path": relative.as_posix(),
        "export_folder": relative.parts[0],
        "folder_path": folder_path,
        "doc_id": document_plan.doc_id,
        "added_date": added_date,
        "title": document_plan.title,
        "title_source": summary["title_source"],
        "source_input_sha256": str(markdown_record["sha256"]),
        "target_source_path": _marker_path(paths, document_plan.target_path),
        "target_source_sha256": _sha256_text(document_plan.source_text),
        "source_text": document_plan.source_text,
        "import_content": document_plan.record.as_dict(),
        "import_preview": document_plan.import_preview,
        "media": media_records,
        "exceptions": [
            *_link_exceptions(raw_markdown),
            *(
                {
                    "kind": "warning",
                    "target": warning,
                    "scheme": "local",
                }
                for warning in summary.get("warnings", [])
                if isinstance(warning, str) and "package" in warning.lower()
            ),
        ],
    }


def _plan_revision(plan: dict[str, Any]) -> str:
    payload = copy.deepcopy(plan)
    payload.pop("plan_revision", None)
    return _canonical_sha256(payload)


def _validate_plan_object(plan: dict[str, Any]) -> None:
    if plan.get("schema") != PLAN_SCHEMA:
        raise ValueError(f"migration plan must use schema {PLAN_SCHEMA}")
    revision = plan.get("plan_revision")
    if not isinstance(revision, str) or not SHA256_PATTERN.fullmatch(revision):
        raise ValueError("migration plan revision is invalid")
    if revision != _plan_revision(plan):
        raise ValueError("migration plan revision does not match its content")
    documents = plan.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("migration plan documents must be a non-empty array")
    identities: set[str] = set()
    relative_paths: list[str] = []
    for index, raw in enumerate(documents):
        if not isinstance(raw, dict):
            raise ValueError(f"migration plan documents[{index}] must be an object")
        doc_id = str(raw.get("doc_id") or "")
        relative = str(raw.get("export_relative_path") or "")
        if not source_model.is_immutable_doc_id(doc_id) or doc_id in identities:
            raise ValueError(f"migration plan has invalid or duplicate doc_id {doc_id!r}")
        if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError(f"migration plan has invalid export-relative path {relative!r}")
        identities.add(doc_id)
        relative_paths.append(relative)
        if _sha256_text(str(raw.get("source_text") or "")) != raw.get("target_source_sha256"):
            raise ValueError(f"migration plan source hash is invalid for {doc_id!r}")
    if relative_paths != sorted(relative_paths, key=lambda value: (value.casefold(), value)):
        raise ValueError("migration plan documents are not in stable export-relative order")


def _report_plan(plan: dict[str, Any] | None, *, blocked: Iterable[str] = ()) -> str:
    blocked_rows = list(blocked)
    lines = ["# dotlineform Project Notes Migration Plan", ""]
    if blocked_rows:
        lines.extend(["Status: blocked pending folder mapping review.", "", "## Review required", ""])
        lines.extend(f"- `{folder}`" for folder in blocked_rows)
        return "\n".join(lines) + "\n"
    assert plan is not None
    documents = list(plan["documents"])
    media_count = sum(len(document.get("media", [])) for document in documents)
    pathless = sum(not str(document.get("folder_path") or "") for document in documents)
    exceptions = sum(len(document.get("exceptions", [])) for document in documents)
    lines.extend(
        [
            "Status: final and identity-allocated.",
            "",
            f"- Documents: {len(documents)}",
            f"- Media objects: {media_count}",
            f"- Documents without a current folder: {pathless}",
            f"- Exceptional links retained for review: {exceptions}",
            f"- Plan revision: `{plan['plan_revision']}`",
            "",
            "Only `folder-mapping.json` is reviewer-editable. Do not edit `plan.json`.",
        ]
    )
    return "\n".join(lines) + "\n"


def plan_migration(
    paths: MigrationPaths,
    *,
    added_date: str | None = None,
    token_factory: Callable[[int], str] | None = None,
) -> dict[str, Any]:
    _require_roots(paths)
    _refresh_scope_registry(paths.repo_root)
    collection = resolve_managed_document_collection(
        paths.repo_root, scope=SCOPE, sub_scope=SUB_SCOPE
    )
    export_inventory = _file_inventory(paths.export_root)
    markdown_records = _markdown_records(paths, export_inventory)
    current_folders = _current_folder_inventory(paths)
    export_sha256 = _canonical_sha256(export_inventory)
    current_folders_sha256 = _canonical_sha256(current_folders)
    mapping_seed = _mapping_seed(
        markdown_records,
        current_folders,
        export_sha256=export_sha256,
        current_folders_sha256=current_folders_sha256,
    )
    if not paths.mapping_path.exists():
        _write_new_or_exact(paths.mapping_path, _json_text(mapping_seed))
    mapping = _load_object(paths.mapping_path, label="folder mapping")
    decisions = _validate_mapping(
        mapping,
        markdown_records,
        current_folders,
        export_sha256=export_sha256,
        current_folders_sha256=current_folders_sha256,
    )
    blocked = sorted(
        (folder for folder, value in decisions.items() if value == "__REVIEW_REQUIRED__"),
        key=lambda value: (value.casefold(), value),
    )
    if blocked:
        _write_text(paths.plan_report_path, _report_plan(None, blocked=blocked))
        return {"ok": False, "status": "review_required", "folders": blocked}

    mapping_bytes = paths.mapping_path.read_bytes()
    live_inputs = {
        "export_inventory_sha256": export_sha256,
        "current_folders_inventory_sha256": current_folders_sha256,
        "folder_mapping_sha256": _sha256_bytes(mapping_bytes),
    }
    if paths.plan_path.exists():
        existing = _load_object(paths.plan_path, label="migration plan")
        _validate_plan_object(existing)
        for field, value in live_inputs.items():
            if existing.get("inputs", {}).get(field) != value:
                raise ValueError(f"existing migration plan input {field} no longer matches")
        _validate_source_baseline(paths, existing, collection)
        _write_text(paths.plan_report_path, _report_plan(existing))
        return {"ok": True, "status": "planned", "plan": existing, "existing": True}

    baseline_sources = _source_inventory(paths, collection)
    inputs = {
        **live_inputs,
        "baseline_source_inventory_sha256": _canonical_sha256(baseline_sources),
    }
    operation_date = added_date or current_doc_timestamp()
    docs = _collection_docs(collection)
    unavailable = {identity for doc in docs for identity in (doc.doc_id, doc.path.stem)}
    documents: list[dict[str, Any]] = []
    for record in markdown_records:
        doc_id = allocate_doc_id(
            operation_date,
            unavailable,
            **({"token_factory": token_factory} if token_factory is not None else {}),
        )
        unavailable.add(doc_id)
        documents.append(
            _plan_document(
                paths,
                collection,
                docs,
                record,
                folder_path=decisions[str(record["export_folder"])],
                doc_id=doc_id,
                added_date=operation_date,
            )
        )
    documents.sort(
        key=lambda document: (
            str(document["export_relative_path"]).casefold(),
            str(document["export_relative_path"]),
        )
    )
    plan: dict[str, Any] = {
        "schema": PLAN_SCHEMA,
        "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": SCOPE,
        "sub_scope": SUB_SCOPE,
        "operation_added_date": operation_date,
        "source_root": _marker_path(paths, paths.export_root),
        "current_folders_root": _marker_path(paths, paths.current_folders_root),
        "inputs": inputs,
        "export_inventory": export_inventory,
        "current_folders": current_folders,
        "folder_mapping": mapping,
        "baseline_sources": baseline_sources,
        "documents": documents,
    }
    plan["plan_revision"] = _plan_revision(plan)
    _validate_plan_object(plan)
    _write_new_or_exact(paths.plan_path, _json_text(plan))
    _write_text(paths.plan_report_path, _report_plan(plan))
    return {"ok": True, "status": "planned", "plan": plan, "existing": False}


def _validate_live_inputs(paths: MigrationPaths, plan: dict[str, Any]) -> None:
    export_inventory = _file_inventory(paths.export_root)
    current_folders = _current_folder_inventory(paths)
    expected = plan["inputs"]
    if _canonical_sha256(export_inventory) != expected["export_inventory_sha256"]:
        raise ValueError("Apple Notes export inventory changed after planning")
    if _canonical_sha256(current_folders) != expected["current_folders_inventory_sha256"]:
        raise ValueError("current Project folders changed after planning")
    if _sha256_bytes(paths.mapping_path.read_bytes()) != expected["folder_mapping_sha256"]:
        raise ValueError("folder mapping changed after planning")
    for document in plan["documents"]:
        source = paths.export_root / str(document["export_relative_path"])
        if _sha256_bytes(source.read_bytes()) != document["source_input_sha256"]:
            raise ValueError(f"planned Markdown source changed: {document['export_relative_path']}")


def _validate_source_baseline(
    paths: MigrationPaths,
    plan: dict[str, Any],
    collection: ManagedDocumentCollection,
) -> None:
    planned_by_id = {str(document["doc_id"]): document for document in plan["documents"]}
    for doc_id, document in planned_by_id.items():
        target = _resolve_marker_path(paths, str(document["target_source_path"]))
        if target.exists() and (
            not target.is_file()
            or _sha256_bytes(target.read_bytes()) != document["target_source_sha256"]
        ):
            raise ValueError(f"planned source target differs for {doc_id!r}")
    current = _source_inventory(paths, collection)
    remaining: list[dict[str, Any]] = []
    for record in current:
        planned = planned_by_id.get(str(record["doc_id"]))
        if planned is None:
            remaining.append(record)
            continue
        if record["source_sha256"] != planned["target_source_sha256"]:
            raise ValueError(f"planned source target differs for {record['doc_id']!r}")
    if remaining != plan["baseline_sources"]:
        raise ValueError("Project source inventory changed outside byte-identical plan targets")
    if _canonical_sha256(remaining) != plan["inputs"]["baseline_source_inventory_sha256"]:
        raise ValueError("Project source baseline hash changed")


def _media_target(paths: MigrationPaths, plan_row: dict[str, Any]) -> Path:
    configs = load_docs_scope_configs(paths.repo_root)
    media_class = str(plan_row.get("media_class") or "")
    filename = str(plan_row.get("source_path") or "")
    target = local_artifact_path(
        paths.repo_root,
        managed_media_config(configs[SCOPE], media_class).location,
        filename,
    )
    if target is None:
        raise ValueError("Project Notes migration requires local Docs media locations")
    return target


def _media_exact(paths: MigrationPaths, media: dict[str, Any]) -> bool:
    target = _media_target(paths, media["plan"])
    return (
        target.is_file()
        and target.stat().st_size == media["output_size_bytes"]
        and _sha256_bytes(target.read_bytes()) == media["output_sha256"]
    )


def _prepare_complete_media_set(
    paths: MigrationPaths,
    plan: dict[str, Any],
    temp_root: Path,
) -> list[Any]:
    config = load_docs_scope_configs(paths.repo_root)[SCOPE]
    files = []
    seen: set[tuple[str, str]] = set()
    for document in plan["documents"]:
        package_root = paths.export_root / str(document["export_folder"])
        for media in document["media"]:
            media_plan = media["plan"]
            identity = (
                str(media_plan.get("media_class") or ""),
                str(media_plan.get("source_path") or ""),
            )
            if identity in seen:
                raise ValueError(f"migration plan duplicates media identity {identity}")
            seen.add(identity)
            prepared = temp_root / identity[0] / identity[1]
            _prepare_media_output(package_root, media_plan, prepared)
            if prepared.stat().st_size != media["output_size_bytes"] or _sha256_bytes(prepared.read_bytes()) != media["output_sha256"]:
                raise ValueError(f"planned media output changed: {identity[0]}/{identity[1]}")
            files.append(
                docs_media_file(
                    config,
                    media_class=identity[0],
                    local_path=prepared,
                    source_root=temp_root,
                    filename=identity[1],
                )
            )
    return files


def _receipt_seed(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": RECEIPT_SCHEMA,
        "plan_revision": plan["plan_revision"],
        "documents": {},
        "rebuild": {"status": "pending", "error": ""},
    }


def _load_receipt(paths: MigrationPaths, plan: dict[str, Any]) -> dict[str, Any]:
    if not paths.receipt_path.exists():
        receipt = _receipt_seed(plan)
        _write_new_or_exact(paths.receipt_path, _json_text(receipt))
        return receipt
    receipt = _load_object(paths.receipt_path, label="migration receipt")
    if receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("plan_revision") != plan["plan_revision"]:
        raise ValueError("migration receipt is not bound to this plan revision")
    if not isinstance(receipt.get("documents"), dict) or not isinstance(receipt.get("rebuild"), dict):
        raise ValueError("migration receipt is malformed")
    return receipt


def _stored_document_plan(
    paths: MigrationPaths,
    document: dict[str, Any],
) -> ImportDocumentPlan:
    record = _import_content_from_dict(document["import_content"])
    return ImportDocumentPlan(
        scope=SCOPE,
        sub_scope=SUB_SCOPE,
        operation=IMPORT_DOCUMENT_CREATE,
        record=record,
        target_path=_resolve_marker_path(paths, str(document["target_source_path"])),
        source_text=str(document["source_text"]),
        title=str(document["title"]),
        parent_id="",
        publishable=None,
        search_doc_ids=(),
        import_preview=copy.deepcopy(document["import_preview"]),
    )


def _document_exact(paths: MigrationPaths, document: dict[str, Any]) -> bool:
    target = _resolve_marker_path(paths, str(document["target_source_path"]))
    return target.is_file() and _sha256_bytes(target.read_bytes()) == document["target_source_sha256"]


def _write_receipt(paths: MigrationPaths, receipt: dict[str, Any]) -> None:
    _write_text(paths.receipt_path, _json_text(receipt))


def _result_report(plan: dict[str, Any], receipt: dict[str, Any], all_sources: list[dict[str, Any]]) -> str:
    by_folder: dict[str, list[str]] = {f"projects/{folder}": [] for folder in plan["current_folders"]}
    pathless: list[str] = []
    for source in all_sources:
        folder = str(source.get("folder_path") or "")
        label = f"{source['title']} (`{source['doc_id']}`)"
        if folder in by_folder:
            by_folder[folder].append(label)
        elif not folder:
            pathless.append(label)
    buckets = {"zero": [], "one": [], "many": []}
    for folder, labels in sorted(by_folder.items(), key=lambda item: item[0].casefold()):
        bucket = "zero" if not labels else "one" if len(labels) == 1 else "many"
        buckets[bucket].append((folder, labels))
    lines = ["# dotlineform Project Notes Migration Result", "", f"Plan revision: `{plan['plan_revision']}`", ""]
    for bucket in ("zero", "one", "many"):
        lines.extend([f"## Current folders with {bucket} documents", ""])
        if not buckets[bucket]:
            lines.append("- None")
        for folder, labels in buckets[bucket]:
            lines.append(f"- `{folder}`" + (f": {', '.join(labels)}" if labels else ""))
        lines.append("")
    lines.extend(["## Documents without a current folder", ""])
    lines.extend(f"- {label}" for label in pathless or ["None"])
    lines.extend(["", "## Exceptional material", ""])
    exceptions = [
        (document["export_relative_path"], exception)
        for document in plan["documents"]
        for exception in document.get("exceptions", [])
    ]
    if not exceptions:
        lines.append("- None")
    else:
        for relative, exception in exceptions:
            lines.append(
                f"- `{relative}`: {exception['kind']} `{exception['target']}` ({exception['scheme']})"
            )
    explicit_pathless = [
        document
        for document in plan["documents"]
        if not str(document.get("folder_path") or "")
    ]
    lines.extend(["", "## Explicit no-current-folder imports", ""])
    if not explicit_pathless:
        lines.append("- None")
    else:
        lines.extend(
            f"- `{document['export_relative_path']}` -> `{document['doc_id']}`"
            for document in explicit_pathless
        )
    lines.extend(["", "## Untouched baseline documents", ""])
    if not plan["baseline_sources"]:
        lines.append("- None")
    else:
        lines.extend(
            f"- {source['title']} (`{source['doc_id']}`)"
            for source in plan["baseline_sources"]
        )
    lines.extend(
        [
            "",
            "## Apply receipt",
            "",
            f"- Committed documents: {len(receipt['documents'])}",
            f"- Rebuild: {receipt['rebuild'].get('status', '')}",
            "- No repair or consolidation was performed.",
        ]
    )
    return "\n".join(lines) + "\n"


def apply_migration(paths: MigrationPaths) -> dict[str, Any]:
    _require_roots(paths)
    _refresh_scope_registry(paths.repo_root)
    plan = _load_object(paths.plan_path, label="migration plan")
    _validate_plan_object(plan)
    _validate_live_inputs(paths, plan)
    collection = resolve_managed_document_collection(paths.repo_root, scope=SCOPE, sub_scope=SUB_SCOPE)
    _validate_source_baseline(paths, plan, collection)

    with tempfile.TemporaryDirectory(prefix="project-notes-preflight-") as temp_dir:
        media_files = _prepare_complete_media_set(paths, plan, Path(temp_dir))
        preflight = publish_docs_media_files(
            paths.repo_root, media_files, write=False, force=False
        )
    blocked = [
        result
        for result in preflight
        if result.status not in {"unchanged", "would_upload"}
    ]
    if blocked:
        detail = ", ".join(
            f"{result.media_class}/{result.filename}: {result.status}" for result in blocked
        )
        raise RuntimeError(f"complete migration media preflight did not pass: {detail}")

    receipt = _load_receipt(paths, plan)
    if receipt["rebuild"].get("status") != "complete":
        rebuild_only = receipt["rebuild"].get("status") == "failed"
        if rebuild_only:
            for document in plan["documents"]:
                doc_id = str(document["doc_id"])
                if (
                    receipt["documents"].get(doc_id, {}).get("status") != "complete"
                    or not _document_exact(paths, document)
                    or not all(_media_exact(paths, media) for media in document["media"])
                ):
                    raise ValueError(
                        "failed-rebuild resume requires every planned document and media target to remain exact"
                    )
        if not rebuild_only:
            for document in plan["documents"]:
                doc_id = str(document["doc_id"])
                target = _resolve_marker_path(paths, str(document["target_source_path"]))
                source_exists = target.exists()
                source_exact = _document_exact(paths, document)
                if source_exists and not source_exact:
                    raise ValueError(f"planned source target differs for {doc_id!r}")
                media_exact = all(_media_exact(paths, media) for media in document["media"])
                if not source_exact or not media_exact:
                    stored_plan = _stored_document_plan(paths, document)
                    if not source_exact:
                        current_docs = _collection_docs(collection)
                        replanned = plan_import_document(
                            paths.repo_root,
                            SCOPE,
                            _import_content_from_dict(document["import_content"]),
                            operation=IMPORT_DOCUMENT_CREATE,
                            docs=current_docs,
                            import_preview=copy.deepcopy(document["import_preview"]),
                            create_doc_id=doc_id,
                            create_added_date=str(document["added_date"]),
                            collection=collection,
                            custom_front_matter=(
                                {"folder_path": str(document["folder_path"])}
                                if document.get("folder_path")
                                else {}
                            ),
                        )
                        if replanned.source_text != document["source_text"]:
                            raise ValueError(f"stored import plan no longer reproduces source {doc_id!r}")
                        stored_plan = replanned
                    package_root = paths.export_root / str(document["export_folder"])
                    materialize_import_document_media(
                        paths.repo_root,
                        stored_plan,
                        media_context=ImportDocumentMediaContext(
                            staging_root=paths.export_root,
                            workspace_root=paths.projects_base,
                            source_path=package_root,
                        ),
                    )
                    if not source_exact:
                        source_model.write_text_atomic_new(target, str(document["source_text"]))
                if not _document_exact(paths, document) or not all(
                    _media_exact(paths, media) for media in document["media"]
                ):
                    raise RuntimeError(f"migration target did not verify for {doc_id!r}")
                receipt["documents"][doc_id] = {
                    "status": "complete",
                    "source_sha256": document["target_source_sha256"],
                    "media": [
                        {
                            "media_class": media["plan"]["media_class"],
                            "filename": media["plan"]["source_path"],
                            "sha256": media["output_sha256"],
                        }
                        for media in document["media"]
                    ],
                }
                _write_receipt(paths, receipt)

        try:
            write_rebuild.rebuild_sub_scope_outputs(paths.repo_root, SCOPE, SUB_SCOPE)
        except Exception as exc:
            receipt["rebuild"] = {"status": "failed", "error": str(exc)}
            _write_receipt(paths, receipt)
            _write_text(
                paths.result_report_path,
                _result_report(plan, receipt, _source_inventory(paths, collection)),
            )
            raise
        receipt["rebuild"] = {"status": "complete", "error": ""}
        _write_receipt(paths, receipt)

    result_report = _result_report(plan, receipt, _source_inventory(paths, collection))
    _write_text(paths.result_report_path, result_report)
    return {
        "ok": True,
        "status": "applied",
        "plan_revision": plan["plan_revision"],
        "documents": len(plan["documents"]),
        "rebuild": receipt["rebuild"]["status"],
    }


def _manifest_rows(path: Path) -> dict[str, dict[str, Any]]:
    payload = _load_object(path, label=path.name)
    rows = payload.get("docs")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"{path.name} docs must be an array of objects")
    return {str(row.get("doc_id") or ""): row for row in rows}


def validate_migration(paths: MigrationPaths) -> dict[str, Any]:
    _require_roots(paths)
    _refresh_scope_registry(paths.repo_root)
    plan = _load_object(paths.plan_path, label="migration plan")
    _validate_plan_object(plan)
    _validate_live_inputs(paths, plan)
    collection = resolve_managed_document_collection(paths.repo_root, scope=SCOPE, sub_scope=SUB_SCOPE)
    _validate_source_baseline(paths, plan, collection)
    receipt = _load_object(paths.receipt_path, label="migration receipt")
    if receipt.get("schema") != RECEIPT_SCHEMA or receipt.get("plan_revision") != plan["plan_revision"]:
        raise ValueError("migration receipt is not bound to this plan")
    if receipt.get("rebuild", {}).get("status") != "complete":
        raise ValueError("migration rebuild is not complete")
    for document in plan["documents"]:
        doc_id = str(document["doc_id"])
        if not _document_exact(paths, document):
            raise ValueError(f"migration source does not verify for {doc_id!r}")
        if not all(_media_exact(paths, media) for media in document["media"]):
            raise ValueError(f"migration media does not verify for {doc_id!r}")
        receipt_row = receipt.get("documents", {}).get(doc_id, {})
        expected_media = [
            {
                "media_class": media["plan"]["media_class"],
                "filename": media["plan"]["source_path"],
                "sha256": media["output_sha256"],
            }
            for media in document["media"]
        ]
        if (
            receipt_row.get("status") != "complete"
            or receipt_row.get("source_sha256") != document["target_source_sha256"]
            or receipt_row.get("media") != expected_media
        ):
            raise ValueError(f"migration receipt is incomplete for {doc_id!r}")

    output_root = resolve_scope_path(
        paths.repo_root, publication_documents_path(collection.document_config)
    )
    public_rows = _manifest_rows(output_root / "manifest.json")
    manage_rows = _manifest_rows(output_root / "manage-manifest.json")
    for document in plan["documents"]:
        doc_id = str(document["doc_id"])
        if public_rows.get(doc_id, {}).get("title") != document["title"]:
            raise ValueError(f"public manifest does not match planned title for {doc_id!r}")
        manage = manage_rows.get(doc_id, {})
        if manage.get("title") != document["title"]:
            raise ValueError(f"manage manifest does not match planned title for {doc_id!r}")
        folder_path = str(document.get("folder_path") or "")
        custom = manage.get("customisation")
        if folder_path:
            if custom != {"folder_path": folder_path}:
                raise ValueError(f"manage manifest folder_path does not match for {doc_id!r}")
        elif custom is not None:
            raise ValueError(f"pathless manage manifest row carries customisation for {doc_id!r}")
    return {
        "ok": True,
        "status": "validated",
        "plan_revision": plan["plan_revision"],
        "documents": len(plan["documents"]),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--validate", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        os.environ.update(runtime_env(repo_root=args.repo_root))
        paths = MigrationPaths.resolve(args.repo_root)
        if args.plan:
            result = plan_migration(paths)
        elif args.apply:
            result = apply_migration(paths)
        else:
            result = validate_migration(paths)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Project Notes migration failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({key: value for key, value in result.items() if key != "plan"}, indent=2))
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
