"""Independent numeric identities defined by Concept and Moment documents."""

from __future__ import annotations

import re
from typing import Any, Mapping

IDENTITY_FIELDS = {"concept": "concept_id", "moment": "moment_id"}
NUMERIC_IDENTITY_PATTERN = re.compile(r"\A[0-9]{3}\Z")


def normalize_document_identity(front_matter: Mapping[str, Any], field: str) -> dict[str, Any]:
    """Keep missing declarations valid without deriving identity from a title."""
    if field not in IDENTITY_FIELDS.values():
        raise ValueError(f"unsupported document identity field: {field}")
    value = front_matter.get(field)
    if value is None or value == "":
        return {"state": "none", field: ""}
    if not isinstance(value, str) or NUMERIC_IDENTITY_PATTERN.fullmatch(value) is None:
        return {"state": "malformed", field: "", "evidence": value}
    return {"state": "valid", field: value}


def validate_unique_document_identities(declarations: Mapping[str, Mapping[str, Any]], field: str) -> None:
    owners: dict[str, str] = {}
    for doc_id, declaration in declarations.items():
        if declaration["state"] == "none":
            continue
        if declaration["state"] != "valid":
            raise ValueError(f"{field} must be an exact three-digit string: {doc_id}")
        value = str(declaration[field])
        if value in owners:
            raise ValueError(f"duplicate {field} {value!r}: {owners[value]} and {doc_id}")
        owners[value] = doc_id


def next_document_identity(declarations: Mapping[str, Mapping[str, Any]], field: str) -> str:
    """Advance the current collection sequence without filling earlier gaps."""
    validate_unique_document_identities(declarations, field)
    highest = max((int(row[field]) for row in declarations.values() if row["state"] == "valid"), default=0)
    if highest >= 999:
        raise ValueError(f"No three-digit {field} remains available")
    return f"{highest + 1:03d}"
