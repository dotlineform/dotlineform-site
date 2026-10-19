---
draft: false
doc_id: d-20261019-184003-68b57f
title: Collection Export
added_date: "2026-10-19 18:40:03"
last_updated: "2026-10-19"
parent_id: d-20260428-000000-f5ff18
---
# Collection Export

Parent: [Planned Features](../Planned_Features.md). Durable owner: [Export](../Export.md). Status: user-approved, implemented, consolidated and cleanup-reviewed on 2026-10-19; awaiting manual acceptance after restarting Docs Viewer and reloading Manage.

## Agreed Result And Ownership

Each Collection Actions menu offers Export for the existing checked-document selection, disabled when empty. The browser owns selection and captures the exact collection/IDs before confirmation; All/Clear/Done retain their current filtering, paging and retained-selection behavior. Selection is shared with Prepare Package without inheriting that action's restrictions. Catalogue offers Export while its editing and package restrictions remain intact. Export has no workspace or Index entry point. `docs-viewer-collection-export-workflow.js` owns all browser Export requests, confirmation, status and busy completion; report composition supplies its target and management dependencies without a second workflow wrapper.

Python requires one configured Working collection, reads its generated manifest and selected by-ID HTML, prepares only referenced owned media, renders the existing browseable/portable output and writes through the existing confirmed snapshot operation. The snapshot service owns the operation and delegates only referenced-media preparation to its media helper. Collection titles name folders and indexes; links, provenance, plan identity and Apply preserve the owning collection. Public reference links consume the configured viewer route. Catalogue Work media remains external under the existing unmatched-media policy; this delivery does not introduce offline Catalogue media packaging.

The six approved review cleanups retain exact-bytes confirmation and final output verification. Each request resolves its export workspace once; generated payloads are trusted after request identity/owner checks; media prefix preparation and HTML collection/rewriting each have one owner/pass. Replacement treats any existing directory the same, without a prior-manifest audit. Installation creates required directories once and carries its prepared set into verification. The browser consumes the service's replacement decisions directly.

## Completion Gates

- [x] User approval of this bounded implementation and shared exporter reuse.
- [x] Collection Actions/selection wiring, exact Preview/Apply identity and existing busy/confirmation behavior.
- [x] Remove workspace/Index menu items, dispatch/state, separate workflow wrappers, Export capability projections/preflights and ordinary-tree/default-document export branches without compatibility aliases.
- [x] Selected generated input/media owners, collection labels, portable/multi-file link rewriting and provenance.
- [x] Implement all six approved review cleanups: remove prior-snapshot audit, duplicate media HTML/configuration processing, repeated workspace resolution, downstream record checks/repair, duplicate directory preparation and browser decision rechecks.
- [x] Focused lint, compilation, import diagnostics, metadata inspection and whitespace checks.
- [x] Distinct code review and mandatory Redundancy And Defensive Behavior Review; durable documentation and icon mapping updated.
- [ ] Manual acceptance: enter Collection Actions, select one/several/all documents, confirm disabled-empty behavior, export/create/replace, inspect packaged document media and selected/unselected/cross-collection links. Include Catalogue's Export-only selection and confirm the workspace/Index menus reflect the current collection-only contract.

## Selected Evidence And Limits

The verification budget is changed-path Python/JavaScript lint, Python compilation/imports and bounded source/diff review, followed by whitespace checks. These address syntax/import integration and the inspected request/owner/rendering boundary, cost seconds of local execution and write only ordinary lint/bytecode caches. Earlier read-only metadata inspection established that all five current collections share the required generated manifest/by-ID format. No source documents, generated outputs or snapshots were written; no network, browser, test or publication work ran. There is no live Export evidence.

Consolidation passed `PATH="$HOME/miniconda3/bin:$PATH" bin/lint-python` and `$HOME/miniconda3/bin/python3 -m py_compile` for `docs_static_html_export.py`, `docs_management_capabilities_service.py` and `docs_viewer_service.py` under `docs-viewer/services/`, plus direct imports of those three modules with the configured environment. `bin/lint-js` passed for ten management owners: `docs-viewer-action-definitions.js`, `docs-viewer-management-actions-renderer.js`, `docs-viewer-management-capabilities.js`, `docs-viewer-management-client.js`, `docs-viewer-management-document-reports.js`, `docs-viewer-management-event-router.js`, `docs-viewer-management-index-controller.js`, `docs-viewer-management-shell-renderer.js`, `docs-viewer-management.js` and `docs-viewer-collection-export-workflow.js`. Final `git diff --check` passed after removing an extra trailing blank line.

The six-cleanup follow-up passed changed-path Python lint/compilation/imports for `docs_static_html_export.py` and `docs_static_html_export_media.py`, JavaScript lint for `docs-viewer-collection-export-workflow.js`, and whitespace checks. Source/diff review traced all three target states, media deduplication/path rewriting, absent/owned/external media handling, root handoff, directory creation and final verification. The shared confirmation modal rejects submission while its primary button is disabled, so the removed Export-specific post-confirmation check duplicated the modal's actual owner. These are static/source-inspection findings; no live Preview/Apply or renderer execution was used as evidence.

All changed JavaScript is local management code outside `site-code-update.json`; there is no public runtime projection or static-site payload change. [Export verification](../Export.md#verification) records the unreviewed existing test boundary. Tests/fixtures/harnesses remain unchanged and unrun; tests of retired ordinary export/capability entry points, prior-snapshot summaries/target states and former workflow/media-prefix/render/writer helper signatures require separately approved migration. No Build, Search rebuild, Publish, commit, push or deployment ran.

## Code Review And Redundancy And Defensive Behavior Review

Reviewed empty/checked selection, Catalogue restrictions, collection-only resolver/endpoint authority, menu/route wiring, both renderers, Preview-to-Apply handoff and the existing destination writer. Consolidation removes the workspace workflow, generic export workflow, Index controller branches, export-specific management-client wrappers, capability parser/projections and their view-only masking, ordinary Index input/hierarchy traversal/filtering, recursive rendering and global-default selection. The single browser workflow trusts the completed selection and service records instead of retaining ID normalization, callback fallbacks or response coercion. Menu composition only wires its exact target and existing services. No compatibility alias, source read, rebuild, corpus payload scan, new capability request or recovery path remains. The configured public viewer route and collection identity continue to own selected/cross-collection link behavior.

Retained safeguards: management route access, required configured collection and safe selected filenames own request authority/confinement; metadata JSON parsing and missing selected inputs fail at their actual reads. Media adapters retain confined identities, availability and portable-path collision checks. Existing explicit replacement confirmation, one Apply plan/destination comparison, destination path/symlink confinement, media digest identity and one final file-set/byte verification protect the confirmed user-owned export destination. No additional scans, audits or validation pass were added. Redundant input existence preflights and the full ordinary-tree ID audit were removed with their obsolete owners. Selected reads remain bounded to one collection's metadata plus selected payload/media bytes; the existing Apply recomputation remains part of the agreed snapshot replacement contract.

Final cleanup review resolved all six findings:

- Prior-snapshot handling now classifies only `absent`, `directory` and `non_directory`. The saved-manifest parser, its per-media/dependency audits, unused summary and recognized/unrecognized distinction are removed without aliases. The destination revision still hashes actual existing bytes once per request.
- Media planning prepares parsed configured prefixes once, collects references/dependencies and writes deterministic package URLs in one HTML pass, then reads each distinct selected object once. Case/path collision checks remain before byte reads. Original HTML is preserved when no owned media is present; the second media-HTML pass and repeated prefix sorting/parsing/validation are gone.
- The resolved export root is part of the internal plan. Destination confinement consumes it and Apply reuses it for root creation, replacing two Preview/three Apply resolver calls with one per request. There is no cross-request cache or retained server plan.
- Request filename and configured-owner checks remain authoritative. Payload loading and rendering no longer revalidate IDs, audit generated ID agreement, overwrite missing IDs, coerce generated title/body fields or fall back to substitute content. HTML parsing and output escaping remain at their actual boundaries.
- Installation owns one required-directory set and one creation pass. The writer consumes ready directories, and verification receives the same set with no unused plan dependency or expected-directory recomputation. Completion-manifest-last writing and final exact file-set/byte verification remain intact.
- The browser uses `replacement_required` and `replace_allowed` from Preview for confirmation and Apply. Export-specific target-state classification and the post-confirmation availability check are removed; the modal owns disabled submission and the server retains request/replace authority.

The complete Apply replan, selected payload/media rereads and old-destination hashing across Preview/Apply remain intentional under the agreed exact-bytes confirmation contract. This cleanup introduces no snapshot-schema audit, compatibility layer, automatic repair, retry/rollback or stronger recovery behavior.
