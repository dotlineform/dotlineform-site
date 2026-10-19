"""Operation-local rendering dependencies shared by document collection builders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .common import load_site_tools_config
from .inline_icons import InlineIconRenderer
from .semantic_token_registry import SemanticTokenRegistry, load_semantic_token_registry


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
