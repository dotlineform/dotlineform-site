# Fixtures

Put stable test fixtures here only when a check cannot safely use existing repo data.

Avoid copying large generated artifacts into fixtures. Prefer tiny JSON, Markdown, or text samples that explain the behavior under test.

- `docs_viewer_v2_custom_tokens.json`: Docs Viewer v2 custom-token contract fixtures for media, interactive HTML, invalid custom tokens, code-skip behavior, and generated search text.
- `generated_output_contracts.json`: app-runtime generated-output contract fixtures for Docs Viewer docs payloads, semantic reference payloads, docs search payloads, catalogue search payloads, and catalogue prose `content_html`.
- `semantic_tokens_catalogue_v1.json`: CT-P0 source grammar, caret boundaries, Catalogue definition, and minimal lookup, usage, and broken-link shapes shared by the later Python and browser implementations. It freezes a contract but is not runtime configuration.
