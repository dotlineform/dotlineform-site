---
doc_id: site-request-rubyless-app-runtimes
title: Rubyless App Runtimes Request
added_date: 2026-05-30
last_updated: 2026-05-30
ui_status: draft
parent_id: change-requests
viewable: true
---
# Rubyless App Runtimes Request

Status:

- draft
- This request defines the migration approach for removing Ruby/Jekyll from local app runtimes one app at a time.
- The target is not to remove Ruby from the repository immediately. The target is to make Ruby/Jekyll a manual public-site preview/build tool only.

## Summary

Move every local management app to a Rubyless runtime contract.

Ruby and Jekyll should remain available for manually previewing or building the public site, but normal app startup and app smoke tests should not require `ruby`, `bundle`, Bundler, or Jekyll.

Target runtime ownership:

- Studio app: Python server plus browser JavaScript.
- Analytics app: Python server plus browser JavaScript.
- Docs Viewer management app: Python service plus browser JavaScript.
- UI Catalogue app: static or non-Ruby local server plus browser JavaScript.
- Public site preview/build: Jekyll/Ruby, run explicitly by the user when needed.

## Reason

The app split work has made the Ruby boundary more visible.

Studio, Analytics, Docs Viewer management, and UI Catalogue are now local tools with app-like runtimes. Their correctness should not depend on the public Jekyll preview server. They may link to public preview URLs, read generated public assets, or trigger public-site build workflows, but their own startup and core routes should stay independent.

Keeping Ruby inside app runtime assumptions creates practical friction:

- app startup can fail because public preview tooling is unavailable
- smoke tests conflate app regressions with Jekyll/Bundler setup problems
- ownership is harder to reason about because app routes and public-site routes appear coupled
- future replacement of the public site renderer becomes harder if app runtime checks already assume Jekyll

## Goals

- make each local app pass a focused runtime smoke with Ruby/Jekyll unavailable
- remove `ruby`, `bundle`, `bundler`, and `jekyll` checks from app startup paths
- keep public preview links optional and config-driven
- keep public-site preview/build commands documented as manual or explicit workflow actions
- convert app-required Ruby scripts to Python or isolate them behind explicit public-site build adapters
- preserve existing app URLs and app behavior while removing Ruby runtime coupling
- document the final boundary in local setup, runtime dependency, command, and ownership docs

## Non-Goals

- removing Jekyll from the public site in this request
- replacing public-site rendering
- changing catalogue, analytics, Docs Viewer, or UI Catalogue product behavior
- removing generated public assets that current apps legitimately read
- requiring public preview to be running for app health
- hiding failed public-build actions when the user explicitly runs a public build

## Target Boundary

Ruby is allowed in:

- manual public-site preview, such as a user-run Jekyll localhost process
- explicit public-site build commands
- public-site projection checks that intentionally test Jekyll output
- docs that explain public site infrastructure

Ruby is not allowed in:

- Local Studio startup
- Local Analytics startup
- Docs Viewer management startup
- UI Catalogue startup
- app route smoke tests unless the test is explicitly checking public-site integration
- app health checks
- app runtime config generation
- app-only generated data rebuilds

Public preview dependency rule:

- App runtimes may expose `PUBLIC_SITE_PREVIEW_BASE` or equivalent configured links.
- App runtimes must not fail health or route boot when the public preview server is not running.
- Actions that intentionally build or open public output should report public-preview/build availability as that action's status, not as app startup status.

## Implementation Strategy

Work app by app. Each app gets a Rubyless runtime contract before moving to the next app.

For each app:

1. inventory Ruby/Jekyll touchpoints in startup scripts, app server code, runtime config, smoke tests, and docs
2. classify each touchpoint as app-runtime, generated-data, public-preview, or public-build
3. remove app-runtime touchpoints or move them behind explicit public-preview/public-build commands
4. add a focused Rubyless smoke that blocks or hides Ruby/Jekyll commands and proves core routes still work
5. update docs to make the runtime boundary durable

## Implementation Tasks

Allowed statuses are `planned`, `in progress`, `done`, and `deferred`.

| ID | status | action |
| --- | --- | --- |
| 1 | planned | Define the Rubyless test harness. Add a reusable way to run app startup/smoke checks with `ruby`, `bundle`, `bundler`, and `jekyll` unavailable or shadowed, without changing the user's normal shell. |
| 2 | planned | Inventory Ruby/Jekyll touchpoints across app launchers, app servers, runtime config builders, smoke tests, command docs, and generated-data workflows. Classify each touchpoint by owner: app runtime, generated data, public preview, or public build. |
| 3 | planned | Make Local Studio Rubyless. Confirm `bin/local-studio`, `/studio/`, `/studio/runtime-config.json`, catalogue editor routes, audits, activity, and Studio APIs start and pass focused smokes without Ruby/Jekyll. Move any remaining public-preview assumptions behind configured links or explicit public-build actions. |
| 4 | planned | Make Local Analytics Rubyless. Confirm Analytics app routes, tag workflows, Data Sharing routes/APIs, runtime config, and focused browser smokes run without Ruby/Jekyll. Remove inherited Studio/Jekyll assumptions from Analytics startup and route tests. |
| 5 | planned | Make Docs Viewer management Rubyless. Confirm local `/docs/` management service, scope config, source mutations, generated-data reads, and management browser smokes run without Ruby/Jekyll. Keep public `/library/` and `/analysis/` Jekyll checks separate as public-site checks. |
| 6 | planned | Make UI Catalogue Rubyless. Serve UI Catalogue through static files or a small non-Ruby local server, and confirm route/demo smokes do not require Jekyll. |
| 7 | planned | Convert or isolate app-required Ruby scripts. Any Ruby script required by app startup or app-only checks should move to Python; Ruby scripts that remain should be documented as public-site build/preview tooling only. |
| 8 | planned | Split verification profiles. Add app-runtime profiles that are Rubyless, and keep Jekyll build/public preview profiles explicitly named as public-site checks. |
| 9 | planned | Update docs and command references. Revise local setup, runtime dependencies, `bin/local-studio`, app runtime, source ownership, and script docs so Ruby is described only under public-site preview/build unless a specific public-site check is being run. |
| 10 | planned | Final closeout. Run Rubyless app smoke set for each app, run explicit public-site build/preview checks separately, update this request with results, and record remaining risks. |

## Baseline Verification

Minimum Rubyless app verification should include:

- Local Studio home and one representative route smoke.
- Local Studio catalogue editor route smoke.
- Local Analytics route smoke for tag maintenance.
- Local Analytics/Data Sharing route smoke for prepare/review flows.
- Docs Viewer management smoke for `/docs/` with a fixture scope.
- UI Catalogue load smoke.
- Python syntax/import checks for changed app server and command modules.
- JavaScript syntax checks for changed app frontend modules.
- A command-path assertion that Ruby/Jekyll commands are not invoked during app startup.

Public-site verification remains separate:

- Jekyll build into a temporary destination.
- Public preview route checks for catalogue pages and public Docs Viewer installs.
- Public `/library/` and `/analysis/` read-only checks.

## Concrete Acceptance Criteria

The request is complete when:

- each local app has a documented Rubyless runtime contract
- each local app has at least one focused Rubyless smoke in the standard check set
- app startup docs do not instruct users to start Jekyll for app health
- app startup scripts do not check for Bundler/Jekyll unless explicitly launching public preview
- app runtime config generation does not shell out to Ruby
- remaining Ruby commands are documented as public-site preview/build commands
- public-site build checks still pass when explicitly run

## Known Risks

- Some app workflows may still read generated assets that are normally produced before public preview. These reads are acceptable only if the app does not require Jekyll to regenerate them during startup.
- Rubyless app checks can create false confidence if they only hide Ruby binaries but still rely on stale generated public assets. The task work should distinguish app runtime health from public projection freshness.
- Public-preview links may look broken when the user has not manually started Jekyll. The app should make this a link/action availability issue, not a runtime failure.
- Converting app-required Ruby scripts to Python can duplicate logic if the public-site build still uses the Ruby version. Prefer one owner per generated artifact before rewriting large scripts.
- Docs Viewer public installs under `/library/` and `/analysis/` are still public-site concerns until a separate public-site renderer migration exists.
