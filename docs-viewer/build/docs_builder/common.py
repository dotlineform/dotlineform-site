from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
for path in (DOCS_SERVICES_DIR, SHARED_PYTHON_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from docs_scope_config import (  # noqa: E402
    CONFIG_REL_PATH,
    DocsScopeConfig,
    document_source_path,
    is_public_readonly_scope,
    load_docs_scope_configs,
    normalize_viewer_base_url,
    path_is_under_configured_sub_scope_source,
    public_documents_path,
    public_search_path,
    publication_documents_path,
    published_documents_path,
    published_search_path,
    resolve_scope_path,
    scope_uses_external_data,
)
from markdown_renderer import plain_text_from_html, render_markdown_to_html  # noqa: E402


DOCS_VIEWER_BROWSER_CONFIG_PATH = Path("docs-viewer/config/defaults/docs-viewer-config.json")
DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH = Path("docs-viewer/config/defaults/docs-viewer-public-config.json")
SITE_DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH = Path("site/docs-viewer/config/defaults/docs-viewer-public-config.json")
DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION = "docs_viewer_config_v1"
DOCS_INDEX_TREE_SCHEMA_VERSION = "docs_index_tree_v1"
DOCS_RECENT_SCHEMA_VERSION = "docs_recent_v1"
DEFAULT_RECENT_LIMIT = 10
FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
MEDIA_TOKEN_PATTERN = re.compile(r"\[\[media:(.+?)\]\]")
MEDIA_IMAGE_TOKEN_PATTERN = re.compile(r"!\[(?P<alt>(?:\\.|[^\]\\])*)\]\(\s*\[\[media:(?P<body>.+?)\]\]\s*\)")
INTERACTIVE_HTML_TOKEN_PATTERN = re.compile(r"\[\[interactive-html:(.+?)\]\]")
SEMANTIC_REF_TOKEN_PATTERN = re.compile(r"\[\[ref:(.*?)\]\](\{[^}\n]*\})?", re.DOTALL)
INTERACTIVE_HTML_FILENAME_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9._-]*\.html\Z", re.IGNORECASE)
INTERACTIVE_HTML_HEIGHT_PATTERN = re.compile(r"\A[1-9][0-9]{0,3}\Z")
IMG_PATTERN = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)
HTML_ATTR_PATTERN_TEMPLATE = r"\b{}\s*=\s*([\"'])(.*?)\1"
INTEGER_PATTERN = re.compile(r"^-?\d+$")
SAFE_REF_KIND_PATTERN = re.compile(r"\A[a-z0-9_-]+\Z")
MEDIA_TOKEN_ALLOWED_ATTRS = {"width", "height"}
MEDIA_TOKEN_DIMENSION_PATTERN = re.compile(r"\A[1-9][0-9]{0,5}\Z")


def monotonic_time() -> float:
    return time.perf_counter()


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()
def humanize(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[_\-\s]+", value.strip()) if part)


def html_attr(raw_attrs: str, name: str) -> str:
    pattern = re.compile(HTML_ATTR_PATTERN_TEMPLATE.format(re.escape(name)), re.IGNORECASE | re.DOTALL)
    match = pattern.search(raw_attrs or "")
    return match.group(2) if match else ""
def json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def browser_path_for_repo_relative(path: Path) -> str:
    rel = Path(path.as_posix().lstrip("/"))
    if len(rel.parts) >= 2 and rel.parts[0] == "site":
        rel = Path(*rel.parts[1:])
    return f"/{rel.as_posix().lstrip('/')}"


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_site_tools_config(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "site-tools" / "config" / "site-tools.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"site-tools config must be a JSON object: {path}")
    return payload


def normalize_doc_ids(values: list[str] | tuple[str, ...] | None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values or []:
        doc_id = str(value or "").strip()
        if doc_id and doc_id not in seen:
            seen.add(doc_id)
            result.append(doc_id)
    return sorted(result)
