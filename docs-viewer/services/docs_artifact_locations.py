#!/usr/bin/env python3
"""Provider adapters for Docs Viewer artifact locations.

The rest of Docs Viewer addresses artifacts by a location plus a confined
relative identity.  Filesystem containment, R2 authentication, staging, and
provider-specific I/O stay in this module.
"""

from __future__ import annotations

import contextlib
import hashlib
import mimetypes
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Protocol


REPOSITORY_PROVIDER = "repository"
EXTERNAL_LOCAL_PROVIDER = "external_local"
R2_PROVIDER = "r2"
SUPPORTED_LOCATION_PROVIDERS = {
    REPOSITORY_PROVIDER,
    EXTERNAL_LOCAL_PROVIDER,
    R2_PROVIDER,
}

LIST_CAPABILITY = "list"
READ_CAPABILITY = "read"
WRITE_CAPABILITY = "write"
REPLACE_CAPABILITY = "replace"
DELETE_CAPABILITY = "delete"
STAT_CAPABILITY = "stat"
VERIFY_BYTES_CAPABILITY = "verify_bytes"
SERVED_REFERENCE_CAPABILITY = "served_reference"
AUTHENTICATE_CAPABILITY = "authenticate"
LOCAL_STAGING_CAPABILITY = "local_staging"

FILESYSTEM_CAPABILITIES = frozenset(
    {
        LIST_CAPABILITY,
        READ_CAPABILITY,
        WRITE_CAPABILITY,
        REPLACE_CAPABILITY,
        DELETE_CAPABILITY,
        STAT_CAPABILITY,
        VERIFY_BYTES_CAPABILITY,
        SERVED_REFERENCE_CAPABILITY,
        LOCAL_STAGING_CAPABILITY,
    }
)
R2_CAPABILITIES = FILESYSTEM_CAPABILITIES | {AUTHENTICATE_CAPABILITY}
PROVIDER_CAPABILITIES = {
    REPOSITORY_PROVIDER: FILESYSTEM_CAPABILITIES,
    EXTERNAL_LOCAL_PROVIDER: FILESYSTEM_CAPABILITIES,
    R2_PROVIDER: R2_CAPABILITIES,
}


@dataclass(frozen=True)
class ArtifactLocation:
    provider: str
    path: Path


@dataclass(frozen=True)
class ArtifactStat:
    identity: str
    size: int
    etag: str = ""


class RemoteArtifactClient(Protocol):
    def list_objects(self, prefix: str) -> Iterable[object]:
        ...

    def get_object(self, key: str) -> bytes:
        ...

    def head_object(self, key: str) -> object | None:
        ...

    def put_object(self, key: str, path: Path, content_type: str) -> None:
        ...

    def delete_object(self, key: str) -> None:
        ...


def normalize_artifact_identity(value: str | Path, *, allow_empty: bool = False) -> str:
    raw = str(value).strip()
    if raw in {"", "."}:
        if allow_empty:
            return ""
        raise ValueError("artifact identity is required")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts or any(part in {"", "."} for part in path.parts):
        raise ValueError(f"artifact identity must be a confined relative path: {value!s}")
    return path.as_posix().strip("/")


def provider_capabilities(provider: str) -> frozenset[str]:
    try:
        return PROVIDER_CAPABILITIES[provider]
    except KeyError as exc:
        supported = ", ".join(sorted(SUPPORTED_LOCATION_PROVIDERS))
        raise ValueError(f"artifact location provider must be one of: {supported}") from exc


def require_location_capabilities(
    location: ArtifactLocation,
    required: Iterable[str],
    *,
    role: str,
) -> None:
    missing = sorted(set(required) - provider_capabilities(location.provider))
    if missing:
        raise ValueError(
            f"Docs artifact role {role!r} at provider {location.provider!r} "
            f"is missing required capabilities: {', '.join(missing)}"
        )


def authenticated_remote_client_for_locations(
    repo_root: Path,
    locations: Iterable[ArtifactLocation],
    *,
    client: RemoteArtifactClient | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> RemoteArtifactClient | None:
    """Resolve provider authentication inside the common location boundary."""

    if client is not None:
        return client
    authenticated_providers = {
        location.provider
        for location in locations
        if AUTHENTICATE_CAPABILITY in provider_capabilities(location.provider)
    }
    if not authenticated_providers:
        return None
    if authenticated_providers != {R2_PROVIDER}:
        providers = ", ".join(sorted(authenticated_providers))
        raise ValueError(f"no authenticated artifact client is available for providers: {providers}")

    from studio.services.media.publish_media_to_r2 import (  # noqa: PLC0415
        DEFAULT_ENV_FILES,
        R2Client,
        load_r2_credentials,
    )

    selected_env_files = list(env_files) if env_files is not None else [
        repo_root / path for path in DEFAULT_ENV_FILES
    ]
    try:
        credentials = load_r2_credentials(env_files=selected_env_files, environ=environ)
    except SystemExit as exc:
        message = str(exc).removeprefix("Error: ")
        raise RuntimeError(message) from exc
    return R2Client(credentials)


class ArtifactLocationAdapter:
    """Common artifact operations exposed to Docs Viewer workflows."""

    def __init__(self, location: ArtifactLocation, *, served_path_prefix: str = "") -> None:
        self.location = location
        self.served_path_prefix = served_path_prefix.rstrip("/")

    @property
    def capabilities(self) -> frozenset[str]:
        return provider_capabilities(self.location.provider)

    def require(self, *capabilities: str, role: str = "artifact") -> None:
        require_location_capabilities(self.location, capabilities, role=role)

    def list(self, identity: str | Path = "") -> list[ArtifactStat]:
        raise NotImplementedError

    def read(self, identity: str | Path) -> bytes:
        raise NotImplementedError

    def write(self, identity: str | Path, data: bytes, *, content_type: str = "") -> ArtifactStat:
        if self.stat(identity) is not None:
            raise FileExistsError(f"artifact already exists: {normalize_artifact_identity(identity)}")
        return self.replace(identity, data, content_type=content_type)

    def replace(self, identity: str | Path, data: bytes, *, content_type: str = "") -> ArtifactStat:
        raise NotImplementedError

    def delete(self, identity: str | Path) -> None:
        raise NotImplementedError

    def stat(self, identity: str | Path) -> ArtifactStat | None:
        raise NotImplementedError

    def verify_bytes(self, identity: str | Path, expected: bytes) -> bool:
        actual = self.read(identity)
        return len(actual) == len(expected) and hashlib.sha256(actual).digest() == hashlib.sha256(expected).digest()

    def served_reference(self, identity: str | Path) -> str:
        normalized = normalize_artifact_identity(identity)
        if not self.served_path_prefix:
            raise ValueError("artifact location has no served_path_prefix")
        return f"{self.served_path_prefix}/{normalized}"

    @contextlib.contextmanager
    def stage_local(self, identity: str | Path) -> Iterator[Path]:
        normalized = normalize_artifact_identity(identity)
        suffix = Path(normalized).suffix
        with tempfile.TemporaryDirectory(prefix="docs-artifact-stage-") as temp_dir:
            staged = Path(temp_dir) / f"artifact{suffix}"
            staged.write_bytes(self.read(normalized))
            yield staged


class FilesystemArtifactLocationAdapter(ArtifactLocationAdapter):
    def __init__(self, location: ArtifactLocation, *, root: Path, served_path_prefix: str = "") -> None:
        if location.provider not in {REPOSITORY_PROVIDER, EXTERNAL_LOCAL_PROVIDER}:
            raise ValueError("filesystem adapter requires repository or external_local provider")
        super().__init__(location, served_path_prefix=served_path_prefix)
        self.root = root.resolve()

    def resolve(self, identity: str | Path, *, allow_empty: bool = False) -> Path:
        normalized = normalize_artifact_identity(identity, allow_empty=allow_empty)
        candidate = (self.root / normalized).resolve() if normalized else self.root
        if not candidate.is_relative_to(self.root):
            raise ValueError("artifact identity escapes its configured location")
        return candidate

    def list(self, identity: str | Path = "") -> list[ArtifactStat]:
        root = self.resolve(identity, allow_empty=True)
        if not root.exists():
            return []
        paths = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
        return [
            ArtifactStat(identity=path.relative_to(self.root).as_posix(), size=path.stat().st_size)
            for path in paths
        ]

    def read(self, identity: str | Path) -> bytes:
        path = self.resolve(identity)
        if not path.is_file():
            raise FileNotFoundError(f"artifact does not exist: {normalize_artifact_identity(identity)}")
        return path.read_bytes()

    def replace(self, identity: str | Path, data: bytes, *, content_type: str = "") -> ArtifactStat:
        del content_type
        path = self.resolve(identity)
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=f".{path.name}.", dir=path.parent, delete=False) as handle:
            temporary_path = Path(handle.name)
            handle.write(data)
        temporary_path.replace(path)
        return ArtifactStat(identity=normalize_artifact_identity(identity), size=len(data))

    def delete(self, identity: str | Path) -> None:
        path = self.resolve(identity)
        if not path.is_file():
            raise FileNotFoundError(f"artifact does not exist: {normalize_artifact_identity(identity)}")
        path.unlink()

    def stat(self, identity: str | Path) -> ArtifactStat | None:
        path = self.resolve(identity)
        if not path.is_file():
            return None
        return ArtifactStat(identity=normalize_artifact_identity(identity), size=path.stat().st_size)

    @contextlib.contextmanager
    def stage_local(self, identity: str | Path) -> Iterator[Path]:
        path = self.resolve(identity)
        if not path.is_file():
            raise FileNotFoundError(f"artifact does not exist: {normalize_artifact_identity(identity)}")
        yield path


class R2ArtifactLocationAdapter(ArtifactLocationAdapter):
    def __init__(
        self,
        location: ArtifactLocation,
        *,
        client: RemoteArtifactClient,
        served_path_prefix: str = "",
    ) -> None:
        if location.provider != R2_PROVIDER:
            raise ValueError("R2 adapter requires r2 provider")
        super().__init__(location, served_path_prefix=served_path_prefix)
        self.client = client
        self.prefix = normalize_artifact_identity(location.path, allow_empty=True)

    def key(self, identity: str | Path) -> str:
        normalized = normalize_artifact_identity(identity)
        return f"{self.prefix}/{normalized}" if self.prefix else normalized

    def identity_for_key(self, key: str) -> str:
        if self.prefix:
            prefix = f"{self.prefix}/"
            if not key.startswith(prefix):
                raise ValueError("remote artifact key is outside its configured location")
            return normalize_artifact_identity(key.removeprefix(prefix))
        return normalize_artifact_identity(key)

    def list(self, identity: str | Path = "") -> list[ArtifactStat]:
        normalized = normalize_artifact_identity(identity, allow_empty=True)
        prefix = self.key(normalized) if normalized else self.prefix
        rows: list[ArtifactStat] = []
        for item in self.client.list_objects(prefix):
            key = str(getattr(item, "key", ""))
            if not key:
                continue
            rows.append(
                ArtifactStat(
                    identity=self.identity_for_key(key),
                    size=int(getattr(item, "size", 0)),
                    etag=str(getattr(item, "etag", "")),
                )
            )
        return sorted(rows, key=lambda row: row.identity)

    def read(self, identity: str | Path) -> bytes:
        return self.client.get_object(self.key(identity))

    def replace(self, identity: str | Path, data: bytes, *, content_type: str = "") -> ArtifactStat:
        normalized = normalize_artifact_identity(identity)
        suffix = Path(normalized).suffix
        with tempfile.TemporaryDirectory(prefix="docs-artifact-upload-") as temp_dir:
            path = Path(temp_dir) / f"artifact{suffix}"
            path.write_bytes(data)
            resolved_content_type = content_type or mimetypes.guess_type(normalized)[0] or "application/octet-stream"
            self.client.put_object(self.key(normalized), path, resolved_content_type)
        remote = self.stat(normalized)
        if remote is None:
            raise RuntimeError(f"remote artifact was not visible after write: {normalized}")
        return remote

    def delete(self, identity: str | Path) -> None:
        normalized = normalize_artifact_identity(identity)
        if self.stat(normalized) is None:
            raise FileNotFoundError(f"artifact does not exist: {normalized}")
        self.client.delete_object(self.key(normalized))

    def stat(self, identity: str | Path) -> ArtifactStat | None:
        normalized = normalize_artifact_identity(identity)
        remote = self.client.head_object(self.key(normalized))
        if remote is None:
            return None
        return ArtifactStat(
            identity=normalized,
            size=int(getattr(remote, "size", 0)),
            etag=str(getattr(remote, "etag", "")),
        )


def filesystem_location_root(repo_root: Path, location: ArtifactLocation) -> Path:
    if location.provider == REPOSITORY_PROVIDER:
        if location.path.is_absolute():
            raise ValueError("repository artifact locations must be repository-relative")
        root = (repo_root.resolve() / location.path).resolve()
        if not root.is_relative_to(repo_root.resolve()):
            raise ValueError("repository artifact location escapes the repository root")
        return root
    if location.provider == EXTERNAL_LOCAL_PROVIDER:
        if not location.path.is_absolute():
            raise ValueError("external_local artifact locations must resolve to absolute paths")
        return location.path.resolve()
    raise ValueError("filesystem location root requires repository or external_local provider")


def local_artifact_path(
    repo_root: Path,
    location: ArtifactLocation,
    identity: str | Path,
) -> Path | None:
    """Return a confined local path when the provider has one, otherwise none."""

    if location.provider not in {REPOSITORY_PROVIDER, EXTERNAL_LOCAL_PROVIDER}:
        return None
    root = filesystem_location_root(repo_root, location)
    return FilesystemArtifactLocationAdapter(location, root=root).resolve(identity)


def artifact_location_adapter(
    repo_root: Path,
    location: ArtifactLocation,
    *,
    served_path_prefix: str = "",
    remote_client: RemoteArtifactClient | None = None,
) -> ArtifactLocationAdapter:
    if location.provider in {REPOSITORY_PROVIDER, EXTERNAL_LOCAL_PROVIDER}:
        return FilesystemArtifactLocationAdapter(
            location,
            root=filesystem_location_root(repo_root, location),
            served_path_prefix=served_path_prefix,
        )
    if location.provider == R2_PROVIDER:
        if remote_client is None:
            raise ValueError("R2 artifact locations require an authenticated remote client")
        return R2ArtifactLocationAdapter(
            location,
            client=remote_client,
            served_path_prefix=served_path_prefix,
        )
    provider_capabilities(location.provider)
    raise AssertionError("unreachable")


__all__ = [
    "AUTHENTICATE_CAPABILITY",
    "ArtifactLocation",
    "ArtifactLocationAdapter",
    "ArtifactStat",
    "DELETE_CAPABILITY",
    "EXTERNAL_LOCAL_PROVIDER",
    "FILESYSTEM_CAPABILITIES",
    "FilesystemArtifactLocationAdapter",
    "LIST_CAPABILITY",
    "LOCAL_STAGING_CAPABILITY",
    "PROVIDER_CAPABILITIES",
    "R2_CAPABILITIES",
    "R2_PROVIDER",
    "R2ArtifactLocationAdapter",
    "READ_CAPABILITY",
    "REPLACE_CAPABILITY",
    "REPOSITORY_PROVIDER",
    "SERVED_REFERENCE_CAPABILITY",
    "STAT_CAPABILITY",
    "SUPPORTED_LOCATION_PROVIDERS",
    "VERIFY_BYTES_CAPABILITY",
    "WRITE_CAPABILITY",
    "artifact_location_adapter",
    "authenticated_remote_client_for_locations",
    "filesystem_location_root",
    "local_artifact_path",
    "normalize_artifact_identity",
    "provider_capabilities",
    "require_location_capabilities",
]
