from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICES_DIR))

from docs_report_source import (  # noqa: E402
    ReportSourceError,
    build_report_source_contract,
    parse_report_source,
)


SOURCE_NAME = "docs-viewer/scopes/analysis/source/documents/report.md"


def registry() -> dict[str, object]:
    def report(
        report_id: str,
        *,
        access: str = "local",
        presets: tuple[str, ...] = (),
    ) -> dict[str, object]:
        return {
            "report_id": report_id,
            "default_access": access,
            "presets": [{"preset_id": preset_id} for preset_id in presets],
        }

    return {
        "reports": [
            report("docs_index_table", presets=("scope_documents_admin", "az_index")),
            report("docs_broken_links"),
            report("semantic_tokens"),
            report("docs_subscope", access="public"),
            report("reports_list", access="public"),
        ]
    }


def contract(**overrides: object):
    kwargs = {
        "source_scope_id": "analysis",
        "configured_scope_ids": ("analysis", "studio"),
        "configured_sub_scope_ids": ("tags", "works"),
        **overrides,
    }
    return build_report_source_contract(registry(), **kwargs)


def parse(markdown: str, **kwargs: object):
    return parse_report_source(
        markdown,
        front_matter=kwargs.pop("front_matter", {}),
        source_name=SOURCE_NAME,
        contract=kwargs.pop("contract", contract()),
        **kwargs,
    )


def block(*attributes: str) -> str:
    return "\n".join((":::report", *attributes, ":::", ""))


def assert_error(markdown: str, code: str, **kwargs: object) -> ReportSourceError:
    with pytest.raises(ReportSourceError) as caught:
        parse(markdown, **kwargs)
    assert caught.value.code == code
    return caught.value


def test_valid_descriptor_is_stable_immutable_and_order_independent() -> None:
    markdown = "Intro\n\n" + block(
        "preset: scope_documents_admin",
        "access: local",
        "id: docs_index_table",
        "scope: analysis",
    )
    descriptor = parse(markdown)

    assert descriptor is not None
    assert dict(descriptor.as_payload()) == {
        "id": "docs_index_table",
        "access": "local",
        "scope": "analysis",
        "preset": "scope_documents_admin",
        "sub_scope": None,
    }
    assert descriptor.source_range.start == len("Intro\n\n")
    assert descriptor.source_range.end == len(markdown)
    assert descriptor.source_range.start_line == 3
    assert descriptor.source_range.end_line == 8
    with pytest.raises(FrozenInstanceError):
        descriptor.id = "reports_list"  # type: ignore[misc]
    with pytest.raises(TypeError):
        descriptor.as_payload()["id"] = "reports_list"  # type: ignore[index]


def test_zero_blocks_returns_none() -> None:
    assert parse("# Ordinary document\n") is None


def test_crlf_range_and_line_offset_are_exact() -> None:
    markdown = "Head\r\n\r\n:::report\r\nid: reports_list\r\naccess: public\r\n:::\r\n"
    descriptor = parse(markdown, line_offset=4)

    assert descriptor is not None
    assert descriptor.source_range.start == len("Head\r\n\r\n")
    assert descriptor.source_range.end == len(markdown)
    assert descriptor.source_range.start_line == 7
    assert descriptor.source_range.end_line == 10


@pytest.mark.parametrize(
    ("markdown", "code"),
    [
        (block("id: reports_list"), "missing_attribute"),
        (block("access: public"), "missing_attribute"),
        (block("id: reports_list", "access: public", ""), "malformed_attribute"),
        (block("id: reports_list", "access: \"public\""), "malformed_attribute"),
        (block(" id: reports_list", "access: public"), "malformed_attribute"),
        (" :::report\nid: reports_list\naccess: public\n:::\n", "malformed_opener"),
        (":::report trailing\n", "malformed_opener"),
    ],
)
def test_required_attributes_and_exact_syntax(markdown: str, code: str) -> None:
    assert_error(markdown, code)


def test_duplicate_and_unknown_attributes_fail_at_attribute_line() -> None:
    duplicate = assert_error(
        block("id: reports_list", "id: reports_list", "access: public"),
        "duplicate_attribute",
    )
    unknown = assert_error(
        block("id: reports_list", "access: public", "loader: reports_list"),
        "unknown_attribute",
    )
    assert duplicate.line == 3
    assert unknown.line == 4


def test_cardinality_closure_and_blank_line_isolation() -> None:
    first = block("id: reports_list", "access: public")
    assert_error(first + "\n" + first, "multiple_blocks")
    assert_error(":::report\nid: reports_list\naccess: public\n", "unclosed_block")
    assert_error("Text\n" + first, "block_isolation")
    assert_error(first.rstrip("\n") + "\nText\n", "block_isolation")


@pytest.mark.parametrize(
    "retired_key",
    [
        "viewer_report",
        "viewer_report_scope",
        "viewer_report_access",
        "viewer_report_preset",
        "viewer_report_subscope",
    ],
)
def test_retired_front_matter_fails_even_when_blank(retired_key: str) -> None:
    error = assert_error(
        "Ordinary body\n",
        "retired_front_matter",
        front_matter={retired_key: ""},
    )
    assert retired_key in str(error)


@pytest.mark.parametrize(
    ("attributes", "code"),
    [
        (("id: missing_report", "access: public"), "unknown_report"),
        (("id: reports_list", "access: private"), "unknown_access"),
        (("id: docs_index_table", "access: local", "scope: missing"), "invalid_scope"),
        (("id: docs_index_table", "access: local", "preset: missing"), "invalid_preset"),
        (("id: reports_list", "access: public", "scope: analysis"), "invalid_scope"),
        (("id: docs_broken_links", "access: local", "preset: az_index"), "invalid_preset"),
        (("id: reports_list", "access: public", "sub_scope: tags"), "invalid_sub_scope"),
    ],
)
def test_unknown_values_and_forbidden_context_fail(
    attributes: tuple[str, ...], code: str
) -> None:
    assert_error(block(*attributes), code)


@pytest.mark.parametrize("report_id", ["docs_broken_links", "semantic_tokens"])
def test_registered_scope_context_is_allowed_for_scope_reports(report_id: str) -> None:
    descriptor = parse(block(f"id: {report_id}", "access: local", "scope: studio"))
    assert descriptor is not None
    assert descriptor.scope == "studio"


def test_docs_subscope_requires_a_configured_child() -> None:
    assert_error(block("id: docs_subscope", "access: public"), "invalid_sub_scope")
    assert_error(
        block("id: docs_subscope", "access: public", "sub_scope: unknown"),
        "invalid_sub_scope",
    )
    descriptor = parse(
        block("id: docs_subscope", "access: public", "sub_scope: works")
    )
    assert descriptor is not None
    assert descriptor.sub_scope == "works"


def test_report_block_is_forbidden_in_child_subscope_source() -> None:
    child_contract = contract(source_sub_scope_id="works")
    assert_error(
        block("id: reports_list", "access: public"),
        "sub_scope_source",
        contract=child_contract,
    )


@pytest.mark.parametrize(
    "literal",
    [
        "```md\n:::report\nid: missing\naccess: private\n:::\n```",
        "~~~\n:::report\nid: missing\naccess: private\n:::\n~~~",
        "    :::report\n    id: missing\n    access: private\n    :::",
        "\t:::report\n\tid: missing\n\taccess: private\n\t:::",
        "``\n:::report\nid: missing\naccess: private\n:::\n``",
        "<!--\n:::report\nid: missing\naccess: private\n:::\n-->",
        "<pre>\n:::report\nid: missing\naccess: private\n:::\n</pre>",
        "<code>\n:::report\nid: missing\naccess: private\n:::\n</code>",
    ],
)
def test_literal_markdown_contexts_are_ignored(literal: str) -> None:
    markdown = literal + "\n\n" + block("id: reports_list", "access: public")
    descriptor = parse(markdown)
    assert descriptor is not None
    assert descriptor.id == "reports_list"


@pytest.mark.parametrize(
    "markdown",
    [
        "> :::report\n> id: missing\n> access: private\n> :::\n",
        "- :::report\n  id: missing\n  access: private\n  :::\n",
        "Text with `:::report` inline.\n",
    ],
)
def test_non_declaration_tokens_are_not_recognized(markdown: str) -> None:
    assert parse(markdown) is None


def test_error_includes_source_path_line_and_exact_range() -> None:
    error = assert_error(
        "Head\n\n" + block("id: reports_list", "access: public", "unknown: value"),
        "unknown_attribute",
    )
    assert error.source_name == SOURCE_NAME
    assert error.line == 6
    assert error.start == len("Head\n\n:::report\nid: reports_list\naccess: public\n")
    assert error.end > error.start
    assert f"{SOURCE_NAME}:6:" in str(error)
    assert f"source range {error.start}:{error.end}" in str(error)


def test_contract_rejects_duplicate_reports_presets_and_unknown_source_scope() -> None:
    duplicate_reports = registry()
    duplicate_reports["reports"].append(duplicate_reports["reports"][0])  # type: ignore[union-attr,index]
    with pytest.raises(ValueError, match="duplicate report_id"):
        build_report_source_contract(
            duplicate_reports,
            source_scope_id="analysis",
            configured_scope_ids=("analysis",),
        )

    duplicate_presets = registry()
    duplicate_presets["reports"][0]["presets"].append(  # type: ignore[index,union-attr]
        {"preset_id": "scope_documents_admin"}
    )
    with pytest.raises(ValueError, match="duplicate preset_id"):
        build_report_source_contract(
            duplicate_presets,
            source_scope_id="analysis",
            configured_scope_ids=("analysis",),
        )

    with pytest.raises(ValueError, match="source_scope_id is not configured"):
        build_report_source_contract(
            registry(),
            source_scope_id="analysis",
            configured_scope_ids=("studio",),
        )
