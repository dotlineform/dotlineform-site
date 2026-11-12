"""Adopt selected Work facts and project render data into generated documents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_artifact_locations import ArtifactLocation
from docs_catalogue_media import read_catalogue_media_config
from docs_publication_paths import confined, working_owner
from docs_workspace_config import DocsWorkspaceConfig, generated_documents_path


def catalogue_renditions(work_id: str, width_px: int, policy: dict[str, Any]) -> tuple[dict[int, str], str]:
    """Select filename identities and deduplicate equal intrinsic width descriptors."""
    primary = policy["primary"]
    widths = sorted(set(primary["widths"]))

    def rendition(width: int) -> str:
        return f"{work_id}-{primary['suffix']}-{width}.{policy['format']}"

    candidates = {}
    for width in widths:
        candidates.setdefault(min(width, width_px), rendition(width))
    return candidates, rendition(widths[-1])


def entry_metadata_lines(work: dict[str, Any], work_id: str) -> list[str]:
    lines = [work["year_display"]]
    if work.get("medium") is not None:
        lines.append(work["medium"])
    if work.get("duration"):
        lines.append(work["duration"])
    dimensions = [work[key] for key in ("height_cm", "width_cm", "depth_cm") if work.get(key) is not None]
    if dimensions:
        lines.append(" × ".join(str(int(value)) if value == int(value) else str(value) for value in dimensions) + " cm")
    lines.extend(["", f"cat. {work_id}"])
    return lines


def prepare_work_image(
    work_id: str, image: dict[str, Any], policy: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    candidates, full_image = catalogue_renditions(work_id, image["width_px"], policy)
    return {
        **image,
        "default": next(iter(candidates.values())),
        "candidates": [{"identity": identity, "width_px": width} for width, identity in candidates.items()],
    }, full_image


def adopt_catalogue_work(
    work: dict[str, Any], policy: dict[str, Any], series_galleries: list[dict[str, str]],
) -> dict[str, Any]:
    """Prepare one supplied Refresh result without reading or writing storage."""
    image, full_image = prepare_work_image(work["work_id"], {
        "alt": work["title"],
        "width_px": work["width_px"],
        "height_px": work["height_px"],
        "version": work["media_version"],
    }, policy)
    direct = work["galleries"]
    seen = {gallery["gallery_id"] for gallery in direct}
    galleries = [
        {"id": gallery["gallery_id"], "label": gallery["title"], "relation": relation}
        for relation, selected in (
            ("direct", direct), ("series", [gallery for gallery in series_galleries if gallery["gallery_id"] not in seen]),
        )
        for gallery in selected
    ]
    entry = {
        "metadata_lines": entry_metadata_lines(work, work["work_id"]),
        "resources": [
            {"kind": "download", "label": download["label"], "identity": download["filename"]}
            for download in work.get("downloads", [])
        ] + [
            {"kind": "link", "label": link["label"], "url": link["url"]}
            for link in work.get("links", [])
        ],
    }
    return {
        **({"series_id": work["series_id"]} if "series_id" in work else {}),
        "entry": entry,
        "image": image,
        "full_image": full_image,
        "galleries": galleries,
    }


def catalogue_work_from_document(doc_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    work = payload.get("catalogue", {}).get("work")
    if payload.get("doc_id") == doc_id and work is not None:
        return work
    raise FileNotFoundError(f"Adopted Catalogue Work {doc_id} is unavailable. Complete Catalogue Regenerate.")


class CatalogueDocumentProjection:
    """Project selected document renders, sharing Work reads within this build."""

    def __init__(
        self, repo_root: Path, catalogue_items: Path, catalogue_root: ArtifactLocation,
        adopted_works: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.catalogue_items = catalogue_items
        self.catalogue_root = catalogue_root
        self.adopted_works = adopted_works or {}
        self.loaded: dict[str, dict[str, Any]] = {}
        self.documents: dict[str, dict[str, Any]] = {}
        self.policy: dict[str, Any] | None = None

    def media_policy(self) -> dict[str, Any]:
        if self.policy is None:
            self.policy = read_catalogue_media_config(self.repo_root, workspace=self.catalogue_root)
        return self.policy

    def prepare(self, work_id: str, work: dict[str, Any]) -> dict[str, Any]:
        image, full_image = prepare_work_image(work_id, work["image"], self.media_policy())
        return {**work, "image": image, "full_image": full_image}

    def reference_image(self, work_id: str, image: dict[str, Any], left_size: str) -> dict[str, Any]:
        """Carry only the selected inline renditions, with the Work's title and version."""
        if left_size == "third":
            return {**image, "candidates": []}
        if left_size == "thumbnail":
            policy = self.media_policy()
            thumbnail = policy["thumbnails"]
            size = min(thumbnail["sizes"])
            return {
                "alt": image["alt"], "version": image["version"], "width_px": size, "height_px": size,
                "media_type": "thumbs", "default": f"{work_id}-{thumbnail['suffix']}-{size}.{policy['format']}",
                "candidates": [],
            }
        return image

    def work(self, work_id: str) -> dict[str, Any]:
        if work_id in self.adopted_works:
            return self.adopted_works[work_id]
        if work_id not in self.loaded:
            payload = self.read_document(work_id)
            self.documents[work_id] = payload
            self.loaded[work_id] = self.prepare(work_id, catalogue_work_from_document(work_id, payload))
        return self.loaded[work_id]

    def read_document(self, work_id: str) -> dict[str, Any]:
        if work_id in self.documents:
            return self.documents.pop(work_id)
        path = confined(self.catalogue_items, f"{work_id}.json")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise FileNotFoundError(f"Adopted Catalogue Work {work_id} is unavailable. Complete Catalogue Regenerate.") from error
        if payload.get("doc_id") != work_id:
            raise ValueError(f"Catalogue document does not match Work {work_id}.")
        return payload

    def document(self, payload: dict[str, Any], previous_text: str | None = None, *, collection: str) -> None:
        envelope = payload.get("catalogue")
        if collection == "catalogue":
            doc_id = payload["doc_id"]
            own = self.adopted_works.get(doc_id) or self.loaded.get(doc_id)
            if own is None:
                previous = json.loads(previous_text) if previous_text is not None else payload
                own = self.prepare(doc_id, catalogue_work_from_document(doc_id, previous))
            envelope = payload.setdefault("catalogue", {"schema": "docs_catalogue_presentation_v1", "references": []})
            envelope["work"] = own
            self.loaded[doc_id] = own
        if envelope is not None:
            for reference in envelope["references"]:
                if reference["presentation"] == "image":
                    work_id = reference["target"]["id"]
                    image = self.work(work_id)["image"]
                    reference["render"] = self.reference_image(work_id, image, reference["options"].get("left_size", ""))


def catalogue_preparation_inputs(repo_root: Path, workspace: DocsWorkspaceConfig) -> CatalogueDocumentProjection:
    owner = working_owner(workspace, "catalogue")
    return CatalogueDocumentProjection(
        repo_root, generated_documents_path(owner) / "by-id", workspace.catalogue.working,
    )


def rendered_catalogue_assets(payload: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    """Select only inline Work renditions used by this referring document."""
    references = payload.get("catalogue", {}).get("references", ())
    selected = {}
    for reference in references:
        if reference["presentation"] != "image":
            continue
        image = reference["render"]
        binding = "catalogue/works/" + image.get("media_type", "primary")
        selected[(binding, image["default"])] = None
        for candidate in image["candidates"]:
            selected[(binding, candidate["identity"])] = None
    return tuple(selected)
