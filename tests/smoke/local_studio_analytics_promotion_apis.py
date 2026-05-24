#!/usr/bin/env python3
"""Smoke local Studio analytics promote/demote APIs against a fixture repo."""

from __future__ import annotations

import json
import sys
import tempfile
import urllib.request
from pathlib import Path
from threading import Thread


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from studio.app.server.studio.studio_app_server import StudioAppServer  # noqa: E402


def write_fixture_data(repo_root: Path) -> tuple[Path, Path, Path]:
    data_root = repo_root / "assets" / "studio" / "data"
    data_root.mkdir(parents=True)
    registry_path = data_root / "tag_registry.json"
    aliases_path = data_root / "tag_aliases.json"
    assignments_path = data_root / "tag_assignments.json"
    registry_path.write_text(
        """{
  "tag_registry_version": "tag_registry_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {
    "allowed_groups": ["subject", "theme"]
  },
  "tags": [
    {
      "tag_id": "subject:trees",
      "group": "subject",
      "label": "trees",
      "status": "active",
      "description": "Trees"
    },
    {
      "tag_id": "theme:growth",
      "group": "theme",
      "label": "growth",
      "status": "active",
      "description": "Growth"
    }
  ]
}
""",
        encoding="utf-8",
    )
    aliases_path.write_text(
        """{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {
    "foliage": {
      "description": "Foliage",
      "tags": ["subject:trees"]
    },
    "growth-alias": {
      "description": "Growth alias",
      "tags": ["theme:growth"]
    }
  }
}
""",
        encoding="utf-8",
    )
    assignments_path.write_text(
        """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {
    "series-a": {
      "tags": [{"tag_id": "subject:trees", "w_manual": 0.6}],
      "works": {
        "00001": {
          "tags": [{"tag_id": "subject:trees", "w_manual": 0.9}]
        }
      }
    }
  }
}
""",
        encoding="utf-8",
    )
    return registry_path, aliases_path, assignments_path


def post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        fixture_root = Path(tmp_dir)
        registry_path, aliases_path, assignments_path = write_fixture_data(fixture_root)
        server = StudioAppServer(("127.0.0.1", 0), fixture_root)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            base_url = f"http://127.0.0.1:{port}/studio/api/analytics"
            promoted_preview = post_json(
                f"{base_url}/promote-tag-alias-preview",
                {
                    "alias": "foliage",
                    "group": "theme",
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            promoted = post_json(
                f"{base_url}/promote-tag-alias",
                {
                    "alias": "foliage",
                    "group": "theme",
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            demoted_preview = post_json(
                f"{base_url}/demote-tag-preview",
                {
                    "tag_id": "subject:trees",
                    "alias_targets": ["theme:growth"],
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            demoted = post_json(
                f"{base_url}/demote-tag",
                {
                    "tag_id": "subject:trees",
                    "alias_targets": ["theme:growth"],
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        aliases = json.loads(aliases_path.read_text(encoding="utf-8"))
        assignments = json.loads(assignments_path.read_text(encoding="utf-8"))

        if promoted_preview.get("new_tag_id") != "theme:foliage":
            raise AssertionError(f"promotion preview failed: {promoted_preview!r}")
        if promoted.get("canonical_added") != 1 or promoted.get("alias_deleted") != 1:
            raise AssertionError(f"promotion failed: {promoted!r}")
        if demoted_preview.get("series_tag_refs_rewritten") != 1 or demoted_preview.get("work_tag_refs_rewritten") != 1:
            raise AssertionError(f"demotion preview failed: {demoted_preview!r}")
        if demoted.get("series_tag_refs_rewritten") != 1 or demoted.get("work_tag_refs_rewritten") != 1:
            raise AssertionError(f"demotion failed: {demoted!r}")
        registry_ids = [row["tag_id"] for row in registry["tags"]]
        if registry_ids != ["theme:growth", "theme:foliage"]:
            raise AssertionError(f"final registry was unexpected: {registry!r}")
        if "foliage" in aliases["aliases"]:
            raise AssertionError(f"promoted alias was not removed: {aliases!r}")
        if aliases["aliases"]["trees"]["tags"] != ["theme:growth"]:
            raise AssertionError(f"demoted alias was not created: {aliases!r}")
        if assignments["series"]["series-a"]["tags"] != [{"tag_id": "theme:growth", "w_manual": 0.6}]:
            raise AssertionError(f"series assignment was not rewritten: {assignments!r}")
        if assignments["series"]["series-a"]["works"]["00001"]["tags"] != [{"tag_id": "theme:growth", "w_manual": 0.9}]:
            raise AssertionError(f"work assignment was not rewritten: {assignments!r}")

    print("local Studio analytics promote/demote APIs OK")


if __name__ == "__main__":
    run()
