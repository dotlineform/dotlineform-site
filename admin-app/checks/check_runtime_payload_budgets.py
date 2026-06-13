#!/usr/bin/env python3
"""Check browser runtime config payload sizes."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_BUDGETS = {
    "studio/app/frontend/config/studio-config.json": 12_000,
    "site/assets/data/search/policy.json": 8_000,
}
UI_TEXT_GLOB = "studio/app/frontend/config/ui-text/*.json"
DEFAULT_UI_TEXT_BUDGET = 16_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=Path.cwd(), type=Path)
    parser.add_argument("--studio-config-max-bytes", default=DEFAULT_BUDGETS["studio/app/frontend/config/studio-config.json"], type=int)
    parser.add_argument("--search-policy-max-bytes", default=DEFAULT_BUDGETS["site/assets/data/search/policy.json"], type=int)
    parser.add_argument("--ui-text-max-bytes", default=DEFAULT_UI_TEXT_BUDGET, type=int)
    return parser.parse_args()


def check_file(repo_root: Path, rel_path: str, max_bytes: int, failures: list[str]) -> None:
    path = repo_root / rel_path
    size = path.stat().st_size
    status = "ok" if size <= max_bytes else "over"
    print(f"{status} {rel_path}: {size} bytes <= {max_bytes}")
    if size > max_bytes:
        failures.append(f"{rel_path} is {size} bytes; budget is {max_bytes}")


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    failures: list[str] = []
    budgets = {
        "studio/app/frontend/config/studio-config.json": args.studio_config_max_bytes,
        "site/assets/data/search/policy.json": args.search_policy_max_bytes,
    }
    for rel_path, max_bytes in budgets.items():
        check_file(repo_root, rel_path, max_bytes, failures)

    for path in sorted(repo_root.glob(UI_TEXT_GLOB)):
        rel_path = path.relative_to(repo_root).as_posix()
        check_file(repo_root, rel_path, args.ui_text_max_bytes, failures)

    if failures:
        print("\nRuntime payload budget failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
