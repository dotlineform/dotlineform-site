---
doc_id: ui-request-docs-html-import-task
title: "Docs HTML Import Task"
last_updated: 2026-04-23
parent_id: ui-requests
sort_order: 40
---

# Docs HTML Import Task

Status:

- implementation in progress
- parser/sanitizer dependencies pinned in `requirements.txt`
- initial dry-run importer scaffold landed in `scripts/docs/docs_html_import.py`
- depends on [Docs HTML Import Spec](/docs/?scope=studio&doc=ui-request-docs-html-import-spec)

## Goal

Implement a local-only HTML import flow that converts a staged external `.html` file into a best-attempt Docs Viewer Markdown source doc for either:

- `studio`
- `library`

This task covers:

- staged source selection
- HTML parsing and sanitization
- rule-driven Markdown conversion
- explicit create/overwrite behavior
- same-scope docs/docs-search rebuild follow-through

This task does not change the broader docs authoring or publishing model.

## Current Progress

Completed now:

- staged fixture directory established at `var/docs/import-staging/`
- four reviewed HTML examples copied into local staging as fixtures
- parser/sanitizer stack pinned in `requirements.txt`
- local project Python has the pinned parser/sanitizer stack installed
- dry-run importer scaffold added at `scripts/docs/docs_html_import.py`
- scaffold now parses through the fixed `beautifulsoup4` + `lxml` stack rather than the stdlib HTML parser
- dry-run `POST /docs/import-html` endpoint added to the Docs Management Server
- staged import preview now reports conversion summary plus `doc_id` collision detection

Not done yet:

- Jekyll render validation in the import path
- Studio import page
- create/overwrite write flow

## Implementation Boundary

The implementation should stay inside the current local docs-management and Studio workflow.

Primary ownership:

- Studio page and client controller
- docs-management server endpoint and write flow
- shared conversion module under `scripts/docs/`

Locked implementation direction:

- keep orchestration and policy logic in Python
- use external libraries for HTML parsing and sanitization
- parse the full source document into a DOM-like in-memory tree
- keep conversion decisions project-owned rather than delegating them to a generic HTML-to-Markdown library
- treat successful rendering through the repo's Jekyll docs pipeline as the canonical Markdown validation step

Pinned v1 parser/sanitizer stack:

- `beautifulsoup4`
- `lxml`
- `bleach`

## Files Likely To Change

Expected implementation files:

- `requirements.txt`
- `scripts/docs/docs_management_server.py`
- new conversion helper(s) under `scripts/docs/`
- new Studio route under `studio/`
- new Studio JS controller under `assets/studio/js/`
- `assets/studio/data/studio_config.json`
- Studio CSS only if the new page needs shared styling

Likely docs follow-through after implementation:

- [Docs HTML Import Spec](/docs/?scope=studio&doc=ui-request-docs-html-import-spec)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Studio](/docs/?scope=studio&doc=studio)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Site Change Log](/docs/?scope=studio&doc=site-change-log)

## Task List

### 1. Pin And Install Parser Dependencies

Add the agreed parser/sanitizer libraries to `requirements.txt` and install them into the configured project Python before extending the importer further.

Required outcome:

- `requirements.txt` pins:
  - `beautifulsoup4`
  - `lxml`
  - `bleach`
- local setup/install instructions are sufficient for the project Python environment to use that exact stack
- subsequent importer work builds against the fixed parser stack rather than the temporary stdlib parser scaffold

Reason:

- the current dry-run importer scaffold is useful for rule exploration, but it should not become the long-term parser boundary

### 2. Create Fixture Coverage

Add and organize local implementation fixtures for the reviewed sample HTML files.

Required outcome:

- keep a stable local set of representative HTML inputs
- document which fixture covers which rule family:
  - conventional prose
  - semantic callouts
  - collapsible sections
  - SVG-heavy visual layout

Reason:

- importer behavior will be easiest to stabilize against real fixture files rather than synthetic snippets

### 3. Add A Shared HTML Import Conversion Module

Create a conversion module under `scripts/docs/` that:

- loads a staged HTML file
- parses the full document into a DOM-like in-memory tree
- extracts title/body content
- sanitizes unsafe or irrelevant elements
- converts supported structures into Markdown
- preserves selected safe inline HTML such as:
  - `<sub>`
  - `<sup>`
  - inline `<svg>`
- returns structured warnings and summary counts

Required v1 behaviors:

- page-level `<head>` and page-shell styling removed
- prompt/meta blocks handled by the include toggle and only when clearly identifiable
- `details/summary` flattened into readable static content
- semantic callouts simplified rather than dropped
- repo-local image paths degraded to plain text
- external images and `data:` URLs handled best-effort, with plain-text fallback when doubtful
- replaces the temporary stdlib parser scaffold with the pinned parser/sanitizer stack

### 4. Add Jekyll-Based Validation

Add a validation step that renders the generated Markdown through the repo's existing Jekyll docs path before write completion.

Required outcome:

- import fails cleanly when the generated Markdown cannot be rendered through the docs pipeline
- warnings stay separate from hard render failures

Reason:

- Jekyll render success is the real runtime contract for the Docs Viewer

### 5. Extend The Docs-Management Server

Add `POST /docs/import-html` to `scripts/docs/docs_management_server.py`.

Required behavior:

- validate scope
- validate staged filename under `var/docs/import-staging/`
- accept `include_prompt_meta`
- detect collisions against existing docs
- support explicit overwrite by `doc_id`
- require confirmation before overwrite
- preserve target doc identity on overwrite
- create untracked light-touch backups before replacement
- rebuild same-scope docs payloads
- rebuild same-scope docs search
- return structured result metadata and warnings

### 6. Add The Studio Import Page

Create a new Studio route and controller for HTML import.

Required UI:

- staged file selector
- scope toggle
- prompt/meta include toggle
- import action
- overwrite warning state
- result summary with next links

Required behavior:

- local-only
- fail closed when the docs-management service is unavailable
- no inline markdown editing
- no pre-write preview

Visible runtime copy should come from `assets/studio/data/studio_config.json`.

### 7. Add Overwrite And Backup Handling

Implement the overwrite confirmation and backup path as a first-class workflow.

Required outcome:

- overwrite only after explicit warning and confirmation
- overwrite target identified by `doc_id`
- same-day backup replacement allowed for v1
- backups remain untracked

Reason:

- early testing is expected to overwrite the same target repeatedly

### 8. Verify With The Real Fixtures

Run the importer against the reviewed example files and verify the expected outcomes.

Required checks:

- prose/table import
- semantic callout simplification
- `details/summary` flattening
- SVG preservation with local SVG styling
- prompt/meta include/exclude behavior
- overwrite flow
- best-effort image and `data:` fallback behavior

### 9. Update Runtime And Script Docs

After the implementation lands, update the runtime/reference docs so the feature is discoverable and operationally clear.

Minimum docs follow-through:

- new Studio page doc if the route is user-facing
- docs-management server endpoint documentation
- Studio/runtime docs if route inventory changes
- site change log entry

## Verification

Codex-run checks:

- Python syntax checks for new/changed Python files using the configured project Python interpreter
- confirm the pinned parser/sanitizer libraries are importable in the configured project Python
- dry-run style fixture execution where possible before live writes
- `./scripts/build_docs.rb --scope studio --write`
- `./scripts/build_search.rb --scope studio --write`
- targeted import tests against the reviewed HTML fixtures
- Jekyll render verification for generated Markdown through the current docs pipeline

Manual checks:

- use the Studio import page to import one staged file into `studio`
- repeat with `library`
- confirm overwrite warning behavior is clear
- confirm imported doc opens in the correct viewer scope
- confirm SVG-heavy fixture renders acceptably in the Docs Viewer

## Open Implementation Risks

- prompt/meta detection may drift across older and newer ChatGPT exports
- SVG sanitization can break diagrams if it is too aggressive
- best-effort image handling may still produce awkward output in some files
- overwrite flow is easy to get wrong if target resolution and warnings are not explicit
- fixture behavior may reveal that one or two locked v1 assumptions need refinement

## Benefits

- turns the approved spec into a concrete execution sequence
- keeps v1 narrow enough to build without overcommitting to unsupported HTML patterns
- provides a clear fixture-driven path for validation

## Done Criteria

- Studio has a working local HTML import page
- the docs-management server can import staged HTML into `studio` or `library`
- create and overwrite both work under the confirmed warning/backup contract
- generated Markdown renders successfully through the Jekyll docs path
- the four reviewed example files are covered by implementation verification
- follow-on docs are updated so the new feature is operationally documented

## Related References

- [UI Requests](/docs/?scope=studio&doc=ui-requests)
- [Docs HTML Import Spec](/docs/?scope=studio&doc=ui-request-docs-html-import-spec)
- [Studio UI Start](/docs/?scope=studio&doc=studio-ui-start)
- [Studio](/docs/?scope=studio&doc=studio)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Docs Management Server](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Viewer Builder](/docs/?scope=studio&doc=scripts-docs-builder)
