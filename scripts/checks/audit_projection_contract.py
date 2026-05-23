#!/usr/bin/env python3
"""Validate the projection contract manifest and enforce mechanical rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


DEFAULT_CONTRACT_PATH = Path("scripts/checks/projection_contract.json")
VALID_CLASSIFICATIONS = {
    "canonical_source",
    "public_projection",
    "studio_projection",
    "docs_viewer_payload",
    "local_working_output",
    "public_runtime_asset",
    "studio_app_asset",
}
VALID_PUBLIC_OUTPUT_POLICIES = {"required", "allowed", "forbidden", "ignored"}


class ProjectionContractError(ValueError):
    """Raised when the projection contract manifest is malformed."""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def as_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProjectionContractError(f"{label} must be a non-empty string")
    return value.strip()


def as_string_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise ProjectionContractError(f"{label} must be a list")
    out: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ProjectionContractError(f"{label}[{index}] must be a non-empty string")
        out.append(item.strip())
    if not allow_empty and not out:
        raise ProjectionContractError(f"{label} must not be empty")
    return out


def load_contract(contract_path: Path) -> dict[str, Any]:
    payload = load_json(contract_path)
    if not isinstance(payload, dict):
        raise ProjectionContractError("projection contract must be a JSON object")
    if payload.get("schema_version") != "projection_contract_v1":
        raise ProjectionContractError("projection contract schema_version must be projection_contract_v1")
    validate_contract(payload)
    return payload


def validate_contract(contract: Mapping[str, Any]) -> None:
    families = contract.get("artifact_families")
    if not isinstance(families, list) or not families:
        raise ProjectionContractError("artifact_families must be a non-empty list")

    seen_family_ids: set[str] = set()
    seen_repo_paths: dict[str, str] = {}
    seen_output_paths: dict[str, str] = {}
    for index, family in enumerate(families):
        if not isinstance(family, dict):
            raise ProjectionContractError(f"artifact_families[{index}] must be an object")
        family_id = as_nonempty_string(family.get("id"), f"artifact_families[{index}].id")
        if family_id in seen_family_ids:
            raise ProjectionContractError(f"duplicate artifact family id: {family_id}")
        seen_family_ids.add(family_id)

        classification = as_nonempty_string(family.get("classification"), f"{family_id}.classification")
        if classification not in VALID_CLASSIFICATIONS:
            raise ProjectionContractError(f"{family_id}.classification is invalid: {classification}")
        owner_doc = as_nonempty_string(family.get("owner_doc"), f"{family_id}.owner_doc")
        if "/" in owner_doc:
            raise ProjectionContractError(f"{family_id}.owner_doc must be a doc_id, not a path")

        repo_paths = as_string_list(family.get("repo_paths"), f"{family_id}.repo_paths")
        for repo_path in repo_paths:
            previous = seen_repo_paths.get(repo_path)
            if previous:
                raise ProjectionContractError(
                    f"repo path {repo_path!r} appears in both {previous} and {family_id}"
                )
            seen_repo_paths[repo_path] = family_id

        public_output = family.get("public_output")
        if not isinstance(public_output, dict):
            raise ProjectionContractError(f"{family_id}.public_output must be an object")
        policy = as_nonempty_string(public_output.get("policy"), f"{family_id}.public_output.policy")
        if policy not in VALID_PUBLIC_OUTPUT_POLICIES:
            raise ProjectionContractError(f"{family_id}.public_output.policy is invalid: {policy}")
        output_paths = as_string_list(
            public_output.get("paths"),
            f"{family_id}.public_output.paths",
            allow_empty=policy == "ignored",
        )
        for output_path in output_paths:
            key = f"{policy}:{output_path}"
            previous = seen_output_paths.get(key)
            if previous:
                raise ProjectionContractError(
                    f"public output path {output_path!r} appears in both {previous} and {family_id}"
                )
            seen_output_paths[key] = family_id

    for index, rule in enumerate(contract.get("field_leak_rules", [])):
        if not isinstance(rule, dict):
            raise ProjectionContractError(f"field_leak_rules[{index}] must be an object")
        rule_id = as_nonempty_string(rule.get("id"), f"field_leak_rules[{index}].id")
        as_string_list(rule.get("fields"), f"{rule_id}.fields")
        as_string_list(rule.get("public_paths"), f"{rule_id}.public_paths")

    public_docs_viewer = contract.get("public_docs_viewer")
    if not isinstance(public_docs_viewer, dict):
        raise ProjectionContractError("public_docs_viewer must be an object")
    as_nonempty_string(public_docs_viewer.get("config_path"), "public_docs_viewer.config_path")
    as_string_list(public_docs_viewer.get("allowed_scope_ids"), "public_docs_viewer.allowed_scope_ids")
    as_string_list(contract.get("public_html_forbidden_hrefs"), "public_html_forbidden_hrefs", allow_empty=True)
    source_audit = contract.get("public_source_reference_audit")
    if not isinstance(source_audit, dict):
        raise ProjectionContractError("public_source_reference_audit must be an object")
    as_string_list(source_audit.get("scan_paths"), "public_source_reference_audit.scan_paths")
    as_string_list(source_audit.get("ignore_paths"), "public_source_reference_audit.ignore_paths", allow_empty=True)
    as_string_list(source_audit.get("forbidden_substrings"), "public_source_reference_audit.forbidden_substrings")


def split_exclude_values(config_path: Path) -> list[str]:
    if not config_path.exists():
        return []
    values: list[str] = []
    in_exclude = False
    for raw_line in read_text(config_path).splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw_line and not raw_line.startswith((" ", "\t", "-")):
            in_exclude = stripped == "exclude:"
            continue
        if not in_exclude:
            continue
        if stripped.startswith("- "):
            value = stripped[2:].strip().strip("'\"").rstrip("/")
            if value:
                values.append(value)
    return values


def root_for_pattern(path_pattern: str) -> str:
    parts: list[str] = []
    for part in PurePosixPath(path_pattern).parts:
        if any(char in part for char in "*?["):
            break
        parts.append(part)
    if not parts:
        return path_pattern.rstrip("/")
    root = PurePosixPath(*parts).as_posix()
    if "." in PurePosixPath(root).name and root == path_pattern:
        return root
    return root.rstrip("/")


def path_is_covered_by_exclude(path_pattern: str, excludes: Iterable[str]) -> bool:
    root = root_for_pattern(path_pattern)
    for raw_exclude in excludes:
        exclude = raw_exclude.rstrip("/")
        if not exclude:
            continue
        if root == exclude or root.startswith(f"{exclude}/"):
            return True
    return False


def audit_jekyll_exclusions(repo_root: Path, contract: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    excludes = split_exclude_values(repo_root / "_config.yml")
    for family in contract["artifact_families"]:
        if not family.get("jekyll_exclude_required"):
            continue
        family_id = family["id"]
        for path_pattern in family["repo_paths"]:
            if not path_is_covered_by_exclude(path_pattern, excludes):
                failures.append(
                    f"{family_id}: {_config_rel(path_pattern)} is not covered by _config.yml exclude"
                )
    return failures


def _config_rel(path_pattern: str) -> str:
    return path_pattern


def glob_matches(root: Path, path_pattern: str) -> list[Path]:
    if any(char in path_pattern for char in "*?["):
        return sorted(root.glob(path_pattern))
    path = root / path_pattern
    return [path] if path.exists() else []


def scan_json_for_fields(path: Path, fields: set[str]) -> list[str]:
    try:
        payload = load_json(path)
    except json.JSONDecodeError as exc:
        return [f"{relative(path, path.parent)} is invalid JSON: {exc}"]

    hits: list[str] = []

    def visit(value: Any, pointer: str = "$") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_pointer = f"{pointer}.{key}" if pointer != "$" else f"$.{key}"
                if key in fields:
                    hits.append(child_pointer)
                visit(child, child_pointer)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{pointer}[{index}]")

    visit(payload)
    return hits


def audit_field_leaks(repo_root: Path, contract: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for rule in contract.get("field_leak_rules", []):
        rule_id = rule["id"]
        fields = set(rule["fields"])
        for path_pattern in rule["public_paths"]:
            matches = glob_matches(repo_root, path_pattern)
            if not matches:
                failures.append(f"{rule_id}: no files matched public path {path_pattern}")
                continue
            for path in matches:
                if path.is_dir() or path.suffix.lower() != ".json":
                    continue
                hits = scan_json_for_fields(path, fields)
                if hits:
                    failures.append(
                        f"{rule_id}: {relative(path, repo_root)} contains source-only fields at {', '.join(hits[:8])}"
                    )
    return failures


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(PurePosixPath(path).match(pattern) for pattern in patterns)


def source_reference_scan_files(repo_root: Path, source_audit: Mapping[str, Any]) -> list[Path]:
    files: dict[str, Path] = {}
    ignore_paths = list(source_audit.get("ignore_paths", []))
    for pattern in source_audit.get("scan_paths", []):
        for path in sorted(repo_root.glob(pattern)):
            if not path.is_file():
                continue
            rel_path = relative(path, repo_root)
            if matches_any(rel_path, ignore_paths):
                continue
            files[rel_path] = path
    return [files[key] for key in sorted(files)]


def audit_public_source_references(repo_root: Path, contract: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    source_audit = contract.get("public_source_reference_audit")
    if not isinstance(source_audit, Mapping):
        return ["public_source_reference_audit must be configured"]
    forbidden_substrings = list(source_audit.get("forbidden_substrings", []))
    for path in source_reference_scan_files(repo_root, source_audit):
        rel_path = relative(path, repo_root)
        for line_number, line in enumerate(read_text(path).splitlines(), start=1):
            for forbidden in forbidden_substrings:
                if forbidden in line:
                    failures.append(
                        f"public source reference audit: {rel_path}:{line_number} contains {forbidden!r}"
                    )
    return failures


def audit_public_docs_viewer_config(site_root: Path, contract: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    config_spec = contract["public_docs_viewer"]
    config_path = site_root / config_spec["config_path"]
    if not config_path.exists():
        return [f"public Docs Viewer config missing: {config_spec['config_path']}"]
    try:
        config = load_json(config_path)
    except json.JSONDecodeError as exc:
        return [f"public Docs Viewer config is invalid JSON: {exc}"]
    scopes = config.get("scopes")
    scope_ids = {
        str(scope.get("scope_id", "")).strip().lower()
        for scope in scopes
        if isinstance(scope, dict)
    } if isinstance(scopes, list) else set()
    allowed_scope_ids = {str(scope_id).strip().lower() for scope_id in config_spec["allowed_scope_ids"]}
    if scope_ids != allowed_scope_ids:
        failures.append(
            "public Docs Viewer config scopes must be "
            f"{sorted(allowed_scope_ids)}, got {sorted(scope_ids)}"
        )
    return failures


def audit_public_html_hrefs(site_root: Path, contract: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    forbidden_hrefs = list(contract.get("public_html_forbidden_hrefs", []))
    if not forbidden_hrefs:
        return failures
    for html_path in sorted(site_root.rglob("*.html")):
        if not html_path.exists():
            continue
        text = read_text(html_path)
        for forbidden in forbidden_hrefs:
            if forbidden in text:
                failures.append(f"forbidden public link {forbidden!r} in {relative(html_path, site_root)}")
    return failures


def audit_public_build(site_root: Path, contract: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    root = site_root.resolve()
    if not root.exists():
        return [f"site root does not exist: {site_root}"]
    if not root.is_dir():
        return [f"site root is not a directory: {site_root}"]

    for family in contract["artifact_families"]:
        family_id = family["id"]
        public_output = family["public_output"]
        policy = public_output["policy"]
        paths = public_output.get("paths", [])
        if policy == "required":
            for path_pattern in paths:
                if not glob_matches(root, path_pattern):
                    failures.append(f"{family_id}: required public output missing: {path_pattern}")
        elif policy == "forbidden":
            for path_pattern in paths:
                matches = glob_matches(root, path_pattern)
                if matches:
                    samples = ", ".join(relative(path, root) for path in matches[:5])
                    failures.append(f"{family_id}: forbidden public output present: {samples}")

    failures.extend(audit_public_docs_viewer_config(root, contract))
    failures.extend(audit_public_html_hrefs(root, contract))
    return failures


def print_failures(failures: list[str]) -> None:
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=Path.cwd(), type=Path)
    parser.add_argument("--contract", default=DEFAULT_CONTRACT_PATH, type=Path)
    parser.add_argument("--site-root", type=Path, help="Optional built public site root to audit.")
    parser.add_argument(
        "--skip-field-leaks",
        action="store_true",
        help="Validate the manifest without scanning checked-in public JSON projections.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    contract_path = args.contract if args.contract.is_absolute() else repo_root / args.contract
    try:
        contract = load_contract(contract_path)
    except (OSError, json.JSONDecodeError, ProjectionContractError) as exc:
        print(f"FAIL: projection contract invalid: {exc}", file=sys.stderr)
        return 1

    failures: list[str] = []
    failures.extend(audit_jekyll_exclusions(repo_root, contract))
    failures.extend(audit_public_source_references(repo_root, contract))
    if not args.skip_field_leaks:
        failures.extend(audit_field_leaks(repo_root, contract))
    if args.site_root:
        failures.extend(audit_public_build(args.site_root, contract))

    if failures:
        print_failures(failures)
        return 1

    print(f"projection contract OK: {relative(contract_path, repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
