---
doc_id: studio-ui-framework-review-coverage
title: Studio UI Framework Review And Coverage
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: archive
sort_order: 84000
---

This doc is deprecated. Please refer to [UI](/docs/?scope=studio&doc=ui) and [UI Catalogue](/docs/?scope=studio&doc=ui-catalogue).

---

# Studio UI Framework Review And Coverage

## What Stays Studio Page-Specific

These should remain page-specific unless another page genuinely needs the same structure:

- registry row/header layout
- alias row/header layout
- series tag editor suggestion content
- editor work selection layout
- page-specific action chip groupings

Do not move page-specific list structure into the shared layer just because two pages are both "lists". Share only the repeated UI primitives.

## Studio Review Rules

When adding or changing Studio UI:

1. Start by checking whether an existing shared primitive already matches the intent.
2. If not, add a new shared primitive only when the pattern is expected to be reused.
3. Do not reuse `tagRegistry__*` classes in aliases, or `tagAliases__*` classes in registry, for shared styling.
4. Keep layout-only exceptions local to the page namespace.
5. Keep UI copy in `assets/studio/data/studio_config.json`, not in CSS or hard-coded duplicated markup.

## Current Studio Shared Coverage

Current Studio cleanup standardizes:

- list-page toolbar/import blocks on `tagStudioToolbar__*`
- list-page search/filter controls on `tagStudioFilters__*`
- shared lists on `tagStudioList__*`
- modal form internals on `tagStudioForm__*`
- lighter pages bind through `data-role` and `data-state` instead of style-class behavior hooks where they expose interactive controls

### Implementation Boundary

The same rule used for modal refactoring applies here:

- shared Studio UI modules and CSS own the shell and styling contract
- page controllers own rendering decisions and event wiring
- domain/service modules own validation, filtering rules, and mutation behavior

Shared styling should not be implemented by borrowing another page's class names. If two pages use the same UI intent, the primitive belongs in the shared `tagStudio*` layer.
