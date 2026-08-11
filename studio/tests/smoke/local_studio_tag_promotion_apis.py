#!/usr/bin/env python3
"""Smoke the Studio tag promote/demote APIs against a fixture repo."""

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


def write_analysis_tags_fixture(repo_root: Path) -> None:
    report_path = (
        repo_root
        / "docs-viewer/scopes/analysis/source/documents"
        / "d-20260430-230000-000099.md"
    )
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        """---
doc_id: d-20260430-230000-000099
title: Tags
added_date: "2026-04-30 23:00:00"
last_updated: 2026-04-30
parent_id: ""
---
# Tags

:::report
id: docs_subscope
access: public
sub_scope: tags
:::
""",
        encoding="utf-8",
    )
    reports_path = repo_root / "docs-viewer/config/reports/reports.json"
    reports_path.parent.mkdir(parents=True)
    shutil.copyfile(
        REPO_ROOT / "docs-viewer/config/reports/reports.json",
        reports_path,
    )
    config_path = repo_root / "docs-viewer/config/scopes/docs_scopes.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps(
            {
                "schema_version": "docs_scopes_v3",
                "scopes": [
                    {
                        "scope_id": "analysis",
                        "scope_type": "local",
                        "meta": "analysis",
                        "scope_root": {
                            "provider": "repository",
                            "path": "docs-viewer/scopes/analysis",
                        },
                        "source": {"build_media": {}},
                        "published": {
                            "media": {
                                "img": {
                                    "reference_prefix": "docs/analysis/img",
                                    "served_path_prefix": "/docs/media/analysis/img",
                                    "build_inputs": [],
                                }
                            }
                        },
                        "public_projection": None,
                        "viewer_base_url": "/docs/",
                        "include_scope_param": True,
                        "default_doc_id": "",
                        "non_loadable_doc_ids": [],
                        "manage_only_tree_root_ids": [],
                        "allow_unresolved_parent_ids": False,
                        "sub_scopes": [
                            {
                                "sub_scope": "tags",
                                "title": "Tags",
                                "ui_statuses": [],
                                "sub_scope_customisation": {
                                    "id": "analysis_tags",
                                    "settings": {
                                        "groups": ["subject", "theme"]
                                    },
                                },
                                "public_projection": None,
                            }
                        ],
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    documents_root = (
        repo_root
        / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
    )
    documents_root.mkdir(parents=True)
    (documents_root / "d-20260501-000000-000001.md").write_text(
        """---
doc_id: d-20260501-000000-000001
title: Unassociated document
added_date: "2026-05-01 00:00:00"
last_updated: 2026-05-01
group: subject
parent_id: ""
---
# Unassociated document
""",
        encoding="utf-8",
    )


def write_fixture_data(repo_root: Path) -> tuple[Path, Path, Path]:
    write_analysis_tags_fixture(repo_root)
    data_root = repo_root / "studio" / "data" / "canonical" / "tags"
    data_root.mkdir(parents=True)
    registry_path = data_root / "tag-registry.json"
    aliases_path = data_root / "tag-aliases.json"
    assignments_path = data_root / "tag-assignments.json"
    registry_path.write_text(
        """{
  "tag_registry_version": "tag_registry_v6",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "policy": {
    "allowed_groups": ["subject", "theme"]
  },
  "tags": [
    {
      "tag_id": "trees",
      "group": "subject",
      "updated_at_utc": "2026-05-01T00:00:00Z"
    },
    {
      "tag_id": "growth",
      "group": "theme",
      "updated_at_utc": "2026-05-01T00:00:00Z"
    }
  ]
}
""",
        encoding="utf-8",
    )
    aliases_path.write_text(
        """{
  "tag_aliases_version": "tag_aliases_v2",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "aliases": {
    "foliage": {
      "description": "Foliage",
      "tags": ["trees"]
    },
    "growth-alias": {
      "description": "Growth alias",
      "tags": ["growth"]
    }
  }
}
""",
        encoding="utf-8",
    )
    assignments_path.write_text(
        """{
  "tag_assignments_version": "tag_assignments_v2",
  "updated_at_utc": "2026-05-01T00:00:00Z",
  "series": {
    "series-a": {
      "tags": [{"tag_id": "trees", "w_manual": 0.6}],
      "works": {
        "00001": {
          "tags": [{"tag_id": "trees", "w_manual": 0.9}]
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
            base_url = f"http://127.0.0.1:{port}/studio/api/tags"
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
                    "tag_id": "trees",
                    "alias_targets": ["growth"],
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            demoted = post_json(
                f"{base_url}/demote-tag",
                {
                    "tag_id": "trees",
                    "alias_targets": ["growth"],
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

        if promoted_preview.get("new_tag_id") != "foliage":
            raise AssertionError(f"promotion preview failed: {promoted_preview!r}")
        if promoted.get("canonical_added") != 1 or promoted.get("alias_deleted") != 1:
            raise AssertionError(f"promotion failed: {promoted!r}")
        if demoted_preview.get("series_tag_refs_rewritten") != 1 or demoted_preview.get("work_tag_refs_rewritten") != 1:
            raise AssertionError(f"demotion preview failed: {demoted_preview!r}")
        if demoted.get("series_tag_refs_rewritten") != 1 or demoted.get("work_tag_refs_rewritten") != 1:
            raise AssertionError(f"demotion failed: {demoted!r}")
        registry_ids = [row["tag_id"] for row in registry["tags"]]
        if registry_ids != ["growth", "foliage"]:
            raise AssertionError(f"final registry was unexpected: {registry!r}")
        if "foliage" in aliases["aliases"]:
            raise AssertionError(f"promoted alias was not removed: {aliases!r}")
        if aliases["aliases"]["trees"]["tags"] != ["growth"]:
            raise AssertionError(f"demoted alias was not created: {aliases!r}")
        if assignments["series"]["series-a"]["tags"] != [{"tag_id": "growth", "w_manual": 0.6}]:
            raise AssertionError(f"series assignment was not rewritten: {assignments!r}")
        if assignments["series"]["series-a"]["works"]["00001"]["tags"] != [{"tag_id": "growth", "w_manual": 0.9}]:
            raise AssertionError(f"work assignment was not rewritten: {assignments!r}")

    print("Studio tag promote/demote APIs OK")


if __name__ == "__main__":
    run()
