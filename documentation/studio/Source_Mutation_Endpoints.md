---
draft: false
doc_id: d-20260607-222033-ce5515
title: Source Mutation Endpoints
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-13 15:47:31"
parent_id: d-20260607-222033-647b52
---
# Docs Viewer Source Mutation Endpoints

Working resolves exact ordinary `{doc_id}` or configured named-collection `{collection, doc_id}` targets from its workspace configuration. Stage/scope selectors and identity fallbacks are retired. Source paths are confined to the configured owner; required request representation, parsing, identity and actual operation failures remain checked. Editorial action availability belongs to the frontend.

Common source editing and Subject buffer changes use [Source Editor Endpoints](Source_Editor_Endpoints.md). The old metadata, immediate Subject field-group and Set Publishable writes are retired without aliases. [Management Operations](Management_Operations.md) owns current action completion and failure behavior.

## `GET /docs/metadata`

The read resolves the exact configured source and returns `record`, target identity and `location_parent_id`; named collections also receive their Folder Subject capability. Ordinary resolution uses Index membership/parent data and its one source, without parsing the corpus. Saved source readiness/report completion does not prevent Source correction. The response contains no source revision. Source load and candidate Save retain their separate owners.

## `POST /docs/set-draft`

The exact request is `{doc_id, draft}`, with `collection` only for a named owner. `draft` must be boolean. Catalogue rejects this write; other documents retain explicit readiness independent of `unpublishable.json`.

The operation parses the exact source once, rewrites only Draft using retained field spans and preserves all unrelated text/body/dates. Prepared metadata/source/report inputs pass into the existing in-process exact document/Links builder without reopening source. Unchanged readiness still awaits exact generation. No metadata GET or source revision participates.

The response carries `target` and its complete committed `record`, plus `source_saved`, `generation_complete` and build diagnostics on a write run. Generation failure returns non-success with persisted source/record and unfinished generation; no restoration runs. The browser projects the returned record through the common owner and surfaces projection failures. Search, registered media production and Publish remain separate.

## `POST /docs/set-selected`

The exact request is `{doc_id, selected}`, with optional `collection` and a boolean `selected`. Star reads exact source metadata for its Selected row. Unstar resolves only its configured owner/identity and removes that row without reading source. Both persist Working `selected.json`, preserve dates/readiness and return the exact target and selected state. Public selection filtering remains Publish-owned.

## `POST /docs/move`

The exact ordinary request is `{doc_id, target_doc_id, placement}`, where `placement` is `before`, `after` or `inside`. An empty destination means Root and requires `inside`. Named collection placement is unsupported.

Position moves the complete canonical Index node with descendants, checks the destination/cycle once and projects saved generated navigation plus only the moved by-ID parent field. It preserves source bytes, rendered body, dates and Links. Collection-host root destinations are enforced by frontend choice, without a server editorial host-root validator.

The response carries `target`, `position_saved`, `generation_complete`, `phase` and the common `committed_document: {target, record}` after the canonical tree write. A later failure reports persisted position and unfinished generation. The browser projects the record and awaits one Index refresh after successful generation.

## `POST /docs/delete`

The exact ordinary request is `{doc_ids: ["<root-id>"], confirm: true}`; nonempty arrays of exact subtree roots are accepted. A named collection uses exactly `{collection, doc_id, confirm: true}`. Direct Catalogue deletion is Regenerate-owned and rejected.

Confirmation derives ordinary scope from the full loaded Index, including collapsed descendants, or the singular flat collection target. It performs no preview request. The service reads canonical tree and Selected once, expands requested ordinary subtrees once and unlinks exact confined source paths. It updates ordinary Index and removes exact Selected rows; a deleted configured default is cleared. Known deleted IDs, remaining parent map, Selected and resolved configuration pass into the existing in-process document/Links builders without source rereads or unrelated payload preflights.

The response carries `target`, `requested_doc_ids`, actual `deleted_doc_ids`, `delete_count`, `source_deleted`, `index_updated`, `selected_updated`, `generation_complete`, `phase`, build diagnostics and `dry_run`. Collection `index_updated` stays false because its ordinary tree is unchanged. A completed default clear adds `default_doc_id_changed: true` and `default_doc_id: ""`. Failures retain completed effects and report the target/phase; a source failure includes `failing_target`. No source revision, rollback, recovery build, public-cleanup or lineage receipt is produced.

The browser projects actual committed deletions/default changes and reports generation and display failures separately. Complete ordinary deletion awaits one Index refresh; displayed deletion awaits surviving-caller or fallback navigation under the busy state. Preview/public distribution, Recent/Search refresh and registered media remain with their own owners. The former `/docs/delete-preview` and `/docs/delete-apply` routes are removed without aliases.
