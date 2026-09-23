"""Preview or apply the reviewed one-time Catalogue Gallery data/media conversion."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)

from catalogue.catalogue_gallery_conversion import plan_gallery_conversion, source_fingerprints, write_conversion_plan
from catalogue.catalogue_gallery_media_conversion import (
    file_sha256, media_workspaces, plan_media_conversion, verify_remote_copies, validate_remote_mapping,
)
from catalogue.catalogue_galleries import read_galleries
from catalogue.catalogue_json_build import populate_catalogue_output
from catalogue.catalogue_lookup import DEFAULT_LOOKUP_DIR, build_and_write_catalogue_lookup
from catalogue.catalogue_output_paths import output_path
from catalogue.catalogue_source import DEFAULT_SOURCE_DIR
from catalogue.catalogue_transactions import atomic_write_many
from media.publish_media_to_r2 import R2Client, load_r2_credentials


def _copy_remote(items: list[dict], client: R2Client) -> None:
    """Bound parallel I/O; surface failures and wait for already-running requests."""
    with ThreadPoolExecutor(max_workers=8) as executor:
        for start in range(0, len(items), 512):
            batches = [items[offset:min(offset + 64, len(items))] for offset in range(start, min(start + 512, len(items)), 64)]
            list(executor.map(client.copy_objects, batches))
            completed = min(start + 512, len(items))
            print(f"R2 copies: {completed}/{len(items)}", flush=True)


def apply_conversion(repo_root: Path, plan: dict, client: R2Client) -> None:
    source_dir = repo_root / DEFAULT_SOURCE_DIR
    if plan.get("schema") != "catalogue_gallery_conversion_v1" or set(plan["canonical"]) != {
        "works.json", "series.json", "galleries.json", "galleries-by-work.json",
    }:
        raise ValueError("Invalid Gallery conversion plan")
    # An explicit rerun after canonical persistence completes output/cleanup from
    # the same reviewed mapping, provided no canonical edits have intervened.
    if all((source_dir / name).is_file() and json.loads((source_dir / name).read_text()) == payload
           for name, payload in plan["canonical"].items()):
        if any((source_dir / "work_details").glob("*.json")):
            raise ValueError("Unexpected Detail source after canonical conversion")
        finish_conversion(repo_root, plan, client)
        return
    expected = plan_gallery_conversion(source_dir)
    if {key: value for key, value in plan.items() if key != "media"} != expected:
        raise ValueError("Conversion plan no longer matches canonical source; review a new plan")
    media = plan["media"]
    if media != plan_media_conversion(repo_root, expected["details_to_works"], client, allow_matching_copies=True):
        raise ValueError("Media inventory changed; review a new plan before applying")
    workspaces = media_workspaces(repo_root)
    # Re-inventory every source before the first write. Existing destination copies
    # are accepted only when identical, allowing an explicit rerun after interruption.
    remote_sources = {obj.key: obj for obj in client.list_objects("work_details/img/")}
    remote_targets = {obj.key: obj for obj in client.list_objects("works/img/")}
    for item in media["r2"]:
        source = remote_sources.get(item["source"])
        if source is None or (source.size, source.etag) != (item["size"], item["etag"]):
            raise ValueError(f"R2 source changed: {item['source']}")
        target = remote_targets.get(item["destination"])
        if target and (target.size, target.etag) != (item["size"], item["etag"]):
            raise ValueError(f"R2 destination collision: {item['destination']}")
    for item in media["local"]:
        workspace = workspaces[item["workspace"]]
        source, target = output_path(workspace, item["source"]), output_path(workspace, item["destination"])
        if file_sha256(source) != item["sha256"]:
            raise ValueError(f"Local source changed: {item['source']}")
        if target.exists() and file_sha256(target) != item["sha256"]:
            raise ValueError(f"Local destination collision: {item['destination']}")

    pending = [item for item in media["r2"] if item["destination"] not in remote_targets]
    _copy_remote(pending, client)
    verify_remote_copies(client, media["r2"])
    for item in media["local"]:
        workspace = workspaces[item["workspace"]]
        source, target = output_path(workspace, item["source"]), output_path(workspace, item["destination"])
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(source.read_bytes())
        if file_sha256(target) != item["sha256"]:
            raise ValueError(f"Copied local media differs: {item['destination']}")
    if source_fingerprints(source_dir) != plan["source_sha256"]:
        raise ValueError("Canonical source changed while media was copied; no canonical data changed")
    atomic_write_many(
        {source_dir / name: payload for name, payload in plan["canonical"].items()},
        delete_paths=[source_dir / name for name in plan["retire_source_files"]],
    )
    finish_conversion(repo_root, plan, client)


def finish_conversion(repo_root: Path, plan: dict, client: R2Client) -> None:
    """Complete ordinary output generation and exact old-media cleanup."""
    source_dir = repo_root / DEFAULT_SOURCE_DIR
    media, workspaces = plan["media"], media_workspaces(repo_root)
    read_galleries(source_dir, plan["canonical"]["works.json"]["works"])
    verify_remote_copies(client, media["r2"])
    print("Canonical conversion written; refreshing Work/Series output and Studio lookup", flush=True)
    output = populate_catalogue_output(repo_root, write=True)
    if output["status"] != "completed":
        raise ValueError("Canonical conversion saved; Catalogue output is incomplete")
    build_and_write_catalogue_lookup(source_dir, repo_root / DEFAULT_LOOKUP_DIR)
    for item in media["local"]:
        source = output_path(workspaces[item["workspace"]], item["source"])
        if source.exists():
            if file_sha256(source) != item["sha256"]:
                raise ValueError(f"Old local media changed; retained: {item['source']}")
            source.unlink()
    print(json.dumps({"status": "converted_old_r2_retained", "counts": plan["counts"],
                      "local_media": len(media["local"]), "r2_media": len(media["r2"])}), flush=True)


def remove_old_remote_media(repo_root: Path, plan: dict, client: R2Client) -> None:
    """Separately authorised removal, after canonical conversion and verification."""
    source_dir = repo_root / DEFAULT_SOURCE_DIR
    if plan.get("schema") != "catalogue_gallery_conversion_v1":
        raise ValueError("Invalid Gallery conversion plan")
    if set(plan["canonical"]) != {"works.json", "series.json", "galleries.json", "galleries-by-work.json"}:
        raise ValueError("Invalid canonical conversion targets")
    for name, payload in plan["canonical"].items():
        if json.loads((source_dir / name).read_text()) != payload:
            raise ValueError("Canonical data differs from the reviewed conversion; cleanup stopped")
    media = plan["media"]
    validate_remote_mapping(repo_root, plan)
    verify_remote_copies(client, media["r2"])
    # Output is usable from new identities. Delete only the listed old objects.
    for start in range(0, len(media["r2"]), 1000):
        originals = {obj.key: obj for obj in client.list_objects("work_details/img/")}
        keys = []
        for item in media["r2"][start:start + 1000]:
            original = originals.get(item["source"])
            if original is None:
                continue
            if (original.size, original.etag) != (item["size"], item["etag"]):
                raise ValueError(f"Old R2 media changed; retained: {item['source']}")
            keys.append(item["source"])
        if keys:
            client.delete_objects(keys)
        print(f"R2 old objects removed: {min(start + 1000, len(media['r2']))}/{len(media['r2'])}", flush=True)
    verify_remote_copies(client, media["r2"])
    print(json.dumps({"status": "completed", "counts": plan["counts"],
                      "local_media": len(media["local"]), "r2_media": len(media["r2"])}), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--plan", type=Path, help="Write a review plan; canonical data and media are read-only")
    modes.add_argument("--apply", type=Path, help="Convert canonical/local data and copy R2 media; retain old R2 objects")
    modes.add_argument("--remove-old-media", type=Path, help="Separately approve removal of the plan's old R2 objects")
    args = parser.parse_args()
    client = R2Client(load_r2_credentials(env_files=[REPO_ROOT / ".env.local"]))
    if args.plan:
        destination = args.plan.resolve()
        if not destination.is_relative_to(REPO_ROOT / "var"):
            raise ValueError("Review plans belong beneath repository var/")
        plan = plan_gallery_conversion(REPO_ROOT / DEFAULT_SOURCE_DIR)
        plan["media"] = plan_media_conversion(REPO_ROOT, plan["details_to_works"], client)
        write_conversion_plan(plan, destination)
        print(json.dumps({"status": "planned", "counts": plan["counts"],
                          "local_media": len(plan["media"]["local"]), "r2_media": len(plan["media"]["r2"]),
                          "unmapped_r2_keys": len(plan["media"]["unmapped_r2_keys"])}))
    elif args.apply:
        apply_conversion(REPO_ROOT, json.loads(args.apply.read_text()), client)
    else:
        remove_old_remote_media(REPO_ROOT, json.loads(args.remove_old_media.read_text()), client)


if __name__ == "__main__":
    main()
