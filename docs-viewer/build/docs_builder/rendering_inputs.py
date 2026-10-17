"""Operation-local rendering dependencies shared by document collection builders."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .common import load_site_tools_config
from .inline_icons import InlineIconRenderer
from .semantic_token_registry import SemanticTokenRegistry, load_semantic_token_registry
from docs_workspace_config import location_child


@dataclass(frozen=True)
class RenderingInputs:
    """Keep configuration and icon reads within one synchronous build operation."""

    site_config: dict[str, Any]
    semantic_token_registry: SemanticTokenRegistry | None
    inline_icons: InlineIconRenderer

    @classmethod
    def load(cls, repo_root: Path) -> RenderingInputs:
        """Read rendering configuration once; icon artwork is loaded on demand."""
        return cls(
            load_site_tools_config(repo_root), load_semantic_token_registry(repo_root),
            InlineIconRenderer(repo_root),
        )


def prepare_catalogue_works(builder: Any, documents: list[Any], records: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Load only the exact Work records required by the selected rendering."""
    from .semantic_tokens import parse_semantic_tokens

    for document in documents:
        for token in parse_semantic_tokens(document.body_markdown, registry=builder.semantic_token_registry):
            if not token.supported or token.family != "catalogue" or token.presentation not in {"image", "entry"}:
                continue
            if token.presentation == "entry" and (getattr(builder, "collection_id", "") != "catalogue" or token.target_id != document.doc_id):
                continue
            if token.target_id in records:
                continue
            root = builder.workspace.catalogue.stage_location(builder.config.stage)
            path = location_child(root, Path("works/index") / f"{token.target_id}.json").path
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                raise ValueError(f"Catalogue Work {token.target_id} generated JSON is unavailable or invalid") from error
            records[token.target_id] = payload["work"]
    return records
