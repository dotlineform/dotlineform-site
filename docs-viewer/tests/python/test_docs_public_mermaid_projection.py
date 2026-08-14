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
    PUBLIC_MERMAID_MANIFEST_SCHEMA_VERSION,
    inventory_public_mermaid_fences,
    plan_public_mermaid_projection,
    public_mermaid_projection_report,
)
import plan_public_mermaid_projection as projection_cli  # noqa: E402

from build_docs_test_support import (  # noqa: E402
    CHILD_DOC_ID,
    PARENT_DOC_ID,
    write_public_scope_config,
    write_public_source_docs,
    write_site_tools_config,
    write_text,
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


def test_cli_reports_both_variants_failures_and_no_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_site_tools_config(tmp_path, media_base="")
    write_public_scope_config(tmp_path)
    write_public_source_docs(tmp_path)
    child_path = (
        tmp_path
        / f"docs-viewer/scopes/example/source/documents/{CHILD_DOC_ID}.md"
    )
    write_text(
        child_path,
        f"""---
doc_id: {CHILD_DOC_ID}
title: Child
added_date: 2026-06-03
last_updated: 2026-06-03 10:00:00
parent_id: {PARENT_DOC_ID}
---
# Child

{fenced_mermaid("CLI flow", "The dry-run reports both variants.")}

```mermaid
flowchart LR
  accTitle: Broken flow
  A --> B
```
""",
    )
    before_files = sorted(
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    monkeypatch.chdir(tmp_path)

    exit_code = projection_cli.main(["--scope", "example", "--diagnostics"])
    output = capsys.readouterr()
    after_files = sorted(
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    )

    assert exit_code == 0
    assert output.err == ""
    assert "Public Mermaid projection plan (dry-run) scope=example" in output.out
    assert "variants total: 2" in output.out
    assert "failures: 1" in output.out
    assert "light=projection-assets/mermaid/" in output.out
    assert "dark=projection-assets/mermaid/" in output.out
    assert "requires a non-empty accDescr" in output.out
    diagnostics_line = next(
        line
        for line in output.out.splitlines()
        if line.startswith("Public Mermaid projection diagnostics: ")
    )
    diagnostics = json.loads(diagnostics_line.split(": ", 1)[1])
    assert diagnostics["manifest"]["schema_version"] == PUBLIC_MERMAID_MANIFEST_SCHEMA_VERSION
    assert diagnostics["summary"]["variant_count"] == 2
    assert all("mermaid" not in item["source"] for item in diagnostics["diagrams"])
    assert before_files == after_files
    assert not (
        tmp_path
        / "docs-viewer/scopes/example/published/documents/.publish"
        / projection_cli.MANIFEST_FILENAME
    ).exists()
