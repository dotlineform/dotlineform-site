"""Plan generated Docs Viewer payload changes before applying filesystem writes."""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path
from typing import Any

from .common import json, json_text, read_text, write_text


class WritePlanMixin:
    """Separate generated-output comparison from filesystem mutation."""

    def existing_doc_payload_ids(self, directory: Path) -> list[str]:
        if not directory.exists():
            return []
        return sorted(path.stem for path in directory.glob("*.json"))

    def stale_doc_payload_ids(
        self, desired_doc_ids: Collection[str], *, target_doc_ids: list[str] | None = None,
    ) -> list[str]:
        """Determine removals once, before relationship refresh and rendering."""
        existing = (
            self.existing_doc_payload_ids(self.items_dir)
            if target_doc_ids is None
            else [doc_id for doc_id in target_doc_ids if (self.items_dir / f"{doc_id}.json").is_file()]
        )
        return sorted(set(existing) - set(desired_doc_ids))

    def build_write_plan(
        self,
        index_tree_payload: dict[str, Any],
        recent_payload: dict[str, Any] | None,
        item_payloads: dict[str, dict[str, Any]],
        *,
        stale_item_ids: list[str],
        existing_tree_text: str | None = None,
    ) -> dict[str, Any]:
        """Return exact writes and removals without mutating generated output.

        Document removals were already confined to the build's selected IDs.
        A missing Recent payload means generation was not requested; leave saved
        Recents alone.
        """

        index_tree_text = json_text(index_tree_payload)
        if existing_tree_text is None:
            existing_tree_text = read_text(self.output_dir / "index-tree.json")
        recent_text = json_text(recent_payload) if recent_payload is not None else ""
        item_text_by_id: dict[str, str] = {}
        changed_item_ids: list[str] = []
        for doc_id, payload in item_payloads.items():
            text = json_text(payload)
            item_text_by_id[doc_id] = text
            if read_text(self.items_dir / f"{doc_id}.json") != text:
                changed_item_ids.append(doc_id)
        return {
            "index_tree_write": existing_tree_text != index_tree_text,
            "index_tree_text": index_tree_text,
            "recent_write": recent_payload is not None and read_text(self.output_dir / "recent.json") != recent_text,
            "recent_text": recent_text,
            "retired_recent_remove": recent_payload is not None and (self.output_dir / ".publish/recent.json").exists(),
            "changed_item_ids": sorted(changed_item_ids),
            "stale_item_ids": stale_item_ids,
            "item_text_by_id": item_text_by_id,
        }

    def write_outputs(
        self,
        write_plan: dict[str, Any],
        *,
        docs_total: int,
        tree_total: int,
        recent_total: int | None,
    ) -> None:
        """Apply one write plan and report the resulting output counts.

        Only entries selected by the plan are written or removed.
        """

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.items_dir.mkdir(parents=True, exist_ok=True)
        if write_plan["recent_write"]:
            write_text(self.output_dir / "recent.json", write_plan["recent_text"])
        if write_plan["retired_recent_remove"]:
            (self.output_dir / ".publish/recent.json").unlink(missing_ok=True)
        for doc_id in write_plan["changed_item_ids"]:
            write_text(self.items_dir / f"{doc_id}.json", write_plan["item_text_by_id"][doc_id])
        for doc_id in write_plan["stale_item_ids"]:
            (self.items_dir / f"{doc_id}.json").unlink(missing_ok=True)
        # Readers seeing the changed index can now load every referenced payload.
        if write_plan["index_tree_write"]:
            write_text(self.output_dir / "index-tree.json", write_plan["index_tree_text"])
        self.print_human_summary(
            write_plan,
            mode="write",
            docs_total=docs_total,
            tree_total=tree_total,
            recent_total=recent_total,
        )

    def print_human_summary(
        self,
        write_plan: dict[str, Any],
        *,
        mode: str,
        docs_total: int,
        tree_total: int,
        recent_total: int | None,
    ) -> None:
        doc_write_count = len(write_plan["changed_item_ids"])
        doc_remove_count = len(write_plan["stale_item_ids"])
        index_write_count = (
            (1 if write_plan["index_tree_write"] else 0)
            + (1 if write_plan["recent_write"] else 0)
        )
        verb = "would write" if mode == "dry-run" else "wrote"
        remove_verb = "would remove" if mode == "dry-run" else "removed"

        print(f"Docs build ({mode}) stage={self.config.stage}")
        print(f"  docs total: {docs_total}")
        print(f"  docs {verb}: {doc_write_count}")
        print(f"  docs {remove_verb}: {doc_remove_count}")
        print(f"  tree docs total: {tree_total}")
        print(f"  recent total: {recent_total if recent_total is not None else 'unchanged'}")
        print(f"  indexes {verb}: {index_write_count}")
        print(f"  warnings: {len(self.warnings)}")

    def diagnostics_payload(
        self,
        *,
        docs_total: int,
        docs_emitted: int,
        write_plan: dict[str, Any],
        elapsed_seconds: float,
        target_doc_ids: list[str] | None,
    ) -> dict[str, Any]:
        return {
            "stage": self.config.stage,
            "build_mode": "targeted" if target_doc_ids is not None else "full",
            "only_doc_ids": target_doc_ids or [],
            "source_files_scanned": self.source_files_scanned,
            "docs_total": docs_total,
            "docs_emitted": docs_emitted,
            "doc_payloads_changed": len(write_plan["changed_item_ids"]),
            "doc_payloads_removed": len(write_plan["stale_item_ids"]),
            "index_tree_changed": 1 if write_plan["index_tree_write"] else 0,
            "recent_changed": 1 if write_plan["recent_write"] else 0,
            "warning_count": len(self.warnings),
            "warnings": self.warnings,
            "elapsed_seconds": elapsed_seconds,
        }

    def print_diagnostics(self, diagnostics: dict[str, Any]) -> None:
        print(f"Docs builder diagnostics: {json.dumps(diagnostics, ensure_ascii=False, separators=(',', ':'))}")
