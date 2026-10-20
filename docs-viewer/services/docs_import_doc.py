"""Browser-native single-document upload and its ordinary import handoff."""

from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
import json
from pathlib import Path
import tempfile
from typing import Any

from docs_import_common import DOCUMENT_STAGED_SUFFIXES, is_interactive_html_import_asset
from docs_import_review_source_folder import is_review_source_markdown
from docs_import_source_service import import_ordinary_source
from docs_management_import_service import import_source_dependencies, resolve_import_collection
from docs_source_media_upload import MAX_MEDIA_BYTES, MAX_METADATA_BYTES, MAX_MULTIPART_OVERHEAD_BYTES, MAX_REQUEST_BYTES, validate_upload_filename


@dataclass(frozen=True)
class ImportDocUpload:
    """One bounded native filename and its request-owned bytes."""

    filename: str
    data: bytes


def parse_import_doc(content_type: str, raw: bytes) -> tuple[dict[str, Any], ImportDocUpload]:
    """Parse exactly metadata plus one opaque document, using native upload limits."""
    if len(raw) > MAX_REQUEST_BYTES:
        raise ValueError("Import doc exceeds the 66 MiB request limit")
    if len(content_type) > 256 or "\r" in content_type or "\n" in content_type:
        raise ValueError("Invalid Import doc Content-Type")
    try:
        header = ("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode("ascii")
    except UnicodeError as error:
        raise ValueError("Invalid Import doc Content-Type") from error
    message = BytesParser(policy=policy.default).parsebytes(header + raw)
    if message.get_content_type() != "multipart/form-data" or not message.is_multipart() or message.defects:
        raise ValueError("Import doc requires valid multipart/form-data")
    fields = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if (part.get_content_disposition() != "form-data" or part.is_multipart() or part.defects
                or not isinstance(name, str) or name in fields):
            raise ValueError("Invalid or duplicate Import doc field")
        fields[name] = part
    if set(fields) != {"metadata", "document"} or fields["metadata"].get_filename() is not None:
        raise ValueError("Import doc requires metadata JSON and one document")
    metadata = fields["metadata"].get_payload(decode=True)
    if not isinstance(metadata, bytes) or len(metadata) > MAX_METADATA_BYTES:
        raise ValueError("Import doc metadata exceeds the 1 MiB limit")
    try:
        body = json.loads(metadata.decode("utf-8"))
    except (ValueError, UnicodeError) as error:
        raise ValueError("Import doc metadata must be valid UTF-8 JSON") from error
    if not isinstance(body, dict) or set(body) - {"include_prompt_meta"} != {"filename", "collection"}:
        raise ValueError("Import doc requires filename and collection, with optional include_prompt_meta")
    filename = body.pop("filename")
    if not isinstance(filename, str):
        raise ValueError("Import doc filename must be a string")
    validate_upload_filename(filename)
    if Path(filename).suffix.lower() not in DOCUMENT_STAGED_SUFFIXES:
        raise ValueError("Import doc accepts Word, HTML, Markdown or text files")
    if "include_prompt_meta" in body and type(body["include_prompt_meta"]) is not bool:
        raise ValueError("include_prompt_meta must be a boolean")
    data = fields["document"].get_payload(decode=True)
    if not isinstance(data, bytes) or not data or len(data) > MAX_MEDIA_BYTES:
        raise ValueError("Import doc requires one nonempty file of at most 64 MiB")
    if len(raw) - len(metadata) - len(data) > MAX_MULTIPART_OVERHEAD_BYTES:
        raise ValueError("Import doc multipart overhead exceeds the 1 MiB limit")
    return body, ImportDocUpload(filename, data)


def import_doc(repo_root: Path, body: dict[str, Any], upload: ImportDocUpload) -> dict[str, Any]:
    """Import one upload through the existing converters, media and write owners.

    The temporary file is request-local converter input and is removed after
    awaited document/media generation. No persistent staging, directory inventory
    or package/companion discovery participates in native document intake.
    """
    destination = resolve_import_collection(repo_root, body)
    if destination.collection == "catalogue":
        raise ValueError("Catalogue documents are owned by Work Regenerate")
    with tempfile.TemporaryDirectory(prefix="docs-import-doc-") as directory:
        root = Path(directory).resolve()
        source_path = root / upload.filename
        source_path.write_bytes(upload.data)
        if is_review_source_markdown(source_path):
            raise ValueError("Use Import with the complete edited Docs Review source folder")
        if is_interactive_html_import_asset(source_path):
            raise ValueError("Use Import for interactive HTML companion assets")
        result = import_ordinary_source(
            repo_root, body, False, import_source_dependencies(), destination=destination,
            staging_root=root, source_root=root, source_path=source_path,
            source_directory="", include_companion_assets=False,
        )
        return {
            "ok": True, "target": result["target"], "record": result["record"],
            "warnings": result["import_preview"].get("warnings", []),
        }
