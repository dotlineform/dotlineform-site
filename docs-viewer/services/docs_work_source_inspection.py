"""Run-local inspection of refreshed Work sources for filesystem reports."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class WorkSource:
    work_id: str
    title: str
    source_id: str
    directory: str
    filename: str


def collect_work_sources(
    works: Mapping[str, Mapping[str, Any]], source_config: Mapping[str, Any],
) -> list[WorkSource]:
    """Project saved declarations using one checked source map, without file reads.

    The Catalogue reader owns field validity. Preserve literal components and
    incomplete/missing-file semantics; only absent source identity uses default.
    """
    sources = []
    for work_id, record in works.items():
        folder, filename = record.get("project_folder"), record.get("project_filename")
        if folder in (None, "") or filename in (None, ""):
            continue
        source_id = record.get("media_source_id", source_config["default"])
        if source_id not in source_config["roots"]:
            raise ValueError(f"unknown Work media source identity: {source_id}")
        subfolder = record.get("project_subfolder")
        directory = f"{folder}/{subfolder}" if subfolder not in (None, "") else folder
        sources.append(WorkSource(work_id, record["title"], source_id, directory, filename))
    return sources


@dataclass(frozen=True)
class InspectedDirectory:
    path: Path
    parts: tuple[str, ...]
    present: bool


@dataclass(frozen=True)
class SourceRoot:
    subdir: str
    directory: InspectedDirectory


def _relative_parts(value: str) -> tuple[str, ...]:
    """Confine the exact filesystem target without normalising its components."""
    parts = tuple(value.split("/"))
    if (not value or value.startswith("/") or "\\" in value
            or any(part in {"", ".", ".."} for part in parts)
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ValueError("Work media path must be a canonical relative POSIX path")
    return parts


def regular_file_identity(metadata: os.stat_result | None) -> tuple[int, int] | None:
    """Reuse inspected file type and physical identity, including filesystem aliases."""
    if metadata is None or not stat.S_ISREG(metadata.st_mode):
        return None
    return metadata.st_dev, metadata.st_ino


class WorkSourceInspection:
    """Inspect each distinct path/prefix once during one synchronous report run.

    Construction accepts an already resolved Projects base and performs no I/O.
    Explicit root, directory, file and entry calls retain their completed facts.
    Parent confinement and no-symlink checks allow lexical joins without another
    resolve()/stat() walk. Results never survive the operation or replace checks
    at later Finder/source actions. Media processing uses its existing resolver.
    """

    def __init__(self, projects_base: Path) -> None:
        self._directories = {(): InspectedDirectory(projects_base, (), True)}
        self._metadata: dict[tuple[str, ...], os.stat_result | None] = {}

    def _read_child(self, parent: InspectedDirectory, name: str) -> os.stat_result | None:
        parts = (*parent.parts, name)
        if parts not in self._metadata:
            metadata = None
            if parent.present:
                try:
                    metadata = (parent.path / name).lstat()
                except FileNotFoundError:
                    pass
                except OSError as error:
                    raise ValueError(f"Work source path could not be inspected safely: {'/'.join(parts)}") from error
            self._metadata[parts] = metadata
        return self._metadata[parts]

    def _directory(self, parts: tuple[str, ...]) -> InspectedDirectory:
        if parts not in self._directories:
            parent = self._directory(parts[:-1])
            metadata = self._read_child(parent, parts[-1])
            if metadata is not None:
                if stat.S_ISLNK(metadata.st_mode):
                    raise ValueError(f"Work media path must not contain symlinks: {'/'.join(parts)}")
                if not stat.S_ISDIR(metadata.st_mode):
                    raise ValueError(f"Work media path parent must be a directory: {'/'.join(parts)}")
            self._directories[parts] = InspectedDirectory(
                parent.path / parts[-1], parts, metadata is not None,
            )
        return self._directories[parts]

    def source_roots(
        self, configured_roots: Mapping[str, str], source_ids: Iterable[str],
    ) -> dict[str, SourceRoot]:
        """Inspect selected configured roots once; unavailable roots fail the run."""
        roots = {}
        for source_id in source_ids:
            subdir = PurePosixPath(configured_roots[source_id]).as_posix()
            directory = self._directory(_relative_parts(subdir))
            if not directory.present:
                raise ValueError(f"Work media source root does not exist: {subdir}")
            if not os.access(directory.path, os.R_OK):
                raise ValueError(f"Work media source root is not readable: {subdir}")
            roots[source_id] = SourceRoot(subdir, directory)
        return roots

    def directory(self, root: SourceRoot, relative: str) -> InspectedDirectory:
        """Resolve required parent segments, carrying missing ancestors forward."""
        return self._directory((*root.directory.parts, *_relative_parts(relative)))

    def file(self, directory: InspectedDirectory, filename: str) -> os.stat_result | None:
        """Inspect an exact declared leaf without following symlinks or rereading it."""
        if len(_relative_parts(filename)) != 1:
            raise ValueError("Work source filename must identify one direct child")
        metadata = self._read_child(directory, filename)
        if metadata is not None and stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"Work media path must not contain symlinks: {'/'.join((*directory.parts, filename))}")
        return metadata

    def entry(self, directory: InspectedDirectory, entry: os.DirEntry[str]) -> os.stat_result | None:
        """Reuse known declared-file metadata or inspect one listed child, unfollowed.

        The report owns candidate filtering and its existing symlink outcome.
        Only a matching entry needs metadata; no unused size/content work is added.
        """
        parts = (*directory.parts, entry.name)
        if parts not in self._metadata:
            try:
                self._metadata[parts] = entry.stat(follow_symlinks=False)
            except FileNotFoundError:
                self._metadata[parts] = None
            except OSError as error:
                raise ValueError("Work source file could not be inspected") from error
        return self._metadata[parts]
