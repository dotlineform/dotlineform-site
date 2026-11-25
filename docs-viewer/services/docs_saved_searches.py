"""Manage the selected saved result file under the configured Working source root."""

from __future__ import annotations

import json
from pathlib import Path

from docs_document_identity import is_document_id
from docs_source_model import write_text_atomic_new
from docs_workspace_config import DocsStageConfig, source_control_path


def _valid_name(name: object) -> bool:
    if (not isinstance(name, str) or not name or name != name.strip()
            or name.startswith(".") or any(char in "/\\" or ord(char) < 32 for char in name)):
        return False
    try:
        return len(name.encode("utf-8")) <= 200
    except UnicodeEncodeError:
        return False


def _saved_search_path(config: DocsStageConfig, name: object) -> Path:
    if not _valid_name(name):
        raise ValueError("Enter a saved list name without path separators or control characters.")
    return source_control_path(config, f"saved-searches/{name}.json")


def _validate_rows(config: DocsStageConfig, name: str, rows: object) -> list[dict[str, str]]:
    if not isinstance(rows, list):
        raise ValueError(f"{name}.json must contain an array of documents.")
    collections = {owner.collection for owner in config.collections}
    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(rows, start=1):
        label = f"{name}.json, row {index}"
        if not isinstance(row, dict) or row.keys() - {"collection"} != {"doc_id", "title"}:
            raise ValueError(f"{label} must contain doc_id and title, with collection for a collection document.")
        collection = row.get("collection", "")
        if "collection" in row and (not isinstance(collection, str) or collection not in collections):
            raise ValueError(f"{label} names an unknown collection.")
        if not isinstance(row["doc_id"], str) or not is_document_id(row["doc_id"], collection=collection):
            raise ValueError(f"{label} has an invalid doc_id.")
        if not isinstance(row["title"], str) or not row["title"].strip():
            raise ValueError(f"{label} needs a display title.")
        target = (collection, row["doc_id"])
        if target in seen:
            raise ValueError(f"{label} repeats document {row['doc_id']}.")
        seen.add(target)
    return rows


def list_saved_searches(config: DocsStageConfig) -> dict[str, object]:
    directory = source_control_path(config, "saved-searches")
    try:
        names = sorted((entry.stem for entry in directory.iterdir()
                        if entry.suffix == ".json" and _valid_name(entry.stem)
                        and not entry.is_symlink() and entry.is_file()), key=str.casefold)
    except FileNotFoundError:
        names = []
    except OSError as error:
        raise RuntimeError("Could not list the saved results.") from error
    return {"names": names}


def read_saved_search(config: DocsStageConfig, name: str) -> dict[str, object]:
    path = _saved_search_path(config, name)
    if not path.is_file():
        raise FileNotFoundError(f"Saved list {path.name} was not found.")
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{path.name} must contain valid UTF-8 JSON.") from error
    except OSError as error:
        raise RuntimeError(f"Could not read {path.name}.") from error
    return {"name": name, "docs": _validate_rows(config, name, rows)}


def create_saved_search(config: DocsStageConfig, body: dict[str, object]) -> dict[str, object]:
    if body.keys() != {"name", "docs"}:
        raise ValueError("Save as new requires a name and documents.")
    path = _saved_search_path(config, body["name"])
    name = path.stem
    rows = _validate_rows(config, name, body["docs"])
    try:
        write_text_atomic_new(path, json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    except FileExistsError as error:
        raise ValueError(f"{path.name} already exists. Choose a new name.") from error
    except (OSError, UnicodeError) as error:
        raise RuntimeError(f"Could not save {path.name}.") from error
    return {"name": name}


def delete_saved_search(config: DocsStageConfig, body: dict[str, object]) -> dict[str, object]:
    if body.keys() != {"name"}:
        raise ValueError("Delete saved list requires a name.")
    path = _saved_search_path(config, body["name"])
    if not path.is_file():
        raise FileNotFoundError(f"Saved list {path.name} was not found.")
    try:
        path.unlink()
    except OSError as error:
        raise RuntimeError(f"Could not delete {path.name}.") from error
    return {"name": path.stem}
