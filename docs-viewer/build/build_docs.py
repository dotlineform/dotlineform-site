#!/usr/bin/env python3
"""Build Docs Viewer generated document payloads."""

from __future__ import annotations

import sys

from docs_builder.runtime_bootstrap import apply_repo_local_env, workspace_overrides_from_argv

if __name__ == "__main__":
    apply_repo_local_env(**workspace_overrides_from_argv(sys.argv[1:]))

from docs_builder.browser_config import (
    browser_docs_index_tree_url,
    browser_docs_recent_url,
    browser_workspace_config_payload,
    browser_stage_record,
    browser_search_index_url,
    browser_search_policy_payload,
    write_browser_config,
)
from docs_builder.cli import main, parse_args
from docs_builder.common import (
    CONFIG_REL_PATH,
    DEFAULT_RECENT_LIMIT,
    DOCS_INDEX_TREE_SCHEMA_VERSION,
    DOCS_RECENT_SCHEMA_VERSION,
    DOCS_VIEWER_BROWSER_CONFIG_PATH,
    DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION,
    DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
    DocsStageConfig,
    FRONT_MATTER_PATTERN,
    HTML_MEDIA_HEIGHT_PATTERN,
    HTML_MEDIA_TOKEN_PATTERN,
    HTML_ATTR_PATTERN_TEMPLATE,
    IMG_PATTERN,
    INTEGER_PATTERN,
    MEDIA_IMAGE_TOKEN_PATTERN,
    MEDIA_TOKEN_PATTERN,
    MEDIA_TOKEN_ALLOWED_ATTRS,
    MEDIA_TOKEN_DIMENSION_PATTERN,
    SITE_DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
    browser_path_for_repo_relative,
    html_attr,
    humanize,
    json_text,
    load_docs_workspace_config,
    load_site_tools_config,
    monotonic_time,
    normalize_doc_ids,
    normalize_text,
    plain_text_from_html,
    read_json,
    read_text,
    render_markdown_to_html,
    resolve_workspace_path,
    utc_timestamp,
    write_text,
)
from docs_builder.pipeline import DocsDataBuilder
from docs_builder.rendering import add_missing_image_titles
from docs_builder.source import (
    DocRecord,
    FrontMatterSyntaxError,
    extract_title,
    front_matter_boolean,
    parse_front_matter_value,
    parse_source,
)


if __name__ == "__main__":
    raise SystemExit(main())
