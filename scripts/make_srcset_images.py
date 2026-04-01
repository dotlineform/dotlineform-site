#!/usr/bin/env python3
"""Build srcset derivatives from staged source images."""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

try:
    from display_paths import format_display_command, format_display_path
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.display_paths import format_display_command, format_display_path

try:
    from pipeline_config import (
        env_var_name,
        env_var_value,
        join_base_and_subdir,
        load_pipeline_config,
        media_mode_input_subdir,
        media_mode_output_subdir,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.pipeline_config import (
        env_var_name,
        env_var_value,
        join_base_and_subdir,
        load_pipeline_config,
        media_mode_input_subdir,
        media_mode_output_subdir,
    )


SUPPORTED_PATTERNS: Sequence[str] = (
    "*.jpg", "*.JPG",
    "*.jpeg", "*.JPEG",
    "*.heic", "*.HEIC",
    "*.heif", "*.HEIF",
    "*.png", "*.PNG",
    "*.tif", "*.TIF",
    "*.tiff", "*.TIFF",
)
HEIF_EXTENSIONS = {"heic", "heif"}

PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
MEDIA_BASE_DIR_ENV_NAME = env_var_name(PIPELINE_CONFIG, "media_base_dir")
SRCSET_JOBS_ENV_NAME = env_var_name(PIPELINE_CONFIG, "srcset_jobs")
SELECTED_IDS_ENV_NAME = env_var_name(PIPELINE_CONFIG, "srcset_selected_ids_file")
SUCCESS_IDS_ENV_NAME = env_var_name(PIPELINE_CONFIG, "srcset_success_ids_file")
REPO_ROOT = Path(__file__).resolve().parents[1]
MEDIA_BASE_DIR = Path(media_base).expanduser() if (media_base := env_var_value(PIPELINE_CONFIG, "media_base_dir")) else None

PRIMARY_WIDTHS = [int(v) for v in PIPELINE_CONFIG["variants"]["compatibility"]["generate_widths"]]
THUMB_SIZES = [int(v) for v in PIPELINE_CONFIG["variants"]["thumb"]["sizes"]]
PRIMARY_SUFFIX = str(PIPELINE_CONFIG["variants"]["primary"]["suffix"])
THUMB_SUFFIX = str(PIPELINE_CONFIG["variants"]["thumb"]["suffix"])
PRIMARY_OUTPUT_SUBDIR = str(PIPELINE_CONFIG["variants"]["primary"]["output_subdir"])
THUMB_OUTPUT_SUBDIR = str(PIPELINE_CONFIG["variants"]["thumb"]["output_subdir"])
OUTPUT_FORMAT = str(PIPELINE_CONFIG["encoding"]["format"])
ENCODER_CODEC = str(PIPELINE_CONFIG["encoding"]["codec"])
WEBP_PRESET = str(PIPELINE_CONFIG["encoding"]["preset"])
PRIMARY_Q = int(PIPELINE_CONFIG["encoding"]["primary_quality"])
THUMB_Q = int(PIPELINE_CONFIG["encoding"]["thumb_quality"])
COMPRESSION_LEVEL = int(PIPELINE_CONFIG["encoding"]["compression_level"])


@dataclass
class ProcessResult:
    item_id: str
    messages: List[str] = field(default_factory=list)
    written_counts: Dict[str, int] = field(default_factory=dict)
    dry_counts: Dict[str, int] = field(default_factory=dict)
    processed_source: Path | None = None
    success_id: str | None = None


def parse_args() -> argparse.Namespace:
    media_base = env_var_value(PIPELINE_CONFIG, "media_base_dir")
    default_input = join_base_and_subdir(media_base, media_mode_input_subdir(PIPELINE_CONFIG, "work"))
    default_output = join_base_and_subdir(media_base, media_mode_output_subdir(PIPELINE_CONFIG, "work"))

    ap = argparse.ArgumentParser(
        description="Build srcset derivatives from staged source images.",
    )
    ap.add_argument("input_dir", nargs="?", default=default_input, help="Source images folder")
    ap.add_argument("output_dir", nargs="?", default=default_output, help="Derivative output root")
    ap.add_argument("jobs", nargs="?", default=os.environ.get(SRCSET_JOBS_ENV_NAME, "1"), help="Parallel workers")
    ap.add_argument("--dry-run", action="store_true", help="Preview writes and source cleanup only")
    args = ap.parse_args()

    if str(args.input_dir).strip() == "":
        raise SystemExit(f"Error: missing media base directory. Set {MEDIA_BASE_DIR_ENV_NAME} or pass INPUT_DIR.")
    if str(args.output_dir).strip() == "":
        raise SystemExit(f"Error: missing output directory. Set {MEDIA_BASE_DIR_ENV_NAME} or pass OUTPUT_DIR.")
    try:
        args.jobs = int(str(args.jobs).strip())
    except ValueError as exc:
        raise SystemExit(f"Error: invalid JOBS value: {args.jobs!r}") from exc
    if args.jobs < 1:
        raise SystemExit("Error: JOBS must be >= 1")
    return args


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def read_selected_ids(path_value: str) -> set[str]:
    if path_value == "":
        return set()
    ids_path = Path(path_value).expanduser()
    if not ids_path.exists():
        raise SystemExit(f"Error: {SELECTED_IDS_ENV_NAME} not found: {ids_path}")
    return {
        line.strip()
        for line in ids_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def collect_sources(input_dir: Path) -> List[Path]:
    sources: List[Path] = []
    for pattern in SUPPORTED_PATTERNS:
        sources.extend(sorted(input_dir.glob(pattern)))
    return sources


def counter_label_order() -> List[str]:
    labels = [THUMB_SUFFIX]
    labels.extend(f"{PRIMARY_SUFFIX}-{width}" for width in PRIMARY_WIDTHS)
    return labels


def output_path(output_dir: Path, variant_subdir: str, item_id: str, variant_label: str) -> Path:
    return output_dir / variant_subdir / f"{item_id}-{variant_label}.{OUTPUT_FORMAT}"


def run_ffmpeg(cmd: Sequence[str]) -> None:
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)


def timestamp_now() -> str:
    return time.strftime("%H:%M:%S")


def log_progress(message: str) -> None:
    print(f"[{timestamp_now()}] {message}", flush=True)


def result_summary(result: ProcessResult, dry_run: bool) -> str:
    counts = result.dry_counts if dry_run else result.written_counts
    total = sum(counts.values())
    if total == 0:
        return "no derivatives written"
    return format_summary(counts)


def display_path(path: Path | str) -> str:
    return format_display_path(
        path,
        repo_root=REPO_ROOT,
        media_base_dir=MEDIA_BASE_DIR,
    )


def display_filename(path: Path | str) -> str:
    return Path(path).name


def make_thumb(src: Path, size: int, out: Path, dry_run: bool, result: ProcessResult) -> None:
    label = THUMB_SUFFIX
    if dry_run:
        result.messages.append(f"DRY-RUN write thumb: {display_filename(out)}")
        result.dry_counts[label] = result.dry_counts.get(label, 0) + 1
        return

    run_ffmpeg(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-i",
            str(src),
            "-map_metadata",
            "-1",
            "-vf",
            f"scale='if(gt(iw,ih),-1,{size})':'if(gt(iw,ih),{size},-1)':flags=lanczos,crop={size}:{size}",
            "-c:v",
            ENCODER_CODEC,
            "-preset",
            WEBP_PRESET,
            "-q:v",
            str(THUMB_Q),
            "-compression_level",
            str(COMPRESSION_LEVEL),
            str(out),
        ]
    )
    result.messages.append(f"Wrote thumb: {display_filename(out)}")
    result.written_counts[label] = result.written_counts.get(label, 0) + 1


def make_primary(src: Path, width: int, out: Path, dry_run: bool, result: ProcessResult) -> None:
    label = f"{PRIMARY_SUFFIX}-{width}"
    if dry_run:
        result.messages.append(f"DRY-RUN write {label}: {display_filename(out)}")
        result.dry_counts[label] = result.dry_counts.get(label, 0) + 1
        return

    run_ffmpeg(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-y",
            "-i",
            str(src),
            "-map_metadata",
            "-1",
            "-vf",
            f"scale=w='min(iw,{width})':h=-2:flags=lanczos",
            "-c:v",
            ENCODER_CODEC,
            "-preset",
            WEBP_PRESET,
            "-q:v",
            str(PRIMARY_Q),
            "-compression_level",
            str(COMPRESSION_LEVEL),
            str(out),
        ]
    )
    result.messages.append(f"Wrote {label}: {display_filename(out)}")
    result.written_counts[label] = result.written_counts.get(label, 0) + 1


def convert_heif_source(src: Path, item_id: str, dry_run: bool, has_sips: bool, has_heif_convert: bool, result: ProcessResult) -> tuple[Path | None, Path | None]:
    ext_lc = src.suffix.lower().lstrip(".")
    if ext_lc not in HEIF_EXTENSIONS:
        return src, None

    tmp_dir = Path(tempfile.mkdtemp(prefix="dlf_heic_"))
    tmp_jpg = tmp_dir / f"{item_id}.jpg"
    if has_sips:
        if dry_run:
            result.messages.append(f"Converting {src.name} -> {tmp_jpg.name} (sips)")
            return src, tmp_dir
        result.messages.append(f"Converting {src.name} -> {tmp_jpg.name} (sips)")
        subprocess.run(
            ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "90", str(src), "--out", str(tmp_jpg)],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        return tmp_jpg, tmp_dir
    if has_heif_convert:
        if dry_run:
            result.messages.append(f"Converting {src.name} -> {tmp_jpg.name} (heif-convert)")
            return src, tmp_dir
        result.messages.append(f"Converting {src.name} -> {tmp_jpg.name} (heif-convert)")
        subprocess.run(
            ["heif-convert", "-q", "90", str(src), str(tmp_jpg)],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        return tmp_jpg, tmp_dir

    result.messages.append(
        f"Warning: {src.name} is HEIC/HEIF but neither 'sips' nor 'heif-convert' is available. Skipping."
    )
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return None, None


def process_one(
    src: Path,
    output_dir: Path,
    dry_run: bool,
    selected_ids: set[str],
    has_sips: bool,
    has_heif_convert: bool,
) -> ProcessResult:
    item_id = src.stem
    result = ProcessResult(item_id=item_id)

    if selected_ids and item_id not in selected_ids:
        result.messages.append(f"Skipping {src.name} ({item_id} not listed in {SELECTED_IDS_ENV_NAME})")
        return result

    log_progress(f"START {src.name} -> {item_id}")
    tmp_dir: Path | None = None
    try:
        src_use, tmp_dir = convert_heif_source(src, item_id, dry_run, has_sips, has_heif_convert, result)
        if src_use is None:
            return result

        for size in THUMB_SIZES:
            make_thumb(
                src_use,
                size,
                output_path(output_dir, THUMB_OUTPUT_SUBDIR, item_id, f"{THUMB_SUFFIX}-{size}"),
                dry_run,
                result,
            )
        for width in PRIMARY_WIDTHS:
            make_primary(
                src_use,
                width,
                output_path(output_dir, PRIMARY_OUTPUT_SUBDIR, item_id, f"{PRIMARY_SUFFIX}-{width}"),
                dry_run,
                result,
            )
        result.processed_source = src
        result.success_id = item_id
        return result
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def merge_counts(results: Iterable[ProcessResult], attr_name: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for result in results:
        counts = getattr(result, attr_name)
        for key, value in counts.items():
            out[key] = out.get(key, 0) + value
    return out


def format_summary(label_counts: Dict[str, int]) -> str:
    ordered = counter_label_order()
    parts = [f"{label}={label_counts.get(label, 0)}" for label in ordered]
    return ", ".join(parts)


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).expanduser()
    output_dir = Path(args.output_dir).expanduser()
    dry_run = bool(args.dry_run)
    jobs = int(args.jobs)

    if not command_exists("ffmpeg"):
        raise SystemExit("Error: ffmpeg not found. Install ffmpeg first.")

    has_sips = command_exists("sips")
    has_heif_convert = command_exists("heif-convert")
    selected_ids_env = env_var_value(PIPELINE_CONFIG, "srcset_selected_ids_file")
    success_ids_env = env_var_value(PIPELINE_CONFIG, "srcset_success_ids_file")

    sources = collect_sources(input_dir)
    if not sources:
        print(f"No supported image files found in: {display_path(input_dir)} (jpg/jpeg/heic/heif/png/tif/tiff)")
        if dry_run:
            print("Dry-run: no source images found; skipping derivative simulation.")
            return 0
        return 1

    selected_ids = read_selected_ids(selected_ids_env)
    if not dry_run:
        (output_dir / PRIMARY_OUTPUT_SUBDIR).mkdir(parents=True, exist_ok=True)
        (output_dir / THUMB_OUTPUT_SUBDIR).mkdir(parents=True, exist_ok=True)

    results: List[ProcessResult] = []
    if jobs <= 1:
        for src in sources:
            result = process_one(src, output_dir, dry_run, selected_ids, has_sips, has_heif_convert)
            results.append(result)
            for message in result.messages:
                print(message)
            if result.success_id is not None:
                log_progress(f"DONE  {result.item_id} ({result_summary(result, dry_run)})")
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
            futures = {
                executor.submit(process_one, src, output_dir, dry_run, selected_ids, has_sips, has_heif_convert): src
                for src in sources
            }
            try:
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    results.append(result)
                    for message in result.messages:
                        print(message)
                    if result.success_id is not None:
                        log_progress(f"DONE  {result.item_id} ({result_summary(result, dry_run)})")
            except Exception:
                for future in futures:
                    future.cancel()
                raise

    processed_sources = [result.processed_source for result in results if result.processed_source is not None]
    success_ids = [result.success_id for result in results if result.success_id is not None]

    if dry_run:
        print(f"DRY-RUN delete source file(s): {len(processed_sources)} from: {display_path(input_dir)}")
    else:
        for src in processed_sources:
            Path(src).unlink(missing_ok=True)
        print(f"Deleted {len(processed_sources)} source file(s) from: {display_path(input_dir)}")

    if (not dry_run) and success_ids_env:
        success_ids_path = Path(success_ids_env).expanduser()
        success_ids_path.parent.mkdir(parents=True, exist_ok=True)
        success_ids_path.write_text(
            "\n".join(success_ids) + ("\n" if success_ids else ""),
            encoding="utf-8",
        )

    print(f"Done. Primaries written to: {display_path(output_dir / PRIMARY_OUTPUT_SUBDIR)}")
    print(f"Done. Thumbnails written to: {display_path(output_dir / THUMB_OUTPUT_SUBDIR)}")

    written_counts = merge_counts(results, "written_counts")
    dry_counts = merge_counts(results, "dry_counts")
    written_total = sum(written_counts.values())
    dry_total = sum(dry_counts.values())

    print("Derivative report:")
    print(f"  written total: {written_total} ({format_summary(written_counts)})")
    print(f"  dry-run total: {dry_total} ({format_summary(dry_counts)})")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(
            "Error: command failed with exit code "
            f"{exc.returncode}: "
            + format_display_command(
                [str(part) for part in exc.cmd],
                repo_root=REPO_ROOT,
                media_base_dir=MEDIA_BASE_DIR,
            ),
            file=sys.stderr,
        )
        raise SystemExit(exc.returncode)
