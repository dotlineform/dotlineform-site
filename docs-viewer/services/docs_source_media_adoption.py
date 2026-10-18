"""Prepare exact foreign document-media copies and their Source path rewrites."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
import re
from urllib.parse import quote, unquote

from docs_artifact_locations import ArtifactLocationAdapter, artifact_location_adapter
from docs_document_identity import is_immutable_doc_id
from docs_image_tokens import encode_image_path, parse_image_token
from docs_management_document_target import ManagedDocumentTarget
from docs_semantic_source import semantic_source_ranges, token_opening_is_escaped
from docs_source_media_service import PreparedSourceMediaWrite, prepare_source_media_write
from docs_workspace_config import DocsCollectionConfig, DocsStageConfig, managed_media_config


SOURCE_REFERENCE = re.compile(
    r"\[\[image:(?P<image>[^|\]\s]+)\|[^\]\r\n]*\]\]"
    r"|\[\[(?:media|html-media):(?P<token>[^\]\s]+)[^\]]*\]\]"
    r"|(?:\]\(\s*<?|(?<![\w:-])(?i:src|href)\s*=\s*[\"']?|^ {0,3}\[[^\]\n]+\]:\s*<?)"
    r"(?P<url>[^\s)\[\]\"'<>?#]+)",
    re.MULTILINE,
)


def active_reference_ranges(body: str) -> Iterator[tuple[int, int]]:
    """Keep adjacent active lines together for wrapped Markdown destinations."""
    previous = None
    for start, end in semantic_source_ranges(body, parse_token=parse_image_token):
        if previous is not None and previous[1] == start:
            previous = previous[0], end
        else:
            if previous is not None:
                yield previous
            previous = start, end
    if previous is not None:
        yield previous


def prepare_source_media_adoption(
    repo_root: Path, resolved: ManagedDocumentTarget, body: str, pending_writes: list[PreparedSourceMediaWrite],
) -> tuple[str, list[PreparedSourceMediaWrite]]:
    """Read only distinct selected foreign files; preserve completed managed bytes.

    Source documents and directories are not discovered. A deleted source document
    is immaterial while its exact configured media file still exists.
    """
    if resolved.document_config.media is None:
        return body, []
    owners = (resolved.parent_config, *resolved.parent_config.media_collections)
    prefixes = [
        (prefix + "/", owner, media_type, representation)
        for owner in owners
        for media_type, media in owner.media.types.items() if media_type != "thumbs"
        for prefix, representation in (
            (media.reference_prefix.as_posix(), "logical"), (media.served_path_prefix.rstrip("/"), "served"),
        )
    ]
    adapters = {(resolved.collection, item.media_type): item.adapter for item in pending_writes}
    prepared = {(item.media_type, item.identity): item for item in pending_writes}
    adopted: dict[tuple[str, str, str], str] = {}
    writes = []
    edits = []

    def adapter_for(owner: DocsStageConfig | DocsCollectionConfig, collection: str, media_type: str) -> ArtifactLocationAdapter:
        key = collection, media_type
        if key not in adapters:
            adapters[key] = artifact_location_adapter(repo_root, managed_media_config(owner, media_type).asset_location)
        return adapters[key]

    for start, end in active_reference_ranges(body):
        for match in SOURCE_REFERENCE.finditer(body, start, end):
            kind = match.lastgroup
            raw_path = match.group(kind)
            if kind != "url" and token_opening_is_escaped(body, match.start()):
                continue
            if kind == "url" and not any(raw_path.startswith(prefix) for prefix, *_rest in prefixes):
                continue
            if kind == "image":
                image = parse_image_token(match.group(0))
                if image is None:
                    continue
                path = image.media_path
            else:
                path = unquote(raw_path, errors="strict") if kind == "url" else raw_path.lstrip("/")
            for prefix, owner, media_type, representation in prefixes:
                if not path.startswith(prefix):
                    continue
                identity = path.removeprefix(prefix)
                source_doc_id, separator, relative_path = identity.partition("/")
                collection = getattr(owner, "collection", "")
                if (not separator or not is_immutable_doc_id(source_doc_id)
                        or (collection == resolved.collection and source_doc_id == resolved.doc_id)):
                    break
                source_key = collection, media_type, identity
                destination_media = managed_media_config(resolved.document_config, media_type)
                if source_key not in adopted:
                    destination = f"{resolved.doc_id}/{relative_path}"
                    try:
                        data = adapter_for(owner, collection, media_type).read(identity)
                        key = media_type, destination
                        existing = prepared.get(key)
                        if existing is not None:
                            if existing.data != data:
                                raise FileExistsError(f"Competing media at {media_type}/{destination}; choose another filename")
                        else:
                            item = prepare_source_media_write(
                                adapter_for(resolved.document_config, resolved.collection, media_type),
                                media_type, destination, data, replace=False,
                            )
                            prepared[key] = item
                            writes.append(item)
                    except (ValueError, OSError, RuntimeError) as error:
                        raise ValueError(f"Source {resolved.doc_id}: media adoption for {path} failed: {error}") from error
                    adopted[source_key] = destination
                destination_prefix = (destination_media.reference_prefix.as_posix() if representation == "logical"
                                      else destination_media.served_path_prefix.rstrip("/"))
                replacement = f"{destination_prefix}/{adopted[source_key]}"
                if kind == "image":
                    replacement = encode_image_path(replacement)
                elif kind == "url":
                    replacement = quote(replacement, safe="/-._~")
                edits.append((match.start(kind), match.end(kind), replacement))
                break

    parts = []
    offset = 0
    for start, end, replacement in edits:
        parts.extend((body[offset:start], replacement))
        offset = end
    return "".join(parts) + body[offset:], writes
