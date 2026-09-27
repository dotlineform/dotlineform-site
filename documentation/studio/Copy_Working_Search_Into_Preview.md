---
draft: false
doc_id: d-20260924-210855-8b419e
title: Copy Working Search Into Preview
added_date: "2026-09-24 21:08:55"
last_updated: "2026-09-24 21:08:55"
summary: Make Working the sole Search builder and copy its existing index through Preview and repository projection before changing corpus policy.
parent_id: d-20260924-135214-baa9ec
---
# Copy Working Search Into Preview

## Requirements

The user explicitly selected workflow ownership before changing Search content. Working builds Search. Prepare Preview copies the existing Working index unchanged while continuing to build eligible documents and collection output. Deploy Repo copies those same Search bytes onward. Coverage, draft/unpublishable Search filtering, Recents and collection-search behavior remain separate work.

Preparation captures the existing index with the selected source and includes its bytes in the plan revision. A missing or malformed index fails without a fallback rebuild. Rebuilding Search during preparation invalidates the reviewed plan. An index may be stale relative to ordinary document edits; this slice does not require source freshness or compare Search membership with the prepared document set. The existing broader corpus can therefore contain results unavailable in Preview until the later coverage change.

## Deliverables And Process

`build_search.py` accepts Working only. Preview's orchestration builds ordinary and named-collection documents, prepares Mermaid, copies captured Search and records the complete generated manifest. Snapshot and repository projection bypass Search JSON reserialization, display-label rewriting and rehashing. Document tree/manifest/by-ID validation remains independent of Search; the old equality check between Search and all prepared document IDs is removed.

Prepare Preview retains its plan/apply review and completion receipt. The isolated capture builder returns validated snapshot files before the live replacement step. Existing Working and Preview indexes are not rebuilt or replaced merely to install this code; the user's next Prepare Preview applies the new copy workflow.

## Delivery Steps

- [x] Readiness: explicit user approval to implement workflow before corpus policy; inspected copy boundaries and the complete-build work previously coupled to Search rebuilding.
- [x] Implementation: capture/index revision binding; Working-only Search builder; Preview copy with complete document/media/manifest preparation; unchanged repository Search bytes and independent document validation.
- [x] Verification: six changed Python files passed lint. The Search CLI rejects Preview. One isolated real capture/build produced 4,935 documents and retained all 5,214 saved Search entries; Working, generated manifest, prepared snapshot and repository projection Search hashes all equal `7d4f9f91884c0946134fb6afc262fc848f0401edb576855f09a2cc6f2839b73c`. Its 5,005 snapshot files and 4,943 repository files passed the existing production preparation/projection checks. Live Preview revision remained unchanged. Evidence: `var/search-index-copy/verification.json`.
- [x] Code review: copy bytes participate in plan revision and completion records; Preview still builds every collection and prepares Mermaid. Document tree/manifest/by-ID validation remains independent of Search. No Preview Search builder or public Search label-rehash path remains. Working orchestration retains explicit full-index builds; its live rebuild was not run. Historical tests and fixtures remain untouched, with no browser or live apply evidence claimed.
- [x] Closeout: updated Search, Builder, configuration and checklist owners. The user's terminal-owned services and live snapshots were untouched; the next Prepare Preview uses the new workflow after the service reloads the changed Python code.

Verification budget: existing Python lint and CLI argument diagnostics plus one production capture/build in ignored temporary storage, with read-only repository projection and hash inspection. Expect seconds for lint/planning and roughly one to two minutes for document/media preparation. No test/fixture/harness changes, mock data, browser checks, live Preview replacement, deployment, service restart, commit or push. Historical tests remain unchanged.

## Follow-on

Implement the agreed ordinary/Works/Processing Search corpus and inherited draft/unpublishable exclusions as the next separate Search change. This delivery changes ownership and copying only.
