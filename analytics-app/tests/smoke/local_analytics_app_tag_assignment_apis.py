#!/usr/bin/env python3
"""Smoke local Analytics tag assignment APIs against a fixture repo."""

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


def write_fixture_assignments(repo_root: Path) -> Path:
    assignments_path = repo_root / "analytics-app" / "data" / "canonical" / "tag-assignments.json"
    assignments_path.parent.mkdir(parents=True)
    assignments_path.write_text(
        """{
  "tag_assignments_version": "tag_assignments_v1",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {}
}
""",
        encoding="utf-8",
    )
    return assignments_path


def write_fixture_series_index(repo_root: Path) -> Path:
    series_index_path = repo_root / "assets" / "data" / "series_index.json"
    series_index_path.parent.mkdir(parents=True)
    series_index_path.write_text(
        """{
  "series": {
    "series-a": {
      "works": []
    }
  }
}
""",
        encoding="utf-8",
    )
    return series_index_path


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
        assignments_path = write_fixture_assignments(fixture_root)
        write_fixture_series_index(fixture_root)
        server = AnalyticsAppServer(("127.0.0.1", 0), fixture_root)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            response = post_json(
                f"http://127.0.0.1:{port}/analytics/api/save-tags",
                {
                    "series_id": "series-a",
                    "tags": [{"tag_id": "subject:trees", "w_manual": 0.9}],
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            saved_payload = json.loads(assignments_path.read_text(encoding="utf-8"))
            import_assignments = {
                "version": "tag_assignments_export_v1",
                "series": {
                    "series-a": {
                        "base_row_snapshot": {"tags": [{"tag_id": "subject:trees", "w_manual": 0.9}]},
                        "staged_row": {"tags": [{"tag_id": "theme:growth", "w_manual": 0.6}]},
                    }
                },
            }
            preview = post_json(
                f"http://127.0.0.1:{port}/analytics/api/import-tag-assignments-preview",
                {
                    "import_assignments": import_assignments,
                    "import_filename": "import.json",
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            apply = post_json(
                f"http://127.0.0.1:{port}/analytics/api/import-tag-assignments",
                {
                    "import_assignments": import_assignments,
                    "import_filename": "import.json",
                    "resolutions": {},
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        persisted = json.loads(assignments_path.read_text(encoding="utf-8"))
        if not response.get("ok"):
            raise AssertionError(f"save-tags response failed: {response!r}")
        if response.get("series_id") != "series-a":
            raise AssertionError(f"unexpected series id: {response!r}")
        if saved_payload["series"]["series-a"]["tags"] != [{"tag_id": "subject:trees", "w_manual": 0.9}]:
            raise AssertionError(f"fixture assignments were not updated by save-tags: {saved_payload!r}")
        if preview.get("applicable_count") != 1:
            raise AssertionError(f"assignment import preview failed: {preview!r}")
        if not apply.get("ok") or apply.get("applied_series") != 1:
            raise AssertionError(f"assignment import apply failed: {apply!r}")
        if persisted["series"]["series-a"]["tags"] != [{"tag_id": "theme:growth", "w_manual": 0.6}]:
            raise AssertionError(f"fixture assignments import was not applied: {persisted!r}")

    print("local Analytics tag assignment APIs OK")


if __name__ == "__main__":
    run()
