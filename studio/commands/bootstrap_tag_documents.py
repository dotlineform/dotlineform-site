#!/usr/bin/env python3
"""Preview, apply, or validate the one-time tag-document bootstrap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict


REPO_ROOT = Path(__file__).resolve().parents[2]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
DOCS_VIEWER_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
DOCS_VIEWER_BUILD_DIR = REPO_ROOT / "docs-viewer" / "build"
for import_dir in (
    STUDIO_SERVICES_DIR,
    DOCS_VIEWER_SERVICES_DIR,
    DOCS_VIEWER_BUILD_DIR,
):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

from docs_builder.source import parse_source  # noqa: E402
from docs_document_identity import (  # noqa: E402
    allocate_doc_id,
    current_doc_timestamp,
    doc_id_matches_added_date,
    is_immutable_doc_id,
)
from tags import tag_document_bootstrap as bootstrap  # noqa: E402
from tags import tag_source_model as tag_source  # noqa: E402
from tags import tag_write_transactions as transactions  # noqa: E402


DEFAULT_PLAN_REL_PATH = Path(
    "var/studio/tag-document-bootstrap/plan.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root containing Studio and Docs Viewer sources.",
    )
    parser.add_argument(
        "--plan-file",
        type=Path,
        help=(
            "Preview output or reviewed apply/validate input. "
            "Defaults to var/studio/tag-document-bootstrap/plan.json."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write",
        action="store_true",
        help="Apply an existing reviewed plan to canonical source.",
    )
    mode.add_argument(
        "--validate",
        action="store_true",
        help="Validate applied canonical source against the reviewed plan.",
    )
    parser.add_argument(
        "--added-date",
        help="Fixed local document timestamp for preview; defaults to now.",
    )
    parser.add_argument(
        "--created-at-utc",
        help="Fixed UTC registry cutover timestamp for preview; defaults to now.",
    )
    parser.add_argument(
        "--show-mapping",
        action="store_true",
        help="Include the complete tag-to-document mapping in command output.",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    return bootstrap.sha256_bytes(path.read_bytes())


def read_json_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"failed to read {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def analysis_tag_documents_root(repo_root: Path) -> Path:
    return (
        repo_root / bootstrap.DEFAULT_DOCUMENTS_ROOT
    ).resolve()


def inventory_analysis_tag_documents(repo_root: Path) -> list[Dict[str, str]]:
    root = analysis_tag_documents_root(repo_root)
    if not root.is_dir():
        raise FileNotFoundError(
            f"Analysis tag document root does not exist: {root}"
        )
    paths = sorted(root.glob("**/*.md"))
    nested = [path for path in paths if path.parent != root]
    if nested:
        relative = ", ".join(
            path.relative_to(root).as_posix() for path in nested
        )
        raise ValueError(
            f"nested Analysis tag documents are not supported: {relative}"
        )
    inventory: list[Dict[str, str]] = []
    seen_ids: set[str] = set()
    for path in paths:
        front_matter, _body = parse_source(path)
        doc_id = str(front_matter.get("doc_id") or "").strip()
        if not is_immutable_doc_id(doc_id):
            raise ValueError(
                f"Analysis tag document has invalid doc_id: "
                f"{path.relative_to(repo_root).as_posix()}"
            )
        if path.stem != doc_id:
            raise ValueError(
                f"Analysis tag document filename does not match doc_id: "
                f"{path.relative_to(repo_root).as_posix()}"
            )
        if doc_id in seen_ids:
            raise ValueError(f"duplicate Analysis tag document ID: {doc_id}")
        seen_ids.add(doc_id)
        inventory.append(
            {
                "doc_id": doc_id,
                "relative_path": path.relative_to(repo_root).as_posix(),
                "source_sha256": sha256_file(path),
            }
        )
    return inventory


def canonical_paths(repo_root: Path) -> Dict[str, Path]:
    return {
        "registry": (repo_root / tag_source.REGISTRY_REL_PATH).resolve(),
        "aliases": (repo_root / tag_source.ALIASES_REL_PATH).resolve(),
        "assignments": (repo_root / tag_source.ASSIGNMENTS_REL_PATH).resolve(),
    }


def load_canonical_sources(
    repo_root: Path,
) -> tuple[Dict[str, Path], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    paths = canonical_paths(repo_root)
    registry = read_json_object(paths["registry"], "tag registry")
    aliases = read_json_object(paths["aliases"], "tag aliases")
    assignments = read_json_object(paths["assignments"], "tag assignments")
    return paths, registry, aliases, assignments


def input_fingerprints(
    paths: Dict[str, Path],
    documents: list[Dict[str, str]],
) -> Dict[str, str]:
    return {
        "registry_sha256": sha256_file(paths["registry"]),
        "aliases_sha256": sha256_file(paths["aliases"]),
        "assignments_sha256": sha256_file(paths["assignments"]),
        "documents_sha256": bootstrap.document_inventory_sha256(documents),
    }


def resolved_plan_path(args: argparse.Namespace, repo_root: Path) -> Path:
    raw_path = args.plan_file or DEFAULT_PLAN_REL_PATH
    if raw_path.is_absolute():
        return raw_path.resolve()
    return (repo_root / raw_path).resolve()


def write_new_plan(path: Path, plan: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(bootstrap.canonical_json_text(plan))


def load_plan(path: Path) -> Dict[str, Any]:
    return read_json_object(path, "tag document bootstrap plan")


def command_result(
    *,
    mode: str,
    plan_path: Path,
    plan: Dict[str, Any],
    stats: Dict[str, int],
    show_mapping: bool,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "mode": mode,
        "ok": True,
        "plan_path": str(plan_path),
        "registry_input_sha256": plan["input"]["fingerprints"][
            "registry_sha256"
        ],
        "projected_registry_sha256": plan["output"][
            "projected_registry_sha256"
        ],
        "mapping_sha256": plan["output"]["mapping_sha256"],
        **stats,
    }
    if show_mapping:
        result["mapping"] = [
            {
                key: document[key]
                for key in (
                    "tag_id",
                    "group",
                    "doc_id",
                    "relative_path",
                    "source_sha256",
                )
            }
            for document in plan["documents"]
        ]
    return result


def preview(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    plan_path: Path,
) -> Dict[str, Any]:
    paths, registry, aliases, assignments = load_canonical_sources(repo_root)
    documents = inventory_analysis_tag_documents(repo_root)
    added_date = str(args.added_date or current_doc_timestamp()).strip()
    created_at_utc = str(args.created_at_utc or tag_source.utc_now()).strip()
    plan = bootstrap.build_tag_document_bootstrap_plan(
        registry,
        aliases,
        assignments,
        documents,
        added_date=added_date,
        created_at_utc=created_at_utc,
        input_fingerprints=input_fingerprints(paths, documents),
        allocate_document_id=allocate_doc_id,
        is_immutable_doc_id=is_immutable_doc_id,
        doc_id_matches_added_date=doc_id_matches_added_date,
    )
    write_new_plan(plan_path, plan)
    stats = {
        "tag_count": int(plan["output"]["tag_count"]),
        "existing_document_count": len(
            plan["input"]["existing_documents"]
        ),
        "new_document_count": int(plan["output"]["new_document_count"]),
        "final_document_count": int(plan["output"]["final_document_count"]),
    }
    return command_result(
        mode="preview",
        plan_path=plan_path,
        plan=plan,
        stats=stats,
        show_mapping=args.show_mapping,
    )


def preflight_reviewed_plan(
    repo_root: Path,
    plan: Dict[str, Any],
) -> tuple[
    Dict[str, Path],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    list[Dict[str, str]],
    Dict[str, int],
]:
    paths, registry, aliases, assignments = load_canonical_sources(repo_root)
    documents = inventory_analysis_tag_documents(repo_root)
    stats = bootstrap.validate_tag_document_bootstrap_plan(
        plan,
        registry,
        aliases,
        assignments,
        documents,
        input_fingerprints=input_fingerprints(paths, documents),
        is_immutable_doc_id=is_immutable_doc_id,
        doc_id_matches_added_date=doc_id_matches_added_date,
    )
    return paths, registry, aliases, assignments, documents, stats


def target_path(repo_root: Path, raw_relative_path: Any) -> Path:
    path = (repo_root / str(raw_relative_path or "")).resolve()
    if path.parent != analysis_tag_documents_root(repo_root):
        raise ValueError(
            f"planned document path escapes Analysis tag root: {path}"
        )
    return path


def applied_validation(
    repo_root: Path,
    plan: Dict[str, Any],
) -> Dict[str, int]:
    paths, registry, aliases, assignments = load_canonical_sources(repo_root)
    documents = inventory_analysis_tag_documents(repo_root)
    return bootstrap.validate_applied_tag_document_bootstrap(
        plan,
        registry,
        aliases,
        assignments,
        documents,
        registry_sha256=sha256_file(paths["registry"]),
        aliases_sha256=sha256_file(paths["aliases"]),
        assignments_sha256=sha256_file(paths["assignments"]),
        is_immutable_doc_id=is_immutable_doc_id,
    )


def apply_reviewed_plan(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    plan_path: Path,
    plan: Dict[str, Any],
) -> Dict[str, Any]:
    paths, _registry, _aliases, _assignments, _documents, _stats = (
        preflight_reviewed_plan(repo_root, plan)
    )
    planned_paths = [
        target_path(repo_root, document["relative_path"])
        for document in plan["documents"]
    ]
    existing_targets = [path for path in planned_paths if path.exists()]
    if existing_targets:
        relative = ", ".join(
            path.relative_to(repo_root).as_posix() for path in existing_targets
        )
        raise FileExistsError(
            f"planned document targets already exist: {relative}"
        )

    created_paths: list[Path] = []
    try:
        for document, path in zip(
            plan["documents"],
            planned_paths,
            strict=True,
        ):
            with path.open("x", encoding="utf-8") as handle:
                handle.write(str(document["source_text"]))
            created_paths.append(path)
        transactions.atomic_write(
            paths["registry"],
            plan["projected_registry"],
        )
    except Exception as exc:
        registry_committed = (
            paths["registry"].exists()
            and sha256_file(paths["registry"])
            == plan["output"]["projected_registry_sha256"]
        )
        remaining: list[str] = []
        if not registry_committed:
            for path in reversed(created_paths):
                try:
                    path.unlink()
                except OSError:
                    if path.exists():
                        remaining.append(path.relative_to(repo_root).as_posix())
        detail = (
            f"; run-created unreferenced files: {', '.join(sorted(remaining))}"
            if remaining
            else ""
        )
        raise RuntimeError(f"tag document bootstrap apply failed: {exc}{detail}") from exc

    stats = applied_validation(repo_root, plan)
    return command_result(
        mode="write",
        plan_path=plan_path,
        plan=plan,
        stats=stats,
        show_mapping=args.show_mapping,
    )


def validate_applied(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    plan_path: Path,
    plan: Dict[str, Any],
) -> Dict[str, Any]:
    stats = applied_validation(repo_root, plan)
    return command_result(
        mode="validate",
        plan_path=plan_path,
        plan=plan,
        stats=stats,
        show_mapping=args.show_mapping,
    )


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    plan_path = resolved_plan_path(args, repo_root)
    if args.write or args.validate:
        if not plan_path.is_file():
            raise FileNotFoundError(
                f"reviewed bootstrap plan does not exist: {plan_path}"
            )
        plan = load_plan(plan_path)
        result = (
            apply_reviewed_plan(
                args,
                repo_root=repo_root,
                plan_path=plan_path,
                plan=plan,
            )
            if args.write
            else validate_applied(
                args,
                repo_root=repo_root,
                plan_path=plan_path,
                plan=plan,
            )
        )
    else:
        result = preview(
            args,
            repo_root=repo_root,
            plan_path=plan_path,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
