"""Pure parsing and validation for Docs Viewer report-source declarations."""

from __future__ import annotations

from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from markdown_it import MarkdownIt


REPORT_OPENER = ":::report"
REPORT_HOST_HTML = (
    '<section class="docsViewerReport" data-docs-viewer-report-host '
    'aria-label="Document report"></section>'
)
RETIRED_REPORT_KEYS = frozenset(
    {
        "viewer_report",
        "viewer_report_scope",
        "viewer_report_access",
        "viewer_report_preset",
        "viewer_report_subscope",
    }
)
_KEYS = frozenset({"id", "access", "scope", "preset", "sub_scope"})
_ACCESS = frozenset({"local", "public"})
_SCOPE_REPORTS = frozenset({"docs_index_table", "docs_broken_links", "semantic_tokens"})
_ID = re.compile(r"[a-z0-9][a-z0-9_-]*\Z")
_ATTRIBUTE = re.compile(r"([a-z_]+): ([a-z0-9][a-z0-9_-]*)\Z")
_MARKDOWN = MarkdownIt("commonmark")


@dataclass(frozen=True)
class ReportSourceRange:
    start: int
    end: int
    start_line: int
    end_line: int


@dataclass(frozen=True)
class ReportDescriptor:
    id: str
    access: str
    scope: str | None
    preset: str | None
    sub_scope: str | None
    source_range: ReportSourceRange

    def as_payload(self) -> Mapping[str, str | None]:
        return MappingProxyType(
            {
                "id": self.id,
                "access": self.access,
                "scope": self.scope,
                "preset": self.preset,
                "sub_scope": self.sub_scope,
            }
        )


def project_report_markdown(
    markdown: str,
    descriptor: ReportDescriptor | None,
    *,
    include_host: bool,
) -> str:
    """Replace a validated report declaration with its inert host or nothing."""

    if descriptor is None:
        return markdown
    source_range = descriptor.source_range
    replacement = REPORT_HOST_HTML if include_host else ""
    return markdown[: source_range.start] + replacement + markdown[source_range.end :]


@dataclass(frozen=True)
class ReportDefinition:
    report_id: str
    preset_ids: frozenset[str]


@dataclass(frozen=True)
class ReportSourceContract:
    reports: tuple[ReportDefinition, ...]
    configured_scope_ids: frozenset[str]
    source_scope_id: str
    configured_sub_scope_ids: frozenset[str]
    source_sub_scope_id: str = ""

    def report(self, report_id: str) -> ReportDefinition | None:
        return next((item for item in self.reports if item.report_id == report_id), None)


class ReportSourceError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        source_name: str,
        line: int,
        start: int,
        end: int,
        code: str,
    ) -> None:
        self.code = code
        self.source_name = source_name
        self.line = line
        self.start = start
        self.end = end
        super().__init__(f"{source_name}:{line}: {message} (source range {start}:{end})")


class ReportSourceContractRequired(ValueError):
    """Raised only after one syntactically valid report declaration is found."""


@dataclass(frozen=True)
class _Line:
    text: str
    start: int
    end: int
    number: int


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"{label} must match [a-z0-9][a-z0-9_-]*")
    return value


def build_report_source_contract(
    registry_payload: Mapping[str, Any],
    *,
    source_scope_id: str,
    configured_scope_ids: Iterable[str],
    configured_sub_scope_ids: Iterable[str] = (),
    source_sub_scope_id: str = "",
) -> ReportSourceContract:
    """Normalize registry and host context into an immutable parser contract."""

    raw_reports = registry_payload.get("reports") if isinstance(registry_payload, Mapping) else None
    if not isinstance(raw_reports, list):
        raise ValueError("report registry reports must be an array")
    reports: list[ReportDefinition] = []
    seen: set[str] = set()
    for index, raw_report in enumerate(raw_reports):
        if not isinstance(raw_report, Mapping):
            raise ValueError(f"report registry reports[{index}] must be an object")
        report_id = _identifier(raw_report.get("report_id"), "report_id")
        if report_id in seen:
            raise ValueError(f"duplicate report_id: {report_id}")
        seen.add(report_id)
        raw_presets = raw_report.get("presets")
        if not isinstance(raw_presets, list):
            raise ValueError(f"report {report_id} presets must be an array")
        presets: set[str] = set()
        for raw_preset in raw_presets:
            if not isinstance(raw_preset, Mapping):
                raise ValueError(f"report {report_id} presets must contain objects")
            preset_id = _identifier(raw_preset.get("preset_id"), "preset_id")
            if preset_id in presets:
                raise ValueError(f"report {report_id} has duplicate preset_id: {preset_id}")
            presets.add(preset_id)
        reports.append(ReportDefinition(report_id, frozenset(presets)))

    scopes = frozenset(_identifier(value, "scope id") for value in configured_scope_ids)
    source_scope = _identifier(source_scope_id, "source_scope_id")
    if source_scope not in scopes:
        raise ValueError(f"source_scope_id is not configured: {source_scope}")
    children = frozenset(_identifier(value, "sub-scope id") for value in configured_sub_scope_ids)
    child_source = _identifier(source_sub_scope_id, "source_sub_scope_id") if source_sub_scope_id else ""
    if child_source and child_source not in children:
        raise ValueError(f"source_sub_scope_id is not configured: {child_source}")
    return ReportSourceContract(tuple(reports), scopes, source_scope, children, child_source)


def _lines(markdown: str) -> list[_Line]:
    result: list[_Line] = []
    offset = 0
    for number, raw in enumerate(markdown.splitlines(keepends=True), 1):
        result.append(_Line(raw.rstrip("\r\n"), offset, offset + len(raw), number))
        offset += len(raw)
    return result


def _failure(
    message: str,
    code: str,
    source_name: str,
    line: _Line,
    line_offset: int,
    span: tuple[int, int] | None = None,
) -> ReportSourceError:
    start, end = span or (line.start, line.end)
    return ReportSourceError(
        message,
        source_name=source_name,
        line=line.number + line_offset,
        start=start,
        end=end,
        code=code,
    )


def _ignored_lines(markdown: str) -> frozenset[int]:
    """Return zero-based lines where CommonMark treats declarations as literals."""

    ignored: set[int] = set()
    for token in _MARKDOWN.parse(markdown):
        if token.map is None:
            continue
        literal = token.type in {"fence", "code_block"}
        if token.type == "html_block":
            start = token.content.lstrip().lower()
            literal = start.startswith(("<!--", "<pre", "<code"))
        if token.type == "inline":
            literal = any(
                child.type in {"code_inline", "html_inline"}
                and REPORT_OPENER in child.content
                for child in token.children or ()
            )
        if literal:
            ignored.update(range(*token.map))
    return frozenset(ignored)


def _parse_block(
    lines: list[_Line],
    index: int,
    source_name: str,
    line_offset: int,
) -> tuple[dict[str, str], ReportSourceRange, int]:
    opener = lines[index]
    if index and lines[index - 1].text.strip():
        raise _failure("report block must be preceded by a blank line", "block_isolation", source_name, opener, line_offset)
    attributes: dict[str, str] = {}
    cursor = index + 1
    while cursor < len(lines) and lines[cursor].text != ":::":
        line = lines[cursor]
        match = _ATTRIBUTE.fullmatch(line.text)
        if not match:
            raise _failure("report attribute must use exact `key: value` syntax", "malformed_attribute", source_name, line, line_offset)
        key, value = match.groups()
        if key not in _KEYS:
            raise _failure(f"unknown report attribute: {key}", "unknown_attribute", source_name, line, line_offset)
        if key in attributes:
            raise _failure(f"duplicate report attribute: {key}", "duplicate_attribute", source_name, line, line_offset)
        attributes[key] = value
        cursor += 1
    if cursor == len(lines):
        end = lines[-1].end
        raise _failure("unclosed report block", "unclosed_block", source_name, opener, line_offset, (opener.start, end))
    closer = lines[cursor]
    span = (opener.start, closer.end)
    if cursor + 1 < len(lines) and lines[cursor + 1].text.strip():
        raise _failure("report block must be followed by a blank line", "block_isolation", source_name, closer, line_offset, span)
    return attributes, ReportSourceRange(*span, opener.number + line_offset, closer.number + line_offset), cursor


def _invalid(
    message: str,
    code: str,
    source_name: str,
    source_range: ReportSourceRange,
) -> ReportSourceError:
    return ReportSourceError(
        message,
        source_name=source_name,
        line=source_range.start_line,
        start=source_range.start,
        end=source_range.end,
        code=code,
    )


def _descriptor(
    attributes: Mapping[str, str],
    source_range: ReportSourceRange,
    contract: ReportSourceContract,
    source_name: str,
) -> ReportDescriptor:
    for required in ("id", "access"):
        if required not in attributes:
            raise _invalid(f"missing required report attribute: {required}", "missing_attribute", source_name, source_range)
    report_id, access = attributes["id"], attributes["access"]
    definition = contract.report(report_id)
    if definition is None:
        raise _invalid(f"unknown report id: {report_id}", "unknown_report", source_name, source_range)
    if access not in _ACCESS:
        raise _invalid(f"unknown report access: {access}", "unknown_access", source_name, source_range)

    scope, preset, sub_scope = (attributes.get(key) for key in ("scope", "preset", "sub_scope"))
    if scope is not None:
        if report_id not in _SCOPE_REPORTS:
            raise _invalid(f"scope is not allowed for report: {report_id}", "invalid_scope", source_name, source_range)
        if scope not in contract.configured_scope_ids:
            raise _invalid(f"scope is not configured: {scope}", "invalid_scope", source_name, source_range)
    if preset is not None:
        if report_id != "docs_index_table":
            raise _invalid(f"preset is not allowed for report: {report_id}", "invalid_preset", source_name, source_range)
        if preset not in definition.preset_ids:
            raise _invalid(f"preset is not registered for {report_id}: {preset}", "invalid_preset", source_name, source_range)
    if report_id == "docs_subscope":
        if sub_scope is None:
            raise _invalid("docs_subscope requires sub_scope", "invalid_sub_scope", source_name, source_range)
        if sub_scope not in contract.configured_sub_scope_ids:
            message = f"sub_scope is not configured for {contract.source_scope_id}: {sub_scope}"
            raise _invalid(message, "invalid_sub_scope", source_name, source_range)
    elif sub_scope is not None:
        raise _invalid(f"sub_scope is not allowed for report: {report_id}", "invalid_sub_scope", source_name, source_range)
    return ReportDescriptor(report_id, access, scope, preset, sub_scope, source_range)


def parse_report_source(
    markdown: str,
    *,
    front_matter: Mapping[str, Any] | None,
    source_name: str,
    contract: ReportSourceContract | None = None,
    line_offset: int = 0,
) -> ReportDescriptor | None:
    """Parse zero or one exact report block from a Markdown body."""

    if not isinstance(markdown, str):
        raise TypeError("markdown must be a string")
    if not source_name:
        raise ValueError("source_name must be a non-empty string")
    if not isinstance(line_offset, int) or line_offset < 0:
        raise ValueError("line_offset must be a non-negative integer")
    metadata = front_matter or {}
    if not isinstance(metadata, Mapping):
        raise TypeError("front_matter must be a mapping or None")
    retired = sorted(RETIRED_REPORT_KEYS.intersection(metadata))
    if retired:
        raise ReportSourceError(
            f"retired report front matter key is forbidden: {retired[0]}",
            source_name=source_name,
            line=1,
            start=0,
            end=0,
            code="retired_front_matter",
        )
    if REPORT_OPENER not in markdown:
        return None

    lines = _lines(markdown)
    ignored = _ignored_lines(markdown)
    found: tuple[dict[str, str], ReportSourceRange] | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        if index in ignored:
            index += 1
            continue
        if line.text.lstrip(" ").startswith(REPORT_OPENER):
            if line.text != REPORT_OPENER:
                raise _failure("report opener must be exact and start at column 1", "malformed_opener", source_name, line, line_offset)
            attributes, source_range, closer = _parse_block(lines, index, source_name, line_offset)
            if found:
                raise _failure("only one report block is allowed", "multiple_blocks", source_name, line, line_offset, (source_range.start, source_range.end))
            found = attributes, source_range
            index = closer + 1
            continue
        index += 1

    if found is None:
        return None
    attributes, source_range = found
    if contract is None:
        raise ReportSourceContractRequired(
            f"{source_name}:{source_range.start_line}: report source contract is required"
        )
    if contract.source_sub_scope_id:
        raise _invalid("report blocks are forbidden in sub-scope document source", "sub_scope_source", source_name, source_range)
    return _descriptor(attributes, source_range, contract, source_name)
