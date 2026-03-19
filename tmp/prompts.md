1. **Findings: how navigation currently works on each page type**

Work image pages:
- The main image viewer is the anchor [`_layouts/work.html#L77`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work.html#L77) through [`_layouts/work.html#L103`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work.html#L103), with `#workMediaLink` wrapping the image.
- The visible prev/next controls are `#seriesNavPrev` and `#seriesNavNext` in [`_layouts/work.html#L119`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work.html#L119) through [`_layouts/work.html#L128`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work.html#L128).
- Their URLs are generated in [`assets/js/work.js#L49`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/js/work.js#L49) through [`assets/js/work.js#L71`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/js/work.js#L71) from `series_index.json` and the current `?series=` / `?series_page=` query. This logic wraps at the ends via modulo.
- If there is no valid series context or fewer than 2 works, the nav is hidden in [`assets/js/work.js#L52`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/js/work.js#L52) through [`assets/js/work.js#L55`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/js/work.js#L55).

Detail image pages:
- The main image viewer is `#detailMediaLink` in [`_layouts/work_details.html#L58`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work_details.html#L58) through [`_layouts/work_details.html#L86`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work_details.html#L86).
- The prev/next controls are `#detailNavPrev` and `#detailNavNext` in [`_layouts/work_details.html#L95`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work_details.html#L95) through [`_layouts/work_details.html#L106`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work_details.html#L106).
- Their URLs are built by `buildDetailHref()` and assigned in `setNavFromWorkPayload()` at [`_layouts/work_details.html#L247`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work_details.html#L247) through [`_layouts/work_details.html#L320`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work_details.html#L320).
- That logic reuses the current work/detail/series query context and also wraps at the ends.

Paginated thumbnail grid pages:
- There are two existing paginated thumbnail grids.
- Series pages use `#seriesGrid` plus `#seriesGridPrev` / `#seriesGridNext` in [`_layouts/series.html#L33`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/series.html#L33) through [`_layouts/series.html#L44`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/series.html#L44). Pagination is runtime state in [`_layouts/series.html#L139`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/series.html#L139) through [`_layouts/series.html#L193`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/series.html#L193), with `updateUrl()` preserving the `series_page` query in the address bar. Prev/next wrap.
- Work pages also render paginated detail thumbnail grids per section in [`_layouts/work.html#L564`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work.html#L564) through [`_layouts/work.html#L606`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work.html#L606). The pager uses `[data-pager-key]` and `[data-pager-delta]`, and clicks are handled in [`_layouts/work.html#L645`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work.html#L645) through [`_layouts/work.html#L658`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work.html#L658). This also wraps.
- There is no separate paginated thumbnail grid on detail pages.

Pointer/touch/library audit:
- I did not find any existing swipe logic, Touch Events, or Pointer Events in the relevant work/detail/grid code.
- I did not find any gallery, zoom, lightbox, pinch, or pan library for these pages. The top image is just an anchor-wrapped `<img>`.
- There is one unrelated global menu closer in [`_layouts/default.html#L177`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/default.html#L177) through [`_layouts/default.html#L180`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/default.html#L180) using `pointerdown` and `touchstart`, but it does not prevent default and should not conflict.
- There is currently no `touch-action` rule for these zones in [`assets/css/main.css#L951`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/css/main.css#L951) through [`assets/css/main.css#L1154`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/css/main.css#L951).

Stable hooks already present:
- Work image zone: `#workMediaLink`
- Work prev/next: `#seriesNavPrev`, `#seriesNavNext`
- Detail image zone: `#detailMediaLink`
- Detail prev/next: `#detailNavPrev`, `#detailNavNext`
- Series grid zone: `#seriesGrid`
- Series grid prev/next buttons: `#seriesGridPrev`, `#seriesGridNext`
- Work detail grid pager buttons: `[data-pager-key]` and `[data-pager-delta]`

Stable hooks likely worth adding:
- One non-presentational hook for the work-page detail grid swipe start region, because today the actual grid region is only exposed as `.seriesGrid` inside generated HTML.

2. **Proposed integration design**

- Add one small shared module, `assets/js/swipe-nav.js`, built around Pointer Events.
- The module should be generic enough to support both:
  - link-based navigation for work/detail image pages
  - action/button-based pagination for grid pages
- It should not invent URLs. For image pages it will resolve the existing prev/next anchors and navigate to their `href`. For grid pages it will invoke the existing prev/next button logic, so the current render/updateUrl behavior remains the single source of truth.
- Activation should be limited to the actual swipe zones:
  - work image: `#workMediaLink`
  - detail image: `#detailMediaLink`
  - series grid: `#seriesGrid`
  - work detail grids: each detail-group grid region only
- Gesture rules:
  - only track `pointerType === "touch"` or `"pen"`
  - ignore mouse
  - ignore multi-touch
  - cancel on `pointercancel`
  - require a clear horizontal threshold
  - require low vertical drift
  - require horizontal dominance over vertical movement
  - enforce a max duration so slow drags do not count
  - suppress the follow-up click after a successful swipe so image-link taps still work normally
- `touch-action: pan-y` should be applied only to the swipe zones, not globally.

3. **File-by-file implementation plan**

[`assets/js/swipe-nav.js`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/js/swipe-nav.js)
- New shared module.
- Provide a small `initSwipeNav(...)` API or equivalent internal bootstrap.
- Support two navigation modes:
  - anchor mode: resolve prev/next anchors and navigate with `window.location.href`
  - action mode: resolve prev/next buttons and trigger their existing click handlers
- Handle thresholds, multi-touch rejection, click suppression, and pointer cleanup.

[`_layouts/work.html`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work.html)
- Add a stable swipe-zone hook to `#workMediaLink`.
- Add a stable swipe-start hook to the rendered detail grid container.
- Include the new JS module.
- Initialize swipe for each work-detail group using the existing group element ref and existing pager buttons, so the swipe path reuses `[data-pager-key]` behavior rather than duplicating pagination logic.

[`_layouts/work_details.html`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/work_details.html)
- Add a stable swipe-zone hook to `#detailMediaLink`.
- Include the new JS module.
- Reuse the same image-swipe initializer used by work pages.

[`_layouts/series.html`](/Users/dlf/Developer/dotlineform/dotlineform-site/_layouts/series.html)
- Add a stable swipe-zone hook to `#seriesGrid`.
- Include the new JS module.
- Bind swipe to the existing `#seriesGridPrev` / `#seriesGridNext` buttons so pagination still runs through current render state and `updateUrl()`.

[`assets/css/main.css`](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/css/main.css)
- Add a narrowly scoped `touch-action: pan-y` rule for the explicit swipe-zone hook only.

4. **Any risks / edge cases**

- The top image is also a link to the full-size image. Swipe handling must suppress the resulting click after a successful swipe, or users will trigger both behaviors.
- Work/detail nav is contextual. If the page lacks valid prev/next links, swipe must no-op rather than infer anything.
- Current behavior wraps at the ends on all three navigation systems. Swipe should preserve that exact behavior because it will call the same anchors/buttons already doing it.
- Work-detail grids are re-rendered with `innerHTML`, so the swipe binding should attach to a stable parent/group ref or be re-applied after render. I would bind against the stable group element and restrict gesture start to the grid region.
- Starting a gesture on a vertical scroll should continue to scroll normally. `pan-y` plus conservative thresholds should keep this intact.
- Multi-touch must cancel tracking so pinch/browser gestures do not navigate.

5. **Then implement**

I have not edited yet. [`AGENTS.md`](/Users/dlf/Developer/dotlineform/dotlineform-site/AGENTS.md) requires confirmation before code changes.

If you confirm this plan, I’ll implement it with the narrow file set above and then run targeted verification.