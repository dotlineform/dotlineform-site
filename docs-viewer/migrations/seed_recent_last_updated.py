#!/usr/bin/env python3
"""Seed only the source documents needed by current edited Recent projections.

Completed projections use a fast path. Pass ``--repair-existing`` only when an
already-full timestamp set must be checked again against semantic Git history.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MIGRATIONS_DIR = Path(__file__).resolve().parent
REPO_ROOT = MIGRATIONS_DIR.parents[1]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

import docs_source_model as source_model  # noqa: E402
from docs_document_identity import DOC_TIMESTAMP_FORMAT, is_doc_timestamp  # noqa: E402
from docs_scope_config import (  # noqa: E402
    EXTERNAL_DATA_ROOT_MARKER,
    load_docs_scope_configs,
    resolve_external_data_root,
)


ROUTE_CONFIG_PATH = Path("docs-viewer/config/routes/docs-viewer-routes.json")
PLAN_SCHEMA = "docs_recent_last_updated_seed_v1"
RECENT_BASES = {"added", "edited"}


@dataclass(frozen=True)
class Candidate:
    doc: source_model.ScopeDoc
    timestamp: str
    timestamp_source: str
    requires_write: bool
    repairs_existing_full_timestamp: bool = False


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _repo_relative(repo_root: Path, path: Path) -> str | None:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return None


def _source_path_label(repo_root: Path, path: Path) -> str:
    relative_path = _repo_relative(repo_root, path)
    if relative_path is not None:
        return relative_path
    try:
        external_relative = path.resolve().relative_to(resolve_external_data_root().resolve())
    except ValueError as exc:
        raise ValueError("seed source path is outside configured source roots") from exc
    return f"{EXTERNAL_DATA_ROOT_MARKER}/{external_relative.as_posix()}"


def _local_doc_timestamp(value: str) -> str:
    parsed = dt.datetime.fromisoformat(str(value or "").strip())
    return parsed.astimezone().strftime(DOC_TIMESTAMP_FORMAT)


def _mtime_doc_timestamp(path: Path) -> str:
    return dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone().strftime(DOC_TIMESTAMP_FORMAT)


def _dirty_repo_paths(repo_root: Path, source_root: Path) -> set[str]:
    relative_root = _repo_relative(repo_root, source_root)
    if relative_root is None:
        return set()
    changed = _git(repo_root, ["diff", "--name-only", "--", relative_root])
    staged = _git(repo_root, ["diff", "--cached", "--name-only", "--", relative_root])
    untracked = _git(repo_root, ["ls-files", "--others", "--exclude-standard", "--", relative_root])
    for result in (changed, staged, untracked):
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "git dirty-path scan failed")
    return {
        line.strip()
        for result in (changed, staged, untracked)
        for line in result.stdout.splitlines()
        if line.strip()
    }


def _git_file_text(repo_root: Path, revision: str, relative_path: str) -> str | None:
    result = _git(repo_root, ["show", f"{revision}:{relative_path}"])
    if result.returncode == 0:
        return result.stdout
    return None


def _git_follow_history(repo_root: Path, relative_path: str) -> list[dict[str, str]]:
    result = _git(
        repo_root,
        [
            "log",
            "--follow",
            "--name-status",
            "--format=COMMIT%x09%H%x09%aI",
            "--",
            relative_path,
        ],
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git history scan failed for {relative_path}")
    records: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in result.stdout.splitlines():
        if line.startswith("COMMIT\t"):
            if current is not None:
                records.append(current)
            _marker, commit, author_timestamp = line.split("\t", 2)
            current = {
                "commit": commit,
                "author_timestamp": author_timestamp,
                "before_path": "",
                "after_path": "",
            }
            continue
        if current is None or not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith(("R", "C")) and len(parts) >= 3:
            current["before_path"] = parts[1]
            current["after_path"] = parts[2]
        elif len(parts) >= 2:
            current["before_path"] = parts[1]
            current["after_path"] = parts[1]
    if current is not None:
        records.append(current)
    return records


def _matching_deleted_path(
    repo_root: Path,
    commit: str,
    current_front_matter: dict[str, Any],
    current_body: str,
) -> str:
    result = _git(repo_root, ["diff-tree", "--no-commit-id", "--name-status", "-r", f"{commit}^", commit])
    if result.returncode != 0:
        return ""
    matches: list[str] = []
    current_content = source_model.recent_edit_content(current_front_matter, current_body)
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 2 or parts[0] != "D":
            continue
        deleted_path = parts[1]
        previous_source = _git_file_text(repo_root, f"{commit}^", deleted_path)
        if previous_source is None:
            continue
        previous_front_matter, previous_body = source_model.parse_source_text(
            previous_source,
            source_name=deleted_path,
        )
        if source_model.recent_edit_content(previous_front_matter, previous_body) == current_content:
            matches.append(deleted_path)
    return matches[0] if len(matches) == 1 else ""


def _git_substantive_author_timestamp(
    repo_root: Path,
    relative_path: str,
    _seen_paths: set[str] | None = None,
) -> str:
    seen_paths = set(_seen_paths or set())
    if relative_path in seen_paths:
        return ""
    seen_paths.add(relative_path)
    for record in _git_follow_history(repo_root, relative_path):
        commit = record["commit"]
        after_path = record["after_path"]
        before_path = record["before_path"] or after_path
        if not after_path:
            continue
        current_source = _git_file_text(repo_root, commit, after_path)
        if current_source is None:
            continue
        current_front_matter, current_body = source_model.parse_source_text(
            current_source,
            source_name=after_path,
        )
        previous_source = _git_file_text(repo_root, f"{commit}^", before_path)
        if previous_source is None:
            deleted_path = _matching_deleted_path(
                repo_root,
                commit,
                current_front_matter,
                current_body,
            )
            if deleted_path:
                return _git_substantive_author_timestamp(repo_root, deleted_path, seen_paths)
            return _local_doc_timestamp(record["author_timestamp"])
        previous_front_matter, previous_body = source_model.parse_source_text(
            previous_source,
            source_name=before_path,
        )
        if source_model.recent_edit_content(
            previous_front_matter,
            previous_body,
        ) != source_model.recent_edit_content(current_front_matter, current_body):
            return _local_doc_timestamp(record["author_timestamp"])
    return ""


def _working_tree_recent_edit_changed(
    repo_root: Path,
    relative_path: str,
    doc: source_model.ScopeDoc,
) -> tuple[bool, str]:
    head_source = _git_file_text(repo_root, "HEAD", relative_path)
    if head_source is None:
        return True, ""
    head_front_matter, head_body = source_model.parse_source_text(
        head_source,
        source_name=relative_path,
    )
    changed = source_model.recent_edit_content(
        head_front_matter,
        head_body,
    ) != source_model.recent_edit_content(doc.front_matter, doc.body)
    return changed, str(head_front_matter.get("last_updated") or "").strip()


def _hidden_doc_ids(
    docs: list[source_model.ScopeDoc],
    manage_only_tree_root_ids: Iterable[str],
) -> set[str]:
    hidden = {str(doc_id or "").strip() for doc_id in manage_only_tree_root_ids}
    hidden.update(doc.doc_id for doc in docs if not doc.viewable)
    hidden.discard("")
    children_by_parent: dict[str, list[str]] = {}
    for doc in docs:
        if doc.parent_id:
            children_by_parent.setdefault(doc.parent_id, []).append(doc.doc_id)
    queue = list(hidden)
    while queue:
        parent_id = queue.pop(0)
        for child_id in children_by_parent.get(parent_id, []):
            if child_id in hidden:
                continue
            hidden.add(child_id)
            queue.append(child_id)
    return hidden


def _route_policies(repo_root: Path) -> list[dict[str, Any]]:
    payload = json.loads((repo_root / ROUTE_CONFIG_PATH).read_text(encoding="utf-8"))
    routes = payload.get("routes") if isinstance(payload, dict) else None
    if not isinstance(routes, list):
        raise ValueError("Docs Viewer route registry must contain routes")
    policies: list[dict[str, Any]] = []
    for route in routes:
        if not isinstance(route, dict):
            continue
        basis = str(route.get("recent_basis") or "").strip()
        features = {str(value or "").strip() for value in route.get("features") or []}
        if "recent" in features and basis not in RECENT_BASES:
            raise ValueError(f"route {route.get('route_id')!r} must declare an added or edited Recent basis")
        if basis and "recent" not in features:
            raise ValueError(f"route {route.get('route_id')!r} declares Recent basis without the feature")
        policies.append(
            {
                "route_id": str(route.get("route_id") or "").strip(),
                "app_kind": str(route.get("app_kind") or "").strip(),
                "scope": str(route.get("default_scope_id") or "").strip(),
                "basis": basis,
            }
        )
    return policies


def _recent_limit(repo_root: Path) -> int:
    payload = json.loads((repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(encoding="utf-8"))
    settings = payload.get("docs_viewer") if isinstance(payload, dict) else None
    raw_limit = settings.get("recent_limit") if isinstance(settings, dict) else None
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        limit = 10
    return limit if limit > 0 else 10


def _projection_specs(repo_root: Path, selected_scopes: set[str]) -> list[dict[str, str]]:
    configs = load_docs_scope_configs(repo_root)
    policies = _route_policies(repo_root)
    specs: list[dict[str, str]] = []
    manage_basis = next(
        (policy["basis"] for policy in policies if policy["app_kind"] == "manage"),
        "",
    )
    if manage_basis == "edited":
        specs.extend(
            {
                "projection": f"manage:{scope}",
                "scope": scope,
                "visibility": "manage",
            }
            for scope in configs
            if not selected_scopes or scope in selected_scopes
        )
    for policy in policies:
        scope = policy["scope"]
        if policy["app_kind"] != "public" or policy["basis"] != "edited":
            continue
        if scope not in configs or (selected_scopes and scope not in selected_scopes):
            continue
        specs.append(
            {
                "projection": f"public:{scope}",
                "scope": scope,
                "visibility": "public",
            }
        )
    return specs


def _candidate_for_doc(
    repo_root: Path,
    doc: source_model.ScopeDoc,
    dirty_paths: set[str],
    dirty_timestamp: str,
) -> Candidate:
    relative_path = _repo_relative(repo_root, doc.path)
    dirty = bool(relative_path and relative_path in dirty_paths)
    existing = str(doc.front_matter.get("last_updated") or "").strip()
    if dirty:
        recent_edit_changed, head_last_updated = _working_tree_recent_edit_changed(
            repo_root,
            str(relative_path),
            doc,
        )
        if recent_edit_changed:
            if is_doc_timestamp(existing) and existing >= dirty_timestamp:
                return Candidate(doc, existing, "existing-full-timestamp", False)
            return Candidate(doc, dirty_timestamp, "dirty-write-time", True)
        if is_doc_timestamp(existing) and existing == head_last_updated:
            return Candidate(doc, existing, "existing-full-timestamp", False)

    if is_doc_timestamp(existing):
        if not dirty:
            return Candidate(doc, existing, "existing-full-timestamp", False)

    if relative_path is not None:
        timestamp = _git_substantive_author_timestamp(repo_root, relative_path)
        if timestamp:
            return Candidate(
                doc,
                timestamp,
                "git-substantive-author-time",
                timestamp != existing,
                dirty and is_doc_timestamp(existing),
            )
        return Candidate(doc, dirty_timestamp, "untracked-write-time", True)
    timestamp = _mtime_doc_timestamp(doc.path)
    return Candidate(doc, timestamp, "filesystem-write-time", timestamp != existing)


def _replace_last_updated(source_text: str, timestamp: str) -> str:
    lines = source_text.splitlines(keepends=True)
    closing_index = -1
    for index, line in enumerate(lines):
        if index > 0 and line.strip().startswith("---"):
            closing_index = index
        if line.lstrip().startswith("last_updated:"):
            newline = "\r\n" if line.endswith("\r\n") else "\n"
            lines[index] = f'last_updated: "{timestamp}"{newline}'
            return "".join(lines)
    if closing_index < 1:
        raise ValueError("source front matter closing delimiter could not be found")
    lines.insert(closing_index, f'last_updated: "{timestamp}"\n')
    return "".join(lines)


def _complete_existing_projection_rows(
    scope: str,
    scope_specs: list[dict[str, str]],
    docs: list[source_model.ScopeDoc],
    hidden_ids: set[str],
    limit: int,
) -> list[dict[str, Any]] | None:
    rows: list[dict[str, Any]] = []
    for spec in scope_specs:
        eligible_docs = [
            doc
            for doc in docs
            if spec["visibility"] == "manage" or doc.doc_id not in hidden_ids
        ]
        full_timestamp_docs = [
            doc
            for doc in eligible_docs
            if is_doc_timestamp(str(doc.front_matter.get("last_updated") or "").strip())
        ]
        required_count = min(limit, len(eligible_docs))
        if len(full_timestamp_docs) < required_count:
            return None
        full_timestamp_docs.sort(
            key=lambda doc: (
                str(doc.front_matter.get("last_updated") or "").strip(),
                doc.doc_id,
            ),
            reverse=True,
        )
        rows.append(
            {
                **spec,
                "scope": scope,
                "limit": limit,
                "eligible_count": len(eligible_docs),
                "required_count": required_count,
                "selected_doc_ids": [doc.doc_id for doc in full_timestamp_docs[:limit]],
            }
        )
    return rows


def build_seed_plan(
    repo_root: Path,
    *,
    selected_scopes: set[str] | None = None,
    dirty_timestamp: str,
    repair_existing_full_timestamps: bool = False,
) -> dict[str, Any]:
    selected = {str(scope or "").strip() for scope in selected_scopes or set() if str(scope or "").strip()}
    configs = load_docs_scope_configs(repo_root)
    unknown = sorted(selected - set(configs))
    if unknown:
        raise ValueError(f"unknown scope: {', '.join(unknown)}")
    if not is_doc_timestamp(dirty_timestamp):
        raise ValueError("dirty timestamp must use YYYY-MM-DD HH:MM:SS")

    limit = _recent_limit(repo_root)
    specs = _projection_specs(repo_root, selected)
    specs_by_scope: dict[str, list[dict[str, str]]] = {}
    for spec in specs:
        specs_by_scope.setdefault(spec["scope"], []).append(spec)

    projection_rows: list[dict[str, Any]] = []
    write_rows: list[dict[str, Any]] = []
    for scope, scope_specs in sorted(specs_by_scope.items()):
        config = configs[scope]
        docs = source_model.load_scope_docs(repo_root, scope)
        source_root = source_model.scope_root(repo_root, scope)
        hidden_ids = _hidden_doc_ids(docs, config.manage_only_tree_root_ids)
        dirty_paths = _dirty_repo_paths(repo_root, source_root)
        has_timestamp_only_seed_repairs = False
        if repair_existing_full_timestamps:
            for doc in docs:
                relative_path = _repo_relative(repo_root, doc.path)
                existing = str(doc.front_matter.get("last_updated") or "").strip()
                if not relative_path or relative_path not in dirty_paths or not is_doc_timestamp(existing):
                    continue
                recent_edit_changed, head_last_updated = _working_tree_recent_edit_changed(
                    repo_root,
                    relative_path,
                    doc,
                )
                if not recent_edit_changed and existing != head_last_updated:
                    has_timestamp_only_seed_repairs = True
                    break
        complete_rows = _complete_existing_projection_rows(
            scope,
            scope_specs,
            docs,
            hidden_ids,
            limit,
        )
        if complete_rows is not None and not has_timestamp_only_seed_repairs:
            projection_rows.extend(complete_rows)
            continue
        candidates = {
            doc.doc_id: _candidate_for_doc(repo_root, doc, dirty_paths, dirty_timestamp)
            for doc in docs
        }
        selected_ids: set[str] = set()
        for spec in scope_specs:
            eligible = [
                candidate
                for candidate in candidates.values()
                if spec["visibility"] == "manage" or candidate.doc.doc_id not in hidden_ids
            ]
            eligible.sort(key=lambda candidate: (candidate.timestamp, candidate.doc.doc_id), reverse=True)
            chosen = eligible[:limit]
            selected_ids.update(candidate.doc.doc_id for candidate in chosen)
            projection_rows.append(
                {
                    **spec,
                    "limit": limit,
                    "eligible_count": len(eligible),
                    "required_count": min(limit, len(eligible)),
                    "selected_doc_ids": [candidate.doc.doc_id for candidate in chosen],
                }
            )

        repair_ids = {
            candidate.doc.doc_id
            for candidate in candidates.values()
            if candidate.repairs_existing_full_timestamp
        }
        for doc_id in sorted(selected_ids | repair_ids):
            candidate = candidates[doc_id]
            current = str(candidate.doc.front_matter.get("last_updated") or "").strip()
            if not candidate.requires_write:
                continue
            next_source = _replace_last_updated(candidate.doc.source_text, candidate.timestamp)
            if next_source == candidate.doc.source_text:
                continue
            write_rows.append(
                {
                    "scope": scope,
                    "doc_id": doc_id,
                    "source_path": _source_path_label(repo_root, candidate.doc.path),
                    "timestamp": candidate.timestamp,
                    "timestamp_source": candidate.timestamp_source,
                    "source_sha256": _sha256(candidate.doc.source_text),
                    "next_source_sha256": _sha256(next_source),
                    "_path": candidate.doc.path,
                    "_next_source": next_source,
                }
            )

    return {
        "schema": PLAN_SCHEMA,
        "dirty_timestamp": dirty_timestamp,
        "repair_existing_full_timestamps": repair_existing_full_timestamps,
        "limit": limit,
        "projections": projection_rows,
        "writes": write_rows,
    }


def public_plan(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        **plan,
        "writes": [
            {key: value for key, value in row.items() if not key.startswith("_")}
            for row in plan["writes"]
        ],
    }


def apply_seed_plan(plan: dict[str, Any]) -> None:
    for row in plan["writes"]:
        path = Path(row["_path"])
        current_source = path.read_text(encoding="utf-8")
        if _sha256(current_source) != row["source_sha256"]:
            raise ValueError(f"source changed after seed planning: {row['source_path']}")
    for row in plan["writes"]:
        source_model.write_text_atomic(Path(row["_path"]), str(row["_next_source"]))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--scope", action="append", default=[], help="Limit planning to one configured scope; repeatable.")
    parser.add_argument("--dirty-timestamp", default=source_model.current_doc_timestamp())
    parser.add_argument(
        "--repair-existing",
        action="store_true",
        help="Recheck dirty full timestamps against semantic Git history before using the fast path.",
    )
    parser.add_argument("--apply", action="store_true", help="Apply the planned bounded source writes after validation.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    plan = build_seed_plan(
        repo_root,
        selected_scopes=set(args.scope),
        dirty_timestamp=args.dirty_timestamp,
        repair_existing_full_timestamps=args.repair_existing,
    )
    if args.apply:
        apply_seed_plan(plan)
    payload = public_plan(plan)
    payload["mode"] = "apply" if args.apply else "dry-run"
    payload["write_count"] = len(payload["writes"])
    print(_json_text(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
