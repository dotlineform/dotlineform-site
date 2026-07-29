#!/usr/bin/env python3
"""Preview, apply, or validate the tag Registry document-link cutover."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for services_dir in (STUDIO_SERVICES_DIR, DOCS_SERVICES_DIR):
    if str(services_dir) not in sys.path:
        sys.path.insert(0, str(services_dir))

from docs_document_location import canonical_sub_scope_document_url  # noqa: E402
from tags import tag_registry_v5_migration as migration  # noqa: E402
from tags import tag_source_model as tag_source  # noqa: E402
from tags import tag_write_transactions as transactions  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Atomically replace only tag-registry.json after validation.",
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

    if registry_payload.get("tag_registry_version") == tag_source.TAG_REGISTRY_VERSION:
        result = migration.validate_tag_registry_v5(
            registry_payload,
            aliases_payload,
            assignments_payload,
        )
        print(json.dumps({"mode": "validate", "ok": True, **result}, indent=2))
        return 0

    now_utc = tag_source.utc_now()
    registry_updated, stats = migration.project_tag_registry_v5(
        registry_payload,
        aliases_payload,
        assignments_payload,
        now_utc=now_utc,
        document_url_for_id=lambda doc_id: canonical_sub_scope_document_url(
            repo_root,
            "analysis",
            "tags",
            doc_id,
        ),
    )
    if args.write:
        transactions.atomic_write_many({registry_path: registry_updated})
    print(
        json.dumps(
            {
                "mode": "write" if args.write else "preview",
                "ok": True,
                "updated_at_utc": now_utc,
                **stats,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
