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

