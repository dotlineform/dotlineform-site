---
doc_id: tmp
title: "tmp"
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: draft
---


actionlint is not installed here,


## VS Code menu ##

- **Commit**: saves the selected/staged changes into your local Git history only. Nothing goes to GitHub. No GitHub Actions run. No live site update.
- **Commit & Push**: commits locally, then sends the commit to GitHub. That can trigger GitHub Actions and, on `main`, the current legacy Pages publish path.
- **Commit & Sync**: commits, pushes your changes, and also pulls remote changes. Treat it as “commit plus network operations”.
- **Commit (Amend)**: rewrites the previous local commit. Useful only when you deliberately want to fold changes into the last commit.

For this moment, use **Commit** only.

After that, we can decide whether to push to a branch/PR for the dual-running workflow test, or hold it local until the next step.

←

`studio/app/frontend/config/ui-text/catalogue-work-editor.json`
 "save_status_loaded": "Loaded work {work_id}.",

config keys report:
`var/ui-text-usage-map.md`

---

## downloads

work_id 00008 has a download `nerve.pdf` (which is saved remotely), but the work page `http://127.0.0.1:4000/works/?series=105&work=00008` doesn't display any link to it. 'downloads' and 'links' may have been dropped from the UI in a previous refactor, but need to be added back in the metadata section of a work page. they should be hidden if no downloads or links have been defined.


/assets/js/public-catalogue-runtime.js
/assets/js/work.js
in-line scripts

---

edit project filename
status -> 'Unsaved source changes.'
'preview update' modal opens:
   Public update preview

   Public update preview: work 00008; series 105, 026; catalogue search no. local media pending 1.

   Changed fields: project_filename.

   Rules: work_media_source.

   Artifacts: local-media, source-json, studio-lookup.

   Reasons:
   - local-media, source-json, studio-lookup: Work source media folder and filename fields control Studio source-image editing, media readiness, and derivative generation; JSON rebuild follows only if derived dimensions change.

status messages:
source and public catalogue are aligned in this session
Public update preview: work 00008; series 105, 026; catalogue search yes. local media pending 1.

'work media' section:
displays:
Source media is ready and local thumbnails are current in assets/works/img/00008-thumb-96.webp.
current filename 'projects/nerve/nerve.jpg'
Local thumbnails are current for this record.
Save source changes before refreshing media.





I am doing some design and style changes to /studio/catalogue-work/ (using ?work=00008 as an example).



in `studio/app/frontend/config/ui-text/catalogue-work-editor.json`,
the save_status_loaded is not really needed for the UI. so I have set it to "". but is it used elsewhere in the code or could we simply remove the whole field?


That’s a good cleanup direction. `ui-text` should probably hold copy that benefits from configuration: user-facing prose l
ikely to change, route-specific labels, warnings, confirmation text, workflow status/result messages. It does not need every obvious or structural string.

Good trim candidates:
- Redundant “loaded” confirmations where the loaded record is already visible.
- Static button labels that are not expected to vary per route, especially common ones like `Save`, `Delete`, `Cancel`, `Close`.
- Internal-ish fallback labels where the UI element already provides context.
- Text keys used only to mirror field names, if field metadata already owns labels.
- One-off empty strings that exist only to suppress a hardcoded fallback.

Keep in config:
- Error and warning copy.
- Confirmation modal text.
- Destructive-action labels.
- Workflow statuses for save/build/publish/delete/import/media refresh.
- Route-specific placeholders or labels that shape workflow.
- Anything reused across routes where consistency matters.

If you want to do this safely, the process should be:
1. Build a usage map: key → file/line references.
2. Classify each key as configurable copy, static UI chrome, redundant status, field metadata, or stale.
3. Remove stale/redundant keys only after changing code fallbacks or removing code reads.
4. Keep tests focused on behavior, not exact configurable wording unless the wording is the behavior.

There’s already precedent in [AGENTS.md](/Users/dlf/Developer/dotlineform/dotlineform-site/AGENTS.md:8) saying compatibility aliases are prohibited and config cleanup should be direct rather than layered.

~

https://excalidraw.com

https://www.figma.com/pricing/


For this repo, the most useful format is usually:

1. **Annotated screenshot or sketch**
   - PNG/JPEG is fine.
   - Mark regions with labels like “filters”, “run list”, “details panel”.
   - Add notes for behavior/state, not just layout.

2. **Simple wireframe in Excalidraw, Figma, or a hand sketch**
   - Export as PNG.
   - Low fidelity is enough. Boxes and labels are better than polished mockups if the workflow is still changing.

3. **Short workflow notes**
   Include:
   - primary user goal
   - required actions
   - important empty/loading/error states
   - what should be visible without scrolling
   - what can be hidden behind details/modals

Best lightweight template:

```text
Screen: /admin/checks/
Goal: Run a report and review output quickly.

Must show:
- report + target filters
- run button
- recent runs
- selected report output

States:
- idle
- running
- failed
- no runs
- selected run loaded

Notes:
- controls should be compact
- output is more important than run history
- mobile is not important for this route
```

If you send an image plus those notes, I can translate it into implementation while keeping it consistent with the existing Admin/UI Catalogue guidance.


~

list document line counts:
`find ./docs-viewer/source/studio -name "*.md" -type f -print0 | xargs -0 wc -l | sort -nr`

scripts:
`find ./docs-viewer/runtime/js -name "*.js" -type f -print0 | xargs -0 wc -l | sort -nr`

with file size:

```
find ./docs-viewer/runtime/js -name "*.js" -type f -print0 |
while IFS= read -r -d '' file; do
  lines=$(wc -l < "$file")
  size=$(du -h "$file" | cut -f1)
  printf "%8s  %8s  %s\n" "$lines" "$size" "$file"
done | sort -nr
```


~

we are working on `site-request-docs-viewer-public-index-slimming-tasks.md`,
please review the request and proposed tasks and identify any areas or tasks that are missing or need clarification.

~

please create a focussed set of implementation docs:
- a task tracker using `tasks-tracker-template.md` as the template,
- a set of batch task delivery dos using `task-batch-template.md` as the template.
Follow the guidance in the templates for what to include in them.

~


---

## source

all scopes:
`docs-viewer/source` - source markdown

# published

management scopes:
`docs-viewer/generated/docs` - published JSON for each management scope

e.g. for `studio`:
`docs-viewer/generated/docs/studio/by-id` - full data, JSON file for each doc
`docs-viewer/generated/docs/studio/index.json` - metadata, all docs

public scopes:
`assets/data/docs/scopes` - published JSON for each public scope

e.g. for `library`:
`assets/data/docs/scopes/library/by-id` - full data, JSON file for each doc
`assets/data/docs/scopes/library/index.json` - metadata, all docs


`index.json` should only contain what is necessary to build the index tree view
`by-id` for public scopes should only contain what is needed

---

semantic references:

- registry: defines what they are, what they can do, who they involve (like tag registry)
- assignments: what actual relationships have been defined (like tag assignments)

a lot of this is already in the request docs, just needs tidying up. see also chatgpt notes - need to import them

---

split out css to separate view-specific files. css is only loaded when a view first needs it.
this keeps the css modular and easier to maintain.
do you agree this is a sensible approach?


---

docs viewer config:

how to update config through manage-mode
equivalent to an app's 'settings' UI

---

semantic [work_id]-[detail_id] link
need more


---

Studio home page

catalogue
- drafts - `studio/catalogue-status/?mode=manage`
- series editor: `/studio/catalogue-series/`
- work editor: `/studio/catalogue-work/`
- work detail editor - `/studio/catalogue-work-detail/?mode=manage`
- bulk add work - `/studio/bulk-add-work/?mode=manage`
- moment editor - `/studio/catalogue-moment/?mode=manage`
- list of works - `/studio/studio-works/?mode=manage&sort=cat&dir=asc`
- project state - `/studio/project-state/?mode=manage`

analytics
- series tags - `/studio/analytics/series-tags/`
- tag registry - `/studio/analytics/tag-registry/`
- tag aliases - `/studio/analytics/tag-aliases/`
- tag groups - `/studio/analytics/tag-groups/`

data sharing
- prepare package - `/studio/data-sharing/prepare/?mode=manage&scope=library`
- returned package - `/studio/data-sharing/review/?mode=manage&scope=library`

admin
- studio audits - `/studio/audits/?mode=manage`
- thumbnail tests - `/studio/thumbnail-quality/?mode=manage`
- UI demos - `/studio/ui-catalogue/demos/`
- studio activity - `/studio/activity/?mode=manage`
- field registry - `/studio/catalogue-field-registry/?mode=manage`


---

servers:

- `bin/local-all` - Studio, Docs Viewer, docs watcher
- `bin/local-studio` - Studio + Docs Watcher: `http://127.0.0.1:8765/studio/`
- local-all also starts Local Admin App: `http://127.0.0.1:8768/admin/`
- `docs-viewer/bin/docs-viewer` - Docs Viewer: `http://127.0.0.1:8776/docs/?scope=studio&mode=manage&doc=change-requests`
- `bin/public-site-preview` - public Jekyll preview: `http://127.0.0.1:4000/series/`
- `bin/public-site-preview --livereload`

scripts:

./docs-viewer/build/build_docs.py --write
./docs-viewer/build/build_docs.py --scope studio
./docs-viewer/build/build_docs.py --scope studio --write
./docs-viewer/build/build_docs.py --scope studio --write --only-doc-ids example-doc
./docs-viewer/build/build_search.py

./studio/services/catalogue/search/build_search.py


---