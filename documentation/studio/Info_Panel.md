---
draft: false
doc_id: d-20260623-000000-c99cef
title: Info Panel
added_date: "2026-06-23 00:00:00"
last_updated: "2026-10-01 17:58:55"
parent_id: d-20260424-000000-50b63f

---
# Info Panel

The Docs Viewer Info panel retains a document's related context beside the main pane. A reader intentionally opens it with **Pin related links** beside a non-empty generated [Related Links](Related_Links.md) section. The panel is always pinned to that document until another pin replaces it or Close releases it. Public and Manage share the reader presentation through [CSS Ownership](CSS_Ownership.md).

## Reader Workflow

- A pin appears beside the section's optional authored H3 heading. A heading-free directive still has a pin. Empty generated sections and documents without the directive have no pin.
- The shell's top row shows the captured document title and a right-hand **Close** control. Long titles wrap before the vertically centred close button.
- The body contains only a non-empty, uncaptioned summary and a copy of the generated related list. It has no repeated heading, pin, IDs, dates, operational fields, diagram-source links or empty-state messages.
- The list retains its collection icons, title ordering, deduplication and exact destinations. Concepts use the same list. The panel body uses the document's loose line spacing and the public list's row gap on both public and Manage surfaces. Links share the document's blue unvisited and purple visited colours, with no underline until hover or keyboard focus.
- Following a panel link or navigating elsewhere changes the main pane while preserving the capture. Another document's pin replaces the capture; repeating the captured document's pin leaves it open.
- Close releases the capture. Navigation does not reopen the panel. Reload clears the capture; persistence, cross-tab synchronization and bookmarkable panel state are outside this workflow.

The rendered-document toolbar has no **i** action. The related section's pin is the reader's only opening control. A summary alone does not make a document eligible to open the panel.

## Data And Exact Targets

Pins capture title and summary from the already loaded by-ID payload and a detached copy of that section's resolved list. Ordinary mounts supply their document ID; collection-detail mounts supply their own exact `{collection, doc_id}` and payload. The selected report host never substitutes for its detail document.

The panel does not fetch relationship records, collection manifests or neighbouring documents. The detached capture survives removal or refresh of the original mount, and normal main-document updates cannot retarget it. The existing root route listener activates panel links through the current local/public reader route, retaining exact report-host and sub-document destinations.

[Builder](Builder.md) owns relationship construction and generated-section freshness. Link targets are the author's references, independently of draft, ordinary ignore membership, inherited publication exclusion or prepared-document membership. A public list can therefore retain a destination whose body was omitted. Following it receives the ordinary unavailable-document response; opening the panel adds no target-readiness scan, warning or publication gate.

## Hosting And Lifetime

The shared panel retains three focused owners:

- `docs-viewer/runtime/js/shared/docs-viewer-info-panel-renderer.js` creates the shell and projects title, visibility and Close.
- `docs-viewer/runtime/js/shared/docs-viewer-info-panel-controller.js` owns the detached reader capture, replacement, repeated-pin behavior and Close.
- `docs-viewer/runtime/js/shared/docs-viewer-info-panel-host.js` loads and mounts the chosen view, invalidating pending loads and shell updates after replacement or Close.

`docs-viewer/runtime/js/shared/docs-viewer-related-links.js` owns pin mounting and the synchronous `related-links` hosted view. That view receives only the capture; it has no main-document subscription or service handles. It copies only the list, so the document heading and opening pin never appear inside the panel. Missing body content produces no placeholder.

`docs-viewer/runtime/js/shared/docs-viewer-document-view-coordinator.js` wires pin mounts and document-mode transitions through these owners. Ordinary and collection-detail mounting provide explicit inputs; the app runtime only wires the callback. Public/Manage view registration makes reader capture available on those routes. Exports and Docs Review retain their static lists without the reader opening control.

## Source Boundary

Entering Source closes and releases the reader capture. Source has no hosted metadata/token view, selection-driven panel routing or **i** control. Returning to rendered content leaves the reader panel closed until a non-empty related section's pin is used.

Source edits complete Markdown, including Title/Summary and other valid front matter, in one buffer. Catalogue modals create and edit supported occurrences there through guarded insertion or Apply. One Save persists the validated complete source; it does not move or reparent the document. [Source Editor Scripts](Source_Editor_Scripts.md) owns authoring integration and [Source Editor Endpoints](Source_Editor_Endpoints.md) owns persistence.

## Public And Local Boundary

Canonical shared JavaScript, styles and artwork live under `docs-viewer/` and reach `site/docs-viewer/` through the explicit tracked code projection. Public readers reuse their loaded prepared sections and configured routes without management modules, local service calls, capability probes or Working fallback. Preview is a physical publication artifact without a browser stage or read route.

Local Manage uses Working generated content. Source editing remains management-only; its editor, modals and service adapters stay outside the public inventory. Public-safe reader shell/controller code is projected explicitly, without management calls or authoring context in the capture.

Ordinary interaction, long-title fit, Close alignment and public mobile presentation require manual review. Automated test changes require an agreed specification under [Testing](Testing.md). [Docs Viewer Runtime](Docs_Viewer_Runtime.md) owns the wider runtime boundary.
