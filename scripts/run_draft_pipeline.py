#!/usr/bin/env python3
"""
Run the draft publish pipeline end-to-end (fail-fast):

1) copy_draft_work_files.py --write
2) make_srcset_images.sh
3) mark successfully processed draft works as ready
4) generate_work_pages.py data/works.xlsx --write

The 2400px derivative selection is driven from Works.has_primary_2400:
- empty cell -> do not request 2400
- non-empty cell -> request 2400

Dry-run mode:
- copy + generate run in preview mode
- srcset generation and status updates are skipped (to avoid writes/deletes)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Set

import openpyxl


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if s.startswith("'") and len(s) > 1:
        s = s[1:]
    return s


def normalize_status(value: Any) -> str:
    return normalize_text(value).lower()


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def slug_id(raw: Any, width: int = 5) -> str:
    if raw is None:
        raise ValueError("Missing id")
    s = normalize_text(raw)
    s = re.sub(r"\.0$", "", s)
    s = re.sub(r"\D", "", s)
    if not s:
        raise ValueError(f"Invalid id value: {raw!r}")
    return s.zfill(width)


def header_map(ws) -> Dict[str, int]:
    headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
    hi: Dict[str, int] = {}
    for i, h in enumerate(headers):
        if h is None:
            continue
        key = str(h).strip()
        hi[key] = i
        hi[key.lower()] = i
    return hi


def run_step(label: str, cmd: list[str], cwd: Path, env: Dict[str, str] | None = None) -> None:
    print(f"\n==> {label}")
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


def read_ids(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    out: Set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s:
            out.add(s)
    return out


def collect_2400_ids(xlsx_path: Path, copied_ids: Iterable[str]) -> Set[str]:
    copied = set(copied_ids)
    if not copied:
        return set()

    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    if "Works" not in wb.sheetnames:
        raise SystemExit("Worksheet not found: 'Works'")
    ws = wb["Works"]
    hi = header_map(ws)

    required = ["work_id", "status"]
    missing = [c for c in required if c not in hi]
    if missing:
        raise SystemExit(f"Works sheet missing required columns: {', '.join(missing)}")

    has_col = hi.get("has_primary_2400")
    if has_col is None:
        return set()

    want_2400: Set[str] = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        work_id = row[hi["work_id"]]
        status = row[hi["status"]]
        if is_empty(work_id):
            continue
        wid = slug_id(work_id)
        if wid not in copied:
            continue
        if normalize_status(status) != "draft":
            continue
        raw = row[has_col] if has_col < len(row) else None
        if not is_empty(raw):
            want_2400.add(wid)
    return want_2400


def mark_ready(xlsx_path: Path, success_ids: Set[str]) -> int:
    if not success_ids:
        return 0

    wb = openpyxl.load_workbook(xlsx_path, read_only=False, data_only=False)
    if "Works" not in wb.sheetnames:
        raise SystemExit("Worksheet not found: 'Works'")
    ws = wb["Works"]
    hi = header_map(ws)

    required = ["work_id", "status"]
    missing = [c for c in required if c not in hi]
    if missing:
        raise SystemExit(f"Works sheet missing required columns: {', '.join(missing)}")

    updated = 0
    for row_cells in ws.iter_rows(min_row=2):
        raw_work_id = row_cells[hi["work_id"]].value
        if is_empty(raw_work_id):
            continue
        wid = slug_id(raw_work_id)
        if wid not in success_ids:
            continue
        status = normalize_status(row_cells[hi["status"]].value)
        if status == "draft":
            row_cells[hi["status"]].value = "ready"
            updated += 1

    if updated > 0:
        wb.save(xlsx_path)
    return updated


def main() -> int:
    ap = argparse.ArgumentParser(description="Run copy -> make_srcset -> ready-update -> generate pipeline.")
    ap.add_argument("--xlsx", default="data/works.xlsx", help="Path to workbook")
    ap.add_argument(
        "--input-dir",
        default="/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/works/make_srcset_images",
        help="Input directory for source images",
    )
    ap.add_argument(
        "--output-dir",
        default="/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/works/srcset_images",
        help="Output directory for srcset derivatives",
    )
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("MAKE_SRCSET_JOBS", "1")), help="Parallel jobs")
    ap.add_argument("--force-generate", action="store_true", help="Pass --force to generate_work_pages.py")
    ap.add_argument("--dry-run", action="store_true", help="Preview mode; no writes/deletes.")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    xlsx_path = (repo_root / args.xlsx).resolve()
    if not xlsx_path.exists():
        raise SystemExit(f"Workbook not found: {xlsx_path}")

    copy_script = repo_root / "scripts/copy_draft_work_files.py"
    make_script = repo_root / "scripts/make_srcset_images.sh"
    generate_script = repo_root / "scripts/generate_work_pages.py"

    with tempfile.TemporaryDirectory(prefix="draft-pipeline-") as tmp:
        tmp_dir = Path(tmp)
        copied_ids_file = tmp_dir / "copied_ids.txt"
        ids_2400_file = tmp_dir / "ids_2400.txt"
        success_ids_file = tmp_dir / "success_ids.txt"

        run_step(
            "Copy Draft Work Files",
            [
                "python3",
                str(copy_script),
                "--copied-ids-file",
                str(copied_ids_file),
            ]
            + ([] if args.dry_run else ["--write"]),
            cwd=repo_root,
        )

        copied_ids = read_ids(copied_ids_file)
        if copied_ids:
            ids_2400 = collect_2400_ids(xlsx_path, copied_ids)
            ids_2400_file.write_text(
                "\n".join(sorted(ids_2400)) + ("\n" if ids_2400 else ""),
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["MAKE_SRCSET_2400_IDS_FILE"] = str(ids_2400_file)
            env["MAKE_SRCSET_SUCCESS_IDS_FILE"] = str(success_ids_file)

            run_step(
                "Generate Srcset Derivatives",
                [
                    "bash",
                    str(make_script),
                    str(args.input_dir),
                    str(args.output_dir),
                    str(args.jobs),
                ]
                + (["--dry-run"] if args.dry_run else []),
                cwd=repo_root,
                env=env,
            )

            if args.dry_run:
                print("\n==> Skip Ready Update\nDry-run mode: status updates are skipped.")
            else:
                success_ids = read_ids(success_ids_file)
                updated = mark_ready(xlsx_path, success_ids)
                print(f"\n==> Mark Ready\nUpdated Works.status draft->ready for {updated} row(s).")
        else:
            print("\n==> Skip Srcset + Ready Update\nNo copied draft files in this run.")

        generate_cmd = ["python3", str(generate_script), str(xlsx_path)]
        if not args.dry_run:
            generate_cmd.append("--write")
        if args.force_generate:
            generate_cmd.append("--force")
        run_step("Generate Work Pages", generate_cmd, cwd=repo_root)

    print("\nPipeline complete.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as e:
        print(f"\nPipeline failed at command: {' '.join(e.cmd)}", file=sys.stderr)
        raise SystemExit(e.returncode)
