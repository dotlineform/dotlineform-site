#!/usr/bin/env python3
"""Focused public Mermaid fence inventory and projection-plan checks."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
for _path in (REPO_ROOT / "docs-viewer" / "build", REPO_ROOT / "docs-viewer" / "services"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from docs_public_mermaid_projection import (  # noqa: E402
    inventory_public_mermaid_fences,
    plan_public_mermaid_projection,
    public_mermaid_projection_report,
)

from build_docs_test_support import (  # noqa: E402
    PARENT_DOC_ID,
)


OTHER_DOC_ID = "d-20260624-000000-000009"


def accessible_mermaid(title: str, description: str, edge: str = "A --> B") -> str:
    return "\n".join(
        [
            "flowchart LR",
            f"  accTitle: {title}",
            f"  accDescr: {description}",
            f"  {edge}",
            "",
        ]
    )


def fenced_mermaid(title: str, description: str, edge: str = "A --> B") -> str:
    return f"```mermaid\n{accessible_mermaid(title, description, edge)}```\n"


def test_inventory_and_plan_use_document_ordinals_and_explicit_theme_records() -> None:
    parent_markdown = "\n".join(
        [
            "# Parent",
            "",
            "```text",
            "not a Mermaid block",
            "```",
            "",
            fenced_mermaid("Architecture flow", "Source reaches the public projection."),
            "~~~mermaid optional-info",
            accessible_mermaid("State flow", "State moves from open to closed.", "Open --> Closed"),
            "~~~",
        ]
    )
    unchanged_source = str(parent_markdown)

    fences, failures = inventory_public_mermaid_fences(
        [
            (OTHER_DOC_ID, "# Other\n"),
            (PARENT_DOC_ID, parent_markdown),
        ]
    )
    plan = plan_public_mermaid_projection(
        scope="example",
        documents=[(PARENT_DOC_ID, parent_markdown), (OTHER_DOC_ID, "# Other\n")],
        public_url_prefix="/assets/data/docs/scopes/example",
    )

    assert failures == ()
    assert parent_markdown == unchanged_source
    assert [fence.projection_id for fence in fences] == [
        f"{PARENT_DOC_ID}--mermaid-0001",
        f"{PARENT_DOC_ID}--mermaid-0002",
    ]
    assert [fence.source_line for fence in fences] == [7, 14]
    assert plan["summary"] == {
        "diagram_count": 2,
        "variant_count": 4,
        "create_count": 2,
        "replace_count": 0,
        "unchanged_count": 0,
        "failure_count": 0,
        "removal_family_count": 0,
        "removal_variant_count": 0,
    }
    first = plan["diagrams"][0]
    assert first["action"] == "create"
    assert first["projection"]["alt"] == "Architecture flow"
    assert first["projection"]["variants"] == {
        "light": {
            "artifact_identity": (
                f"projection-assets/mermaid/{PARENT_DOC_ID}--mermaid-0001/light.svg"
            ),
            "url": (
                "/assets/data/docs/scopes/example/projection-assets/mermaid/"
                f"{PARENT_DOC_ID}--mermaid-0001/light.svg"
            ),
        },
        "dark": {
            "artifact_identity": (
                f"projection-assets/mermaid/{PARENT_DOC_ID}--mermaid-0001/dark.svg"
            ),
            "url": (
                "/assets/data/docs/scopes/example/projection-assets/mermaid/"
                f"{PARENT_DOC_ID}--mermaid-0001/dark.svg"
            ),
        },
    }
    assert "mermaid" in first["source"]
    assert "mermaid" not in public_mermaid_projection_report(plan)["diagrams"][0]["source"]


def test_changed_source_replaces_same_pair_and_invalid_or_deleted_fences_remove_whole_families() -> None:
    initial = plan_public_mermaid_projection(
        scope="example",
        documents=[
            (PARENT_DOC_ID, fenced_mermaid("Parent flow", "Initial parent description.")),
            (OTHER_DOC_ID, fenced_mermaid("Other flow", "Initial other description.")),
        ],
        public_url_prefix="/assets/data/docs/scopes/example",
    )
    changed_parent = fenced_mermaid(
        "Parent flow",
        "Changed parent description.",
        "A --> C",
    )
    invalid_other = "```mermaid\nflowchart LR\n  accTitle: Other flow\n  A --> B\n```\n"

    next_plan = plan_public_mermaid_projection(
        scope="example",
        documents=[
            (PARENT_DOC_ID, changed_parent),
            (OTHER_DOC_ID, invalid_other),
        ],
        public_url_prefix="/assets/data/docs/scopes/example",
        previous_manifest=initial["manifest"],
    )

    assert next_plan["summary"] == {
        "diagram_count": 1,
        "variant_count": 2,
        "create_count": 0,
        "replace_count": 1,
        "unchanged_count": 0,
        "failure_count": 1,
        "removal_family_count": 1,
        "removal_variant_count": 2,
    }
    replacement = next_plan["diagrams"][0]
    assert replacement["projection"]["projection_id"] == f"{PARENT_DOC_ID}--mermaid-0001"
    assert replacement["projection"]["variants"] == initial["diagrams"][0]["projection"]["variants"]
    assert next_plan["failures"][0]["projection_id"] == f"{OTHER_DOC_ID}--mermaid-0001"
    assert "requires a non-empty accDescr" in next_plan["failures"][0]["message"]
    assert next_plan["removals"] == [
        {
            "projection_id": f"{OTHER_DOC_ID}--mermaid-0001",
            "doc_id": OTHER_DOC_ID,
            "fence_index": 1,
            "variant_identities": [
                f"projection-assets/mermaid/{OTHER_DOC_ID}--mermaid-0001/light.svg",
                f"projection-assets/mermaid/{OTHER_DOC_ID}--mermaid-0001/dark.svg",
            ],
        }
    ]


def test_previous_manifest_cannot_claim_authored_or_unowned_svg() -> None:
    plan = plan_public_mermaid_projection(
        scope="example",
        documents=[(PARENT_DOC_ID, fenced_mermaid("Flow", "A useful description."))],
        public_url_prefix="/assets/data/docs/scopes/example",
    )
    manifest = json.loads(json.dumps(plan["manifest"]))
    manifest["diagrams"][0]["variants"]["light"]["artifact_identity"] = "media/svg/authored.svg"

    with pytest.raises(ValueError, match="outside manifest ownership"):
        plan_public_mermaid_projection(
            scope="example",
            documents=[(PARENT_DOC_ID, fenced_mermaid("Flow", "A useful description."))],
            public_url_prefix="/assets/data/docs/scopes/example",
            previous_manifest=manifest,
        )
