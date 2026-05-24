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

docs viewer extraction:

the current request doc site-request-docs-viewer-shell-extraction.md states that Studio app may host Docs Viewer. This is not necessary, and would continue to blur the boundary between studio and docs viewer. here is some clarification:

- docs viewer needs to be self contained in a folder .docs-viewer/
- it is known to the host repo through repo owned config
- it is not part of Local Studio app. it runs in its own shell, which is started/stopped independently of Local Studio.
- it advertises it's running local host location e.g port, through config so that other pages (e.g. studio or jekyll hosted pages) can link to documents hosted by docs viewer in either public read-only docs viewer pages or local-only manage-mode docs hosted by docs viewer.
- therefore for this repo, we might have 3 services running independently: Live Preview, Local Studio, Docs Viewer. (it will be useful for this repo to have a shell script that starts all those services).

Yes, a few that are worth settling before task planning:

Where should the repo-owned host config live?
Current draft says config/docs-viewer-host.json, but this repo also uses var/local/site.env for local env. We should decide which parts are tracked defaults versus local runtime state.

- i'll leave for you to decide. I think var/local/site.env is an acceptable prerequisite for hosting docs viewer. also any relevant entries that need to be made in _config.yml, .gitignore. anything else can belong in a docs viewer owned config.

Should .docs-viewer/ be committed as source in this repo, or treated as a portable package folder that may later become a submodule/package?
This affects import paths, scripts, tests, and how much repo-specific config is allowed inside it.

- can we keep it tracked in this repo as is currently, and consider treating as a package later, when we've got it all working?

Who writes the advertised base URL/port?
Options: Docs Viewer launcher writes runtime config on start, a shared service manager writes it, or it is static config with fixed ports.

- can we keep it static for now, and deal with truely portable issues later?

What should happen when Docs Viewer is not running?
Studio/Jekyll links could be hidden, disabled with status text, or still point to the configured URL and fail normally.

- just fail normally. It just happened to me when clicking on a link and i realised that i didn't have Live Preview running. in this case, a 404 is the best reminder, rather than complicate the UI.

Are public read-only docs served by Docs Viewer meant to replace /docs/, /library/, /analysis/ locally, or only provide alternate links?
The current spec preserves public routes but lets pages link into Docs Viewer.

- I'm not sure I understand this question. you either read a doc in the docs viewer browser page hosted by its own server (i.e. manage mode) or in a page that is hosted by the repo (i.e. Jekyll) and which was installed/registered by docs viewer.
- so, docs viewer comes with one route built-in, `/docs/`, which is manage mode. from there you can create other scopes like we have got with Library and Analysis, which are mapped to corresponding routes `/library/` and `/analysis/`. That is the whole point of the 'New Scope' Action in manage mode, it creates those scopes/routes for you, which at runtime would use the scripts contained in `.docs-viewer/` folder.

Should manage-mode remain local-only by service binding/auth boundary, by route capability config, or both?
I’d lean both: loopback-only service plus explicit capability flags.

- let's assume that manage mode is local only. assuming that a site has it's own server to run manage mode 'live' is a leap too far. Plus, we are currently only supporting GitHub Pages sites.

For “start all three services”, should this be a lightweight shell script or a small process supervisor?
A script is enough for v1, but stop/restart/log behavior should be defined so it doesn’t become fragile.

- I don't know the technology but I would steer towards a solution that is not fragile. A script is fine for v1, i assume that is what we used for the now deprecated bin/dev-studio which started jekyll and docs watcher and various write services?


---

normal development should use:

- `bin/local-studio` for Studio
- `bin/public-site-preview` for public Jekyll preview
- `bin/public-site-preview --livereload`



---

<https://developers.openai.com/codex/migrate?utm_campaign=ML_MIX_GWT_AW_codexnewsletter_OF_EX_MAY_18&utm_content=utm_content&utm_medium=email&utm_source=sendgrid&utm_term=utm_term>

<https://developers.openai.com/codex/skills>

---

