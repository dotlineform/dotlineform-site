"""Local Studio app adapter for narrow Catalogue-owned routes."""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path
import stat
import sys
from typing import Any, Mapping

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths


REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"
STUDIO_DIR = Path(__file__).resolve().parent
for candidate in (SCRIPTS_DIR, STUDIO_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from catalogue import catalogue_lookup_refresh as lookup_refresh  # noqa: E402
from catalogue import catalogue_write_service  # noqa: E402
from catalogue.catalogue_revisions import CatalogueRevisionConflict  # noqa: E402
from catalogue.catalogue_build_media import PIPELINE_CONFIG  # noqa: E402
from catalogue.catalogue_lookup import (  # noqa: E402
    DEFAULT_LOOKUP_DIR,
    build_series_lookup_payload,
    build_series_search_payload,
    build_work_detail_lookup_payload,
    build_work_lookup_payload,
    build_work_search_payload,
)
from catalogue.catalogue_media_files import IMAGE_EXTENSIONS  # noqa: E402
from catalogue.catalogue_source import (  # noqa: E402
    DEFAULT_SOURCE_DIR,
    SOURCE_FILES,
    load_json_file,
    normalize_text,
    normalize_detail_uid_value,
    records_from_json_source,
    slug_id,
)
from catalogue_work_media_sources import (  # noqa: E402
    WorkMediaSourceRoot,
    resolve_work_media_path,
    resolve_work_media_source_id,
    resolve_work_media_source_root,
)
from pipeline_config import default_work_media_source_id, work_media_source_ids  # noqa: E402
from catalogue.series_ids import normalize_series_id  # noqa: E402
from local_env import runtime_env  # noqa: E402
from script_logging import append_script_log  # noqa: E402


LOGS_REL_DIR = Path("var/studio/catalogue/logs")
CATALOGUE_READ_KEYS = {
    "catalogue_works",
    "catalogue_series",
    "catalogue_lookup_work_search",
    "catalogue_lookup_series_search",
    "catalogue_lookup_series_base",
    "catalogue_work_record",
    "catalogue_work_detail_record",
}

def catalogue_get_payload(repo_root: Path, api_path: str, query: Mapping[str, list[str]] | None = None) -> dict[str, Any]:
    if api_path == "/health":
        return {
            "ok": True,
            "service": "studio_catalogue",
            "routes": [
                "read",
                "bulk-save",
                "delete-preview",
                "delete-apply",
                "work/create",
                "work/save",
                "series/create",
                "series/save",
                "project-media",
            ],
        }
    if api_path == "/project-media":
        return project_media_payload(repo_root, query or {})
    if api_path == "/read":
        return catalogue_read_payload(repo_root, query or {})
    raise FileNotFoundError(f"Unknown catalogue API route: {api_path}")


def catalogue_post_response(
    repo_root: Path,
    api_path: str,
    body: dict[str, Any],
    *,
    dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, Any]]:
    if api_path in catalogue_write_service.SERVICE_POST_PATHS:
        try:
            return catalogue_write_service.handle_catalogue_post(repo_root, api_path, body, dry_run=dry_run)
        except CatalogueRevisionConflict as exc:
            return HTTPStatus.CONFLICT, {"ok": False, "error": str(exc)}
    raise FileNotFoundError(f"Unknown catalogue API route: {api_path}")


def catalogue_read_payload(repo_root: Path, query: Mapping[str, list[str]]) -> dict[str, Any]:
    key = str((query.get("key") or [""])[0] or "").strip()
    record_id = str((query.get("record_id") or [""])[0] or "").strip()
    if key not in CATALOGUE_READ_KEYS:
        raise ValueError(f"unsupported catalogue read key: {key}")

    paths = catalogue_paths(repo_root)
    if key == "catalogue_works":
        return load_source_payload(paths["works_path"], "works")
    if key == "catalogue_series":
        return load_source_payload(paths["series_path"], "series")

    source_records = records_from_json_source(paths["source_dir"])
    if key == "catalogue_lookup_work_search":
        return build_work_search_payload(source_records)
    if key == "catalogue_lookup_series_search":
        return build_series_search_payload(source_records)
    if key == "catalogue_work_record":
        work_id = slug_id(record_id)
        if not work_id:
            raise ValueError("record_id is required for work lookup reads")
        return build_work_lookup_payload(source_records, work_id)
    if key == "catalogue_work_detail_record":
        detail_uid = normalize_detail_uid_value(record_id)
        if not detail_uid:
            raise ValueError("record_id is required for work detail lookup reads")
        return build_work_detail_lookup_payload(source_records, detail_uid)
    if key == "catalogue_lookup_series_base":
        series_id = normalize_series_id(record_id)
        if not series_id:
            raise ValueError("record_id is required for series lookup reads")
        return build_series_lookup_payload(source_records, series_id)
    raise ValueError(f"unsupported catalogue read key: {key}")


def project_media_payload(repo_root: Path, query: Mapping[str, list[str]]) -> dict[str, Any]:
    mode = str((query.get("mode") or ["folders"])[0] or "folders").strip().lower()
    if mode == "sources":
        return {
            "ok": True,
            "mode": mode,
            "default_media_source_id": default_work_media_source_id(PIPELINE_CONFIG),
            "media_source_ids": list(work_media_source_ids(PIPELINE_CONFIG)),
        }
    media_source_id = resolve_work_media_source_id(
        PIPELINE_CONFIG,
        str((query.get("media_source_id") or [""])[0] or ""),
    )
    source_root = resolve_work_media_source_root(
        PIPELINE_CONFIG,
        media_source_id,
        environ=runtime_env(repo_root=repo_root),
        require_exists=True,
    )
    if mode == "folders":
        return {
            "ok": True,
            "mode": mode,
            "media_source_id": media_source_id,
            "project_folders": project_media_folder_records(source_root.root, query_text(query)),
        }
    if mode == "files":
        project_folder = normalize_project_media_segment(
            str((query.get("project_folder") or [""])[0] or ""),
            field="project_folder",
            required=True,
        )
        project_subfolder = normalize_project_media_segment(
            str((query.get("project_subfolder") or [""])[0] or ""),
            field="project_subfolder",
            required=False,
        )
        folder_path = resolve_project_media_folder(source_root, project_folder, project_subfolder)
        return {
            "ok": True,
            "mode": mode,
            "media_source_id": media_source_id,
            "project_folder": project_folder,
            "project_subfolder": project_subfolder,
            "subfolders": project_media_subfolder_records(
                resolve_project_media_folder(source_root, project_folder)
            ),
            "files": project_media_file_records(folder_path, query_text(query)),
        }
    raise ValueError("project-media mode must be sources, folders or files")


def query_text(query: Mapping[str, list[str]]) -> str:
    return str((query.get("q") or [""])[0] or "").strip().lower()


def normalize_project_media_segment(value: str, *, field: str, required: bool) -> str:
    text = normalize_text(value)
    if not text:
        if required:
            raise ValueError(f"{field} is required")
        return ""
    path = Path(text)
    if path.is_absolute() or len(path.parts) != 1:
        raise ValueError(f"{field} must be a single path segment")
    part = path.parts[0]
    if part in {"", ".", ".."} or part.startswith("."):
        raise ValueError(f"{field} must be a visible folder name")
    return part


def resolve_project_media_folder(
    source_root: WorkMediaSourceRoot,
    project_folder: str,
    project_subfolder: str = "",
) -> Path:
    folder = resolve_work_media_path(
        source_root,
        project_folder,
        project_subfolder,
        require_exists=True,
    )
    if not folder.is_dir():
        raise ValueError("project media folder does not exist")
    return folder


def visible_dir(path: Path) -> bool:
    try:
        return stat.S_ISDIR(path.lstat().st_mode) and not path.name.startswith(".")
    except OSError:
        return False


def visible_image_file(path: Path) -> bool:
    try:
        is_file = stat.S_ISREG(path.lstat().st_mode)
    except OSError:
        return False
    return is_file and not path.name.startswith(".") and path.suffix.lower() in IMAGE_EXTENSIONS


def project_media_folder_records(source_root: Path, query: str) -> list[dict[str, Any]]:
    records = []
    for child in sorted(source_root.iterdir(), key=lambda item: item.name.lower()):
        if not visible_dir(child):
            continue
        if query and not child.name.lower().startswith(query):
            continue
        records.append({"project_folder": child.name})
    return records


def project_media_subfolder_records(project_folder_path: Path) -> list[dict[str, Any]]:
    if not project_folder_path.is_dir():
        raise ValueError("project_folder does not exist")
    return [
        {"project_subfolder": child.name}
        for child in sorted(project_folder_path.iterdir(), key=lambda item: item.name.lower())
        if visible_dir(child)
    ]


def project_media_file_records(folder_path: Path, query: str) -> list[dict[str, Any]]:
    records = []
    for child in sorted(folder_path.iterdir(), key=lambda item: item.name.lower()):
        if not visible_image_file(child):
            continue
        if query and query not in child.name.lower():
            continue
        records.append({"filename": child.name})
    return records


def catalogue_paths(repo_root: Path) -> dict[str, Any]:
    source_dir = (repo_root / DEFAULT_SOURCE_DIR).resolve()
    lookup_dir = (repo_root / DEFAULT_LOOKUP_DIR).resolve()
    works_path = (source_dir / SOURCE_FILES["works"]).resolve()
    series_path = (source_dir / SOURCE_FILES["series"]).resolve()
    return {
        "source_dir": source_dir,
        "lookup_dir": lookup_dir,
        "works_path": works_path,
        "series_path": series_path,
    }


def load_source_payload(path: Path, object_key: str) -> dict[str, Any]:
    payload = load_json_file(path)
    if not isinstance(payload.get(object_key), dict):
        raise ValueError(f"{object_key} source file must include a {object_key} object")
    return payload


def refresh_lookup_payloads(repo_root: Path, source_dir: Path, lookup_dir: Path) -> dict[str, Any]:
    result = lookup_refresh.full_lookup_refresh(source_dir, lookup_dir, repo_root)
    log_event(
        repo_root,
        "catalogue_lookup_refresh",
        {
            "lookup_dir": rel_path(repo_root, lookup_dir),
            "mode": result["mode"],
            "artifacts": result["artifacts"],
            "written_count": result["written_count"],
        },
    )
    return result


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return path.name


def log_event(repo_root: Path, event: str, details: dict[str, Any]) -> None:
    append_script_log(
        Path(__file__),
        event=event,
        details=details,
        repo_root=repo_root,
        log_dir_rel=LOGS_REL_DIR,
    )
