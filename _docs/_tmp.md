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