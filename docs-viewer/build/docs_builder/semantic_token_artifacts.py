from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import json_text, read_json, read_text, write_text
from .source import DocRecord


SEMANTIC_TOKEN_USAGE_INDEX_SCHEMA_VERSION = "docs_semantic_token_usage_index_v1"


class SemanticTokenArtifactsMixin:
    @property
    def semantic_tokens_dir(self) -> Path:
        return self.output_dir / "semantic-tokens"

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
        occurrences = [
            occurrence
            for doc in docs
            for occurrence in occurrences_by_doc.get(doc.doc_id, [])
        ]
        return {
            "enabled": True,
            "index": self.semantic_token_usage_envelope(occurrences),
        }

    def existing_semantic_token_occurrences_by_doc(
        self,
        docs: list[DocRecord],
        target_doc_ids: list[str],
    ) -> dict[str, list[dict[str, Any]]]:
        selected = set(target_doc_ids)
        known_doc_ids = {doc.doc_id for doc in docs}
        payload = read_json(self.semantic_tokens_dir / "index.json")
        occurrences = payload.get("occurrences") if isinstance(payload, dict) else None
        out: dict[str, list[dict[str, Any]]] = {}
        if not isinstance(occurrences, list):
            return out
        for occurrence in occurrences:
            if not isinstance(occurrence, dict):
                continue
            doc_id = str(occurrence.get("source_doc_id") or "").strip()
            if not doc_id or doc_id in selected or doc_id not in known_doc_ids:
                continue
            out.setdefault(doc_id, []).append(dict(occurrence))
        return out

    def build_semantic_token_write_plan(
        self,
        payloads: dict[str, Any],
    ) -> dict[str, Any]:
        if payloads.get("enabled") is not True:
            return {
                "semantic_token_outputs_enabled": False,
                "semantic_token_index_write": False,
                "semantic_token_index_text": "",
            }
        index_text = json_text(payloads["index"])
        return {
            "semantic_token_outputs_enabled": True,
            "semantic_token_index_write": read_text(self.semantic_tokens_dir / "index.json") != index_text,
            "semantic_token_index_text": index_text,
        }

    def write_semantic_token_outputs(self, write_plan: dict[str, Any]) -> None:
        if write_plan.get("semantic_token_outputs_enabled") is not True:
            return
        self.semantic_tokens_dir.mkdir(parents=True, exist_ok=True)
        if write_plan["semantic_token_index_write"]:
            write_text(
                self.semantic_tokens_dir / "index.json",
                write_plan["semantic_token_index_text"],
            )
