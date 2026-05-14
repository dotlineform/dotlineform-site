---
doc_id: studio-javascript-payload-inventory
title: Studio JavaScript Payload Inventory
added_date: 2026-05-14
last_updated: 2026-05-14
ui_status: urgent
parent_id: studio
sort_order: 55
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

Measured on 2026-05-14.

- Browser JavaScript files under `assets/`: 98
- Total browser JavaScript lines under `assets/`: 35,492
- Files over the 1,000-line review threshold: 6
- Files in the 900-1,000 line watch band: 5
- Over-threshold raw size total: 352.3 KiB
- Over-threshold gzip size total: 68.1 KiB

The over-threshold set is still maintenance-driven more than transfer-driven.
No route loads all over-threshold files together.

## Current Inventory

| File | Lines | Raw | Gzip | Classification | Maintenance risk | Transfer-size risk | Notes |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `assets/docs-viewer/js/docs-viewer-management.js` | 1,892 | 69.5 KiB | 11.8 KiB | mixed Docs Viewer management controller | high | low | Dynamically loaded only for management mode. Management markup helpers for status pills, metadata parent/status controls, and settings warnings now live in `assets/docs-viewer/js/docs-viewer-management-render.js`. The controller still owns metadata modal, settings modal, import modal boot, drag/drop, context menu, and write orchestration. Next cleanup should split modal view-models or write-action orchestration behind management-only helpers. |
| `assets/studio/js/tag-studio.js` | 1,886 | 63.2 KiB | 13.0 KiB | mixed route controller | high | low | Continue the Tag Editor split by moving render groups, popup behavior, and modal/save orchestration behind route-local helpers. |
| `assets/studio/js/tag-aliases.js` | 1,708 | 62.3 KiB | 11.2 KiB | mixed route controller | high | low | Existing domain/save/service split is useful but incomplete. Next cleanup should target modal view-models and list rendering before more alias workflow is added. |
| `assets/docs-viewer/js/docs-viewer.js` | 1,673 | 55.5 KiB | 11.6 KiB | mixed shared viewer runtime controller | high | medium | Still the top cleanup target for read-only route payload. Bookmark state, storage, rendering, and events now live in `assets/docs-viewer/js/docs-viewer-bookmarks.js`; sidebar/nav/meta rendering and trail display now live in `assets/docs-viewer/js/docs-viewer-sidebar.js`; result-row and bookmark-row markup helpers live in `assets/docs-viewer/js/docs-viewer-render.js`; status-pill markup and events stay behind the lazy management-controller boundary. The entry controller still owns route state, content loading, search orchestration, reports entry, and management dynamic-loading. |
| `assets/studio/js/tag-registry.js` | 1,625 | 58.3 KiB | 11.1 KiB | mixed route controller | high | low | Existing domain/save/service split is useful but incomplete. Next cleanup should target modal view-models, delete-impact rendering, and import-result rendering. |
| `assets/studio/js/data-sharing-review.js` | 1,163 | 43.4 KiB | 9.3 KiB | mixed route controller | medium | low | Newly over threshold relative to the older inventory. It owns staged package listing, preview rendering, apply confirmation, result rendering, and workflow-scope state. Split preview/result rendering or apply-action orchestration if it grows further. |

## Watch Band

These files are below the 1,000-line review threshold but close enough to watch during future feature work.

| File | Lines | Raw | Gzip | Notes |
| --- | ---: | ---: | ---: | --- |
| `assets/studio/js/catalogue-work-editor.js` | 992 | 36.0 KiB | 7.2 KiB | Accepted as a route coordinator after work editor extraction. Avoid adding new rendering or mutation clusters here. |
| `assets/docs-viewer/js/docs-html-import.js` | 985 | 36.9 KiB | 7.9 KiB | Close to threshold. Future import UI additions should prefer helper modules for result rendering or source-format-specific UI. |
| `assets/studio/js/data-sharing-prepare.js` | 945 | 34.6 KiB | 7.8 KiB | Still under threshold. Watch if more package profile or result modal behavior is added. |
| `assets/studio/js/series-tags.js` | 942 | 34.9 KiB | 7.7 KiB | Under threshold but still a route controller. Split rendering helpers if the series tag workflow expands. |
| `assets/studio/js/catalogue-work-actions.js` | 913 | 38.5 KiB | 6.3 KiB | Under threshold and route-local. Keep it action-workflow focused rather than adding form or section rendering. |

## Current Priority

1. `assets/docs-viewer/js/docs-viewer.js`
2. `assets/docs-viewer/js/docs-viewer-management.js`
3. `assets/studio/js/tag-studio.js`
4. `assets/studio/js/tag-aliases.js` and `assets/studio/js/tag-registry.js`
5. `assets/studio/js/data-sharing-review.js`

The first two are Docs Viewer files, but they are included here because `/docs/` is the Studio documentation and management surface.

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
