#!/usr/bin/env python3
"""Focused checks for the R2 media publisher."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from types import SimpleNamespace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "scripts"
PUBLISHER_PATH = REPO_ROOT / "studio" / "services" / "media" / "publish_media_to_r2.py"


def load_publisher_module():
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("publish_media_to_r2", PUBLISHER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load publish_media_to_r2.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


publisher = load_publisher_module()


class FakeR2Client:
    def __init__(self, remote=None):
        self.remote = remote or {}
        self.puts = []
        self.deletes = []

    def head_object(self, key: str):
        return self.remote.get(key)

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        self.puts.append((key, path.name, content_type))

    def delete_object(self, key: str) -> None:
        self.deletes.append(key)


def make_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    path = repo / "site-tools/config/site-tools.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "site_tools_config_v1",
                "media": {
                    "image_works": "/works/img",
                    "image_work_details": "/work_details/img",
                    "image_moments": "/moments/img",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return repo


def write_primary(media_root: Path, kind_subdir: str, filename: str, content: bytes = b"image") -> Path:
    path = media_root / kind_subdir / "srcset_images" / "primary" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_credentials_load_from_env_file_without_printing_values() -> None:
    with tempfile.TemporaryDirectory() as temp:
        env_file = Path(temp) / ".env.local"
        env_file.write_text(
            "\n".join(
                [
                    "R2_ACCOUNT_ID=account",
                    "R2_ACCESS_KEY_ID=access",
                    "R2_SECRET_ACCESS_KEY=placeholder",
                    "R2_BUCKET=bucket",
                    "R2_ENDPOINT=https://example.r2.cloudflarestorage.com",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        credentials = publisher.load_r2_credentials(env_files=[env_file], environ={})

    assert credentials.account_id == "account"
    assert credentials.access_key_id == "access"
    assert credentials.secret_access_key == "placeholder"
    assert credentials.bucket == "bucket"
    assert credentials.endpoint == "https://example.r2.cloudflarestorage.com"


def test_default_env_file_is_env_local() -> None:
    assert publisher.DEFAULT_ENV_FILES == (Path(".env.local"),)


def test_missing_credentials_error_names_missing_vars_only() -> None:
    try:
        publisher.load_r2_credentials(env_files=[], environ={"R2_ACCESS_KEY_ID": "access"})
    except SystemExit as exc:
        message = str(exc)
    else:
        raise AssertionError("missing credentials should exit")

    assert "R2_ACCOUNT_ID" in message
    assert ".env.local" in message
    assert "R2_ACCESS_KEY_ID" not in message
    assert "access" not in message


def test_catalogue_mapping_uses_configured_remote_prefixes_and_blocks_partial_sets() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        repo = make_repo(root)
        media_root = root / "projects-base/catalogue/media"
        source = write_primary(media_root, "works", "01007-primary-800.webp", b"small")

        objects, missing = publisher.discover_catalogue_primary_objects(
            repo_root=repo,
            media_root=media_root,
            kinds=["works"],
            item_id="01007",
            allow_partial=False,
        )

    assert len(objects) == 1
    assert objects[0].local_path == source.resolve()
    assert objects[0].object_key == "works/img/01007-primary-800.webp"
    assert objects[0].blocked_reason == "missing variants: 1200, 1600"
    assert [item.missing_widths for item in missing] == [[1200, 1600]]


def test_symlink_escape_is_refused() -> None:
    if not hasattr(os, "symlink"):
        return
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        allowed = root / "allowed"
        outside = root / "outside.webp"
        allowed.mkdir()
        outside.write_bytes(b"outside")
        symlink = allowed / "01007-primary-800.webp"
        os.symlink(outside, symlink)

        try:
            publisher.ensure_allowed_file(symlink, allowed)
        except SystemExit as exc:
            message = str(exc)
        else:
            raise AssertionError("symlink escape should exit")

    assert "outside allowlisted root" in message


def test_dry_run_marks_missing_remote_as_would_upload() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        repo = make_repo(root)
        media_root = root / "projects-base/catalogue/media"
        for width in publisher.PRIMARY_WIDTHS:
            write_primary(media_root, "works", f"01007-primary-{width}.webp", f"image-{width}".encode("utf-8"))
        objects, _missing = publisher.discover_catalogue_primary_objects(
            repo_root=repo,
            media_root=media_root,
            kinds=["works"],
            item_id="01007",
        )
        results = publisher.plan_and_publish(
            objects=objects,
            client=FakeR2Client(),
            write=False,
            force=False,
        )

    assert {result.status for result in results} == {"would_upload"}
    assert len(results) == 3


def test_high_level_catalogue_upload_runner_is_reused_by_studio() -> None:
    with tempfile.TemporaryDirectory() as temp:
        projects_base = Path(temp) / "projects-base"
        media_root = projects_base / "catalogue/media"
        for width in publisher.PRIMARY_WIDTHS:
            write_primary(media_root, "works", f"01007-primary-{width}.webp", f"image-{width}".encode("utf-8"))

        report_payload = publisher.run_catalogue_upload(
            repo_root=REPO_ROOT,
            kind="works",
            item_id="01007",
            write=False,
            force=True,
            client=FakeR2Client(),
            environ={"DOTLINEFORM_PROJECTS_BASE_DIR": str(projects_base)},
            env_files=[],
        )

    assert report_payload["counts"] == {"would_upload": 3}
    assert report_payload["mode"] == "dry-run"
    assert report_payload["media_versions"] == []


def test_unchanged_remote_is_skipped_and_changed_remote_requires_force() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        repo = make_repo(root)
        media_root = root / "projects-base/catalogue/media"
        local_path = write_primary(media_root, "works", "01007-primary-800.webp", b"same")
        for width in [1200, 1600]:
            write_primary(media_root, "works", f"01007-primary-{width}.webp", f"image-{width}".encode("utf-8"))
        objects, _missing = publisher.discover_catalogue_primary_objects(
            repo_root=repo,
            media_root=media_root,
            kinds=["works"],
            item_id="01007",
        )
        md5 = publisher.file_md5(local_path)
        remote = {
            "works/img/01007-primary-800.webp": publisher.RemoteObject(size=local_path.stat().st_size, etag=f'"{md5}"'),
            "works/img/01007-primary-1200.webp": publisher.RemoteObject(size=99, etag='"different"'),
        }
        results = publisher.plan_and_publish(
            objects=objects,
            client=FakeR2Client(remote),
            write=False,
            force=False,
        )
        forced_client = FakeR2Client(remote)
        forced = publisher.plan_and_publish(
            objects=objects,
            client=forced_client,
            write=True,
            force=True,
        )

    statuses = {result.object_key: result.status for result in results}
    assert statuses["works/img/01007-primary-800.webp"] == "unchanged"
    assert statuses["works/img/01007-primary-1200.webp"] == "blocked_changed"
    assert statuses["works/img/01007-primary-1600.webp"] == "would_upload"
    forced_statuses = {result.object_key: result.status for result in forced}
    assert forced_statuses["works/img/01007-primary-1200.webp"] == "overwritten"
    assert forced_statuses["works/img/01007-primary-1600.webp"] == "uploaded"
    assert [put[0] for put in forced_client.puts] == [
        "works/img/01007-primary-1200.webp",
        "works/img/01007-primary-1600.webp",
    ]


def test_delete_plan_uses_deterministic_remote_keys_and_requires_write() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        repo = make_repo(root)
        objects = publisher.build_catalogue_remote_objects(repo_root=repo, kind_name="works", item_id="01007")
        remote = {
            "works/img/01007-primary-800.webp": publisher.RemoteObject(size=10, etag='"a"'),
            "works/img/01007-primary-1200.webp": publisher.RemoteObject(size=20, etag='"b"'),
        }
        dry_client = FakeR2Client(remote)
        dry_results = publisher.plan_and_delete(objects=objects, client=dry_client, write=False)
        write_client = FakeR2Client(remote)
        write_results = publisher.plan_and_delete(objects=objects, client=write_client, write=True)

    assert [obj.object_key for obj in objects] == [
        "works/img/01007-primary-800.webp",
        "works/img/01007-primary-1200.webp",
        "works/img/01007-primary-1600.webp",
    ]
    assert {result.object_key: result.status for result in dry_results} == {
        "works/img/01007-primary-800.webp": "would_delete",
        "works/img/01007-primary-1200.webp": "would_delete",
        "works/img/01007-primary-1600.webp": "missing",
    }
    assert dry_client.deletes == []
    assert {result.object_key: result.status for result in write_results} == {
        "works/img/01007-primary-800.webp": "deleted",
        "works/img/01007-primary-1200.webp": "deleted",
        "works/img/01007-primary-1600.webp": "missing",
    }
    assert write_client.deletes == [
        "works/img/01007-primary-800.webp",
        "works/img/01007-primary-1200.webp",
    ]


def test_complete_upload_promotes_once_and_incomplete_set_does_not_promote() -> None:
    results = [
        publisher.PublishResult(
            scope="catalogue",
            kind="works",
            item_id="01007",
            width=width,
            local_path=f"01007-primary-{width}.webp",
            object_key=f"works/img/01007-primary-{width}.webp",
            size=10,
            md5="digest",
            status="overwritten" if width == 800 else "unchanged",
        )
        for width in publisher.PRIMARY_WIDTHS
    ]
    results.append(
        publisher.PublishResult(
            scope="catalogue",
            kind="work_details",
            item_id="01007-001",
            width=800,
            local_path="01007-001-primary-800.webp",
            object_key="work_details/img/01007-001-primary-800.webp",
            size=10,
            md5="digest",
            status="uploaded",
        )
    )
    calls = []
    original = publisher.finalize_catalogue_media_version
    publisher.finalize_catalogue_media_version = lambda repo_root, **kwargs: (
        calls.append(kwargs)
        or SimpleNamespace(
            advanced=kwargs["advance"],
            work_id="01007",
            previous_version=1,
            media_version=2 if kwargs["advance"] else 1,
            public_json_path="site/assets/works/index/01007.json",
        )
    )
    try:
        finalized = publisher.finalize_complete_catalogue_uploads(
            repo_root=REPO_ROOT,
            results=results,
        )
    finally:
        publisher.finalize_catalogue_media_version = original

    assert calls == [{"kind": "works", "item_id": "01007", "advance": True}]
    assert [(item.kind, item.status, item.media_version) for item in finalized] == [
        ("work_details", "not_promoted", None),
        ("works", "promoted", 2),
    ]


def test_moments_are_not_a_catalogue_publisher_kind() -> None:
    assert set(publisher.CATALOGUE_KINDS) == {"works", "work_details"}


if __name__ == "__main__":
    test_credentials_load_from_env_file_without_printing_values()
    test_default_env_file_is_site_env()
    test_missing_credentials_error_names_missing_vars_only()
    test_catalogue_mapping_uses_configured_remote_prefixes_and_blocks_partial_sets()
    test_symlink_escape_is_refused()
    test_dry_run_marks_missing_remote_as_would_upload()
    test_unchanged_remote_is_skipped_and_changed_remote_requires_force()
    test_delete_plan_uses_deterministic_remote_keys_and_requires_write()
    print("publish media to R2 checks passed")
