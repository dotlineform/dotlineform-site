Use the 5-pass plan, but treat it as 7 commit points so you always have a clean rollback/test boundary.

**Pass 1**
Framework and rules.
- Add `studio-ui.js`.
- Document the contract in [ui-framework.md](/Users/dlf/Developer/dotlineform/dotlineform-site/docs/studio/ui-framework.md).
- No page behavior changes yet.

Best commit point:
- `studio: add UI contract and role/state conventions`

Good time to test:
- Minimal. Mostly a no-regression smoke check.

**Pass 2**
`series-tag-editor` page shell.
- Move the four major editor containers into [index.md](/Users/dlf/Developer/dotlineform/dotlineform-site/studio/series-tag-editor/index.md).
- Add `data-role` hooks for the page shell.
- Keep behavior unchanged where possible.

Best commit point:
- `studio: move series tag editor shell markup into template`

Good time to test:
- Layout only. Check desktop/mobile placement and container styling freedom.

**Pass 3**
`tag-studio.js` behavior split.
- Make [tag-studio.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/tag-studio.js) bind to template containers by `data-role`.
- Reduce JS-generated shell markup to dynamic inner fragments only.
- Replace style-class querying/toggling with `data-role`, `aria-*`, or `data-state`.

Best commit point:
- `studio: decouple tag studio behavior from style classes`

Good time to test:
- High value checkpoint. This is the first full interactive validation point for the editor.

**Pass 4**
`tag-registry` shell and behavior.
- Move major containers into template markup.
- Apply the same `studio-ui.js` conventions.
- Remove class-based behavior hooks.

Best commit point:
- `studio: refactor tag registry shell and behavior hooks`

Good time to test:
- Registry flows only.

**Pass 5**
`tag-aliases` shell and behavior.
- Same treatment as registry.
- Centralize remaining generated style class tokens.

Best commit point:
- `studio: refactor tag aliases shell and behavior hooks`

Good time to test:
- Alias create/edit/import flows.

**Pass 6**
Lighter pages.
- [studio-works.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/studio-works.js)
- [series-tags.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/series-tags.js)
- [tag-groups.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/tag-groups.js)

Best commit point:
- `studio: align lighter studio pages with UI role contract`

Good time to test:
- Sorting/filtering, list rendering, static page shells.

**Pass 7**
Cleanup and docs.
- Consolidate CSS patterns in [studio.css](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/css/studio.css).
- Update page docs and regression notes.
- Remove leftover mixed patterns.

Best commit point:
- `studio: document and clean up shared UI patterns`

Good time to test:
- Final cross-page sweep.

Practical staging advice:
- Stage by page or feature, not by file type.
- Don’t combine “template shell move” and “behavior rewrite” in one commit if you can avoid it.
- The strongest test boundaries are after Pass 3, Pass 5, and Pass 6.

Recommended order to start:
1. Pass 1
2. Pass 2
3. Test locally
4. Pass 3
5. Test locally

If you want, I’ll start with Pass 1 plus Pass 2 only.

----------------------

update following cache issue and commit 'refactor studio tag editor UI...':

Pass 1: effectively complete.

Evidence:
- [studio-ui.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/studio-ui.js) exists and defines the shared role/class/state contract.
- [ui-framework.md](/Users/dlf/Developer/dotlineform/dotlineform-site/docs/studio/ui-framework.md) now documents the contract boundary and rules.

Caveat:
- It was not preserved as a pure “framework only, no behavior change yet” checkpoint. The current branch includes later behavior changes, so Pass 1 is complete in outcome, not as an isolated commit boundary.

Pass 2: complete in outcome.

Evidence:
- [index.md](/Users/dlf/Developer/dotlineform/dotlineform-site/studio/series-tag-editor/index.md) now owns the four major shell sections:
  - work section
  - message section
  - groups section
  - search section
- Those sections have `data-role` hooks.
- [tag-studio.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/tag-studio.js) now binds to those template containers rather than generating the full shell.

Caveat:
- Again, this was not preserved as a “shell move only” checkpoint. The current code also includes behavior changes and new series-tag save behavior.

Pass 3: mostly already done.

Evidence:
- `tag-studio.js` now queries by `UI_SELECTOR.*` and `data-role`, not styling classes.
- status and save-result state now use `data-state` rather than `.is-*` classes.
- selected work active state uses `data-state`.
- JS-generated shell markup has been reduced to dynamic fragments, while the template owns the major layout containers.

What is still incomplete or worth tightening before calling Pass 3 finished:
- [tag-studio.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/tag-studio.js#L228) has `syncStateFromAssignments(...)`, which now appears unused after the cache isolation change.
- There is still one literal selector in the modal close handler, `closest('[data-role="close-modal"]')`, instead of routing that through the shared contract. Small issue, but it breaks the “one source of truth” discipline.
- `renderFatalError(...)` still replaces the mount’s full HTML. That may be acceptable, but it bypasses the template-owned shell model.
- The current Pass 3 state is mixed with feature expansion: series-tag editing/saving and cache fixes. So the decoupling is there, but the checkpoint is noisy.

Best way to approach “Phase 3” now:
Don’t treat it as a big rewrite anymore. Treat it as a stabilization/cleanup pass for the tag editor.

Recommended scope:
1. Finish the contract cleanup in `tag-studio.js`.
2. Remove dead or superseded code introduced during the save/cache debugging.
3. Do a focused interactive validation pass for the editor.
4. Only after that, move to registry/aliases.

Concretely, I’d define the remaining Pass 3 work as:
- remove unused helpers left behind by the earlier save strategy
- make any remaining role selectors come from `studio-ui.js`
- decide whether fatal error rendering should preserve the template shell or intentionally replace it
- run the high-value interactive checks the original plan called for

Manual checks for this Pass 3 closeout:
- desktop/mobile shell still lays out correctly
- no selected work: add/remove/cycle series tags
- selected work: add/remove/cycle work overrides
- inherited tags stay non-editable in work scope
- save success leaves UI stable
- reload still reflects persisted assignments
- patch mode still renders valid payload/snippet

My assessment:
- Pass 1: yes
- Pass 2: yes
- Pass 3: about 85-90% already done, but not cleanly closed

So the best next move is not “start Pass 3”, it is “finish and harden Pass 3, then move to Pass 4”. If you want, I can turn that into a minimal cleanup checklist against the current files before any more code changes.

----------------

Use this as the Pass 3 closeout checklist.

Code cleanup:
- Remove `syncStateFromAssignments(...)` from [tag-studio.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/tag-studio.js) if it is now unused.
- Move the modal close role into [studio-ui.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/studio-ui.js) so `tag-studio.js` stops using the literal selector `"[data-role=\"close-modal\"]"`.
- Review `renderFatalError(...)` in [tag-studio.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/tag-studio.js) and decide whether replacing the whole mount is acceptable or whether the error should render inside the template shell.
- Check [studio_config.json](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/data/studio_config.json) for any copy added during the series-save work that should be split from pure UI-contract changes later.

Behavior verification:
- No selected work: add series tag, remove series tag, cycle `w_manual`, save.
- Selected work: add override, remove override, cycle `w_manual`, save.
- Confirm inherited series tags are not editable when a work is active.
- Confirm save leaves the editor stable and does not snap back.
- Reload and confirm persisted tags still match `tag_assignments.json`.
- Force patch mode and confirm the modal payload/snippet still makes sense for both series and work changes.

Docs/checkpoint:
- Treat Pass 3 as complete once [tag-studio.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/tag-studio.js), [studio-ui.js](/Users/dlf/Developer/dotlineform/dotlineform-site/assets/studio/js/studio-ui.js), [docs/studio/pages/tag-editor.md](/Users/dlf/Developer/dotlineform/dotlineform-site/docs/studio/pages/tag-editor.md), and [docs/studio/regression-checklist.md](/Users/dlf/Developer/dotlineform/dotlineform-site/docs/studio/regression-checklist.md) all agree on the boundary.
- Then move to Pass 4: registry shell and behavior hooks.

If you want, I can review the current code against just that cleanup scope before any more edits.

