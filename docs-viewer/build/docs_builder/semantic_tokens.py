from __future__ import annotations

import html
import re
from uuid import uuid4
from dataclasses import dataclass, replace
from typing import Any, Callable, Iterable

from .semantic_token_registry import SemanticTokenRegistry
from .summary_formatting import render_summary_inline
from docs_image_tokens import (
    FIGURE_NATURAL_WIDTH_CLASS,
    FIGURE_PLACEMENT_CLASSES,
    decode_image_value,
    encode_image_value,
    parse_image_token,
)
from docs_semantic_source import semantic_source_ranges, source_token_spans


LEXICAL_KEY_PATTERN = re.compile(r"[a-z][a-z0-9-]*")
LEXICAL_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


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
    use_work_title_caption: bool | None = None
    summary: str = ""
    placement: str = ""
    fill_width: bool | None = None
    media_path: str = ""
    alt: str = ""
    caption: str = ""

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


def serialize_catalogue_entry_token(work_id: str) -> str:
    """Bind a generated Catalogue document to its exact Work, without options."""
    if not isinstance(work_id, str) or not re.fullmatch(r"[0-9]{5}", work_id):
        return ""
    return f"[[catalogue:entry:work:{work_id}]]"


def serialize_catalogue_image_token(
    *,
    target_type: str,
    target_id: str,
    use_work_title_caption: Any,
    summary: Any = "",
    placement: Any,
    fill_width: Any = None,
) -> str:
    """Serialize a Work image's caption choice, authored summary and layout."""
    if (
        target_type != "work"
        or not re.fullmatch(r"[0-9]{5}", str(target_id or ""))
        or type(use_work_title_caption) is not bool
        or type(fill_width) is not bool
        or not isinstance(summary, str)
    ):
        return ""
    placement_value = normalize_plain_text(placement, required=True).lower()
    if placement_value not in FIGURE_PLACEMENT_CLASSES:
        return ""
    fields: list[tuple[str, str]] = [
        ("use_work_title_caption", "true" if use_work_title_caption else "false"),
    ]
    summary_text = normalize_summary_text(summary)
    if summary_text:
        fields.append(("summary", summary_text))
    fields.extend((
        ("placement", placement_value),
        ("fill_width", "true" if fill_width else "false"),
    ))
    query = "&".join(
        f"{key}={encode_image_value(value)}" for key, value in fields
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
            or key not in {"use_work_title_caption", "summary", "placement", "fill_width"}
            or key in fields
            or not encoded_value
        ):
            return None
        value = decode_image_value(encoded_value)
        if value is None:
            return None
        fields[key] = value
    required = ("use_work_title_caption", "placement", "fill_width")
    if any(key not in fields for key in required):
        return None
    if any(fields[key] not in {"true", "false"} for key in ("use_work_title_caption", "fill_width")):
        return None
    token = serialize_catalogue_image_token(
        target_type=target_type,
        target_id="00000",
        use_work_title_caption=fields["use_work_title_caption"] == "true",
        summary=fields.get("summary", ""),
        placement=fields["placement"],
        fill_width=fields["fill_width"] == "true",
    )
    if not token:
        return None
    canonical_query = token.partition("|")[2][:-2]
    if canonical_query != raw_query:
        return None
    return {
        "use_work_title_caption": fields["use_work_title_caption"] == "true",
        "summary": normalize_summary_text(fields.get("summary", "")),
        "placement": normalize_plain_text(fields["placement"], required=True),
        "fill_width": fields["fill_width"] == "true",
    }


def parse_semantic_token(
    raw: str,
    *,
    start: int = 0,
    registry: SemanticTokenRegistry | None = None,
) -> SemanticTokenOccurrence | None:
    image = parse_image_token(raw)
    if image is not None:
        return SemanticTokenOccurrence(
            raw=raw, family="image", target_type=image.media_type, target_id=image.media_path,
            title="", start=start, end=start + len(raw), supported=True, presentation="image",
            media_path=image.media_path, alt=image.alt, caption=image.caption, summary=image.summary,
            placement=image.placement, fill_width=image.fill_width,
        )
    if not raw.startswith("[[") or not raw.endswith("]]") or "\n" in raw or "\r" in raw:
        return None
    body = raw[2:-2]
    identity, separator, raw_fields = body.partition("|")
    parts = identity.split(":")
    family = parts[0] if parts else ""
    is_entry = family == "catalogue" and len(parts) == 4 and parts[1] == "entry"
    if is_entry:
        if separator or parts[2] != "work" or not serialize_catalogue_entry_token(parts[3]):
            return None
        definition = registry.family(family) if registry else None
        return SemanticTokenOccurrence(
            raw=raw, family=family, target_type="work", target_id=parts[3], title="",
            start=start, end=start + len(raw),
            supported=definition is not None and definition.target_type("work") is not None,
            presentation="entry",
        )
    is_image = (
        family == "catalogue"
        and len(parts) == 4
        and parts[1] == "image"
    )
    is_media = family == "catalogue" and len(parts) == 4 and parts[1] == "media"
    if not separator or (not is_image and not is_media):
        return None
    target_type = parts[2]
    target_id = parts[3]
    if is_image and (target_type != "work" or not re.fullmatch(r"[0-9]{5}", target_id)):
        return None
    if is_media:
        if target_type == "work":
            if not re.fullmatch(r"[0-9]{5}", target_id):
                return None
        elif target_type == "gallery":
            if not re.fullmatch(r"(?:[0-9]{3}|[1-9][0-9]{3,})", target_id):
                return None
        else:
            return None
    if (
        not LEXICAL_KEY_PATTERN.fullmatch(family)
        or not LEXICAL_KEY_PATTERN.fullmatch(target_type)
        or not LEXICAL_ID_PATTERN.fullmatch(target_id)
    ):
        return None
    image_fields = (
        parse_catalogue_image_fields(raw_fields, target_type=target_type)
        if is_image
        else None
    )
    title = "" if is_image else unescape_semantic_token_title(raw_fields)
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
        presentation="image" if is_image else "media",
        use_work_title_caption=image_fields["use_work_title_caption"] if image_fields else None,
        summary=image_fields["summary"] if image_fields else "",
        placement=image_fields["placement"] if image_fields else "",
        fill_width=image_fields["fill_width"] if image_fields else None,
    )


def parse_catalogue_token(
    raw: str,
    *,
    start: int = 0,
    registry: SemanticTokenRegistry | None = None,
) -> SemanticTokenOccurrence | None:
    token = parse_semantic_token(raw, start=start, registry=registry)
    return token if token is not None and token.family == "catalogue" else None


def semantic_token_text_ranges(markdown: str) -> Iterable[tuple[int, int]]:
    return semantic_source_ranges(markdown, parse_token=parse_semantic_token)


def parse_semantic_tokens(
    markdown: str,
    *,
    registry: SemanticTokenRegistry | None,
) -> list[SemanticTokenOccurrence]:
    return [
        replace(token, start=start, end=end)
        for start, end, token in source_token_spans(
            markdown, lambda raw: parse_semantic_token(raw, registry=registry),
        )
    ]


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


def catalogue_reference(token: SemanticTokenOccurrence, reference_id: str) -> dict[str, Any]:
    """Carry only the occurrence's authored choices into Working output."""
    options: dict[str, Any] = {}
    if token.presentation == "image":
        options = {
            "use_work_title_caption": token.use_work_title_caption,
            "summary_html": render_summary_inline(token.summary),
            "placement": token.placement,
            "fill_width": token.fill_width,
        }
    elif token.presentation == "media":
        options["label"] = token.title
    return {
        "reference_id": reference_id,
        "target": {"kind": f"catalogue-{token.target_type}", "id": token.target_id},
        "presentation": token.presentation,
        "options": options,
    }


def catalogue_reference_slot(reference: dict[str, Any]) -> str:
    """The same explicit slot is filled by live or static presentation owners."""
    tag = "span" if reference["presentation"] == "media" else "div"
    return f'<{tag} data-docs-catalogue-ref="{reference["reference_id"]}"></{tag}>'


def render_image_reference(token: SemanticTokenOccurrence, src: str) -> str:
    """Render static Docs-owned image presentation without media writes or lookups."""
    modifiers = [FIGURE_PLACEMENT_CLASSES[token.placement]]
    if not token.fill_width:
        modifiers.append(FIGURE_NATURAL_WIDTH_CLASS)
    blocks = []
    if token.caption:
        blocks.append(f'<span class="docsViewerFigure__caption">{html.escape(token.caption)}</span>')
    if token.summary:
        blocks.append(f'<span class="docsViewerFigure__summary">{render_summary_inline(token.summary)}</span>')
    caption = f'<figcaption>{"".join(blocks)}</figcaption>' if blocks else ""
    return (
        f'<figure class="docsViewerFigure {" ".join(modifiers)}">'
        f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(token.alt, quote=True)}">'
        f'{caption}</figure>'
    )


class SemanticTokensMixin:
    def restore_semantic_media_html(self, content_html: str) -> str:
        """Restore built fragments after Markdown so authored labels stay literal."""
        for marker, fragment in self._semantic_media_html.items():
            content_html = content_html.replace(marker, fragment)
        return content_html

    def resolve_semantic_tokens(
        self,
        markdown: str,
        *, document_id: str = "",
    ) -> str:
        """Render media without writes; Entry needs its exact Catalogue document ID."""
        self._semantic_media_html: dict[str, str] = {}
        self.catalogue_references: list[dict[str, Any]] = []
        entry_seen = False

        def replace(token: SemanticTokenOccurrence) -> str:
            nonlocal entry_seen
            if not token.supported:
                return token.raw
            if token.family == "image":
                fragment = render_image_reference(
                    token, self.image_token_media_url(token.media_path),
                )
            else:
                if token.presentation == "entry":
                    if getattr(self, "collection_id", "") != "catalogue" or token.target_id != document_id or entry_seen:
                        raise ValueError("Catalogue Entry requires one token matching its Catalogue document identity")
                    entry_seen = True
                reference = catalogue_reference(token, f"c{len(self.catalogue_references) + 1}")
                self.catalogue_references.append(reference)
                fragment = catalogue_reference_slot(reference)
            marker_id = uuid4().hex
            # Comments start HTML blocks at line beginnings; inline references must not.
            marker = (
                f"<!--semantic-media-{marker_id}-->"
                if token.presentation in {"image", "entry"}
                else f'<span data-semantic-media-fragment="{marker_id}"></span>'
            )
            self._semantic_media_html[marker] = fragment
            return marker

        rendered = replace_semantic_tokens(
            markdown,
            registry=self.semantic_token_registry,
            replacer=replace,
        )
        return rendered
