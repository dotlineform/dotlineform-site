"""Selected static Catalogue presentation; no generation, queues or destination writes."""

from __future__ import annotations

from dataclasses import dataclass
import html
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

from docs_image_tokens import FIGURE_NATURAL_WIDTH_CLASS, FIGURE_PLACEMENT_CLASSES
from docs_publication_paths import confined
from docs_publication_transfer import read_bytes
from docs_workspace_config import DocsWorkspaceConfig


@dataclass(frozen=True)
class CatalogueMedia:
    """An exact object under the configured Work media owner, never document media."""

    media_type: str
    identity: str
    url: str

    @property
    def binding(self) -> str:
        return f"catalogue/works/{self.media_type}"


@dataclass(frozen=True)
class PreparedCatalogueDocument:
    payload: dict[str, Any]
    media: tuple[CatalogueMedia, ...]


def resource_url(value: str) -> str:
    """Keep URL safety at the markup boundary, trusting authored resource fields."""
    if not value or re.search(r"[\s\x00-\x1f\x7f\\]", value):
        raise ValueError("Catalogue resource URL is unsafe")
    if value.startswith("/") and not value.startswith("//"):
        return value
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or (parsed.port is not None and parsed.port <= 0)):
        raise ValueError("Catalogue resource URL requires an HTTP(S) target")
    return value


def entry_fields(work: dict[str, Any], work_id: str) -> dict[str, Any]:
    lines = [work["year_display"]]
    if work.get("medium") is not None:
        lines.append(work["medium"])
    dimensions = [work[key] for key in ("height_cm", "width_cm", "depth_cm") if work.get(key) is not None]
    if dimensions:
        lines.append(" × ".join(str(int(value)) if value == int(value) else str(value) for value in dimensions) + " cm")
    lines.extend(["", f"cat. {work_id}"])
    return {"metadata_lines": lines, "resources": [
        {"kind": kind, "label": resource["label"], "url": resource_url(resource["url"])}
        for key, kind in (("downloads", "download"), ("links", "link"))
        for resource in work.get(key, [])
    ]}


class CatalogueStaticInputs:
    """Reuse selected Working inputs within one caller-owned synchronous operation.

    Construction performs no reads. Policy, relationships and icons are lazy;
    no source, inventory, eligibility or destination is opened here.
    """

    def __init__(self, repo_root: Path, workspace: DocsWorkspaceConfig) -> None:
        self.repo_root = repo_root
        self.workspace = workspace
        self.works: dict[str, dict[str, Any]] = {}
        self.raw_inputs: dict[str, bytes] = {}
        self.presentations: dict[str, tuple[dict[str, Any], tuple[CatalogueMedia, ...]]] = {}
        self.entries: dict[str, dict[str, Any]] = {}
        self.policy: dict[str, Any] | None = None
        self.relationships: dict[str, Any] | None = None
        self.icons: Any = None

    def bytes(self, identity: str) -> bytes:
        if identity not in self.raw_inputs:
            self.raw_inputs[identity] = read_bytes(confined(self.workspace.catalogue.working.path, identity))
        return self.raw_inputs[identity]

    def read(self, identity: str) -> dict[str, Any]:
        try:
            return json.loads(self.bytes(identity))
        except (OSError, ValueError) as error:
            raise ValueError(f"Required Working Catalogue input is unavailable: {identity}") from error

    def work(self, work_id: str) -> dict[str, Any]:
        if work_id not in self.works:
            self.works[work_id] = self.read(f"works/index/{work_id}.json")["work"]
        return self.works[work_id]

    def presentation(self, work_id: str, *, include_entry: bool) -> tuple[dict[str, Any], tuple[CatalogueMedia, ...]]:
        if work_id in self.presentations:
            presentation, media = self.presentations[work_id]
            return self.with_entry(work_id, presentation, include_entry), media
        work = self.work(work_id)
        if self.policy is None:
            self.policy = self.read("media-config.json")
        policy = self.policy
        primary = policy["primary"]
        widths = sorted(set(primary["widths"]))
        def rendition(width: int) -> CatalogueMedia:
            identity = f"{work_id}-{primary['suffix']}-{width}.{policy['format']}"
            return CatalogueMedia("primary", identity, primary["base_urls"]["works"] + identity
                                  + f"?{primary['version_query_parameter']}={work['media_version']}")

        candidates: dict[int, CatalogueMedia] = {}
        for width in widths:
            candidates.setdefault(min(width, work["width_px"]), rendition(width))
        largest = rendition(widths[-1])
        media = {item.identity: item for item in (*candidates.values(), largest)}
        galleries = [{"target": {"kind": "catalogue-gallery", "id": gallery["gallery_id"]},
                      "label": gallery["title"], "relation": "direct"} for gallery in work["galleries"]]
        seen = {gallery["target"]["id"] for gallery in galleries}
        if "series_id" in work:
            if self.relationships is None:
                self.relationships = self.read("series-galleries-index.json")
            for gallery in self.relationships["series_galleries"][work["series_id"]]:
                if gallery["gallery_id"] not in seen:
                    seen.add(gallery["gallery_id"])
                    galleries.append({"target": {"kind": "catalogue-gallery", "id": gallery["gallery_id"]},
                                      "label": gallery["title"], "relation": "series"})
        presentation = {
            "schema_version": "docs_media_view_v2", "target": {"kind": "catalogue-work", "id": work_id},
            "label": work["title"],
            "image": {"src": next(iter(candidates.values())).url,
                      "candidates": [{"src": item.url, "width_px": width} for width, item in candidates.items()],
                      "alt": work["title"], "width_px": work["width_px"], "height_px": work["height_px"]},
            "new_tab_target": largest.url, "galleries": galleries,
        }
        selected_media = tuple(media.values())
        self.presentations[work_id] = presentation, selected_media
        return self.with_entry(work_id, presentation, include_entry), selected_media

    def with_entry(self, work_id: str, presentation: dict[str, Any], include_entry: bool) -> dict[str, Any]:
        if not include_entry:
            return presentation
        if work_id not in self.entries:
            self.entries[work_id] = entry_fields(self.work(work_id), work_id)
        return {**presentation, "entry": self.entries[work_id]}

    def icon(self, name: str) -> str:
        if self.icons is None:
            from docs_inline_icon_artwork import InlineIconArtwork

            self.icons = InlineIconArtwork(self.repo_root)
        return self.icons.render(name, decorative=True)


def image_control(presentation: dict[str, Any], *, entry: bool) -> str:
    image = presentation["image"]
    title = html.escape(presentation["label"], quote=True)
    width, height = image["width_px"], image["height_px"]
    frame = ' docsViewerCatalogueEntry__frame' if entry else ""
    ratio = f' style="aspect-ratio: {width} / {height};"' if entry else ""
    srcset = ", ".join(f"{resource_url(item['src'])} {item['width_px']}w" for item in image["candidates"])
    return (
        f'<button type="button" class="docsViewer__mediaImageLink docsViewerFigure__imageLink{frame}"{ratio} '
        f'data-docs-media-open aria-label="Open {title}">'
        f'<img data-docs-media-image src="{html.escape(resource_url(image["src"]), quote=True)}" '
        f'srcset="{html.escape(srcset, quote=True)}" sizes="100vw" alt="{title}" '
        f'width="{width}" height="{height}" decoding="async">'
        f'<span data-docs-media-placeholder hidden>{title}</span></button>'
    )


def reference_markup(reference: dict[str, Any], presentation: dict[str, Any] | None, inputs: CatalogueStaticInputs) -> str:
    target, options = reference["target"], reference["options"]
    attrs = (f'data-docs-content-detail="media" data-docs-media-kind="{target["kind"]}" '
             f'data-docs-media-id="{html.escape(target["id"], quote=True)}"')
    mode = reference["presentation"]
    if mode == "media":
        return (f'<span {attrs}><button type="button" class="docsViewer__mediaTextLink" data-docs-media-open>'
                f'{html.escape(options["label"])}</button></span>')
    image = image_control(presentation, entry=mode == "entry")
    if mode == "image":
        modifiers = [FIGURE_PLACEMENT_CLASSES[options["placement"]]]
        if not options["fill_width"]:
            modifiers.append(FIGURE_NATURAL_WIDTH_CLASS)
        blocks = []
        if options["use_work_title_caption"]:
            blocks.append(f'<span class="docsViewerFigure__caption">{html.escape(presentation["label"])}</span>')
        if options["summary_html"]:
            blocks.append(f'<span class="docsViewerFigure__summary">{options["summary_html"]}</span>')
        caption = f'<figcaption>{"".join(blocks)}</figcaption>' if blocks else ""
        return f'<figure class="docsViewerFigure {" ".join(modifiers)}" {attrs}>{image}{caption}</figure>'
    entry = presentation["entry"]
    metadata = "<br>".join(html.escape(line) for line in entry["metadata_lines"])
    resources = []
    for resource in entry["resources"]:
        icon = inputs.icon("file" if resource["kind"] == "download" else "link")
        resources.append(f'<li>{icon} <a href="{html.escape(resource_url(resource["url"]), quote=True)}" '
                         f'target="_blank" rel="noopener noreferrer">{html.escape(resource["label"])}</a></li>')
    resources_html = ('<div class="docsViewerCatalogueEntry__resources"><section data-catalogue-resource="links">'
                      f'<ul>{"".join(resources)}</ul></section></div>') if resources else ""
    return ('<article class="docsViewerCatalogueEntry"><div class="docsViewerCatalogueEntry__record">'
            f'<h1>{html.escape(presentation["label"])}</h1>'
            f'<figure class="docsViewerCatalogueEntry__image" {attrs}>{image}</figure>'
            f'<p class="docsViewerCatalogueEntry__metadata">{metadata}</p></div>{resources_html}</article>')


def prepare_catalogue_document(target: Any, payload: dict[str, Any], inputs: CatalogueStaticInputs) -> PreparedCatalogueDocument:
    """Resolve only the supplied document, leaving it and all persistent state untouched."""
    envelope = payload.get("catalogue")
    own_work = target["collection"] == "catalogue"
    if envelope is None and not own_work:
        return PreparedCatalogueDocument(payload, ())
    references = envelope["references"] if envelope else []
    required = {ref["target"]["id"]: False for ref in references if ref["target"]["kind"] == "catalogue-work"}
    for reference in references:
        if reference["presentation"] == "entry":
            required[reference["target"]["id"]] = True
    if own_work:
        required.setdefault(target["doc_id"], False)
    presentations, media = {}, {}
    for work_id, include_entry in required.items():
        presentation, images = inputs.presentation(work_id, include_entry=include_entry)
        presentations[f"catalogue-work:{work_id}"] = presentation
        for item in images:
            media[(item.media_type, item.identity)] = item
        if include_entry:
            work = inputs.work(work_id)
            for download in work.get("downloads", []):
                # The producer supplies the owned filename independently of its public URL.
                identity = download["filename"]
                item = CatalogueMedia("files", identity, resource_url(download["url"]))
                media[(item.media_type, item.identity)] = item
    content = payload["content_html"]
    for reference in references:
        tag = "span" if reference["presentation"] == "media" else "div"
        slot = f'<{tag} data-docs-catalogue-ref="{reference["reference_id"]}"></{tag}>'
        key = f'{reference["target"]["kind"]}:{reference["target"]["id"]}'
        markup = reference_markup(reference, presentations.get(key), inputs)
        content = content.replace(slot, f'<{tag} data-docs-catalogue-ref="{reference["reference_id"]}">{markup}</{tag}>')
    prepared_envelope = {**(envelope or {"schema": "docs_catalogue_presentation_v1", "references": []})}
    if presentations:
        prepared_envelope["presentations"] = presentations
    return PreparedCatalogueDocument({**payload, "content_html": content, "catalogue": prepared_envelope}, tuple(media.values()))
