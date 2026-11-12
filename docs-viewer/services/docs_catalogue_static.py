"""Selected static Catalogue presentation; no generation, queues or destination writes."""

from __future__ import annotations

from dataclasses import dataclass
import html
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote, urlsplit

from docs_image_tokens import FIGURE_NATURAL_WIDTH_CLASS, FIGURE_PLACEMENT_CLASSES
from docs_catalogue_projection import catalogue_preparation_inputs
from docs_publication_media import catalogue_public_thumbnail_location
from docs_workspace_config import DocsWorkspaceConfig


LEFT_IMAGE_SIZE_CLASSES = {
    "third": "docsViewerFigure--left-third",
    "thumbnail": "docsViewerFigure--left-thumbnail",
}


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
    work_links: dict[str, str]


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


class CatalogueStaticInputs:
    """Carry the selected adopted Works and stage asset roots through HTML preparation."""

    def __init__(
        self, repo_root: Path, workspace: DocsWorkspaceConfig, *, public_media: dict[str, Any] | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.projection = catalogue_preparation_inputs(repo_root, workspace)
        if public_media is None:
            self.primary_base = workspace.assets.url(workspace.assets.work_primary) + "/"
            self.thumbnail_base = workspace.assets.url(workspace.assets.work_thumbnails) + "/"
            self.files_base = workspace.assets.url(workspace.assets.work_files) + "/"
        else:
            base = public_media["base"].rstrip("/")
            self.primary_base = base + "/" + public_media["image_works"].strip("/") + "/"
            self.thumbnail_base = "/" + catalogue_public_thumbnail_location(workspace).path.relative_to("site").as_posix() + "/"
            self.files_base = base + "/" + public_media["files_works"].strip("/") + "/"
        self.icons: Any = None

    def image_asset(self, identity: str, version: int, *, media_type: str = "primary") -> CatalogueMedia:
        base = self.thumbnail_base if media_type == "thumbs" else self.primary_base
        return CatalogueMedia(media_type, identity, base + quote(identity, safe="") + f"?v={version}")

    def download(self, identity: str) -> CatalogueMedia:
        return CatalogueMedia("files", identity, self.files_base + quote(identity, safe=""))

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
    responsive = f'srcset="{html.escape(srcset, quote=True)}" sizes="100vw" ' if srcset else ""
    return (
        f'<button type="button" class="docsViewer__mediaImageLink docsViewerFigure__imageLink{frame}"{ratio} '
        f'data-docs-media-open aria-label="Open {title}">'
        f'<img data-docs-media-image src="{html.escape(resource_url(image["src"]), quote=True)}" '
        f'{responsive}alt="{title}" '
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
        left_size = options.get("left_size")
        if left_size:
            modifiers.append(LEFT_IMAGE_SIZE_CLASSES[left_size])
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


def prepare_catalogue_document(
    payload: dict[str, Any], inputs: CatalogueStaticInputs, *, export: bool = False,
) -> PreparedCatalogueDocument:
    """Materialize selected static HTML and the exact Work assets used by Export."""
    envelope = payload.get("catalogue")
    if envelope is None:
        return PreparedCatalogueDocument(payload, (), {})
    content = payload["content_html"]
    work_links = {}
    media = {}

    def select(asset: CatalogueMedia) -> str:
        if export:
            media[(asset.binding, asset.identity)] = asset
        return asset.url

    for reference in envelope["references"]:
        mode = reference["presentation"]
        work_target = reference["target"]
        presentation = None
        left_size = reference["options"].get("left_size", "")
        if work_target["kind"] == "catalogue-work" and (mode != "media" or export):
            work_id = work_target["id"]
            work = inputs.projection.work(work_id)
            image = work["image"]
            primary_url = ""
            if export:
                primary_url = select(inputs.image_asset(image["default"], image["version"]))
                work_links[f"catalogue-work:{work_id}"] = primary_url
            if mode != "media":
                if mode == "image":
                    image = inputs.projection.reference_image(work_id, image, left_size)
                media_type = image.get("media_type", "primary")
                src = primary_url if export and media_type == "primary" else select(inputs.image_asset(
                    image["default"], image["version"], media_type=media_type,
                ))
                candidates = [] if export else [
                    {"src": inputs.image_asset(candidate["identity"], image["version"]).url,
                     "width_px": candidate["width_px"]} for candidate in image["candidates"]
                ]
                presentation = {"label": image["alt"], "image": {**image, "src": src, "candidates": candidates}}
            if mode == "entry":
                entry = work["entry"]
                presentation["entry"] = {
                    "metadata_lines": entry["metadata_lines"],
                    "resources": [
                        {**resource, "url": select(inputs.download(resource["identity"]))}
                        if resource["kind"] == "download" else resource
                        for resource in entry["resources"]
                    ],
                }
        tag = "span" if mode == "media" else "div"
        slot = f'<{tag} data-docs-catalogue-ref="{reference["reference_id"]}">'
        markup = reference_markup(reference, presentation, inputs)
        rendered_slot = slot
        if left_size == "thumbnail":
            width = presentation["image"]["width_px"]
            rendered_slot = f'{slot[:-1]} style="--docs-viewer-thumbnail-width: {width}px">'
        content = content.replace(f"{slot}</{tag}>", f"{rendered_slot}{markup}</{tag}>")
    return PreparedCatalogueDocument({**payload, "content_html": content}, tuple(media.values()), work_links)
