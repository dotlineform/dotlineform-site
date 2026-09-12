from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .common import generated_documents_path, json_text, read_text, resolve_scope_path, write_text
from .source import DocRecord


SEMANTIC_TOKEN_USAGE_INDEX_SCHEMA_VERSION = "docs_semantic_token_usage_index_v1"


class SemanticTokenArtifactsMixin:
    @property
    def semantic_tokens_dir(self) -> Path:
        """All collections contribute to the parent scope/stage's one usage index."""
        output = (
            resolve_scope_path(self.repo_root, generated_documents_path(self.config))
            if getattr(self, "sub_scope_id", "") else self.output_dir
        )
        return output / "semantic-tokens"

    def semantic_token_usage_envelope(
        self,
        occurrences: list[dict[str, Any]],
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "schema_version": SEMANTIC_TOKEN_USAGE_INDEX_SCHEMA_VERSION,
            "scope": self.scope_id,
            "stage": self.config.stage,
            **extra,
            "occurrences": occurrences,
        }

    def build_semantic_token_payloads(
        self,
        docs: list[DocRecord],
        occurrences_by_doc: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Replace built documents and prune deleted members of this collection only.

        The existing synchronous Build sequence owns ordering. Reuse collected
        occurrences without another source scan or publication eligibility decision.
        """
        collection = getattr(self, "sub_scope_id", "")
        text = read_text(self.semantic_tokens_dir / "index.json")
        payload = json.loads(text) if text is not None else self.semantic_token_usage_envelope([])
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != SEMANTIC_TOKEN_USAGE_INDEX_SCHEMA_VERSION
            or payload.get("scope") != self.scope_id
            or payload.get("stage", self.config.stage) != self.config.stage
            or not isinstance(payload.get("occurrences"), list)
        ):
            raise ValueError("Semantic-token index does not match its scope/stage")
        known = {doc.doc_id for doc in docs}
        selected = set(self.only_doc_ids) if self.targeted_build else known
        configured = {"", *(child.sub_scope for child in self.config.sub_scopes)}
        retained = []
        for row in payload["occurrences"]:
            if not isinstance(row, dict) or row.get("source_scope") != self.scope_id or not row.get("source_doc_id"):
                raise ValueError("Semantic-token occurrence has invalid source identity")
            # Existing v1 rows describe the main collection; make that explicit on write.
            source_collection = row.get("source_sub_scope", "")
            if source_collection not in configured:
                continue
            if source_collection == collection and (row["source_doc_id"] in selected or row["source_doc_id"] not in known):
                continue
            retained.append({**row, "source_sub_scope": source_collection})
        occurrences = retained + [
            {**occurrence, "source_sub_scope": collection}
            for doc in docs
            for occurrence in occurrences_by_doc.get(doc.doc_id, [])
        ]
        occurrences.sort(key=lambda row: (row["source_sub_scope"], row["source_doc_id"]))
        return {"enabled": True, "index": self.semantic_token_usage_envelope(occurrences)}

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
        """Write the prepared scope/stage index before the owning Build returns."""
        if write_plan.get("semantic_token_outputs_enabled") is not True:
            return
        self.semantic_tokens_dir.mkdir(parents=True, exist_ok=True)
        if write_plan["semantic_token_index_write"]:
            write_text(
                self.semantic_tokens_dir / "index.json",
                write_plan["semantic_token_index_text"],
            )
