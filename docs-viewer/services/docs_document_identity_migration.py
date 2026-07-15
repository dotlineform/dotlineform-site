#!/usr/bin/env python3
"""Plan and apply the one-off repository-owned document identity migration."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


SERVICES_DIR = Path(__file__).resolve().parent
REPO_ROOT = SERVICES_DIR.parents[1]
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from docs_document_identity import (  # noqa: E402
    DOC_TIMESTAMP_FORMAT,
    allocate_doc_id,
    doc_id_matches_added_date,
    is_immutable_doc_id,
)


PLAN_SCHEMA = "docs_document_identity_migration_v1"
SOURCE_CONFIG_PATH = Path("docs-viewer/config/scopes/docs_scopes.json")
SCOPE_MANIFEST_PATH = Path("docs-viewer/config/scopes/docs_scope_manifest.json")
DEFAULT_PLAN_PATH = Path("var/docs/document-identity/mapping.json")
FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(?P<header>.*?)\n---(?P<tail>\s*\n?)", re.DOTALL)
URL_PATTERN = re.compile(r"/(?:docs|library|analysis|moments)/\?[^\s)>'\"<]+")
ROUTE_SCOPES = {
    "/docs/": "studio",
    "/library/": "library",
    "/analysis/": "analysis",
    "/moments/": "moments",
}
IDENTITY_CONFIG_FIELDS = {
    "default_doc_id",
    "non_loadable_doc_ids",
    "manage_only_tree_root_ids",
}
PROJECTS_BASE_DIR_MARKER = "$DOTLINEFORM_PROJECTS_BASE_DIR"


def _clean_scalar(value: str) -> str:
    text = str(value or "").strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        if text[0] == '"':
            try:
                return str(json.loads(text))
            except json.JSONDecodeError:
                pass
        return text[1:-1]
    return text


def _front_matter_fields(source_text: str, path: Path) -> dict[str, str]:
    match = FRONT_MATTER_PATTERN.match(source_text)
    if not match:
        raise ValueError(f"missing parseable front matter: {path}")
    fields: dict[str, str] = {}
    for line in match.group("header").splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = _clean_scalar(value)
    return fields


def _replace_front_matter_field(source_text: str, field: str, value: str) -> str:
    match = FRONT_MATTER_PATTERN.match(source_text)
    if not match:
        raise ValueError("source front matter could not be parsed")
    header = match.group("header")
    pattern = re.compile(rf"(?m)^{re.escape(field)}\s*:\s*.*$")
    if not pattern.search(header):
        raise ValueError(f"source front matter is missing {field}")
    header = pattern.sub(f"{field}: {value}", header, count=1)
    return "---\n" + header + "\n---" + match.group("tail") + source_text[match.end():]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _resolve_source_locator(repo_root: Path, locator: str) -> Path:
    value = str(locator or "").strip()
    if value.startswith(PROJECTS_BASE_DIR_MARKER):
        projects_base = str(os.environ.get("DOTLINEFORM_PROJECTS_BASE_DIR") or "").strip()
        if not projects_base:
            raise ValueError("DOTLINEFORM_PROJECTS_BASE_DIR is required for external document migration")
        suffix = value.removeprefix(PROJECTS_BASE_DIR_MARKER).lstrip("/")
        return (Path(projects_base).expanduser() / suffix).resolve()
    path = Path(value)
    if path.is_absolute():
        raise ValueError(f"document migration source locator must use a configured marker: {value}")
    return (repo_root / path).resolve()


def _source_locator_for_path(spec: dict[str, Any], path: Path) -> str:
    relative_path = path.resolve().relative_to(Path(spec["root_path"]).resolve())
    return (Path(spec["root"]) / relative_path).as_posix()


def _namespace_specs(
    repo_root: Path,
    *,
    include_external: bool = False,
    scope_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    config = json.loads((repo_root / SOURCE_CONFIG_PATH).read_text(encoding="utf-8"))
    selected_scopes = {str(scope_id or "").strip() for scope_id in (scope_ids or set()) if str(scope_id or "").strip()}
    configured_scopes = {
        str(scope.get("scope_id") or "").strip()
        for scope in config.get("scopes") or []
        if isinstance(scope, dict)
    }
    unknown_scopes = sorted(selected_scopes - configured_scopes)
    if unknown_scopes:
        raise ValueError(f"unknown document migration scope: {', '.join(unknown_scopes)}")
    specs: list[dict[str, Any]] = []
    for scope in config.get("scopes") or []:
        if not isinstance(scope, dict):
            continue
        scope_id = str(scope.get("scope_id") or "").strip()
        if selected_scopes and scope_id not in selected_scopes:
            continue
        scope_type = str(scope.get("scope_type") or "").strip()
        if scope_type == "local_external" and not include_external:
            if scope_id in selected_scopes:
                raise ValueError(
                    f"document migration scope {scope_id!r} is external-local; pass --include-external"
                )
            continue
        source = str(scope.get("source") or "").strip()
        if not scope_id or not source:
            continue
        if source.startswith("$") and scope_type != "local_external":
            continue
        sub_sources: set[Path] = set()
        for sub_scope in scope.get("sub_scopes") or []:
            if not isinstance(sub_scope, dict):
                continue
            sub_id = str(sub_scope.get("sub_scope") or "").strip()
            sub_source = str(sub_scope.get("source") or "").strip()
            if not sub_id or not sub_source:
                continue
            if sub_source.startswith("$") and scope_type != "local_external":
                continue
            sub_source_path = _resolve_source_locator(repo_root, sub_source)
            sub_sources.add(sub_source_path)
            specs.append(
                {
                    "namespace": f"{scope_id}/{sub_id}",
                    "scope": scope_id,
                    "sub_scope": sub_id,
                    "scope_type": scope_type,
                    "root": Path(sub_source).as_posix(),
                    "root_path": sub_source_path,
                }
            )
        source_path = _resolve_source_locator(repo_root, source)
        specs.append(
            {
                "namespace": scope_id,
                "scope": scope_id,
                "sub_scope": "",
                "scope_type": scope_type,
                "root": Path(source).as_posix(),
                "root_path": source_path,
                "excluded_roots": [path.as_posix() for path in sorted(sub_sources)],
            }
        )
    return sorted(specs, key=lambda item: item["namespace"])


def _paths_for_spec(repo_root: Path, spec: dict[str, Any]) -> list[Path]:
    root = Path(spec.get("root_path") or _resolve_source_locator(repo_root, spec["root"])).resolve()
    if spec.get("scope_type") != "local_external":
        root.relative_to(repo_root.resolve())
    return sorted(root.glob("*.md"))


def _git_first_added(repo_root: Path, relative_path: str) -> str:
    result = subprocess.run(
        [
            "git",
            "log",
            "--follow",
            "--diff-filter=A",
            "--format=%aI",
            "--",
            relative_path,
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    timestamps = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return timestamps[-1] if timestamps else ""


def normalize_added_date(value: str, git_first_added: str = "") -> tuple[str, str]:
    raw = str(value or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", raw):
        dt.datetime.strptime(raw, DOC_TIMESTAMP_FORMAT)
        return raw, "front-matter-time"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", raw):
        dt.datetime.strptime(raw, "%Y-%m-%d %H:%M")
        return raw + ":00", "front-matter-time"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        dt.datetime.strptime(raw, "%Y-%m-%d")
        if git_first_added:
            git_time = dt.datetime.fromisoformat(git_first_added.replace("Z", "+00:00"))
            if git_time.strftime("%Y-%m-%d") == raw:
                return git_time.strftime(DOC_TIMESTAMP_FORMAT), "git-time-on-matching-date"
        return raw + " 00:00:00", "midnight-default"
    if not raw:
        return "1900-01-01 00:00:00", "midnight-default"
    raise ValueError(f"unsupported added_date value: {raw!r}")


def _mapping_indexes(rows: list[dict[str, Any]]) -> tuple[dict[str, dict[str, str]], dict[str, list[str]]]:
    by_namespace: dict[str, dict[str, str]] = {}
    sub_namespaces: dict[str, list[str]] = {}
    for row in rows:
        by_namespace.setdefault(row["namespace"], {})[row["old_doc_id"]] = row["new_doc_id"]
        if row.get("sub_scope"):
            sub_namespaces.setdefault(row["scope"], []).append(row["namespace"])
    for scope in sub_namespaces:
        sub_namespaces[scope] = sorted(set(sub_namespaces[scope]))
    return by_namespace, sub_namespaces


def _link_mapping_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    mappings: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        namespace = str(row.get("namespace") or "").strip()
        old_doc_id = str(row.get("old_doc_id") or "").strip()
        new_doc_id = str(row.get("new_doc_id") or "").strip()
        if not namespace or not old_doc_id or not new_doc_id:
            continue
        mappings[(namespace, old_doc_id)] = {
            "namespace": namespace,
            "scope": str(row.get("scope") or namespace.split("/", 1)[0]).strip(),
            "sub_scope": str(row.get("sub_scope") or "").strip(),
            "old_doc_id": old_doc_id,
            "new_doc_id": new_doc_id,
        }
    return [mappings[key] for key in sorted(mappings)]


def _plan_link_rows(plan: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mappings = plan.get("viewer_link_mappings")
    return mappings if isinstance(mappings, list) and mappings else rows


def _query_value(url: str, key: str) -> str:
    match = re.search(rf"(?:[?&]){re.escape(key)}=([^&#]*)", url)
    return match.group(1) if match else ""


def _replace_query_value(url: str, key: str, old_value: str, new_value: str) -> str:
    return re.sub(
        rf"([?&]{re.escape(key)}=){re.escape(old_value)}(?=&|#|$)",
        rf"\g<1>{new_value}",
        url,
        count=1,
    )


def rewrite_viewer_links(source_text: str, rows: list[dict[str, Any]]) -> tuple[str, int]:
    by_namespace, sub_namespaces = _mapping_indexes(rows)
    changed = 0

    def replace_url(match: re.Match[str]) -> str:
        nonlocal changed
        url = match.group(0)
        route = url.split("?", 1)[0]
        scope = _query_value(url, "scope") or ROUTE_SCOPES.get(route, "")
        if not scope:
            return url
        next_url = url
        old_doc_id = _query_value(url, "doc")
        new_doc_id = by_namespace.get(scope, {}).get(old_doc_id)
        if old_doc_id and new_doc_id and new_doc_id != old_doc_id:
            next_url = _replace_query_value(next_url, "doc", old_doc_id, new_doc_id)
        old_subdoc_id = _query_value(url, "subdoc")
        if old_subdoc_id:
            candidates = {
                by_namespace[namespace][old_subdoc_id]
                for namespace in sub_namespaces.get(scope, [])
                if old_subdoc_id in by_namespace.get(namespace, {})
            }
            if len(candidates) == 1:
                new_subdoc_id = next(iter(candidates))
                if new_subdoc_id != old_subdoc_id:
                    next_url = _replace_query_value(next_url, "subdoc", old_subdoc_id, new_subdoc_id)
        if next_url != url:
            changed += 1
        return next_url

    return URL_PATTERN.sub(replace_url, source_text), changed


def build_plan(
    repo_root: Path,
    *,
    include_external: bool = False,
    scope_ids: set[str] | None = None,
    additional_link_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    specs = _namespace_specs(
        repo_root,
        include_external=include_external,
        scope_ids=scope_ids,
    )
    if not specs:
        raise ValueError("document migration selection has no configured source namespaces")
    unavailable: set[str] = set()
    identity_specs = _namespace_specs(repo_root, include_external=include_external)
    for spec in identity_specs:
        for path in _paths_for_spec(repo_root, spec):
            fields = _front_matter_fields(path.read_text(encoding="utf-8"), path)
            doc_id = fields.get("doc_id", "")
            if is_immutable_doc_id(doc_id):
                unavailable.add(doc_id)
    seen_by_namespace: dict[str, set[str]] = {}
    for spec in specs:
        for path in _paths_for_spec(repo_root, spec):
            source_path = _source_locator_for_path(spec, path)
            source_text = path.read_text(encoding="utf-8")
            fields = _front_matter_fields(source_text, path)
            old_doc_id = fields.get("doc_id", "")
            if not old_doc_id:
                raise ValueError(f"missing doc_id: {source_path}")
            if old_doc_id in seen_by_namespace.setdefault(spec["namespace"], set()):
                raise ValueError(f"duplicate {spec['namespace']} doc_id: {old_doc_id}")
            seen_by_namespace[spec["namespace"]].add(old_doc_id)
            if path.stem != old_doc_id:
                raise ValueError(f"source filename does not match doc_id: {source_path}")
            git_added = ""
            if spec.get("scope_type") != "local_external":
                git_added = _git_first_added(repo_root, source_path)
            normalized_date, evidence_method = normalize_added_date(
                fields.get("added_date", ""),
                git_added,
            )
            if is_immutable_doc_id(old_doc_id):
                if not doc_id_matches_added_date(old_doc_id, normalized_date):
                    raise ValueError(
                        f"existing immutable ID timestamp does not match added_date: {source_path}"
                    )
                new_doc_id = old_doc_id
            else:
                new_doc_id = allocate_doc_id(normalized_date, unavailable)
            unavailable.add(new_doc_id)
            rows.append(
                {
                    "namespace": spec["namespace"],
                    "scope": spec["scope"],
                    "sub_scope": spec["sub_scope"],
                    "scope_type": spec.get("scope_type") or "",
                    "title": fields.get("title", ""),
                    "source_path": source_path,
                    "source_sha256": _sha256_text(source_text),
                    "old_doc_id": old_doc_id,
                    "new_doc_id": new_doc_id,
                    "old_filename": path.name,
                    "new_filename": f"{new_doc_id}.md",
                    "old_parent_id": fields.get("parent_id", ""),
                    "new_parent_id": "",
                    "original_added_date": fields.get("added_date", ""),
                    "normalized_added_date": normalized_date,
                    "timestamp_evidence": evidence_method,
                    "git_first_added": git_added,
                }
            )

    rows.sort(key=lambda row: (row["namespace"], row["source_path"]))
    by_namespace, _sub_namespaces = _mapping_indexes(rows)
    for row in rows:
        old_parent_id = row["old_parent_id"]
        if old_parent_id:
            parent_map = by_namespace[row["namespace"]]
            if old_parent_id not in parent_map:
                raise ValueError(
                    f"unresolved parent {old_parent_id!r} for {row['source_path']}"
                )
            row["new_parent_id"] = parent_map[old_parent_id]

    link_rows = _link_mapping_rows([*(additional_link_rows or []), *rows])
    link_changes = 0
    for row in rows:
        source_text = _resolve_source_locator(repo_root, row["source_path"]).read_text(encoding="utf-8")
        _rewritten, count = rewrite_viewer_links(source_text, link_rows)
        row["viewer_link_rewrites"] = count
        link_changes += count

    evidence_counts: dict[str, int] = {}
    for row in rows:
        evidence = row["timestamp_evidence"]
        evidence_counts[evidence] = evidence_counts.get(evidence, 0) + 1
    plan = {
        "schema_version": PLAN_SCHEMA,
        "created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "repository": repo_root.resolve().as_posix(),
        "source_config": SOURCE_CONFIG_PATH.as_posix(),
        "scope_manifest": SCOPE_MANIFEST_PATH.as_posix(),
        "summary": {
            "documents": len(rows),
            "renames": sum(row["old_doc_id"] != row["new_doc_id"] for row in rows),
            "preserved_immutable_ids": sum(row["old_doc_id"] == row["new_doc_id"] for row in rows),
            "viewer_link_rewrites": link_changes,
            "timestamp_evidence": evidence_counts,
            "scopes": sorted({row["scope"] for row in rows}),
        },
        "documents": rows,
    }
    if additional_link_rows:
        plan["viewer_link_mappings"] = link_rows
    return plan


def _rewrite_identity_config(value: Any, identity_map: dict[str, str]) -> Any:
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            if key in IDENTITY_CONFIG_FIELDS:
                if isinstance(item, str):
                    output[key] = identity_map.get(item, item)
                elif isinstance(item, list):
                    output[key] = [identity_map.get(str(entry), entry) for entry in item]
                else:
                    output[key] = item
            else:
                output[key] = _rewrite_identity_config(item, identity_map)
        return output
    if isinstance(value, list):
        return [_rewrite_identity_config(item, identity_map) for item in value]
    return value


def _rewrite_exact_paths(value: Any, path_map: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _rewrite_exact_paths(item, path_map) for key, item in value.items()}
    if isinstance(value, list):
        return [_rewrite_exact_paths(item, path_map) for item in value]
    if isinstance(value, str):
        return path_map.get(value, value)
    return value


def _rewritten_config_texts(repo_root: Path, rows: list[dict[str, Any]]) -> dict[Path, str]:
    by_namespace, _sub_namespaces = _mapping_indexes(rows)
    outputs: dict[Path, str] = {}
    source_path = repo_root / SOURCE_CONFIG_PATH
    source_config = json.loads(source_path.read_text(encoding="utf-8"))
    for scope in source_config.get("scopes") or []:
        if not isinstance(scope, dict):
            continue
        scope_id = str(scope.get("scope_id") or "")
        if scope_id in by_namespace:
            rewritten = _rewrite_identity_config(scope, by_namespace[scope_id])
            scope.clear()
            scope.update(rewritten)
    outputs[source_path] = _json_text(source_config)

    manifest_path = repo_root / SCOPE_MANIFEST_PATH
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_path_map: dict[str, str] = {}
    for row in rows:
        old_locator = str(row["source_path"])
        new_locator = str(Path(old_locator).with_name(row["new_filename"]))
        source_path_map[old_locator] = new_locator
        old_resolved = _resolve_source_locator(repo_root, old_locator)
        source_path_map[old_resolved.as_posix()] = old_resolved.with_name(row["new_filename"]).as_posix()
    for scope in manifest.get("scopes") or []:
        if not isinstance(scope, dict):
            continue
        scope_id = str(scope.get("scope_id") or "")
        if scope_id in by_namespace:
            rewritten = _rewrite_identity_config(scope, by_namespace[scope_id])
            scope.clear()
            scope.update(rewritten)
    manifest = _rewrite_exact_paths(manifest, source_path_map)
    outputs[manifest_path] = _json_text(manifest)
    return outputs


def _plan_namespace_specs(repo_root: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scope_ids = {str(row.get("scope") or "").strip() for row in rows}
    include_external = any(
        row.get("scope_type") == "local_external"
        or str(row.get("source_path") or "").startswith(PROJECTS_BASE_DIR_MARKER)
        for row in rows
    )
    return _namespace_specs(
        repo_root,
        include_external=include_external,
        scope_ids=scope_ids,
    )


def apply_plan(repo_root: Path, plan: dict[str, Any]) -> dict[str, int]:
    if plan.get("schema_version") != PLAN_SCHEMA:
        raise ValueError(f"unsupported migration plan schema: {plan.get('schema_version')!r}")
    rows = plan.get("documents")
    if not isinstance(rows, list) or not rows:
        raise ValueError("migration plan has no document rows")
    link_rows = _plan_link_rows(plan, rows)
    current_paths = {
        _source_locator_for_path(spec, path)
        for spec in _plan_namespace_specs(repo_root, rows)
        for path in _paths_for_spec(repo_root, spec)
    }
    planned_paths = {str(row.get("source_path") or "") for row in rows if isinstance(row, dict)}
    if current_paths != planned_paths:
        raise ValueError("repository-owned source set changed after the migration plan was created")

    rewritten_sources: dict[Path, str] = {}
    old_paths_to_delete: list[Path] = []
    for row in rows:
        source_path = _resolve_source_locator(repo_root, row["source_path"])
        source_text = source_path.read_text(encoding="utf-8")
        if _sha256_text(source_text) != row["source_sha256"]:
            raise ValueError(f"source changed after plan creation: {row['source_path']}")
        target_path = source_path.with_name(row["new_filename"])
        if row.get("scope_type") != "local_external":
            target_path.relative_to(repo_root.resolve())
        if target_path != source_path and target_path.exists():
            target_locator = str(Path(row["source_path"]).with_name(row["new_filename"]))
            raise ValueError(f"migration destination already exists: {target_locator}")
        rewritten = _replace_front_matter_field(source_text, "doc_id", row["new_doc_id"])
        rewritten = _replace_front_matter_field(
            rewritten,
            "added_date",
            row["normalized_added_date"],
        )
        if row["old_parent_id"]:
            rewritten = _replace_front_matter_field(rewritten, "parent_id", row["new_parent_id"])
        rewritten, _link_count = rewrite_viewer_links(rewritten, link_rows)
        rewritten_sources[target_path] = rewritten
        if target_path != source_path:
            old_paths_to_delete.append(source_path)

    config_texts = _rewritten_config_texts(repo_root, rows)
    for path, text in rewritten_sources.items():
        _write_text_atomic(path, text)
    for path, text in config_texts.items():
        _write_text_atomic(path, text)
    for path in old_paths_to_delete:
        path.unlink()
    return {
        "documents": len(rows),
        "renamed": len(old_paths_to_delete),
        "source_writes": len(rewritten_sources),
        "config_writes": len(config_texts),
    }


def verify_applied_plan(repo_root: Path, plan: dict[str, Any]) -> dict[str, int]:
    if plan.get("schema_version") != PLAN_SCHEMA:
        raise ValueError(f"unsupported migration plan schema: {plan.get('schema_version')!r}")
    rows = plan.get("documents")
    if not isinstance(rows, list) or not rows:
        raise ValueError("migration plan has no document rows")
    link_rows = _plan_link_rows(plan, rows)
    expected_paths = {
        str(Path(row["source_path"]).with_name(row["new_filename"]))
        for row in rows
    }
    current_paths = {
        _source_locator_for_path(spec, path)
        for spec in _plan_namespace_specs(repo_root, rows)
        for path in _paths_for_spec(repo_root, spec)
    }
    if current_paths != expected_paths:
        raise ValueError("applied repository-owned source set does not match the migration plan")
    link_rewrites_remaining = 0
    for row in rows:
        target_locator = str(Path(row["source_path"]).with_name(row["new_filename"]))
        target_path = _resolve_source_locator(repo_root, target_locator)
        source_text = target_path.read_text(encoding="utf-8")
        fields = _front_matter_fields(source_text, target_path)
        if fields.get("doc_id") != row["new_doc_id"]:
            raise ValueError(f"applied doc_id does not match plan: {target_locator}")
        if fields.get("added_date") != row["normalized_added_date"]:
            raise ValueError(f"applied added_date does not match plan: {target_locator}")
        if fields.get("parent_id", "") != row["new_parent_id"]:
            raise ValueError(f"applied parent_id does not match plan: {target_locator}")
        _rewritten, count = rewrite_viewer_links(source_text, link_rows)
        link_rewrites_remaining += count
    if link_rewrites_remaining:
        raise ValueError(f"{link_rewrites_remaining} old viewer links remain after migration")
    expected_config = _rewritten_config_texts(repo_root, rows)
    for path, expected_text in expected_config.items():
        if path.read_text(encoding="utf-8") != expected_text:
            raise ValueError(f"applied config does not match plan: {path.relative_to(repo_root)}")
    return {
        "documents": len(rows),
        "source_paths": len(current_paths),
        "viewer_link_rewrites_remaining": link_rewrites_remaining,
        "config_files": len(expected_config),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "apply", "verify"))
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN_PATH)
    parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="Limit a new plan to one configured scope; repeat to select more than one.",
    )
    parser.add_argument(
        "--include-external",
        action="store_true",
        help="Allow selected external-local scopes in a new migration plan.",
    )
    parser.add_argument(
        "--link-plan",
        action="append",
        type=Path,
        default=[],
        help="Use document mappings from another plan when rewriting cross-scope links.",
    )
    return parser


def _plan_display_path(repo_root: Path, plan_path: Path) -> str:
    try:
        return plan_path.relative_to(repo_root).as_posix()
    except ValueError:
        return plan_path.as_posix()


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    plan_path = args.plan if args.plan.is_absolute() else repo_root / args.plan
    if args.command == "plan":
        additional_link_rows: list[dict[str, Any]] = []
        for link_plan_arg in args.link_plan:
            link_plan_path = link_plan_arg if link_plan_arg.is_absolute() else repo_root / link_plan_arg
            link_plan = json.loads(link_plan_path.read_text(encoding="utf-8"))
            link_rows = link_plan.get("viewer_link_mappings") or link_plan.get("documents")
            if not isinstance(link_rows, list):
                raise ValueError(f"link plan has no document mappings: {link_plan_path}")
            additional_link_rows.extend(link_rows)
        plan = build_plan(
            repo_root,
            include_external=args.include_external,
            scope_ids=set(args.scope),
            additional_link_rows=additional_link_rows,
        )
        _write_text_atomic(plan_path, _json_text(plan))
        print(_json_text({"plan": _plan_display_path(repo_root, plan_path), **plan["summary"]}), end="")
        return 0
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    result = apply_plan(repo_root, plan) if args.command == "apply" else verify_applied_plan(repo_root, plan)
    print(_json_text({"plan": _plan_display_path(repo_root, plan_path), **result}), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
