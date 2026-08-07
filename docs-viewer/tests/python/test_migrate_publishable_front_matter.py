from __future__ import annotations

from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "docs-viewer" / "migrations" / "migrate_publishable_front_matter.py"
sys.path.insert(0, str(SCRIPT_PATH.parent))
import migrate_publishable_front_matter as migration  # noqa: E402


def source(field: str, body: str = "viewable: false\n") -> str:
    return f"---\ndoc_id: d-20260807-000000-aaaaaa\n{field}---\n# Body\n\n{body}"


def test_public_false_becomes_publishable_false_without_rewriting_body() -> None:
    result = migration.migrate_source_text(
        source("viewable: false\n"),
        publishable_supported=True,
        source_name="analysis/example.md",
    )

    assert result.changed is True
    assert result.legacy_value is False
    assert "\npublishable: false\n---" in result.text
    assert result.text.endswith("viewable: false\n")


@pytest.mark.parametrize("publishable_supported", [True, False])
def test_true_is_removed_for_public_and_local_collections(
    publishable_supported: bool,
) -> None:
    result = migration.migrate_source_text(
        source("viewable: true\n", body="unchanged\n"),
        publishable_supported=publishable_supported,
        source_name="scope/example.md",
    )

    assert "\nviewable:" not in result.text.split("---", 2)[1]
    assert "publishable:" not in result.text
    assert result.text.endswith("unchanged\n")


def test_local_false_is_removed_but_reported_for_explicit_approval() -> None:
    result = migration.migrate_source_text(
        source("viewable: false\n"),
        publishable_supported=False,
        source_name="studio/default/example.md",
    )

    assert result.changed is True
    assert result.legacy_value is False
    assert "publishable:" not in result.text


def test_existing_publishable_conflict_fails_closed() -> None:
    with pytest.raises(ValueError, match="both viewable and publishable"):
        migration.migrate_source_text(
            source("viewable: false\npublishable: false\n"),
            publishable_supported=True,
            source_name="analysis/example.md",
        )
