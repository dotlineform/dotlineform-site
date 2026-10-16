"""Working-owned eligible reader metadata beside complete management metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docs_publication_paths import confined, shared_path, working_owner
from docs_workspace_config import generated_documents_path, select_workspace_stage


def tree_ids(rows: list[dict[str, Any]]) -> set[str]:
    result: set[str] = set()
    for row in rows:
        result.add(row["doc_id"])
        result.update(tree_ids(row.get("children", [])))
    return result


class PublicMetadata:
    """Reuse loaded metadata and public membership for one generation operation.

    Saved public files provide prior eligibility. Management inputs supply the
    authoritative hierarchy, Draft and reader fields; no document/source reads.
    """

    def __init__(self, workspace: Any, ignored: frozenset[str], *, navigation: dict[str, Any], navigation_text: str | None) -> None:
        self.workspace = workspace
        self.ignored = ignored
        self.public: dict[str, dict[str, Any]] = {}
        self.public_members: dict[str, set[str]] = {}
        self.projected: dict[str, dict[str, Any]] = {}
        self.management: dict[str, dict[str, Any]] = {"": navigation}
        self.navigation_text = navigation_text
        self.eligible: dict[str, set[str]] = {}
        self.restored: dict[str, str] = {}
        self.withdrawn: dict[str, str] = {}

    def read_public(self, collection: str) -> dict[str, Any]:
        if collection not in self.public:
            path = shared_path(self.workspace, collection or "workspace", "collection_manifest" if collection else "ordinary_index")
            self.public[collection] = json.loads(path.read_bytes())
            rows = self.public[collection]["docs"]
            self.public_members[collection] = {row["doc_id"] for row in rows} if collection else tree_ids(rows)
        return self.public[collection]

    def read_management(self, collection: str) -> dict[str, Any]:
        if collection not in self.management:
            owner = working_owner(self.workspace, collection)
            filename = "manage-manifest.json" if collection else "index-tree.json"
            self.management[collection] = json.loads(confined(generated_documents_path(owner), filename).read_bytes())
        return self.management[collection]

    def membership(self, collection: str) -> set[str]:
        if collection not in self.eligible:
            self.read_public(collection)
            self.eligible[collection] = self.public_members[collection]
        return self.eligible[collection]

    def _complete(self, collection: str, payload: dict[str, Any], eligible: set[str]) -> None:
        previous = self.membership(collection)
        for doc_id in previous - eligible:
            self.withdrawn[doc_id] = collection
            self.restored.pop(doc_id, None)
        for doc_id in eligible - previous:
            self.restored[doc_id] = collection
            self.withdrawn.pop(doc_id, None)
        self.eligible[collection] = eligible
        self.projected[collection] = payload

    def ordinary(self, navigation: dict[str, Any]) -> None:
        """Select ordinary membership once and propagate actual host changes."""
        before = self.membership("")
        self.management[""] = navigation

        def project(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            result = []
            for row in rows:
                if row["draft"] or row["doc_id"] in self.ignored:
                    continue
                node = {key: value for key, value in row.items() if key not in {"draft", "children"}}
                children = project(row.get("children", []))
                if children:
                    node["children"] = children
                result.append(node)
            return result

        rows = project(navigation["docs"])
        old = self.read_public("")
        payload = {**navigation, "docs": rows}
        if old["docs"] == rows:
            payload["generated_at"] = old["generated_at"]
        current = tree_ids(rows)
        self._complete("", payload, current)
        changed_hosts = before ^ current
        for owner in select_workspace_stage(self.workspace, "working").collections:
            if owner.report_host_doc_id in changed_hosts:
                self.collection(owner.collection, self.read_management(owner.collection))

    def collection(self, collection: str, manifest: dict[str, Any]) -> None:
        """Project the selected complete management manifest without source work."""
        owner = working_owner(self.workspace, collection)
        host_eligible = owner.report_host_doc_id in self.membership("")
        self.management[collection] = manifest

        def draft(row: dict[str, Any]) -> bool:
            return False if collection == "catalogue" else row["draft"]

        rows = []
        if host_eligible:
            for row in manifest["docs"]:
                if draft(row):
                    continue
                public = {key: row[key] for key in ("doc_id", "title", "last_updated", "has_thumbnail") if key in row}
                subject = row.get("subject")
                if collection == "works" and not row.get("has_thumbnail", False) and subject is not None and len(subject) == 5 and subject.isascii() and subject.isdecimal():
                    public["subject"] = subject
                rows.append(public)
        self._complete(collection, {"docs": rows}, {row["doc_id"] for row in rows})

    def changes(self) -> list[tuple[str, Path, dict[str, Any]]]:
        """Return changed completed views; callers own their writes and queueing."""
        result = []
        for collection, payload in self.projected.items():
            if payload != self.read_public(collection):
                path = shared_path(self.workspace, collection or "workspace", "collection_manifest" if collection else "ordinary_index")
                result.append((collection, path, payload))
        return result
