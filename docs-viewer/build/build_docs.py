#!/usr/bin/env python3
"""Build Docs Viewer generated document payloads."""

from __future__ import annotations

from docs_builder.browser_config import (
    browser_docs_index_tree_url,
    browser_docs_recent_url,
    browser_scope_config_payload,
    browser_scope_record,
    browser_search_index_url,
    browser_search_policy_payload,
    docs_viewer_settings_payload,
    public_readonly_configs,
    raw_scope_items,
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
    DocsScopeConfig,
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
    SAFE_REF_KIND_PATTERN,
    SEMANTIC_REF_TOKEN_PATTERN,
    SITE_DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
    browser_path_for_repo_relative,
    html_attr,
    humanize,
    is_public_readonly_scope,
    json_text,
    load_docs_scope_configs,
    load_site_tools_config,
    monotonic_time,
    normalize_doc_ids,
    normalize_text,
    normalize_viewer_base_url,
    plain_text_from_html,
    read_json,
    read_text,
    render_markdown_to_html,
    resolve_scope_path,
    scope_uses_external_data,
    utc_timestamp,
    write_text,
)
from docs_builder.pipeline import DocsDataBuilder
from docs_builder.rendering import add_missing_image_titles
from docs_builder.semantic_references import SemanticRefToken
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
