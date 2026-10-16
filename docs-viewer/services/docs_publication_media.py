"""Selected media identities and configured Catalogue destinations."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import unquote

from docs_artifact_locations import R2_PROVIDER, ArtifactLocation, normalize_artifact_identity
from docs_workspace_config import DocsStageConfig, DocsWorkspaceConfig, DocsPublicMediaConfig, public_media_bindings, safe_relative_path


HTML_START_TAG_PATTERN = re.compile(
    r"<(?P<body>[A-Za-z][A-Za-z0-9:-]*(?:[^>\"']|\"[^\"]*\"|'[^']*')*)>",
    re.DOTALL,
)
MEDIA_URL_ATTRIBUTE_PATTERN = re.compile(
    r"(?<![\w:-])(?:src|href|data-docs-viewer-diagram-(?:light|dark)-src)\s*=\s*"
    r"(?:(?P<quote>[\"'])(?P<quoted_value>.*?)(?P=quote)|(?P<unquoted_value>[^\s\"'=<>`]+))",
    re.IGNORECASE,
)


def _media_identity_from_url(value: str, prefix: str) -> str:
    candidate = html.unescape(str(value or "").strip())
    normalized_prefix = prefix.rstrip("/")
    if not candidate.startswith(f"{normalized_prefix}/"):
        return ""
    identity = candidate.removeprefix(f"{normalized_prefix}/")
    identity = unquote(re.split(r"[?#]", identity, maxsplit=1)[0])
    try:
        return normalize_artifact_identity(identity)
    except ValueError:
        return ""


def publication_media_bindings(
    repo_root: Path, config: DocsStageConfig, *, workspace: DocsWorkspaceConfig,
) -> dict[str, tuple[ArtifactLocation, DocsPublicMediaConfig]]:
    """Pair each shared family with its unchanged configured public destination."""
    bindings = {
        key: (collection.media.types[public.media_type].asset_location, public)
        for key, (collection, public) in public_media_bindings(config).items()
    }
    assets = workspace.assets.for_stage("preview")
    settings = json.loads((repo_root / "site-tools/config/site-tools.json").read_bytes())["media"]
    # Catalogue families must not collide with <collection>/<media_type> bindings.
    for key, source, prefix_key in (
        ("catalogue/works/primary", assets.work_primary, "image_works"),
        ("catalogue/works/files", assets.work_files, "files_works"),
    ):
        prefix = safe_relative_path(settings[prefix_key].strip("/"), field=f"media.{prefix_key}")
        if prefix.parts[0] == "archive":
            raise ValueError("Catalogue publication cannot write the archive")
        bindings[key] = (source, DocsPublicMediaConfig(
            key, prefix, ArtifactLocation(R2_PROVIDER, prefix),
            settings["base"].rstrip("/") + "/" + prefix.as_posix(),
        ))
    destination = workspace.catalogue.public_projection.location
    bindings["catalogue/works/thumbs"] = (assets.work_thumbnails, DocsPublicMediaConfig(
        "catalogue/works/thumbs", Path("works/thumbs"),
        ArtifactLocation(destination.provider, destination.path / "works/thumbs"),
        "/" + (destination.path / "works/thumbs").relative_to("site").as_posix(),
    ))
    return bindings



