#!/usr/bin/env python3
"""Derive public Catalogue document metadata from exact published Docs identity."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from docs_document_location_projection import build_exact_document_location_records
from docs_document_subjects import normalize_authoring_subject
from docs_workspace_config import load_docs_workspace_config, select_workspace_stage
from docs_publish import validate_published_snapshot
from docs_publication_payloads import project_public_view
import json


CatalogueTarget = tuple[str, str]
CatalogueDocuments = dict[str, dict[str, list[dict[str, str]]]]


def exact_location_target(record: Mapping[str, Any]) -> CatalogueTarget:
    collection = str(record.get("collection") or "").strip().lower()
    doc_id = str(record.get("doc_id") or "").strip()
    if "scope_id" in record or "scope" in record or not doc_id:
        raise ValueError("public document location must retain exact collection and doc_id without scope")
    return collection, doc_id


def project_catalogue_documents(
    *,
    exact_locations: Sequence[Mapping[str, Any]],
    front_matter_by_target: Mapping[CatalogueTarget, Mapping[str, Any]],
) -> CatalogueDocuments:
    """Group current public document metadata by exact Work or Series subject."""

    documents_by_subject: dict[tuple[str, str], dict[str, str]] = {}
    for location in exact_locations:
        target = exact_location_target(location)
        front_matter = front_matter_by_target.get(target)
        if front_matter is None:
            raise ValueError(
                "public document has no exact accepted subject record: "
                + "/".join(part for part in target if part)
            )
        url = str(location.get("url") or "").strip()
        if not url:
            raise ValueError("public document location URL must not be empty")
        title = str(location.get("document_title") or "").strip()
        if not title:
            raise ValueError("public document location title must not be empty")

        subject = normalize_authoring_subject(
            front_matter,
            folder_supported=False,
        )
        if subject.get("state") != "valid":
            continue
        kind = str(subject.get("kind") or "")
        key = str(subject.get("key") or "")
        if kind not in {"work", "series"} or not key:
            continue
        documents = documents_by_subject.setdefault((kind, key), {})
        existing_title = documents.get(url)
        if existing_title is not None and existing_title != title:
            raise ValueError(f"public document location {url!r} has conflicting titles")
        documents[url] = title

    projection: CatalogueDocuments = {"work": {}, "series": {}}
    for kind, key in sorted(documents_by_subject):
        projection[kind][key] = [
            {"url": url, "title": title}
            for url, title in sorted(documents_by_subject[(kind, key)].items())
        ]
    return projection


def project_catalogue_documents_from_subject_associations(
    *,
    exact_locations: Sequence[Mapping[str, Any]],
    subject_associations_by_collection: Mapping[
        tuple[str, str], Mapping[str, Any]
    ],
) -> CatalogueDocuments:
    """Join accepted public locations to accepted exact authoring subjects."""

    location_targets = {exact_location_target(record) for record in exact_locations}
    front_matter_by_target: dict[CatalogueTarget, Mapping[str, Any]] = {
        target: {} for target in location_targets
    }
    seen_targets: set[CatalogueTarget] = set()
    for (stage, collection), payload in sorted(subject_associations_by_collection.items()):
        if payload.get("schema_version") != "docs_subject_associations_v2":
            raise ValueError(
                f"accepted subject associations for {stage}/{collection} have an unsupported schema"
            )
        if stage != "published" or "scope" in payload or payload.get("stage") != stage or payload.get("collection") != collection:
            raise ValueError(
                f"accepted subject associations for {stage}/{collection} have the wrong collection identity"
            )
        raw_associations = payload.get("associations")
        if not isinstance(raw_associations, list):
            raise ValueError(
                f"accepted subject associations for {stage}/{collection} are missing associations"
            )
        for raw_association in raw_associations:
            if not isinstance(raw_association, Mapping):
                raise ValueError("accepted subject association must be an object")
            subject = raw_association.get("subject")
            documents = raw_association.get("documents")
            if not isinstance(subject, Mapping) or not isinstance(documents, list):
                raise ValueError("accepted subject association must contain subject and documents")
            kind = str(subject.get("kind") or "").strip()
            key = str(subject.get("key") or "").strip()
            if kind not in {"work", "series"} or not key:
                raise ValueError("accepted deployment subject must be an exact Work or Series")
            field_name = "work_id" if kind == "work" else "series_id"
            for raw_document in documents:
                if not isinstance(raw_document, Mapping):
                    raise ValueError("accepted subject document must be an object")
                raw_target = raw_document.get("target")
                if not isinstance(raw_target, Mapping):
                    raise ValueError("accepted subject document must contain an exact target")
                target = (
                    str(raw_target.get("collection") or "").strip().lower(),
                    str(raw_target.get("doc_id") or "").strip(),
                )
                if not target[0] or not target[1]:
                    raise ValueError("accepted subject document target is incomplete")
                if "scope" in raw_target or raw_target.get("stage") != stage or target[0] != collection:
                    raise ValueError("accepted subject document has the wrong collection identity")
                if target not in location_targets:
                    raise ValueError(
                        "accepted subject document has no accepted public location: "
                        + "/".join(part for part in target if part)
                    )
                if target in seen_targets:
                    raise ValueError("accepted document has more than one authoring subject")
                seen_targets.add(target)
                front_matter_by_target[target] = {field_name: key}

    return project_catalogue_documents(
        exact_locations=exact_locations,
        front_matter_by_target=front_matter_by_target,
    )


def load_public_catalogue_documents(repo_root: Path) -> CatalogueDocuments:
    """Join the complete accepted document set to its accepted subjects."""
    workspace = load_docs_workspace_config(repo_root)
    config = select_workspace_stage(workspace, "pre-publish")
    _manifest, _root, files = validate_published_snapshot(repo_root)

    def payload(path: Path) -> dict[str, Any]:
        if path not in files:
            raise FileNotFoundError(f"Accepted Published snapshot is missing {path}")
        value = json.loads(files[path].decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"Accepted {path} must be an object")
        return project_public_view(workspace, value)

    accepted_children = {path.parts[1] for path in files if len(path.parts) > 2 and path.parts[0] == "collections"}
    configured_children = {child.collection: child for child in config.collections}
    if accepted_children - set(configured_children):
        raise ValueError("Accepted snapshot contains unconfigured child identities")
    children = [configured_children[child] for child in sorted(accepted_children)]
    locations = build_exact_document_location_records(
        workspace,
        search_payload=payload(Path("search/index.json")),
        parent_documents={path.stem: payload(path) for path in files
                          if len(path.parts) == 3 and path.parts[:2] == ("documents", "by-id") and path.suffix == ".json"},
        collection_manifests={child.collection: payload(Path("collections") / child.collection / "documents/manifest.json")
                             for child in children},
    )
    associations = {}
    for child in children:
        path = Path("collections") / child.collection / "documents/subject-associations.json"
        if path in files:
            associations[("published", child.collection)] = payload(path)
        elif child.collection_customisation is not None:
            raise FileNotFoundError(f"Accepted Published snapshot is missing {path}")
    return project_catalogue_documents_from_subject_associations(
        exact_locations=locations, subject_associations_by_collection=associations,
    )


__all__ = [
    "CatalogueDocuments",
    "CatalogueTarget",
    "exact_location_target",
    "load_public_catalogue_documents",
    "project_catalogue_documents",
    "project_catalogue_documents_from_subject_associations",
]
