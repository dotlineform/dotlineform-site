from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from .common import read_json
from .semantic_token_registry import SemanticTokenRegistry
from .source import DocRecord


LEXICAL_KEY_PATTERN = re.compile(r"[a-z][a-z0-9-]*")
LEXICAL_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
FENCE_PATTERN = re.compile(r"\A {0,3}(`{3,}|~{3,})")
SEMANTIC_TOKEN_TARGET_LOOKUP_SCHEMA_VERSION = "docs_semantic_token_target_lookup_v1"
SEMANTIC_TOKEN_TARGET_LOOKUP_PATH = Path(
    "docs-viewer/data/generated/semantic-tokens/target-lookup.json"
)


@dataclass(frozen=True)
class SemanticTokenOccurrence:
    raw: str
    family: str
    target_type: str
    target_id: str
    title: str
    start: int
    end: int
    supported: bool

    @property
    def source_range(self) -> dict[str, int]:
        return {"start": self.start, "end": self.end}


def escape_semantic_token_title(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("]", "\\]")


def serialize_semantic_token(
    *,
    family: str,
    target_type: str,
    target_id: str,
    title: str,
) -> str:
    clean_title = str(title or "").strip()
    if not clean_title or "\n" in clean_title or "\r" in clean_title:
        return ""
    return (
        f"[[{family}:{target_type}:{target_id}|"
        f"{escape_semantic_token_title(clean_title)}]]"
    )


def unescape_semantic_token_title(value: str) -> str | None:
    out: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char != "\\":
            out.append(char)
            index += 1
            continue
        if index + 1 >= len(value) or value[index + 1] not in {"\\", "|", "]"}:
            return None
        out.append(value[index + 1])
        index += 2
    title = "".join(out).strip()
    return title or None


def token_closing_index(text: str, start: int) -> int:
    index = start
    while index < len(text) - 1:
        if text[index] == "\\":
            index += 2
            continue
        if text[index:index + 2] == "]]":
            return index
        index += 1
    return -1


def parse_catalogue_token(
    raw: str,
    *,
    start: int = 0,
    registry: SemanticTokenRegistry | None = None,
) -> SemanticTokenOccurrence | None:
    if not raw.startswith("[[") or not raw.endswith("]]") or "\n" in raw or "\r" in raw:
        return None
    body = raw[2:-2]
    identity, separator, raw_title = body.partition("|")
    parts = identity.split(":")
    if not separator or len(parts) != 3:
        return None
    family, target_type, target_id = parts
    if (
        family != "catalogue"
        or not LEXICAL_KEY_PATTERN.fullmatch(family)
        or not LEXICAL_KEY_PATTERN.fullmatch(target_type)
        or not LEXICAL_ID_PATTERN.fullmatch(target_id)
    ):
        return None
    title = unescape_semantic_token_title(raw_title)
    if title is None:
        return None
    family_definition = registry.family(family) if registry else None
    target_definition = family_definition.target_type(target_type) if family_definition else None
    supported = target_definition is not None
    if supported and not re.fullmatch(target_definition.id_policy.canonical_pattern, target_id):
        return None
    return SemanticTokenOccurrence(
        raw=raw,
        family=family,
        target_type=target_type,
        target_id=target_id,
        title=title,
        start=start,
        end=start + len(raw),
        supported=supported,
    )


def _outside_inline_code_ranges(text: str, start: int, end: int) -> Iterable[tuple[int, int]]:
    index = start
    while index < end:
        tick = re.search(r"`+", text[index:end])
        if tick is None:
            yield index, end
            return
        tick_start = index + tick.start()
        tick_end = index + tick.end()
        if tick_start > index:
            yield index, tick_start
        marker = tick.group(0)
        close = text.find(marker, tick_end, end)
        if close < 0:
            return
        index = close + len(marker)


def _outside_comment_ranges(
    text: str,
    start: int,
    end: int,
    *,
    in_comment: bool,
) -> tuple[list[tuple[int, int]], bool]:
    ranges: list[tuple[int, int]] = []
    index = start
    while index < end:
        if in_comment:
            close = text.find("-->", index, end)
            if close < 0:
                return ranges, True
            index = close + 3
            in_comment = False
            continue
        open_index = text.find("<!--", index, end)
        segment_end = open_index if open_index >= 0 else end
        ranges.extend(_outside_inline_code_ranges(text, index, segment_end))
        if open_index < 0:
            return ranges, False
        index = open_index + 4
        in_comment = True
    return ranges, in_comment


def semantic_token_text_ranges(markdown: str) -> Iterable[tuple[int, int]]:
    offset = 0
    in_fence = False
    fence_character = ""
    in_comment = False
    for line in markdown.splitlines(keepends=True):
        fence_match = FENCE_PATTERN.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if in_fence and marker[0] == fence_character:
                in_fence = False
                fence_character = ""
            elif not in_fence:
                in_fence = True
                fence_character = marker[0]
            offset += len(line)
            continue
        if not in_fence:
            ranges, in_comment = _outside_comment_ranges(
                markdown,
                offset,
                offset + len(line),
                in_comment=in_comment,
            )
            yield from ranges
        offset += len(line)


def parse_catalogue_tokens(
    markdown: str,
    *,
    registry: SemanticTokenRegistry | None,
) -> list[SemanticTokenOccurrence]:
    if "[[catalogue:" not in markdown:
        return []
    tokens: list[SemanticTokenOccurrence] = []
    for range_start, range_end in semantic_token_text_ranges(markdown):
        index = range_start
        while index < range_end:
            opening = markdown.find("[[catalogue:", index, range_end)
            if opening < 0:
                break
            closing = token_closing_index(markdown, opening + 2)
            if closing < 0 or closing + 2 > range_end:
                break
            raw = markdown[opening:closing + 2]
            token = parse_catalogue_token(raw, start=opening, registry=registry)
            if token is not None:
                tokens.append(token)
            index = closing + 2
    return tokens


def semantic_token_at_selection(
    tokens: list[SemanticTokenOccurrence],
    *,
    start: int,
    end: int,
) -> SemanticTokenOccurrence | None:
    active = [
        token
        for token in tokens
        if token.supported
        and (
            (start == end and token.start < start < token.end)
            or (start != end and token.start == start and token.end == end)
        )
    ]
    return active[0] if len(active) == 1 else None


def replace_catalogue_tokens(
    markdown: str,
    *,
    registry: SemanticTokenRegistry | None,
    replacer: Callable[[SemanticTokenOccurrence], str],
) -> str:
    tokens = parse_catalogue_tokens(markdown, registry=registry)
    if not tokens:
        return markdown
    output: list[str] = []
    offset = 0
    for token in tokens:
        output.append(markdown[offset:token.start])
        output.append(replacer(token))
        offset = token.end
    output.append(markdown[offset:])
    return "".join(output)


def render_catalogue_token(token: SemanticTokenOccurrence, target: dict[str, Any]) -> str:
    href = str(target.get("href") or "").strip()
    if not href:
        return token.raw
    attrs = (
        f'data-semantic-token-family="{html.escape(token.family, quote=True)}" '
        f'data-semantic-token-target-type="{html.escape(token.target_type, quote=True)}" '
        f'data-semantic-token-target-id="{html.escape(token.target_id, quote=True)}" '
        'target="_blank" rel="noopener noreferrer"'
    )
    return (
        f'<a href="{html.escape(href, quote=True)}" {attrs}>'
        f"{html.escape(token.title)}</a>"
    )


def load_semantic_token_targets(repo_root: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    payload = read_json(repo_root / SEMANTIC_TOKEN_TARGET_LOOKUP_PATH)
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != SEMANTIC_TOKEN_TARGET_LOOKUP_SCHEMA_VERSION
        or not isinstance(payload.get("targets"), list)
    ):
        return {}
    targets: dict[tuple[str, str, str], dict[str, Any]] = {}
    for raw_target in payload["targets"]:
        if not isinstance(raw_target, dict):
            continue
        family = str(raw_target.get("family") or "").strip()
        target_type = str(raw_target.get("target_type") or "").strip()
        target_id = str(raw_target.get("target_id") or "").strip()
        title = str(raw_target.get("title") or "").strip()
        href = str(raw_target.get("href") or "").strip()
        if not family or not target_type or not target_id or not title or not href.startswith("/"):
            continue
        targets[(family, target_type, target_id)] = {
            "family": family,
            "target_type": target_type,
            "target_id": target_id,
            "title": title,
            "href": href,
            "meta": [
                str(value).strip()
                for value in raw_target.get("meta", [])
                if str(value).strip()
            ]
            if isinstance(raw_target.get("meta"), list)
            else [],
        }
    return targets


class SemanticTokensMixin:
    def resolve_semantic_tokens(
        self,
        markdown: str,
        *,
        doc: DocRecord,
        occurrences_by_doc: dict[str, list[dict[str, Any]]],
    ) -> str:
        if self.public_readonly_scope:
            occurrences_by_doc[doc.doc_id] = []
            return markdown
        occurrences: list[dict[str, Any]] = []

        def replace(token: SemanticTokenOccurrence) -> str:
            if not token.supported:
                return token.raw
            target = self.semantic_token_targets_by_key.get(
                (token.family, token.target_type, token.target_id)
            )
            if target is None:
                return token.raw
            occurrences.append(
                {
                    "source_scope": self.scope_id,
                    "source_doc_id": doc.doc_id,
                    "source_range": token.source_range,
                    "raw": token.raw,
                    "title": token.title,
                    "family": token.family,
                    "target_type": token.target_type,
                    "target_id": token.target_id,
                    "href": target["href"],
                }
            )
            return render_catalogue_token(token, target)

        rendered = replace_catalogue_tokens(
            markdown,
            registry=self.semantic_token_registry,
            replacer=replace,
        )
        occurrences_by_doc[doc.doc_id] = occurrences
        return rendered
