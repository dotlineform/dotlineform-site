"""Confined selected byte transfers, with exact-object remote comparison."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping

from docs_artifact_locations import R2_PROVIDER, artifact_location_adapter, authenticated_remote_client_for_locations


def read_bytes(path: Path) -> bytes:
    if path.resolve() != path or not path.is_file():
        raise FileNotFoundError(f"Required publication input is unavailable: {path}")
    return path.read_bytes()


def write_bytes(path: Path, data: bytes) -> bytes:
    if path.resolve() != path:
        raise ValueError(f"Publication target must not be a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_bytes() == data:
        return data
    path.write_bytes(data)
    if path.read_bytes() != data:
        raise RuntimeError(f"Publication bytes did not verify: {path}")
    return data


def delete_path(path: Path) -> None:
    if path.resolve() != path:
        raise ValueError(f"Publication target must not be a symlink: {path}")
    path.unlink(missing_ok=True)


def completed_effect(result: dict[str, Any], phase: str, identity: str | Path) -> None:
    """Report partial-unit effects without a persisted progress ledger."""
    counts = result.setdefault("effects", {})
    counts[phase] = counts.get(phase, 0) + 1
    result["last_completed_effect"] = {"phase": phase, "target": str(identity)}


class SelectedTransfers:
    """One operation's lazily authenticated selected adapters; no listings."""

    def __init__(self, repo_root: Path, *, client: object | None = None, env_files: Iterable[Path] | None = None, environ: Mapping[str, str] | None = None) -> None:
        self.repo_root = repo_root
        self.client = client
        self.env_files = env_files
        self.environ = environ
        self.adapters: dict[Any, Any] = {}

    def transfer(self, location: Any, identity: str, *, data: bytes | None) -> None:
        if location not in self.adapters:
            if location.provider == R2_PROVIDER and self.client is None:
                self.client = authenticated_remote_client_for_locations(self.repo_root, [location], env_files=self.env_files, environ=self.environ)
            self.adapters[location] = artifact_location_adapter(self.repo_root, location, remote_client=self.client)
        adapter = self.adapters[location]
        if data is None:
            try:
                adapter.delete(identity)
            except FileNotFoundError:
                return
            if adapter.stat(identity) is not None:
                raise RuntimeError(f"Publication deletion did not verify: {identity}")
            return
        if location.provider == R2_PROVIDER:
            stat = adapter.stat(identity)
            checksum = hashlib.md5(data, usedforsecurity=False).hexdigest()
            if stat is not None and stat.size == len(data) and stat.etag.strip('"').lower() == checksum:
                return
            completed = adapter.replace(identity, data)
            if completed.size != len(data) or completed.etag.strip('"').lower() != checksum:
                raise RuntimeError(f"Publication transfer did not verify: {identity}")
        else:
            try:
                current = adapter.read(identity)
            except FileNotFoundError:
                current = None
            if current == data:
                return
            adapter.replace(identity, data)
            if not adapter.verify_bytes(identity, data):
                raise RuntimeError(f"Publication transfer did not verify: {identity}")
