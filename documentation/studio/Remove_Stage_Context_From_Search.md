---
draft: false
doc_id: d-20260924-203338-b9417d
title: Remove Stage Context From Search
added_date: "2026-09-24 20:33:38"
last_updated: "2026-09-24 20:33:38"
summary: Make Search JSON independent of stage and navigation routes before changing Search coverage or build ownership.
parent_id: d-20260924-135214-baa9ec
---
# Remove Stage Context From Search

## Requirements

Remove embedded stage and result URLs from Search before doing other Search work. Keep exact document/collection/report-host identity and let the consuming route supply navigation context. Preserve corpus membership, field policy, tokenizer, ranking, postings and build ownership. Existing historical tests remain unchanged; no compatibility reader is retained for retired Search schemas.

## Deliverables And Process

The builder emits `docs_viewer_search_index_v4` without `header.stage` or `docs[].href`, and the content version excludes stage. Browser readers validate v4 and continue constructing result URLs through the current route. Public document locations now derive their URLs from exact IDs and configured routes. Snapshot readers/validators accept v4; generic stage projection passes Search through without rewriting or rehashing it. Existing public collection-display-title projection remains unchanged.

Convert saved Working, Preview and tracked public indexes in place, preserving each one's existing documents, order, metadata, fields, terms and generation timestamp. Update the Preview receipt with the converted Search hash and record its prior revision; retain original preparation provenance. Update paired local/public browser config and project shared runtime assets. A format conversion does not bring historical indexes up to date with newer source.

## Delivery Steps

- [x] Readiness: explicit user approval and inspection of builder, browser, snapshot, deployment and document-location consumers.
- [x] Implementation: stage-independent v4, reader/config cutover, removal of obsolete Search URL projection and stage-based rehashing.
- [x] Saved payload conversion: Working 5,214 documents, Preview 4,935, tracked public 318. Each retained its document table except `href`, all term postings and generation time. Preview receipt validates after the Search-only conversion.
- [x] Focused checks: six changed Python files and three shared JavaScript files passed lint; Search builder dry run passed for current Working source (5,213 documents); public document-location dry run reported unchanged output (318 records). Runtime projection/check and site validation passed.
- [x] Final code review and whitespace check. Preview schema/manifest validation passed, and read-only Deploy Repo projection resolved 4,935 document locations and 4,944 output files without applying them. No active v3 Search consumer, embedded-stage check or retired Search URL rehash helper remains. Historical tests are unchanged and were not run.
- [ ] User-owned process restart and browser review; delivery acceptance.

Verification budget: existing lint/whitespace/config checks, one real Search dry build, one document-location dry build, snapshot validation and read-only deployment projection. Expected local work is seconds to tens of seconds; no R2 writes or browser automation. No new tests, fixture changes, coverage changes, full Preview preparation, Deploy Repo apply, commit, push or public deployment. The user's terminal owns the running services.

## Follow-on

The agreed ordinary/Works/Processing corpus, inherited draft/unpublishable exclusions and Working-only Search build/copy ownership remain the next Search delivery. This prerequisite does not reconcile the different historical membership of the three saved indexes.
