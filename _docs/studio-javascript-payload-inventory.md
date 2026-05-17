---
doc_id: studio-javascript-payload-inventory
title: Studio JavaScript Payload Inventory
added_date: 2026-05-14
last_updated: 2026-05-17
ui_status: urgent
parent_id: studio
sort_order: 70
hidden: false
---
# Studio JavaScript Payload Inventory

This document records the current browser JavaScript size inventory for Studio and adjacent Docs Viewer management runtime files.

It turns the durable inventory guidance from [JavaScript Payload And Runtime Cleanup Inventory](/docs/?scope=studio&doc=site-request-js-payload-runtime-cleanup-inventory) into the current Studio reference.

## Policy

Any browser JavaScript file over 1,000 lines should be classified as one of:

- route shell
- mixed route controller
- domain module
- generated/runtime utility

Any mixed route controller over 1,000 lines should have either:

- a named extraction slice in the owning request or implementation plan
- an explicit reason to stay large for the next implementation period

Prioritize long mixed controllers that combine mutation orchestration, modal composition, generated-data reads, and rendering.

Treat transfer-size risk separately from maintenance risk.
A large file is not automatically a runtime problem unless it is eagerly loaded on a high-traffic route or brings avoidable transitive payload.

Re-run this inventory after material Studio or Docs Viewer JavaScript refactors.

## Current Summary

Measured on 2026-05-17, after the Docs Viewer management drag/drop/context-menu extraction pass.

- Browser JavaScript files under `assets/`: 118
- Total browser JavaScript lines under `assets/`: 39,705
- Files over the 1,000-line review threshold: 5
- Files in the 900-1,000 line watch band: 5
- Over-threshold raw size total: 218.9 KiB
- Over-threshold gzip size total: 46.1 KiB

The over-threshold set is still maintenance-driven more than transfer-driven.
No route loads all over-threshold files together.

The modal extraction pass reduced several large mixed route controllers while adding focused route-local modal modules. The Docs Viewer management write-action, capability/config, and interaction extractions continued that pattern: total JavaScript lines increased because write orchestration, capability probing, config application, and management interactions now have named modules, but the management controller is smaller and no longer embeds every create/update/delete/move flow, capability retry, UI-text merge, drag/drop event, or context-menu dispatch inline.

The extraction plan is now complete: [Modal Responsibility Extraction Plan](/docs/?scope=studio&doc=modal-responsibility-extraction-plan).
The next modal-related work is pattern standardization, not further modal extraction: [Modal Composition Pattern Request](/docs/?scope=studio&doc=ui-request-modal-composition-pattern).

## Current Inventory

### `assets/studio/js/tag-studio.js`

- Lines: 1,846
- Raw: 61.4 KiB
- Gzip: 12.6 KiB
- Classification: mixed route controller
- Maintenance risk: high
- Transfer-size risk: low

The save preview modal rendering and wiring now live in `assets/studio/js/tag-studio-modals.js`.
The route still owns editor diff construction, save/probe decisions, clipboard write behavior, status wording, popup suggestions, assignment rendering, and editor rendering.
Next cleanup should target render groups and autocomplete/suggestion popup behavior before adding more tag editor workflow. Save modal extraction is complete.

### `assets/studio/js/tag-aliases.js`

- Lines: 1,181
- Raw: 38.7 KiB
- Gzip: 7.9 KiB
- Classification: mixed route controller
- Maintenance risk: high
- Transfer-size risk: low

Existing domain/save/service split is useful but incomplete.
Alias modal rendering, field population, popup option rendering, and modal event/lifecycle wiring now live in `assets/studio/js/tag-aliases-modals.js`.
The route still owns alias/tag lookup, validation decisions, match filtering rules, import parsing/submission, service calls, patch fallback decisions, route busy/ready state, and list/control rendering.
Next cleanup should target list/control rendering, import parsing/submission, or service orchestration. Modal extraction is complete.

### `assets/studio/js/tag-registry.js`

- Lines: 1,128
- Raw: 36.0 KiB
- Gzip: 7.8 KiB
- Classification: mixed route controller
- Maintenance risk: high
- Transfer-size risk: low

Existing domain/save/service split is useful but incomplete.
Registry modal rendering, field population, delete impact display, import result display, popup option rendering, and modal event/lifecycle wiring now live in `assets/studio/js/tag-registry-modals.js`.
The route still owns tag lookup, validation decisions, match filtering rules, import parsing/submission, service calls, patch fallback decisions, route busy/ready state, and list/control rendering.
Next cleanup should target list/control rendering, import parsing/submission, or service orchestration. Modal extraction is complete.

### `assets/docs-viewer/js/docs-viewer.js`

- Lines: 1,264
- Raw: 41.3 KiB
- Gzip: 8.9 KiB
- Classification: mixed shared viewer runtime controller
- Maintenance risk: high
- Transfer-size risk: medium

Recent extractions moved the largest non-route responsibilities out of the entry controller:

- Bookmark state, storage, rendering, and events now live in `assets/docs-viewer/js/docs-viewer-bookmarks.js`.
- Config/scope boot and viewer UI text merging now live in `assets/docs-viewer/js/docs-viewer-config-controller.js`.
- Sidebar/nav/meta rendering and trail display now live in `assets/docs-viewer/js/docs-viewer-sidebar.js`.
- Search loading, recent/search result rendering, result batching, and debounced search input binding now live in `assets/docs-viewer/js/docs-viewer-search-controller.js`.
- Result-row and bookmark-row markup helpers live in `assets/docs-viewer/js/docs-viewer-render.js`.
- URL building, anchor route parsing, history writes, requested-doc resolution, canonical route correction, popstate route orchestration, and payload-load orchestration now live in `assets/docs-viewer/js/docs-viewer-router.js`.
- Status-pill markup and events stay behind the lazy management-controller boundary.

The remaining entry controller responsibilities are route callback binding, generated-payload fetch dependencies, final payload rendering, reports entry, and management dynamic-loading.
Maintenance risk remains high because the entry controller still binds several cross-module runtime dependencies.
This is not an acceptable long-term resting point: avoid adding route behavior directly to the entry controller unless the same change also reduces the routing surface there.

The router extraction is complete for URL building, anchor route parsing, history writes, requested-doc resolution, canonical route correction, popstate route orchestration, and payload-load orchestration.
Do not reopen router work just for line count.
Future entry-controller cleanup should be triggered by concrete changes to generated-payload loading, final payload rendering, report ownership, or management dynamic-loading.

### `assets/studio/js/data-sharing-review.js`

- Lines: 1,109
- Raw: 41.6 KiB
- Gzip: 8.9 KiB
- Classification: mixed route controller
- Maintenance risk: medium
- Transfer-size risk: low

Result modal and apply-confirmation modal behavior now lives in `assets/studio/js/data-sharing-review-modals.js`.
The route still owns returned package loading, staged package listing, preview row rendering, selection state, preflight/apply service calls, apply result payload shaping, activity context, status updates, and route busy state.
Next cleanup should target preview table rendering or apply-action orchestration if the workflow grows further.

## Watch Band

These files are below the 1,000-line review threshold but close enough to watch during future feature work.

| File | Lines | Raw | Gzip | Notes |
| --- | ---: | ---: | ---: | --- |
| `assets/studio/js/tag-aliases-modals.js` | 964 | 35.2 KiB | 6.2 KiB | Under threshold and route-local. Keep it modal-focused rather than adding service or list rendering. |
| `assets/studio/js/tag-registry-modals.js` | 963 | 35.3 KiB | 6.6 KiB | Under threshold and route-local. Keep it modal-focused rather than adding service or list rendering. |
| `assets/docs-viewer/js/docs-html-import.js` | 960 | 33.2 KiB | 7.3 KiB | Under threshold and lazy management-only import flow. Keep service orchestration and modal rendering delegated. |
| `assets/studio/js/catalogue-work-actions.js` | 951 | 40.3 KiB | 6.6 KiB | Under threshold and route-local. Keep it action-workflow focused rather than adding form or section rendering. |
| `assets/docs-viewer/js/docs-viewer-management.js` | 918 | 31.9 KiB | 5.9 KiB | Under threshold after modal, action, capability/config, and interaction extractions. Keep it a management coordinator rather than adding interaction or write flow bodies back inline. |

## Current Priority

1. `assets/studio/js/tag-studio.js`
2. `assets/docs-viewer/js/docs-viewer.js`, evaluate any further reduction only when a concrete route or payload-rendering change needs it
3. `assets/studio/js/tag-aliases.js` and `assets/studio/js/tag-registry.js`
4. `assets/studio/js/data-sharing-review.js`

The Docs Viewer management controller is no longer over the review threshold after the drag/drop/context-menu extraction.
Do not open another Docs Viewer management split just for line count unless new management workflow growth pushes the coordinator back over the threshold or reintroduces mixed ownership.

The Docs Viewer entry controller remains over the review threshold after the sidebar, search, config, and router extractions.
Do not reopen router work just for line count.
Future entry-controller cleanup should be tied to concrete generated-payload loading, final payload rendering, report ownership, or management dynamic-loading changes.
Docs Viewer files remain in this inventory because `/docs/` is the Studio documentation and management surface.

The Tag Studio, Tag Aliases, and Tag Registry routes are still over the threshold after modal extraction. Their next likely slices are rendering helpers, inline suggestion/autocomplete popup ownership, import parsing/submission, and service orchestration. Avoid opening another modal-extraction slice for those files unless new modal responsibilities are introduced.

## Remaining Extraction Options

The modal extraction pass is complete. Remaining candidates are broader route-controller refactors:

- Tag Studio: split editor rendering groups and inline work/tag suggestion popup behavior from save/probe orchestration.
- Docs Viewer entry controller: split only when a concrete change touches generated payload loading, final payload rendering, report ownership, or management dynamic-loading.
- Tag Aliases and Tag Registry: split list/control rendering, import parsing/submission, or service orchestration from route state and validation decisions.
- Data Sharing Review: split preview table rendering or apply-action orchestration if the workflow grows.

Do not count route bridge calls into extracted modal modules as remaining extraction debt. They keep opener ownership visible and are an acceptable controller boundary.

## How To Rerun

Run this from the repo root:

```bash
find assets -type f -name '*.js' -print0 | xargs -0 wc -l | sort -nr
```

Use this for the line, raw byte, and gzip byte inventory:

```bash
python3 - <<'PY'
from pathlib import Path
import gzip

rows = []
for p in Path('assets').rglob('*.js'):
    data = p.read_bytes()
    lines = data.count(b'\n') + (0 if data.endswith(b'\n') or not data else 1)
    rows.append((lines, len(data), len(gzip.compress(data, compresslevel=9)), str(p)))

for lines, raw, gz, path in sorted(rows, reverse=True):
    print(f'{lines}\t{raw}\t{gz}\t{path}')
PY
```

To summarize only the review threshold and watch band:

```bash
python3 - <<'PY'
from pathlib import Path
import gzip

rows = []
for p in Path('assets').rglob('*.js'):
    data = p.read_bytes()
    lines = data.count(b'\n') + (0 if data.endswith(b'\n') or not data else 1)
    rows.append((lines, len(data), len(gzip.compress(data, compresslevel=9)), str(p)))

over = [r for r in rows if r[0] > 1000]
near = [r for r in rows if 900 <= r[0] <= 1000]

print('files', len(rows))
print('total_lines', sum(r[0] for r in rows))
print('over_count', len(over), 'over_raw', sum(r[1] for r in over), 'over_gzip', sum(r[2] for r in over))
print('near_count', len(near))

for label, collection in [('over', sorted(over, reverse=True)), ('near', sorted(near, reverse=True))]:
    print(label)
    for lines, raw, gz, path in collection:
        print(f'{path}\t{lines}\t{raw/1024:.1f} KiB\t{gz/1024:.1f} KiB')
PY
```

When updating this doc, classify each over-threshold file by role and record why it should be split or why it can stay large for the next implementation period.

## Related References

- [Studio](/docs/?scope=studio&doc=studio)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [JavaScript Payload And Runtime Cleanup Request](/docs/?scope=studio&doc=site-request-js-payload-runtime-cleanup)
- [JavaScript Payload And Runtime Cleanup Inventory](/docs/?scope=studio&doc=site-request-js-payload-runtime-cleanup-inventory)
