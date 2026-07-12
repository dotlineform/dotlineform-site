#!/usr/bin/env python3
"""Preview dispatcher for Docs staged source imports."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
if str(SHARED_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON_DIR))

from markdown_renderer import markdown_renderer_contract, render_markdown_document  # noqa: E402

from docs_import_common import (  # noqa: E402
    FILE_MEDIA_STAGED_SUFFIXES,
    HTML_STAGED_SUFFIXES,
    MARKDOWN_HEADING_PATTERN,
    MARKDOWN_IMAGE_PATTERN,
    MARKDOWN_LINK_PATTERN,
    MARKDOWN_STAGED_SUFFIXES,
    PLAIN_URL_PATTERN,
    RASTER_IMAGE_STAGED_SUFFIXES,
    SOURCE_IMPORTER_BY_SUFFIX,
    SVG_STAGED_SUFFIXES,
    SUPPORTED_STAGED_SUFFIXES,
    TEXT_STAGED_SUFFIXES,
    autolink_plain_urls,
    fence_code,
    humanize,
    is_interactive_html_import_asset,
    normalize_scope,
    normalize_space,
    relative_path,
    slugify,
    source_format_for_path,
)
from docs_import_html_parser import (  # noqa: E402
    build_summary,
)
from docs_import_content import CONTENT_INTENT_REPLACE, ImportContent  # noqa: E402
from docs_html_markdown import (  # noqa: E402
    extract_html_title,
    parse_html_document,
    sanitize_svg_source,
)
from docs_import_markdown_package import (  # noqa: E402
    find_package_markdown_file,
    normalize_apple_notes_caption_spans,
    rewrite_markdown_package_media_links,
)
from docs_import_media import (  # noqa: E402
    apply_inline_raster_media_plans,
    build_file_media_summary,
    build_image_summary,
)
from services.paths import configured_workspace_paths, marker_path  # noqa: E402


def import_artifact_path(repo_root: Path, path: Path, workspace_root: Path) -> str:
    resolved = path.resolve()
    if resolved.is_relative_to(workspace_root.resolve()):
        return marker_path(resolved, workspace_root=workspace_root)
    return relative_path(repo_root, resolved)

def validate_markdown_preview(markdown: str, *, title: str = "") -> dict[str, Any]:
    try:
        rendered = render_markdown_document(markdown, title=title)
    except Exception as exc:
        raise RuntimeError(f"Python Markdown validation failed: {exc}") from exc

    contract = markdown_renderer_contract()
    return {
        "ok": True,
        "html_chars": len(rendered.html),
        "text_chars": len(rendered.plain_text),
        "renderer": "studio/shared/python/markdown_renderer.py",
        "renderer_contract": contract,
        "sanitizer_boundary": {
            "import_html": "docs_html_markdown structured conversion and SVG serialization",
            "raw_markdown_html": "allowed by renderer contract; authored Markdown remains trusted input",
            "sanitizes_html": False,
        },
    }


def resolve_staged_html(staging_root: Path, staged_filename: str) -> Path:
    return resolve_staged_import_source(staging_root, staged_filename, allowed_suffixes=HTML_STAGED_SUFFIXES)


def resolve_staged_import_source(
    staging_root: Path,
    staged_filename: str,
    *,
    allowed_suffixes: set[str] | None = None,
) -> Path:
    filename = str(staged_filename or "").strip()
    if not filename:
        raise ValueError("staged_filename is required")
    staging_root = staging_root.resolve()
    unresolved_path = staging_root / filename
    if unresolved_path.is_symlink():
        raise ValueError("staged import sources must not be symlinks")
    path = unresolved_path.resolve()
    if staging_root not in [path, *path.parents]:
        raise ValueError("staged file must resolve inside the configured import staging root")
    if not path.exists():
        raise FileNotFoundError(f"staged import source does not exist: {filename}")
    if path.is_dir():
        if allowed_suffixes is not None:
            raise ValueError("staged file must use one of these extensions: " + ", ".join(sorted(allowed_suffixes)))
        if path.parent != staging_root:
            raise ValueError("staged Markdown packages must be direct child directories of the configured import staging root")
        if path.is_symlink():
            raise ValueError("staged Markdown packages must not be symlinks")
        if any(candidate.is_symlink() for candidate in path.rglob("*")):
            raise ValueError("staged Markdown packages must not contain symlinks")
        return path
    if path.parent != staging_root:
        raise ValueError("staged import files must be direct children of the configured import staging root")
    suffixes = allowed_suffixes or SUPPORTED_STAGED_SUFFIXES
    if path.suffix.lower() not in suffixes:
        raise ValueError("staged file must use one of these extensions: " + ", ".join(sorted(suffixes)))
    return path


def list_staged_html_files(staging_root: Path, workspace_root: Path) -> list[dict[str, Any]]:
    return [
        file
        for file in list_staged_import_source_files(staging_root, workspace_root)
        if file.get("source_format") == "html"
    ]


def list_staged_import_source_files(
    staging_root: Path,
    workspace_root: Path,
    *,
    registered_source_formats: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    staging_root = staging_root.resolve()
    if not staging_root.exists():
        return []
    files: list[dict[str, Any]] = []
    candidates = [
        path
        for path in staging_root.iterdir()
        if path.is_file() and not path.is_symlink() and path.suffix.lower() in SUPPORTED_STAGED_SUFFIXES
    ]
    package_candidates = [
        path
        for path in staging_root.iterdir()
        if path.is_dir()
        and not path.is_symlink()
        and not any(candidate.is_symlink() for candidate in path.rglob("*"))
    ]
    for path in sorted(candidates, key=lambda candidate: candidate.name.lower()):
        if is_interactive_html_import_asset(path):
            continue
        stat = path.stat()
        files.append(
            {
                "filename": path.name,
                "path": marker_path(path, workspace_root=workspace_root),
                "source_format": (registered_source_formats or {}).get(path.name) or source_format_for_path(path),
                "size_bytes": stat.st_size,
                "modified_utc": dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
    for path in sorted(package_candidates, key=lambda candidate: candidate.name.lower()):
        markdown_files = [
            file
            for file in path.rglob("*")
            if file.is_file() and file.suffix.lower() in MARKDOWN_STAGED_SUFFIXES
        ]
        if not markdown_files:
            continue
        package_files = [file for file in path.rglob("*") if file.is_file()]
        modified = max((file.stat().st_mtime for file in package_files), default=path.stat().st_mtime)
        files.append(
            {
                "filename": path.name,
                "path": marker_path(path, workspace_root=workspace_root),
                "source_format": "markdown_package",
                "size_bytes": sum(file.stat().st_size for file in package_files),
                "modified_utc": dt.datetime.fromtimestamp(modified, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "package_file_count": len(package_files),
                "package_markdown_count": len(markdown_files),
            }
        )
    return files


def generate_import_preview(
    repo_root: Path,
    *,
    staging_root: Path,
    workspace_root: Path,
    source_path: Path,
    scope: str,
    include_prompt_meta: bool,
) -> dict[str, Any]:
    source_format = source_format_for_path(source_path)
    if source_format == "markdown_package":
        return generate_markdown_package_import_preview(
            repo_root,
            staging_root=staging_root,
            workspace_root=workspace_root,
            package_path=source_path,
            scope=scope,
        )
    if source_format == "markdown":
        return generate_markdown_import_preview(
            repo_root,
            staging_root=staging_root,
            workspace_root=workspace_root,
            source_path=source_path,
            scope=scope,
        )
    if source_format == "text":
        return generate_text_import_preview(
            repo_root,
            staging_root=staging_root,
            workspace_root=workspace_root,
            source_path=source_path,
            scope=scope,
        )
    if source_format == "svg":
        return generate_svg_import_preview(
            repo_root,
            workspace_root=workspace_root,
            source_path=source_path,
            scope=scope,
        )
    if source_format == "image":
        return generate_image_import_preview(
            repo_root,
            workspace_root=workspace_root,
            source_path=source_path,
            scope=scope,
        )
    if source_format == "file":
        return generate_file_media_import_preview(
            repo_root,
            workspace_root=workspace_root,
            source_path=source_path,
            scope=scope,
        )
    return generate_html_import_preview(
        repo_root,
        staging_root=staging_root,
        workspace_root=workspace_root,
        source_path=source_path,
        scope=scope,
        include_prompt_meta=include_prompt_meta,
    )


def generate_html_import_preview(
    repo_root: Path,
    *,
    staging_root: Path,
    workspace_root: Path,
    source_path: Path,
    scope: str,
    include_prompt_meta: bool,
) -> dict[str, Any]:
    source_html = source_path.read_text(encoding="utf-8", errors="replace")
    summary = generate_html_content_import_preview(
        source_html=source_html,
        source_identity=source_path.stem,
        scope=scope,
        include_prompt_meta=include_prompt_meta,
        staging_root=staging_root,
        workspace_root=workspace_root,
    )
    summary["source_path"] = import_artifact_path(repo_root, source_path, workspace_root)
    summary["source_html"] = summary["source_path"]
    return summary


def apply_content_identity_hints(
    summary: dict[str, Any],
    *,
    title: str = "",
    doc_id: str = "",
) -> None:
    normalized_title = normalize_space(title)
    normalized_doc_id = str(doc_id or "").strip()
    if normalized_title:
        summary["title"] = normalized_title
        summary["title_source"] = "record"
    if normalized_doc_id:
        summary["proposed_doc_id"] = normalized_doc_id
        summary["proposed_doc_id_source"] = "record"


def generate_html_content_import_preview(
    *,
    source_html: str,
    source_identity: str,
    scope: str,
    include_prompt_meta: bool,
    staging_root: Path,
    workspace_root: Path,
    title: str = "",
    doc_id: str = "",
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    parsed = parse_html_document(source_html)
    parsed_title = extract_html_title(parsed.root)
    summary = build_summary(
        parsed.root,
        source_html=source_html,
        source_filename_stem=source_identity,
        title=parsed_title,
        include_prompt_meta=include_prompt_meta,
        parsed=parsed,
    )
    apply_content_identity_hints(summary, title=title, doc_id=doc_id)
    summary["scope"] = normalized_scope
    summary["source_format"] = "html"
    summary["staging_root"] = marker_path(staging_root, workspace_root=workspace_root)
    summary["tag_counts"] = dict(parsed.tag_counts.most_common())
    summary["comment_count"] = parsed.comment_count
    apply_inline_raster_media_plans(staging_root, workspace_root, summary, normalized_scope)
    summary["markdown_validation"] = validate_markdown_preview(summary["markdown_preview"], title=summary["title"])
    return summary


def extract_markdown_title(markdown: str, fallback: str) -> tuple[str, str]:
    match = MARKDOWN_HEADING_PATTERN.search(markdown or "")
    if match:
        title = normalize_space(re.sub(r"\s+#*$", "", match.group(1)))
        if title:
            return title, "h1"
    return humanize(fallback) or "Imported Doc", "filename"


def build_markdown_summary(source_markdown: str, source_filename_stem: str) -> dict[str, Any]:
    markdown = (source_markdown or "").lstrip("\ufeff").strip()
    title, title_source = extract_markdown_title(markdown, source_filename_stem)
    warnings: list[str] = []
    if not markdown:
        markdown = f"# {title}"
        warnings.append("Staged Markdown was blank; generated a title-only body.")
    link_matches = MARKDOWN_LINK_PATTERN.findall(markdown)
    image_matches = MARKDOWN_IMAGE_PATTERN.findall(markdown)
    plain_url_text = MARKDOWN_IMAGE_PATTERN.sub("", MARKDOWN_LINK_PATTERN.sub("", markdown))
    return {
        "title": title,
        "title_source": title_source,
        "proposed_doc_id": slugify(source_filename_stem or title or "Imported Doc"),
        "proposed_doc_id_source": "filename" if source_filename_stem else "title",
        "source_stats": {
            "chars": len(source_markdown or ""),
            "links": len(link_matches) + len(PLAIN_URL_PATTERN.findall(plain_url_text)),
            "images": len(image_matches),
            "svg": markdown.lower().count("<svg"),
            "details": markdown.lower().count("<details"),
        },
        "image_summary": {
            "external": sum(1 for src in image_matches if src.startswith("http://") or src.startswith("https://")),
            "data_urls": sum(1 for src in image_matches if src.startswith("data:")),
            "repo_local_or_other": sum(1 for src in image_matches if not (src.startswith("http://") or src.startswith("https://") or src.startswith("data:"))),
        },
        "warnings": warnings,
        "markdown_preview": markdown,
    }

def build_text_summary(source_text: str, source_filename_stem: str) -> dict[str, Any]:
    text = (source_text or "").lstrip("\ufeff")
    first_line = next((normalize_space(line) for line in text.splitlines() if normalize_space(line)), "")
    title = first_line if 0 < len(first_line) <= 90 else humanize(source_filename_stem)
    title = title or "Imported Text"
    body = autolink_plain_urls(text.strip())
    warnings: list[str] = []
    if not body:
        body = f"# {title}"
        warnings.append("Staged text was blank; generated a title-only body.")
    return {
        "title": title,
        "title_source": "first_line" if first_line and title == first_line else "filename",
        "proposed_doc_id": slugify(source_filename_stem or title or "Imported Text"),
        "proposed_doc_id_source": "filename" if source_filename_stem else "title",
        "source_stats": {
            "chars": len(source_text or ""),
            "links": len(PLAIN_URL_PATTERN.findall(source_text or "")),
            "images": 0,
            "svg": 0,
            "details": 0,
        },
        "image_summary": {
            "external": 0,
            "data_urls": 0,
            "repo_local_or_other": 0,
        },
        "warnings": warnings,
        "markdown_preview": body,
    }

def generate_markdown_import_preview(
    repo_root: Path,
    *,
    staging_root: Path,
    workspace_root: Path,
    source_path: Path,
    scope: str,
) -> dict[str, Any]:
    source_markdown = source_path.read_text(encoding="utf-8", errors="replace")
    summary = generate_markdown_content_import_preview(
        source_markdown=source_markdown,
        source_identity=source_path.stem,
        scope=scope,
        staging_root=staging_root,
        workspace_root=workspace_root,
    )
    summary["source_path"] = import_artifact_path(repo_root, source_path, workspace_root)
    summary["source_markdown"] = summary["source_path"]
    return summary


def generate_markdown_content_import_preview(
    *,
    source_markdown: str,
    source_identity: str,
    scope: str,
    staging_root: Path,
    workspace_root: Path,
    title: str = "",
    doc_id: str = "",
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    summary = build_markdown_summary(source_markdown, source_identity)
    apply_content_identity_hints(summary, title=title, doc_id=doc_id)
    summary["scope"] = normalized_scope
    summary["source_format"] = "markdown"
    summary["staging_root"] = marker_path(staging_root, workspace_root=workspace_root)
    summary["tag_counts"] = {}
    summary["comment_count"] = 0
    apply_inline_raster_media_plans(staging_root, workspace_root, summary, normalized_scope)
    summary["markdown_validation"] = validate_markdown_preview(summary["markdown_preview"], title=summary["title"])
    return summary


def generate_markdown_package_import_preview(
    repo_root: Path,
    *,
    staging_root: Path,
    workspace_root: Path,
    package_path: Path,
    scope: str,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    package_root = package_path.resolve()
    markdown_path = find_package_markdown_file(package_root)
    source_markdown = markdown_path.read_text(encoding="utf-8", errors="replace")
    package_markdown = normalize_apple_notes_caption_spans(source_markdown)
    summary = build_markdown_summary(package_markdown, package_path.name)
    summary["scope"] = normalized_scope
    summary["source_format"] = "markdown_package"
    summary["source_path"] = marker_path(package_root, workspace_root=workspace_root)
    summary["source_markdown"] = marker_path(markdown_path, workspace_root=workspace_root)
    summary["package_path"] = summary["source_path"]
    summary["package_markdown_path"] = markdown_path.relative_to(package_root).as_posix()
    summary["staging_root"] = marker_path(staging_root, workspace_root=workspace_root)
    summary["tag_counts"] = {}
    summary["comment_count"] = 0
    rewrite_markdown_package_media_links(
        repo_root,
        staging_root=staging_root,
        workspace_root=workspace_root,
        package_root=package_root,
        markdown_path=markdown_path,
        summary=summary,
        scope=normalized_scope,
    )
    apply_inline_raster_media_plans(staging_root, workspace_root, summary, normalized_scope)
    summary["markdown_validation"] = validate_markdown_preview(summary["markdown_preview"], title=summary["title"])
    return summary


def generate_text_import_preview(
    repo_root: Path,
    *,
    staging_root: Path,
    workspace_root: Path,
    source_path: Path,
    scope: str,
) -> dict[str, Any]:
    source_text = source_path.read_text(encoding="utf-8", errors="replace")
    summary = generate_plain_text_content_import_preview(
        source_text=source_text,
        source_identity=source_path.stem,
        scope=scope,
        staging_root=staging_root,
        workspace_root=workspace_root,
    )
    summary["source_path"] = import_artifact_path(repo_root, source_path, workspace_root)
    summary["source_text"] = summary["source_path"]
    return summary


def generate_plain_text_content_import_preview(
    *,
    source_text: str,
    source_identity: str,
    scope: str,
    staging_root: Path,
    workspace_root: Path,
    title: str = "",
    doc_id: str = "",
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    summary = build_text_summary(source_text, source_identity)
    apply_content_identity_hints(summary, title=title, doc_id=doc_id)
    summary["scope"] = normalized_scope
    summary["source_format"] = "text"
    summary["staging_root"] = marker_path(staging_root, workspace_root=workspace_root)
    summary["tag_counts"] = {}
    summary["comment_count"] = 0
    summary["markdown_validation"] = validate_markdown_preview(summary["markdown_preview"], title=summary["title"])
    return summary


def generate_content_import_preview(
    *,
    content: str,
    content_format: str,
    source_identity: str,
    scope: str,
    staging_root: Path,
    workspace_root: Path,
    title: str = "",
    doc_id: str = "",
) -> dict[str, Any]:
    if content_format == "markdown":
        return generate_markdown_content_import_preview(
            source_markdown=content,
            source_identity=source_identity,
            scope=scope,
            staging_root=staging_root,
            workspace_root=workspace_root,
            title=title,
            doc_id=doc_id,
        )
    if content_format == "html":
        return generate_html_content_import_preview(
            source_html=content,
            source_identity=source_identity,
            scope=scope,
            include_prompt_meta=False,
            staging_root=staging_root,
            workspace_root=workspace_root,
            title=title,
            doc_id=doc_id,
        )
    if content_format == "plain_text":
        return generate_plain_text_content_import_preview(
            source_text=content,
            source_identity=source_identity,
            scope=scope,
            staging_root=staging_root,
            workspace_root=workspace_root,
            title=title,
            doc_id=doc_id,
        )
    raise ValueError("content_format must be one of: html, markdown, plain_text")


def generate_normalized_import_content_preview(
    record: ImportContent,
    *,
    scope: str,
    staging_root: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    if record.content_intent != CONTENT_INTENT_REPLACE or not isinstance(record.content, str):
        raise ValueError("only replace ImportContent records have body content to preview")
    return generate_content_import_preview(
        content=record.content,
        content_format=record.content_format,
        source_identity=record.record_identity,
        scope=scope,
        staging_root=staging_root,
        workspace_root=workspace_root,
        title=record.title,
        doc_id=record.doc_id,
    )


def generate_svg_import_preview(
    repo_root: Path,
    *,
    workspace_root: Path,
    source_path: Path,
    scope: str,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    source_svg = source_path.read_text(encoding="utf-8", errors="replace")
    sanitized_svg, svg_title, warnings, svg_count = sanitize_svg_source(source_svg)
    title = svg_title or humanize(source_path.stem) or "Imported Diagram"
    markdown = f"# {title}\n\n{sanitized_svg}".strip()
    summary = {
        "title": title,
        "title_source": "svg_title" if svg_title else "filename",
        "proposed_doc_id": slugify(source_path.stem or title),
        "proposed_doc_id_source": "filename",
        "source_stats": {
            "chars": len(source_svg),
            "links": len(PLAIN_URL_PATTERN.findall(source_svg)),
            "images": source_svg.lower().count("<image"),
            "svg": svg_count,
            "details": 0,
        },
        "image_summary": {
            "external": 0,
            "data_urls": 0,
            "repo_local_or_other": 0,
        },
        "warnings": warnings,
        "markdown_preview": markdown,
        "scope": normalized_scope,
        "source_format": "svg",
        "source_path": import_artifact_path(repo_root, source_path, workspace_root),
        "source_svg": import_artifact_path(repo_root, source_path, workspace_root),
        "staging_root": marker_path(source_path.parent, workspace_root=workspace_root),
        "tag_counts": {"svg": svg_count} if svg_count else {},
        "comment_count": 0,
    }
    summary["markdown_validation"] = validate_markdown_preview(summary["markdown_preview"], title=summary["title"])
    return summary


def generate_image_import_preview(
    repo_root: Path,
    *,
    workspace_root: Path,
    source_path: Path,
    scope: str,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    summary = build_image_summary(source_path, normalized_scope)
    summary["scope"] = normalized_scope
    summary["source_format"] = "image"
    summary["source_path"] = import_artifact_path(repo_root, source_path, workspace_root)
    summary["source_media"] = summary["source_path"]
    summary["staging_root"] = marker_path(source_path.parent, workspace_root=workspace_root)
    summary["tag_counts"] = {}
    summary["comment_count"] = 0
    summary["markdown_validation"] = validate_markdown_preview(summary["markdown_preview"], title=summary["title"])
    return summary


def generate_file_media_import_preview(
    repo_root: Path,
    *,
    workspace_root: Path,
    source_path: Path,
    scope: str,
) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)
    summary = build_file_media_summary(source_path, normalized_scope)
    summary["scope"] = normalized_scope
    summary["source_format"] = "file"
    summary["source_path"] = import_artifact_path(repo_root, source_path, workspace_root)
    summary["source_media"] = summary["source_path"]
    summary["staging_root"] = marker_path(source_path.parent, workspace_root=workspace_root)
    summary["tag_counts"] = {}
    summary["comment_count"] = 0
    summary["markdown_validation"] = validate_markdown_preview(summary["markdown_preview"], title=summary["title"])
    return summary


def detect_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        root = Path(explicit_root).expanduser().resolve()
        if not (root / "site-tools" / "config" / "site-tools.json").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing site-tools/config/site-tools.json): {root}")
        return root
    for candidate in [Path.cwd(), Path(__file__).resolve().parent]:
        current = candidate.resolve()
        for parent in [current, *current.parents]:
            if (parent / "site-tools" / "config" / "site-tools.json").exists():
                return parent
    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def resolve_import_source(repo_root: Path, args: argparse.Namespace) -> Path:
    if args.source_html:
        path = Path(args.source_html).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"Source HTML does not exist: {path}")
        return path
    if args.staged_filename:
        try:
            return resolve_staged_import_source(configured_workspace_paths(repo_root).import_staging, args.staged_filename)
        except (FileNotFoundError, ValueError) as exc:
            raise SystemExit(str(exc)) from exc
    raise SystemExit("Pass either --source-html or --staged-filename.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run source import conversion for Docs Viewer source docs.")
    parser.add_argument("--repo-root", default="", help="Override repo root auto-detection.")
    parser.add_argument("--source-html", default="", help="Import directly from an HTML file path.")
    parser.add_argument("--staged-filename", default="", help="Import from the configured shared import staging root.")
    parser.add_argument("--scope", default="studio", choices=sorted(SCOPE_ROOTS.keys()), help="Target docs scope.")
    parser.add_argument("--include-prompt-meta", action="store_true", help="Include clearly identifiable prompt/meta blocks.")
    parser.add_argument("--markdown-preview-out", default="", help="Optional path to write the Markdown preview.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = detect_repo_root(args.repo_root)
    workspace_paths = configured_workspace_paths(repo_root)
    source_path = resolve_import_source(repo_root, args)
    summary = generate_import_preview(
        repo_root,
        staging_root=workspace_paths.import_staging,
        workspace_root=workspace_paths.root,
        source_path=source_path,
        scope=args.scope,
        include_prompt_meta=bool(args.include_prompt_meta),
    )

    if args.markdown_preview_out:
        output_path = Path(args.markdown_preview_out).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary["markdown_preview"] + "\n", encoding="utf-8")
        summary["markdown_preview_out"] = str(output_path)

    json.dump(summary, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
