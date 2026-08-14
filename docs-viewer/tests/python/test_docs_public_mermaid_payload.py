#!/usr/bin/env python3
"""Focused public-only Mermaid payload assembly checks."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

from markdown_it import MarkdownIt
import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from docs_publish_gate import publishable_docs_files  # noqa: E402
from docs_public_mermaid_projection import plan_public_mermaid_projection  # noqa: E402
from docs_svg_sanitizer import sanitize_svg_bytes  # noqa: E402


DOC_ID = "d-20260725-000000-000001"
PREPARED_ROOT = Path(".publish/public-mermaid-projection")


def mermaid_source(*, edge: str = "A --> B") -> str:
    return "\n".join(
        [
            "flowchart LR",
            "  accTitle: Public projection",
            "  accDescr: Canonical source becomes one themed public image.",
            f"  {edge}",
            "",
        ]
    )


def markdown(source: str) -> str:
    return (
        '<img data-docs-viewer-diagram-kind="persistent-svg" '
        'src="/assets/data/docs/scopes/example/media/svg/fixed.svg" alt="Fixed diagram">\n\n'
        f"```mermaid\n{source}```\n"
    )


def svg_bytes(title: str, description: str, *, fill: str) -> bytes:
    return sanitize_svg_bytes(
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80">
<title>{title}</title>
<desc>{description}</desc>
<rect width="30" height="20" fill="{fill}"/>
</svg>"""
    ).bytes


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def prepare_projection(
    working_root: Path,
    *,
    source: str,
    include_dark: bool = True,
) -> dict[str, object]:
    plan = plan_public_mermaid_projection(
        scope="example",
        documents=[(DOC_ID, markdown(source))],
        public_url_prefix="/assets/data/docs/scopes/example",
    )
    record = plan["manifest"]["diagrams"][0]
    write_json(working_root / PREPARED_ROOT / "manifest.json", plan["manifest"])
    colors = {"light": "#ffffff", "dark": "#111111"}
    for theme in ("light", "dark"):
        if theme == "dark" and not include_dark:
            continue
        identity = record["variants"][theme]["artifact_identity"]
        path = working_root / PREPARED_ROOT / identity
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(
            svg_bytes(record["title"], record["description"], fill=colors[theme])
        )
    return plan


def write_payload(working_root: Path, source: str) -> Path:
    payload_path = working_root / f"by-id/{DOC_ID}.json"
    write_json(
        payload_path,
        {
            "title": "Projected document",
            "content_html": MarkdownIt("commonmark").render(markdown(source)),
        },
    )
    return payload_path


def test_public_assembly_replaces_verified_fence_and_preserves_working_payload(
    tmp_path: Path,
) -> None:
    working_root = tmp_path / "working"
    source = mermaid_source()
    payload_path = write_payload(working_root, source)
    ordinary_path = working_root / "by-id/ordinary.json"
    ordinary_path.write_text('{"title":"Ordinary","content_html":"<p>Text</p>"}\n', encoding="utf-8")
    plan = prepare_projection(working_root, source=source)
    working_bytes = payload_path.read_bytes()

    files = publishable_docs_files(
        working_root,
        Path("site/assets/data/docs/scopes/example"),
        projection_scope="example",
    )

    public_payload = json.loads(files[Path(f"by-id/{DOC_ID}.json")])
    content_html = public_payload["content_html"]
    record = plan["manifest"]["diagrams"][0]
    assert payload_path.read_bytes() == working_bytes
    assert files[Path("by-id/ordinary.json")] == ordinary_path.read_bytes()
    assert '<code class="language-mermaid">' not in content_html
    assert "flowchart LR" not in content_html
    assert content_html.count('data-docs-viewer-diagram-kind="themed-mermaid"') == 1
    assert content_html.count('data-docs-viewer-diagram-kind="persistent-svg"') == 1
    assert 'data-docs-viewer-diagram-light-src="' in content_html
    assert 'data-docs-viewer-diagram-dark-src="' in content_html
    assert ' alt="Public projection"' in content_html
    assert ' title="Public projection"' in content_html
    assert "Canonical source becomes one themed public image." in content_html
    assert " hidden " in content_html
    themed_tag = re.search(
        r'<img[^>]+data-docs-viewer-diagram-kind="themed-mermaid"[^>]*>',
        content_html,
    )
    assert themed_tag is not None
    assert " src=" not in themed_tag.group(0)
    assert PREPARED_ROOT / "manifest.json" not in files
    for theme in ("light", "dark"):
        identity = Path(record["variants"][theme]["artifact_identity"])
        assert files[identity] == (
            working_root / PREPARED_ROOT / identity
        ).read_bytes()


def test_public_assembly_blocks_fence_without_complete_prepared_pair(
    tmp_path: Path,
) -> None:
    working_root = tmp_path / "working"
    source = mermaid_source()
    write_payload(working_root, source)

    with pytest.raises(RuntimeError, match="incomplete or stale"):
        publishable_docs_files(
            working_root,
            Path("site/assets/data/docs/scopes/example"),
            projection_scope="example",
        )

    prepare_projection(working_root, source=source, include_dark=False)
    with pytest.raises(FileNotFoundError, match="dark variant not found"):
        publishable_docs_files(
            working_root,
            Path("site/assets/data/docs/scopes/example"),
            projection_scope="example",
        )


def test_public_assembly_rejects_stale_source_and_tampered_variant(
    tmp_path: Path,
) -> None:
    working_root = tmp_path / "working"
    source = mermaid_source()
    plan = prepare_projection(working_root, source=source)
    write_payload(working_root, mermaid_source(edge="A --> C"))

    with pytest.raises(RuntimeError, match="source digest is stale"):
        publishable_docs_files(
            working_root,
            Path("site/assets/data/docs/scopes/example"),
            projection_scope="example",
        )

    write_payload(working_root, source)
    dark_identity = plan["manifest"]["diagrams"][0]["variants"]["dark"]["artifact_identity"]
    (working_root / PREPARED_ROOT / dark_identity).write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">'
        "<script>alert(1)</script><rect width=\"1\" height=\"1\"/></svg>",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="not the verified sanitized bytes"):
        publishable_docs_files(
            working_root,
            Path("site/assets/data/docs/scopes/example"),
            projection_scope="example",
        )
