#!/usr/bin/env python3
"""Smoke local Analytics tag registry APIs against a fixture repo."""

from __future__ import annotations

import json
import sys
import tempfile
import urllib.request
from pathlib import Path
from threading import Thread


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ANALYTICS_SERVER_DIR = REPO_ROOT / "analytics-app" / "app" / "server"
ANALYTICS_PACKAGE_DIR = ANALYTICS_SERVER_DIR / "analytics_app"
for path in (ANALYTICS_SERVER_DIR, ANALYTICS_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from analytics_app_server import AnalyticsAppServer  # noqa: E402


def write_fixture_data(repo_root: Path) -> tuple[Path, Path, Path]:
    data_root = repo_root / "analytics-app" / "data" / "canonical"
    data_root.mkdir(parents=True)
    registry_path = data_root / "tag-registry.json"
    aliases_path = data_root / "tag-aliases.json"
    assignments_path = data_root / "tag-assignments.json"
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
      "description": "Trees"
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
    "woodland": {
      "description": "Woodland",
      "tags": ["subject:trees", "theme:growth"]
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
        server = AnalyticsAppServer(("127.0.0.1", 0), fixture_root)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            base_url = f"http://127.0.0.1:{port}/analytics/api"
            imported = post_json(
                f"{base_url}/import-tag-registry",
                {
                    "mode": "add",
                    "import_registry": {
                        "tags": [
                            {
                                "tag_id": "theme:growth",
                                "group": "theme",
                                "label": "growth",
                                "description": "Growth",
                            }
                        ]
                    },
                    "import_filename": "registry.json",
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            edited = post_json(
                f"{base_url}/mutate-tag",
                {
                    "action": "edit",
                    "tag_id": "subject:trees",
                    "description": "Canopy",
                    "allow_canonical_rename": False,
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            preview = post_json(
                f"{base_url}/mutate-tag-preview",
                {
                    "action": "delete",
                    "tag_id": "subject:trees",
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            deleted = post_json(
                f"{base_url}/mutate-tag",
                {
                    "action": "delete",
                    "tag_id": "subject:trees",
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

        if imported.get("added") != 1:
            raise AssertionError(f"registry import failed: {imported!r}")
        if not edited.get("description_changed"):
            raise AssertionError(f"registry edit failed: {edited!r}")
        if preview.get("series_tag_refs_rewritten") != 1 or preview.get("work_tag_refs_rewritten") != 1:
            raise AssertionError(f"registry delete preview did not report assignment rewrites: {preview!r}")
        if deleted.get("series_tag_refs_rewritten") != 1 or deleted.get("work_tag_refs_rewritten") != 1:
            raise AssertionError(f"registry delete did not rewrite assignments: {deleted!r}")
        if [row["tag_id"] for row in registry["tags"]] != ["theme:growth"]:
            raise AssertionError(f"registry delete did not leave expected tags: {registry!r}")
        if aliases["aliases"]["woodland"]["tags"] != ["theme:growth"]:
            raise AssertionError(f"alias references were not rewritten: {aliases!r}")
        if assignments["series"]["series-a"].get("tags") != []:
            raise AssertionError(f"series tag references were not removed: {assignments!r}")
        if assignments["series"]["series-a"].get("works"):
            raise AssertionError(f"empty work assignment row was not removed: {assignments!r}")

    print("local Analytics tag registry APIs OK")


if __name__ == "__main__":
    run()
