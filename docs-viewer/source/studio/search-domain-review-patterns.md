---
doc_id: search-domain-review-patterns
title: Domain Review Patterns
added_date: 2026-06-02
last_updated: 2026-06-02
ui_status: review
parent_id: search
viewable: true
---
# Search Domain Review Patterns

## Purpose

Catalogue search and Docs Viewer search are separate domain search systems.
They should not share one product policy, one ranking model, or one build package.

They do, however, use equivalent static-search infrastructure.
Each domain has a config surface, generated index artifact, build pipeline, browser runtime, ranking logic, and validation path.
That means the same review questions apply to both domains, even when the answers and implementation details differ.

## Current Shared Pattern

The current shared pattern is architectural, not package-level.

Both domains:

- reduce source data into a flat JSON search artifact
- emit compact records rather than heavy source payloads
- derive `search_terms` and `search_text` at build time
- load generated JSON in the browser
- normalize the user query in the browser
- score, sort, and render matches in a domain-specific runtime
- use content-version hashing so unchanged generated artifacts can be skipped
- support targeted-update concepts only where the domain source model makes them safe

Current non-goals:

- no merged global search product
- no shared search backend service
- no shared ranking package
- no runtime parsing of raw source Markdown, HTML, workbook data, or catalogue source systems
- no forced generic schema beyond the practical `header` plus `entries` artifact shape

Small low-level helper duplication is intentional.
Normalization, token building, JSON formatting, hashing, and diagnostics are simple enough to keep in each domain builder unless repeated changes prove otherwise.

## Review Questions

### Config

Ask for each domain:

- Does config express the domain's real source ownership?
- Are source dependencies and output paths explicit enough to audit?
- Are visibility, scope, or eligibility rules represented in the right domain config?
- Does config declare invalidation boundaries without becoming a record-generation DSL?
- Are domain-specific policies easy to find without suggesting one global search policy?

### Index Schema

Ask for each domain:

- Does the artifact contain the fields needed for lookup, ranking, display, and routing?
- Does it avoid derivable fields when the browser runtime can compute them reliably?
- Does it avoid body-heavy or prose-heavy fields unless there is a measured search need?
- Are derived fields such as `search_terms` and `search_text` understandable from the source fields?
- Is the top-level artifact shape stable enough for browser and smoke-test consumers?

### Ranking

Ask for each domain:

- Does ranking reflect the way users search this data domain?
- Are exact identifiers and exact titles weighted appropriately?
- Are relationships weighted appropriately for the domain?
- Are broad text matches intentionally weaker than high-confidence identity matches?
- Are tie-breakers deterministic and understandable?
- Is ranking logic close enough to the browser runtime that UI behavior can be tested realistically?

### Pipeline

Ask for each domain:

- Does the build pipeline read the canonical generated/source artifact for the domain?
- Is search downstream of the domain source of truth rather than becoming a source of truth itself?
- Does targeted update behavior match the domain mutation model?
- Are full-rebuild fallbacks clear when targeted updates are unsafe?
- Does the pipeline produce deterministic output and skip unchanged writes?
- Can local services and watcher flows call the domain owner without resolving unrelated toolchains?

### Runtime And UI

Ask for each domain:

- Does the runtime load the right artifact for the current scope or route?
- Does result rendering expose domain-useful metadata?
- Do result links open in the right product context?
- Is the UI policy located with the domain that owns the surface?
- Are loading, empty, error, and more-results states domain-appropriate?

### Validation

Ask for each domain:

- Are unsupported cross-domain flags rejected?
- Do tests cover command shape, build output, targeted behavior, and browser module loading?
- Is there a lightweight dry-run path?
- Are generated artifacts reviewable without requiring a live service?
- Are docs updated when config, ranking, schema, or pipeline behavior changes?

## How To Use This

Use this document as a review checklist, not as a mandate to unify implementation.

The useful conclusion may be different for each domain.
For example, catalogue search may need better relationship or status fields, while Docs Viewer search may need heading/body summaries.
Those are equivalent review questions with domain-specific answers.

Related implementation docs:

- [Catalogue Search Infrastructure](/docs/?scope=studio&doc=search-catalogue-infrastructure)
- [Docs Viewer Search Infrastructure](/docs/?scope=studio&doc=search-docs-viewer-infrastructure)
- [Search Overview](/docs/?scope=studio&doc=search-overview)
- [Search Build Pipeline](/docs/?scope=studio&doc=search-build-pipeline)
