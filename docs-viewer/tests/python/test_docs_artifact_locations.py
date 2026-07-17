#!/usr/bin/env python3
"""Provider-independent Docs artifact location adapter checks."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from docs_artifact_locations import (
    AUTHENTICATE_CAPABILITY,
    EXTERNAL_LOCAL_PROVIDER,
    R2_PROVIDER,
    REPOSITORY_PROVIDER,
    ArtifactLocation,
    artifact_location_adapter,
    normalize_artifact_identity,
    require_location_capabilities,
)


class FakeRemoteClient:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}

    def list_objects(self, prefix: str):
        return [
            SimpleNamespace(key=key, size=len(value), etag=f"etag-{len(value)}")
            for key, value in self.objects.items()
            if key.startswith(prefix)
        ]

    def get_object(self, key: str) -> bytes:
        try:
            return self.objects[key]
        except KeyError as exc:
            raise FileNotFoundError(key) from exc

    def head_object(self, key: str):
        value = self.objects.get(key)
        return None if value is None else SimpleNamespace(size=len(value), etag=f"etag-{len(value)}")

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        self.objects[key] = path.read_bytes()
        self.content_types[key] = content_type

    def delete_object(self, key: str) -> None:
        del self.objects[key]


@pytest.mark.parametrize("provider", [REPOSITORY_PROVIDER, EXTERNAL_LOCAL_PROVIDER])
def test_filesystem_adapters_share_the_complete_artifact_workflow(tmp_path: Path, provider: str) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    location_path = Path("published/media") if provider == REPOSITORY_PROVIDER else tmp_path / "external-media"
    location = ArtifactLocation(provider=provider, path=location_path)
    adapter = artifact_location_adapter(
        repo_root,
        location,
        served_path_prefix="/docs/media/example/img",
    )

    written = adapter.write("nested/example.png", b"first", content_type="image/png")
    assert written.identity == "nested/example.png"
    assert adapter.read("nested/example.png") == b"first"
    assert adapter.stat("nested/example.png").size == 5  # type: ignore[union-attr]
    assert [row.identity for row in adapter.list()] == ["nested/example.png"]
    assert adapter.verify_bytes("nested/example.png", b"first") is True
    assert adapter.served_reference("nested/example.png") == "/docs/media/example/img/nested/example.png"
    with adapter.stage_local("nested/example.png") as staged:
        assert staged.read_bytes() == b"first"
    with pytest.raises(FileExistsError):
        adapter.write("nested/example.png", b"duplicate")

    adapter.replace("nested/example.png", b"second")
    assert adapter.read("nested/example.png") == b"second"
    adapter.delete("nested/example.png")
    assert adapter.stat("nested/example.png") is None


def test_r2_adapter_confines_keys_and_uses_the_same_artifact_workflow(tmp_path: Path) -> None:
    client = FakeRemoteClient()
    location = ArtifactLocation(provider=R2_PROVIDER, path=Path("docs/example/img"))
    adapter = artifact_location_adapter(
        tmp_path,
        location,
        served_path_prefix="https://media.example.test/docs/example/img",
        remote_client=client,
    )

    adapter.write("nested/example.png", b"first")
    assert client.content_types["docs/example/img/nested/example.png"] == "image/png"
    assert adapter.read("nested/example.png") == b"first"
    assert [row.identity for row in adapter.list()] == ["nested/example.png"]
    assert adapter.verify_bytes("nested/example.png", b"first") is True
    assert adapter.served_reference("nested/example.png") == (
        "https://media.example.test/docs/example/img/nested/example.png"
    )
    with adapter.stage_local("nested/example.png") as staged:
        assert staged.read_bytes() == b"first"

    adapter.replace("nested/example.png", b"second")
    assert adapter.stat("nested/example.png").size == 6  # type: ignore[union-attr]
    adapter.delete("nested/example.png")
    assert adapter.stat("nested/example.png") is None


@pytest.mark.parametrize("identity", ["", ".", "../escape", "nested/../escape", "/absolute"])
def test_artifact_identity_rejects_empty_absolute_and_escaping_paths(identity: str) -> None:
    with pytest.raises(ValueError):
        normalize_artifact_identity(identity)


def test_capability_errors_name_the_role_provider_and_missing_capability() -> None:
    location = ArtifactLocation(provider=REPOSITORY_PROVIDER, path=Path("published/media"))
    with pytest.raises(ValueError) as exc_info:
        require_location_capabilities(location, [AUTHENTICATE_CAPABILITY], role="published.media.img")
    message = str(exc_info.value)
    assert "published.media.img" in message
    assert "repository" in message
    assert "authenticate" in message


def test_r2_adapter_requires_an_authenticated_client(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="authenticated remote client"):
        artifact_location_adapter(
            tmp_path,
            ArtifactLocation(provider=R2_PROVIDER, path=Path("docs/example/img")),
        )
