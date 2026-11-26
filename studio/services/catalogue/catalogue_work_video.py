"""Prepare and select one complete HLS package for a saved Catalogue Work."""

from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from typing import Any

from catalogue.catalogue_output_paths import output_path
from catalogue.catalogue_pending_state import WORK_ID, load_pending_queue, pending_path, persist_pending_queue
from catalogue.catalogue_pending_updates import FILENAME
from catalogue.catalogue_service_context import build_catalogue_write_context, load_works_payload
from catalogue.catalogue_source import PIPELINE_CONFIG, payload_for_map
from catalogue.catalogue_staged_media import catalogue_staging_assets
from catalogue.catalogue_transactions import execute_source_json_write
from catalogue_work_media_sources import resolve_work_media_path, resolve_work_media_source_root
from local_env import runtime_env


VIDEO_SOURCE_EXTENSIONS = frozenset({".m4v", ".mov", ".mp4"})


def prepare_work_video(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    work_id = body.get("work_id")
    if set(body) != {"work_id"} or not isinstance(work_id, str) or not WORK_ID.fullmatch(work_id):
        raise ValueError("Prepare video requires an exact Work ID")
    context = build_catalogue_write_context(repo_root)
    works = load_works_payload(context.works_path)["works"]
    if work_id not in works or not works[work_id].get("video_source"):
        raise ValueError(f"Work {work_id}: save a video source before preparation")
    record = works[work_id]
    phase = "source"
    try:
        source_root = resolve_work_media_source_root(
            PIPELINE_CONFIG, environ=runtime_env(repo_root=repo_root), require_exists=True,
        )
        source = resolve_work_media_path(source_root, record["video_source"], require_exists=True)
        if not source.is_file() or source.suffix.lower() not in VIDEO_SOURCE_EXTENSIONS:
            raise ValueError("Select a Projects M4V, MOV or MP4 file")

        phase = "encode"
        staging = catalogue_staging_assets(repo_root, config=PIPELINE_CONFIG).work_video
        staging.path.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="prepare-", dir=staging.path) as directory:
            package = Path(directory) / "hls"
            encode = subprocess.run(
                [str(repo_root / "bin/prepare-hls-pilot"), str(source), str(package)],
                capture_output=True, text=True, check=False,
            )
            if encode.returncode:
                detail = encode.stderr.strip().splitlines()
                raise RuntimeError(detail[-1] if detail else "FFmpeg did not complete")
            files = sorted(path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file())
            duration = sum(float(line.removeprefix("#EXTINF:").split(",", 1)[0])
                           for line in (package / "720p/index.m3u8").read_text().splitlines()
                           if line.startswith("#EXTINF:"))

            phase = "staging"
            queue_path = pending_path(repo_root, FILENAME)
            pending = load_pending_queue(queue_path)
            for name in files:
                target = output_path(staging, f"{work_id}/{name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                (package / name).replace(target)

        phase = "saved record"
        prepared = {"staged": True, "files": files}
        if record.get("video_package") != prepared:
            record["video_package"] = prepared
            execute_source_json_write({context.works_path: payload_for_map("works", works)}, dry_run=False, repo_root=repo_root)
        phase = "Refresh queue"
        entry = pending["current_works"].setdefault(work_id, {"metadata": False, "image": False, "file_names": []})
        entry.update(video_files=files, refreshed=False)
        persist_pending_queue(queue_path, pending, progress="refreshed")
    except (OSError, RuntimeError, ValueError) as error:
        raise RuntimeError(f"Prepare video incomplete ({work_id}, {phase}): {error}") from error
    return {"ok": True, "work_id": work_id, "duration_seconds": duration}
