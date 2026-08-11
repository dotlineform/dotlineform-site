#!/usr/bin/env python3
"""Preview, apply, or validate the Registry-v5 Tag document-link cutover."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
for import_dir in (
    REPO_ROOT / "studio" / "services",
    REPO_ROOT / "docs-viewer" / "services",
):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

import docs_source_model  # noqa: E402
from docs_document_location_projection import (  # noqa: E402
    load_public_exact_document_location_records,
)
from docs_scope_config import load_docs_scope_configs  # noqa: E402
from tags import tag_document_declarations  # noqa: E402
from tags import tag_document_link_migration as migration  # noqa: E402
from tags import tag_source_model as tag_source  # noqa: E402
from tags import tag_write_transactions as transactions  # noqa: E402


DEFAULT_PLAN_REL_PATH = Path("var/studio/tag-document-link-migration/plan.json")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--plan-file", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--validate", action="store_true")
    parser.add_argument("--created-at-utc")
    return parser.parse_args(argv)


def plan_path(args: argparse.Namespace, repo_root: Path) -> Path:
    raw = args.plan_file or DEFAULT_PLAN_REL_PATH
    return raw.resolve() if raw.is_absolute() else (repo_root / raw).resolve()


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"failed to read {label}: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def analysis_tags_configs(repo_root: Path) -> tuple[Any, Any]:
    parent = load_docs_scope_configs(repo_root, scope_ids=["analysis"])["analysis"]
    matches = [row for row in parent.sub_scopes if row.sub_scope == "tags"]
    if len(matches) != 1:
        raise ValueError("Analysis Tags collection is not configured")
    return parent, matches[0]


def live_documents(repo_root: Path) -> list[dict[str, Any]]:
    parent, tags_config = analysis_tags_configs(repo_root)
    documents = docs_source_model.load_document_collection_docs_for_config(
        repo_root,
        parent,
        tags_config,
    )
    return [
        {
            "doc_id": document.doc_id,
            "relative_path": document.path.relative_to(repo_root).as_posix(),
            "source_sha256": migration.sha256_text(document.source_text),
            "source_text": document.source_text,
            "title": document.title,
        }
        for document in documents
    ]


def live_locations(repo_root: Path) -> list[dict[str, str]]:
    parent, _tags_config = analysis_tags_configs(repo_root)
    return sorted(
        (
            dict(record)
            for record in load_public_exact_document_location_records(
                repo_root,
                parent,
            )
            if record.get("scope_id") == "analysis"
            and record.get("sub_scope") == "tags"
        ),
        key=lambda row: str(row.get("url") or ""),
    )


def inventory_fingerprints(
    registry_path: Path,
    documents: list[dict[str, Any]],
    locations: list[dict[str, str]],
) -> dict[str, str]:
    document_inventory = [
        {
            "doc_id": row["doc_id"],
            "relative_path": row["relative_path"],
            "source_sha256": row["source_sha256"],
        }
        for row in documents
    ]
    return {
        "registry_sha256": migration.sha256_bytes(registry_path.read_bytes()),
        "documents_sha256": migration.canonical_json_sha256(document_inventory),
        "locations_sha256": migration.canonical_json_sha256(locations),
    }


def live_inputs(
    repo_root: Path,
) -> tuple[Path, dict[str, Any], list[dict[str, Any]], list[dict[str, str]], dict[str, str]]:
    registry_path = (repo_root / tag_source.REGISTRY_REL_PATH).resolve()
    registry = read_json_object(registry_path, "tag registry")
    documents = live_documents(repo_root)
    locations = live_locations(repo_root)
    fingerprints = inventory_fingerprints(
        registry_path,
        documents,
        locations,
    )
    return registry_path, registry, documents, locations, fingerprints


def write_new_plan(path: Path, plan: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(migration.canonical_json_text(plan))


def preview(
    args: argparse.Namespace,
    repo_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    _path, registry, documents, locations, fingerprints = live_inputs(repo_root)
    plan = migration.build_migration_plan(
        registry,
        documents,
        locations,
        created_at_utc=str(args.created_at_utc or tag_source.utc_now()),
        input_fingerprints=fingerprints,
    )
    write_new_plan(output_path, plan)
    return command_result("preview", output_path, plan)


def confined_source_path(repo_root: Path, relative_path: str) -> Path:
    _parent, tags_config = analysis_tags_configs(repo_root)
    source_root = docs_source_model.resolve_scope_path(
        repo_root,
        docs_source_model.document_source_path(tags_config),
    ).resolve()
    path = (repo_root / relative_path).resolve()
    if path.parent != source_root:
        raise ValueError(f"migration source target escapes Analysis Tags: {path}")
    return path


def applied_source_hashes(
    repo_root: Path,
    plan: dict[str, Any],
) -> dict[str, str]:
    return {
        str(row["doc_id"]): migration.sha256_bytes(
            confined_source_path(repo_root, str(row["relative_path"])).read_bytes()
        )
        for row in plan.get("source_edits", [])
        if isinstance(row, dict)
    }


def apply_plan(
    repo_root: Path,
    output_path: Path,
    plan: dict[str, Any],
) -> dict[str, Any]:
    registry_path, registry, documents, locations, fingerprints = live_inputs(repo_root)
    migration.validate_migration_plan(
        plan,
        registry,
        documents,
        locations,
        input_fingerprints=fingerprints,
    )
    payloads: dict[Path, bytes] = {
        registry_path: migration.canonical_json_text(
            plan["projected_registry"]
        ).encode("utf-8")
    }
    for row in plan["source_edits"]:
        path = confined_source_path(repo_root, str(row["relative_path"]))
        if migration.sha256_bytes(path.read_bytes()) != row["input_sha256"]:
            raise ValueError(f"source changed since preview: {row['relative_path']}")
        payloads[path] = str(row["source_text"]).encode("utf-8")
    transactions.atomic_write_bytes_many(payloads)
    if migration.canonical_json_sha256(
        read_json_object(registry_path, "applied tag registry")
    ) != plan["output"]["registry_sha256"]:
        raise ValueError("applied Registry does not match reviewed migration")
    source_hashes = applied_source_hashes(repo_root, plan)
    for row in plan["source_edits"]:
        actual = source_hashes.get(str(row["doc_id"]))
        if actual != row["output_sha256"]:
            raise ValueError(f"applied source does not match plan: {row['relative_path']}")
    return command_result("write", output_path, plan)


def actual_association_identities(repo_root: Path) -> list[dict[str, Any]]:
    payload = tag_document_declarations.load_tag_document_association_payload(
        repo_root
    )
    return [
        {
            "tag_id": association["tag_id"],
            "documents": [dict(document["target"]) for document in association["documents"]],
        }
        for association in payload["associations"]
    ]


def validate_applied(
    repo_root: Path,
    output_path: Path,
    plan: dict[str, Any],
) -> dict[str, Any]:
    registry_path = (repo_root / tag_source.REGISTRY_REL_PATH).resolve()
    registry = tag_source.load_registry(registry_path)
    if migration.canonical_json_sha256(registry) != plan["output"]["registry_sha256"]:
        raise ValueError("applied Registry does not match reviewed migration")
    hashes = applied_source_hashes(repo_root, plan)
    for row in plan.get("source_edits", []):
        if hashes.get(str(row["doc_id"])) != row["output_sha256"]:
            raise ValueError(f"applied source does not match plan: {row['relative_path']}")
    if actual_association_identities(repo_root) != plan["expected_associations"]:
        raise ValueError("generated Tag associations do not match reviewed migration")
    result = command_result("validate", output_path, plan)
    result["association_validation"] = "matched"
    return result


def command_result(
    mode: str,
    output_path: Path,
    plan: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ok": True,
        "mode": mode,
        "plan_path": str(output_path),
        **{key: value for key, value in plan["output"].items() if key != "registry_sha256"},
        "registry_sha256": plan["output"]["registry_sha256"],
        "unresolved_legacy": plan["unresolved_legacy"],
        "unassociated_documents": plan["unassociated_documents"],
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    output_path = plan_path(args, repo_root)
    if args.write or args.validate:
        plan = read_json_object(output_path, "Tag document link migration plan")
        result = (
            apply_plan(repo_root, output_path, plan)
            if args.write
            else validate_applied(repo_root, output_path, plan)
        )
    else:
        result = preview(args, repo_root, output_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
