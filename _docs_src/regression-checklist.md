---
doc_id: regression-checklist
title: "Studio Regression Checklist"
last_updated: 2026-03-28
parent_id: _archive
sort_order: 80
published: false
---

# Studio Regression Checklist

Use `Pass`, `Fail`, or `N/A` for each item.

## Test Environment

- Local server mode tested: `On` / `Off`
- Test date:
- Browser:
- Base Studio URL:
- Sample `series_id` used:
- Notes location for console output/screenshots:
- [ ] Shared site header renders on Studio pages and Studio docs with the Studio link set (`studio`, `series tags`, `docs`).

## Series Tag Editor

Page: `studio/series-tag-editor/index.md`

- [ ] Load page with valid `?series=...`; works appear.
- [ ] Work search accepts exact `work_id`.
- [ ] Comma-separated work input adds multiple works.
- [ ] Selected work switching updates chip state correctly.
- [ ] Media preview updates when selected work changes.
- [ ] With no work selected, tag input remains enabled for series-tag editing.
- [ ] Adding a series tag works.
- [ ] Removing a series tag works.
- [ ] Cycling `w_manual` on a series tag works.
- [ ] Adding a canonical tag works.
- [ ] Adding an alias-resolved tag works.
- [ ] Removing a work override tag works.
- [ ] `w_manual` cycle updates chip state and status text.
- [ ] Inherited vs override chips render correctly.
- [ ] Local-server save succeeds and status/result text is correct.
- [ ] Patch fallback modal opens when local server is unavailable.
- [ ] Patch modal JSON/snippet content looks correct.
- [ ] Save/patch modal title, body spacing, and action row match the shared Studio modal shell.
- [ ] Save/patch modal backdrop and dialog surface render correctly with no transparency issues.
- [ ] No console errors during load or save flow.

Notes:
- Issue:
- Steps:
- Screenshot/log:

## Tag Registry

Page: `studio/tag-registry/index.md`

- [ ] Registry page loads without error.
- [ ] Registry shell layout renders correctly on desktop/mobile.
- [ ] Search filters rows correctly.
- [ ] Group filter buttons work.
- [ ] Sort toggle works.
- [ ] New tag modal opens and validates correctly.
- [ ] Create tag succeeds in local-server mode.
- [ ] Edit modal opens with current tag data.
- [ ] Edit save succeeds in local-server mode.
- [ ] Delete modal opens with impact preview.
- [ ] Delete modal shows the selected tag as a coloured group pill with the correct `tag_id`.
- [ ] Delete impact preview enumerates assignments/aliases as structured counts.
- [ ] Delete confirm succeeds in local-server mode.
- [ ] Demote modal opens and tag search works.
- [ ] Demote confirm succeeds in local-server mode.
- [ ] Import JSON succeeds in local-server mode.
- [ ] New tag modal uses shared shell spacing, labels, and action row layout.
- [ ] Edit tag modal uses shared shell spacing, labels, and action row layout.
- [ ] Delete tag modal uses shared shell spacing, impact text placement, and action row layout.
- [ ] Demote confirmation modal uses shared `confirm-detail` shell and renders inside the page styling context.
- [ ] Patch preview modal uses shared shell spacing and action row layout.
- [ ] Patch fallback works for create.
- [ ] Patch fallback works for demote.
- [ ] Patch fallback works for import.
- [ ] No console errors during registry flows.

Notes:
- Issue:
- Steps:
- Screenshot/log:

## Tag Aliases

Page: `studio/tag-aliases/index.md`

- [ ] Aliases page loads without error.
- [ ] Aliases shell layout renders correctly on desktop/mobile.
- [ ] Search filters rows correctly.
- [ ] Group filter buttons work.
- [ ] Sort toggle works.
- [ ] New alias modal opens and validates correctly.
- [ ] Create alias succeeds in local-server mode.
- [ ] Edit alias updates name/description/tags correctly.
- [ ] Delete alias succeeds in local-server mode.
- [ ] Promote alias preview appears correctly.
- [ ] Promote alias confirm succeeds in local-server mode.
- [ ] Demote-from-aliases form accepts valid target tags.
- [ ] Demote-from-aliases confirm succeeds in local-server mode.
- [ ] Import JSON succeeds in local-server mode.
- [ ] New/edit alias modal uses shared shell spacing, labels, and action row layout.
- [ ] Delete alias confirmation uses shared `confirm` shell and renders inside the page styling context.
- [ ] Promote alias form and confirm-detail modals use shared shell spacing and warning/status placement.
- [ ] Demote-from-aliases form and confirm-detail modals use shared shell spacing and warning/status placement.
- [ ] Patch preview modal uses shared shell spacing and action row layout.
- [ ] Patch fallback works for create/edit.
- [ ] Patch fallback works for delete.
- [ ] Patch fallback works for promote/demote.
- [ ] Patch fallback works for import.
- [ ] No console errors during alias flows.

Notes:
- Issue:
- Steps:
- Screenshot/log:

## Series Tags

Page: `studio/series-tags/index.md`

- [ ] Series Tags page loads without error.
- [ ] Group filter buttons work.
- [ ] Active filter styling is correct.
- [ ] Default sort is by series.
- [ ] Clicking each column header toggles sort order.
- [ ] Active sort styling is correct.
- [ ] Tags sort behaves consistently with the visible tag list.
- [ ] Series links point to the Series Tag Editor.
- [ ] RAG dots and visible tag chips render correctly.
- [ ] No console errors during series-tags flow.

## Tag Groups

Page: `studio/tag-groups/index.md`

- [ ] Tag Groups page loads without error.
- [ ] Group sections render in configured order.
- [ ] Group chips and description text render correctly.
- [ ] No console errors during tag-groups load.

## Studio Works

Page: `studio/studio-works/index.md`

- [ ] Studio Works page loads without error.
- [ ] Sort buttons work.
- [ ] Active sort styling is correct.
- [ ] Single-series filtered view still works.
- [ ] No console errors during studio-works flow.

## Cross-check

- [ ] Save/import mode label switches correctly between `Local server` and `Patch`.
- [ ] Status/result copy is still coherent across pages.
- [ ] No unexpected layout regressions on desktop.
- [ ] No obvious mobile layout breakage on key Studio pages.

## Modal Cross-check

- [ ] Modal backdrops, dialog surfaces, and title spacing look consistent across editor, registry, and aliases.
- [ ] Modal action rows use consistent button ordering and spacing across modal types.
- [ ] Form modals place labels, warnings, and status text consistently.
- [ ] Confirm and confirm-detail modals use the shared shell instead of native browser dialogs.
- [ ] Patch-preview modals present read-only output consistently across pages.
