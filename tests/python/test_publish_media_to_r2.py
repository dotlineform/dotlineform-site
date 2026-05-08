#!/usr/bin/env python3
"""Focused checks for the R2 media publisher."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
PUBLISHER_PATH = SCRIPTS_DIR / "publish_media_to_r2.py"


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

    def head_object(self, key: str):
        return self.remote.get(key)

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        self.puts.append((key, path.name, content_type))


def make_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    (repo / "_config.yml").write_text(
        "\n".join(
            [
                'media_image_works: "/works/img"',
                'media_image_work_details: "/work_details/img"',
                'media_image_moments: "/moments/img"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return repo


def write_primary(media_root: Path, kind_subdir: str, filename: str, content: bytes = b"image") -> Path:
    path = media_root / f"website/pipeline/{kind_subdir}/srcset_images/primary" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_credentials_load_from_env_file_without_printing_values() -> None:
    with tempfile.TemporaryDirectory() as temp:
        env_file = Path(temp) / "r2.env"
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


def test_missing_credentials_error_names_missing_vars_only() -> None:
    try:
        publisher.load_r2_credentials(env_files=[], environ={"R2_ACCESS_KEY_ID": "access"})
    except SystemExit as exc:
        message = str(exc)
    else:
        raise AssertionError("missing credentials should exit")

    assert "R2_ACCOUNT_ID" in message
    assert "R2_ACCESS_KEY_ID" not in message
    assert "access" not in message


def test_catalogue_mapping_uses_configured_remote_prefixes_and_blocks_partial_sets() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        repo = make_repo(root)
        media_root = root / "media"
        source = write_primary(media_root, "works", "01007-primary-800.webp", b"small")

        objects, missing = publisher.discover_catalogue_primary_objects(
            repo_root=repo,
            media_base_dir=media_root,
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
        media_root = root / "media"
        for width in publisher.PRIMARY_WIDTHS:
            write_primary(media_root, "works", f"01007-primary-{width}.webp", f"image-{width}".encode("utf-8"))
        objects, _missing = publisher.discover_catalogue_primary_objects(
            repo_root=repo,
            media_base_dir=media_root,
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


def test_unchanged_remote_is_skipped_and_changed_remote_requires_force() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        repo = make_repo(root)
        media_root = root / "media"
        local_path = write_primary(media_root, "works", "01007-primary-800.webp", b"same")
        for width in [1200, 1600]:
            write_primary(media_root, "works", f"01007-primary-{width}.webp", f"image-{width}".encode("utf-8"))
        objects, _missing = publisher.discover_catalogue_primary_objects(
            repo_root=repo,
            media_base_dir=media_root,
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


if __name__ == "__main__":
    test_credentials_load_from_env_file_without_printing_values()
    test_missing_credentials_error_names_missing_vars_only()
    test_catalogue_mapping_uses_configured_remote_prefixes_and_blocks_partial_sets()
    test_symlink_escape_is_refused()
    test_dry_run_marks_missing_remote_as_would_upload()
    test_unchanged_remote_is_skipped_and_changed_remote_requires_force()
    print("publish media to R2 checks passed")
