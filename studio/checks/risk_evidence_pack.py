#!/usr/bin/env python3
"""Collect repeatable Studio risk evidence into a local run directory."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_ROOT = REPO_ROOT / "var" / "studio" / "risk" / "runs"
COMMAND_VERSION = "1"
DEFAULT_HISTORY_WINDOW = "90 days"

VALID_APPS = ("public-site", "studio", "analytics", "docs-viewer", "all")
APP_ROOTS: dict[str, tuple[str, ...]] = {
    "public-site": ("_config.yml", "_includes", "_layouts", "assets/css", "assets/js", "index.md", "series", "work"),
    "studio": ("studio", "ui-catalogue-app"),
    "analytics": ("analytics-app",),
    "docs-viewer": ("docs-viewer", "assets/docs"),
}
RUNTIME_PROFILE_BY_APP: dict[str, tuple[str, ...]] = {
    "public-site": ("studio-smoke",),
    "studio": ("studio-smoke", "ui-catalogue-smoke"),
    "analytics": ("analytics-smoke",),
    "docs-viewer": ("docs-viewer-smoke",),
    "all": ("studio-smoke", "ui-catalogue-smoke", "analytics-smoke", "docs-viewer-smoke"),
}

METRIC_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".liquid",
    ".md",
    ".py",
    ".rb",
    ".scss",
    ".ts",
    ".yaml",
    ".yml",
}
GENERATED_PAYLOAD_ROOTS = (
    "assets/data",
    "docs-viewer/generated",
    "studio/data/generated",
    "studio/workflows/change-requests/generated",
)
SCRIPT_INVENTORY_ROOTS = ("studio", "docs-viewer", "analytics-app", "data-sharing")
STATIC_METRIC_EXCLUDED_PREFIXES: tuple[tuple[str, ...], ...] = (
    ("assets", "data"),
    ("docs-viewer", "generated"),
    ("studio", "data", "canonical"),
    ("studio", "data", "generated"),
    ("studio", "workflows", "change-requests", "generated"),
    ("studio", "workflows", "change-requests", "reports"),
    ("analytics-app", "data", "canonical"),
)
EXCLUDED_DIRS = {
    ".git",
    ".jekyll-cache",
    ".pytest_cache",
    "__pycache__",
    "_site",
    "node_modules",
    "vendor",
    "var",
}
SCRIPT_INVENTORY_EXCLUDED_PARTS = {"tests", "test", "smoke", "__pycache__"}
STATIC_SEARCH_PATTERNS: tuple[tuple[str, str], ...] = (
    ("todo_markers", r"\b(TODO|FIXME|HACK|XXX)\b"),
    ("broad_browser_state", r"\b(window|document)\.[A-Za-z0-9_$]*State\b|\bwindow\.[A-Za-z0-9_$]*Config\b"),
    ("browser_storage", r"\b(localStorage|sessionStorage)\b"),
    ("local_service_url", r"\b(127\.0\.0\.1|localhost):[0-9]{2,5}\b"),
    ("generated_path_reference", r"\b(assets/data|docs-viewer/generated|studio/data/generated)/"),
    ("legacy_or_retired", r"\b(legacy|retired|deprecated|compatibility)\b"),
)


@dataclass(frozen=True)
class PlannedArtifact:
    name: str
    path: str
    producer: str


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip().lower())
    return value.strip("-") or "risk"


def command_text(argv: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in argv)


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def default_run_id(app: str, area: str) -> str:
    suffix = slugify(f"{app}-{area}")
    return f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-{suffix}"


def repo_relative(path: Path, repo_root: Path = REPO_ROOT) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def selected_root_paths(app: str, repo_root: Path = REPO_ROOT) -> list[Path]:
    names = APP_ROOTS.keys() if app == "all" else (app,)
    paths: list[Path] = []
    seen: set[Path] = set()
    for name in names:
        for rel_path in APP_ROOTS[name]:
            path = repo_root / rel_path
            if path in seen or not path.exists():
                continue
            seen.add(path)
            paths.append(path)
    return paths


def relative_parts(path: Path, repo_root: Path) -> tuple[str, ...]:
    try:
        return path.relative_to(repo_root).parts
    except ValueError:
        return path.parts


def iter_source_files(roots: Iterable[Path], repo_root: Path = REPO_ROOT) -> Iterable[Path]:
    for root in roots:
        if root.is_file():
            if root.suffix in METRIC_EXTENSIONS:
                yield root
            continue
        for path in root.rglob("*"):
            if path.is_dir():
                continue
            if path.suffix not in METRIC_EXTENSIONS:
                continue
            parts = relative_parts(path, repo_root)
            if EXCLUDED_DIRS.intersection(parts):
                continue
            if any(parts[: len(prefix)] == prefix for prefix in STATIC_METRIC_EXCLUDED_PREFIXES):
                continue
            yield path


def count_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _line in handle)
    except OSError:
        return 0


def file_family(path: Path, repo_root: Path = REPO_ROOT) -> str:
    rel = Path(repo_relative(path, repo_root))
    parts = rel.parts
    if not parts:
        return "root"
    if parts[0] == "assets" and len(parts) > 1:
        return f"assets/{parts[1]}"
    if parts[0] in {"studio", "docs-viewer", "analytics-app", "ui-catalogue-app"}:
        return parts[0]
    return parts[0]


def collect_static_metrics(app: str, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    roots = selected_root_paths(app, repo_root)
    files = sorted(iter_source_files(roots, repo_root))
    by_extension: collections.Counter[str] = collections.Counter()
    by_family: dict[str, dict[str, int]] = collections.defaultdict(lambda: {"files": 0, "lines": 0, "bytes": 0})
    largest_files: list[dict[str, object]] = []
    total_lines = 0
    total_bytes = 0

    for path in files:
        lines = count_lines(path)
        size = path.stat().st_size
        total_lines += lines
        total_bytes += size
        by_extension[path.suffix or "[none]"] += 1
        family = by_family[file_family(path, repo_root)]
        family["files"] += 1
        family["lines"] += lines
        family["bytes"] += size
        largest_files.append({"path": repo_relative(path, repo_root), "lines": lines, "bytes": size})

    return {
        "app": app,
        "roots": [repo_relative(path, repo_root) for path in roots],
        "totals": {"files": len(files), "lines": total_lines, "bytes": total_bytes},
        "by_extension": dict(sorted(by_extension.items())),
        "by_family": [
            {"family": family, **values}
            for family, values in sorted(by_family.items(), key=lambda item: (-item[1]["lines"], item[0]))
        ],
        "largest_files": sorted(largest_files, key=lambda item: (-int(item["lines"]), str(item["path"])))[:25],
    }


def import_export_scan(app: str, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    roots = selected_root_paths(app, repo_root)
    files = sorted(iter_source_files(roots, repo_root))
    summary: dict[str, dict[str, int]] = collections.defaultdict(lambda: {"files": 0, "imports": 0, "exports": 0})
    cross_app_refs: list[dict[str, object]] = []
    file_results: list[dict[str, object]] = []
    app_tokens = ("analytics-app", "docs-viewer", "studio", "ui-catalogue-app", "assets/js")

    for path in files:
        if path.suffix not in {".js", ".py", ".rb"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel_path = repo_relative(path, repo_root)
        if path.suffix == ".js":
            imports = re.findall(r"^\s*import\b|^\s*import\s*\(", text, flags=re.MULTILINE)
            exports = re.findall(r"^\s*export\b", text, flags=re.MULTILINE)
            specifiers = re.findall(r"\bfrom\s+['\"]([^'\"]+)['\"]|import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", text)
            dependencies = sorted({left or right for left, right in specifiers if left or right})
        elif path.suffix == ".py":
            imports = re.findall(r"^\s*(?:import|from)\s+[A-Za-z0-9_.]+", text, flags=re.MULTILINE)
            exports = []
            dependencies = sorted({match.split()[1].split(".")[0] for match in imports if len(match.split()) > 1})
        else:
            imports = re.findall(r"^\s*(?:require|load)\s+['\"]([^'\"]+)['\"]", text, flags=re.MULTILINE)
            exports = []
            dependencies = sorted(set(imports))

        family = file_family(path, repo_root)
        summary[family]["files"] += 1
        summary[family]["imports"] += len(imports)
        summary[family]["exports"] += len(exports)
        for dependency in dependencies:
            if any(token in dependency for token in app_tokens):
                cross_app_refs.append({"path": rel_path, "dependency": dependency})
        file_results.append(
            {
                "path": rel_path,
                "family": family,
                "imports": len(imports),
                "exports": len(exports),
                "dependencies": dependencies[:50],
            }
        )

    return {
        "app": app,
        "totals": {
            "files": len(file_results),
            "imports": sum(item["imports"] for item in file_results),
            "exports": sum(item["exports"] for item in file_results),
            "cross_app_references": len(cross_app_refs),
        },
        "by_family": [
            {"family": family, **values}
            for family, values in sorted(summary.items(), key=lambda item: (-item[1]["imports"], item[0]))
        ],
        "cross_app_references": cross_app_refs[:100],
        "files": file_results,
    }


def collect_static_searches(app: str, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    roots = selected_root_paths(app, repo_root)
    files = sorted(iter_source_files(roots, repo_root))
    pattern_results: list[dict[str, object]] = []
    for name, pattern in STATIC_SEARCH_PATTERNS:
        regex = re.compile(pattern, re.IGNORECASE)
        matched_paths: set[str] = set()
        matches: list[dict[str, object]] = []
        count = 0
        for path in files:
            rel_path = repo_relative(path, repo_root)
            for number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
                if not regex.search(line):
                    continue
                count += 1
                matched_paths.add(rel_path)
                if len(matches) < 40:
                    matches.append({"path": rel_path, "line": number, "excerpt": line.strip()[:220]})
        pattern_results.append(
            {
                "name": name,
                "pattern": pattern,
                "match_count": count,
                "matched_path_count": len(matched_paths),
                "matches": matches,
            }
        )
    return {"app": app, "patterns": pattern_results}


def json_shape(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        return {"valid_json": False, "error": str(error)}
    if isinstance(payload, dict):
        return {"valid_json": True, "top_level_type": "object", "top_level_keys": sorted(payload.keys())[:30]}
    if isinstance(payload, list):
        return {"valid_json": True, "top_level_type": "array", "items": len(payload)}
    return {"valid_json": True, "top_level_type": type(payload).__name__}


def collect_generated_payloads(app: str, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    roots = [repo_root / root for root in GENERATED_PAYLOAD_ROOTS if (repo_root / root).exists()]
    payloads: list[dict[str, object]] = []
    by_root: dict[str, dict[str, int]] = collections.defaultdict(lambda: {"files": 0, "bytes": 0})
    for root in roots:
        for path in sorted(root.rglob("*.json")):
            if EXCLUDED_DIRS.intersection(relative_parts(path, repo_root)):
                continue
            size = path.stat().st_size
            root_name = repo_relative(root, repo_root)
            by_root[root_name]["files"] += 1
            by_root[root_name]["bytes"] += size
            payloads.append({"path": repo_relative(path, repo_root), "bytes": size, **json_shape(path)})

    return {
        "app": app,
        "roots": [repo_relative(root, repo_root) for root in roots],
        "totals": {"files": len(payloads), "bytes": sum(int(item["bytes"]) for item in payloads)},
        "by_root": [{"root": root, **values} for root, values in sorted(by_root.items())],
        "largest_payloads": sorted(payloads, key=lambda item: (-int(item["bytes"]), str(item["path"])))[:30],
    }


def script_family(path: Path, repo_root: Path = REPO_ROOT) -> str:
    rel = Path(repo_relative(path, repo_root))
    parts = rel.parts
    if not parts:
        return "root"
    if parts[:3] == ("studio", "services", "catalogue"):
        return "studio/services/catalogue"
    if parts[:2] == ("studio", "checks"):
        return "studio/checks"
    if parts[:4] == ("studio", "app", "server", "studio"):
        return "studio/app/server/studio"
    if parts[:4] == ("analytics-app", "app", "server", "analytics_app"):
        if len(parts) > 4 and parts[4] == "tag_services":
            return "analytics-app/app/server/analytics_app/tag_services"
        return "analytics-app/app/server/analytics_app"
    if parts and parts[0] == "docs-viewer":
        return "docs-viewer"
    if parts and parts[0] == "data-sharing":
        return "data-sharing"
    return parts[0]


def iter_script_inventory_files(repo_root: Path = REPO_ROOT) -> Iterable[Path]:
    roots = [repo_root / root for root in SCRIPT_INVENTORY_ROOTS if (repo_root / root).exists()]
    for root in roots:
        for path in root.rglob("*"):
            if path.is_dir():
                continue
            if path.suffix not in {".py", ".rb"}:
                continue
            parts = set(relative_parts(path, repo_root))
            if EXCLUDED_DIRS.intersection(parts) or SCRIPT_INVENTORY_EXCLUDED_PARTS.intersection(parts):
                continue
            yield path


def collect_script_family_inventory(repo_root: Path = REPO_ROOT) -> dict[str, object]:
    files = sorted(iter_script_inventory_files(repo_root))
    by_family: dict[str, dict[str, object]] = collections.defaultdict(
        lambda: {"files": 0, "lines": 0, "python": 0, "ruby": 0, "largest_file": None}
    )
    largest_files: list[dict[str, object]] = []
    by_extension: collections.Counter[str] = collections.Counter()

    for path in files:
        lines = count_lines(path)
        family_name = script_family(path, repo_root)
        row = by_family[family_name]
        row["files"] = int(row["files"]) + 1
        row["lines"] = int(row["lines"]) + lines
        if path.suffix == ".py":
            row["python"] = int(row["python"]) + 1
        elif path.suffix == ".rb":
            row["ruby"] = int(row["ruby"]) + 1
        largest = row["largest_file"]
        largest_lines = int(largest["lines"]) if isinstance(largest, dict) else -1
        if lines > largest_lines:
            row["largest_file"] = {"path": repo_relative(path, repo_root), "lines": lines}
        by_extension[path.suffix] += 1
        largest_files.append({"path": repo_relative(path, repo_root), "family": family_name, "lines": lines})

    return {
        "roots": [root for root in SCRIPT_INVENTORY_ROOTS if (repo_root / root).exists()],
        "excluded_path_parts": sorted(SCRIPT_INVENTORY_EXCLUDED_PARTS),
        "totals": {
            "files": len(files),
            "lines": sum(int(item["lines"]) for item in largest_files),
            "python": by_extension.get(".py", 0),
            "ruby": by_extension.get(".rb", 0),
        },
        "by_family": [
            {"family": family, **values}
            for family, values in sorted(by_family.items(), key=lambda item: (-int(item[1]["lines"]), item[0]))
        ],
        "largest_files": sorted(largest_files, key=lambda item: (-int(item["lines"]), str(item["path"])))[:30],
    }


def git_output(argv: tuple[str, ...], repo_root: Path) -> tuple[int, str]:
    result = subprocess.run(argv, cwd=repo_root, check=False, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def collect_git_history(app: str, since: str, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    roots = [repo_relative(path, repo_root) for path in selected_root_paths(app, repo_root)]
    argv = ("git", "log", f"--since={since}", "--name-only", "--pretty=format:--COMMIT--", "--", *roots)
    result = subprocess.run(argv, cwd=repo_root, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return {"app": app, "since": since, "status": "failed", "error": result.stderr.strip()}

    commits = 0
    file_touches: collections.Counter[str] = collections.Counter()
    family_touches: collections.Counter[str] = collections.Counter()
    current_paths: set[str] = set()
    for line in result.stdout.splitlines():
        text = line.strip()
        if text == "--COMMIT--":
            if current_paths:
                commits += 1
                for touched in current_paths:
                    file_touches[touched] += 1
                    family_touches[file_family(REPO_ROOT / touched, repo_root)] += 1
            current_paths = set()
        elif text:
            current_paths.add(text)
    if current_paths:
        commits += 1
        for touched in current_paths:
            file_touches[touched] += 1
            family_touches[file_family(REPO_ROOT / touched, repo_root)] += 1

    return {
        "app": app,
        "since": since,
        "status": "passed",
        "commit_count": commits,
        "by_family": [{"family": family, "touches": count} for family, count in family_touches.most_common()],
        "top_files": [{"path": path, "touches": count} for path, count in file_touches.most_common(40)],
    }


def run_recorded_command(name: str, argv: tuple[str, ...], repo_root: Path, output_path: Path | None = None) -> dict[str, object]:
    started = time.monotonic()
    started_at = utc_now().isoformat()
    result = subprocess.run(argv, cwd=repo_root, check=False, capture_output=True, text=True)
    elapsed = round(time.monotonic() - started, 2)
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if output_path is not None:
        output_path.write_text(stdout, encoding="utf-8")
    return {
        "name": name,
        "command": list(argv),
        "command_text": command_text(argv),
        "cwd": repo_relative(repo_root, repo_root),
        "started_at_utc": started_at,
        "exit_code": result.returncode,
        "duration_seconds": elapsed,
        "stdout_path": repo_relative(output_path, repo_root) if output_path is not None else None,
        "stderr_excerpt": stderr.strip()[:1000],
    }


def collect_javascript_guardrail(run_dir: Path, repo_root: Path = REPO_ROOT) -> tuple[dict[str, object], dict[str, object]]:
    output_path = run_dir / "javascript-inventory-guardrail.json"
    argv = (sys.executable, "studio/checks/javascript_inventory_guardrail.py", "--json")
    command = run_recorded_command("javascript-inventory-guardrail", argv, repo_root, output_path)
    if command["exit_code"] != 0:
        return command, {"status": "failed", "error": command["stderr_excerpt"]}
    try:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return command, {"status": "failed", "error": f"invalid JSON output: {error}"}
    return command, {"status": "passed", **payload}


def runtime_profiles_for(args: argparse.Namespace) -> list[str]:
    profiles = list(args.runtime_profile or [])
    if args.include_runtime and not profiles:
        profiles.extend(RUNTIME_PROFILE_BY_APP[args.app])
    return sorted(dict.fromkeys(profiles))


def collect_runtime_checks(args: argparse.Namespace, run_id: str, repo_root: Path = REPO_ROOT) -> tuple[list[dict[str, object]], dict[str, object]]:
    profiles = runtime_profiles_for(args)
    if not profiles and not args.include_lighthouse:
        return [], {"status": "omitted", "reason": "runtime checks were not requested"}

    commands: list[dict[str, object]] = []
    results: list[dict[str, object]] = []
    for profile in profiles:
        check_run_id = slugify(f"risk-{run_id}-{profile}")
        argv = (sys.executable, "studio/commands/run_checks.py", "--profile", profile, "--run-id", check_run_id)
        command = run_recorded_command(f"runtime-profile-{profile}", argv, repo_root)
        commands.append(command)
        summary_path = REPO_ROOT / "var" / "test-runs" / check_run_id / "summary.md"
        results.append(
            {
                "profile": profile,
                "exit_code": command["exit_code"],
                "summary_path": repo_relative(summary_path, repo_root) if summary_path.exists() else None,
            }
        )

    lighthouse = {"status": "omitted", "reason": "Lighthouse hook is reserved for a future explicit URL contract."}
    if args.include_lighthouse:
        lighthouse = {"status": "deferred", "reason": "No allowlisted Lighthouse URL flag exists yet."}

    if lighthouse["status"] == "deferred":
        status = "deferred"
    elif any(result["exit_code"] != 0 for result in results):
        status = "failed"
    else:
        status = "passed"
    return commands, {"status": status, "profiles": results, "lighthouse": lighthouse}


def copy_subjective_notes(source: Path, run_dir: Path, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    destination = run_dir / "subjective-notes.jsonl"
    shutil.copy2(source, destination)
    lines = destination.read_text(encoding="utf-8", errors="ignore").splitlines()
    invalid_lines: list[int] = []
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError:
            invalid_lines.append(index)
    return {
        "status": "failed" if invalid_lines else "passed",
        "source": repo_relative(source, repo_root),
        "path": repo_relative(destination, repo_root),
        "records": len([line for line in lines if line.strip()]),
        "invalid_lines": invalid_lines,
    }


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def planned_artifacts(run_dir: Path, include_runtime: bool, include_subjective: bool) -> list[PlannedArtifact]:
    artifacts = [
        PlannedArtifact("manifest.json", repo_relative(run_dir / "manifest.json"), "manifest"),
        PlannedArtifact("commands.json", repo_relative(run_dir / "commands.json"), "commands"),
        PlannedArtifact("summary.md", repo_relative(run_dir / "summary.md"), "summary"),
        PlannedArtifact("summary.json", repo_relative(run_dir / "summary.json"), "summary"),
        PlannedArtifact("static-metrics.json", repo_relative(run_dir / "static-metrics.json"), "static-metrics"),
        PlannedArtifact("static-searches.json", repo_relative(run_dir / "static-searches.json"), "static-searches"),
        PlannedArtifact("generated-payloads.json", repo_relative(run_dir / "generated-payloads.json"), "generated-payloads"),
        PlannedArtifact(
            "script-family-inventory.json",
            repo_relative(run_dir / "script-family-inventory.json"),
            "script-family-inventory",
        ),
        PlannedArtifact("git-history.json", repo_relative(run_dir / "git-history.json"), "git-history"),
        PlannedArtifact(
            "javascript-inventory-guardrail.json",
            repo_relative(run_dir / "javascript-inventory-guardrail.json"),
            "javascript-inventory-guardrail",
        ),
    ]
    if include_runtime:
        artifacts.append(PlannedArtifact("runtime-checks.json", repo_relative(run_dir / "runtime-checks.json"), "runtime-checks"))
    if include_subjective:
        artifacts.append(
            PlannedArtifact("subjective-notes.jsonl", repo_relative(run_dir / "subjective-notes.jsonl"), "subjective-notes")
        )
    return artifacts


def build_summary_markdown(summary: dict[str, object]) -> str:
    status = summary["status"]
    app = summary["app"]
    area = summary["area"]
    run_id = summary["run_id"]
    lines = [
        "# Risk Evidence Summary",
        "",
        f"- Status: {status}",
        f"- App: {app}",
        f"- Area: {area}",
        f"- Run id: {run_id}",
        f"- Run directory: `{summary['run_dir']}`",
        "",
        "## Evidence",
        "",
    ]
    for item in summary["evidence"]:
        lines.append(f"- {item['status']}: `{item['artifact']}` - {item['summary']}")
    if summary["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for warning in summary["warnings"]:
            lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)


def summarize_evidence(
    app: str,
    area: str,
    run_id: str,
    run_dir: Path,
    artifacts: dict[str, dict[str, object]],
    warnings: list[str],
) -> dict[str, object]:
    evidence: list[dict[str, str]] = []
    metrics = artifacts["static-metrics"]
    totals = metrics["totals"]
    evidence.append(
        {
            "artifact": "static-metrics.json",
            "status": "collected",
            "summary": f"{totals['files']} files, {totals['lines']} lines across selected app roots.",
        }
    )
    imports = artifacts["static-metrics"]["import_export"]["totals"]
    evidence.append(
        {
            "artifact": "static-metrics.json",
            "status": "collected",
            "summary": f"{imports['imports']} imports, {imports['exports']} exports, {imports['cross_app_references']} cross-app references.",
        }
    )
    search_count = sum(int(item["match_count"]) for item in artifacts["static-searches"]["patterns"])
    evidence.append(
        {
            "artifact": "static-searches.json",
            "status": "collected",
            "summary": f"{search_count} matches across configured static risk search patterns.",
        }
    )
    payloads = artifacts["generated-payloads"]["totals"]
    evidence.append(
        {
            "artifact": "generated-payloads.json",
            "status": "collected",
            "summary": f"{payloads['files']} JSON payloads, {payloads['bytes']} bytes in generated payload roots.",
        }
    )
    script_inventory = artifacts["script-family-inventory"]["totals"]
    evidence.append(
        {
            "artifact": "script-family-inventory.json",
            "status": "collected",
            "summary": (
                f"{script_inventory['files']} Python/Ruby files, {script_inventory['lines']} lines "
                "across active script-family roots."
            ),
        }
    )
    history = artifacts["git-history"]
    evidence.append(
        {
            "artifact": "git-history.json",
            "status": str(history["status"]),
            "summary": f"{history.get('commit_count', 0)} commits in the configured history window.",
        }
    )
    guardrail = artifacts["javascript-inventory-guardrail"]
    guardrail_totals = guardrail.get("totals", {})
    evidence.append(
        {
            "artifact": "javascript-inventory-guardrail.json",
            "status": str(guardrail["status"]),
            "summary": f"{guardrail_totals.get('maintenance_2_files', 0)} maintenance>=2 JavaScript files in the legacy inventory.",
        }
    )
    if "runtime-checks" in artifacts:
        runtime = artifacts["runtime-checks"]
        evidence.append(
            {
                "artifact": "runtime-checks.json",
                "status": str(runtime["status"]),
                "summary": f"{len(runtime.get('profiles', []))} allowlisted runtime profiles requested.",
            }
        )
    if "subjective-notes" in artifacts:
        notes = artifacts["subjective-notes"]
        evidence.append(
            {
                "artifact": "subjective-notes.jsonl",
                "status": str(notes["status"]),
                "summary": f"{notes['records']} subjective note records copied into the run.",
            }
        )

    failed = [item for item in evidence if item["status"] in {"failed", "deferred"}]
    return {
        "app": app,
        "area": area,
        "run_id": run_id,
        "run_dir": repo_relative(run_dir),
        "status": "failed" if failed else "passed",
        "evidence": evidence,
        "warnings": warnings,
    }


def dry_run(args: argparse.Namespace, run_id: str, run_dir: Path) -> int:
    profiles = runtime_profiles_for(args)
    print("Risk evidence pack dry run")
    print(f"app: {args.app}")
    print(f"area: {args.area}")
    print(f"run id: {run_id}")
    print(f"run directory: {repo_relative(run_dir)}")
    print("")
    print("Planned producers:")
    producers = [
        "static file metrics",
        "import/export scan",
        "static searches",
        "generated payload scan",
        "script family inventory",
        "git touch counts",
        "JavaScript inventory guardrail",
    ]
    if profiles:
        producers.append(f"runtime profiles: {', '.join(profiles)}")
    if args.include_lighthouse:
        producers.append("Lighthouse: deferred until explicit URL contract")
    if args.include_subjective_notes:
        producers.append(f"subjective notes: {args.include_subjective_notes}")
    for producer in producers:
        print(f"- {producer}")
    print("")
    print("Planned artifacts:")
    for artifact in planned_artifacts(run_dir, bool(profiles or args.include_lighthouse), bool(args.include_subjective_notes)):
        print(f"- {artifact.path}")
    return 0


def write_run(args: argparse.Namespace, run_id: str, run_dir: Path) -> int:
    run_dir.mkdir(parents=True, exist_ok=False)
    commands: list[dict[str, object]] = []
    warnings: list[str] = []
    artifacts: dict[str, dict[str, object]] = {}

    static_metrics = collect_static_metrics(args.app)
    static_metrics["import_export"] = import_export_scan(args.app)
    artifacts["static-metrics"] = static_metrics
    write_json(run_dir / "static-metrics.json", static_metrics)

    artifacts["static-searches"] = collect_static_searches(args.app)
    write_json(run_dir / "static-searches.json", artifacts["static-searches"])

    artifacts["generated-payloads"] = collect_generated_payloads(args.app)
    write_json(run_dir / "generated-payloads.json", artifacts["generated-payloads"])

    artifacts["script-family-inventory"] = collect_script_family_inventory()
    write_json(run_dir / "script-family-inventory.json", artifacts["script-family-inventory"])

    artifacts["git-history"] = collect_git_history(args.app, args.since)
    write_json(run_dir / "git-history.json", artifacts["git-history"])
    if artifacts["git-history"]["status"] != "passed":
        warnings.append("git-history producer failed; see git-history.json")

    guardrail_command, guardrail = collect_javascript_guardrail(run_dir)
    commands.append(guardrail_command)
    artifacts["javascript-inventory-guardrail"] = guardrail
    if guardrail["status"] != "passed":
        warnings.append("JavaScript inventory guardrail failed; see commands.json")

    runtime_commands, runtime = collect_runtime_checks(args, run_id)
    commands.extend(runtime_commands)
    if runtime["status"] != "omitted":
        artifacts["runtime-checks"] = runtime
        write_json(run_dir / "runtime-checks.json", runtime)
        if runtime["status"] != "passed":
            warnings.append("One or more runtime evidence hooks failed or were deferred; see runtime-checks.json")

    if args.include_subjective_notes:
        notes = copy_subjective_notes(args.include_subjective_notes, run_dir)
        artifacts["subjective-notes"] = notes
        if notes["status"] != "passed":
            warnings.append("Subjective notes JSONL contains invalid JSON lines.")

    repo_status, commit = git_output(("git", "rev-parse", "HEAD"), REPO_ROOT)
    manifest = {
        "app": args.app,
        "area": args.area,
        "command_version": COMMAND_VERSION,
        "created_at_utc": utc_now().isoformat(),
        "history_window": args.since,
        "omitted_evidence": [
            item
            for item, omitted in (
                ("runtime-checks", runtime["status"] == "omitted"),
                ("subjective-notes", not args.include_subjective_notes),
                ("route-exposure", True),
                ("compact-generated-risk-summary", True),
            )
            if omitted
        ],
        "operator": os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown",
        "repo_commit": commit if repo_status == 0 else None,
        "run_id": run_id,
        "selected_evidence": sorted(artifacts.keys()),
    }

    write_json(run_dir / "manifest.json", manifest)
    write_json(run_dir / "commands.json", commands)

    summary = summarize_evidence(args.app, args.area, run_id, run_dir, artifacts, warnings)
    write_json(run_dir / "summary.json", summary)
    (run_dir / "summary.md").write_text(build_summary_markdown(summary), encoding="utf-8")

    print(f"summary: {repo_relative(run_dir / 'summary.md')}")
    print(f"status: {summary['status']}")
    return 1 if summary["status"] != "passed" else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", choices=VALID_APPS, required=True)
    parser.add_argument("--area", required=True, help="Risk area slug.")
    parser.add_argument("--run-id", help="Optional run id for var/studio/risk/runs/.")
    parser.add_argument("--since", default=DEFAULT_HISTORY_WINDOW, help="Git history window for touch counts.")
    parser.add_argument("--include-runtime", action="store_true", help="Run allowlisted runtime check profiles for the selected app.")
    parser.add_argument(
        "--runtime-profile",
        action="append",
        choices=("studio-smoke", "ui-catalogue-smoke", "analytics-smoke", "docs-viewer-smoke"),
        help="Allowlisted runtime check profile. Repeat to combine profiles.",
    )
    parser.add_argument("--include-lighthouse", action="store_true", help="Record the deferred Lighthouse hook in runtime evidence.")
    parser.add_argument("--include-subjective-notes", type=Path, help="Copy a JSONL subjective notes file into the run.")
    parser.add_argument("--write", action="store_true", help="Write the local run directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = slugify(args.run_id) if args.run_id else default_run_id(args.app, args.area)
    run_dir = RUNS_ROOT / run_id

    if args.include_subjective_notes and not args.include_subjective_notes.exists():
        print(f"subjective notes file does not exist: {args.include_subjective_notes}", file=sys.stderr)
        return 2

    if not args.write:
        return dry_run(args, run_id, run_dir)
    return write_run(args, run_id, run_dir)


if __name__ == "__main__":
    raise SystemExit(main())
