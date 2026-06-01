# Fixtures

Put stable test fixtures here only when a check cannot safely use existing repo data.

Avoid copying large generated artifacts into fixtures. Prefer tiny JSON, Markdown, or text samples that explain the behavior under test.

- `docs_viewer_v2_custom_tokens.json`: Docs Viewer v2 custom-token contract fixtures for media, interactive HTML, semantic references, invalid references, code-skip behavior, generated reference payloads, and generated search text.
- `generated_output_contracts.json`: Rubyless app-runtime generated-output contract fixtures for Docs Viewer docs payloads, semantic reference payloads, docs search payloads, catalogue search payloads, and catalogue prose `content_html` without locking in Jekyll/Kramdown markup.
