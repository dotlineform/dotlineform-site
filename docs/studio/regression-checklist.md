# Studio Regression Checklist

Use `Pass`, `Fail`, or `N/A` for each item.

## Test Environment

- Local server mode tested: `On` / `Off`
- Test date:
- Browser:
- Base Studio URL:
- Sample `series_id` used:
- Notes location for console output/screenshots:

## Series Tag Editor

Page: `studio/series-tag-editor/index.md`

- [ ] Load page with valid `?series=...`; works appear.
- [ ] Work search accepts exact `work_id`.
- [ ] Comma-separated work input adds multiple works.
- [ ] Selected work switching updates chip state correctly.
- [ ] Media preview updates when selected work changes.
- [ ] Adding a canonical tag works.
- [ ] Adding an alias-resolved tag works.
- [ ] Removing a work override tag works.
- [ ] `w_manual` cycle updates chip state and status text.
- [ ] Inherited vs override chips render correctly.
- [ ] Local-server save succeeds and status/result text is correct.
- [ ] Patch fallback modal opens when local server is unavailable.
- [ ] Patch modal JSON/snippet content looks correct.
- [ ] No console errors during load or save flow.

Notes:
- Issue:
- Steps:
- Screenshot/log:

## Tag Registry

Page: `assets/studio/js/tag-registry.js`

- [ ] Registry page loads without error.
- [ ] Search filters rows correctly.
- [ ] Group filter buttons work.
- [ ] Sort toggle works.
- [ ] New tag modal opens and validates correctly.
- [ ] Create tag succeeds in local-server mode.
- [ ] Edit modal opens with current tag data.
- [ ] Edit save succeeds in local-server mode.
- [ ] Delete modal opens with impact preview.
- [ ] Delete confirm succeeds in local-server mode.
- [ ] Demote modal opens and tag search works.
- [ ] Demote confirm succeeds in local-server mode.
- [ ] Import JSON succeeds in local-server mode.
- [ ] Patch fallback works for create.
- [ ] Patch fallback works for demote.
- [ ] Patch fallback works for import.
- [ ] No console errors during registry flows.

Notes:
- Issue:
- Steps:
- Screenshot/log:

## Tag Aliases

Page: `assets/studio/js/tag-aliases.js`

- [ ] Aliases page loads without error.
- [ ] Search filters rows correctly.
- [ ] Group filter buttons work.
- [ ] Sort toggle works.
- [ ] New alias modal opens and validates correctly.
- [ ] Create alias succeeds in local-server mode.
- [ ] Edit alias updates name/description/tags correctly.
- [ ] Delete alias succeeds in local-server mode.
- [ ] Promote alias preview appears correctly.
- [ ] Promote alias confirm succeeds in local-server mode.
- [ ] Demote-from-aliases prompt accepts valid target tags.
- [ ] Demote-from-aliases confirm succeeds in local-server mode.
- [ ] Import JSON succeeds in local-server mode.
- [ ] Patch fallback works for create/edit.
- [ ] Patch fallback works for delete.
- [ ] Patch fallback works for promote/demote.
- [ ] Patch fallback works for import.
- [ ] No console errors during alias flows.

Notes:
- Issue:
- Steps:
- Screenshot/log:

## Cross-check

- [ ] Save/import mode label switches correctly between `Local server` and `Patch`.
- [ ] Status/result copy is still coherent across pages.
- [ ] No unexpected layout regressions on desktop.
- [ ] No obvious mobile layout breakage on key Studio pages.
