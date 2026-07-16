from __future__ import annotations

from typing import Any

from .common import json, json_text, read_text, write_text
from .source import DocRecord


class WritePlanMixin:
    def existing_doc_payload_ids(self, directory: Path) -> list[str]:
        if not directory.exists():
            return []
        return sorted(path.stem for path in directory.glob("*.json"))
    def build_write_plan(
        self,
        index_tree_payload: dict[str, Any],
        recent_payload: dict[str, Any],
        publication_recent_payload: dict[str, Any] | None,
        item_payloads: dict[str, dict[str, Any]],
        reference_payloads: dict[str, Any],
        *,
        target_doc_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        index_tree_text = json_text(index_tree_payload)
        recent_text = json_text(recent_payload)
        publication_recent_text = json_text(publication_recent_payload) if publication_recent_payload else ""
        item_text_by_id: dict[str, str] = {}
        changed_item_ids: list[str] = []
        for doc_id, payload in item_payloads.items():
            text = json_text(payload)
            item_text_by_id[doc_id] = text
            if read_text(self.items_dir / f"{doc_id}.json") != text:
                changed_item_ids.append(doc_id)
        existing_item_ids = self.existing_doc_payload_ids(self.items_dir)
        desired_item_ids = sorted(item_payloads)
        stale_item_ids = sorted(set(existing_item_ids) - set(desired_item_ids))
        if target_doc_ids:
            stale_item_ids = sorted(set(stale_item_ids) & set(target_doc_ids))
        return {
            "index_tree_write": read_text(self.output_dir / "index-tree.json") != index_tree_text,
            "index_tree_text": index_tree_text,
            "recent_write": read_text(self.output_dir / "recent.json") != recent_text,
            "recent_text": recent_text,
            "publication_recent_write": (
                read_text(self.output_dir / ".publish/recent.json") != publication_recent_text
                if publication_recent_payload
                else False
            ),
            "publication_recent_text": publication_recent_text,
            "publication_recent_remove": publication_recent_payload is None and (self.output_dir / ".publish/recent.json").exists(),
            "changed_item_ids": sorted(changed_item_ids),
            "stale_item_ids": stale_item_ids,
            "item_text_by_id": item_text_by_id,
            **self.build_reference_write_plan(reference_payloads, target_doc_ids=target_doc_ids),
        }
    def write_outputs(
        self,
        write_plan: dict[str, Any],
        *,
        docs_total: int,
        tree_total: int,
        recent_total: int,
        reference_total: int,
    ) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.items_dir.mkdir(parents=True, exist_ok=True)
        if write_plan["index_tree_write"]:
            write_text(self.output_dir / "index-tree.json", write_plan["index_tree_text"])
        if write_plan["recent_write"]:
            write_text(self.output_dir / "recent.json", write_plan["recent_text"])
        if write_plan["publication_recent_write"]:
            write_text(self.output_dir / ".publish/recent.json", write_plan["publication_recent_text"])
        if write_plan["publication_recent_remove"]:
            (self.output_dir / ".publish/recent.json").unlink(missing_ok=True)
        for doc_id in write_plan["changed_item_ids"]:
            write_text(self.items_dir / f"{doc_id}.json", write_plan["item_text_by_id"][doc_id])
        for doc_id in write_plan["stale_item_ids"]:
            (self.items_dir / f"{doc_id}.json").unlink(missing_ok=True)
        self.write_reference_outputs(write_plan)
        self.print_human_summary(
            write_plan,
            mode="write",
            docs_total=docs_total,
            tree_total=tree_total,
            recent_total=recent_total,
            reference_total=reference_total,
        )
    def print_dry_run(
        self,
        index_payload: dict[str, Any],
        index_tree_payload: dict[str, Any],
        recent_payload: dict[str, Any],
        reference_payloads: dict[str, Any],
        write_plan: dict[str, Any],
    ) -> None:
        self.print_human_summary(
            write_plan,
            mode="dry-run",
            docs_total=len(index_payload["docs"]),
            tree_total=len(index_tree_payload["docs"]),
            recent_total=len(recent_payload["docs"]),
            reference_total=reference_payloads["index"]["header"]["count"],
        )

    def print_human_summary(
        self,
        write_plan: dict[str, Any],
        *,
        mode: str,
        docs_total: int,
        tree_total: int,
        recent_total: int,
        reference_total: int,
    ) -> None:
        doc_write_count = len(write_plan["changed_item_ids"])
        doc_remove_count = len(write_plan["stale_item_ids"])
        reference_write_count = (
            (1 if write_plan["reference_index_write"] else 0)
            + len(write_plan["changed_reference_doc_ids"])
            + len(write_plan["changed_reference_target_keys"])
        )
        reference_remove_count = (
            len(write_plan["stale_reference_doc_ids"])
            + len(write_plan["stale_reference_target_keys"])
        )
        index_write_count = (
            (1 if write_plan["index_tree_write"] else 0)
            + (1 if write_plan["recent_write"] else 0)
            + (1 if write_plan["publication_recent_write"] else 0)
            + (1 if write_plan["reference_index_write"] else 0)
        )
        verb = "would write" if mode == "dry-run" else "wrote"
        remove_verb = "would remove" if mode == "dry-run" else "removed"

        print(f"Docs build ({mode}) scope={self.scope_id}")
        print(f"  docs total: {docs_total}")
        print(f"  docs {verb}: {doc_write_count}")
        print(f"  docs {remove_verb}: {doc_remove_count}")
        print(f"  tree docs total: {tree_total}")
        print(f"  recent total: {recent_total}")
        print(f"  references total: {reference_total}")
        print(f"  references {verb}: {reference_write_count}")
        print(f"  references {remove_verb}: {reference_remove_count}")
        print(f"  indexes {verb}: {index_write_count}")
        print(f"  warnings: {len(self.warnings)}")

    def diagnostics_payload(
        self,
        *,
        docs: list[DocRecord],
        write_plan: dict[str, Any],
        elapsed_seconds: float,
        target_doc_ids: list[str] | None,
    ) -> dict[str, Any]:
        return {
            "scope": self.scope_id,
            "build_mode": "targeted" if target_doc_ids is not None else "full",
            "only_doc_ids": target_doc_ids or [],
            "source_files_scanned": self.source_files_scanned,
            "docs_emitted": len(docs),
            "doc_payloads_changed": len(write_plan["changed_item_ids"]),
            "doc_payloads_removed": len(write_plan["stale_item_ids"]),
            "index_tree_changed": 1 if write_plan["index_tree_write"] else 0,
            "recent_changed": 1 if write_plan["recent_write"] else 0,
            "publication_recent_changed": 1 if write_plan["publication_recent_write"] else 0,
            "reference_index_changed": 1 if write_plan["reference_index_write"] else 0,
            "reference_by_doc_payloads_changed": len(write_plan["changed_reference_doc_ids"]),
            "reference_by_doc_payloads_removed": len(write_plan["stale_reference_doc_ids"]),
            "reference_by_target_payloads_changed": len(write_plan["changed_reference_target_keys"]),
            "reference_by_target_payloads_removed": len(write_plan["stale_reference_target_keys"]),
            "warning_count": len(self.warnings),
            "warnings": self.warnings,
            "elapsed_seconds": elapsed_seconds,
        }

    def print_diagnostics(self, diagnostics: dict[str, Any]) -> None:
        print(f"Docs builder diagnostics: {json.dumps(diagnostics, ensure_ascii=False, separators=(',', ':'))}")
