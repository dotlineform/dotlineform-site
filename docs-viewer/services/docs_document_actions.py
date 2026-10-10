"""Configured action restrictions for exact managed document targets.

The first matching rule owns availability. Collection-host selectors expand from
the supplied Working configuration, without source inventories or hierarchy checks.
Capabilities project the same resolved rules consumed by operation guards.
"""

from pathlib import Path
from typing import Any, Mapping
import json
import re

from docs_document_identity import is_document_id


POLICY_SCHEMA = "docs_management_document_actions_v1"
POLICY_PATH = "docs-viewer/config/management/document-actions.json"
ACTION_ID_PATTERN = re.compile(r"[a-z][a-z0-9-]*")


def _strings(value: Any, field: str) -> list[str]:
    if (not isinstance(value, list) or not value
            or any(not isinstance(item, str) or not item or item != item.strip() for item in value)
            or len(set(value)) != len(value)):
        raise ValueError(f"{field} requires distinct non-blank strings")
    return value


def load_document_action_policy(repo_root: Path, config: Any) -> dict[str, Any]:
    """Validate the sole policy owner and resolve configured collection hosts."""
    payload = json.loads((repo_root / POLICY_PATH).read_text(encoding="utf-8"))
    if (not isinstance(payload, dict) or set(payload) != {"schema", "rules"}
            or payload["schema"] != POLICY_SCHEMA or not isinstance(payload["rules"], list)):
        raise ValueError("Invalid managed document action policy")
    rules = []
    seen = set()
    collections = {child.collection for child in config.collections}
    for raw in payload["rules"]:
        if not isinstance(raw, dict):
            raise ValueError("Document action rules must be objects")
        mode = "allow" if "allow" in raw else "deny"
        if set(raw) != {"id", "match", mode, "reason"}:
            raise ValueError("Document action rules require id, match, reason and exactly one of allow/deny")
        rule_id = raw["id"]
        if not isinstance(rule_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", rule_id) or rule_id in seen:
            raise ValueError("Document action rule IDs must be valid and distinct")
        seen.add(rule_id)
        reason = raw["reason"]
        if not isinstance(reason, str) or not reason.strip() or reason != reason.strip():
            raise ValueError(f"Document action rule {rule_id} requires a reason")
        actions = _strings(raw[mode], f"{rule_id}.{mode}")
        if any(not ACTION_ID_PATTERN.fullmatch(action) for action in actions):
            raise ValueError(f"Document action rule {rule_id} has an invalid action ID")
        match = raw["match"]
        if not isinstance(match, dict) or len(match) != 1:
            raise ValueError(f"Document action rule {rule_id} requires exactly one selector")
        if "collection_hosts" in match:
            if match["collection_hosts"] is not True:
                raise ValueError("collection_hosts must be true")
            match = {"doc_ids": [child.report_host_doc_id for child in config.collections]}
        elif "collections" in match:
            values = _strings(match["collections"], f"{rule_id}.collections")
            if set(values) - collections:
                raise ValueError(f"Document action rule {rule_id} names an unconfigured collection")
        elif "doc_ids" in match:
            values = _strings(match["doc_ids"], f"{rule_id}.doc_ids")
            if any(not is_document_id(value) for value in values):
                raise ValueError(f"Document action rule {rule_id} requires exact ordinary document IDs")
        else:
            raise ValueError(f"Document action rule {rule_id} has an unknown selector")
        rules.append({"id": rule_id, "match": match, mode: actions, "reason": reason})
    return {"schema": POLICY_SCHEMA, "rules": rules}


def document_action_state(policy: Mapping[str, Any], action_id: str, target: Mapping[str, str]) -> dict[str, Any]:
    """Resolve one exact target; unmatched targets retain their ordinary actions."""
    for rule in policy["rules"]:
        match = rule["match"]
        matched = (target.get("collection") in match["collections"] if "collections" in match
                   else not target.get("collection") and target.get("doc_id") in match["doc_ids"])
        if matched:
            allowed = action_id in rule["allow"] if "allow" in rule else action_id not in rule["deny"]
            return {"hidden": not allowed, "disabled": not allowed, "reason": "" if allowed else rule["reason"]}
    return {"hidden": False, "disabled": False, "reason": ""}


def require_document_action(
    repo_root: Path, config: Any, action_id: str, target: Mapping[str, str],
    *, policy: Mapping[str, Any] | None = None,
) -> None:
    """Reject a restricted operation before its writes or external effects."""
    state = document_action_state(policy if policy is not None else load_document_action_policy(repo_root, config), action_id, target)
    if state["disabled"]:
        raise ValueError(state["reason"])
