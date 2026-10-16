"""Prepare one eligible document's public Mermaid output upstream of Publish."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_mermaid_renderer import MERMAID_EXECUTABLE_RELATIVE_PATH, MERMAID_TOOLCHAIN_ROOT
from docs_public_mermaid_payload import PUBLIC_MERMAID_HTML_FENCE_PATTERN, project_mermaid_payload
from docs_public_mermaid_projection import plan_public_mermaid_projection
from docs_public_mermaid_producer import DOCS_VIEWER_THEME_CSS_REL_PATH, load_public_mermaid_theme_seeds, render_public_mermaid_variants
from docs_publication_transfer import read_bytes, write_bytes
from docs_workspace_config import location_child


def prepare_document_mermaid(repo_root: Path, owner: Any, document: Any, payload: dict[str, Any], previous: dict[str, Any] | None, *, force: bool, baseline_source: Any, runtime: Any) -> tuple[dict[str, Any], list[dict[str, Any]], Any]:
    if owner.media is None or PUBLIC_MERMAID_HTML_FENCE_PATTERN.search(payload["content_html"]) is None:
        return payload, [], runtime
    media = owner.media.types["svg"]
    collection = getattr(owner, "collection", "")
    plan = plan_public_mermaid_projection(
        collection=f"preview/{collection}" if collection else "preview",
        documents=[(document.doc_id, document.body_markdown)],
        public_url_prefix="docs-media:" + media.served_path_prefix.removeprefix("/docs/assets/media/"),
    )
    if plan["failures"]:
        raise ValueError(f"Document {document.doc_id} public Mermaid: " + "; ".join(item["message"] for item in plan["failures"]))
    prior = {} if previous is None else {item["projection_id"]: item for item in previous["mermaid"]}
    planned = {item["projection_id"]: item for item in plan["manifest"]["diagrams"]}
    changed = [item for item in plan["diagrams"] if force or prior.get(item["projection"]["projection_id"]) != planned[item["projection"]["projection_id"]]]
    if baseline_source is not None:
        writes = {
            variant["artifact_identity"]: read_bytes(location_child(baseline_source, Path(variant["artifact_identity"])).path)
            for item in changed for variant in item["projection"]["variants"].values()
        }
    elif changed:
        if runtime is None:
            executable = MERMAID_TOOLCHAIN_ROOT / MERMAID_EXECUTABLE_RELATIVE_PATH
            runtime = executable, load_public_mermaid_theme_seeds(repo_root / DOCS_VIEWER_THEME_CSS_REL_PATH)
        writes = render_public_mermaid_variants(changed, executable=runtime[0], theme_seeds=runtime[1])
    else:
        writes = {}
    for identity, data in writes.items():
        write_bytes(location_child(media.asset_location, Path(identity)).path, data)
    return project_mermaid_payload(payload, plan["diagrams"]), plan["manifest"]["diagrams"], runtime
