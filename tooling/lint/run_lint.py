#!/usr/bin/env python3
"""Run repository-owned lint tools against explicit or maintained targets."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = REPO_ROOT / "tooling" / "lint"
TARGETS_PATH = TOOL_ROOT / "targets.json"
RUFF_BIN = TOOL_ROOT / ".venv" / "bin" / "ruff"
ESLINT_BIN = TOOL_ROOT / "node_modules" / ".bin" / "eslint"
LANGUAGE_SUFFIXES = {
    "python": ".py",
    "javascript": ".js",
}


class LintTargetError(ValueError):
    """Raised when a requested lint target is missing, unsafe, or empty."""


def load_targets() -> dict[str, object]:
    payload = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    if payload.get("version") != 1 or not isinstance(payload.get("scopes"), dict):
        raise LintTargetError(f"Unsupported lint target configuration: {TARGETS_PATH}")
    return payload


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError as exc:
        raise LintTargetError(f"Lint targets must stay inside the repository: {path}") from exc


def matches_exclusion(relative_path: str, exclusions: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(relative_path, pattern) for pattern in exclusions)


def candidate_files(
    raw_paths: Sequence[str],
    *,
    language: str,
    exclusions: Sequence[str],
) -> list[str]:
    """Resolve requested repository paths to eligible source or reject the whole request.

    Missing and out-of-repository paths fail immediately. A request that
    resolves only excluded or wrong-language files also fails so callers
    cannot report a false-green lint result.
    """
    suffix = LANGUAGE_SUFFIXES[language]
    resolved: set[str] = set()
    for raw_path in raw_paths:
        candidate = (REPO_ROOT / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
        relative = repo_relative(candidate)
        if not candidate.exists():
            raise LintTargetError(f"Lint target does not exist: {relative}")
        paths = [candidate] if candidate.is_file() else candidate.rglob(f"*{suffix}")
        for path in paths:
            if not path.is_file() or path.suffix != suffix:
                continue
            rel_path = repo_relative(path)
            if matches_exclusion(rel_path, exclusions):
                continue
            resolved.add(rel_path)
    if not resolved:
        joined = ", ".join(raw_paths) or "<none>"
        raise LintTargetError(f"No eligible {language} source resolved from: {joined}")
    return sorted(resolved)


def tool_command(language: str, files: Sequence[str]) -> list[str]:
    """Build the command for the pinned repository-local tool installation."""
    if language == "python":
        if not RUFF_BIN.is_file():
            raise LintTargetError(
                "Repository Ruff is not installed. Install tooling/lint/python-requirements.txt "
                f"into {TOOL_ROOT / '.venv'}."
            )
        return [
            str(RUFF_BIN),
            "check",
            "--config",
            str(TOOL_ROOT / "ruff.toml"),
            *files,
        ]
    if not ESLINT_BIN.is_file():
        raise LintTargetError(
            f"Repository ESLint is not installed. Run npm ci --prefix {TOOL_ROOT}."
        )
    return [
        str(ESLINT_BIN),
        "--config",
        str(TOOL_ROOT / "eslint.config.mjs"),
        *files,
    ]


def run_language(
    language: str,
    raw_paths: Sequence[str],
    *,
    exclusions: Sequence[str],
    label: str,
) -> int:
    """Run one language and print the maintained roots that support the result."""
    files = candidate_files(raw_paths, language=language, exclusions=exclusions)
    print(
        f"Lint {label}: language={language} files={len(files)} "
        f"targets={','.join(raw_paths)}",
        flush=True,
    )
    return subprocess.run(tool_command(language, files), cwd=REPO_ROOT, check=False).returncode


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", help="Lint one complete maintained scope.")
    parser.add_argument("--language", choices=sorted(LANGUAGE_SUFFIXES))
    parser.add_argument("--paths", nargs="*", help="Explicit source paths to lint.")
    parser.add_argument("--list", action="store_true", help="List maintained scopes.")
    args = parser.parse_args(argv)
    selected_modes = sum((bool(args.scope), args.paths is not None, args.list))
    if selected_modes != 1:
        parser.error("choose exactly one of --scope, --paths, or --list")
    if args.paths is not None and (not args.language or not args.paths):
        parser.error("--paths requires --language and at least one path")
    if args.language and args.paths is None:
        parser.error("--language is valid only with --paths")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_targets()
        scopes = config["scopes"]
        exclusions = tuple(config.get("exclude", ()))
        if args.list:
            for scope_id in sorted(scopes):
                payload = scopes[scope_id]
                languages = [
                    language
                    for language in LANGUAGE_SUFFIXES
                    if payload.get(language)
                ]
                print(f"{scope_id}: {', '.join(languages) or 'no source'}")
            return 0
        if args.paths is not None:
            return run_language(
                args.language,
                args.paths,
                exclusions=exclusions,
                label="explicit",
            )
        if args.scope not in scopes:
            raise LintTargetError(f"Unknown maintained lint scope: {args.scope}")
        payload = scopes[args.scope]
        exit_code = 0
        ran = False
        for language in LANGUAGE_SUFFIXES:
            raw_paths = payload.get(language, ())
            if not raw_paths:
                continue
            ran = True
            result = run_language(
                language,
                raw_paths,
                exclusions=exclusions,
                label=f"scope={args.scope}",
            )
            exit_code = result if result and not exit_code else exit_code
        if not ran:
            raise LintTargetError(f"Maintained lint scope has no source: {args.scope}")
        return exit_code
    except (LintTargetError, json.JSONDecodeError, OSError) as exc:
        print(f"lint target error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
