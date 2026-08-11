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


TREES_DOC_ID = "d-20260501-000000-000001"
GROWTH_DOC_ID = "d-20260501-000001-000002"
REPORT_DOC_ID = "d-20260430-230000-000099"


def write_fixture_docs(repo_root: Path) -> Path:
    config_path = (
        repo_root / "docs-viewer/config/scopes/docs_scopes.json"
    )
    report_path = (
        repo_root
        / "docs-viewer/scopes/analysis/source/documents"
        / f"{REPORT_DOC_ID}.md"
    )
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        f"""---
doc_id: {REPORT_DOC_ID}
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
                                        "groups": [
                                            "subject",
                                            "form",
                                            "theme",
                                        ]
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
    reports_path = repo_root / "docs-viewer/config/reports/reports.json"
    reports_path.parent.mkdir(parents=True, exist_ok=True)
    reports_path.write_text(
        (REPO_ROOT / "docs-viewer/config/reports/reports.json").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    documents_root = (
        repo_root
        / "docs-viewer/scopes/analysis/source/sub-scopes/tags/documents"
    )
    documents_root.mkdir(parents=True)
    for doc_id, tag_id, group, description in (
        (TREES_DOC_ID, "trees", "subject", "Trees"),
        (GROWTH_DOC_ID, "trees", "theme", "Growth"),
    ):
        (documents_root / f"{doc_id}.md").write_text(
            f"""---
doc_id: {doc_id}
title: {tag_id}
added_date: "2026-05-01 00:00:00"
last_updated: 2026-05-01
group: {group}
tag_id: {tag_id}
parent_id: ""
---
# {tag_id}

{description}
""",
            encoding="utf-8",
        )
    return documents_root


def write_fixture_data(repo_root: Path) -> tuple[Path, Path, Path, Path]:
    documents_root = write_fixture_docs(repo_root)
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
    "allowed_groups": ["subject", "form", "theme"]
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
    "woodland": {
      "description": "Woodland",
      "tags": ["trees", "growth"]
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
    activity_contract_path = repo_root / "studio" / "data" / "config" / "runtime" / "activity-contract.json"
    activity_contract_path.parent.mkdir(parents=True)
    shutil.copyfile(
        REPO_ROOT / "studio" / "data" / "config" / "runtime" / "activity-contract.json",
        activity_contract_path,
    )
    return registry_path, aliases_path, assignments_path, documents_root


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
        registry_path, aliases_path, assignments_path, documents_root = (
            write_fixture_data(fixture_root)
        )
        document_names_before = sorted(path.name for path in documents_root.glob("*.md"))
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
                    "tag_id": "renewal",
                    "client_time_utc": "2026-05-22T00:00:00Z",
                    "activity_context": {
                        "correlation_id": "tag-registry-api-smoke",
                        "page_id": "tag-registry",
                        "action_id": "create-tag",
                        "route": "/studio/tag-registry/",
                        "control_id": "create-tag",
                        "control_selector": "[data-role=\"create-tag\"]",
                        "tag_id": "renewal",
                    },
                },
            )
            edited = post_json(
                f"{base_url}/mutate-tag",
                {
                    "action": "edit",
                    "tag_id": "trees",
                    "new_group": "form",
                    "primary_document": {
                        "scope": "analysis",
                        "sub_scope": "tags",
                        "doc_id": GROWTH_DOC_ID,
                    },
                    "allow_canonical_rename": False,
                    "client_time_utc": "2026-05-22T00:00:00Z",
                },
            )
            preview = post_json(
                f"{base_url}/mutate-tag-preview",
                {
                    "action": "delete",
                    "tag_id": "trees",
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

        if created.get("tag_id") != "renewal" or created.get("activity_log") != {"written_count": 1}:
            raise AssertionError(f"registry create failed: {created!r}")
        if "doc_id" in created or "document_target" in created:
            raise AssertionError(f"registry create returned document identity: {created!r}")
        if sorted(path.name for path in documents_root.glob("*.md")) != document_names_before:
            raise AssertionError("registry create changed Analysis Tag documents")
        if len(activity_rows) != 1 or activity_rows[0].get("user_action_id") != "create-tag":
            raise AssertionError(f"registry create activity failed: {activity_rows!r}")
        if activity_rows[0].get("record_groups", {}).get("tags", {}).get("sample_ids") != ["renewal"]:
            raise AssertionError(f"registry create activity tag identity failed: {activity_rows!r}")
        if not edited.get("group_changed"):
            raise AssertionError(f"registry edit failed: {edited!r}")
        if edited.get("primary_document") != {
            "scope": "analysis",
            "sub_scope": "tags",
            "doc_id": GROWTH_DOC_ID,
        }:
            raise AssertionError(
                f"registry primary-document edit failed: {edited!r}"
            )
        if edited.get("primary_document_changed") is not True:
            raise AssertionError(
                f"registry primary-document stats failed: {edited!r}"
            )
        if preview.get("series_tag_refs_rewritten") != 1 or preview.get("work_tag_refs_rewritten") != 1:
            raise AssertionError(f"registry delete preview did not report assignment rewrites: {preview!r}")
        if preview.get("blocked") is not True or preview.get("document_association_count") != 2:
            raise AssertionError(f"associated registry delete preview was not blocked: {preview!r}")
        if [row["tag_id"] for row in registry["tags"]] != ["trees", "growth", "renewal"]:
            raise AssertionError(f"registry edit did not leave expected tags: {registry!r}")
        if "primary_document" in registry["tags"][2]:
            raise AssertionError(
                f"registry create unexpectedly associated a document: {registry!r}"
            )
        if aliases["aliases"]["woodland"]["tags"] != ["trees", "growth"]:
            raise AssertionError(f"blocked delete changed alias references: {aliases!r}")
        if assignments["series"]["series-a"]["tags"][0]["tag_id"] != "trees":
            raise AssertionError(f"blocked delete changed assignments: {assignments!r}")

    print("Studio tag registry APIs OK")


if __name__ == "__main__":
    run()
