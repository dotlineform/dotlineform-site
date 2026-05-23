---
doc_id: "_tmp"
title: tmp
added_date: 2026-05-20
last_updated: "2026-05-20 19:37"
parent_id: ""
sort_order: 40000
viewable: false
---
# tmp

we are working on _docs/local-studio-app-implementation-plan.md
please continue with the next suitable slice.

---

normal development should use:

- `bin/local-studio` for Studio
- `bin/public-site-preview` for public Jekyll preview
- `bin/public-site-build` for public Jekyll build


---

Reviewed `_docs/local-studio-app-implementation-plan.md`. Remaining work is:

**Next Slices**
1. Finish any remaining public-site link resolver adoption when migrated routes are touched.
2. Continue service consolidation, especially remaining catalogue write-handler extraction.
3. Start Phase 6 projection/build contract work.
4. Defer repo split decision until the publish/export contract is stable.

**Phase 4: Local Service Consolidation**
- Continue moving endpoint ownership into the Python app server.
- Keep expanding focused route/API modules for catalogue and shared Studio routes.
- Finish replacing in-process `catalogue_write_server.Handler` bridge in `studio_catalogue_api.py`.
- Current catalogue extraction order in the plan:
  - moment save
  - publication preview/apply
  - delete apply
  - bulk save
  - remove fake handler bridge
- Keep reducing `bin/dev-studio` to only genuinely required background tasks.
- Finish compatibility docs cleanup around old sibling-service startup.

**Transition Cleanup Backlog**
- Retire remaining migrated Jekyll Studio route files or add intentional transition redirects.
- Finish compatibility docs that still imply old sibling services are normal.
- Finish extracting remaining catalogue write behavior out of the standalone HTTP handler.

---

**Phase 5: Route Family Migration**
- Catalogue editors/dashboards remain partial, though many shells are already local-hosted.
- Analytics/tag routes remain partial, though dashboard/tag groups/registry/aliases/series-tags/per-series editor are local-hosted.
- Broader public-link resolver adoption remains partial, mainly “adopt when touched.”
- Shared route URL builder adoption remains partial.
- Jekyll route retirement remains partial.
- Decide whether temporary redirects are useful for local transition ergonomics.

Bullet check:
Catalogue editors/dashboards: done for the current Phase 5 scope. Local app config includes catalogue dashboard, Bulk Add, Activity, Field Registry, Drafts, Studio Works, and all four catalogue editors in studio_app_config.py (line 13).
Analytics/tag routes: done for the current Phase 5 scope. Analytics dashboard plus tag groups, registry, aliases, series-tags, and per-series editor are all in local app config.
Public-link resolver: done for currently migrated route surfaces after the slice we just landed. Future route families still need to use the helper if they add public links.
Shared route URL builder: done for the important migrated record-param links (work=, detail=, series=, moment=). There are still static route strings for fixed dashboard/nav links and route-context labels, which is fine. If the plan meant “all Studio links must use a builder,” then it is still partial, but that would be broader than the original risk.
Jekyll route retirement: done for operational Studio routes. studio/ now only has UI Catalogue demo material left, which docs describe as isolated demo/reference pages, not migrated Studio workflow routes.
Temporary redirects: no evidence that redirects are needed or implemented. This should be closed as “not useful for now” rather than left pending.
So I’d mark Phase 5 as complete for current operational route-family migration, with a caveat that future route families must follow the same resolver/builder conventions. The next cleanup would be a docs-only/status update: change the stale Phase 5 table entries and explicitly record “no temporary redirects for now.”

---

**Phase 6: Projection And Build Contract**
All still pending:
- Document canonical source families and public projections.
- Distinguish public projections, Studio projections, and Docs Viewer payloads.
- Add checks for source-only fields leaking into public projections.
- Verify Jekyll consumes public projections rather than Studio-only data.
- Keep generated output paths explicit.

**Phase 7: Optional Repo Split Decision**
All still pending:
- Review ownership of public site, Studio app, canonical data, Docs Viewer, and generated outputs.
- Decide one repo vs split public-site/Studio repos vs Docs Viewer extraction.
- Identify concrete operational benefits required to justify a split.
- Define publish/export contract before moving files.

Phases 0, 1, 1A, 2, and 3 are complete. Phase 4 and 5 are the active implementation areas; Phase 6 is the next strategic boundary work.

---

<https://developers.openai.com/codex/migrate?utm_campaign=ML_MIX_GWT_AW_codexnewsletter_OF_EX_MAY_18&utm_content=utm_content&utm_medium=email&utm_source=sendgrid&utm_term=utm_term>

<https://developers.openai.com/codex/skills>

---

'I’m adding this as a plain ES module, not a route framework.' - why, whats the difference?

A plain ES module here means: a small browser file that exports functions like buildStudioViewUrl() / navigateTo() and can enhance links marked with data-studio-navigate.

A route framework would mean the app has a central router that owns more of the application lifecycle: matching URLs, rendering views into an outlet, preserving/replacing history state, loading/unloading page modules, handling params, redirects, guards, and usually becoming the place every view has to integrate with.

Why I’m avoiding a route framework right now:

We want to preserve current Studio behavior and modules, not turn this into a SPA rewrite.
The Studio user does not care whether navigation changes routes or swaps panels, but the existing modules still assume page-level boot in several places.
Real hrefs are useful during migration: links still work without JS enhancement, and each page can still be smoke-tested directly.
A small ES module gives us a stable view-id API now without forcing a decision about whether the final Studio app is multi-page, mostly single-page, or mixed.
It keeps complexity proportional to the current slice: Tag Groups only needs “view id -> URL”, not route guards, nested routes, history restoration, or lifecycle orchestration.
So the distinction is ownership. The ES module is a helper. A router/framework becomes the app’s navigation and rendering authority. I think the helper is the right intermediate step because it creates the migration contract without prematurely changing the app model.

---

I’m going to make the local server render the existing Docs Viewer include through a small server-side adapter. That avoids copying the whole shell into Python and keeps the local mount tracking the shared Docs Viewer markup while we still retire Jekyll as the route host.

---

I added a local /docs/ mount to studio_app_server.py It hosts the existing Docs Viewer management shell through the Python Studio app server, using the shared Docs Viewer include as the source template

---

docs viewer needs to use full screen when expanded!

---

The docs watcher should stay, but it should not be “Jekyll’s watcher.” The useful thing is scripts/docs/docs_live_rebuild_watcher.py: it watches _docs, _docs_library, _docs_analysis, rebuilds the matching generated Docs Viewer payloads/search, and keeps local docs current. That remains useful after Studio moves off Jekyll. The target is probably: bin/dev-studio starts the local Studio app server plus the Docs watcher and only the remaining needed background services.

You can still use bin/dev-studio now. Current behavior is unchanged: it starts Jekyll on 4000, tag/catalogue/docs/audit services, and the Docs Live Watcher by default via DOCS_WATCH_ENABLED=1. It does not yet start the new scripts/studio/studio_app_server.py on 8765, so for the new local app routes you still use the separate local app server at http://127.0.0.1:8765/studio/.

So current practical setup is:

bin/dev-studio
for the existing Jekyll Studio stack, old routes, write services, and docs watcher.

./scripts/studio/studio_app_server.py --port 8765
for the new local Studio app surface.

Later, Phase 4 should fold that second command into bin/dev-studio, then Jekyll becomes optional/separate for public-site preview rather than the Studio host.

---

footer:

The current local views in studio_app_views.py build their own minimal HTML shells with a header/nav and main content only. They do not reuse the Jekyll public layout/footer. That was intentional for the first slice: prove local hosting, runtime config, nav, Docs Viewer shell, and Tag Groups without pulling public-site chrome into Studio.

My recommendation: keep the local Studio app footerless unless it has a real Studio job. Public-site footer content probably should not come over. A small local footer/status strip could be useful later for things like server mode, active repo, health, docs watcher status, or version, but that should be designed as Studio app chrome, not inherited Jekyll chrome.

---

Implemented the bridge step: bin/dev-studio now starts the local Python Studio app server by default.

bin/dev-studio now has:
STUDIO_APP_ENABLED, default 1
STUDIO_APP_HOST, default 127.0.0.1
STUDIO_APP_PORT, default 8765

---

I’m about to add POST handling to the local app server and a Docs API adapter that calls the existing docs-management domain functions directly. The browser-facing base stays /studio/api/docs, so this is endpoint migration, not a second server or proxy.

It calls the existing Python docs-management functions directly.

Flow now:

Browser Docs Viewer JS
  -> fetch("/studio/api/docs/docs/update-metadata")
  -> scripts/studio/studio_app_server.py
  -> scripts/studio/studio_docs_api.py
  -> existing Python docs-management domain functions
So the browser still uses the existing JavaScript modules, especially assets/docs-viewer/js/docs-viewer-management-client.js, but the server-side call is Python-to-Python, not JavaScript-to-JavaScript.

The important distinction:

Before: Docs Viewer JS could call a separate docs-management HTTP server.
Now: Docs Viewer JS calls the Studio app server at /studio/api/docs.
The Studio app server imports/reuses the existing Python docs-management implementation instead of proxying to another localhost port.
This is the “one app server” direction we discussed.

---

Not quite.

The **page URL** is still the same:

`/studio/analytics/tag-groups/`

That page is now served by the **local Python Studio app server**, not by a Jekyll-rendered route, when you are using the local app on port `8765`.

Inside that page, the **data request changed**:

Before:
`GET /assets/studio/data/tag_groups.json`

Now, in local Studio:
`GET /studio/api/analytics/tag-groups`

So the route split is:

- `/studio/analytics/tag-groups/` = local app page shell
- `/studio/api/analytics/tag-groups` = local app API returning the tag-groups JSON data
- Jekyll/static fallback still exists for contexts that do not have the local runtime config/API.

Yes.

Before, the browser fetched the JSON file directly:

`/assets/studio/data/tag_groups.json`

Now, in the local Studio app, the browser calls:

`/studio/api/analytics/tag-groups`

and the Python app server reads:

`assets/studio/data/tag_groups.json`

then returns that JSON as an API response with `ok: true` added.

So the source data file has not moved. Only the access path changed: browser direct file read -> local app API read.

> so whats the benefit of doing it the api way?

For this specific Tag Groups read, the immediate benefit is small. It is mostly an architecture slice, not a feature improvement.

The useful benefits are:

- It proves the Phase 4 pattern for non-Docs route families: `studio_app_server.py` dispatches, `studio_analytics_api.py` owns analytics endpoints.
- It lets local Studio views stop depending on public/static asset paths as their data interface.
- It gives us one place to add validation, shaping, caching, diagnostics, or future source changes without changing the browser module again.
- It prepares for write/read workflows where the API boundary matters more, such as tag registry, aliases, assignments, and eventually retiring `tag_write_server.py`.
- It keeps the page URL stable while moving implementation behind it away from Jekyll/static-file assumptions.

But yes: for Tag Groups alone, this is deliberately low-value/low-risk. Its main value is establishing the route-module pattern before moving higher-risk analytics write services.

---