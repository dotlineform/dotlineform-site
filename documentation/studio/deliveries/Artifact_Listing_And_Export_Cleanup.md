---
draft: false
doc_id: d-20261014-175258-91e620
title: Artifact Listing And Export Cleanup
added_date: "2026-10-14 17:52:58"
last_updated: "2026-10-14 17:52:58"
parent_id: d-20260428-000000-f5ff18
---
# Artifact Listing And Export Cleanup

Parent: [Planned Features](../Planned_Features.md). Durable owners: [Media And Asset Handling](../Media_And_Asset_Handling.md#link-resolution-and-delivery) and [Export](../Export.md). The user approved this bounded follow-up to [Docs Media Optimisation](Docs_Media_Optimisation.md) on 2026-10-14.

## Agreed Result

The browser presents an Export media-file count without a byte total. Export's server retains selected preparation, digest identity, persistence and final output verification while removing the unused total, per-media sizes and associated bookkeeping from preview, apply, provenance and destination summaries. Mermaid's server-owned filesystem discovery needs file identities only; remote Publish's selected-family listing retains size/ETag metadata for comparing and verifying transfers. Upload limits remain with intake.

## Completion Gates

- [x] Readiness: traced both Mermaid listing consumers, Publish's remote metadata listing and all production Export byte-count consumers; user approved filename-only discovery and byte-count removal.
- [x] Make artifact `list()` return identities through the shared filesystem traversal and Mermaid planning consume strings. Expose R2 metadata through `list_stats()` and migrate Publish's one metadata-list call without adding a second request or compatibility alias.
- [x] Remove Export's byte formatter, aggregate/per-media size bookkeeping and payload/provenance/summary size fields and sum checks. Retain media SHA-256 plan identity and final file-set/byte verification.
- [x] Focused Python lint/compilation, JavaScript lint and whitespace passed for changed source; verify the method/field call sites by scoped source inspection.
- [x] Complete the distinct code review and mandatory Redundancy And Defensive Behavior Review. Traced empty/prefix/exact-file discovery, symlink confinement, Mermaid mapping, remote comparison, Export manifest recognition/revisions and final byte verification. Removed redundant Mermaid output uniqueness validation and a compatibility default for its required replacement field; affected Mermaid lint/compilation passed again after that review refinement. Durable owners record retained safeguards and evidence limits.
- [x] Update durable owners and the implementation guardrail. The changed management JavaScript is local-only and outside the public projection inventory.
- [ ] User manual acceptance after restarting the local service and force-reloading Docs Viewer: Export confirmation's file count and ordinary creation/replacement, plus normal explicit Mermaid Build and Publish use when needed.

Selected evidence is `bin/lint-python` and Python compilation for `docs_artifact_locations.py`, `docs_mermaid_media.py`, `docs_public_media_reconciliation.py`, `docs_static_html_export.py` and `docs_static_html_export_media.py`; `bin/lint-js` for `docs-viewer-static-html-export-workflow.js`; `git diff --check`; and scoped source/diff review. These checks cover source syntax/lint and inspected integration, without creating or updating tests. Existing artifact-list, Mermaid-plan and Export size assertions need separately agreed test migration under [Test Contract Discipline](../Test_Contract_Discipline.md). No tests, browser actions, real rendering, Build, Export, Publish, service restart, canonical data writes or public projection ran.
