"""Read the workspace's exact Working ordinary-document exclusion list."""

from pathlib import Path
from collections.abc import Mapping
import json

from docs_document_identity import is_immutable_doc_id
from docs_source_model import parse_source
from docs_workspace_config import DocsStageConfig, document_source_path, load_docs_stage, resolve_workspace_path


def publication_ignore_path(repo_root: Path) -> Path:
    """Resolve the exact Working policy file without creating or substituting it."""
    config = load_docs_stage(repo_root, "working")
    root = resolve_workspace_path(repo_root, document_source_path(config))
    path = root / "unpublishable.json"
    if path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError("Publication ignore file must stay in its configured source directory")
    return path


def read_publication_ignore_ids(repo_root: Path) -> frozenset[str]:
    """Read fresh exact IDs; missing, unreadable and invalid files fail visibly."""
    path = publication_ignore_path(repo_root)
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("unpublishable.json must contain a JSON array of document IDs") from error
    if not isinstance(values, list) or any(
        not isinstance(value, str) or value != value.strip() or not is_immutable_doc_id(value) for value in values
    ):
        raise ValueError("unpublishable.json must contain only immutable document ID strings")
    return frozenset(values)


def working_ignored_doc_ids(repo_root: Path, config: DocsStageConfig) -> frozenset[str]:
    """Load once per Working operation; callers apply membership only to ordinary documents."""
    if config.stage != "working":
        return frozenset()
    return read_publication_ignore_ids(repo_root)


class WorkingLinksExclusions:
    """Resolve ordinary ignore-list ancestry once per operation, without a scan.

    Callers may seed parents from documents they already loaded. Otherwise only
    exact ancestors are read. Draft state never participates in Working Links.
    """

    def __init__(self, source_root: Path, ignored_ids: frozenset[str], parents: Mapping[str, str] | None = None):
        self.source_root = source_root
        self.parents = dict(parents or {})
        self.excluded = dict.fromkeys(ignored_ids, True)

    def excludes(self, doc_id: str) -> bool:
        ancestors: set[str] = set()
        current = doc_id
        while current and current not in self.excluded:
            if not is_immutable_doc_id(current):
                raise ValueError("Working Links ancestry requires immutable document IDs")
            if current in ancestors:
                raise ValueError(f"Working Links ancestry contains a cycle at {current}")
            ancestors.add(current)
            if current not in self.parents:
                path = self.source_root / f"{current}.md"
                if self.source_root.is_symlink() or path.is_symlink() or path.resolve().parent != self.source_root.resolve():
                    raise ValueError("Working Links ancestor must stay in its configured source directory")
                if not path.is_file():
                    break
                metadata = parse_source(path)[0]
                if metadata.get("doc_id") != current:
                    raise ValueError("Working Links ancestor source identity does not match")
                self.parents[current] = str(metadata.get("parent_id") or "").strip()
            current = self.parents[current]
        excluded = self.excluded.get(current, False)
        self.excluded.update(dict.fromkeys(ancestors, excluded))
        return excluded
