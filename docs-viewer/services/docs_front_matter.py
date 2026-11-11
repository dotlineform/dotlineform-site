"""Shared front matter, including Summary and Book source records."""

from __future__ import annotations

import json
import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Any

from docs_document_identity import is_immutable_doc_id


FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
STRICT_FRONT_MATTER_PATTERN = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.DOTALL)
INTEGER_PATTERN = re.compile(r"^-?\d+$")
SAFE_PLAIN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,&()/_'-]*$")
SUMMARY_LITERAL_PATTERN = re.compile(r"\|(-)?(?:[ \t]+#.*)?\Z")
BOOK_SOURCE_FIELDS = frozenset({"copied_from_library", "library_sources"})


def book_source_record(value: Any) -> dict[str, str]:
    if (
        not isinstance(value, dict) or set(value) != {"doc_id", "title"}
        or not isinstance(value["doc_id"], str) or not is_immutable_doc_id(value["doc_id"])
        or not isinstance(value["title"], str) or not value["title"].strip()
    ):
        raise ValueError("Book source requires a Library document ID and title")
    return value


def book_source_records(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ValueError("Library sources must be a list")
    records = [book_source_record(record) for record in value]
    if len({record["doc_id"] for record in records}) != len(records):
        raise ValueError("Library sources must use distinct document IDs")
    return records


def parse_book_source_block(key: str, lines: list[str]) -> Any:
    sequence = key == "library_sources"
    id_prefix = "  - doc_id:" if sequence else "  doc_id:"
    title_prefix = "    title:" if sequence else "  title:"
    if len(lines) % 2 or (not sequence and len(lines) != 2):
        raise ValueError(f"{key} requires complete doc_id and title pairs")
    records = []
    for offset in range(0, len(lines), 2):
        id_line, title_line = lines[offset:offset + 2]
        if not id_line.startswith(id_prefix) or not title_line.startswith(title_prefix):
            raise ValueError(f"{key} requires doc_id followed by title")
        raw_title = title_line[len(title_prefix):].strip()
        records.append({
            "doc_id": parse_front_matter_value(id_line[len(id_prefix):]),
            "title": json.loads(raw_title) if raw_title.startswith('"') else parse_front_matter_value(raw_title),
        })
    return book_source_records(records) if sequence else book_source_record(records[0])


@dataclass(frozen=True)
class FrontMatterField:
    key: str
    raw_value: str
    value: Any
    start: int
    end: int


def normalize_summary(value: Any) -> str:
    """Ignore outer whitespace, retaining internal line and paragraph breaks."""
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def parse_front_matter_value(raw_value: str) -> Any:
    value = raw_value.strip()
    if value == '""':
        return ""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if INTEGER_PATTERN.fullmatch(value):
        try:
            return int(value)
        except ValueError:
            return value
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        if value[0] == '"':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value[1:-1]
        return value[1:-1].replace("\\'", "'")
    return value


def read_front_matter_fields(
    header: str, *, source_name: str = "source", strict: bool = False, require_pairs: bool = False,
) -> list[FrontMatterField]:
    """Read fields and complete block spans, with offsets into the raw header."""
    lines = header.splitlines(keepends=True)
    fields: list[FrontMatterField] = []
    seen: set[str] = set()
    index = 0
    offset = 0
    has_literal_summary = False

    def fail(line: int, message: str) -> None:
        raise ValueError(f"front matter line {line + 2} {message} in {source_name}")

    while index < len(lines):
        start = offset
        line = lines[index]
        stripped = line.strip()
        offset += len(line)
        index += 1
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            if strict or require_pairs or has_literal_summary:
                fail(index - 1, "is not a key/value pair")
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        value_text = raw_value.strip()
        if (strict and key in seen) or ((strict or require_pairs) and not key):
            fail(index - 1, "has a blank or duplicate key")
        seen.add(key)
        if key in BOOK_SOURCE_FIELDS:
            block_start = index - 1
            block = []
            while index < len(lines) and lines[index].startswith(" ") and lines[index].strip():
                block.append(lines[index].rstrip("\r\n"))
                offset += len(lines[index])
                index += 1
            try:
                if value_text:
                    raise ValueError(f"{key} requires an indented block")
                value = parse_book_source_block(key, block)
            except ValueError as error:
                fail(block_start, str(error))
        elif key == "summary" and value_text.startswith(("|", ">")):
            marker = SUMMARY_LITERAL_PATTERN.fullmatch(value_text)
            if marker is None:
                fail(index - 1, "summary literal block must use | or |-")
            has_literal_summary = True
            field_indent = len(line) - len(line.lstrip(" "))
            if line[field_indent:].startswith("\t"):
                fail(index - 1, "has tab indentation")
            block_indent: int | None = None
            content: list[str] = []
            while index < len(lines):
                block_line = lines[index].rstrip("\r\n")
                if block_line.strip():
                    indent = len(block_line) - len(block_line.lstrip(" "))
                    if indent <= field_indent:
                        if block_line[indent:].startswith("\t"):
                            fail(index, "summary block requires space indentation")
                        break
                    if block_indent is None:
                        block_indent = indent
                    if indent < block_indent:
                        fail(index, "summary block has inconsistent indentation")
                    content.append(block_line[block_indent:])
                else:
                    content.append("")
                offset += len(lines[index])
                index += 1
            value = "\n".join(content).rstrip("\n")
            if marker.group(1) is None and block_indent is not None:
                value += "\n"
        else:
            if has_literal_summary and line[:1].isspace():
                fail(index - 1, "has unexpected indentation outside summary")
            if strict and value_text.startswith(('"', "'")):
                if len(value_text) < 2 or value_text[-1] != value_text[0]:
                    fail(index - 1, "has an unclosed quoted value")
                if value_text[0] == '"':
                    try:
                        json.loads(value_text)
                    except json.JSONDecodeError:
                        fail(index - 1, "has an invalid quoted value")
            value = parse_front_matter_value(raw_value)
        fields.append(FrontMatterField(key, raw_value, value, start, offset))
    return fields


def format_front_matter_value(value: Any) -> str:
    if value is None:
        return '""'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if SAFE_PLAIN_PATTERN.fullmatch(text) and text not in {"true", "false"} and not INTEGER_PATTERN.fullmatch(text):
        return text
    return json.dumps(text, ensure_ascii=False)


def format_front_matter_field(key: str, value: Any) -> str:
    if key in BOOK_SOURCE_FIELDS:
        sequence = key == "library_sources"
        records = value if sequence else [value]
        lines = [f"{key}:"]
        for record in records:
            lines.append(f"  {'- ' if sequence else ''}doc_id: {record['doc_id']}")
            title = json.dumps(record["title"], ensure_ascii=False)
            lines.append(f"{'    ' if sequence else '  '}title: {title}")
        return "\n".join(lines)
    if key == "summary" and isinstance(value, str):
        value = normalize_summary(value)
        if "\n" in value:
            return "summary: |-\n" + "\n".join("  " + line if line else "" for line in value.split("\n"))
    return f"{key}: {format_front_matter_value(value)}"


def rewrite_front_matter_fields(
    prefix: str, updates: Mapping[str, Any], *, remove_fields: Collection[str] = (),
    fields: list[FrontMatterField] | None = None,
) -> str:
    """Replace whole field spans, preserving all unrelated authored text."""
    match = STRICT_FRONT_MATTER_PATTERN.match(prefix)
    if match is None:
        raise ValueError("source front matter could not be updated")
    header = match.group(1)
    if fields is None:
        fields = read_front_matter_fields(header, require_pairs=True)
    newline = "\r\n" if prefix.startswith("---\r\n") else "\n"
    seen: set[str] = set()
    for field in reversed(fields):
        seen.add(field.key)
        if field.key not in updates and field.key not in remove_fields:
            continue
        replacement = ""
        if field.key in updates:
            replacement = format_front_matter_field(field.key, updates[field.key]).replace("\n", newline)
            if header[field.start:field.end].endswith("\n"):
                replacement += newline
        header = header[:field.start] + replacement + header[field.end:]
    missing = [format_front_matter_field(key, value).replace("\n", newline) for key, value in updates.items() if key not in seen]
    if missing:
        if header and not header.endswith("\n"):
            header += newline
        header += newline.join(missing)
    return prefix[:match.start(1)] + header + prefix[match.end(1):]
