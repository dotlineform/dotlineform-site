"""Shared active-source boundaries for semantic rendering and media discovery."""

from __future__ import annotations

import re
from typing import Any, Callable, Iterable


def token_closing_index(text: str, start: int) -> int:
    index = start
    while index < len(text) - 1:
        if text[index] == "\\":
            index += 2
        elif text[index:index + 2] == "]]":
            return index
        else:
            index += 1
    return -1


def token_opening_is_escaped(text: str, start: int) -> bool:
    escapes = re.search(r"\\+$", text[:start])
    return bool(escapes and len(escapes.group()) % 2)


def _context_source(text: str, parse_token: Callable[[str], Any] | None) -> str:
    if parse_token is None:
        return text
    parts: list[str] = []
    offset = index = 0
    while (opening := text.find("[[", index)) >= 0:
        closing = token_closing_index(text, opening + 2)
        if closing < 0:
            break
        end = closing + 2
        if not token_opening_is_escaped(text, opening) and parse_token(text[opening:end]) is not None:
            parts.extend((text[offset:opening], "x" * (end - opening)))
            offset = end
        index = end
    return "".join(parts) + text[offset:]


def semantic_source_ranges(text: str, *, parse_token: Callable[[str], Any] | None = None) -> Iterable[tuple[int, int]]:
    """Yield active spans, excluding comments, pre, inline/indented/fenced code."""
    source = _context_source(text, parse_token)
    offset = 0
    fence_character = ""
    fence_length = 0
    literal = ""
    for line in re.findall(r"[^\n]*\n|[^\n]+$", source):
        fence = re.match(r" {0,3}(`{3,}|~{3,})", line)
        if fence and not literal:
            marker = fence.group(1)
            if fence_character:
                if marker[0] == fence_character and len(marker) >= fence_length and re.fullmatch(r"[ \t\r\n]*", line[fence.end():]):
                    fence_character = ""
            else:
                fence_character, fence_length = marker[0], len(marker)
        elif not fence_character and (literal or not re.match(r"(?: {4}|\t)", line)):
            index, end = offset, offset + len(line)
            while index < end:
                if literal:
                    close = re.search(r"-->" if literal == "comment" else r"</pre\s*>", source[index:end], re.IGNORECASE)
                    if close is None:
                        break
                    index += close.end()
                    literal = ""
                    continue
                marker = re.search(r"`+|<!--|<pre\b", source[index:end], re.IGNORECASE)
                if marker is None:
                    yield index, end
                    break
                opening = index + marker.start()
                if opening > index:
                    yield index, opening
                value = marker.group()
                if value.startswith("`"):
                    close = source.find(value, opening + len(value), end)
                    if close < 0:
                        break
                    index = close + len(value)
                else:
                    index = opening + len(value)
                    literal = "comment" if value == "<!--" else "pre"
        offset += len(line)


def source_token_spans(text: str, parse_token: Callable[[str], Any]) -> Iterable[tuple[int, int, Any]]:
    """Yield parsed tokens and exact half-open ranges in active source only."""
    for start, end in semantic_source_ranges(text, parse_token=parse_token):
        index = start
        while (opening := text.find("[[", index, end)) >= 0:
            if token_opening_is_escaped(text, opening):
                index = opening + 2
                continue
            closing = token_closing_index(text, opening + 2)
            if closing < 0 or closing + 2 > end:
                break
            token = parse_token(text[opening:closing + 2])
            if token is not None:
                yield opening, closing + 2, token
            index = closing + 2
