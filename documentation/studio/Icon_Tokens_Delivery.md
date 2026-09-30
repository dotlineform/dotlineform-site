---
draft: false
doc_id: d-20260930-202533-921c4b
title: Icon Tokens Delivery
added_date: "2026-09-30 20:25:33"
last_updated: "2026-09-30 20:25:33"
summary: Deliver manual SVG icon tokens and Source insertion; static verification and code review precede user visual acceptance.
ui_status: in-progress
parent_id: d-20260910-223116-9a1011
---
# Icon Tokens Delivery

## Requirements

Deliver `[[icon:<filename-stem>]]` for manual use. **Directives → Insert icon** inserts `[[icon:refresh-cw]]` inline and selects its filename stem for editing. Render at the surrounding text size and colour, preserve literal examples, report missing/invalid artwork clearly and keep public/review/export content portable. There is one extensionless form, without aliases or a second icon-name registry.

## Deliverables

- A shared builder-owned inline-icon renderer using existing canonical SVGs and the existing sanitizer.
- Ordinary/collection payload integration and one local Source menu entry.
- Durable [Icon Tokens](Icon_Tokens.md) documentation and current navigation from the shared-icon proposal and Source owner.

Related-links generation, collection icon mappings, an icon picker, native App work and test changes are outside this delivery.

## Process

Insert the token in Source, edit the selected filename stem, then Save. The watcher rebuilds the document independently. Icons are embedded in the generated content and require no reader-time lookup. Missing files fail the owning build; fix the token/artwork and rebuild.

## Delivery Steps

### IT-0 — Readiness

- [x] Confirm the authoring syntax, Source insertion and export boundary against current owners.
- [x] Record implementation approval and the bounded verification budget.

Record: the user approved implementation after choosing extensionless filename stems. The existing Directives owner supplies captured insertion and placeholder selection; payload generation is shared by ordinary, collection, Review and package builds. Embedding sanitized mask bytes avoids a new asset-resolution or export-packaging owner.

Verification budget: source/diff review, explicit lint and syntax for the four changed Python files and one changed JavaScript file, whitespace checks, the existing public projection consistency check and the builder's read-only `--help` import diagnostic. These are local static/diagnostic checks with expected runtime of seconds and only normal lint/bytecode cache effects; they do not build documents, start a browser/server or mutate canonical documents. No tests, fixtures or temporary regression scripts are authorized. Visual fit and Source interaction are user manual review.

### IT-1 — Implementation

- [x] Render exact extensionless stems through one portable icon owner.
- [x] Integrate document builders and add inline Source insertion with filename selection.
- [x] Document ownership, failure, accessibility and export behaviour.
- [x] Complete the selected static checks.

Gate: static checks pass and the bounded implementation is ready for code review. Record: four Python files and the Directives module passed explicit lint; Python compilation passed; `bin/site-code-update --check` reported 98 unchanged public files and no changes. `build_docs.py --help` completed successfully, confirming CLI imports without a build. Tracked/new source whitespace review reported no issues. The menu module is local-only and the renderer is build-time Python, so no public runtime projection is required. No document build, Search rebuild, Publish, commit or push is part of this delivery.

### IT-2 — Code Review

- [x] Review the bounded production/documentation diff for ownership, literal handling, lookup safety, export portability, stale caches and unintended aliases.
- [x] Resolve findings and rerun only affected checks.

Gate: no blocking code-review findings. Record: review confirmed normal Markdown parsing and explicit HTML-code/image-alt preservation, operation-scoped SVG caching, exact confined filenames, self-contained masks and text-export token retention. Review tightened path confinement and read/sanitizer diagnostics; the affected renderer passed lint and compilation again. Shared-icon documentation was reconciled to the current Subject icon files and a stage-free report link. No aliases or extra runtime consumers were introduced. Static evidence does not establish browser appearance or exercise authored-source builds/export operations; those limits remain explicit.

### IT-3 — Closeout

- [ ] Record user manual acceptance of Source insertion/selection and rendered icon appearance.
- [x] Confirm the durable owner and present the retain-or-retire recommendation.

Gate: user acceptance of the manual interaction and visual result. Retain [Icon Tokens](Icon_Tokens.md) as the durable owner and [Shared Icons](Shared_Icons.md) for its remaining collection/native scope; recommend archiving this delivery after acceptance. No document is deleted automatically.

## Follow-on

The related-links builder can later select an icon by collection and call the same renderer. That requires its own agreed presentation and build slice. Any test work requires a separate specification under [Test Contract Discipline](Test_Contract_Discipline.md).
