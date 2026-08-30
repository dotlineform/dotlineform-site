#!/usr/bin/env python3
"""Derive public Catalogue document URLs from exact published Docs identity."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from docs_document_location_projection import (
    load_public_exact_document_location_records,
)
from docs_document_subjects import normalize_authoring_subject
from docs_scope_config import load_docs_scope_configs
from docs_source_model import load_document_collection_docs_for_config


CatalogueTarget = tuple[str, str, str]
CatalogueDocumentUrls = dict[str, dict[str, list[str]]]


def exact_location_target(record: Mapping[str, Any]) -> CatalogueTarget:
    scope_id = str(record.get("scope_id") or "").strip()
    sub_scope = str(record.get("sub_scope") or "").strip().lower()
    doc_id = str(record.get("doc_id") or "").strip()
    if not scope_id or not doc_id:
        raise ValueError("public document location must retain exact scope and doc_id")
    return scope_id, sub_scope, doc_id


def project_catalogue_document_urls(
    *,
    exact_locations: Sequence[Mapping[str, Any]],
    front_matter_by_target: Mapping[CatalogueTarget, Mapping[str, Any]],
) -> CatalogueDocumentUrls:
    """Group current public URLs by one exact normalized Work or Series subject."""

    urls_by_subject: dict[tuple[str, str], set[str]] = {}
    for location in exact_locations:
        target = exact_location_target(location)
        front_matter = front_matter_by_target.get(target)
        if front_matter is None:
            raise ValueError(
                "public document has no exact canonical source: "
                + "/".join(part for part in target if part)
            )
        url = str(location.get("url") or "").strip()
        if not url:
            raise ValueError("public document location URL must not be empty")

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
        urls_by_subject.setdefault((kind, key), set()).add(url)

    projection: CatalogueDocumentUrls = {"work": {}, "series": {}}
    for kind, key in sorted(urls_by_subject):
        projection[kind][key] = sorted(urls_by_subject[(kind, key)])
    return projection


def project_catalogue_document_urls_from_subject_associations(
    *,
    exact_locations: Sequence[Mapping[str, Any]],
    subject_associations_by_collection: Mapping[
        tuple[str, str], Mapping[str, Any]
    ],
) -> CatalogueDocumentUrls:
    """Join accepted public locations to accepted exact authoring subjects."""

    location_targets = {exact_location_target(record) for record in exact_locations}
    front_matter_by_target: dict[CatalogueTarget, Mapping[str, Any]] = {
        target: {} for target in location_targets
    }
    seen_targets: set[CatalogueTarget] = set()
    for (scope, sub_scope), payload in sorted(subject_associations_by_collection.items()):
        if payload.get("schema_version") != "docs_subject_associations_v1":
            raise ValueError(
                f"accepted subject associations for {scope}/{sub_scope} have an unsupported schema"
            )
        if payload.get("scope") != scope or payload.get("sub_scope") != sub_scope:
            raise ValueError(
                f"accepted subject associations for {scope}/{sub_scope} have the wrong collection identity"
            )
        raw_associations = payload.get("associations")
        if not isinstance(raw_associations, list):
            raise ValueError(
                f"accepted subject associations for {scope}/{sub_scope} are missing associations"
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
                    str(raw_target.get("scope") or "").strip(),
                    str(raw_target.get("sub_scope") or "").strip().lower(),
                    str(raw_target.get("doc_id") or "").strip(),
                )
                if not target[0] or not target[2]:
                    raise ValueError("accepted subject document target is incomplete")
                if target[:2] != (scope, sub_scope):
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

    return project_catalogue_document_urls(
        exact_locations=exact_locations,
        front_matter_by_target=front_matter_by_target,
    )


def load_public_catalogue_document_urls(repo_root: Path) -> CatalogueDocumentUrls:
    """Join current public locations to exact canonical source front matter."""

    configs = load_docs_scope_configs(repo_root, public_only=True)
    exact_locations: list[dict[str, str]] = []
    front_matter_by_target: dict[CatalogueTarget, Mapping[str, Any]] = {}

    for scope_id in sorted(configs):
        config = configs[scope_id]
        scope_locations = load_public_exact_document_location_records(
            repo_root,
            config,
        )
        exact_locations.extend(scope_locations)

        targets_by_sub_scope: dict[str, set[str]] = {}
        for location in scope_locations:
            _, sub_scope, doc_id = exact_location_target(location)
            targets_by_sub_scope.setdefault(sub_scope, set()).add(doc_id)

        collection_configs = {
            "": config,
            **{sub_scope.sub_scope: sub_scope for sub_scope in config.sub_scopes},
        }
        for sub_scope, public_doc_ids in sorted(targets_by_sub_scope.items()):
            collection_config = collection_configs.get(sub_scope)
            if collection_config is None:
                raise ValueError(
                    f"public document location references unconfigured collection "
                    f"{scope_id}/{sub_scope}"
                )
            documents = load_document_collection_docs_for_config(
                repo_root,
                config,
                collection_config,
            )
            documents_by_id = {document.doc_id: document for document in documents}
            for doc_id in sorted(public_doc_ids):
                document = documents_by_id.get(doc_id)
                if document is None:
                    collection = f"{scope_id}/{sub_scope}" if sub_scope else scope_id
                    raise ValueError(
                        f"public document {collection}/{doc_id} has no canonical source"
                    )
                front_matter_by_target[(scope_id, sub_scope, doc_id)] = (
                    document.front_matter
                )

    return project_catalogue_document_urls(
        exact_locations=exact_locations,
        front_matter_by_target=front_matter_by_target,
    )


__all__ = [
    "CatalogueDocumentUrls",
    "CatalogueTarget",
    "exact_location_target",
    "load_public_catalogue_document_urls",
    "project_catalogue_document_urls",
    "project_catalogue_document_urls_from_subject_associations",
]
