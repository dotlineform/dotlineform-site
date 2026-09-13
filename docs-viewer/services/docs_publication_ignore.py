"""Read the one configured Analysis Working ordinary-document exclusion list."""

from pathlib import Path
import json

from docs_document_identity import is_immutable_doc_id
from docs_scope_config import DocsScopeConfig, document_source_path, load_docs_scope_stage, resolve_scope_path


def publication_ignore_path(repo_root: Path) -> Path:
    """Resolve the exact Working policy file without creating or substituting it."""
    config = load_docs_scope_stage(repo_root, "analysis", "working")
    root = resolve_scope_path(repo_root, document_source_path(config))
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


def working_ignored_doc_ids(repo_root: Path, config: DocsScopeConfig) -> frozenset[str]:
    """Load once per Working operation; callers apply membership only to ordinary documents."""
    if config.scope_id != "analysis" or config.stage != "working":
        return frozenset()
    return read_publication_ignore_ids(repo_root)
