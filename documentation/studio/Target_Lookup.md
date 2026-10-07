---
draft: false
doc_id: d-20260726-185814-c5e581
title: Target Lookup
added_date: "2026-07-26 18:58:14"
last_updated: "2026-10-07 16:05:28"
parent_id: d-20260725-153656-516b61
---
# Target Lookup

Catalogue authoring and the Works Subject picker obtain current target choices through `/docs/catalogue-media-targets`. The owning service reads configured Working Catalogue Work and Gallery indexes and returns exact identities, titles and compact metadata. It does not read canonical Catalogue records or a persisted discovery lookup.

The response retains `docs_semantic_token_target_lookup_v2`, with a `targets` array. Shared browser normalization and matching consume this active response contract. The token registry declares supported identities and parser/UI policy; it contains no target-store URL or generator adapter declarations.

Catalogue images and Media View resolve exact generated records through the configured Catalogue provider. Document Build reads `works/index/<work_id>.json` for Work image text and metadata. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) owns those boundaries.

The former `docs-viewer/data/generated/semantic-tokens/target-lookup.json`, its standalone builder/CLI and browser file loader are retired. No refresh command, static serving prefix or compatibility read remains for that file. Save, Refresh Catalogue, Build and Publish keep their existing completion boundaries.

## Approved Test Retirement

The bounded retirement removes `docs-viewer/tests/python/test_semantic_target_lookup.py`: canonical Work/Series identity and image projection, CLI output writing, and retention of text targets when images are unavailable. Those three checks exercised the removed generator using temporary canonical records, registry/media configuration, generated JSON, and captured CLI output; they used no live service or network. They provide no retained coverage.

In `docs-viewer/tests/python/test_build_docs_cli.py::test_python_docs_builder_scripts_load_repo_local_env_before_scope_config`, only the retired lookup CLI is removed from the subprocess help inventory. Remaining commands and assertions are unchanged; that selection is not certified or run by this retirement.

Lookup-file setup and obsolete registry lookup declarations are removed from `docs-viewer/tests/python/build_docs_test_support.py::write_semantic_token_contract`, `docs-viewer/tests/python/test_docs_broken_links.py::write_semantic_token_contract`, and `docs-viewer/tests/python/test_build_docs_public_payloads.py::test_python_docs_builder_public_generated_payloads_include_manage_rows`. Those temporary fixture writes no longer create unused discovery JSON. Existing assertions, real components, other fixtures, network behavior and collection membership remain unchanged.

The agreed obsolete test setup is removed. No replacement tests, expanded assertions, profile changes, or test runs are included in this approved cleanup. Focused lint, syntax, registry diagnostics, reference and diff review provide the selected evidence at low local cost, without workspace/service writes or network calls. Retained scope-bearing tests remain unreviewed against the current workspace; this cleanup does not establish their coverage. Studio's existing write-route test retains a historical negative response-key assertion for `semantic_target_lookup`; it is not a lookup reader and was outside the approved test changes.
