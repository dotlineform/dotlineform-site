#!/usr/bin/env python3
"""Verify the Studio activity contract registry."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_REL_PATH = Path("assets/studio/data/activity_contract.json")

EXPECTED_SCHEMA = "activity_contract_v1"
EXPECTED_V1_PAGE_ID = "catalogue-work"
EXPECTED_V1_ACTION_ID = "save-work"
EXPECTED_V1_PURPOSE_IDS = [
    "save-canonical-data",
    "rebuild-published-work-data",
    "rebuild-lookups",
    "update-search",
]


def fail(message: str) -> None:
    raise AssertionError(message)


def load_activity_contract(repo_root: Path = REPO_ROOT) -> Mapping[str, Any]:
    path = repo_root / CONTRACT_REL_PATH
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        fail("activity contract root must be an object")
    return payload


def require_text(row: Mapping[str, Any], key: str, label: str) -> str:
    value = str(row.get(key) or "").strip()
    if not value:
        fail(f"{label} missing {key}")
    return value


def require_mapping(row: Mapping[str, Any], key: str, label: str) -> Mapping[str, Any]:
    value = row.get(key)
    if not isinstance(value, Mapping):
        fail(f"{label} missing {key} object")
    return value


def require_list(row: Mapping[str, Any], key: str, label: str) -> list[Any]:
    value = row.get(key)
    if not isinstance(value, list):
        fail(f"{label} missing {key}[]")
    return value


def verify_script_purposes(contract: Mapping[str, Any]) -> set[str]:
    purposes = require_mapping(contract, "script_purposes", "activity contract")
    seen: set[str] = set()
    for purpose_id, purpose in purposes.items():
        if not isinstance(purpose_id, str) or not purpose_id.strip():
            fail("script purpose id must be a non-empty string")
        if purpose_id in seen:
            fail(f"duplicate script purpose id: {purpose_id}")
        if not isinstance(purpose, Mapping):
            fail(f"script purpose {purpose_id} must be an object")
        require_text(purpose, "label", f"script purpose {purpose_id}")
        templates = require_list(purpose, "detail_templates", f"script purpose {purpose_id}")
        if not templates:
            fail(f"script purpose {purpose_id} detail_templates[] must not be empty")
        for index, template in enumerate(templates):
            if not isinstance(template, str) or not template.strip():
                fail(f"script purpose {purpose_id} detail_templates[{index}] must be non-empty text")
        seen.add(purpose_id)
    return seen


def verify_pages(contract: Mapping[str, Any], purpose_ids: set[str]) -> set[str]:
    pages = require_mapping(contract, "pages", "activity contract")
    action_ids: set[str] = set()
    for page_id, page in pages.items():
        if not isinstance(page_id, str) or not page_id.strip():
            fail("page id must be a non-empty string")
        if not isinstance(page, Mapping):
            fail(f"page {page_id} must be an object")
        require_text(page, "label", f"page {page_id}")
        route = require_text(page, "route", f"page {page_id}")
        if not route.startswith("/studio/"):
            fail(f"page {page_id} route must be a Studio route")
        actions = require_mapping(page, "actions", f"page {page_id}")
        if not actions:
            fail(f"page {page_id} actions must not be empty")
        for action_id, action in actions.items():
            if not isinstance(action_id, str) or not action_id.strip():
                fail(f"page {page_id} action id must be a non-empty string")
            if action_id in action_ids:
                fail(f"duplicate action id: {action_id}")
            if not isinstance(action, Mapping):
                fail(f"action {action_id} must be an object")
            require_text(action, "label", f"action {action_id}")
            require_text(action, "control_id", f"action {action_id}")
            require_text(action, "control_selector", f"action {action_id}")
            require_text(action, "control_label", f"action {action_id}")
            script_purposes = require_list(action, "script_purposes", f"action {action_id}")
            if not script_purposes:
                fail(f"action {action_id} script_purposes[] must not be empty")
            for index, reference in enumerate(script_purposes):
                if not isinstance(reference, Mapping):
                    fail(f"action {action_id} script_purposes[{index}] must be an object")
                purpose_id = require_text(reference, "id", f"action {action_id} script_purposes[{index}]")
                if purpose_id not in purpose_ids:
                    fail(f"action {action_id} references unknown script purpose {purpose_id}")
                optional = reference.get("optional")
                if not isinstance(optional, bool):
                    fail(f"action {action_id} script purpose {purpose_id} optional must be boolean")
                require_text(reference, "when", f"action {action_id} script purpose {purpose_id}")
            action_ids.add(action_id)
    return action_ids


def verify_v1_contract(contract: Mapping[str, Any]) -> None:
    pages = require_mapping(contract, "pages", "activity contract")
    page = pages.get(EXPECTED_V1_PAGE_ID)
    if not isinstance(page, Mapping):
        fail(f"missing v1 page {EXPECTED_V1_PAGE_ID}")
    if page.get("label") != "catalogue work editor":
        fail("v1 page label must be 'catalogue work editor'")
    if page.get("route") != "/studio/catalogue-work/":
        fail("v1 page route must be /studio/catalogue-work/")
    actions = require_mapping(page, "actions", f"page {EXPECTED_V1_PAGE_ID}")
    action = actions.get(EXPECTED_V1_ACTION_ID)
    if not isinstance(action, Mapping):
        fail(f"missing v1 action {EXPECTED_V1_ACTION_ID}")
    if action.get("control_id") != "catalogueWorkSave":
        fail("v1 save action control_id must be catalogueWorkSave")
    if action.get("control_selector") != "#catalogueWorkSave":
        fail("v1 save action control_selector must be #catalogueWorkSave")
    if action.get("endpoint") != "/catalogue/work/save":
        fail("v1 save action endpoint must be /catalogue/work/save")
    if action.get("no_change_activity") != "skip":
        fail("v1 save action must skip true no-change activity")
    if action.get("report_forced_rewrites") is not True:
        fail("v1 save action must report forced rewrites")

    script_purposes = require_list(action, "script_purposes", f"action {EXPECTED_V1_ACTION_ID}")
    purpose_refs = [str(row.get("id") or "").strip() for row in script_purposes if isinstance(row, Mapping)]
    if purpose_refs != EXPECTED_V1_PURPOSE_IDS:
        fail(f"v1 save action purpose order mismatch: {purpose_refs!r}")
    optional_by_id = {
        str(row.get("id") or "").strip(): row.get("optional")
        for row in script_purposes
        if isinstance(row, Mapping)
    }
    if optional_by_id.get("save-canonical-data") is not False:
        fail("save-canonical-data must be the required v1 purpose")
    for purpose_id in EXPECTED_V1_PURPOSE_IDS[1:]:
        if optional_by_id.get(purpose_id) is not True:
            fail(f"{purpose_id} must be optional in v1")


def main() -> None:
    contract = load_activity_contract(REPO_ROOT)
    schema = contract.get("schema")
    if schema != EXPECTED_SCHEMA:
        fail(f"activity contract schema must be {EXPECTED_SCHEMA}, got {schema!r}")
    purpose_ids = verify_script_purposes(contract)
    verify_pages(contract, purpose_ids)
    verify_v1_contract(contract)
    print(f"Activity contract OK: {len(purpose_ids)} script purposes")


if __name__ == "__main__":
    main()
