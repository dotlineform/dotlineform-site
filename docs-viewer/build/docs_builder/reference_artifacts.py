from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

from .common import json_text, read_json, read_text, scope_uses_external_data, utc_timestamp, write_text
from .source import DocRecord


class ReferenceArtifactsMixin:
    @property
    def references_dir(self) -> Path:
        return self.output_dir / "references"

    @property
    def references_by_doc_dir(self) -> Path:
        return self.references_dir / "by-doc"

    @property
    def references_by_target_dir(self) -> Path:
        return self.references_dir / "by-target"

    def reference_target_path(self, target_kind: str, target_id: str) -> Path:
        return self.references_by_target_dir / str(target_kind) / f"{quote(str(target_id))}.json"

    def reference_target_url(self, target_kind: str, target_id: str) -> str:
        if scope_uses_external_data(self.config):
            return (
                f"/docs/reference-target?scope={quote(self.scope_id)}"
                f"&target_kind={quote(str(target_kind))}&target_slug={quote(str(target_id))}"
            )
        return f"{self.output_url_base}/references/by-target/{quote(str(target_kind))}/{quote(str(target_id))}.json"

    def build_reference_payloads(
        self,
        docs: list[DocRecord],
        semantic_references_by_doc: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        references = [ref for doc in docs for ref in semantic_references_by_doc.get(doc.doc_id, [])]
        by_doc = {
            doc_id: {
                "header": {
                    "schema": "docs_semantic_references_by_doc_v1",
                    "scope": self.scope_id,
                    "doc_id": doc_id,
                    "count": len(refs),
                },
                "references": refs,
            }
            for doc_id, refs in semantic_references_by_doc.items() if refs
        }
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for ref in references:
            grouped.setdefault((str(ref["target_kind"]), str(ref["target_id"])), []).append(ref)
        by_target: dict[tuple[str, str], dict[str, Any]] = {}
        for key, refs in grouped.items():
            first = refs[0]
            by_target[key] = {
                "header": {
                    "schema": "docs_semantic_references_by_target_v1",
                    "scope": self.scope_id,
                    "count": len(refs),
                },
                "target_key": first["target_key"],
                "target_kind": key[0],
                "target_id": key[1],
                "target_href": first["target_href"],
                "target_title": first.get("target_title", ""),
                "target_status": first["target_status"],
                "count": len(refs),
                "references": sorted(
                    [
                        {
                            "source_scope": ref["source_scope"],
                            "source_doc_id": ref["source_doc_id"],
                            "source_title": ref["source_title"],
                            "source_viewer_url": ref["source_viewer_url"],
                            "label": ref["label"],
                            "action": ref["action"],
                            "ordinal": ref["ordinal"],
                        }
                        for ref in refs
                    ],
                    key=lambda ref: (ref["source_title"].lower(), ref["source_doc_id"], ref["ordinal"]),
                ),
            }
        targets = sorted(
            [
                {
                    "target_key": payload["target_key"],
                    "target_kind": payload["target_kind"],
                    "target_id": payload["target_id"],
                    "target_href": payload["target_href"],
                    "target_title": payload.get("target_title", ""),
                    "target_status": payload["target_status"],
                    "count": payload["count"],
                    "bucket_url": self.reference_target_url(payload["target_kind"], payload["target_id"]),
                }
                for payload in by_target.values()
            ],
            key=lambda target: (target["target_kind"], target["target_id"]),
        )
        comparable_index = {
            "header": {
                "schema": "docs_semantic_references_index_v1",
                "scope": self.scope_id,
                "count": len(references),
                "target_count": len(targets),
            },
            "targets": targets,
        }
        index_payload = {
            **comparable_index,
            "header": {
                **comparable_index["header"],
                "generated_at": self.effective_reference_generated_at(comparable_index),
            },
        }
        return {"index": index_payload, "by_doc": by_doc, "by_target": by_target}

    def effective_reference_generated_at(self, index_without_generated_at: dict[str, Any]) -> str:
        existing = read_json(self.references_dir / "index.json")
        if not isinstance(existing, dict):
            return utc_timestamp()
        header = dict(existing.get("header") or {})
        generated_at = str(header.pop("generated_at", "")).strip()
        comparable = {**existing, "header": header}
        if comparable == index_without_generated_at and generated_at:
            return generated_at
        return utc_timestamp()

    def existing_reference_records_by_doc(self, docs: list[DocRecord], target_doc_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        selected = set(target_doc_ids)
        out: dict[str, list[dict[str, Any]]] = {}
        for doc in docs:
            if doc.doc_id in selected:
                continue
            payload = read_json(self.references_by_doc_dir / f"{doc.doc_id}.json")
            refs = payload.get("references") if isinstance(payload, dict) else None
            if isinstance(refs, list):
                out[doc.doc_id] = refs
        return out
    def existing_reference_target_keys(self) -> list[tuple[str, str]]:
        if not self.references_by_target_dir.exists():
            return []
        return sorted(
            (path.parent.name, unquote(path.stem))
            for path in self.references_by_target_dir.glob("*/*.json")
        )
    def build_reference_write_plan(self, reference_payloads: dict[str, Any], *, target_doc_ids: list[str] | None) -> dict[str, Any]:
        reference_index_text = json_text(reference_payloads["index"])
        doc_text_by_id: dict[str, str] = {}
        changed_doc_ids: list[str] = []
        for doc_id, payload in reference_payloads["by_doc"].items():
            text = json_text(payload)
            doc_text_by_id[doc_id] = text
            if read_text(self.references_by_doc_dir / f"{doc_id}.json") != text:
                changed_doc_ids.append(doc_id)
        target_text_by_key: dict[tuple[str, str], str] = {}
        changed_target_keys: list[tuple[str, str]] = []
        for key, payload in reference_payloads["by_target"].items():
            text = json_text(payload)
            target_text_by_key[key] = text
            if read_text(self.reference_target_path(*key)) != text:
                changed_target_keys.append(key)
        stale_doc_ids = sorted(set(self.existing_doc_payload_ids(self.references_by_doc_dir)) - set(reference_payloads["by_doc"]))
        if target_doc_ids:
            target_set = set(target_doc_ids)
            changed_doc_ids = [doc_id for doc_id in changed_doc_ids if doc_id in target_set]
            stale_doc_ids = sorted(set(stale_doc_ids) & target_set)
        stale_target_keys = sorted(set(self.existing_reference_target_keys()) - set(reference_payloads["by_target"]))
        return {
            "reference_index_write": read_text(self.references_dir / "index.json") != reference_index_text,
            "reference_index_text": reference_index_text,
            "changed_reference_doc_ids": sorted(changed_doc_ids),
            "stale_reference_doc_ids": stale_doc_ids,
            "reference_doc_text_by_id": doc_text_by_id,
            "changed_reference_target_keys": sorted(changed_target_keys),
            "stale_reference_target_keys": stale_target_keys,
            "reference_target_text_by_key": target_text_by_key,
        }
    def write_reference_outputs(self, write_plan: dict[str, Any]) -> None:
        self.references_by_doc_dir.mkdir(parents=True, exist_ok=True)
        self.references_by_target_dir.mkdir(parents=True, exist_ok=True)
        if write_plan["reference_index_write"]:
            write_text(self.references_dir / "index.json", write_plan["reference_index_text"])
        for doc_id in write_plan["changed_reference_doc_ids"]:
            write_text(self.references_by_doc_dir / f"{doc_id}.json", write_plan["reference_doc_text_by_id"][doc_id])
        for doc_id in write_plan["stale_reference_doc_ids"]:
            (self.references_by_doc_dir / f"{doc_id}.json").unlink(missing_ok=True)
        for key in write_plan["changed_reference_target_keys"]:
            write_text(self.reference_target_path(*key), write_plan["reference_target_text_by_key"][key])
        for key in write_plan["stale_reference_target_keys"]:
            self.reference_target_path(*key).unlink(missing_ok=True)
