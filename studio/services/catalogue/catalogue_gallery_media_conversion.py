"""Inventory exact local and R2 identities for the one-time Gallery conversion."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from external_workspace_paths import resolve_external_workspace_root, resolve_workspace_path
from catalogue_media_paths import configured_catalogue_media_workspace
from media.publish_media_to_r2 import R2Client
from pipeline_config import load_pipeline_config
from local_env import runtime_env


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def media_workspaces(repo_root: Path) -> dict:
    # Frozen conversion inputs retain their historical Projects owner.
    return {"generated": resolve_external_workspace_root("catalogue/generated", environ=runtime_env(repo_root=repo_root), require_exists=True),
            "staging": configured_catalogue_media_workspace(repo_root)}


def plan_media_conversion(repo_root: Path, conversions: dict, client: R2Client, *, allow_matching_copies: bool = False) -> dict[str, Any]:
    pipeline = load_pipeline_config(repo_root=repo_root)
    media = json.loads((repo_root / "site-tools/config/site-tools.json").read_text())["media"]
    # The one-time conversion owns its retired source, outside active media policy.
    detail_prefix = "work_details/img/"
    work_prefix = media["image_works"].strip("/") + "/"
    if work_prefix != "works/img/":
        raise ValueError("Review conversion for changed Catalogue media prefixes")
    remote_sources = {obj.key: obj for obj in client.list_objects(detail_prefix)}
    remote_destinations = {obj.key: obj for obj in client.list_objects(work_prefix)}
    remote, consumed = [], set()
    for uid, conversion in conversions.items():
        for width in pipeline["variants"]["primary"]["widths"]:
            tail = f"-{pipeline['variants']['primary']['suffix']}-{width}.{pipeline['encoding']['format']}"
            source, target = detail_prefix + uid + tail, work_prefix + conversion["work_id"] + tail
            obj = remote_sources.get(source)
            if obj is None or obj.size <= 0 or not obj.etag:
                raise ValueError(f"Missing or empty R2 rendition: {source}")
            existing = remote_destinations.get(target)
            if existing and (not allow_matching_copies or (existing.size, existing.etag) != (obj.size, obj.etag)):
                raise ValueError(f"R2 destination already exists or differs: {target}")
            remote.append({"source": source, "destination": target, "size": obj.size, "etag": obj.etag})
            consumed.add(source)
    for key in remote_sources.keys() - consumed:
        match = re.match(r"work_details/img/([0-9]{5}-[0-9]{3})-", key)
        if match and match[1] in conversions:
            raise ValueError(f"Unexpected rendition for a converted Detail: {key}")
    local = []
    workspaces = media_workspaces(repo_root)
    for name, workspace in workspaces.items():
        family = resolve_workspace_path(workspace, "work_details")
        for path in sorted(family.rglob("*")):
            if not path.is_file() or path.name == ".DS_Store" or path.suffix == ".json":
                continue
            match = re.match(r"([0-9]{5}-[0-9]{3})(?=[.-])", path.name)
            if not match or match[1] not in conversions:
                raise ValueError(f"Unmapped local Detail media: {path.name}")
            uid = match[1]
            suffix = path.name[len(uid):]
            relative = path.relative_to(workspace.root)
            destination = Path("works", *relative.parts[1:-1], conversions[uid]["work_id"] + suffix)
            target = resolve_workspace_path(workspace, destination)
            if target.exists() and (not allow_matching_copies or file_sha256(target) != file_sha256(path)):
                raise ValueError(f"Local destination already exists or differs: {destination}")
            local.append({"workspace": name, "source": str(relative), "destination": str(destination),
                          "sha256": file_sha256(resolve_workspace_path(workspace, relative))})
    expected = {
        f"work_details/thumbs/{uid}-{pipeline['variants']['thumb']['suffix']}-{size}.{pipeline['encoding']['format']}"
        for uid in conversions for size in pipeline["variants"]["thumb"]["sizes"]
    }
    present = {item["source"] for item in local if item["workspace"] == "generated"}
    if expected - present:
        raise ValueError(f"Missing local thumbnails: {sorted(expected - present)[:10]}")
    return {"local": local, "r2": remote,
            "unmapped_r2_keys": sorted(remote_sources.keys() - consumed)}


def verify_remote_copies(client: R2Client, operations: list[dict]) -> None:
    """Verify the complete destination inventory before changing canonical identity."""
    existing = {obj.key: obj for obj in client.list_objects("works/img/")}
    for item in operations:
        obj = existing.get(item["destination"])
        if obj is None or obj.size != item["size"] or obj.etag != item["etag"]:
            raise ValueError(f"Copied rendition does not match the source: {item['destination']}")


def validate_remote_mapping(repo_root: Path, plan: dict) -> None:
    """Confine destructive cleanup to the exact Detail-to-Work rendition mapping."""
    pipeline = load_pipeline_config(repo_root=repo_root)
    primary = pipeline["variants"]["primary"]
    expected = set()
    for uid, conversion in plan["details_to_works"].items():
        wid = conversion["work_id"]
        if not re.fullmatch(r"[0-9]{5}-[0-9]{3}", uid) or not re.fullmatch(r"[0-9]{5}", wid):
            raise ValueError("Invalid exact conversion identity in remote cleanup")
        if wid not in plan["canonical"]["works.json"]["works"]:
            raise ValueError(f"Cleanup target has no converted Work: {wid}")
        for width in primary["widths"]:
            suffix = f"-{primary['suffix']}-{width}.{pipeline['encoding']['format']}"
            expected.add((f"work_details/img/{uid}{suffix}", f"works/img/{wid}{suffix}"))
    operations = plan["media"]["r2"]
    actual = {(item["source"], item["destination"]) for item in operations}
    if actual != expected or len(actual) != len(operations):
        raise ValueError("Remote cleanup differs from the exact conversion mapping")
