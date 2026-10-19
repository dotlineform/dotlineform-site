"""Apply and transfer exact Work-owned objects, reusing completed operation effects."""

from pathlib import Path
from typing import Any, Iterable

from docs_publication_media import publication_media_bindings
from docs_publication_paths import confined
from docs_publication_transfer import completed_effect, delete_path, read_bytes, write_bytes
from docs_workspace_config import select_workspace_stage


class CatalogueMediaTransfers:
    def __init__(self, repo_root: Path, workspace: Any, transfers: Any, result: dict[str, Any]) -> None:
        self.repo_root, self.workspace, self.transfers, self.result = repo_root, workspace, transfers, result
        self.bindings: Any = None
        self.completed: set[tuple[str, str, bool]] = set()

    def apply(self, selections: Iterable[tuple[str, str]], *, deleting: bool = False) -> None:
        for key, identity in selections:
            effect = (key, identity, deleting)
            if effect in self.completed:
                continue
            if self.bindings is None:
                self.bindings = publication_media_bindings(
                    self.repo_root, select_workspace_stage(self.workspace, "preview"), workspace=self.workspace,
                )
            preview_owner, destination = self.bindings[key]
            preview = confined(preview_owner.path, identity)
            self.result.update(phase="Catalogue media Preview", target=f"{key}/{identity}")
            if deleting:
                delete_path(preview)
                data = None
            else:
                source_owner = {"primary": self.workspace.assets.work_primary,
                                "thumbs": self.workspace.assets.work_thumbnails,
                                "files": self.workspace.assets.work_files}[key.rsplit("/", 1)[1]]
                data = write_bytes(preview, read_bytes(confined(source_owner.path, identity)))
            completed_effect(self.result, "Preview files removed" if deleting else "Preview files applied", preview)
            self.result["phase"] = "Catalogue media distribution"
            self.transfers.transfer(destination.location, identity, data=data)
            completed_effect(self.result, "media files removed" if deleting else "media files distributed", identity)
            self.completed.add(effect)
