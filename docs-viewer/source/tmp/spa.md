---
doc_id: "spa"
title: SPA
added_date: 2026-05-22
last_updated: "2026-05-22"
parent_id: ""
sort_order: 300
viewable: false
---

- there is no reason why /studio/... pages need to be on the public site. they are only run on local server. on public site, they are read-only shells but essentially non-functional as a public github jekyll page.
- There is no reason why site documentation at /docs/ should be publicly viewable. If it does need to be published publicly, it could be published in a read-only curated docs viewer install.
- Docs Viewer manage-mode of any docs viewer install is only functional when run off local server. Manage-only tools are not even displayed on public read-only docs viewer installs.

conclusions:

- studio infrastructure and front-end could be in a completely separate repo.
- they could be hosted as web pages on local server but that server does not need to be tied to github software versions or dependencies.
- studio infrastructure does not have to be Jekyll-managed web pages. it could be a pure javascript app. it could be a javascript app wrapped in a native app-shell. it could be entirely a native app front-end, built in Swift.
- we currently use the html-markdown library bundled with the jekyll server, but that does not mean that the studio web pages themselves need to be Jekyll. we could use any python or ruby library for the html conversion. producing github/jekyll-friendly markdown is not a requirement for use in Docs Viewer is not an actual requirement, because Docs Viewer doesn't render the markdown, it renders html. The markdown is a data source, not a published artifact.

Codex:

I agree with your conclusions. The current structure already points that way.

Current facts in the repo:

- Public `_config.yml` has `docs_viewer_management_enabled: false`, so `/docs/?mode=manage` is intentionally read-only on public builds.
- `bin/local-studio` serves management mode through the local Python app.
- public Jekyll preview/build stays separate.
- `/studio/` still ships as public static pages, and `assets/studio/` is about 26 MB of local-only UI/data/assets.
- Generated Studio docs/search payloads are also published today unless excluded.

Relevant files:
[public config](_config.yml), [local launcher](bin/local-studio), [docs shell gate](_includes/docs_viewer_management_route.html).

**Recommended Direction**

Treat the public site as a publishing artifact, Studio as a local application, and Docs Viewer as a portable document viewer/manager.

I would do this in stages:

1. **Public build hygiene first**
   Exclude `/studio/`, `assets/studio/`, `/docs/`, Studio docs payloads, and Studio docs search from public builds. Keep `/library/` or `/analysis/` public only if they are intentionally curated read-only corpora.

2. **Keep local Studio in-repo for now**
   Do not jump straight to a new repo until the public/local boundary is clean. A low-risk first move is keeping `_config.yml` public-only and serving Local Studio through the Python app.

3. **Then split Studio if it still feels valuable**
   A separate Studio repo makes sense once ownership is clear. The key decision is where canonical source data lives: public-site repo, Studio repo, or a shared/private data repo. That choice matters more than whether the frontend is Jekyll, Vite, Electron/Tauri, or Swift.

4. **Do not start with native Swift**
   A local web app is the pragmatic next architecture. Native shell only becomes attractive if you need OS integration, offline packaging, file pickers, tray behavior, or a more app-like distribution model.

On Markdown/rendering: yes, the markdown does not need to be GitHub/Jekyll-publishable if Docs Viewer consumes generated HTML. The real contract is “source markdown plus tokens in, viewer-safe HTML JSON out.” Current docs rendering is Jekyll-coupled through [scripts/jekyll_markdown_renderer.rb](scripts/jekyll_markdown_renderer.rb), but that can be replaced later with golden-output tests around headings, links, code, media tokens, semantic refs, and interactive HTML.

One caveat: excluding docs from the published site does not make them private if the GitHub repo itself is public. If privacy is the goal, source docs need a private repo/submodule or separate private data package.

---

- yes, `/library/` and `/analysis/` need to be public viewable, intentionally read-only.
- canonical source data doesn't need to live in the public site repo. if the public site repo cleanly reflects what is actually published, then presumably, canonical source data shouldn't live there, it should live next to the things that manage it.
- agree, some native shell functionality would be nice but not essential. native shell is not currently a realistic option given developer constraints.
- note that privacy is not goal. general public visibility through dotlineform.com is the key factor, that is what I mean when I say 'public'. repos are public, there is no reason for them to be private. there is no private data (excepting security tokens).

Codex:

That clarification changes the framing: this is not a privacy/security boundary, it is a **published-surface boundary**. The public repo can stay public; dotlineform.com should only expose what is meant to be a public site.

**Revised Direction**

I’d separate the system into three conceptual products:

1. **Public site**
   Publishes dotlineform.com. Includes works, series, moments, public catalogue data, public assets, `/library/`, `/analysis/`, and read-only Docs Viewer runtime needed by those routes.

2. **Studio**
   Local management app. Owns canonical source data, editors, local write services, docs management, catalogue management, audits, imports/exports, generated-data builders, and unpublished operational docs.

3. **Docs Viewer**
   Reusable viewer/manager module. Public installs use read-only mode; local Studio uses manage mode. `/library/` and `/analysis/` are public read-only consumers.

The cleanest end state is: Studio generates or exports the exact public-site source/artifact set, and the public site repo reflects only what dotlineform.com needs to build and serve.

**Near-Term Practical Path**

I would not start with a separate repo immediately. First, make the current repo behave like the desired boundary:

1. Public build excludes `/studio/`, `assets/studio/`, local Studio data, and the Studio docs route at `/docs/`.
2. Public build keeps `/library/` and `/analysis/`, plus their generated docs/search payloads.
3. Local `bin/local-studio` continues to use the dev config and can still serve `/studio/` and management `/docs/`.
4. Define a “published artifact manifest”: what files/directories are intentionally part of dotlineform.com.
5. Once that manifest is stable, move canonical source data and Studio app code into a Studio repo or sibling workspace.

**Repo Split Option**

Best eventual split:

- `dotlineform-site`: public site only.
- `dotlineform-studio`: local app, canonical data, scripts/services, docs source, builders.
- optional later: `docs-viewer`: portable viewer package or subtree used by both.

The important contract becomes a publish/export step from Studio to public site. That step should write only public-safe, intentionally published files.

**Jekyll**

Public site can stay Jekyll.

Studio does not need to stay Jekyll. A local JS app served by a small Python/Ruby/Node server is enough. The current Jekyll coupling is mostly route/template convenience plus markdown rendering. Since Docs Viewer consumes generated HTML, the renderer can eventually be replaced behind tests without requiring GitHub/Jekyll-friendly markdown as the source contract.

My recommendation: first clean the build/public boundary in-place, then split repos once the generated/published file contract is explicit.

---

yes. happy to stay with one repo until everything settles. disengaging studio from jekyll is more important, because I think it gives us more problems to solve than it helps (e.g. all the regenerating issues we have had)

a further clarification on public vs private. there is some canonical data about works that is not published, but it is not private in the sense that it cannot be saved in a public repo. quote from docs-viewer/source/studio/data-models-catalogue-source.md: 'source-only fields such as `notes` and `provenance` stay out of public projections unless an explicit runtime contract includes them.'

Codex:

Yes. That distinction is important:

- **not private**: fine to live in a public repo
- **not published**: must not be emitted into dotlineform.com runtime files, routes, JSON, HTML, search indexes, or viewer payloads

So the boundary is not “secret vs public repo.” It is **canonical authoring data vs published projection**.

I’d frame the direction like this:

**Primary Goal**
Disengage Studio from Jekyll as the local application/runtime, while preserving Jekyll as the public site publisher for now.

That means Studio becomes responsible for:

- editing canonical source data
- running local services
- generating public projections
- generating Docs Viewer payloads
- managing local-only operational docs
- previewing outputs

Jekyll becomes responsible for:

- building the public dotlineform.com site
- rendering public pages from already-prepared source/projection files
- serving `/library/` and `/analysis/` as read-only Docs Viewer installs

**The Key Architectural Move**

Introduce a stronger projection boundary:

```text
canonical source data
  -> Studio/app builders
  -> published projections
  -> Jekyll public site
```

For catalogue data, the rule you quoted is exactly right: `notes`, `provenance`, and similar fields can remain in canonical source, but they should only enter generated public artifacts when a specific public/runtime contract says so.

That suggests a useful naming discipline:

- `source` or `canonical`: complete working records
- `projection`: generated records for a specific consumer
- `public projection`: safe for dotlineform.com
- `studio projection`: local app/runtime only
- `viewer payload`: generated Docs Viewer JSON/HTML

**Why Disengaging Studio From Jekyll Should Come First**

I agree this matters more than repo splitting. The current setup makes local app behavior depend on Jekyll rebuild mechanics, Liquid route shells, generated `_site` state, and dev/public config overlays. That creates avoidable failure modes.

A local Studio server/app would let you:

- serve Studio routes directly without Jekyll page regeneration
- make generated-data rebuilds explicit app actions, not side effects of site serving
- separate “preview public site” from “use Studio”
- keep Docs Viewer management local without coupling it to Jekyll shell behavior
- choose a markdown-to-HTML renderer as an implementation detail

**Recommended Next Shape**

Short term, still one repo:

```text
studio-app/
  local frontend app
  local server/services

canonical-data/
  works, series, moments, docs source, tags, etc.

public-site/
  Jekyll site source, layouts, public pages

packages/docs-viewer/ or assets/docs-viewer/
  reusable read-only/manage viewer runtime

generated/
  public projections
  studio projections
  viewer payloads
```

The exact folders can wait. The important thing is to stop treating Jekyll as the Studio application host.

**Practical Migration Order**

1. Define the public projection contract for catalogue, docs, search, and assets.
2. Make public Jekyll builds consume only those public projections.
3. Move Studio route serving to a local non-Jekyll server/app while still reusing current JS modules where possible.
4. Keep Jekyll preview/build available as a separate command from Studio.
5. Only after that, decide whether to split repos.

My bias: build the next Studio shell as a plain local web app first. Native shell can remain a later wrapper decision, not an architectural dependency.

---

if studio is a plain local web app, how hard is reusing existing js modules, given that we would essentially want to preserve current functionality, workflows, behaviour, nav?

Not very hard if we keep it as a **plain vanilla local web app** and preserve the DOM contracts. It becomes hard only if we use the move as an excuse to rewrite the UI framework.

Most existing JS modules look reusable because they are already browser ES modules, fetch JSON, bind to stable IDs/data roles, and render into existing DOM. For example, [studio-data.js](assets/studio/js/studio-data.js) is already mostly runtime/data helpers, and [studio-ui.js](assets/studio/js/studio-ui.js) defines explicit UI contracts. That is good news.

The less reusable part is the route shell. A route like [studio/catalogue-work/index.md](studio/catalogue-work/index.md) mixes:

- front matter: route title, permalink, docs link
- Liquid config expansion from `_config.yml` and `_data/pipeline`
- HTML markup with fixed IDs/classes/data attributes
- Jekyll `relative_url`
- script include via [studio_module_script.html](_includes/studio_module_script.html)

That is all replaceable. It is not business logic. The migration task is mostly to turn those Jekyll/Liquid shells into local app templates and feed them config from JSON instead of Liquid.

**Difficulty Estimate**

- Preserving current workflows with a local multi-page vanilla app: **moderate, very feasible**
- Reusing existing JS/CSS without major rewrites: **highly feasible**
- Removing Jekyll route regeneration from Studio: **high value, moderate effort**
- Rebuilding Studio in React/Vue/Svelte/native: **much harder and not justified now**

The best path is not “rewrite Studio.” It is “replace Jekyll as the route/template host.”

**Recommended Shape**

Use a small local server that serves:

```text
/studio/
/studio/catalogue-work/
/studio/catalogue-series/
/studio/analytics/tag-registry/
...
/assets/studio/js/...
/assets/studio/css/...
/studio/runtime-config.json
/api/catalogue/...
/api/docs/...
/api/tags/...
```

Then keep the current route controllers mostly intact. The server can provide what Liquid currently injects:

- media bases
- thumbnail bases
- pipeline variant config
- route docs links
- UI text paths
- service endpoint URLs
- cache-busting/no-cache headers

**Main Migration Risks**

The biggest risk is not JS reuse. It is **implicit Jekyll assumptions**:

- paths generated through `relative_url`
- config injected as `data-*` attributes
- route layout/header/nav from `_layouts/studio.html`
- links between Studio routes
- links from Studio to public preview pages
- any tests that assume Jekyll-served `/studio/...`

Those are manageable if we migrate one route at a time and keep IDs/classes/data roles unchanged.

**Practical Migration Order**

1. Build a local non-Jekyll Studio server that can serve static assets and one route.
2. Convert a simple route first, probably `/studio/studio-works/` or `/studio/activity/`.
3. Add a shared Studio shell/nav template outside Jekyll.
4. Convert one complex editor route, probably `/studio/catalogue-work/`.
5. Keep current write services/endpoints stable, or proxy them through the new local server.
6. Once representative routes work, move the rest mechanically.
7. Leave public Jekyll build untouched except for excluding Studio from the published site.

My read: preserving functionality is realistic because the existing frontend is already modular enough. The work is mostly route-host extraction, config injection cleanup, and test coverage around the pages where Jekyll currently supplies hidden glue.

---

note that by 'nav', I mean 'user clicks a button and it takes them to a page or a modal'. it doesn't really matter if they are taken to different url routes or stay on the same page all the time. how we maintain persistent nav states through url queries is only the current (jekyll) enforced solution. the url doesn't actually matter to the studio user.

Codex:

That makes the local-app direction easier, not harder.

If Studio users do not care about stable URL routes, then Studio does not need to preserve Jekyll-style page navigation. It only needs to preserve **task navigation**:

- click opens editor
- click opens modal
- select record
- return to prior list/filter/context
- save/build/delete/import flows keep their state
- preview links go to the right public artifact when needed

So the target can be an **application state machine**, not a static route collection.

**Implication**

The current URL-query model should be treated as an implementation detail, not a product contract. It exists because Jekyll gives us static routes and the browser URL is the easiest shared state container.

A local Studio app can replace that with:

- in-memory app state for active page/modal/selection
- browser history only when useful
- local/session storage for restoring last workspace
- explicit return targets in state, not `?from=...`
- modals/drawers instead of separate pages where that improves workflow

**Better Target Shape**

Studio could become a single local app shell:

```text
/studio/
```

with internal views:

```text
catalogue.work
catalogue.series
catalogue.moment
analytics.tagRegistry
docs.manage
activity
audits
dataSharing.prepare
```

The visible URL could stay `/studio/`, or optionally use hash/history state like:

```text
/studio/#catalogue.work:00456
/studio/#analytics.tagRegistry
```

But that is for restore/debugging, not because the user needs URL fidelity.

**Reuse Impact**

This slightly reduces direct reuse of page shells but keeps most JS logic reusable if we wrap it carefully.

Current route controllers likely assume:

- specific root DOM exists
- specific buttons/inputs exist
- initial state comes from URL query
- navigation is `window.location.href = ...`

Those can be adapted with a small navigation/service layer:

- `getInitialRouteState()` currently reads URL; later reads app state
- `navigateTo(view, params)` currently sets URL; later swaps view or opens modal
- `openModal(name, params)` centralizes modal behavior
- `setReturnContext()` replaces `?from=...`

The goal would be to avoid rewriting editor internals. Replace the edges where controllers enter/leave pages.

**Recommendation**

Do not migrate to SPA all at once. First create a local app shell with a router abstraction, but keep route-like views internally. Then gradually decide which “pages” should become modals or panels.

That preserves current behavior while removing Jekyll as the thing enforcing URL-shaped workflow.

---

'Rebuilding Studio in React/Vue/Svelte/native: much harder and not justified now' - agree. if I had made this design decision much earlier, there would have been pros and cons. now it too late and I have no intention of moving unless there is a serious technical/maintenance reason to do so.

Codex:

That is the right call.

At this point, the technical debt is not “missing framework.” The debt is that Studio is hosted by the wrong runtime. Jekyll is forcing app workflows through static-page mechanics: Liquid injection, rebuild coupling, URL-query state, generated `_site` behavior, and dev/public config overlays.

A framework migration would add a second problem:

- porting UI and controller behavior
- revalidating every workflow
- replacing mature route-specific modules
- rebuilding CSS/component conventions
- introducing package/build tooling
- likely pausing actual product work for a long time

The better move is narrower:

**Keep:**

- current vanilla ES modules
- current CSS/UI conventions
- current DOM contracts where useful
- current local Python/Ruby services initially
- current workflows and labels

**Change:**

- Studio host runtime
- config injection model
- app navigation/state ownership
- public build inclusion
- generated projection boundaries

So I’d describe the strategic direction as:

> Studio should become a local vanilla web app, not a Jekyll section and not a frontend-framework rewrite.

A good migration target is boring:

```text
local server
  serves one Studio app shell
  serves existing JS/CSS/assets
  provides runtime config JSON
  exposes/proxies existing write/read endpoints
  optionally serves public-site preview/build artifacts
```

Then the current Jekyll route files become source material for view templates. Existing JS modules continue to carry the behavior until there is a specific reason to refactor them.

The standard for introducing any new framework should be high: it should solve a concrete maintenance problem that cannot be solved cleanly with smaller vanilla modules. Right now, the concrete problem is Jekyll coupling, not lack of React/Vue/Svelte.

---
