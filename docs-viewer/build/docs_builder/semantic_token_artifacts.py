from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

from .common import json_text, read_json, read_text, write_text
from .source import DocRecord


SEMANTIC_TOKEN_USAGE_INDEX_SCHEMA_VERSION = "docs_semantic_token_usage_index_v1"


class SemanticTokenArtifactsMixin:
    @property
    def semantic_tokens_dir(self) -> Path:
        return self.output_dir / "semantic-tokens"

    @property
    def semantic_tokens_by_document_dir(self) -> Path:
        return self.semantic_tokens_dir / "by-document"

    @property
    def semantic_tokens_by_target_dir(self) -> Path:
        return self.semantic_tokens_dir / "by-target"

    def semantic_token_target_path(self, family: str, target_type: str, target_id: str) -> Path:
        return (
            self.semantic_tokens_by_target_dir
            / quote(str(family))
            / quote(str(target_type))
            / f"{quote(str(target_id))}.json"
        )

    def semantic_token_usage_envelope(
        self,
        occurrences: list[dict[str, Any]],
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "schema_version": SEMANTIC_TOKEN_USAGE_INDEX_SCHEMA_VERSION,
            "scope": self.scope_id,
            **extra,
            "occurrences": occurrences,
        }

    def build_semantic_token_payloads(
        self,
        docs: list[DocRecord],
        occurrences_by_doc: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        if self.public_readonly_scope:
            return {
                "enabled": False,
                "index": self.semantic_token_usage_envelope([]),
                "by_document": {},
                "by_target": {},
            }
        occurrences = [
            occurrence
            for doc in docs
            for occurrence in occurrences_by_doc.get(doc.doc_id, [])
        ]
        by_document = {
            doc_id: self.semantic_token_usage_envelope(
                records,
                source_doc_id=doc_id,
            )
            for doc_id, records in occurrences_by_doc.items()
            if records
        }
        grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for occurrence in occurrences:
            key = (
                str(occurrence["family"]),
                str(occurrence["target_type"]),
                str(occurrence["target_id"]),
            )
            grouped.setdefault(key, []).append(occurrence)
        by_target = {
            key: self.semantic_token_usage_envelope(
                records,
                target={
                    "family": key[0],
                    "target_type": key[1],
                    "target_id": key[2],
                    "href": records[0]["href"],
                },
            )
            for key, records in grouped.items()
        }
        return {
            "enabled": True,
            "index": self.semantic_token_usage_envelope(occurrences),
            "by_document": by_document,
            "by_target": by_target,
        }

    def existing_semantic_token_occurrences_by_doc(
        self,
        docs: list[DocRecord],
        target_doc_ids: list[str],
    ) -> dict[str, list[dict[str, Any]]]:
        if self.public_readonly_scope:
            return {}
        selected = set(target_doc_ids)
        out: dict[str, list[dict[str, Any]]] = {}
        for doc in docs:
            if doc.doc_id in selected:
                continue
            payload = read_json(self.semantic_tokens_by_document_dir / f"{doc.doc_id}.json")
            occurrences = payload.get("occurrences") if isinstance(payload, dict) else None
            if isinstance(occurrences, list):
                out[doc.doc_id] = [
                    dict(occurrence)
                    for occurrence in occurrences
                    if isinstance(occurrence, dict)
                ]
        return out

    def existing_semantic_token_target_keys(self) -> list[tuple[str, str, str]]:
        if not self.semantic_tokens_by_target_dir.exists():
            return []
        return sorted(
            (
                unquote(path.parents[1].name),
                unquote(path.parent.name),
                unquote(path.stem),
            )
            for path in self.semantic_tokens_by_target_dir.glob("*/*/*.json")
        )

    def build_semantic_token_write_plan(
        self,
        payloads: dict[str, Any],
        *,
        target_doc_ids: list[str] | None,
    ) -> dict[str, Any]:
        if payloads.get("enabled") is not True:
            return {
                "semantic_token_outputs_enabled": False,
                "semantic_token_index_write": False,
                "semantic_token_index_text": "",
                "changed_semantic_token_document_ids": [],
                "stale_semantic_token_document_ids": [],
                "semantic_token_document_text_by_id": {},
                "changed_semantic_token_target_keys": [],
                "stale_semantic_token_target_keys": [],
                "semantic_token_target_text_by_key": {},
            }
        index_text = json_text(payloads["index"])
        document_text_by_id: dict[str, str] = {}
        changed_document_ids: list[str] = []
        for doc_id, payload in payloads["by_document"].items():
            text = json_text(payload)
            document_text_by_id[doc_id] = text
            if read_text(self.semantic_tokens_by_document_dir / f"{doc_id}.json") != text:
                changed_document_ids.append(doc_id)
        existing_document_ids = self.existing_doc_payload_ids(self.semantic_tokens_by_document_dir)
        stale_document_ids = sorted(set(existing_document_ids) - set(payloads["by_document"]))
        if target_doc_ids:
            target_set = set(target_doc_ids)
            changed_document_ids = [
                doc_id for doc_id in changed_document_ids if doc_id in target_set
            ]
            stale_document_ids = sorted(set(stale_document_ids) & target_set)

        target_text_by_key: dict[tuple[str, str, str], str] = {}
        changed_target_keys: list[tuple[str, str, str]] = []
        for key, payload in payloads["by_target"].items():
            text = json_text(payload)
            target_text_by_key[key] = text
            if read_text(self.semantic_token_target_path(*key)) != text:
                changed_target_keys.append(key)
        stale_target_keys = sorted(
            set(self.existing_semantic_token_target_keys()) - set(payloads["by_target"])
        )
        return {
            "semantic_token_outputs_enabled": True,
            "semantic_token_index_write": read_text(self.semantic_tokens_dir / "index.json") != index_text,
            "semantic_token_index_text": index_text,
            "changed_semantic_token_document_ids": sorted(changed_document_ids),
            "stale_semantic_token_document_ids": stale_document_ids,
            "semantic_token_document_text_by_id": document_text_by_id,
            "changed_semantic_token_target_keys": sorted(changed_target_keys),
            "stale_semantic_token_target_keys": stale_target_keys,
            "semantic_token_target_text_by_key": target_text_by_key,
        }

    def write_semantic_token_outputs(self, write_plan: dict[str, Any]) -> None:
        if write_plan.get("semantic_token_outputs_enabled") is not True:
            return
        self.semantic_tokens_by_document_dir.mkdir(parents=True, exist_ok=True)
        self.semantic_tokens_by_target_dir.mkdir(parents=True, exist_ok=True)
        if write_plan["semantic_token_index_write"]:
            write_text(
                self.semantic_tokens_dir / "index.json",
                write_plan["semantic_token_index_text"],
            )
        for doc_id in write_plan["changed_semantic_token_document_ids"]:
            write_text(
                self.semantic_tokens_by_document_dir / f"{doc_id}.json",
                write_plan["semantic_token_document_text_by_id"][doc_id],
            )
        for doc_id in write_plan["stale_semantic_token_document_ids"]:
            (self.semantic_tokens_by_document_dir / f"{doc_id}.json").unlink(missing_ok=True)
        for key in write_plan["changed_semantic_token_target_keys"]:
            write_text(
                self.semantic_token_target_path(*key),
                write_plan["semantic_token_target_text_by_key"][key],
            )
        for key in write_plan["stale_semantic_token_target_keys"]:
            self.semantic_token_target_path(*key).unlink(missing_ok=True)
