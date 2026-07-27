#!/usr/bin/env python3
"""Smoke the Studio tag registry APIs against a fixture repo."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path
from threading import Thread


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STUDIO_SERVER_DIR = REPO_ROOT / "studio" / "app" / "server" / "studio"
for path in (STUDIO_SERVER_DIR,):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from studio_app_server import StudioAppServer  # noqa: E402


def write_fixture_data(repo_root: Path) -> tuple[Path, Path, Path]:
    data_root = repo_root / "studio" / "data" / "canonical" / "tags"
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
    },
    {
      "tag_id": "theme:growth",
      "group": "theme",
      "label": "growth",
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
    activity_contract_path = repo_root / "studio" / "data" / "config" / "runtime" / "activity-contract.json"
    activity_contract_path.parent.mkdir(parents=True)
    shutil.copyfile(
        REPO_ROOT / "studio" / "data" / "config" / "runtime" / "activity-contract.json",
        activity_contract_path,
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
            base_url = f"http://127.0.0.1:{port}/studio/api/tags"
            created = post_json(
                f"{base_url}/create-tag",
                {
                    "group": "theme",
                    "slug": "renewal",
                    "description": " Renewal ",
                    "client_time_utc": "2026-05-22T00:00:00Z",
                    "activity_context": {
                        "correlation_id": "tag-registry-api-smoke",
                        "page_id": "tag-registry",
                        "action_id": "create-tag",
                        "route": "/studio/tag-registry/",
                        "control_id": "create-tag",
                        "control_selector": "[data-role=\"create-tag\"]",
                        "tag_id": "theme:renewal",
                    },
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
        activity_rows = [
            json.loads(line)
            for line in (fixture_root / "var" / "admin" / "activity" / "activity_log.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        if created.get("tag_id") != "theme:renewal" or created.get("activity_log") != {"written_count": 1}:
            raise AssertionError(f"registry create failed: {created!r}")
        if len(activity_rows) != 1 or activity_rows[0].get("user_action_id") != "create-tag":
            raise AssertionError(f"registry create activity failed: {activity_rows!r}")
        if activity_rows[0].get("record_groups", {}).get("tags", {}).get("sample_ids") != ["theme:renewal"]:
            raise AssertionError(f"registry create activity tag identity failed: {activity_rows!r}")
        if not edited.get("description_changed"):
            raise AssertionError(f"registry edit failed: {edited!r}")
        if preview.get("series_tag_refs_rewritten") != 1 or preview.get("work_tag_refs_rewritten") != 1:
            raise AssertionError(f"registry delete preview did not report assignment rewrites: {preview!r}")
        if deleted.get("series_tag_refs_rewritten") != 1 or deleted.get("work_tag_refs_rewritten") != 1:
            raise AssertionError(f"registry delete did not rewrite assignments: {deleted!r}")
        if [row["tag_id"] for row in registry["tags"]] != ["theme:growth", "theme:renewal"]:
            raise AssertionError(f"registry delete did not leave expected tags: {registry!r}")
        if aliases["aliases"]["woodland"]["tags"] != ["theme:growth"]:
            raise AssertionError(f"alias references were not rewritten: {aliases!r}")
        if assignments["series"]["series-a"].get("tags") != []:
            raise AssertionError(f"series tag references were not removed: {assignments!r}")
        if assignments["series"]["series-a"].get("works"):
            raise AssertionError(f"empty work assignment row was not removed: {assignments!r}")

    print("Studio tag registry APIs OK")


if __name__ == "__main__":
    run()
