#!/usr/bin/env python3
"""
Run the draft publish pipeline end-to-end (fail-fast):

1) copy_draft_media_files.py --mode work --write
2) make_srcset_images.sh
3) copy_draft_media_files.py --mode work_details --write
4) make_srcset_images.sh (for work details)
5) copy_draft_media_files.py --mode moment --write
6) make_srcset_images.sh (for moments)
7) generate_work_pages.py data/works.xlsx --write (for affected work IDs only)

The 2400px derivative selection is driven from Works.has_primary_2400:
- empty cell -> do not request 2400
- non-empty cell -> request 2400

Dry-run mode:
- copy + srcset + generate run in preview mode
- no workbook writes/deletes are performed

Flag usage summary:
- --xlsx: workbook path (repo-relative by default)
- --dry-run: preview-only mode for all steps
- --force-generate: pass --force to generate_work_pages.py
- --jobs: parallelism for make_srcset_images.sh
- --*-input-dir / --*-output-dir: source/derivative directories for each media type
- --mode: select one or more flows: work, work_details, moment (repeatable)
- --work-ids / --work-ids-file: limit work + work_details processing scope
- --series-ids / --series-ids-file: pass series filter into generation
- --moment-ids / --moment-ids-file: limit moment processing scope

Manifest files (created in a temporary directory):
- draft_*: candidates from workbook (status=draft)
- copied_*: successfully copied source IDs (input to srcset step)
- *_success_ids: srcset-success IDs returned by make_srcset_images.sh
- generate_ids.txt: work IDs to regenerate (works + any work_details parents)
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
    """Run one pipeline step and fail fast on non-zero exit."""
    print(f"\n==> {label}")
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


def read_ids(path: Path) -> Set[str]:
    """Read newline-delimited IDs from a manifest file."""
    if not path.exists():
        return set()
    out: Set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s:
            out.add(s)
    return out


def read_optional_ids_file(path: str) -> Set[str]:
    if not path:
        return set()
    ids_path = Path(path).expanduser()
    if not ids_path.exists():
        raise SystemExit(f"IDs file not found: {ids_path}")
    return read_ids(ids_path)


def collect_2400_ids(xlsx_path: Path, copied_ids: Iterable[str]) -> Set[str]:
    """Select work IDs that require 2400 derivatives based on Works.has_primary_2400."""
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


def collect_draft_ids(
    xlsx_path: Path,
    allowed_ids: Set[str] | None = None,
    include_published: bool = False,
) -> Set[str]:
    """Collect draft work_ids from Works.status."""
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
        if allowed_ids is not None and wid not in allowed_ids:
            continue
        status = normalize_status(row[hi["status"]])
        if status != "draft" and not (include_published and status == "published"):
            continue
        out.add(wid)
    return out


def collect_draft_detail_uids(
    xlsx_path: Path,
    allowed_uids: Set[str] | None = None,
    allowed_work_ids: Set[str] | None = None,
    include_published: bool = False,
) -> Set[str]:
    """Collect draft detail_uids from WorkDetails.status."""
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
        uid = f"{wid}-{did}"
        if allowed_uids is not None and uid not in allowed_uids:
            continue
        if allowed_work_ids is not None and wid not in allowed_work_ids:
            continue
        status = normalize_status(row[hi["status"]])
        if status != "draft" and not (include_published and status == "published"):
            continue
        out.add(uid)
    return out


def collect_draft_moment_ids(
    xlsx_path: Path,
    allowed_ids: Set[str] | None = None,
    include_published: bool = False,
) -> Set[str]:
    """Collect draft moment_ids from Moments.status."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    if "Moments" not in wb.sheetnames:
        return set()
    ws = wb["Moments"]
    hi = header_map(ws)

    required = ["moment_id", "status"]
    missing = [c for c in required if c not in hi]
    if missing:
        raise SystemExit(f"Moments sheet missing required columns: {', '.join(missing)}")

    out: Set[str] = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        raw_moment_id = row[hi["moment_id"]]
        if is_empty(raw_moment_id):
            continue
        mid = normalize_text(raw_moment_id).lower()
        if not mid:
            continue
        if allowed_ids is not None and mid not in allowed_ids:
            continue
        status = normalize_status(row[hi["status"]])
        if status != "draft" and not (include_published and status == "published"):
            continue
        out.add(mid)
    return out


def collect_detail_2400_uids(xlsx_path: Path, copied_uids: Iterable[str]) -> Set[str]:
    """Select detail_uids that require 2400 derivatives based on WorkDetails.has_primary_2400."""
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
    """Map detail_uids (work_id-detail_id) to parent work_ids."""
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
        "--mode",
        action="append",
        choices=["work", "work_details", "moment"],
        help="Flow(s) to run. Repeat to run multiple modes. Default: all.",
    )
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
    ap.add_argument(
        "--moment-input-dir",
        default="/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/moments/make_srcset_images",
        help="Input directory for moment source images",
    )
    ap.add_argument(
        "--moment-output-dir",
        default="/Users/dlf/Library/Mobile Documents/com~apple~CloudDocs/dotlineform/moments/srcset_images",
        help="Output directory for moment srcset derivatives",
    )
    ap.add_argument("--jobs", type=int, default=int(os.environ.get("MAKE_SRCSET_JOBS", "1")), help="Parallel jobs")
    ap.add_argument("--force-generate", action="store_true", help="Pass --force to generate_work_pages.py")
    ap.add_argument("--dry-run", action="store_true", help="Preview mode; no writes/deletes.")
    ap.add_argument("--work-ids", default="", help="Comma-separated work_ids filter for this run.")
    ap.add_argument("--work-ids-file", default="", help="Path to work_ids file (one id per line).")
    ap.add_argument("--series-ids", default="", help="Comma-separated series_ids passed to generation.")
    ap.add_argument("--series-ids-file", default="", help="Path to series_ids file (one id per line).")
    ap.add_argument("--moment-ids", default="", help="Comma-separated moment_ids filter for this run.")
    ap.add_argument("--moment-ids-file", default="", help="Path to moment_ids file (one id per line).")
    args = ap.parse_args()
    selected_modes = set(args.mode or ["work", "work_details", "moment"])

    explicit_work_ids = read_optional_ids_file(args.work_ids_file)
    if args.work_ids:
        explicit_work_ids.update({slug_id(w.strip()) for w in args.work_ids.split(",") if w.strip()})
    work_filter = explicit_work_ids if explicit_work_ids else None

    explicit_series_ids = read_optional_ids_file(args.series_ids_file)
    if args.series_ids:
        explicit_series_ids.update({normalize_text(s.strip()) for s in args.series_ids.split(",") if s.strip()})
    series_filter = explicit_series_ids if explicit_series_ids else None

    explicit_moment_ids = read_optional_ids_file(args.moment_ids_file)
    if args.moment_ids:
        explicit_moment_ids.update({normalize_text(m.strip()).lower() for m in args.moment_ids.split(",") if m.strip()})
    moment_filter = explicit_moment_ids if explicit_moment_ids else None

    repo_root = Path(__file__).resolve().parents[1]
    xlsx_path = (repo_root / args.xlsx).resolve()
    if not xlsx_path.exists():
        raise SystemExit(f"Workbook not found: {xlsx_path}")

    copy_script = repo_root / "scripts/copy_draft_media_files.py"
    make_script = repo_root / "scripts/make_srcset_images.sh"
    generate_script = repo_root / "scripts/generate_work_pages.py"
    py = sys.executable

    with tempfile.TemporaryDirectory(prefix="draft-pipeline-") as tmp:
        tmp_dir = Path(tmp)
        draft_ids_file = tmp_dir / "draft_ids.txt"
        copied_ids_file = tmp_dir / "copied_ids.txt"
        draft_detail_uids_file = tmp_dir / "draft_detail_uids.txt"
        copied_detail_uids_file = tmp_dir / "copied_detail_uids.txt"
        ids_2400_file = tmp_dir / "ids_2400.txt"
        detail_ids_2400_file = tmp_dir / "detail_ids_2400.txt"
        moment_ids_2400_file = tmp_dir / "moment_ids_2400.txt"
        success_ids_file = tmp_dir / "success_ids.txt"
        detail_success_ids_file = tmp_dir / "detail_success_ids.txt"
        moment_success_ids_file = tmp_dir / "moment_success_ids.txt"
        draft_moment_ids_file = tmp_dir / "draft_moment_ids.txt"
        copied_moment_ids_file = tmp_dir / "copied_moment_ids.txt"
        generate_moment_ids_file = tmp_dir / "generate_moment_ids.txt"
        generate_ids_file = tmp_dir / "generate_ids.txt"

        draft_ids = set()
        if "work" in selected_modes:
            draft_ids = collect_draft_ids(
                xlsx_path,
                allowed_ids=work_filter,
                include_published=bool(args.force_generate and work_filter is not None),
            )
        draft_ids_file.write_text(
            "\n".join(sorted(draft_ids)) + ("\n" if draft_ids else ""),
            encoding="utf-8",
        )
        print(f"Draft candidates (work): {len(draft_ids)}")

        draft_detail_uids = set()
        if "work_details" in selected_modes:
            draft_detail_uids = collect_draft_detail_uids(
                xlsx_path,
                allowed_uids=None,
                allowed_work_ids=work_filter,
                include_published=bool(args.force_generate and work_filter is not None),
            )
        draft_detail_uids_file.write_text(
            "\n".join(sorted(draft_detail_uids)) + ("\n" if draft_detail_uids else ""),
            encoding="utf-8",
        )
        print(f"Draft detail candidates (work_details): {len(draft_detail_uids)}")

        draft_moment_ids = set()
        if "moment" in selected_modes:
            draft_moment_ids = collect_draft_moment_ids(
                xlsx_path,
                allowed_ids=moment_filter,
                include_published=bool(args.force_generate and moment_filter is not None),
            )
        draft_moment_ids_file.write_text(
            "\n".join(sorted(draft_moment_ids)) + ("\n" if draft_moment_ids else ""),
            encoding="utf-8",
        )
        print(f"Draft moment candidates (moment): {len(draft_moment_ids)}")

        copied_ids = read_ids(copied_ids_file)
        generated_work_ids = set()
        if "work" in selected_modes:
            run_step(
                "Copy Draft Work Files",
                [
                    py,
                    str(copy_script),
                    "--mode",
                    "work",
                    "--ids-file",
                    str(draft_ids_file),
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

                # make_srcset_images.sh controls selection via environment variables.
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
        else:
            print("\n==> Skip Work\nMode not selected.")
            generated_work_ids = set()

        copied_detail_uids = read_ids(copied_detail_uids_file)
        generated_detail_uids = set()
        if "work_details" in selected_modes:
            run_step(
                "Copy Draft Work Detail Files",
                [
                    py,
                    str(copy_script),
                    "--mode",
                    "work_details",
                    "--ids-file",
                    str(draft_detail_uids_file),
                    "--copied-ids-file",
                    str(copied_detail_uids_file),
                ]
                + ([] if args.dry_run else ["--write"]),
                cwd=repo_root,
            )

            copied_detail_uids = read_ids(copied_detail_uids_file)
            if copied_detail_uids:
                detail_2400_ids = collect_detail_2400_uids(xlsx_path, copied_detail_uids)
                detail_ids_2400_file.write_text(
                    "\n".join(sorted(detail_2400_ids)) + ("\n" if detail_2400_ids else ""),
                    encoding="utf-8",
                )

                # Restrict run to copied detail_uids and track success IDs.
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
        else:
            print("\n==> Skip Work Details\nMode not selected.")
            generated_detail_uids = set()

        copied_moment_ids = read_ids(copied_moment_ids_file)
        generated_moment_ids = set()
        if "moment" in selected_modes:
            run_step(
                "Copy Draft Moment Files",
                [
                    py,
                    str(copy_script),
                    "--mode",
                    "moment",
                    "--ids-file",
                    str(draft_moment_ids_file),
                    "--copied-ids-file",
                    str(copied_moment_ids_file),
                ]
                + ([] if args.dry_run else ["--write"]),
                cwd=repo_root,
            )

            copied_moment_ids = read_ids(copied_moment_ids_file)
            if copied_moment_ids:
                # Moments never request 2400 derivatives: set an explicit empty allow-list.
                moment_ids_2400_file.write_text("", encoding="utf-8")
                # Restrict run to copied moment_ids and track success IDs.
                env = os.environ.copy()
                env["MAKE_SRCSET_2400_IDS_FILE"] = str(moment_ids_2400_file)
                env["MAKE_SRCSET_WORK_IDS_FILE"] = str(copied_moment_ids_file)
                env["MAKE_SRCSET_SUCCESS_IDS_FILE"] = str(moment_success_ids_file)

                run_step(
                    "Generate Moment Srcset Derivatives",
                    [
                        "bash",
                        str(make_script),
                        str(args.moment_input_dir),
                        str(args.moment_output_dir),
                        str(args.jobs),
                    ]
                    + (["--dry-run"] if args.dry_run else []),
                    cwd=repo_root,
                    env=env,
                )

                if args.dry_run:
                    generated_moment_ids = copied_moment_ids
                else:
                    generated_moment_ids = read_ids(moment_success_ids_file)
            else:
                print("\n==> Skip Moment Srcset\nNo copied moment files in this run.")
        else:
            print("\n==> Skip Moments\nMode not selected.")
            generated_moment_ids = set()

        generate_ids = set(generated_work_ids)
        generate_ids.update(work_ids_from_detail_uids(generated_detail_uids))

        generate_ids_file.write_text(
            "\n".join(sorted(generate_ids)) + ("\n" if generate_ids else ""),
            encoding="utf-8",
        )
        # Moment generation should be driven by selected draft moments, not copied image IDs.
        # This ensures moments without images are still generated.
        generate_moment_ids_file.write_text(
            "\n".join(sorted(draft_moment_ids)) + ("\n" if draft_moment_ids else ""),
            encoding="utf-8",
        )

        generate_cmd = [py, str(generate_script), str(xlsx_path)]
        generate_cmd += ["--work-ids-file", str(generate_ids_file)]
        generate_cmd += ["--moment-ids-file", str(generate_moment_ids_file)]
        if series_filter is not None:
            generate_cmd += ["--series-ids", ",".join(sorted(series_filter))]
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
