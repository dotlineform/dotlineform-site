#!/usr/bin/env python3
"""Run allowlisted Admin checks reports from a JSON request."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping

from admin_checks_config import DEFAULT_CONFIG_PATH, ChecksConfigError, load_checks_config, validate_path_pattern, validate_run_request
from target_map_resolver import REPO_ROOT, iter_repo_source_files, repo_relative, resolve_run_files, resolve_scope


COMMAND_CONTRACT_VERSION = "1"
RUN_SCHEMA_VERSION = "admin_checks_run_v1"
DEFAULT_RUNS_ROOT = Path("var/admin/checks")


class RunReportsError(RuntimeError):
    """Raised when the report runner cannot build or execute a run."""


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run_id_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")


def safe_repo_path(path_text: str, *, label: str, repo_root: Path = REPO_ROOT) -> Path:
    validate_path_pattern(path_text, label)
    return repo_root / path_text


def read_json_object(path: Path | None = None) -> Mapping[str, Any]:
    if path is None:
        raw = sys.stdin.read()
        label = "stdin"
    else:
        raw = path.read_text(encoding="utf-8")
        label = repo_relative(path)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RunReportsError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RunReportsError(f"{label} must contain a JSON object")
    return payload


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def merged_report_options(config: Mapping[str, Any], normalized_request: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    selected_options = normalized_request["options"]
    if not isinstance(selected_options, Mapping):
        raise RunReportsError("normalized request options must be a mapping")
    out: dict[str, dict[str, Any]] = {}
    for report_id in normalized_request["reports"]:
        report = config["reports"][report_id]
        options = dict(report.get("default_options", {}))
        options.update(selected_options.get(report_id, {}))
        out[report_id] = options
    return out


def selected_target_counts(files: list[Mapping[str, Any]]) -> dict[str, Any]:
    families: collections.Counter[str] = collections.Counter()
    areas: collections.Counter[str] = collections.Counter()
    routes: collections.Counter[str] = collections.Counter()
    for file in files:
        for family_id in file["families"] or ["_unclassified"]:
            families[family_id] += 1
        for area_id in sorted(set(file["areas"]) | set(file["shared_areas"])):
            areas[area_id] += 1
        for route_id in sorted(set(file["routes"]) | set(file["shared_routes"])):
            routes[route_id] += 1
    return {
        "files": len(files),
        "families": dict(sorted(families.items())),
        "areas": dict(sorted(areas.items())),
        "routes": dict(sorted(routes.items())),
    }


def validate_targets_resolve_in_scope(
    config: Mapping[str, Any],
    normalized_request: Mapping[str, Any],
    *,
    source_files: list[str],
) -> dict[str, Any]:
    scope_id = normalized_request["scope"]
    scope = resolve_scope(config, scope_id, source_files=source_files, global_source_files=source_files)
    files = scope["files"]
    checks = {
        "families": lambda file, target_id: target_id in file["families"],
        "areas": lambda file, target_id: target_id in file["areas"] or target_id in file["shared_areas"],
        "routes": lambda file, target_id: target_id in file["routes"] or target_id in file["shared_routes"],
    }
    for section, predicate in checks.items():
        missing = [
            target_id
            for target_id in normalized_request[section]
            if not any(predicate(file, target_id) for file in files)
        ]
        if missing:
            raise ChecksConfigError(
                f"request.{section} contains ids with no files in scope {scope_id}: {', '.join(sorted(missing))}"
            )
    return scope


def make_run_id(scope_id: str) -> str:
    return f"{run_id_timestamp()}-{scope_id}"


def create_run_dir(run_id: str, *, repo_root: Path = REPO_ROOT, runs_root: Path = DEFAULT_RUNS_ROOT) -> Path:
    base = repo_root / runs_root / run_id
    candidate = base
    index = 2
    while candidate.exists():
        candidate = repo_root / runs_root / f"{run_id}-{index}"
        index += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def report_artifact_paths(run_dir: Path, report_id: str, repo_root: Path = REPO_ROOT) -> dict[str, str]:
    report_dir = run_dir / report_id
    return {
        "output_dir": repo_relative(report_dir, repo_root),
        "report_json": repo_relative(report_dir / "report.json", repo_root),
        "report_markdown": repo_relative(report_dir / "report.md", repo_root),
    }


def build_plan(
    config: Mapping[str, Any],
    normalized_request: Mapping[str, Any],
    *,
    config_path: Path,
    repo_root: Path = REPO_ROOT,
    run_id: str | None = None,
) -> dict[str, Any]:
    source_files = iter_repo_source_files(repo_root)
    validate_targets_resolve_in_scope(config, normalized_request, source_files=source_files)
    selected_files = resolve_run_files(
        config,
        scope_id=normalized_request["scope"],
        families=normalized_request["families"],
        areas=normalized_request["areas"],
        routes=normalized_request["routes"],
        source_files=source_files,
        repo_root=repo_root,
    )
    resolved_options = merged_report_options(config, normalized_request)
    resolved_run_id = run_id or make_run_id(normalized_request["scope"])
    planned_run_dir = DEFAULT_RUNS_ROOT / resolved_run_id
    reports: list[dict[str, Any]] = []
    for report_id in normalized_request["reports"]:
        report = config["reports"][report_id]
        artifact_paths = report_artifact_paths(repo_root / planned_run_dir, report_id, repo_root)
        reports.append(
            {
                "report_id": report_id,
                "label": report["label"],
                "description": report["description"],
                "script": report["script"],
                "options": resolved_options[report_id],
                "artifacts": artifact_paths,
            }
        )
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "command_contract_version": COMMAND_CONTRACT_VERSION,
        "created_at": utc_timestamp(),
        "config_path": config_path.as_posix(),
        "run_id": resolved_run_id,
        "run_dir": planned_run_dir.as_posix(),
        "write": normalized_request["write"],
        "targets": {
            "scope": normalized_request["scope"],
            "families": normalized_request["families"],
            "areas": normalized_request["areas"],
            "routes": normalized_request["routes"],
        },
        "reports": reports,
        "target_match_counts": selected_target_counts(selected_files),
    }


def command_record(
    *,
    kind: str,
    argv: list[str],
    cwd: Path,
    status: str,
    started_at: str,
    finished_at: str,
    duration_ms: int,
    exit_code: int | None = None,
    report_id: str | None = None,
    stdout: str = "",
    stderr: str = "",
    error: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "kind": kind,
        "argv": argv,
        "cwd": repo_relative(cwd),
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "exit_code": exit_code,
    }
    if report_id:
        record["report_id"] = report_id
    if stdout:
        record["stdout"] = stdout
    if stderr:
        record["stderr"] = stderr
    if error:
        record["error"] = error
    return record


def report_argv(
    report: Mapping[str, Any],
    *,
    config_path: Path,
    manifest_path: Path,
    repo_root: Path = REPO_ROOT,
) -> list[str]:
    output_dir = report["artifacts"]["output_dir"]
    return [
        sys.executable,
        report["script"],
        "--config",
        config_path.as_posix(),
        "--run-manifest",
        repo_relative(manifest_path, repo_root),
        "--report-id",
        report["report_id"],
        "--output-dir",
        output_dir,
    ]


def invoke_report(
    report: Mapping[str, Any],
    *,
    config_path: Path,
    run_dir: Path,
    manifest_path: Path,
    repo_root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    report_id = report["report_id"]
    report_dir = run_dir / report_id
    report_dir.mkdir(parents=True, exist_ok=True)
    argv = report_argv(report, config_path=config_path, manifest_path=manifest_path, repo_root=repo_root)
    started = utc_timestamp()
    start_time = time.monotonic()
    script_path = repo_root / report["script"]
    if not script_path.is_file():
        finished = utc_timestamp()
        error = f"report script does not exist: {report['script']}"
        duration_ms = round((time.monotonic() - start_time) * 1000)
        command = command_record(
            kind="report",
            report_id=report_id,
            argv=argv,
            cwd=repo_root,
            status="failed",
            started_at=started,
            finished_at=finished,
            duration_ms=duration_ms,
            error=error,
        )
        result = {
            "report_id": report_id,
            "status": "failed",
            "exit_code": None,
            "artifacts": report["artifacts"],
            "error": error,
        }
        return command, result

    completed = subprocess.run(argv, cwd=repo_root, text=True, capture_output=True, check=False)
    finished = utc_timestamp()
    duration_ms = round((time.monotonic() - start_time) * 1000)
    status = "passed" if completed.returncode == 0 else "failed"
    error = None if status == "passed" else f"report exited with code {completed.returncode}"

    report_json = repo_root / report["artifacts"]["report_json"]
    report_md = repo_root / report["artifacts"]["report_markdown"]
    if status == "passed" and (not report_json.is_file() or not report_md.is_file()):
        status = "failed"
        missing = [
            path
            for path, exists in (
                (report["artifacts"]["report_json"], report_json.is_file()),
                (report["artifacts"]["report_markdown"], report_md.is_file()),
            )
            if not exists
        ]
        error = f"report completed without required artifacts: {', '.join(missing)}"

    command = command_record(
        kind="report",
        report_id=report_id,
        argv=argv,
        cwd=repo_root,
        status=status,
        started_at=started,
        finished_at=finished,
        duration_ms=duration_ms,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        error=error,
    )
    result = {
        "report_id": report_id,
        "status": status,
        "exit_code": completed.returncode,
        "artifacts": report["artifacts"],
    }
    if error:
        result["error"] = error
    return command, result


def render_summary_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Admin Checks Run",
        "",
        f"- run: `{summary['run_id']}`",
        f"- status: `{summary['status']}`",
        f"- scope: `{summary['targets']['scope']}`",
        f"- run directory: `{summary['run_dir']}`",
        "",
        "## Reports",
        "",
        "| report | status | artifacts |",
        "| --- | --- | --- |",
    ]
    for report in summary["reports"]:
        artifacts = report["artifacts"]
        artifact_text = f"`{artifacts['report_json']}`, `{artifacts['report_markdown']}`"
        lines.append(f"| `{report['report_id']}` | `{report['status']}` | {artifact_text} |")
    errors = summary.get("errors", [])
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
    lines.append("")
    return "\n".join(lines)


def build_summary(plan: Mapping[str, Any], report_results: list[Mapping[str, Any]], *, run_dir: Path, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    failed = [result for result in report_results if result["status"] != "passed"]
    status = "failed" if failed else "passed"
    errors = [
        f"{result['report_id']}: {result['error']}"
        for result in report_results
        if result.get("error")
    ]
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "command_contract_version": COMMAND_CONTRACT_VERSION,
        "run_id": plan["run_id"],
        "created_at": plan["created_at"],
        "finished_at": utc_timestamp(),
        "status": status,
        "run_dir": repo_relative(run_dir, repo_root),
        "targets": plan["targets"],
        "target_match_counts": plan["target_match_counts"],
        "reports": report_results,
        "totals": {
            "reports": len(report_results),
            "passed": len(report_results) - len(failed),
            "failed": len(failed),
        },
        "errors": errors,
    }


def write_run_artifacts(
    plan: dict[str, Any],
    *,
    repo_root: Path = REPO_ROOT,
    run_id: str | None = None,
    argv: list[str] | None = None,
) -> dict[str, Any]:
    run_dir = create_run_dir(run_id or plan["run_id"], repo_root=repo_root)
    plan["run_id"] = run_dir.name
    plan["run_dir"] = repo_relative(run_dir, repo_root)
    for report in plan["reports"]:
        report["artifacts"] = report_artifact_paths(run_dir, report["report_id"], repo_root)

    manifest_path = run_dir / "manifest.json"
    manifest = {
        **plan,
        "status": "running",
        "manifest_path": repo_relative(manifest_path, repo_root),
    }
    write_json(manifest_path, manifest)

    orchestrator_started = utc_timestamp()
    orchestrator_start_time = time.monotonic()
    commands: list[dict[str, Any]] = [
        command_record(
            kind="orchestrator",
            argv=argv or sys.argv,
            cwd=repo_root,
            status="started",
            started_at=orchestrator_started,
            finished_at=orchestrator_started,
            duration_ms=0,
            exit_code=None,
        )
    ]
    report_results: list[dict[str, Any]] = []
    config_path = Path(plan["config_path"])
    for report in plan["reports"]:
        command, result = invoke_report(
            report,
            config_path=config_path,
            run_dir=run_dir,
            manifest_path=manifest_path,
            repo_root=repo_root,
        )
        commands.append(command)
        report_results.append(result)

    summary = build_summary(plan, report_results, run_dir=run_dir, repo_root=repo_root)
    commands[0]["status"] = summary["status"]
    commands[0]["finished_at"] = summary["finished_at"]
    commands[0]["duration_ms"] = round((time.monotonic() - orchestrator_start_time) * 1000)
    commands[0]["exit_code"] = 0 if summary["status"] == "passed" else 1
    manifest["status"] = summary["status"]
    manifest["finished_at"] = summary["finished_at"]
    write_json(manifest_path, manifest)
    write_json(run_dir / "commands.json", {"schema_version": RUN_SCHEMA_VERSION, "commands": commands})
    write_json(run_dir / "run-summary.json", summary)
    (run_dir / "run-summary.md").write_text(render_summary_markdown(summary), encoding="utf-8")
    return summary


def run_request(
    request: Mapping[str, Any],
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    repo_root: Path = REPO_ROOT,
    argv: list[str] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    config = load_checks_config(config_path, repo_root)
    normalized_request = validate_run_request(config, request)
    plan = build_plan(config, normalized_request, config_path=config_path, repo_root=repo_root, run_id=run_id)
    if not normalized_request["write"]:
        return {"mode": "dry-run", "plan": plan}
    summary = write_run_artifacts(plan, repo_root=repo_root, run_id=run_id, argv=argv)
    return {"mode": "write", "summary": summary}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run allowlisted Admin checks reports from a JSON request.")
    parser.add_argument("--request", help="Repo-relative JSON request path. Omit or pass '-' to read standard input.")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH.as_posix(),
        help="Repo-relative Admin checks config path.",
    )
    parser.add_argument("--json", action="store_true", help="Print the full resolved plan or summary as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config_path = Path(args.config)
        safe_repo_path(config_path.as_posix(), label="--config")
        request_path = None
        if args.request and args.request != "-":
            request_path = safe_repo_path(args.request, label="--request")
        request = read_json_object(request_path)
        result = run_request(request, config_path=config_path, repo_root=REPO_ROOT, argv=sys.argv)
    except (ChecksConfigError, RunReportsError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json or result["mode"] == "dry-run":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        summary = result["summary"]
        print(f"Wrote {summary['run_dir']}")
        print(f"Status: {summary['status']}")
    if result["mode"] == "write" and result["summary"]["status"] != "passed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
