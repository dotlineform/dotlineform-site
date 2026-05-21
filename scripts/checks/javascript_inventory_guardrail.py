#!/usr/bin/env python3
"""Report JavaScript inventory maintenance-risk concentration."""

from __future__ import annotations

import argparse
import collections
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY = "_docs/javascript-inventory.md"


@dataclass(frozen=True)
class InventoryRow:
    rank: int
    path: str
    family: str
    maintenance: int
    structural: int
    performance: int
    architectural: int
    risk: int
    focus: str
    lines: int

    @property
    def has_overlap_risk(self) -> bool:
        return self.maintenance >= 2 and (
            self.structural >= 2 or self.performance >= 2 or self.architectural >= 2
        )


def parse_inventory_table(inventory_path: Path, repo_root: Path) -> list[InventoryRow]:
    rows: list[InventoryRow] = []
    for line in inventory_path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "`assets/" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 9:
            continue
        path = cells[1].strip("`")
        source_path = repo_root / path
        if not source_path.exists():
            raise FileNotFoundError(f"inventory row source is missing: {path}")
        category_scores = {
            "maintenance": int(cells[3]),
            "structural": int(cells[4]),
            "performance": int(cells[5]),
            "architectural": int(cells[6]),
        }
        invalid_scores = {name: score for name, score in category_scores.items() if score < 0 or score > 3}
        if invalid_scores:
            formatted = ", ".join(f"{name}={score}" for name, score in invalid_scores.items())
            raise ValueError(f"inventory row has category score outside 0..3 for {path}: {formatted}")
        risk = int(cells[7])
        expected_risk = sum(category_scores.values())
        if risk != expected_risk:
            raise ValueError(f"inventory row risk total mismatch for {path}: expected {expected_risk}, got {risk}")
        rows.append(
            InventoryRow(
                rank=int(cells[0]),
                path=path,
                family=cells[2],
                maintenance=category_scores["maintenance"],
                structural=category_scores["structural"],
                performance=category_scores["performance"],
                architectural=category_scores["architectural"],
                risk=risk,
                focus=cells[8],
                lines=count_lines(source_path),
            )
        )
    return rows


def count_lines(path: Path) -> int:
    with path.open(encoding="utf-8") as handle:
        return sum(1 for _line in handle)


def git_touch_counts(repo_root: Path, since: str) -> collections.Counter[str]:
    result = subprocess.run(
        ["git", "log", f"--since={since}", "--name-only", "--pretty=format:--COMMIT--"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    commits: list[set[str]] = []
    current: set[str] = set()
    for line in result.stdout.splitlines():
        text = line.strip()
        if text == "--COMMIT--":
            if current:
                commits.append(current)
            current = set()
            continue
        if text:
            current.add(text)
    if current:
        commits.append(current)

    counts: collections.Counter[str] = collections.Counter()
    for commit_paths in commits:
        for path in commit_paths:
            if path.startswith("assets/") and path.endswith(".js"):
                counts[path] += 1
    return counts


def percentage(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return round((part / whole) * 100, 1)


def summarize(
    rows: Iterable[InventoryRow],
    touch_counts: collections.Counter[str],
    *,
    top_limit: int = 12,
) -> dict[str, object]:
    row_list = list(rows)
    line_total = sum(row.lines for row in row_list)
    files_by_maintenance: collections.Counter[int] = collections.Counter(row.maintenance for row in row_list)
    lines_by_maintenance: collections.Counter[int] = collections.Counter()
    families: dict[str, dict[str, int]] = collections.defaultdict(lambda: {"files": 0, "lines": 0, "touches": 0})

    for row in row_list:
        lines_by_maintenance[row.maintenance] += row.lines
        if row.maintenance >= 2:
            family = families[row.family]
            family["files"] += 1
            family["lines"] += row.lines
            family["touches"] += touch_counts[row.path]

    maintenance_two_rows = [row for row in row_list if row.maintenance >= 2]
    overlap_rows = [row for row in maintenance_two_rows if row.has_overlap_risk]
    ranked = sorted(
        maintenance_two_rows,
        key=lambda row: (
            -(row.lines + (touch_counts[row.path] * 50)),
            -row.risk,
            row.path,
        ),
    )

    return {
        "totals": {
            "files": len(row_list),
            "lines": line_total,
            "maintenance_2_files": len(maintenance_two_rows),
            "maintenance_2_lines": sum(row.lines for row in maintenance_two_rows),
            "maintenance_2_file_percent": percentage(len(maintenance_two_rows), len(row_list)),
            "maintenance_2_line_percent": percentage(sum(row.lines for row in maintenance_two_rows), line_total),
            "maintenance_2_overlap_files": len(overlap_rows),
        },
        "files_by_maintenance": dict(sorted(files_by_maintenance.items())),
        "lines_by_maintenance": dict(sorted(lines_by_maintenance.items())),
        "maintenance_2_by_family": [
            {
                "family": family,
                "files": values["files"],
                "lines": values["lines"],
                "touches": values["touches"],
            }
            for family, values in sorted(
                families.items(),
                key=lambda item: (-item[1]["files"], -item[1]["lines"], item[0]),
            )
        ],
        "maintenance_2_overlap_files": [
            row_payload(row, touch_counts)
            for row in sorted(overlap_rows, key=lambda row: (-row.risk, -row.lines, row.path))
        ],
        "top_maintenance_risk_files": [row_payload(row, touch_counts) for row in ranked[:top_limit]],
    }


def row_payload(row: InventoryRow, touch_counts: collections.Counter[str]) -> dict[str, object]:
    return {
        "path": row.path,
        "family": row.family,
        "risk": row.risk,
        "maintenance": row.maintenance,
        "structural": row.structural,
        "performance": row.performance,
        "architectural": row.architectural,
        "lines": row.lines,
        "touches": touch_counts[row.path],
        "focus": row.focus,
    }


def print_report(summary: dict[str, object], *, since: str) -> None:
    totals = summary["totals"]
    assert isinstance(totals, dict)
    print("JavaScript inventory maintenance guardrail")
    print(f"history window: {since}")
    print(
        "maintenance>=2: "
        f"{totals['maintenance_2_files']} / {totals['files']} files "
        f"({totals['maintenance_2_file_percent']}%), "
        f"{totals['maintenance_2_lines']} / {totals['lines']} lines "
        f"({totals['maintenance_2_line_percent']}%)"
    )
    print(f"maintenance>=2 with overlapping structural/performance/architectural risk: {totals['maintenance_2_overlap_files']}")

    print("\nFiles by maintenance score")
    for score, count in summary["files_by_maintenance"].items():
        print(f"- {score}: {count}")

    print("\nMaintenance>=2 by family")
    for item in summary["maintenance_2_by_family"]:
        print(f"- {item['family']}: {item['files']} files, {item['lines']} lines, {item['touches']} recent touches")

    print("\nTop maintenance-risk files")
    for item in summary["top_maintenance_risk_files"]:
        scores = f"M/S/P/A={item['maintenance']}/{item['structural']}/{item['performance']}/{item['architectural']}"
        print(f"- {item['path']}: risk {item['risk']}, {scores}, {item['lines']} lines, {item['touches']} touches")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=REPO_ROOT, type=Path)
    parser.add_argument("--inventory", default=DEFAULT_INVENTORY, help="Inventory markdown path, relative to repo root.")
    parser.add_argument("--since", default="90 days", help="Git history window for recent touch counts.")
    parser.add_argument("--top", default=12, type=int, help="Number of top risk files to print.")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    inventory_path = repo_root / args.inventory
    rows = parse_inventory_table(inventory_path, repo_root)
    touch_counts = git_touch_counts(repo_root, args.since)
    summary = summarize(rows, touch_counts, top_limit=args.top)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_report(summary, since=args.since)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
