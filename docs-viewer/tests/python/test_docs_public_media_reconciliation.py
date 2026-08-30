#!/usr/bin/env python3
"""Focused checks for public media planning and reconciliation."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from repo_factory import docs_scope_record, write_docs_scope_config


REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
if str(DOCS_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_SERVICES_DIR))

from docs_public_media_reconciliation import (  # noqa: E402
    apply_public_media_reconciliation,
    plan_public_media_reconciliation,
    referenced_public_media,
)
from docs_scope_config import load_docs_scope_configs  # noqa: E402


def public_config(repo_root: Path, *, media_type: str, provider: str = "repository"):
    record = docs_scope_record(
        "example",
        scope_type="public",
        viewer_base_url="/example/",
        include_scope_param=False,
        default_doc_id="example",
        media_provider=provider,
        media_types=(media_type,),
    )
    write_docs_scope_config(repo_root, [record])
    return load_docs_scope_configs(repo_root)["example"]


def payload_files(doc_id: str, content_html: str) -> dict[Path, bytes]:
    return {
        Path("by-id") / f"{doc_id}.json": (
            json.dumps({"doc_id": doc_id, "content_html": content_html}) + "\n"
        ).encode("utf-8")
    }


def published_root(repo_root: Path, scope: str, media_type: str) -> Path:
    return (
        repo_root
        / "docs-viewer/scopes"
        / scope
        / "published/media"
        / media_type
    )


class FakeR2Client:
    def __init__(self, objects: dict[str, bytes] | None = None, *, fail_put: bool = False) -> None:
        self.objects = dict(objects or {})
        self.fail_put = fail_put
        self.deleted: list[str] = []

    def list_objects(self, prefix: str):
        return [
            SimpleNamespace(key=key, size=len(data), etag=f"etag-{len(data)}")
            for key, data in sorted(self.objects.items())
            if key.startswith(prefix)
        ]

    def get_object(self, key: str) -> bytes:
        try:
            return self.objects[key]
        except KeyError as exc:
            raise FileNotFoundError(key) from exc

    def head_object(self, key: str):
        data = self.objects.get(key)
        return None if data is None else SimpleNamespace(size=len(data), etag=f"etag-{len(data)}")

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        del content_type
        if self.fail_put:
            raise OSError("simulated R2 write failure")
        self.objects[key] = path.read_bytes()

    def delete_object(self, key: str) -> None:
        self.deleted.append(key)
        self.objects.pop(key, None)


def test_referenced_public_media_uses_exact_attributes_and_unions_collections() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        config = public_config(repo_root, media_type="img")
        prefix = "/assets/data/docs/scopes/example/media/img"
        parent = payload_files(
            "parent",
            (
                f'<img src="{prefix}/shared.png?width=2#detail">'
                f'<a href={prefix}/shared.png>Shared again</a>'
                f'<span data-src="{prefix}/ignored.png">src="{prefix}/prose.png"</span>'
            ),
        )
        child = payload_files("child", f"<a href='{prefix}/shared.png'>Shared</a>")

        references = referenced_public_media(
            config,
            [("example", parent), ("example/tags", child)],
        )

    assert references == {
        ("img", "shared.png"): ("example/tags:child", "example:parent")
    }


def test_repository_plan_and_apply_copy_retain_missing_and_remove_only_stale_public_media() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        config = public_config(repo_root, media_type="img")
        published = published_root(repo_root, "example", "img")
        published.mkdir(parents=True)
        (published / "shared.png").write_bytes(b"new shared")
        (published / "current.png").write_bytes(b"current")
        public = repo_root / "site/assets/data/docs/scopes/example/media/img"
        public.mkdir(parents=True)
        (public / "shared.png").write_bytes(b"old shared")
        (public / "current.png").write_bytes(b"current")
        (public / "retained.png").write_bytes(b"retained public")
        (public / "stale.png").write_bytes(b"stale")
        (public / ".gitkeep").write_bytes(b"")
        references = {
            ("img", "shared.png"): ("example:parent", "example/tags:child"),
            ("img", "current.png"): ("example:parent",),
            ("img", "retained.png"): ("example:parent",),
            ("img", "missing.png"): ("example:parent",),
        }

        plan = plan_public_media_reconciliation(repo_root, config, references)
        applied = apply_public_media_reconciliation(repo_root, config, references)

        assert plan["referenced_count"] == 4
        assert plan["available_count"] == 2
        assert plan["copy_count"] == 1
        assert plan["unchanged_count"] == 1
        assert plan["retained_count"] == 1
        assert plan["missing_count"] == 2
        assert plan["remove_count"] == 1
        assert plan["error_count"] == 0
        assert applied["copied_count"] == 1
        assert applied["unchanged_count"] == 1
        assert applied["retained_count"] == 1
        assert applied["missing_count"] == 1
        assert applied["removed_count"] == 1
        assert applied["error_count"] == 0
        assert (public / "shared.png").read_bytes() == b"new shared"
        assert (public / "current.png").read_bytes() == b"current"
        assert (public / "retained.png").read_bytes() == b"retained public"
        assert not (public / "missing.png").exists()
        assert not (public / "stale.png").exists()
        assert (public / ".gitkeep").is_file()


def test_r2_apply_verifies_copy_removes_stale_and_preserves_prefix_marker() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        config = public_config(repo_root, media_type="files", provider="r2")
        published = published_root(repo_root, "example", "files")
        published.mkdir(parents=True)
        (published / "download.pdf").write_bytes(b"published pdf")
        client = FakeR2Client(
            {
                "docs/example/files/": b"",
                "docs/example/files/stale.pdf": b"stale",
            }
        )
        references = {
            ("files", "download.pdf"): ("example:parent",),
        }

        plan = plan_public_media_reconciliation(
            repo_root,
            config,
            references,
            client=client,
        )
        applied = apply_public_media_reconciliation(
            repo_root,
            config,
            references,
            client=client,
        )

        assert plan["copy_count"] == 1
        assert plan["remove_count"] == 1
        assert applied["copied_count"] == 1
        assert applied["removed_count"] == 1
        assert applied["error_count"] == 0
        assert client.objects["docs/example/files/download.pdf"] == b"published pdf"
        assert "docs/example/files/stale.pdf" not in client.objects
        assert "docs/example/files/" in client.objects


def test_r2_copy_failure_is_reported_without_stopping_other_reconciliation() -> None:
    with tempfile.TemporaryDirectory() as temp_path:
        repo_root = Path(temp_path)
        config = public_config(repo_root, media_type="files", provider="r2")
        published = published_root(repo_root, "example", "files")
        published.mkdir(parents=True)
        (published / "download.pdf").write_bytes(b"published pdf")
        client = FakeR2Client(
            {"docs/example/files/stale.pdf": b"stale"},
            fail_put=True,
        )
        references = {
            ("files", "download.pdf"): ("example:parent",),
        }

        applied = apply_public_media_reconciliation(
            repo_root,
            config,
            references,
            client=client,
        )

        assert applied["copied_count"] == 0
        assert applied["removed_count"] == 1
        assert applied["error_count"] == 1
        assert applied["errors"] == ["files: simulated R2 write failure"]
        assert "docs/example/files/download.pdf" not in client.objects
        assert "docs/example/files/stale.pdf" not in client.objects
