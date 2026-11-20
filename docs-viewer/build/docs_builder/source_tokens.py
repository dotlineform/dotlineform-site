from __future__ import annotations

import html
import re
from uuid import uuid4
from dataclasses import dataclass, replace
from typing import Any, Callable, Iterable

from .summary_formatting import render_summary_inline, render_summary_paragraphs
from docs_image_tokens import (
    FIGURE_NATURAL_WIDTH_CLASS,
    FIGURE_PLACEMENT_CLASSES,
    decode_image_value,
    encode_image_value,
    parse_image_token,
)
from docs_source_token_scan import active_source_ranges, source_token_spans


WORK_ID_PATTERN = re.compile(r"[0-9]{5}")
CATALOGUE_TARGET_ID_PATTERNS = {
    "work": WORK_ID_PATTERN,
    "gallery": re.compile(r"(?:[0-9]{3}|[1-9][0-9]{3,})"),
}


@dataclass(frozen=True)
class SourceTokenOccurrence:
    raw: str
    family: str
    target_type: str
    target_id: str
    title: str
    start: int
    end: int
    presentation: str
    visible: bool = True
    gallery_id: str = ""
    gallery_label: str = ""
    use_work_title_caption: bool | None = None
    summary: str = ""
    placement: str = ""
    fill_width: bool | None = None
    left_size: str = ""
    media_path: str = ""
    alt: str = ""
    caption: str = ""

    @property
    def source_range(self) -> dict[str, int]:
        return {"start": self.start, "end": self.end}


def unescape_catalogue_label(value: str) -> str | None:
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


def serialize_catalogue_image_token(
    *,
    target_type: str,
    target_id: str,
    use_work_title_caption: Any,
    summary: Any = "",
    placement: Any,
    fill_width: Any = None,
    left_size: str = "",
    gallery_id: str = "",
    gallery_label: str = "",
) -> str:
    """Serialize a Work image's caption choice, authored summary and layout."""
    if (
        target_type != "work"
        or not WORK_ID_PATTERN.fullmatch(str(target_id or ""))
        or type(use_work_title_caption) is not bool
        or type(fill_width) is not bool
        or not isinstance(summary, str)
    ):
        return ""
    placement_value = normalize_plain_text(placement, required=True).lower()
    if placement_value not in FIGURE_PLACEMENT_CLASSES:
        return ""
    if left_size != "" and (
        left_size not in ("third", "thumbnail")
        or placement_value not in ("left", "wrap-left")
        or (left_size == "thumbnail" and fill_width)
    ):
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
    if left_size:
        fields.append(("left_size", left_size))
    identity = f"work:{target_id}"
    if gallery_id:
        if not CATALOGUE_TARGET_ID_PATTERNS["gallery"].fullmatch(gallery_id) or not gallery_label.strip() or re.search(r"[\r\n]", gallery_label):
            return ""
        identity += f":gallery:{gallery_id}"
        fields.append(("gallery_label", gallery_label))
    query = "&".join(
        f"{key}={encode_image_value(value)}" for key, value in fields
    )
    return f"[[catalogue:image:{identity}|{query}]]"


def parse_catalogue_image_fields(raw_query: str, *, target_id: str, gallery_id: str) -> dict[str, Any] | None:
    if not raw_query:
        return None
    fields: dict[str, str] = {}
    for pair in raw_query.split("&"):
        key, separator, encoded_value = pair.partition("=")
        if (
            not separator
            or key not in {"use_work_title_caption", "summary", "placement", "fill_width", "left_size", "gallery_label"}
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
        target_type="work", target_id=target_id, gallery_id=gallery_id, gallery_label=fields.get("gallery_label", ""),
        use_work_title_caption=fields["use_work_title_caption"] == "true",
        summary=fields.get("summary", ""),
        placement=fields["placement"],
        fill_width=fields["fill_width"] == "true",
        left_size=fields.get("left_size", ""),
    )
    if not token:
        return None
    canonical_query = token.partition("|")[2][:-2]
    if canonical_query != raw_query:
        return None
    return {
        "gallery_label": fields.get("gallery_label", ""),
        "use_work_title_caption": fields["use_work_title_caption"] == "true",
        "summary": normalize_summary_text(fields.get("summary", "")),
        "placement": normalize_plain_text(fields["placement"], required=True),
        "fill_width": fields["fill_width"] == "true",
        "left_size": fields.get("left_size", ""),
    }


def parse_source_token(raw: str) -> SourceTokenOccurrence | None:
    image = parse_image_token(raw)
    if image is not None:
        return SourceTokenOccurrence(
            raw=raw, family="image", target_type=image.media_type, target_id=image.media_path,
            title="", start=0, end=len(raw), presentation="image",
            media_path=image.media_path, alt=image.alt, caption=image.caption, summary=image.summary,
            placement=image.placement, fill_width=image.fill_width,
        )
    if not raw.startswith("[[") or not raw.endswith("]]") or "\n" in raw or "\r" in raw:
        return None
    body = raw[2:-2]
    identity, separator, raw_fields = body.partition("|")
    parts = identity.split(":")
    if len(parts) < 4 or parts[0] != "catalogue":
        return None
    family, presentation, target_type, target_id = parts[:4]
    if len(parts) == 4 and presentation == "entry":
        if separator or target_type != "work" or not WORK_ID_PATTERN.fullmatch(target_id):
            return None
        return SourceTokenOccurrence(
            raw=raw, family=family, target_type=target_type, target_id=target_id, title="",
            start=0, end=len(raw), presentation=presentation,
        )
    visible = parts[-1] != "visible=false"
    if presentation == "media" and (not visible or (target_type == "gallery" and parts[-1] == "visible=true")):
        parts.pop()
    gallery_id = ""
    if len(parts) == 6 and target_type == "work" and parts[4] == "gallery" and CATALOGUE_TARGET_ID_PATTERNS["gallery"].fullmatch(parts[5]):
        gallery_id = parts[5]
    elif len(parts) != 4:
        return None
    is_image = presentation == "image" and target_type == "work"
    is_media = presentation == "media"
    if not separator or (not is_image and not is_media):
        return None
    id_pattern = CATALOGUE_TARGET_ID_PATTERNS.get(target_type)
    if id_pattern is None or not id_pattern.fullmatch(target_id):
        return None
    image_fields = (
        parse_catalogue_image_fields(raw_fields, target_id=target_id, gallery_id=gallery_id)
        if is_image
        else None
    )
    title = "" if is_image else unescape_catalogue_label(raw_fields)
    if title is None or (is_image and image_fields is None):
        return None
    return SourceTokenOccurrence(
        raw=raw,
        family=family,
        target_type=target_type,
        target_id=target_id,
        title=title,
        start=0,
        end=len(raw),
        presentation=presentation,
        visible=visible, gallery_id=gallery_id, gallery_label=image_fields["gallery_label"] if image_fields else "",
        use_work_title_caption=image_fields["use_work_title_caption"] if image_fields else None,
        summary=image_fields["summary"] if image_fields else "",
        placement=image_fields["placement"] if image_fields else "",
        fill_width=image_fields["fill_width"] if image_fields else None,
        left_size=image_fields["left_size"] if image_fields else "",
    )


def source_token_text_ranges(markdown: str) -> Iterable[tuple[int, int]]:
    return active_source_ranges(markdown, parse_token=parse_source_token)


def parse_source_tokens(markdown: str) -> list[SourceTokenOccurrence]:
    return [
        replace(token, start=start, end=end)
        for start, end, token in source_token_spans(markdown, parse_source_token)
    ]


def replace_source_tokens(
    markdown: str,
    *,
    replacer: Callable[[SourceTokenOccurrence], str],
) -> str:
    tokens = parse_source_tokens(markdown)
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


def catalogue_reference(token: SourceTokenOccurrence, reference_id: str) -> dict[str, Any]:
    """Carry only the occurrence's authored choices into Working output."""
    options: dict[str, Any] = {}
    if token.presentation == "image":
        options = {
            "use_work_title_caption": token.use_work_title_caption,
            "summary_html": render_summary_inline(token.summary),
            "placement": token.placement,
            "fill_width": token.fill_width,
        }
        if token.left_size:
            options["left_size"] = token.left_size
        if token.gallery_id:
            options["gallery_label"] = token.gallery_label
    elif token.presentation == "media":
        options["label"] = token.title
    return {
        "reference_id": reference_id,
        "target": ({"kind": "catalogue-gallery", "id": token.gallery_id} if token.gallery_id else
                   {"kind": f"catalogue-{token.target_type}", "id": token.target_id}),
        **({"work_id": token.target_id} if token.gallery_id else {}),
        "presentation": token.presentation,
        "options": options,
    }


def catalogue_reference_slot(reference: dict[str, Any]) -> str:
    """The same explicit slot is filled by live or static presentation owners."""
    tag = "span" if reference["presentation"] == "media" else "div"
    return f'<{tag} data-docs-catalogue-ref="{reference["reference_id"]}"></{tag}>'


def render_image_reference(token: SourceTokenOccurrence, src: str | None) -> str:
    """Render static Docs-owned image presentation without media writes or lookups."""
    if src is None:
        caption = f"<p>{html.escape(token.caption)}</p>" if token.caption else ""
        return caption + render_summary_paragraphs(token.summary)
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


class SourceTokensMixin:
    def restore_source_token_html(self, content_html: str) -> str:
        """Restore built fragments after Markdown so authored labels stay literal."""
        for marker, fragment in self._source_token_html.items():
            content_html = content_html.replace(marker, fragment)
        return content_html

    def resolve_source_tokens(
        self,
        markdown: str,
        *, document_id: str = "",
    ) -> str:
        """Render media without writes; Entry needs its exact Catalogue document ID."""
        self._source_token_html: dict[str, str] = {}
        self.catalogue_references: list[dict[str, Any]] = []
        self.related_galleries: dict[str, str] = {}
        self.related_works: set[str] = set()
        entry_seen = False

        def replace(token: SourceTokenOccurrence) -> str:
            nonlocal entry_seen
            if token.family == "image":
                fragment = render_image_reference(
                    token, self.image_token_media_url(token.media_path),
                )
            elif self.config.stage == "review":
                if not token.visible:
                    return ""
                fragment = render_summary_paragraphs(token.summary) if token.presentation == "image" else html.escape(token.title)
            else:
                if token.target_type == "work":
                    self.related_works.add(token.target_id)
                    if token.gallery_id:
                        self.related_galleries.setdefault(token.gallery_id, token.gallery_label or token.title)
                else:
                    self.related_galleries.setdefault(token.target_id, token.title)
                if not token.visible:
                    return ""
                if token.presentation == "entry":
                    if getattr(self, "collection_id", "") != "catalogue" or token.target_id != document_id or entry_seen:
                        raise ValueError("Catalogue Entry requires one token matching its Catalogue document identity")
                    entry_seen = True
                reference = catalogue_reference(token, f"c{len(self.catalogue_references) + 1}")
                self.catalogue_references.append(reference)
                fragment = catalogue_reference_slot(reference)
            if not fragment:
                return ""
            marker_id = uuid4().hex
            # Comments start HTML blocks at line beginnings; inline references must not.
            marker = (
                f"<!--source-token-{marker_id}-->"
                if token.presentation in {"image", "entry"}
                else f'<span data-source-token-fragment="{marker_id}"></span>'
            )
            self._source_token_html[marker] = fragment
            return marker

        return replace_source_tokens(markdown, replacer=replace)
