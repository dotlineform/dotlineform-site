---
doc_id: design-backlog
title: Design Backlog
last_updated: 2026-03-31
parent_id: ""
sort_order: 60
published: false
---

# Design Backlog

This document holds the main design and UI follow-up work for the site.

Keep current implementation rules in:

- `_docs_src/design/ui-framework.md`
- `_docs_src/design/studio-ui-framework.md`
- `_docs_src/design/css-primitives.md`

Use this document for deferred refinement work so `_docs_src/_dev/backlog.md` can stay focused on repo-level tasks.

## Audit And Review Tooling

- Extend `scripts/css_token_audit.py` beyond token checks into selector and declaration duplication reporting.
- When a new shared pattern lands in code, update the current-state design docs in the same change rather than leaving the new pattern described only here.

## Shared Studio Primitives

- Standardize the active selected-state treatment for Studio group and filter pills so selection stays distinct without thicker borders, rings, or shadows.
- Standardize the baseline Studio pill treatment so tag, key, popup, selected-work, and group-name pills share the same height and `--font-small` type scale.
- Standardize the shared Studio action-button treatment so page actions and modal actions use one baseline height, type scale, padding, and visual weight.
- Standardize the shared Studio text-input treatment, including search fields, so they read as one control family rather than page-specific variants.
- Standardize the shared Studio info-button treatment so the `i` button stays circular and vertically aligned wherever it appears.
- Standardize the shared Studio message and result container pattern so status, warning, and outcome text use one consistent layout across pages and modals.

## Shared Studio Shells

- Standardize the shared Studio list-shell treatment using `studio/tag-registry/` as the baseline for row spacing, header spacing, alignment, and surface treatment.
- Move `studio/series-tags/` group filters above the list, matching the shared filter-row pattern, and give the tags column an explicit `tags` header.
- Add sortable column headers to `studio/series-tags/`, keeping the current filter behavior while aligning header state and ARIA treatment with other sortable Studio lists.

## Cross-Surface Presentation

- Standardize work and series metadata presentation around one unboxed metadata pattern, using public work pages as the visual baseline and applying the same presentation to related Studio surfaces.
- Treat tag-group names as colored pills wherever they are shown rather than allowing plain-text group labels to persist on some pages.
- Review remaining repeated site and Studio list or layout variants and consolidate them where the UI intent is already shared.
- Review cross-page spacing and shared link-state styling so the broader site feels more consistent without forcing unnecessary redesign.

## Structural Redesigns

- Give Studio its own navigation model rather than reusing the public site header navigation.
- Redesign the `Delete Tag` modal as its own pass rather than treating it as solved by the shared message-container cleanup.

## Maintenance Notes

- Keep one backlog item per pattern, not per selector.
- Split behaviour changes from presentation changes when they do not need to ship together.
- Update the relevant current-state docs when a design task lands, especially:
  - `_docs_src/design/studio-ui-framework.md`
  - `_docs_src/design/ui-framework.md`
  - `_docs_src/design/css-primitives.md`
  - the affected Studio page docs in `_docs_src/studio/`
