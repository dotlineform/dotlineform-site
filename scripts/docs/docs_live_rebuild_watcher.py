#!/usr/bin/env python3
"""
Watch docs source roots and rebuild same-scope docs payloads plus docs search.

Run:
  ./scripts/docs/docs_live_rebuild_watcher.py
  ./scripts/docs/docs_live_rebuild_watcher.py --poll-seconds 0.5 --debounce-seconds 1.5
  ./scripts/docs/docs_live_rebuild_watcher.py --repo-root /path/to/dotlineform-site
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

SCRIPTS_DOCS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DOCS_DIR))

from docs_management_server import load_scope_docs, scope_doc_sort_key
from docs_watch_suppression import SUPPRESSION_COMPLETE, clear_watch_suppressions, load_active_watch_suppressions

SCOPE_ROOTS = {
    "studio": Path("_docs_src"),
    "library": Path("_docs_library_src"),
    "analysis": Path("_docs_src_analysis"),
}
NESTED_SOURCE_SCOPES = {"analysis"}


def log(message: str) -> None:
    print(f"[docs-watch] {message}", flush=True)


def find_repo_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    return None


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "_config.yml").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing _config.yml): {repo_root}")
        return repo_root

    for start in [Path.cwd(), Path(__file__).resolve().parent]:
        found = find_repo_root(start)
        if found is not None:
            return found

    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def detect_bundle_bin() -> Optional[str]:
    rbenv_bundle = Path.home() / ".rbenv" / "shims" / "bundle"
    if rbenv_bundle.exists() and os.access(rbenv_bundle, os.X_OK):
        return str(rbenv_bundle)
    return shutil.which("bundle")


def snapshot_scope(root: Path, scope: str) -> Dict[str, tuple[int, int]]:
    if not root.exists():
        raise FileNotFoundError(f"Source root not found: {root}")

    snapshot: Dict[str, tuple[int, int]] = {}
    pattern = "**/*.md" if scope in NESTED_SOURCE_SCOPES else "*.md"
    for path in sorted(root.glob(pattern)):
        stat = path.stat()
        snapshot[path.relative_to(root).as_posix()] = (stat.st_mtime_ns, stat.st_size)
    return snapshot


def summarize_output(output: str, fallback: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines[-1] if lines else fallback


def changed_filenames(previous: Dict[str, tuple[int, int]], current: Dict[str, tuple[int, int]]) -> list[str]:
    filenames = set(previous.keys()) | set(current.keys())
    return sorted(name for name in filenames if previous.get(name) != current.get(name))


def ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def parsed_doc_snapshot(repo_root: Path, scope: str) -> Dict[str, Dict[str, Any]]:
    docs = load_scope_docs(repo_root, scope)
    root = repo_root / SCOPE_ROOTS[scope]
    return {
        doc.path.relative_to(root).as_posix(): {
            "filename": doc.path.relative_to(root).as_posix(),
            "doc_id": doc.doc_id,
            "title": doc.title,
            "parent_id": doc.parent_id,
            "published": doc.published,
            "viewable": doc.viewable,
            "sort_key": scope_doc_sort_key(doc),
        }
        for doc in docs
    }


def try_parsed_doc_snapshot(repo_root: Path, scope: str) -> tuple[Optional[Dict[str, Dict[str, Any]]], str]:
    try:
        return parsed_doc_snapshot(repo_root, scope), ""
    except Exception as exc:  # noqa: BLE001 - watcher must fall back rather than stop on bad source state.
        return None, str(exc)


def direct_child_doc_ids(snapshot: Dict[str, Dict[str, Any]], parent_doc_id: str) -> list[str]:
    children = [row for row in snapshot.values() if row.get("parent_id") == parent_doc_id]
    children.sort(key=lambda row: row.get("sort_key") or (True, 0, str(row.get("title") or "").lower(), row.get("doc_id")))
    return [str(row.get("doc_id") or "").strip() for row in children]


def affected_search_doc_ids(
    previous_docs: Optional[Dict[str, Dict[str, Any]]],
    current_docs: Dict[str, Dict[str, Any]],
    changed_files: list[str],
    threshold: int,
) -> tuple[Optional[list[str]], str]:
    if previous_docs is None:
        return None, "missing previous parsed docs snapshot"
    if threshold >= 0 and len(changed_files) > threshold:
        return None, f"changed file count {len(changed_files)} exceeds targeted threshold {threshold}"

    affected: list[str] = []
    for filename in changed_files:
        previous = previous_docs.get(filename)
        current = current_docs.get(filename)

        if previous is None and current is None:
            return None, f"could not resolve changed file {filename}"
        if previous is None:
            affected.append(str(current.get("doc_id") or ""))
            continue
        if current is None:
            affected.append(str(previous.get("doc_id") or ""))
            continue

        current_doc_id = str(current.get("doc_id") or "")
        previous_doc_id = str(previous.get("doc_id") or "")
        affected.append(current_doc_id)
        if previous_doc_id != current_doc_id:
            affected.append(previous_doc_id)
        if str(previous.get("title") or "") != str(current.get("title") or ""):
            affected.extend(direct_child_doc_ids(current_docs, current_doc_id))

    return ordered_unique(affected), ""


def rebuild_scope(
    repo_root: Path,
    bundle_bin: str,
    scope: str,
    search_doc_ids: Optional[list[str]] = None,
) -> bool:
    commands = [("docs", [bundle_bin, "exec", "ruby", "scripts/build_docs.rb", "--scope", scope, "--write"])]
    if search_doc_ids is None:
        commands.append(("search", [bundle_bin, "exec", "ruby", "scripts/build_search.rb", "--scope", scope, "--write"]))
        log(f"Rebuilding {scope} docs and full docs search.")
    else:
        target_doc_ids = ordered_unique(search_doc_ids)
        if target_doc_ids:
            commands.append(
                (
                    "search",
                    [
                        bundle_bin,
                        "exec",
                        "ruby",
                        "scripts/build_search.rb",
                        "--scope",
                        scope,
                        "--write",
                        "--only-doc-ids",
                        ",".join(target_doc_ids),
                        "--remove-missing",
                    ],
                )
            )
            log(f"Rebuilding {scope} docs and targeted docs search: {', '.join(target_doc_ids)}.")
        else:
            log(f"Rebuilding {scope} docs; no docs-search ids were affected.")

    for label, command in commands:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = completed.stdout.strip()
        stderr = completed.stderr.strip()
        if completed.returncode != 0:
            detail = stderr or stdout or f"exit {completed.returncode}"
            log(f"{scope} {label} rebuild failed: {detail}")
            return False
        log(f"{scope} {label}: {summarize_output(stdout, 'done')}")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch docs source roots and rebuild same-scope outputs.")
    parser.add_argument("--repo-root", default="", help="Override repo root auto-detection.")
    parser.add_argument("--bundle-bin", default="", help="Override bundle executable path.")
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=float(os.environ.get("DOCS_WATCH_POLL_SECONDS", "1.0")),
        help="Polling interval in seconds.",
    )
    parser.add_argument(
        "--debounce-seconds",
        type=float,
        default=float(os.environ.get("DOCS_WATCH_DEBOUNCE_SECONDS", "1.0")),
        help="Debounce window in seconds before rebuild.",
    )
    parser.add_argument(
        "--targeted-search-threshold",
        type=int,
        default=int(os.environ.get("DOCS_WATCH_TARGETED_SEARCH_THRESHOLD", "5")),
        help="Maximum changed file count for targeted docs-search updates; use -1 to always target when safe.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.poll_seconds <= 0:
        raise SystemExit("--poll-seconds must be greater than zero")
    if args.debounce_seconds < 0:
        raise SystemExit("--debounce-seconds must be zero or greater")

    repo_root = detect_repo_root(args.repo_root)
    bundle_bin = args.bundle_bin or detect_bundle_bin()
    if not bundle_bin:
        raise SystemExit("bundle executable not found")

    states = {}
    for scope, rel_root in SCOPE_ROOTS.items():
        root = repo_root / rel_root
        doc_snapshot, snapshot_error = try_parsed_doc_snapshot(repo_root, scope)
        if snapshot_error:
            log(f"{scope} parsed docs snapshot unavailable at startup; watcher search will use full rebuilds: {snapshot_error}")
        states[scope] = {
            "root": root,
            "snapshot": snapshot_scope(root, scope),
            "doc_snapshot": doc_snapshot,
            "dirty_at": None,
            "changed_files": [],
        }

    log(
        "Watching _docs_src/*.md -> studio, _docs_library_src/*.md -> library, "
        "and _docs_src_analysis/**/*.md -> analysis "
        f"(poll={args.poll_seconds:.2f}s, debounce={args.debounce_seconds:.2f}s)."
    )

    try:
        while True:
            now = time.monotonic()
            for scope in ("studio", "library", "analysis"):
                state = states[scope]
                previous_snapshot = state["snapshot"]
                current_snapshot = snapshot_scope(state["root"], scope)
                if current_snapshot != previous_snapshot:
                    state["snapshot"] = current_snapshot
                    state["changed_files"] = changed_filenames(previous_snapshot, current_snapshot)
                    state["dirty_at"] = now
                    changed_text = ", ".join(state["changed_files"]) or "unknown files"
                    log(f"Detected source changes for {scope}: {changed_text}.")

            ready_scope = None
            for scope in ("studio", "library", "analysis"):
                dirty_at = states[scope]["dirty_at"]
                if dirty_at is not None and (now - dirty_at) >= args.debounce_seconds:
                    ready_scope = scope
                    break

            if ready_scope:
                changed_files = list(states[ready_scope]["changed_files"])
                active_suppressions = load_active_watch_suppressions(repo_root, ready_scope)
                if changed_files:
                    matching = [active_suppressions.get(filename) for filename in changed_files]
                    if all(record is not None for record in matching):
                        if all(str(record.get("status") or "").strip() == SUPPRESSION_COMPLETE for record in matching):
                            clear_watch_suppressions(repo_root, ready_scope, changed_files)
                            current_doc_snapshot, snapshot_error = try_parsed_doc_snapshot(repo_root, ready_scope)
                            if snapshot_error:
                                log(f"{ready_scope} parsed docs snapshot not refreshed after suppressed write: {snapshot_error}")
                            else:
                                states[ready_scope]["doc_snapshot"] = current_doc_snapshot
                            states[ready_scope]["dirty_at"] = None
                            states[ready_scope]["changed_files"] = []
                            log(
                                f"Skipped duplicate {ready_scope} rebuild for docs-management write: "
                                f"{', '.join(changed_files)}."
                            )
                            continue
                        continue

                current_doc_snapshot, snapshot_error = try_parsed_doc_snapshot(repo_root, ready_scope)
                search_doc_ids = None
                if snapshot_error:
                    log(f"{ready_scope} targeted search fallback: {snapshot_error}")
                else:
                    search_doc_ids, fallback_reason = affected_search_doc_ids(
                        states[ready_scope]["doc_snapshot"],
                        current_doc_snapshot,
                        changed_files,
                        args.targeted_search_threshold,
                    )
                    if fallback_reason:
                        log(f"{ready_scope} targeted search fallback: {fallback_reason}")

                rebuild_succeeded = rebuild_scope(repo_root, bundle_bin, ready_scope, search_doc_ids=search_doc_ids)
                post_rebuild_snapshot = snapshot_scope(states[ready_scope]["root"], ready_scope)
                if post_rebuild_snapshot != states[ready_scope]["snapshot"]:
                    previous_snapshot = states[ready_scope]["snapshot"]
                    states[ready_scope]["snapshot"] = post_rebuild_snapshot
                    states[ready_scope]["changed_files"] = changed_filenames(previous_snapshot, post_rebuild_snapshot)
                    states[ready_scope]["dirty_at"] = time.monotonic()
                    log(f"Additional source changes arrived during the {ready_scope} rebuild; scheduling another pass.")
                else:
                    if rebuild_succeeded and current_doc_snapshot is not None:
                        states[ready_scope]["doc_snapshot"] = current_doc_snapshot
                    states[ready_scope]["dirty_at"] = None
                    states[ready_scope]["changed_files"] = []
                continue

            time.sleep(args.poll_seconds)
    except KeyboardInterrupt:
        log("Stopping watcher.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
