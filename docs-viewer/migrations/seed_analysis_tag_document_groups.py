#!/usr/bin/env python3
"""Plan, apply, and validate the one-time Analysis tag document group seed."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


MIGRATIONS_DIR = Path(__file__).resolve().parent
REPO_ROOT = MIGRATIONS_DIR.parents[1]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
for module_dir in (DOCS_SERVICES_DIR, STUDIO_SERVICES_DIR):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

import docs_source_model as source_model  # noqa: E402
from tags import tag_source_model as tag_source  # noqa: E402


PLAN_SCHEMA = "analysis_tag_document_group_seed_v1"
SOURCE_REGISTRY_VERSION = "tag_registry_v4"
BOOTSTRAP_ADDED_DATE = "2026-07-27 22:56:08"
EXPECTED_BOOTSTRAP_DOCUMENTS = 245
EXPECTED_INDEPENDENT_DOCUMENTS = 3
REGISTRY_PATH = Path("studio/data/canonical/tags/tag-registry.json")
SCOPES_CONFIG_PATH = Path("docs-viewer/config/scopes/docs_scopes.json")
DOCUMENTS_ROOT = Path(
    "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
)
DEFAULT_PLAN_PATH = Path(
    "var/docs/analysis-tag-document-group-seed/plan.json"
)


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(payload: str) -> str:
    return _sha256_bytes(payload.encode("utf-8"))


def _canonical_sha256(payload: Any) -> str:
    return _sha256_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def _analysis_tag_groups(repo_root: Path) -> list[str]:
    payload = _load_json(repo_root / SCOPES_CONFIG_PATH)
    scopes = payload.get("scopes")
    if not isinstance(scopes, list):
        raise ValueError("Docs scope config must contain scopes")
    for scope in scopes:
        if not isinstance(scope, dict) or scope.get("scope_id") != "analysis":
            continue
        sub_scopes = scope.get("sub_scopes")
        if not isinstance(sub_scopes, list):
            break
        for sub_scope in sub_scopes:
            if not isinstance(sub_scope, dict) or sub_scope.get("sub_scope") != "tags":
                continue
            customisation = sub_scope.get("sub_scope_customisation")
            settings = (
                customisation.get("settings")
                if isinstance(customisation, dict)
                and customisation.get("id") == "analysis_tags"
                else None
            )
            raw_groups = settings.get("groups") if isinstance(settings, dict) else None
            if (
                not isinstance(raw_groups, list)
                or not raw_groups
                or not all(isinstance(group, str) and group.strip() for group in raw_groups)
            ):
                raise ValueError(
                    "Analysis/tags must configure non-empty analysis_tags groups"
                )
            groups = [group.strip().lower() for group in raw_groups]
            if len(set(groups)) != len(groups):
                raise ValueError("Analysis/tags customisation groups must be unique")
            return groups
    raise ValueError("Analysis/tags sub-scope config was not found")


def _registry_rows(
    repo_root: Path,
    *,
    analysis_tag_groups: list[str],
) -> tuple[bytes, dict[str, dict[str, str]]]:
    registry_path = repo_root / REGISTRY_PATH
    registry_bytes = registry_path.read_bytes()
    payload = json.loads(registry_bytes.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("tag Registry must contain a JSON object")
    if payload.get("tag_registry_version") != SOURCE_REGISTRY_VERSION:
        raise ValueError(
            f"tag Registry must use {SOURCE_REGISTRY_VERSION}"
        )
    allowed_groups = tag_source.extract_allowed_groups(payload)
    if allowed_groups != analysis_tag_groups:
        raise ValueError(
            "Analysis/tags document groups must exactly match Registry allowed groups"
        )
    raw_tags = payload.get("tags")
    if not isinstance(raw_tags, list):
        raise ValueError("tag Registry tags must be an array")

    rows: dict[str, dict[str, str]] = {}
    seen_tag_ids: set[str] = set()
    for index, raw_tag in enumerate(raw_tags):
        if not isinstance(raw_tag, dict):
            raise ValueError(f"tag Registry tags[{index}] must be an object")
        tag_id = tag_source.sanitize_tag_id(
            raw_tag.get("tag_id"),
            f"tag Registry tags[{index}].tag_id",
        )
        group = tag_source.sanitize_group(
            raw_tag.get("group"),
            allowed_groups,
            f"tag Registry tags[{index}].group",
        )
        doc_id = str(raw_tag.get("doc_id") or "").strip()
        if not source_model.is_immutable_doc_id(doc_id):
            raise ValueError(
                f"tag Registry tags[{index}].doc_id must use immutable identity"
            )
        if tag_id in seen_tag_ids:
            raise ValueError(f"tag Registry duplicates tag_id {tag_id!r}")
        if doc_id in rows:
            raise ValueError(f"tag Registry duplicates doc_id {doc_id!r}")
        seen_tag_ids.add(tag_id)
        rows[doc_id] = {
            "tag_id": tag_id,
            "group": group,
        }
    return registry_bytes, rows


def _source_body(source_text: str, *, source_name: str) -> str:
    _front_matter, body = source_model.parse_source_text(
        source_text,
        source_name=source_name,
    )
    return body


def insert_missing_group(source_text: str, group: str) -> str:
    """Insert group in front matter without rewriting any existing source line."""

    normalized_group = source_model.normalize_document_group(group)
    if not normalized_group:
        raise ValueError("seed group must not be blank")
    match = source_model.FRONT_MATTER_PATTERN.match(source_text)
    if match is None:
        raise ValueError("source must have parseable front matter")
    front_matter, _body = source_model.parse_source_text(source_text)
    if "group" in front_matter:
        raise ValueError("source already contains group")

    raw_front_matter = match.group(1)
    newline = "\r\n" if "\r\n" in source_text[: match.end()] else "\n"
    lines = raw_front_matter.splitlines(keepends=True)
    insert_at = len(lines)
    for index, line in enumerate(lines):
        if line.lstrip().startswith(("parent_id:", "viewable:")):
            insert_at = index
            break

    rendered = f"group: {source_model.format_front_matter_value(normalized_group)}"
    if insert_at < len(lines):
        lines.insert(insert_at, rendered + newline)
        next_front_matter = "".join(lines)
    else:
        separator = "" if raw_front_matter.endswith(("\n", "\r")) else newline
        next_front_matter = raw_front_matter + separator + rendered
    return (
        source_text[: match.start(1)]
        + next_front_matter
        + source_text[match.end(1):]
    )


def _source_inventory(
    repo_root: Path,
) -> list[dict[str, Any]]:
    documents_root = repo_root / DOCUMENTS_ROOT
    paths = source_model.scope_markdown_paths(documents_root)
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for path in paths:
        source_bytes = path.read_bytes()
        source_text = source_bytes.decode("utf-8")
        front_matter, body = source_model.parse_source_text(
            source_text,
            source_name=path.name,
        )
        doc_id = str(front_matter.get("doc_id") or "").strip()
        if not source_model.is_immutable_doc_id(doc_id):
            raise ValueError(f"{path.name} must contain an immutable doc_id")
        if path.name != f"{doc_id}.md":
            raise ValueError(f"{path.name} must match its front-matter doc_id")
        if doc_id in seen_ids:
            raise ValueError(f"Analysis/tags sources duplicate doc_id {doc_id!r}")
        seen_ids.add(doc_id)
        records.append(
            {
                "doc_id": doc_id,
                "relative_path": path.relative_to(repo_root).as_posix(),
                "source_sha256": _sha256_bytes(source_bytes),
                "body_sha256": _sha256_text(body),
                "_path": path,
                "_source_text": source_text,
                "_front_matter": front_matter,
            }
        )
    return records


def _public_source_record(record: dict[str, Any]) -> dict[str, str]:
    return {
        "doc_id": str(record["doc_id"]),
        "relative_path": str(record["relative_path"]),
        "source_sha256": str(record["source_sha256"]),
    }


def build_seed_plan(
    repo_root: Path,
    *,
    created_at_utc: str,
    candidate_added_date: str = BOOTSTRAP_ADDED_DATE,
    expected_candidate_count: int = EXPECTED_BOOTSTRAP_DOCUMENTS,
    expected_independent_count: int = EXPECTED_INDEPENDENT_DOCUMENTS,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    analysis_tag_groups = _analysis_tag_groups(repo_root)
    registry_bytes, registry_by_doc_id = _registry_rows(
        repo_root,
        analysis_tag_groups=analysis_tag_groups,
    )
    source_records = _source_inventory(repo_root)
    candidates: list[dict[str, Any]] = []
    preserved: list[dict[str, str]] = []

    for record in source_records:
        front_matter = record["_front_matter"]
        doc_id = str(record["doc_id"])
        registry_row = registry_by_doc_id.get(doc_id)
        is_candidate = (
            str(front_matter.get("added_date") or "").strip()
            == candidate_added_date
        )
        if is_candidate:
            if registry_row is None:
                raise ValueError(
                    f"bootstrap candidate {doc_id!r} is not linked from Registry"
                )
            if "group" in front_matter:
                projected_source = str(record["_source_text"])
                action = "preserve_existing"
                existing_group = source_model.normalize_document_group(
                    front_matter.get("group")
                )
            else:
                projected_source = insert_missing_group(
                    str(record["_source_text"]),
                    registry_row["group"],
                )
                action = "seed"
                existing_group = ""
            projected_body = _source_body(
                projected_source,
                source_name=str(record["relative_path"]),
            )
            if _sha256_text(projected_body) != record["body_sha256"]:
                raise ValueError(
                    f"group seed would change body content for {doc_id!r}"
                )
            candidates.append(
                {
                    "tag_id": registry_row["tag_id"],
                    "doc_id": doc_id,
                    "relative_path": str(record["relative_path"]),
                    "registry_group": registry_row["group"],
                    "existing_group": existing_group,
                    "action": action,
                    "source_sha256": str(record["source_sha256"]),
                    "projected_source_sha256": _sha256_text(projected_source),
                    "body_sha256": str(record["body_sha256"]),
                }
            )
            continue

        preserved.append(
            {
                **_public_source_record(record),
                "relationship": (
                    "registry_linked"
                    if registry_row is not None
                    else "independent"
                ),
            }
        )

    candidates.sort(key=lambda row: row["relative_path"])
    preserved.sort(key=lambda row: row["relative_path"])
    independent_count = sum(
        row["relationship"] == "independent"
        for row in preserved
    )
    if len(candidates) != expected_candidate_count:
        raise ValueError(
            f"expected {expected_candidate_count} bootstrap candidates, "
            f"found {len(candidates)}"
        )
    if independent_count != expected_independent_count:
        raise ValueError(
            f"expected {expected_independent_count} independent documents, "
            f"found {independent_count}"
        )
    linked_source_ids = {
        str(record["doc_id"])
        for record in source_records
        if str(record["doc_id"]) in registry_by_doc_id
    }
    missing_registry_documents = sorted(set(registry_by_doc_id) - linked_source_ids)
    if missing_registry_documents:
        raise ValueError(
            "Registry links missing Analysis/tags sources: "
            + ", ".join(missing_registry_documents)
        )

    public_inventory = [
        _public_source_record(record)
        for record in source_records
    ]
    seeded_count = sum(row["action"] == "seed" for row in candidates)
    existing_count = sum(
        row["action"] == "preserve_existing"
        for row in candidates
    )
    linked_preserved_count = sum(
        row["relationship"] == "registry_linked"
        for row in preserved
    )
    return {
        "schema": PLAN_SCHEMA,
        "created_at_utc": created_at_utc,
        "candidate_added_date": candidate_added_date,
        "documents_root": DOCUMENTS_ROOT.as_posix(),
        "input": {
            "registry_path": REGISTRY_PATH.as_posix(),
            "registry_sha256": _sha256_bytes(registry_bytes),
            "source_inventory_sha256": _canonical_sha256(public_inventory),
            "analysis_tag_groups": analysis_tag_groups,
            "source_document_count": len(source_records),
            "registry_linked_document_count": len(linked_source_ids),
        },
        "output": {
            "candidate_count": len(candidates),
            "seeded_count": seeded_count,
            "preserved_existing_group_count": existing_count,
            "independent_document_count": independent_count,
            "later_linked_document_count": linked_preserved_count,
            "body_changes": 0,
            "registry_changes": 0,
        },
        "documents": candidates,
        "preserved_documents": preserved,
    }


def _plan_path(repo_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def _validate_plan_shape(plan: Any) -> dict[str, Any]:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise ValueError(f"seed plan must use {PLAN_SCHEMA}")
    if not isinstance(plan.get("documents"), list):
        raise ValueError("seed plan documents must be an array")
    if not isinstance(plan.get("preserved_documents"), list):
        raise ValueError("seed plan preserved_documents must be an array")
    if not isinstance(plan.get("input"), dict) or not isinstance(plan.get("output"), dict):
        raise ValueError("seed plan input and output must be objects")
    return plan


def preview_seed_plan(repo_root: Path, plan_path: Path) -> dict[str, Any]:
    plan = build_seed_plan(
        repo_root,
        created_at_utc=_utc_now(),
    )
    source_model.write_text_atomic_new(plan_path, _json_text(plan))
    return plan


def _projected_source_for_row(
    source_text: str,
    row: dict[str, Any],
) -> str:
    if row.get("action") == "seed":
        return insert_missing_group(source_text, str(row.get("registry_group") or ""))
    if row.get("action") == "preserve_existing":
        return source_text
    raise ValueError(f"unknown seed action {row.get('action')!r}")


def apply_seed_plan(repo_root: Path, plan: dict[str, Any]) -> dict[str, int]:
    plan = _validate_plan_shape(plan)
    reviewed_plan = build_seed_plan(
        repo_root,
        created_at_utc=str(plan.get("created_at_utc") or ""),
        candidate_added_date=str(plan.get("candidate_added_date") or ""),
        expected_candidate_count=int(plan["output"].get("candidate_count") or 0),
        expected_independent_count=int(
            plan["output"].get("independent_document_count") or 0
        ),
    )
    if reviewed_plan != plan:
        raise ValueError("live Registry or sources do not match the reviewed seed plan")

    writes: list[tuple[Path, bytes, bytes]] = []
    for row in plan["documents"]:
        if row.get("action") != "seed":
            continue
        path = repo_root / str(row["relative_path"])
        original = path.read_bytes()
        projected = _projected_source_for_row(
            original.decode("utf-8"),
            row,
        ).encode("utf-8")
        if _sha256_bytes(projected) != row.get("projected_source_sha256"):
            raise ValueError(
                f"projected source does not match reviewed plan: {row['relative_path']}"
            )
        writes.append((path, original, projected))

    written: list[tuple[Path, bytes]] = []
    try:
        for path, original, projected in writes:
            source_model.write_bytes_atomic(path, projected)
            written.append((path, original))
        stats = validate_applied_seed(repo_root, plan)
    except Exception:
        for path, original in reversed(written):
            source_model.write_bytes_atomic(path, original)
        raise

    stats["written_count"] = len(writes)
    return stats


def validate_applied_seed(
    repo_root: Path,
    plan: dict[str, Any],
) -> dict[str, int]:
    plan = _validate_plan_shape(plan)
    registry_path = repo_root / str(plan["input"]["registry_path"])
    if _sha256_bytes(registry_path.read_bytes()) != plan["input"].get("registry_sha256"):
        raise ValueError("tag Registry changed after seed preview")

    expected_paths = {
        str(row["relative_path"])
        for row in plan["documents"] + plan["preserved_documents"]
    }
    actual_records = _source_inventory(repo_root)
    actual_paths = {
        str(record["relative_path"])
        for record in actual_records
    }
    if actual_paths != expected_paths:
        raise ValueError("Analysis/tags source inventory changed after seed preview")

    seeded_count = 0
    for row in plan["documents"]:
        path = repo_root / str(row["relative_path"])
        source_text = path.read_text(encoding="utf-8")
        if _sha256_text(source_text) != row.get("projected_source_sha256"):
            raise ValueError(
                f"applied source does not match reviewed projection: {row['relative_path']}"
            )
        if _sha256_text(
            _source_body(source_text, source_name=str(row["relative_path"]))
        ) != row.get("body_sha256"):
            raise ValueError(
                f"document body changed during group seed: {row['relative_path']}"
            )
        if row.get("action") == "seed":
            seeded_count += 1

    for row in plan["preserved_documents"]:
        path = repo_root / str(row["relative_path"])
        if _sha256_bytes(path.read_bytes()) != row.get("source_sha256"):
            raise ValueError(
                f"preserved source changed during group seed: {row['relative_path']}"
            )
    return {
        "candidate_count": len(plan["documents"]),
        "seeded_count": seeded_count,
        "preserved_document_count": len(plan["preserved_documents"]),
        "body_changes": 0,
        "registry_changes": 0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--plan", default=str(DEFAULT_PLAN_PATH))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Apply only the exact reviewed plan.",
    )
    mode.add_argument(
        "--validate",
        action="store_true",
        help="Validate the applied sources against the reviewed plan.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    plan_path = _plan_path(repo_root, args.plan)
    if args.apply or args.validate:
        if not plan_path.is_file():
            raise FileNotFoundError(f"reviewed seed plan was not found: {plan_path}")
        plan = _validate_plan_shape(_load_json(plan_path))
        stats = (
            apply_seed_plan(repo_root, plan)
            if args.apply
            else validate_applied_seed(repo_root, plan)
        )
        print(
            _json_text(
                {
                    "mode": "apply" if args.apply else "validate",
                    "plan_path": plan_path.relative_to(repo_root).as_posix(),
                    **stats,
                }
            ),
            end="",
        )
        return 0

    plan = preview_seed_plan(repo_root, plan_path)
    print(
        _json_text(
            {
                "mode": "preview",
                "plan_path": plan_path.relative_to(repo_root).as_posix(),
                **plan["output"],
            }
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
