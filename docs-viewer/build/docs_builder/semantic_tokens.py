from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import quote, unquote_to_bytes, urlsplit

from .common import read_json
from .semantic_token_registry import SemanticTokenRegistry
from .semantic_target_lookup import positive_integer, primary_image_settings
from .source import DocRecord
from docs_staged_media_fragments import (
    FIGURE_NATURAL_WIDTH_CLASS,
    FIGURE_PLACEMENT_CLASSES,
    validate_figure_presentation,
)


LEXICAL_KEY_PATTERN = re.compile(r"[a-z][a-z0-9-]*")
LEXICAL_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
FENCE_PATTERN = re.compile(r"\A {0,3}(`{3,}|~{3,})")
SEMANTIC_TOKEN_TARGET_LOOKUP_SCHEMA_VERSION = "docs_semantic_token_target_lookup_v2"
SEMANTIC_TOKEN_TARGET_LOOKUP_PATH = Path(
    "docs-viewer/data/generated/semantic-tokens/target-lookup.json"
)
CATALOGUE_WORK_DETAILS_SOURCE_DIR = Path(
    "studio/data/canonical/catalogue/work_details"
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
    presentation: str = "text"
    alt: str = ""
    caption: str = ""
    summary: str = ""
    placement: str = ""
    fill_width: bool | None = None
    detail_id: str = ""

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
) -> str:
    if (
        not LEXICAL_KEY_PATTERN.fullmatch(str(target_type or ""))
        or not LEXICAL_ID_PATTERN.fullmatch(str(target_id or ""))
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
    return f"[[catalogue:image:{target_type}:{target_id}|{query}]]"


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


def parse_catalogue_token(
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
    is_image = len(parts) == 4 and parts[1] == "image"
    if not separator or (len(parts) != 3 and not is_image):
        return None
    family = parts[0]
    target_type = parts[-2]
    target_id = parts[-1]
    if (
        family != "catalogue"
        or not LEXICAL_KEY_PATTERN.fullmatch(family)
        or not LEXICAL_KEY_PATTERN.fullmatch(target_type)
        or not LEXICAL_ID_PATTERN.fullmatch(target_id)
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
        presentation="image" if is_image else "text",
        alt=image_fields["alt"] if image_fields else "",
        caption=image_fields["caption"] if image_fields else "",
        summary=image_fields["summary"] if image_fields else "",
        placement=image_fields["placement"] if image_fields else "",
        fill_width=image_fields["fill_width"] if image_fields else None,
        detail_id=image_fields["detail_id"] if image_fields else "",
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
    if token.presentation != "image":
        return (
            f'<a href="{html.escape(href, quote=True)}" {attrs}>'
            f"{html.escape(token.title)}</a>"
        )
    image = target.get("image") if isinstance(target.get("image"), dict) else {}
    src = browser_safe_image_src(image.get("src"))
    if not src:
        return token.raw
    link_attrs = f'href="{html.escape(href, quote=True)}" {attrs}'
    image_html = (
        f'<img src="{html.escape(src, quote=True)}" '
        f'alt="{html.escape(token.alt, quote=True)}">'
    )
    if not token.caption:
        return (
            f'<a class="docsViewerCatalogueImageLink" {link_attrs}>'
            f"{image_html}</a>"
        )
    modifiers = [FIGURE_PLACEMENT_CLASSES[token.placement]]
    if not token.fill_width:
        modifiers.append(FIGURE_NATURAL_WIDTH_CLASS)
    summary_html = (
        f'\n    <span class="docsViewerFigure__summary">'
        f'{html.escape(token.summary, quote=False)}</span>'
        if token.summary
        else ""
    )
    return (
        f'<figure class="docsViewerFigure {" ".join(modifiers)}">\n'
        f'  <a class="docsViewerFigure__imageLink" {link_attrs}>{image_html}</a>\n'
        "  <figcaption>\n"
        f'    <span class="docsViewerFigure__caption">'
        f'{html.escape(token.caption, quote=False)}</span>'
        f"{summary_html}\n"
        "  </figcaption>\n"
        "</figure>"
    )


def resolve_catalogue_image_target(
    repo_root: Path,
    token: SemanticTokenOccurrence,
    target: dict[str, Any],
) -> dict[str, Any] | None:
    if token.presentation != "image":
        return target
    if not token.detail_id:
        return target if target.get("image") else None
    if token.target_type != "work":
        return None
    payload = read_json(
        repo_root
        / CATALOGUE_WORK_DETAILS_SOURCE_DIR
        / f"{token.target_id}.json"
    )
    if not isinstance(payload, dict):
        return None
    header = payload.get("header") if isinstance(payload.get("header"), dict) else {}
    source_work_id = str(payload.get("work_id") or header.get("work_id") or "").strip()
    if source_work_id != token.target_id:
        return None
    detail_uid = f"{token.target_id}-{token.detail_id}"
    detail_record: dict[str, Any] | None = None
    sections = payload.get("detail_sections")
    if not isinstance(sections, list):
        return None
    for section in sections:
        details = section.get("details") if isinstance(section, dict) else None
        if not isinstance(details, list):
            continue
        for raw_detail in details:
            if not isinstance(raw_detail, dict):
                continue
            if str(raw_detail.get("detail_uid") or "").strip() == detail_uid:
                detail_record = raw_detail
                break
        if detail_record is not None:
            break
    if (
        detail_record is None
        or str(detail_record.get("detail_id") or "").strip() != token.detail_id
        or not str(detail_record.get("project_filename") or "").strip()
        or positive_integer(detail_record.get("media_version")) is None
        or positive_integer(detail_record.get("width_px")) is None
        or positive_integer(detail_record.get("height_px")) is None
    ):
        return None
    try:
        settings = primary_image_settings(
            repo_root,
            media_path_key="image_work_details",
        )
    except ValueError:
        return None
    filename = (
        f"{detail_uid}-{settings['suffix']}-{settings['width']}."
        f"{settings['format']}"
    )
    src = browser_safe_image_src(
        f"{settings['base']}{settings['path']}/{quote(filename)}"
        f"?v={positive_integer(detail_record.get('media_version'))}"
    )
    if not src:
        return None
    resolved = dict(target)
    resolved["href"] = (
        f"/work-details/?detail={quote(detail_uid)}"
        f"&from_work={quote(token.target_id)}"
    )
    resolved["image"] = {"src": src}
    return resolved


def browser_safe_image_src(value: Any) -> str:
    src = str(value or "").strip()
    if not src:
        return ""
    if src.startswith("/") and not src.startswith("//"):
        return src
    parsed = urlsplit(src)
    if (
        parsed.scheme == "https"
        and parsed.netloc
        and parsed.username is None
        and parsed.password is None
    ):
        return src
    return ""


def load_semantic_token_target_records(
    repo_root: Path,
) -> dict[tuple[str, str, str], dict[str, Any]]:
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
        if not family or not target_type or not target_id or not title:
            continue
        target = {
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
        raw_image = raw_target.get("image")
        image_src = (
            browser_safe_image_src(raw_image.get("src"))
            if isinstance(raw_image, dict)
            else ""
        )
        if image_src:
            target["image"] = {"src": image_src}
        if raw_target.get("has_details") is True:
            target["has_details"] = True
        targets[(family, target_type, target_id)] = target
    return targets


def load_semantic_token_targets(repo_root: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {
        key: target
        for key, target in load_semantic_token_target_records(repo_root).items()
        if str(target.get("href") or "").startswith("/")
    }


class SemanticTokensMixin:
    def resolve_semantic_tokens(
        self,
        markdown: str,
        *,
        doc: DocRecord,
        occurrences_by_doc: dict[str, list[dict[str, Any]]],
    ) -> str:
        occurrences: list[dict[str, Any]] = []

        def replace(token: SemanticTokenOccurrence) -> str:
            if not token.supported:
                return token.raw
            target = self.semantic_token_targets_by_key.get(
                (token.family, token.target_type, token.target_id)
            )
            if target is None:
                return token.raw
            resolved_target = (
                resolve_catalogue_image_target(self.repo_root, token, target)
                if token.presentation == "image"
                else target
            )
            if resolved_target is None:
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
                    "href": resolved_target["href"],
                }
            )
            return render_catalogue_token(token, resolved_target)

        rendered = replace_catalogue_tokens(
            markdown,
            registry=self.semantic_token_registry,
            replacer=replace,
        )
        occurrences_by_doc[doc.doc_id] = occurrences
        return rendered
