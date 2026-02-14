#!/usr/bin/env python3
"""
Run the draft publish pipeline end-to-end (fail-fast):

1) copy_draft_work_files.py --write
2) make_srcset_images.sh
3) copy_draft_work_detail_files.py --write
4) make_srcset_images.sh (for work details)
5) generate_work_pages.py data/works.xlsx --write (for affected work IDs only)

The 2400px derivative selection is driven from Works.has_primary_2400:
- empty cell -> do not request 2400
- non-empty cell -> request 2400

Dry-run mode:
- copy + srcset + generate run in preview mode
- no workbook writes/deletes are performed
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

    required = ["work_id"]
    missing = [c for c in required if c not in hi]
    if missing:
        raise SystemExit(f"Works sheet missing required columns: {', '.join(missing)}")

    has_col = hi.get("has_primary_2400")
    if has_col is None:
        return set()

    want_2400: Set[str] = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        work_id = row[hi["work_id"]]
        if is_empty(work_id):
            continue
        wid = slug_id(work_id)
        if wid not in copied:
            continue
        raw = row[has_col] if has_col < len(row) else None
        if not is_empty(raw):
            want_2400.add(wid)
    return want_2400


def collect_draft_ids(xlsx_path: Path) -> Set[str]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    if "Works" not in wb.sheetnames:
        raise SystemExit("Worksheet not found: 'Works'")
    ws = wb["Works"]
    hi = header_map(ws)

    required = ["work_id", "status"]
    missing = [c for c in required if c not in hi]
    if missing:
        raise SystemExit(f"Works sheet missing required columns: {', '.join(missing)}")

    out: Set[str] = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        raw_work_id = row[hi["work_id"]]
        if is_empty(raw_work_id):
            continue
        wid = slug_id(raw_work_id)
        status = normalize_status(row[hi["status"]])
        if status != "draft":
            continue
        out.add(wid)
    return out


def collect_draft_detail_uids(xlsx_path: Path) -> Set[str]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    if "WorkDetails" not in wb.sheetnames:
        return set()
    ws = wb["WorkDetails"]
    hi = header_map(ws)

    required = ["work_id", "detail_id", "status"]
    missing = [c for c in required if c not in hi]
    if missing:
        raise SystemExit(f"WorkDetails sheet missing required columns: {', '.join(missing)}")

    out: Set[str] = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        raw_work_id = row[hi["work_id"]]
        raw_detail_id = row[hi["detail_id"]]
        if is_empty(raw_work_id) or is_empty(raw_detail_id):
            continue
        wid = slug_id(raw_work_id)
        did = slug_id(raw_detail_id, width=3)
        status = normalize_status(row[hi["status"]])
        if status != "draft":
            continue
        out.add(f"{wid}-{did}")
    return out


def collect_detail_2400_uids(xlsx_path: Path, copied_uids: Iterable[str]) -> Set[str]:
    copied = set(copied_uids)
    if not copied:
        return set()

    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    if "WorkDetails" not in wb.sheetnames:
        return set()
    ws = wb["WorkDetails"]
    hi = header_map(ws)

    required = ["work_id", "detail_id"]
    missing = [c for c in required if c not in hi]
    if missing:
        raise SystemExit(f"WorkDetails sheet missing required columns: {', '.join(missing)}")

    has_col = hi.get("has_primary_2400")
    if has_col is None:
        return set()

    want_2400: Set[str] = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        raw_work_id = row[hi["work_id"]]
        raw_detail_id = row[hi["detail_id"]]
        if is_empty(raw_work_id) or is_empty(raw_detail_id):
            continue
        wid = slug_id(raw_work_id)
        did = slug_id(raw_detail_id, width=3)
        uid = f"{wid}-{did}"
        if uid not in copied:
            continue
        raw = row[has_col] if has_col < len(row) else None
        if not is_empty(raw):
            want_2400.add(uid)
    return want_2400


def work_ids_from_detail_uids(detail_uids: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for uid in detail_uids:
        s = str(uid).strip()
        if not s or "-" not in s:
            continue
        out.add(s.split("-", 1)[0])
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Run copy -> make_srcset -> generate pipeline.")
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
    ap.add_argument(
        "--detail-input-dir",
        default="/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/work_details/make_srcset_images",
        help="Input directory for work detail source images",
    )
    ap.add_argument(
        "--detail-output-dir",
        default="/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/work_details/srcset_images",
        help="Output directory for work detail srcset derivatives",
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
    copy_detail_script = repo_root / "scripts/copy_draft_work_detail_files.py"
    make_script = repo_root / "scripts/make_srcset_images.sh"
    generate_script = repo_root / "scripts/generate_work_pages.py"

    with tempfile.TemporaryDirectory(prefix="draft-pipeline-") as tmp:
        tmp_dir = Path(tmp)
        draft_ids_file = tmp_dir / "draft_ids.txt"
        copied_ids_file = tmp_dir / "copied_ids.txt"
        draft_detail_uids_file = tmp_dir / "draft_detail_uids.txt"
        copied_detail_uids_file = tmp_dir / "copied_detail_uids.txt"
        ids_2400_file = tmp_dir / "ids_2400.txt"
        detail_ids_2400_file = tmp_dir / "detail_ids_2400.txt"
        success_ids_file = tmp_dir / "success_ids.txt"
        detail_success_ids_file = tmp_dir / "detail_success_ids.txt"
        generate_ids_file = tmp_dir / "generate_ids.txt"

        draft_ids = collect_draft_ids(xlsx_path)
        draft_ids_file.write_text(
            "\n".join(sorted(draft_ids)) + ("\n" if draft_ids else ""),
            encoding="utf-8",
        )
        print(f"Draft candidates: {len(draft_ids)}")

        draft_detail_uids = collect_draft_detail_uids(xlsx_path)
        draft_detail_uids_file.write_text(
            "\n".join(sorted(draft_detail_uids)) + ("\n" if draft_detail_uids else ""),
            encoding="utf-8",
        )
        print(f"Draft detail candidates: {len(draft_detail_uids)}")

        run_step(
            "Copy Draft Work Files",
            [
                "python3",
                str(copy_script),
                "--work-ids-file",
                str(draft_ids_file),
                "--copied-ids-file",
                str(copied_ids_file),
            ]
            + ([] if args.dry_run else ["--write"]),
            cwd=repo_root,
        )

        copied_ids = read_ids(copied_ids_file)
        generated_work_ids = set()
        if copied_ids:
            ids_2400 = collect_2400_ids(xlsx_path, copied_ids)
            ids_2400_file.write_text(
                "\n".join(sorted(ids_2400)) + ("\n" if ids_2400 else ""),
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["MAKE_SRCSET_2400_IDS_FILE"] = str(ids_2400_file)
            env["MAKE_SRCSET_WORK_IDS_FILE"] = str(copied_ids_file)
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
                generated_work_ids = copied_ids
            else:
                generated_work_ids = read_ids(success_ids_file)
        else:
            print("\n==> Skip Srcset\nNo copied draft files in this run.")
            generated_work_ids = set()

        run_step(
            "Copy Draft Work Detail Files",
            [
                "python3",
                str(copy_detail_script),
                "--detail-uids-file",
                str(draft_detail_uids_file),
                "--copied-detail-uids-file",
                str(copied_detail_uids_file),
            ]
            + ([] if args.dry_run else ["--write"]),
            cwd=repo_root,
        )

        copied_detail_uids = read_ids(copied_detail_uids_file)
        generated_detail_uids = set()
        if copied_detail_uids:
            detail_2400_ids = collect_detail_2400_uids(xlsx_path, copied_detail_uids)
            detail_ids_2400_file.write_text(
                "\n".join(sorted(detail_2400_ids)) + ("\n" if detail_2400_ids else ""),
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["MAKE_SRCSET_2400_IDS_FILE"] = str(detail_ids_2400_file)
            env["MAKE_SRCSET_WORK_IDS_FILE"] = str(copied_detail_uids_file)
            env["MAKE_SRCSET_SUCCESS_IDS_FILE"] = str(detail_success_ids_file)

            run_step(
                "Generate Work Detail Srcset Derivatives",
                [
                    "bash",
                    str(make_script),
                    str(args.detail_input_dir),
                    str(args.detail_output_dir),
                    str(args.jobs),
                ]
                + (["--dry-run"] if args.dry_run else []),
                cwd=repo_root,
                env=env,
            )

            if args.dry_run:
                generated_detail_uids = copied_detail_uids
            else:
                generated_detail_uids = read_ids(detail_success_ids_file)
        else:
            print("\n==> Skip Work Detail Srcset\nNo copied detail files in this run.")
            generated_detail_uids = set()

        generate_ids = set(generated_work_ids)
        generate_ids.update(work_ids_from_detail_uids(generated_detail_uids))

        generate_ids_file.write_text(
            "\n".join(sorted(generate_ids)) + ("\n" if generate_ids else ""),
            encoding="utf-8",
        )

        generate_cmd = ["python3", str(generate_script), str(xlsx_path)]
        generate_cmd += ["--work-ids-file", str(generate_ids_file)]
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
