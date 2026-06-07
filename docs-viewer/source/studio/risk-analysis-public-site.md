---
doc_id: risk-analysis-public-site
title: Risk Analysis - Public Site
added_date: 2026-06-07
last_updated: 2026-06-07
parent_id: admin
---
# Risk Analysis - Public Site

This describes risk evidence for the public site as a user-facing catalogue of artwork and text hosted on GitHub Pages.

Policy: [Studio Risk Analysis Policy](/docs/?scope=studio&doc=studio-risk-analysis-policy).

## Priority Order

1. Performance / cost
2. Architectural fit
3. Structural
4. Workflow

## Risk Analysis

| Area | Indicator | Evidence | Current action |
| --- | --- | --- | --- |
| Public route and media payloads | Performance / cost | Public pages are media-heavy and user-facing, so route payload, image derivation, and runtime responsiveness are more important here than in local-only tools. [Javascript Inventory](/docs/?scope=studio&doc=javascript-inventory) keeps public runtime rows for `assets/js/catalogue-search.js`, `assets/js/work.js`, `assets/js/moment.js`, and shared public catalogue helpers. | Use this inventory to collect public-route performance evidence before opening optimisation work. |
| Public catalogue search runtime | Structural | The old JavaScript inventory identifies `assets/js/catalogue-search.js` as the only public-runtime row above target score 4 after query normalization, ordering, HTML projection, and metric view-model work moved into `assets/js/search/catalogue-search-runtime.js`. | Keep future public search behavior in the focused runtime/helper split; open a public-site optimisation request only after route-cost evidence shows user-visible impact. |
| Jekyll/public-build boundary | Architectural fit | Jekyll remains the public preview/build layer, while app-facing runtimes now use Python and JavaScript for docs/search generation, catalogue search, and catalogue prose rendering. Ruby/Bundler/Jekyll risk belongs here when it affects public preview/build parity rather than local app behavior. | Keep public-site verification separate from app-generation checks; use `bin/public-site-preview` or `bin/public-site-build` for this layer. |
| Catalogue taxonomy | Structural | Catalogue structure is complex but relatively stable, with modest record growth. | Treat taxonomy changes as deliberate app-level changes rather than opportunistic refactors. |
