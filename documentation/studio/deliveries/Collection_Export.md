---
draft: false
doc_id: d-20261019-184003-68b57f
title: Collection Export
added_date: "2026-10-19 18:40:03"
last_updated: "2026-10-19 18:40:03"
parent_id: d-20260428-000000-f5ff18
---
# Collection Export

Parent: [Planned Features](../Planned_Features.md). Durable owner: [Export](../Export.md). Status: user-approved, implemented and reviewed on 2026-10-19; awaiting manual acceptance after restarting Docs Viewer and reloading Manage.

## Agreed Result And Ownership

Each Collection Actions menu offers Export for the existing checked-document selection, disabled when empty. The browser owns selection and captures the exact collection/IDs before confirmation; All/Clear/Done retain their current filtering, paging and retained-selection behavior. Selection is shared with Prepare Package without inheriting that action's restrictions. Catalogue offers Export while its editing and package restrictions remain intact. The top-row whole-ordinary-Index action and invoked ordinary subtree action keep their selection owners.

Python resolves one configured Working owner, reads its generated Index/collection manifest and selected by-ID HTML, prepares only referenced owned media, renders the existing browseable/portable output and writes through the existing confirmed snapshot operation. Collection titles name folders and indexes; links, provenance, plan identity and Apply preserve the owning collection. Public reference links consume the configured viewer route. Catalogue Work media remains external under the existing unmatched-media policy; this delivery does not introduce offline Catalogue media packaging.

## Completion Gates

- [x] User approval of this bounded implementation and shared exporter reuse.
- [x] Collection Actions/selection wiring, exact Preview/Apply identity and existing busy/confirmation behavior.
- [x] Selected generated input/media owners, collection labels, portable/multi-file link rewriting and provenance.
- [x] Focused lint, compilation, import diagnostics, metadata inspection and whitespace checks.
- [x] Distinct code review and mandatory Redundancy And Defensive Behavior Review; durable documentation and icon mapping updated.
- [ ] Manual acceptance: enter Actions, select one/several/all documents, confirm disabled-empty behavior, export/create/replace, inspect packaged document media and selected/unselected/cross-collection links. Include Catalogue's Export-only selection and an ordinary Index export.

## Selected Evidence And Limits

The verification budget is changed-path Python/JavaScript lint, two-file Python compilation/imports, read-only inspection of current generated metadata and source/diff review, followed by whitespace checks. These address syntax/import integration and the inspected request/owner/rendering boundary, cost seconds of local execution and write only ordinary lint/bytecode caches. Metadata inspection read each configured collection's manifest and one selected payload to establish the existing format: Library 68, Context 187, Concepts 246, Moments 58 and Catalogue 4,618 rows. No source documents, generated outputs or snapshots were written; no network, browser, test or publication work ran. There is no live Export evidence.

Passed commands: `PATH="$HOME/miniconda3/bin:$PATH" bin/lint-python docs-viewer/services/docs_static_html_export.py docs-viewer/services/docs_static_html_export_media.py`; `bin/lint-js` for `docs-viewer-action-definitions.js`, `docs-viewer-management-client.js`, `docs-viewer-management-collection-default-contribution.js`, `docs-viewer-management-document-reports.js` and `docs-viewer-static-html-export-workflow.js` under `docs-viewer/runtime/js/management/`; `$HOME/miniconda3/bin/python3 -m py_compile` for both Python owners; direct imports of both service modules with the configured environment; and `git diff --check`.

All changed JavaScript is local management code outside `site-code-update.json`; there is no public runtime projection or static-site payload change. [Export verification](../Export.md#verification) records the unreviewed existing test boundary. Tests/fixtures/harnesses remain unchanged and unrun; the media planner now takes its explicit media-type map and render helpers require collection/public-route inputs, so old-signature tests require separately approved migration. No Build, Search rebuild, Publish, commit, push or deployment ran.

## Code Review And Redundancy And Defensive Behavior Review

Reviewed empty selection, checked selection capture, ordinary/subtree behavior, Catalogue restrictions, generated owner resolution, media planning, both renderers, Preview-to-Apply handoff and the existing destination writer. The implementation removes Prepare Package as the selection-visibility owner, reuses the existing menu item/selection/confirmation/writer owners, and replaces the media planner's whole-stage dependency with the resolved map it actually consumes. It adds no capability request, manifest reload, source read, rebuild, corpus payload scan, schema alias or recovery path. The configured public viewer route replaces the exporter's hard-coded `/docs/` route; selected links require both matching collection and document identity. Unselected/cross-collection query links remain viewer links rather than resolving inside the exported folder.

Retained safeguards: incoming collection/selected-file identity and configured-owner resolution prevent arbitrary input paths; metadata JSON parsing and missing selected inputs fail visibly; media adapters retain confined identities, availability and portable-path collision checks. Existing explicit replacement confirmation, one Apply plan/destination comparison, destination path/symlink confinement, media digest identity and one final file-set/byte verification protect the confirmed user-owned export destination. No additional scans, audits or validation pass were added. Review removed a duplicate capability-path existence check after its owning resolver had already established the same facts. Selected reads remain bounded to one owner's metadata plus selected payload/media bytes; the existing Apply recomputation remains part of the agreed snapshot replacement contract.
