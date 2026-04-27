#!/usr/bin/env python3
"""Report source project folders and primary images not represented in works.json."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

try:
    from catalogue_source import DEFAULT_SOURCE_DIR, SOURCE_FILES, normalize_text, records_from_json_source
    from pipeline_config import env_var_name, env_var_value, load_pipeline_config, source_works_root_subdir
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.catalogue_source import DEFAULT_SOURCE_DIR, SOURCE_FILES, normalize_text, records_from_json_source
    from scripts.pipeline_config import env_var_name, env_var_value, load_pipeline_config, source_works_root_subdir


PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
PROJECTS_BASE_DIR_ENV_NAME = env_var_name(PIPELINE_CONFIG, "projects_base_dir")
DEFAULT_OUTPUT_REL_PATH = Path("_docs_src/project-state.md")
IMAGE_EXTENSIONS = {
    ".avif",
    ".gif",
    ".heic",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}
OUT_OF_SCOPE_DIR_NAMES = {"details"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def detect_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    raise ValueError("Could not detect repo root.")


def resolve_projects_base_dir(explicit: str = "", env: Mapping[str, str] | None = None) -> Path:
    raw_value = explicit or env_var_value(PIPELINE_CONFIG, "projects_base_dir", dict(env or os.environ))
    if not raw_value:
        raise ValueError(f"Missing source base dir. Set {PROJECTS_BASE_DIR_ENV_NAME} or pass --projects-base-dir.")
    base_dir = Path(raw_value).expanduser().resolve()
    if not base_dir.exists():
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV_NAME} does not exist: {base_dir}")
    return base_dir


def relative_posix(path: Path) -> str:
    return path.as_posix().strip("/")


def normalize_rel_value(value: Any) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    return relative_posix(Path(text))


def is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def is_image_path(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def iter_candidate_project_dirs(projects_root: Path, detail_dirs: set[str], include_subfolders: bool = False) -> Iterable[Path]:
    if not include_subfolders:
        for child in sorted(projects_root.iterdir(), key=lambda value: value.name.lower()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            rel = relative_posix(child.relative_to(projects_root))
            if is_detail_dir(rel, detail_dirs):
                continue
            if any(is_image_path(grandchild) for grandchild in child.iterdir()):
                yield child
        return

    for current, dirnames, filenames in os.walk(projects_root):
        current_path = Path(current)
        rel = relative_posix(current_path.relative_to(projects_root))
        dirnames[:] = sorted(
            dirname for dirname in dirnames
            if not dirname.startswith(".")
            and not is_detail_dir(relative_posix((current_path / dirname).relative_to(projects_root)), detail_dirs)
        )
        if is_hidden_path(current_path.relative_to(projects_root)):
            continue
        if rel and is_detail_dir(rel, detail_dirs):
            continue
        if any(Path(filename).suffix.lower() in IMAGE_EXTENSIONS for filename in filenames):
            yield current_path


def is_detail_dir(rel_path: str, detail_dirs: set[str]) -> bool:
    parts = Path(rel_path).parts
    if any(part.lower() in OUT_OF_SCOPE_DIR_NAMES for part in parts):
        return True
    return any(rel_path == detail_dir or rel_path.startswith(f"{detail_dir}/") for detail_dir in detail_dirs)


def collect_work_project_references(records: Any) -> tuple[set[str], set[str], Dict[str, list[str]], list[Dict[str, str]]]:
    project_folders: set[str] = set()
    project_images: set[str] = set()
    works_by_image: Dict[str, list[str]] = {}
    incomplete_works: list[Dict[str, str]] = []

    for work_id, record in sorted(records.works.items()):
        folder = normalize_rel_value(record.get("project_folder"))
        filename = normalize_rel_value(record.get("project_filename"))
        if not folder or not filename:
            incomplete_works.append(
                {
                    "work_id": str(work_id),
                    "project_folder": folder,
                    "project_filename": filename,
                }
            )
            continue
        rel_image = relative_posix(Path(folder) / filename)
        project_folders.add(folder)
        project_images.add(rel_image)
        works_by_image.setdefault(rel_image, []).append(str(work_id))

    return project_folders, project_images, works_by_image, incomplete_works


def collect_detail_dirs(records: Any, works_by_id: Mapping[str, Mapping[str, Any]]) -> set[str]:
    detail_dirs: set[str] = set()
    for record in records.work_details.values():
        work_id = normalize_text(record.get("work_id"))
        project_subfolder = normalize_rel_value(record.get("project_subfolder"))
        if not work_id or not project_subfolder:
            continue
        work = works_by_id.get(work_id) or {}
        project_folder = normalize_rel_value(work.get("project_folder"))
        if project_folder:
            detail_dirs.add(relative_posix(Path(project_folder) / project_subfolder))
    return detail_dirs


def collect_source_state(
    projects_root: Path,
    detail_dirs: set[str],
    include_subfolders: bool = False,
) -> tuple[set[str], set[str], Dict[str, list[str]]]:
    source_folders: set[str] = set()
    source_images: set[str] = set()
    images_by_folder: Dict[str, list[str]] = {}

    for folder_path in iter_candidate_project_dirs(projects_root, detail_dirs, include_subfolders=include_subfolders):
        folder_rel = relative_posix(folder_path.relative_to(projects_root))
        if not folder_rel:
            continue
        source_folders.add(folder_rel)
        for child in sorted(folder_path.iterdir(), key=lambda value: value.name.lower()):
            if not is_image_path(child):
                continue
            image_rel = relative_posix(Path(folder_rel) / child.name)
            source_images.add(image_rel)
            images_by_folder.setdefault(folder_rel, []).append(child.name)

    return source_folders, source_images, images_by_folder


def build_project_state_report(
    repo_root: Path,
    projects_base_dir: Path,
    output_path: Path | None = None,
    write: bool = False,
    include_subfolders: bool = False,
) -> Dict[str, Any]:
    repo_root = repo_root.resolve()
    projects_base_dir = projects_base_dir.resolve()
    projects_root = (projects_base_dir / source_works_root_subdir(PIPELINE_CONFIG)).resolve()
    if not projects_root.exists():
        raise ValueError(f"Projects source root does not exist: {projects_root}")

    source_dir = (repo_root / DEFAULT_SOURCE_DIR).resolve()
    records = records_from_json_source(source_dir)
    works_by_id = records.works
    project_folders, project_images, works_by_image, incomplete_works = collect_work_project_references(records)
    detail_dirs = collect_detail_dirs(records, works_by_id)
    source_folders, source_images, images_by_folder = collect_source_state(
        projects_root,
        detail_dirs,
        include_subfolders=include_subfolders,
    )

    unrepresented_folders = sorted(source_folders - project_folders, key=str.lower)
    unrepresented_images = sorted(
        (
            image_rel
            for image_rel in source_images - project_images
            if relative_posix(Path(image_rel).parent) in project_folders
        ),
        key=str.lower,
    )
    unrepresented_folder_image_count = sum(len(images_by_folder.get(folder, [])) for folder in unrepresented_folders)
    catalogue_missing_folders = sorted(project_folders - source_folders, key=str.lower)
    missing_source_images = sorted(project_images - source_images, key=str.lower)

    generated_at_utc = utc_now()
    output = output_path or (repo_root / DEFAULT_OUTPUT_REL_PATH)
    output = output.resolve()
    added_date = existing_added_date(output) or today_iso()
    markdown = render_report_markdown(
        generated_at_utc=generated_at_utc,
        added_date=added_date,
        include_subfolders=include_subfolders,
        source_folders=source_folders,
        project_folders=project_folders,
        source_images=source_images,
        project_images=project_images,
        unrepresented_folders=unrepresented_folders,
        unrepresented_images=unrepresented_images,
        catalogue_missing_folders=catalogue_missing_folders,
        missing_source_images=missing_source_images,
        incomplete_works=incomplete_works,
        images_by_folder=images_by_folder,
        works_by_image=works_by_image,
    )

    if write:
        expected_root = (repo_root / "_docs_src").resolve()
        if output.parent != expected_root:
            raise ValueError("Project-state report writes are restricted to _docs_src/.")
        output.write_text(markdown, encoding="utf-8")

    return {
        "generated_at_utc": generated_at_utc,
        "projects_root_display": f"${PROJECTS_BASE_DIR_ENV_NAME}/{source_works_root_subdir(PIPELINE_CONFIG)}",
        "catalogue_source_path": str((DEFAULT_SOURCE_DIR / SOURCE_FILES["works"]).as_posix()),
        "output_path": str(output.relative_to(repo_root).as_posix()),
        "written": bool(write),
        "include_subfolders": bool(include_subfolders),
        "summary": {
            "include_subfolders": bool(include_subfolders),
            "source_folder_count": len(source_folders),
            "catalogue_project_folder_count": len(project_folders),
            "unrepresented_folder_count": len(unrepresented_folders),
            "source_image_count": len(source_images),
            "catalogue_project_image_count": len(project_images),
            "unrepresented_image_count": len(unrepresented_images),
            "unrepresented_folder_image_count": unrepresented_folder_image_count,
            "catalogue_missing_folder_count": len(catalogue_missing_folders),
            "missing_source_image_count": len(missing_source_images),
            "incomplete_work_count": len(incomplete_works),
            "skipped_detail_folder_count": len(detail_dirs),
        },
        "unrepresented_folders": unrepresented_folders,
        "unrepresented_images": unrepresented_images,
        "catalogue_missing_folders": catalogue_missing_folders,
        "missing_source_images": missing_source_images,
        "incomplete_works": incomplete_works,
        "markdown": markdown,
    }


def render_report_markdown(
    *,
    generated_at_utc: str,
    added_date: str,
    include_subfolders: bool,
    source_folders: set[str],
    project_folders: set[str],
    source_images: set[str],
    project_images: set[str],
    unrepresented_folders: list[str],
    unrepresented_images: list[str],
    catalogue_missing_folders: list[str],
    missing_source_images: list[str],
    incomplete_works: list[Dict[str, str]],
    images_by_folder: Mapping[str, list[str]],
    works_by_image: Mapping[str, list[str]],
) -> str:
    grouped_unrepresented = group_images_by_folder(unrepresented_images)
    scan_scope = "direct source folders and their direct images"
    if include_subfolders:
        scan_scope = "direct source folders, subfolders, and each scanned folder's direct images"
    lines = [
        "---",
        "doc_id: project-state",
        'title: "Project State"',
        f"added_date: {added_date}",
        f"last_updated: {today_iso()}",
        "published: false",
        'parent_id: ""',
        "sort_order: 999",
        "---",
        "# Project State",
        "",
        f"Generated at `{generated_at_utc}`.",
        "",
        "This report compares source image candidates under `$DOTLINEFORM_PROJECTS_BASE_DIR/projects` with primary work image references in `assets/studio/data/catalogue/works.json`.",
        "",
        f"Scan mode: {scan_scope}.",
        "",
        "Work details are intentionally out of scope. Known detail subfolders from `assets/studio/data/catalogue/work_details.json` are skipped so detail images do not appear as unimported primary work images.",
        "",
        "## Summary",
        "",
        f"- include subfolders: {'true' if include_subfolders else 'false'}",
        f"- source folders scanned: {len(source_folders)}",
        f"- catalogue project folders: {len(project_folders)}",
        f"- source folders not in `works.json`: {len(unrepresented_folders)}",
        f"- source images scanned: {len(source_images)}",
        f"- primary work images in `works.json`: {len(project_images)}",
        f"- source images in represented folders but not in `works.json`: {len(unrepresented_images)}",
        f"- top-level source images inside folders not in `works.json`: {sum(len(images_by_folder.get(folder, [])) for folder in unrepresented_folders)}",
        f"- catalogue project folders with no scanned source folder: {len(catalogue_missing_folders)}",
        f"- primary work image references with no scanned source file: {len(missing_source_images)}",
        f"- work records missing `project_folder` or `project_filename`: {len(incomplete_works)}",
        "",
        "## Source Folders Not In Works JSON",
        "",
    ]
    lines.extend(format_folder_list(unrepresented_folders, images_by_folder))
    lines.extend([
        "",
        "## Source Images In Represented Folders But Not In Works JSON",
        "",
    ])
    if grouped_unrepresented:
        for folder in sorted(grouped_unrepresented, key=str.lower):
            lines.append(f"### `{folder}`")
            lines.append("")
            lines.extend(format_bullet_list(grouped_unrepresented[folder]))
            lines.append("")
    else:
        lines.append("None.")
        lines.append("")

    lines.extend([
        "## Catalogue References Missing Source Files",
        "",
    ])
    if missing_source_images:
        for image_rel in missing_source_images:
            work_ids = ", ".join(works_by_image.get(image_rel, []))
            suffix = f" (work {work_ids})" if work_ids else ""
            lines.append(f"- `{image_rel}`{suffix}")
    else:
        lines.append("None.")
    lines.append("")

    lines.extend([
        "## Catalogue Folders Missing From Source Scan",
        "",
    ])
    lines.extend(format_bullet_list(catalogue_missing_folders))
    lines.extend([
        "",
        "## Work Records Missing Source Fields",
        "",
    ])
    if incomplete_works:
        for item in incomplete_works:
            fields = []
            if not item["project_folder"]:
                fields.append("project_folder")
            if not item["project_filename"]:
                fields.append("project_filename")
            lines.append(f"- `{item['work_id']}` missing {', '.join(fields)}")
    else:
        lines.append("None.")
    lines.append("")

    return "\n".join(lines)


def existing_added_date(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("added_date:"):
                return line.split(":", 1)[1].strip().strip('"')
    except OSError:
        return ""
    return ""


def group_images_by_folder(image_paths: Iterable[str]) -> Dict[str, list[str]]:
    grouped: Dict[str, list[str]] = {}
    for image_path in image_paths:
        path = Path(image_path)
        folder = relative_posix(path.parent)
        grouped.setdefault(folder, []).append(path.name)
    return {folder: sorted(names, key=str.lower) for folder, names in grouped.items()}


def format_bullet_list(values: Iterable[str]) -> list[str]:
    values = list(values)
    if not values:
        return ["None."]
    return [f"- `{value}`" for value in values]


def format_folder_list(values: Iterable[str], images_by_folder: Mapping[str, list[str]]) -> list[str]:
    values = list(values)
    if not values:
        return ["None."]
    lines = []
    for value in values:
        count = len(images_by_folder.get(value, []))
        suffix = f" ({count} top-level image{'s' if count != 1 else ''})" if count else ""
        lines.append(f"- `{value}`{suffix}")
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report project source folders/images not represented by works.json.")
    parser.add_argument("--repo-root", default="", help="Repo root path (auto-detected if omitted)")
    parser.add_argument(
        "--projects-base-dir",
        default="",
        help=f"Override {PROJECTS_BASE_DIR_ENV_NAME}; the script scans its projects/ child",
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_REL_PATH), help="Markdown output path for --write")
    parser.add_argument("--write", action="store_true", help="Write the Markdown report instead of previewing only")
    parser.add_argument(
        "--include-subfolders",
        action="store_true",
        help="Include source subfolders under projects/ folders in the report",
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of Markdown")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = detect_repo_root(Path(args.repo_root) if args.repo_root else None)
    projects_base_dir = resolve_projects_base_dir(args.projects_base_dir)
    output_path = (repo_root / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output).resolve()
    result = build_project_state_report(
        repo_root=repo_root,
        projects_base_dir=projects_base_dir,
        output_path=output_path,
        write=bool(args.write),
        include_subfolders=bool(args.include_subfolders),
    )
    if args.json:
        printable = {
            "generated_at_utc": result["generated_at_utc"],
            "output_path": result["output_path"],
            "written": result["written"],
            "summary": result["summary"],
        }
        print(json.dumps(printable, indent=2, ensure_ascii=False))
    else:
        if args.write:
            print(f"Wrote {result['output_path']}")
            print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
        else:
            print(result["markdown"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"project_state_report: {exc}", file=sys.stderr)
        raise SystemExit(1)
