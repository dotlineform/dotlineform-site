# Fixtures

Put stable test fixtures here only when a check cannot safely use existing repo data.

Avoid copying large generated artifacts into fixtures. Prefer tiny JSON, Markdown, or text samples that explain the behavior under test.

- `docs_managed_document_targets_v1.json`: explicit parent/sub-scope managed-document targets and parent, valid-detail, invalid-detail, loading, failure, and server-rejection cases shared by the Sub-Scope Document Editing delivery. It freezes test inputs and expected boundaries without configuring runtime behavior.
- `generated_output_contracts.json`: app-runtime generated-output contract fixtures for Docs Viewer docs payloads, semantic reference payloads, docs search payloads, and catalogue search payloads.
- `semantic_tokens_catalogue_v1.json`: CT-P0 source grammar, caret boundaries, Catalogue definition, and minimal lookup, usage, and broken-link shapes shared by the later Python and browser implementations. It freezes a contract but is not runtime configuration.
