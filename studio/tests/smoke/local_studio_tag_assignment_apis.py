#!/usr/bin/env python3
"""Smoke the direct Studio tag assignment API against a fixture repo."""

from __future__ import annotations

import json
import sys
import tempfile
import urllib.error
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


def write_fixture_assignments(repo_root: Path) -> Path:
    assignments_path = repo_root / "studio" / "data" / "canonical" / "tags" / "tag-assignments.json"
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


def post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_post_not_found(url: str) -> None:
    try:
        post_json(url, {})
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return
        raise AssertionError(f"retired assignment route returned {error.code}: {url}") from error
    raise AssertionError(f"retired assignment route still accepts POST: {url}")


def run() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        fixture_root = Path(tmp_dir)
        assignments_path = write_fixture_assignments(fixture_root)
        server = StudioAppServer(("127.0.0.1", 0), fixture_root)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            response = post_json(
                f"http://127.0.0.1:{port}/studio/api/tags/save-tags",
                {
                    "series_id": "series-a",
                    "tags": [{"tag_id": "subject:trees", "w_manual": 0.9}],
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            assert_post_not_found(
                f"http://127.0.0.1:{port}/studio/api/tags/import-tag-assignments-preview"
            )
            assert_post_not_found(
                f"http://127.0.0.1:{port}/studio/api/tags/import-tag-assignments"
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
        if persisted["series"]["series-a"]["tags"] != [{"tag_id": "subject:trees", "w_manual": 0.9}]:
            raise AssertionError(f"fixture assignments were not updated by save-tags: {persisted!r}")

    print("Studio direct tag assignment API OK")


if __name__ == "__main__":
    run()
