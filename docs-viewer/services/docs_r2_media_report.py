"""Explicit, read-only remote inventory with one saved Manage report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from io import BytesIO
import json
from os.path import commonpath
from pathlib import Path
import re
import subprocess
import tarfile
from urllib.parse import unquote
from urllib.request import Request, urlopen

from docs_artifact_locations import R2_PROVIDER, ArtifactLocation, authenticated_remote_client_for_locations
from docs_document_identity import is_immutable_doc_id
from docs_document_images import document_thumbnail_filename, has_document_thumbnail
from docs_image_tokens import parse_image_token
from docs_publication_queue import read_queue
from docs_source_token_scan import token_opening_is_escaped
from docs_source_inspection import inspection_source_paths, read_inspection_source
from docs_source_media_adoption import SOURCE_REFERENCE, active_reference_ranges
from docs_source_model import write_text_atomic
from docs_workspace_config import (
    DocsStageConfig, load_docs_workspace_config, public_document_reader_paths,
    public_documents_path, select_workspace_stage,
)

SCHEMA = "docs_r2_media_report_v1"
THUMB_SUFFIX = "-thumb.webp"
GITHUB_ORIGIN = re.compile(r"(?:https://github\.com/|git@github\.com:)([\w.-]+/[\w.-]+?)(?:\.git)?")
SHA = re.compile(r"[a-f0-9]{40}")


@dataclass(frozen=True)
class MediaFamily:
    collection: str
    title: str
    kind: str
    location: ArtifactLocation
    prefixes: tuple[str, ...]

    def key(self, identity: str) -> str:
        return f"{self.location.path.as_posix()}/{identity}"


def _families(preview: DocsStageConfig) -> list[MediaFamily]:
    families = []
    for owner in (preview, *preview.media_collections):
        collection = getattr(owner, "collection", "")
        for kind, public in owner.public_projection.media.items():
            if public.location.provider != R2_PROVIDER:
                continue
            media = owner.media.types[kind]
            logical_root = f"collections/{collection}" if collection else "workspace"
            families.append(MediaFamily(
                collection, owner.title if collection else "Ordinary docs", kind, public.location,
                (media.reference_prefix.as_posix(), media.served_path_prefix,
                 f"docs-media:{logical_root}/{kind}", public.served_path_prefix),
            ))
    return families


def _github_json(url: str) -> list[dict]:
    request = Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "Docs-Viewer"})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def deployed_commit(repo_root: Path) -> str:
    """Use the latest successful Pages deployment, which may precede HEAD."""
    try:
        remote = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], cwd=repo_root, text=True, timeout=10,
        ).strip()
        match = GITHUB_ORIGIN.fullmatch(remote)
        if not match:
            raise ValueError("origin must be a GitHub repository")
        api = f"https://api.github.com/repos/{match[1]}/deployments"
        for item in _github_json(f"{api}?environment=github-pages&per_page=10"):
            deploy_id, sha = item["id"], item["sha"]
            if type(deploy_id) is not int or not SHA.fullmatch(sha):
                raise ValueError("invalid Pages deployment identity")
            statuses = _github_json(f"{api}/{deploy_id}/statuses?per_page=1")
            if statuses and statuses[0]["state"] == "success":
                return sha
        raise ValueError("no successful Pages deployment was returned")
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        raise ValueError(f"Deployed site could not be verified: {error}") from error


class ReferenceKeys:
    def __init__(self, families: list[MediaFamily]) -> None:
        self.protected: set[str] = set()
        self.thumbs = {family.collection: family for family in families if family.kind == "thumbs"}
        self.prefixes = {
            prefix.rstrip("/") + "/": family
            for family in families for prefix in family.prefixes
        }

    def add_path(self, path: str) -> None:
        if path.startswith("//"):
            path = "https:" + path
        for prefix, family in self.prefixes.items():
            if path.startswith(prefix):
                self.protected.add(family.key(path.removeprefix(prefix)))
                return

    def add_url(self, url: str) -> None:
        self.add_path(unquote(re.split(r"[?#]", url, maxsplit=1)[0]))

    def add_thumbnail(self, collection: str, doc_id: str) -> None:
        family = self.thumbs.get(collection)
        if family is not None:
            self.protected.add(family.key(document_thumbnail_filename(doc_id)))

    def scan_source(self, body: str) -> None:
        for start, end in active_reference_ranges(body):
            for match in SOURCE_REFERENCE.finditer(body, start, end):
                kind = match.lastgroup
                if kind != "url" and token_opening_is_escaped(body, match.start()):
                    continue
                if kind == "image":
                    image = parse_image_token(match[0])
                    if image is not None:
                        self.add_path(image.media_path)
                else:
                    value = match[kind].removeprefix("/") if kind == "token" else match[kind]
                    self.add_url(unescape(value))


class HtmlMediaReferences(HTMLParser):
    def __init__(self, keys: ReferenceKeys) -> None:
        super().__init__()
        self.keys = keys

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if value and name in {"src", "href", "poster", "data", "xlink:href"}:
                self.keys.add_url(value)
            elif value and name == "srcset":
                for url in re.split(r"[\s,]+", value):
                    self.keys.add_url(url)


def _public_payload(path: Path, raw: bytes, owners: dict[Path, str], keys: ReferenceKeys) -> None:
    if path.parent.name == "by-id":
        parser = HtmlMediaReferences(keys)
        parser.feed(json.loads(raw).get("content_html", ""))
        parser.close()
    else:
        collection = owners.get(path.parent, "")

        def visit(value):
            if isinstance(value, dict):
                if value.get("has_thumbnail") and isinstance(value.get("doc_id"), str):
                    keys.add_thumbnail(value.get("collection", collection), value["doc_id"])
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(json.loads(raw))


def _is_public_payload(path: Path) -> bool:
    return path.suffix == ".json" and (
        path.parent.name == "by-id" or path.name in {"manifest.json", "index-tree.json", "recent.json", "selected.json"}
    )


def _protect_public_references(
    repo_root: Path, root: Path, owners: dict[Path, str], commit: str, keys: ReferenceKeys,
) -> None:
    # Prepared output may already differ from the currently deployed commit.
    for path in (repo_root / root).rglob("*.json"):
        if _is_public_payload(path):
            _public_payload(path.relative_to(repo_root), path.read_bytes(), owners, keys)
    try:
        archive = subprocess.check_output(
            ["git", "archive", "--format=tar.gz", commit, "--", root.as_posix()],
            cwd=repo_root, stderr=subprocess.PIPE, timeout=30,
        )
    except subprocess.SubprocessError as error:
        raise ValueError(f"Could not read the deployed Pages snapshot {commit[:12]} from local Git.") from error
    with tarfile.open(fileobj=BytesIO(archive), mode="r:gz") as snapshot:
        for member in snapshot:
            path = Path(member.name)
            if member.isfile() and _is_public_payload(path):
                with snapshot.extractfile(member) as artifact:
                    _public_payload(path, artifact.read(), owners, keys)


def _document_id(family: MediaFamily, identity: str) -> str:
    if family.kind == "thumbs":
        doc_id = identity.removesuffix(THUMB_SUFFIX) if identity.endswith(THUMB_SUFFIX) else ""
    else:
        doc_id, separator, _ = identity.partition("/")
        if not separator:
            return ""
    return doc_id if is_immutable_doc_id(doc_id) else ""


def build_report(repo_root: Path, workspace) -> dict:
    working = select_workspace_stage(workspace, "working")
    families = _families(select_workspace_stage(workspace, "preview"))
    keys = ReferenceKeys(families)
    commit = deployed_commit(repo_root)
    public_root = public_documents_path(workspace)
    if public_root is None or not (repo_root / public_root).is_dir():
        raise ValueError("The prepared public Docs snapshot is unavailable.")
    public_owners = {path: collection for collection, path in public_document_reader_paths(workspace).items()}
    _protect_public_references(repo_root, public_root, public_owners, commit, keys)

    titles = {}
    working_owners = {"": working, **{owner.collection: owner for owner in working.collections}}
    for collection, owner in working_owners.items():
        root, paths = inspection_source_paths(repo_root, owner)
        for path in paths:
            document = read_inspection_source(root, path, collection=collection)
            titles[collection, document.doc_id] = document.title
            keys.scan_source(document.body)

    queue = read_queue(workspace)
    lookup = {(family.collection, family.kind): family for family in families}
    for group in ("current_documents", "deleted_documents"):
        for selection in queue[group].values():
            for kind, identities in selection.get("removed_media", {}).items():
                family = lookup.get((selection.get("collection", ""), kind))
                if family:
                    keys.protected.update(family.key(identity) for identity in identities)

    locations = [family.location for family in families]
    client = authenticated_remote_client_for_locations(repo_root, locations)
    prefix = commonpath([location.path.as_posix() for location in locations])
    if client is None or prefix in {"", "."}:
        raise ValueError("R2 Docs media requires a configured shared prefix.")
    scanned = 0
    findings = []
    collections = {family.collection: family.title for family in families}
    bindings = {family.location.path.as_posix(): family for family in families}
    for item in client.list_objects(prefix + "/"):
        # Body media paths may have nested folders. Resolve the configured family
        # before deciding whether the remainder belongs to a document.
        for boundary, family in bindings.items():
            if item.key.startswith(boundary + "/"):
                identity = item.key.removeprefix(boundary + "/")
                break
        else:
            continue
        doc_id = _document_id(family, identity)
        if not doc_id:
            continue
        scanned += 1
        if item.key in keys.protected:
            continue
        owner_title = titles.get((family.collection, doc_id))
        if family.kind == "thumbs" and owner_title is not None and has_document_thumbnail(working_owners[family.collection], doc_id):
            continue
        findings.append({
            "collection": family.collection, "doc_id": doc_id, "owner_title": owner_title, "key": item.key,
        })
    return {
        "schema_version": SCHEMA, "refreshed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "deployed_commit": commit, "scanned": scanned,
        "collections": collections,
        "findings": sorted(findings, key=lambda row: (collections[row["collection"]].casefold(), row["key"])),
    }


def read_report(repo_root: Path) -> dict:
    path = load_docs_workspace_config(repo_root).r2_media_report.path
    try:
        report = json.loads(path.read_bytes())
    except FileNotFoundError:
        report = None
    except (OSError, ValueError) as error:
        raise ValueError("Saved R2 media report could not be read. Use Refresh to replace it.") from error
    if report is not None and (not isinstance(report, dict) or report.get("schema_version") != SCHEMA):
        raise ValueError("Saved R2 media report is unreadable. Use Refresh to replace it.")
    return {"ok": True, "report": report}


def refresh_report(repo_root: Path) -> dict:
    workspace = load_docs_workspace_config(repo_root)
    report = build_report(repo_root, workspace)
    try:
        write_text_atomic(workspace.r2_media_report.path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    except OSError as error:
        raise RuntimeError("The completed R2 media report could not be saved.") from error
    return {"ok": True, "report": report}
