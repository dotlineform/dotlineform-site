#!/usr/bin/env python3
"""Focused endpoint paths for persistent read-only returned-package review."""

PACKAGES_PATH = "/docs-review/packages"
CAPABILITIES_PATH = "/docs-review/capabilities"
MANIFEST_PATH = "/docs-review/packages/manifest"
ASSETS_PATH = "/docs-review/packages/assets"
ASSET_CONTENT_PREFIX = "/docs-review/packages/assets-content/"
INDEX_TREE_PATH = "/docs-review/packages/index-tree"
PAYLOAD_PATH = "/docs-review/packages/payload"
BUILD_PATH = "/docs-review/packages/build"

GET_PATHS = (
    CAPABILITIES_PATH,
    PACKAGES_PATH,
    MANIFEST_PATH,
    ASSETS_PATH,
    INDEX_TREE_PATH,
    PAYLOAD_PATH,
)

POST_PATHS = (
    BUILD_PATH,
)

OPTIONS_PATHS = tuple(dict.fromkeys((*GET_PATHS, *POST_PATHS)))
