"""Registered Docs Viewer collection customisations."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable, Mapping


CUSTOMISATION_ID_PATTERN = re.compile(r"\A[a-z][a-z0-9_]*\Z")
LINEAGE_SOURCE_ROLE = "source"
LINEAGE_EDITORIAL_ROLE = "editorial"
SUPPORTED_LINEAGE_ROLES = frozenset({LINEAGE_SOURCE_ROLE, LINEAGE_EDITORIAL_ROLE})


@dataclass(frozen=True)
class DocsCollectionCustomisationConfig:
    customisation_id: str
    settings: Mapping[str, Any]


@dataclass(frozen=True)
class DocsCollectionDocumentLineageAspect:
    contract_id: str
    role: str


@dataclass(frozen=True)
class DocsCollectionCustomisationDefinition:
    customisation_id: str
    normalize_settings: Callable[[Any, str], Mapping[str, Any]]
    document_lineages: tuple[DocsCollectionDocumentLineageAspect, ...] = ()


def _strict_object(raw: Any, *, field: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"Docs workspace config field {field} must be an object")
    unknown = sorted(set(raw) - keys)
    if unknown:
        raise ValueError(
            f"Docs workspace config field {field} contains unknown fields: "
            f"{', '.join(unknown)}"
        )
    missing = sorted(keys - set(raw))
    if missing:
        raise ValueError(
            f"Docs workspace config field {field} is missing required fields: "
            f"{', '.join(missing)}"
        )
    return raw


COLLECTION_CUSTOMISATION_DEFINITIONS: dict[str, DocsCollectionCustomisationDefinition] = {}


def _validate_definition(
    registry_id: str,
    definition: DocsCollectionCustomisationDefinition,
) -> DocsCollectionCustomisationDefinition:
    field = f"Docs collection customisation definition {registry_id!r}"
    if definition.customisation_id != registry_id:
        raise ValueError(f"{field} identity does not match its registry key")
    if not callable(definition.normalize_settings):
        raise ValueError(f"{field} normalize_settings must be callable")
    document_lineages = definition.document_lineages
    if not isinstance(document_lineages, tuple):
        raise ValueError(f"{field} document_lineages must be a tuple")
    seen_lineage_contracts: set[str] = set()
    for document_lineage in document_lineages:
        if not isinstance(document_lineage, DocsCollectionDocumentLineageAspect):
            raise ValueError(f"{field} document_lineages contains an invalid aspect")
        if not isinstance(
            document_lineage.contract_id,
            str,
        ) or not CUSTOMISATION_ID_PATTERN.fullmatch(document_lineage.contract_id):
            raise ValueError(
                f"{field} document_lineages contains an invalid contract id"
            )
        if document_lineage.contract_id in seen_lineage_contracts:
            raise ValueError(
                f"{field} document_lineages contains a duplicate contract id"
            )
        seen_lineage_contracts.add(document_lineage.contract_id)
        if document_lineage.role not in SUPPORTED_LINEAGE_ROLES:
            raise ValueError(f"{field} document_lineages contains an invalid role")
    return definition


def _definition_for(
    customisation: DocsCollectionCustomisationConfig,
) -> DocsCollectionCustomisationDefinition:
    definition = COLLECTION_CUSTOMISATION_DEFINITIONS.get(
        customisation.customisation_id
    )
    if definition is None:
        raise ValueError(
            "Docs collection customisation is not registered: "
            f"{customisation.customisation_id}"
        )
    return _validate_definition(customisation.customisation_id, definition)


def normalize_docs_collection_customisation(
    raw: Any,
    *,
    field: str,
) -> DocsCollectionCustomisationConfig | None:
    if raw is None:
        return None
    value = _strict_object(raw, field=field, keys={"id", "settings"})
    customisation_id = str(value.get("id") or "").strip()
    if not CUSTOMISATION_ID_PATTERN.fullmatch(customisation_id):
        raise ValueError(f"Docs workspace config field {field}.id is invalid")
    definition = COLLECTION_CUSTOMISATION_DEFINITIONS.get(customisation_id)
    if definition is None:
        raise ValueError(
            f"Docs workspace config field {field}.id is unknown: {customisation_id!r}"
        )
    definition = _validate_definition(customisation_id, definition)
    return DocsCollectionCustomisationConfig(
        customisation_id=customisation_id,
        settings=definition.normalize_settings(
            value["settings"],
            f"{field}.settings",
        ),
    )


def collection_customisation_document_lineage_contracts(
    customisation: DocsCollectionCustomisationConfig | None,
) -> tuple[DocsCollectionDocumentLineageAspect, ...]:
    if customisation is None:
        return ()
    return _definition_for(customisation).document_lineages
