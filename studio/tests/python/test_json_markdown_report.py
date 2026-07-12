"""Shared deterministic JSON-to-Markdown report tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_PYTHON = REPO_ROOT / "studio/shared/python"
if str(SHARED_PYTHON) not in sys.path:
    sys.path.insert(0, str(SHARED_PYTHON))

from json_markdown_report import (  # noqa: E402
    render_json_markdown_report,
    write_json_markdown_report,
)


def test_render_json_markdown_report_orders_sections_and_escapes_nested_values() -> None:
    payload = {
        "warnings": ["Repair [asset] | later"],
        "package_identity": {"filename": "reviewed_file.jsonl", "count": 2},
        "created": [
            {"doc_id": "alpha", "title": "Alpha *One*"},
            {"doc_id": "beta", "details": ["first", "second"]},
        ],
        "skipped": [],
    }

    markdown = render_json_markdown_report(
        payload,
        title="Import #1",
        section_order=("package_identity", "created", "skipped", "warnings"),
    )

    assert markdown == (
        "# Import \\#1\n\n"
        "## package identity\n\n"
        "- **filename:** reviewed\\_file.jsonl\n"
        "  **count:** 2\n\n"
        "## created\n\n"
        "- **doc id:** alpha\n"
        "  **title:** Alpha \\*One\\*\n"
        "- **doc id:** beta\n"
        "  **details:**\n"
        "  - first\n"
        "  - second\n\n"
        "## skipped\n\n"
        "- []\n\n"
        "## warnings\n\n"
        "- Repair \\[asset\\] \\| later\n"
    )


def test_write_json_markdown_report_replaces_atomically(tmp_path: Path) -> None:
    target = tmp_path / "results" / "report.md"
    target.parent.mkdir(parents=True)
    target.write_text("old\n", encoding="utf-8")

    written = write_json_markdown_report(target, {"status": "complete"}, title="Result")

    assert written == target
    assert target.read_text(encoding="utf-8") == "# Result\n\n## status\n\ncomplete\n"
    assert list(target.parent.glob(".*.tmp")) == []


@pytest.mark.parametrize(
    "payload",
    [
        {1: "non-string key"},
        {"value": float("nan")},
        {"value": ("tuple",)},
    ],
)
def test_render_json_markdown_report_rejects_non_json_values(payload: object) -> None:
    with pytest.raises(ValueError, match="JSON-compatible|keys|non-finite"):
        render_json_markdown_report(payload, title="Invalid")
