#!/usr/bin/env python3
"""Smoke the Studio tag alias APIs against a fixture repo."""

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


def write_fixture_data(repo_root: Path) -> tuple[Path, Path]:
    data_root = repo_root / "studio" / "data" / "canonical" / "tags"
    data_root.mkdir(parents=True)
    aliases_path = data_root / "tag-aliases.json"
    registry_path = data_root / "tag-registry.json"
    aliases_path.write_text(
        """{
  "tag_aliases_version": "tag_aliases_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {
    "foliage": {
      "description": "Foliage",
      "tags": ["subject:trees"]
    }
  }
}
""",
        encoding="utf-8",
    )
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
    return aliases_path, registry_path


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
        aliases_path, _registry_path = write_fixture_data(fixture_root)
        activity_contract_path = fixture_root / "studio" / "data" / "config" / "runtime" / "activity-contract.json"
        activity_contract_path.parent.mkdir(parents=True)
        shutil.copyfile(
            REPO_ROOT / "studio" / "data" / "config" / "runtime" / "activity-contract.json",
            activity_contract_path,
        )
        server = StudioAppServer(("127.0.0.1", 0), fixture_root)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            base_url = f"http://127.0.0.1:{port}/studio/api/tags"
            created = post_json(
                f"{base_url}/create-tag-alias",
                {
                    "alias": "growth",
                    "description": " Growth ",
                    "tags": ["theme:growth"],
                    "client_time_utc": "2026-05-22T00:00:00Z",
                    "activity_context": {
                        "correlation_id": "tag-alias-api-smoke",
                        "page_id": "tag-aliases",
                        "action_id": "create-tag-alias",
                        "route": "/studio/tag-aliases/",
                        "control_id": "save-edit-alias",
                        "control_selector": "[data-role=\"save-edit-alias\"]",
                        "alias": "growth",
                    },
                },
            )
            imported = post_json(
                f"{base_url}/import-tag-aliases",
                {
                    "mode": "add",
                    "import_aliases": {
                        "aliases": {
                            "studio": {
                                "description": "Studio",
                                "tags": ["theme:growth"],
                            }
                        }
                    },
                    "import_filename": "aliases.json",
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            preview = post_json(
                f"{base_url}/mutate-tag-alias-preview",
                {
                    "alias": "foliage",
                    "new_alias": "canopy",
                    "description": "Canopy",
                    "tags": ["subject:trees", "theme:growth"],
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            edited = post_json(
                f"{base_url}/mutate-tag-alias",
                {
                    "alias": "foliage",
                    "new_alias": "canopy",
                    "description": "Canopy",
                    "tags": ["subject:trees", "theme:growth"],
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            deleted = post_json(
                f"{base_url}/delete-tag-alias",
                {
                    "alias": "studio",
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        aliases = json.loads(aliases_path.read_text(encoding="utf-8"))
        activity_rows = [
            json.loads(line)
            for line in (fixture_root / "var" / "admin" / "activity" / "activity_log.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        if created.get("alias") != "growth" or created.get("activity_log") != {"written_count": 1}:
            raise AssertionError(f"alias create failed: {created!r}")
        if created.get("summary_text") != "created alias growth; targets 1; final 2":
            raise AssertionError(f"alias create summary failed: {created!r}")
        if len(activity_rows) != 1 or activity_rows[0].get("user_action_id") != "create-tag-alias":
            raise AssertionError(f"alias create activity failed: {activity_rows!r}")
        if activity_rows[0].get("record_groups", {}).get("aliases", {}).get("sample_ids") != ["growth"]:
            raise AssertionError(f"alias create activity identity failed: {activity_rows!r}")
        if imported.get("added") != 1:
            raise AssertionError(f"alias import failed: {imported!r}")
        if not preview.get("preview") or not preview.get("renamed"):
            raise AssertionError(f"alias edit preview failed: {preview!r}")
        if not edited.get("renamed") or not edited.get("tags_changed"):
            raise AssertionError(f"alias edit failed: {edited!r}")
        if deleted.get("alias") != "studio":
            raise AssertionError(f"alias delete failed: {deleted!r}")
        if list(aliases["aliases"].keys()) != ["canopy", "growth"]:
            raise AssertionError(f"final alias keys were unexpected: {aliases!r}")
        if aliases["aliases"]["canopy"]["tags"] != ["subject:trees", "theme:growth"]:
            raise AssertionError(f"final alias tags were unexpected: {aliases!r}")
        if aliases["aliases"]["growth"]["description"] != "Growth":
            raise AssertionError(f"created alias normalization was unexpected: {aliases!r}")

    print("Studio tag alias APIs OK")


if __name__ == "__main__":
    run()
