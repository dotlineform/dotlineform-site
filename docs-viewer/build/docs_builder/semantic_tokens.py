from __future__ import annotations

import html
import re
from uuid import uuid4
from dataclasses import dataclass, replace
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import quote, unquote_to_bytes

from .semantic_token_registry import SemanticTokenRegistry
from .source import DocRecord
from docs_document_subjects import parse_detail_uid
from docs_staged_media_fragments import (
    FIGURE_NATURAL_WIDTH_CLASS,
    FIGURE_PLACEMENT_CLASSES,
    validate_figure_presentation,
)


LEXICAL_KEY_PATTERN = re.compile(r"[a-z][a-z0-9-]*")
LEXICAL_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
FENCE_PATTERN = re.compile(r"\A {0,3}(`{3,}|~{3,})")



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
    presentation: str
    alt: str = ""
    caption: str = ""
    summary: str = ""
    placement: str = ""
    fill_width: bool | None = None
    detail_id: str = ""
    use_document_subject: bool = False

    @property
    def source_range(self) -> dict[str, int]:
        return {"start": self.start, "end": self.end}


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


def normalize_plain_text(value: Any, *, required: bool) -> str:
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split())
    return text if text or not required else ""


def normalize_summary_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(" ".join(line.split()) for line in normalized.split("\n")).strip()


def encode_catalogue_image_value(value: str) -> str:
    return quote(value, safe="-._~")


def decode_catalogue_image_value(value: str) -> str | None:
    if re.search(r"%(?![0-9A-Fa-f]{2})", value):
        return None
    try:
        decoded = unquote_to_bytes(value).decode("utf-8")
    except UnicodeDecodeError:
        return None
    return decoded if encode_catalogue_image_value(decoded) == value else None


def normalize_catalogue_detail_id(value: Any) -> str | None:
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return None
    raw = str(value).strip()
    if not re.fullmatch(r"\d+", raw):
        return None
    number = int(raw)
    if number < 1:
        return None
    return str(number).zfill(3)


def serialize_catalogue_image_token(
    *,
    target_type: str,
    target_id: str,
    alt: Any,
    caption: Any = "",
    summary: Any = "",
    placement: Any = "",
    fill_width: Any = None,
    detail_id: Any = "",
    use_document_subject: bool = False,
) -> str:
    if (
        target_type != "work"
        or (not use_document_subject and not re.fullmatch(r"[0-9]{5}", str(target_id or "")))
    ):
        return ""
    alt_text = normalize_plain_text(alt, required=True)
    if not alt_text:
        return ""
    detail_id_value = normalize_catalogue_detail_id(detail_id)
    if detail_id_value is None or (detail_id_value and target_type != "work"):
        return ""
    caption_text = normalize_plain_text(caption, required=False)
    fields: list[tuple[str, str]] = [("alt", alt_text)]
    if detail_id_value:
        fields.append(("detail_id", detail_id_value))
    if caption_text:
        try:
            caption_text, summary_text, placement_value, fill_width_value = (
                validate_figure_presentation(
                    caption,
                    summary,
                    placement,
                    fill_width,
                )
            )
        except ValueError:
            return ""
        fields.append(("caption", caption_text))
        if summary_text:
            fields.append(("summary", summary_text))
        fields.extend(
            [
                ("placement", placement_value),
                ("fill_width", "true" if fill_width_value else "false"),
            ]
        )
    elif normalize_summary_text(summary) or normalize_plain_text(placement, required=False):
        return ""
    elif fill_width is not None:
        return ""
    query = "&".join(
        f"{key}={encode_catalogue_image_value(value)}" for key, value in fields
    )
    identity = target_type if use_document_subject else f"{target_type}:{target_id}"
    return f"[[catalogue:image:{identity}|{query}]]"


def parse_catalogue_image_fields(raw_query: str, *, target_type: str) -> dict[str, Any] | None:
    if not raw_query:
        return None
    fields: dict[str, str] = {}
    for pair in raw_query.split("&"):
        key, separator, encoded_value = pair.partition("=")
        if (
            not separator
            or key not in {"alt", "detail_id", "caption", "summary", "placement", "fill_width"}
            or key in fields
            or not encoded_value
        ):
            return None
        value = decode_catalogue_image_value(encoded_value)
        if value is None:
            return None
        fields[key] = value
    alt = fields.get("alt", "")
    caption = fields.get("caption", "")
    if not alt:
        return None
    fill_width: bool | None = None
    if "fill_width" in fields:
        if fields["fill_width"] not in {"true", "false"}:
            return None
        fill_width = fields["fill_width"] == "true"
    token = serialize_catalogue_image_token(
        target_type=target_type,
        target_id="00000",
        alt=alt,
        detail_id=fields.get("detail_id", ""),
        caption=caption,
        summary=fields.get("summary", ""),
        placement=fields.get("placement", ""),
        fill_width=fill_width,
    )
    if not token:
        return None
    canonical_query = token.partition("|")[2][:-2]
    if canonical_query != raw_query:
        return None
    return {
        "alt": normalize_plain_text(alt, required=True),
        "caption": normalize_plain_text(caption, required=False),
        "summary": normalize_summary_text(fields.get("summary", "")),
        "placement": normalize_plain_text(fields.get("placement", ""), required=False),
        "fill_width": fill_width,
        "detail_id": normalize_catalogue_detail_id(fields.get("detail_id", "")) or "",
    }


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


def parse_semantic_token(
    raw: str,
    *,
    start: int = 0,
    registry: SemanticTokenRegistry | None = None,
) -> SemanticTokenOccurrence | None:
    if not raw.startswith("[[") or not raw.endswith("]]") or "\n" in raw or "\r" in raw:
        return None
    body = raw[2:-2]
    identity, separator, raw_fields = body.partition("|")
    parts = identity.split(":")
    family = parts[0] if parts else ""
    is_image = (
        family == "catalogue"
        and len(parts) in {3, 4}
        and parts[1] == "image"
    )
    is_media = family == "catalogue" and len(parts) in {3, 4, 5} and parts[1] == "media"
    if not separator or (not is_image and not is_media):
        return None
    target_type = parts[2]
    use_document_subject = len(parts) == 3
    target_id = "" if use_document_subject else parts[3]
    media_detail_id = parts[4] if len(parts) == 5 else ""
    if is_image and (target_type != "work" or (not use_document_subject and not re.fullmatch(r"[0-9]{5}", target_id))):
        return None
    if is_media and use_document_subject:
        if target_type not in {"work", "series", "detail"}:
            return None
    elif is_media:
        if target_type == "work":
            if not re.fullmatch(r"[0-9]{5}", target_id):
                return None
        elif target_type != "series" or not re.fullmatch(r"[0-9]{3}", target_id) or len(parts) == 5:
            return None
        if len(parts) == 5 and (not media_detail_id or normalize_catalogue_detail_id(media_detail_id) != media_detail_id):
            return None
    if (
        not LEXICAL_KEY_PATTERN.fullmatch(family)
        or not LEXICAL_KEY_PATTERN.fullmatch(target_type)
        or (not use_document_subject and not LEXICAL_ID_PATTERN.fullmatch(target_id))
    ):
        return None
    image_fields = (
        parse_catalogue_image_fields(raw_fields, target_type=target_type)
        if is_image
        else None
    )
    title = (
        image_fields["caption"] or image_fields["alt"]
        if image_fields is not None
        else unescape_semantic_token_title(raw_fields)
    )
    if title is None or (is_image and image_fields is None):
        return None
    family_definition = registry.family(family) if registry else None
    registry_type = "work" if use_document_subject and target_type == "detail" else target_type
    target_definition = family_definition.target_type(registry_type) if family_definition else None
    supported = target_definition is not None
    if supported and not use_document_subject and not re.fullmatch(target_definition.id_policy.canonical_pattern, target_id):
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
        presentation="image" if is_image else "media",
        alt=image_fields["alt"] if image_fields else "",
        caption=image_fields["caption"] if image_fields else "",
        summary=image_fields["summary"] if image_fields else "",
        placement=image_fields["placement"] if image_fields else "",
        fill_width=image_fields["fill_width"] if image_fields else None,
        detail_id=image_fields["detail_id"] if image_fields else media_detail_id,
        use_document_subject=use_document_subject,
    )


def resolve_catalogue_token_subject(
    token: SemanticTokenOccurrence, front_matter: Mapping[str, Any],
) -> SemanticTokenOccurrence:
    """Resolve an abbreviated identity, retaining its authored token and ranges."""
    if not token.use_document_subject:
        return token
    if token.target_type == "detail":
        work_id, detail_id = parse_detail_uid(front_matter["detail_uid"])
        return replace(token, target_type="work", target_id=work_id, detail_id=detail_id)
    return replace(token, target_id=front_matter[f"{token.target_type}_id"])


def parse_catalogue_token(
    raw: str,
    *,
    start: int = 0,
    registry: SemanticTokenRegistry | None = None,
) -> SemanticTokenOccurrence | None:
    token = parse_semantic_token(raw, start=start, registry=registry)
    return token if token is not None and token.family == "catalogue" else None


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


def parse_semantic_tokens(
    markdown: str,
    *,
    registry: SemanticTokenRegistry | None,
) -> list[SemanticTokenOccurrence]:
    if "[[" not in markdown:
        return []
    tokens: list[SemanticTokenOccurrence] = []
    for range_start, range_end in semantic_token_text_ranges(markdown):
        index = range_start
        while index < range_end:
            opening = markdown.find("[[", index, range_end)
            if opening < 0:
                break
            closing = token_closing_index(markdown, opening + 2)
            if closing < 0 or closing + 2 > range_end:
                break
            raw = markdown[opening:closing + 2]
            token = parse_semantic_token(raw, start=opening, registry=registry)
            if token is not None:
                tokens.append(token)
            index = closing + 2
    return tokens


def parse_catalogue_tokens(
    markdown: str,
    *,
    registry: SemanticTokenRegistry | None,
) -> list[SemanticTokenOccurrence]:
    return [
        token
        for token in parse_semantic_tokens(markdown, registry=registry)
        if token.family == "catalogue"
    ]


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


def replace_semantic_tokens(
    markdown: str,
    *,
    registry: SemanticTokenRegistry | None,
    replacer: Callable[[SemanticTokenOccurrence], str],
) -> str:
    tokens = parse_semantic_tokens(markdown, registry=registry)
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


def render_catalogue_media_reference(token: SemanticTokenOccurrence) -> str:
    """Retain only authored text and exact Catalogue identity for runtime resolution."""
    kind = "catalogue-work-detail" if token.detail_id else f"catalogue-{token.target_type}"
    identity = f"{token.target_id}-{token.detail_id}" if token.detail_id else token.target_id
    attrs = (
        f'data-docs-content-detail="media" data-docs-media-kind="{kind}" '
        f'data-docs-media-id="{html.escape(identity, quote=True)}"'
    )
    if token.detail_id:
        attrs += f' data-docs-media-work-id="{html.escape(token.target_id, quote=True)}"'
    if token.presentation == "media":
        return (
            f'<span {attrs}><button type="button" class="docsViewer__mediaTextLink" data-docs-media-open>'
            f'{html.escape(token.title)}</button></span>'
        )
    image_class = "docsViewerFigure__imageLink" if token.caption else "docsViewerCatalogueImageLink"
    opener = (
        f'<button type="button" class="docsViewer__mediaImageLink {image_class}" data-docs-media-open '
        f'aria-label="{html.escape("Open " + token.alt + " in Media View", quote=True)}">'
        f'<img data-docs-media-image alt="{html.escape(token.alt, quote=True)}" hidden>'
        f'<span data-docs-media-placeholder>{html.escape(token.alt)}</span></button>'
    )
    if not token.caption:
        return f'<span {attrs}>{opener}</span>'
    modifiers = [FIGURE_PLACEMENT_CLASSES[token.placement]]
    if not token.fill_width:
        modifiers.append(FIGURE_NATURAL_WIDTH_CLASS)
    summary = f'<span class="docsViewerFigure__summary">{html.escape(token.summary)}</span>' if token.summary else ""
    return (
        f'<figure class="docsViewerFigure {" ".join(modifiers)}" {attrs}>{opener}'
        f'<figcaption><span class="docsViewerFigure__caption">{html.escape(token.caption)}</span>'
        f'{summary}</figcaption></figure>'
    )


class SemanticTokensMixin:
    def restore_catalogue_media_html(self, content_html: str) -> str:
        """Restore built fragments after Markdown so authored labels stay literal."""
        for marker, fragment in self._catalogue_media_html.items():
            content_html = content_html.replace(marker, fragment)
        return content_html

    def resolve_semantic_tokens(
        self,
        markdown: str,
        *,
        doc: DocRecord,
        occurrences_by_doc: dict[str, list[dict[str, Any]]],
    ) -> str:
        occurrences: list[dict[str, Any]] = []
        self._catalogue_media_html: dict[str, str] = {}

        def replace(token: SemanticTokenOccurrence) -> str:
            if not token.supported:
                return token.raw
            token = resolve_catalogue_token_subject(token, doc.front_matter)
            occurrences.append({
                "source_stage": self.config.stage, "source_doc_id": doc.doc_id,
                "source_range": token.source_range, "raw": token.raw, "title": token.title,
                "family": token.family, "target_type": token.target_type, "target_id": token.target_id,
                "detail_id": token.detail_id, "href": "",
            })
            fragment = render_catalogue_media_reference(token)
            marker_id = uuid4().hex
            # Comments start HTML blocks at line beginnings; inline references must not.
            marker = (
                f"<!--catalogue-media-{marker_id}-->"
                if token.presentation == "image" and token.caption
                else f'<span data-catalogue-media-fragment="{marker_id}"></span>'
            )
            self._catalogue_media_html[marker] = fragment
            return marker

        rendered = replace_semantic_tokens(
            markdown,
            registry=self.semantic_token_registry,
            replacer=replace,
        )
        occurrences_by_doc[doc.doc_id] = occurrences
        return rendered
