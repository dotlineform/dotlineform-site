"""Document-owned Moment identity, independent of authoring Subject."""

from typing import Any, Mapping, Sequence
from pathlib import Path

from docs_document_identities import normalize_document_identity


def metadata_record(settings: Mapping[str, Any], front_matter: Mapping[str, Any], *, doc_id: str) -> dict[str, Any]:
    del settings, doc_id
    return {"moment_id": front_matter.get("moment_id", "")}


def validate_source(settings: Mapping[str, Any], front_matter: Mapping[str, Any], *, doc_id: str) -> None:
    del settings
    if normalize_document_identity(front_matter, "moment_id")["state"] == "malformed":
        raise ValueError(f"moment_id must be an exact three-digit string: {doc_id}")


def normalize_import(settings: Mapping[str, Any], raw: Any, *, doc_id: str) -> dict[str, str]:
    if not isinstance(raw, dict) or set(raw) - {"moment_id"}:
        raise ValueError("Moment import accepts only moment_id")
    validate_source(settings, raw, doc_id=doc_id)
    value = normalize_document_identity(raw, "moment_id")["moment_id"]
    return {"moment_id": value} if value else {}


def validate_transfer(settings: Mapping[str, Any], field_name: str, value: Any) -> None:
    if field_name != "moment_id":
        raise ValueError(f"unsupported Moment field: {field_name}")
    validate_source(settings, {field_name: value}, doc_id="transfer")


def project_manifest(settings: Mapping[str, Any], documents: Sequence[Any], repo_root: Path, scope: str, sub_scope: str, stage: str = "") -> dict[str, Any]:
    del repo_root, scope, sub_scope, stage
    return {
        "root": {"id": "moments", "data": {}},
        "rows": {doc.doc_id: metadata_record(settings, doc.front_matter, doc_id=doc.doc_id) for doc in documents},
    }
