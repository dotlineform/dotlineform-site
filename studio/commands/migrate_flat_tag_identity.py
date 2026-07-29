#!/usr/bin/env python3
"""Preview, apply, or validate the flat tag identity cutover."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict


REPO_ROOT = Path(__file__).resolve().parents[2]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
if str(STUDIO_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(STUDIO_SERVICES_DIR))

from tags import tag_flat_identity_migration as migration  # noqa: E402
from tags import tag_source_model as tag_source  # noqa: E402
from tags import tag_write_transactions as transactions  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root containing studio/data/canonical/tags.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Atomically replace registry, aliases, and assignments after validation.",
    )
    parser.add_argument(
        "--show-mapping",
        action="store_true",
        help="Include the complete old-to-flat tag ID map in preview output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    registry_path = (repo_root / tag_source.REGISTRY_REL_PATH).resolve()
    aliases_path = (repo_root / tag_source.ALIASES_REL_PATH).resolve()
    assignments_path = (repo_root / tag_source.ASSIGNMENTS_REL_PATH).resolve()
    registry_payload = tag_source.load_json_object(registry_path, {}, "tag registry")
    aliases_payload = tag_source.load_aliases(aliases_path)
    assignments_payload = tag_source.load_assignments(assignments_path)

    if registry_payload.get("tag_registry_version") == migration.TARGET_REGISTRY_VERSION:
        result = migration.validate_flat_identity_sources(
            registry_payload,
            aliases_payload,
            assignments_payload,
        )
        print(json.dumps({"mode": "validate", "ok": True, **result}, indent=2))
        return 0

    now_utc = tag_source.utc_now()
    registry_updated, aliases_updated, assignments_updated, stats = (
        migration.project_flat_identity_sources(
            registry_payload,
            aliases_payload,
            assignments_payload,
            now_utc=now_utc,
        )
    )
    id_map = stats.pop("id_map")
    result: Dict[str, Any] = {
        "mode": "write" if args.write else "preview",
        "ok": True,
        "updated_at_utc": now_utc,
        **stats,
    }
    if args.show_mapping:
        result["id_map"] = id_map
    if args.write:
        transactions.atomic_write_many(
            {
                registry_path: registry_updated,
                aliases_path: aliases_updated,
                assignments_path: assignments_updated,
            }
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
