from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_ROOT = REPO_ROOT / "public-site" / "build"
sys.path.insert(0, str(BUILD_ROOT))

from public_site_builder.audit import audit_artifact  # noqa: E402
from public_site_builder.builder import build_site  # noqa: E402
from public_site_builder.config import load_config  # noqa: E402


CONFIG_PATH = REPO_ROOT / "public-site" / "config" / "public-site.json"


def test_build_site_writes_route_artifact(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH)
    destination = tmp_path / "artifact"

    result = build_site(REPO_ROOT, destination, config)
    audit_result = audit_artifact(result.destination, config)

    assert (destination / ".public-site-artifact").is_file()
    assert (destination / ".nojekyll").is_file()
    assert (destination / "CNAME").read_text(encoding="utf-8").strip()
    assert (destination / "series" / "index.html").is_file()
    assert (destination / "works" / "index.html").is_file()
    assert (destination / "library" / "index.html").is_file()
    assert (destination / "assets" / "css" / "main.css").is_file()
    assert (destination / "assets" / "data" / "works_index.json").is_file()
    assert (destination / "assets" / "works" / "index" / "00008.json").is_file()
    assert (destination / "docs-viewer" / "runtime" / "js" / "docs-viewer-public.js").is_file()
    assert not (destination / "docs-viewer" / "runtime" / "js" / "docs-viewer-management.js").exists()
    assert not (destination / "docs-viewer" / "source").exists()
    assert not any(path.name == ".DS_Store" for path in destination.rglob("*"))
    for html_path in destination.rglob("*.html"):
        html = html_path.read_text(encoding="utf-8")
        assert "{{" not in html
        assert "{%" not in html
    assert audit_result.checked_count > len(config.required_files)


def test_build_site_refuses_non_artifact_destination(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH)
    destination = tmp_path / "not-artifact"
    destination.mkdir()
    (destination / "user-file.txt").write_text("keep me\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="refusing to replace non-artifact destination"):
        build_site(REPO_ROOT, destination, config)


def test_audit_rejects_denied_files(tmp_path: Path) -> None:
    config = load_config(CONFIG_PATH)
    destination = tmp_path / "artifact"
    build_site(REPO_ROOT, destination, config)
    (destination / "Gemfile").write_text("source leak\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="artifact contains denied file"):
        audit_artifact(destination, config)
