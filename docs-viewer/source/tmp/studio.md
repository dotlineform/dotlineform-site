---
doc_id: studio
title: tmp studio
added_date: 2026-05-24
last_updated: 2026-05-24
parent_id: ""
sort_order: 200
---

> great. my initial reading is that lots of actions are needed which implies that the previous work wasn't thorough enough. but perhaps the reason is rather that the migration targetted functional areas, which was the only way to tackle it, and accept that gaps will remain. if we were to do a similar app/shell rewrite for studio, would we keep the same basic approach and follow up cleanup as we are doing here?

Yes. I would keep the same basic approach for a Studio app/shell rewrite: migrate by functional area, make ownership better with each slice, and then run a deliberate cleanup/classification pass like this one.

The important distinction is that the cleanup findings do not automatically mean the prior work was poor. In a live app, the alternative to functional slices is usually a risky “big rewrite” where you try to make the architecture perfect before behavior is safely moved. The Docs Viewer work seems to have chosen the safer path: extract boot, app context, service context, generated-data runtime, state domains, hosted views, route workflow, search/bookmarks, management lazy loading, etc., while leaving compatibility bridges where complete controller families still depended on broad state or callbacks.

That is a valid migration strategy if three things are true:

1. The temporary bridges are named honestly.
2. The public API is narrowed as soon as possible.
3. A follow-up cleanup pass classifies each remaining bridge as remove, track, or rename as current architecture.

That is exactly what this cleanup tracker is doing now.

For Studio, I would use the same migration shape, but I would be stricter up front about the cleanup ledger because Studio has more write surfaces and operational routes. I would expect each slice to record:

- the functional area moved,
- the new owner module,
- the compatibility bridge left behind,
- why it could not be removed yet,
- the test that guards current behavior,
- the exact follow-up task that removes or narrows it.

So the lesson is not “avoid compatibility gaps.” The lesson is “make compatibility gaps explicit, bounded, and scheduled.” For a Studio shell rewrite, that is probably the only pragmatic way to reduce risk while keeping the app working.

---

I reviewed [site-request-studio-source-tree-reorganization.md](/Users/dlf/Developer/dotlineform/dotlineform-site/_docs/site-request-studio-source-tree-reorganization.md:1). The spec is directionally solid, but it would benefit from a few sharper decisions before implementation.

**Clarification Areas**

- **Define “source boundary” vs “served URL” explicitly.**  
  Lines 58-70 propose `studio/app/static/` while preserving `/assets/studio/...`. Clarify whether files move physically and are served by a local static mount, copied/projected back into `assets/studio/`, or left in place until later.

- **Clarify what happens to current `studio/` Jekyll route files.**  
  The target uses `studio/` as the new source boundary, but `studio/` is also an existing route/source location. State whether old route markdown shells are removed, moved under `studio/app/shells/`, or retained as compatibility fixtures.

- **Separate canonical data, generated data, and local runtime config.**  
  Lines 38 and 116-117 mention Studio static data and generated-output-adjacent paths, but current `assets/studio/data/` includes mixed things: config, UI text, canonical catalogue-ish data, lookup payloads, previews, activity payloads. Add a decision table for what moves, what remains generated, and what is explicitly out of scope.

- **Tighten domain-service ownership.**  
  Lines 35 and 48 leave some ambiguity around `scripts/studio/` route/API modules versus `scripts/catalogue/`, `scripts/analytics/`, and `scripts/docs/` domain services. Clarify that Studio app server/adapters may move under `studio/app/server/`, while domain services stay domain-owned unless a specific file is only a Studio route adapter.

- **Make the browser-shell step either required or optional.**  
  Lines 72-99 describe an architectural direction, while lines 119 and 123 make it sound partly prerequisite/conditional. Decide whether “move nav/shell composition out of Python” is an acceptance requirement for this request or a separate follow-up slice. Current Python config and views still own route labels, scripts, CSS includes, and shell rendering.

- **Define the compatibility layer lifetime.**  
  Lines 41, 69-70, and 126 mention compatibility paths/import aliases. Add criteria like: compatibility aliases must be removed in the same slice unless needed by named smoke tests, and any retained alias needs an owner plus removal condition.

- **Clarify CSS split mechanics.**  
  Lines 101-112 set the target well, but implementation needs a rule for tokens/selectors: what counts as “genuinely shared primitive,” whether shared primitives stay in public `main.css` or move to a neutral base, and whether UI Catalogue demos should use Studio base CSS or a separate catalogue demo base.

- **Add verification gates per slice.**  
  Acceptance says focused smoke checks should pass, but the spec could name minimum checks for each move type: Python import/syntax checks, Local Studio route smoke, UI Catalogue smoke, public Jekyll build, CSS/public selector audit, projection-contract/public-build-surface audit.

- **Clarify Jekyll/public preview exclusion expectations.**  
  The repo already excludes `studio/`, `assets/ui-catalogue/`, and `assets/studio/` in [_config.yml](/Users/dlf/Developer/dotlineform/dotlineform-site/_config.yml:108). If source files move under `studio/`, spell out whether public preview should ignore all of that tree or whether any projected public artifact is allowed.

- **Call out docs-log/update expectations.**  
  Given this is a multi-slice reorganization, add that each slice should update this request with status, update owning runtime/UI docs when behavior changes, and create a `_docs_logs` entry at commit points.

I did not edit the spec. The biggest thing to settle first is the source-vs-served-path model, because it determines whether this is mostly path mapping inside the local server or a projection/build-contract migration.