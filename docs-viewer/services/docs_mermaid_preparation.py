"""Prepare document-owned Mermaid media inside the Preview generated snapshot."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import Any

from docs_artifact_locations import ArtifactLocation, artifact_location_adapter
from docs_public_mermaid_payload import project_mermaid_payload
from docs_public_mermaid_producer import DOCS_VIEWER_THEME_CSS_REL_PATH, produce_public_mermaid_projection
from docs_public_mermaid_projection import PUBLIC_MERMAID_ASSET_PREFIX, plan_public_mermaid_projection
from docs_workspace_config import DocsStageConfig, generated_documents_path, resolve_workspace_path
from docs_source_model import load_document_collection_docs_for_config


def prepare_stage_mermaid(repo_root: Path, config: DocsStageConfig) -> dict[str, Any] | None:
    """Render every prepared collection before its complete Build is recorded.

    Working Markdown and payloads retain their fences. Only public Preview
    collections receive SVG pairs and projected HTML. Temporary rendering must
    succeed before that collection's generated media or payloads are replaced;
    any failure propagates to the Build owner, leaving completion invalidated.
    Snapshot preparation and Deploy Repo subsequently consume only these bytes.
    """
    if config.stage != "preview" or config.public_projection is None:
        return None
    results = []
    for collection in (config, *config.collections):
        if collection.public_projection is None:
            continue
        child = getattr(collection, "collection", "")
        owner = f"{config.stage}/{child}" if child else config.stage
        docs = load_document_collection_docs_for_config(repo_root, config, collection)
        media = collection.media.types.get("svg")
        if media is None:
            raise ValueError(f"Mermaid preparation requires SVG media for {owner}")
        source_locations = [media.source_location]
        build = collection.media.build_sources.get("mermaid")
        if build is not None:
            source_locations.append(build.location)
        for location in source_locations:
            if artifact_location_adapter(repo_root, location).list(PUBLIC_MERMAID_ASSET_PREFIX):
                raise ValueError(f"Mermaid preparation output conflicts with authored media in {owner}/{PUBLIC_MERMAID_ASSET_PREFIX}")
        plan = plan_public_mermaid_projection(
            collection=owner, documents=((doc.doc_id, doc.body) for doc in docs),
            public_url_prefix=media.served_path_prefix,
        )
        if plan["failures"]:
            raise ValueError("Mermaid preparation failed: " + "; ".join(
                f"{owner}/{item['doc_id']}: {item['message']}" for item in plan["failures"]
            ))
        by_doc: dict[str, list[dict[str, Any]]] = {}
        for diagram in plan["diagrams"]:
            by_doc.setdefault(diagram["source"]["doc_id"], []).append(diagram)
        payload_root = resolve_workspace_path(repo_root, generated_documents_path(collection)) / "by-id"
        payloads = {}
        for doc_id, diagrams in by_doc.items():
            path = payload_root / f"{doc_id}.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("doc_id") != doc_id:
                raise ValueError(f"Mermaid payload identity does not match {owner}/{doc_id}")
            payloads[path] = project_mermaid_payload(payload, diagrams)

        generated = artifact_location_adapter(repo_root, media.generated_location)
        identities: set[str] = set()
        if plan["diagrams"]:
            with tempfile.TemporaryDirectory(prefix="docs-mermaid-preparation-") as temporary:
                prepared = artifact_location_adapter(Path(temporary), ArtifactLocation("repository", Path("rendered")))
                result = produce_public_mermaid_projection(
                    plan, prepared=prepared, write=True,
                    theme_css_path=repo_root / DOCS_VIEWER_THEME_CSS_REL_PATH,
                )
                if result["failures"]:
                    raise RuntimeError("Mermaid preparation failed: " + "; ".join(
                        f"{owner}/{item['doc_id']}: {item['message']}" for item in result["failures"]
                    ))
                identities = set(result["published_identities"])
                for identity in sorted(identities):
                    data = prepared.read(identity)
                    generated.replace(identity, data, content_type="image/svg+xml")
                    if not generated.verify_bytes(identity, data):
                        raise RuntimeError(f"Mermaid generated media did not verify: {owner}/{identity}")
        for item in generated.list():
            if Path(item.identity).is_relative_to(PUBLIC_MERMAID_ASSET_PREFIX) and item.identity not in identities:
                generated.delete(item.identity)
        for path, payload in payloads.items():
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        results.append({"collection": owner, "diagrams": len(plan["diagrams"]), "variants": len(identities)})
    return {"collections": results}
