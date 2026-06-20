---
doc_id: tmp
title: "tmp"
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: draft
---


please adjust dropdowns and 'format' pills on `/analytics/data-sharing/prepare/?mode=manage&scope=library` so that they are vertically stacked, as styled on `/admin/checks/`

---

The archive is present at `studio/retired/site-routes/moments/index.html`


[Docs Viewer View And Mode Registry](/docs/?scope=studio&doc=site-request-docs-viewer-view-mode-registry).

The useful core was the original:
- create site/docs-viewer/runtime/js/shared/docs-viewer-view-registry.js
- use it as the shared owner for normalization and lookup
- centralize the decisions currently split across hosted views, display modes, and toolbar rendering
- keep runtime implementations where they are
- make config answer “is this view/mode/control available here?”

---



## doc viewer toolbars

- `docsViewer__controls`
  - mount point only, plus status/bookmark row
- `docsViewer__topBar`
  - `docsViewer__viewerToolbar` with `role="toolbar"` and `aria-label="Viewer controls"`
    - scope selector
    - recently added
    - search input
    - panel controls group: folder toggle + info toggle
  - management toolbar mount
    - `docsViewer__manageActions` with `role="toolbar"` and `aria-label="Management actions"`
      - Actions
      - Show
      - show non-viewable
    - theme toggle sits in the management row beside that toolbar

So search and recents are not floating controls. Structurally they are inside the viewer toolbar. The visual top row is a top bar containing two toolbar groups: viewer controls on the left, management controls on the right.

---

## Future modal UI:

- section modal edits `details_subfolder`, `section_title`, `section_order`, and `detail_sort`
- detail modal edits `detail_id`, `title`, `project_filename`, and selected `section_id`
- detail move workflows should change only the detail `section_id`
- empty sections are allowed while editing draft works so users can create sections before adding details
- saving a published work should be disabled while any detail section is empty
- deleting a section deletes all contained detail records after explicit confirmation

### Add Work-Scoped Section/Detail Save Rules

The later modal implementation should not reuse the old detail-route API.

Touched areas:

- new or updated work-scoped service APIs: define section create/update/delete and detail create/update/move/delete operations around the parent work.
- write allowlist and transaction planning: allow writes to the canonical source file through the new work-scoped operations, not through retired route endpoints.
- publication/build preview and apply paths: block saving a published work while any detail section is empty; allow empty sections for draft works.
- delete planning: deleting a section deletes contained detail records after explicit confirmation.

---


we are working in the work details section on the works editor page `/studio/catalogue-work/` using the shared lists component [Record List And Action Layer Implementation Note](/docs/?scope=studio&doc=ui-pattern-record-action-list)


please review and update [Catalogue Work Detail Editor](/docs/?scope=studio&doc=catalogue-work-detail-editor) - it mentions `site/assets/studio/js/catalogue-work-detail-editor.js` which doesn't exist, so I think the document picked up some errors during maintenance.


the plan is to replace the current work details editor page with modals on the works editor page. however there is a problem with the current data model that needs to be fixed first. we will use `studio/data/generated/catalogue-lookup/works/00782.json` as the example.
this contains the work metadata, and then a section for each work detail section:

```
  "detail_sections": [
    {
      "section_id": "00782-1",
      "section_title": "details",
      "sort_order": null,
      "count": 4,
      "details": [
        {
          "detail_uid": "00782-001",
          "detail_id": "001",
          "title": "birth of forms - detail 1",
          "section_id": "00782-1",
          "section_title": "details",
          "sort_order": null,
          "details_subfolder": "details",
          "project_filename": "birth of forms - detail 1.jpg"
        },
```

issues:

- `section_id`, `section_title`, `details_subfolder` are repeated for every detail, even though this is a nested structure.
- `details_subfolder` doesn't appear in the section metadata

this gives the impression that section and subfolder are independent attributes, but in reality they are not. source detail images are organised into subfolders, and each subfolder relates to a 'section' on the published site.

this matters because the current work details page mixes editing sections and editing detail records in the same thing. we need to change this when we migrate detail editing to the work editor. detail_section `section_title` and `sort_order` need to be editable independently of the details within them.

---

ok this is an opportunity to address the sorting. currently it is only `/studio/catalogue-series/` that enables works within a series to be sorted by id or title (for the thumbnail gallery of works in a series). sorting work details has happened in Excel as part of the bulk import process, i.e. the rows have been sorted in a meaningful order and then assigned sequential detail ids. there is currently no UI way of changing detail sort order.

so let's make the changes to the data model and associated plumbing first, before looking at the UI:

- rename the section `sort_order` to `section_order` which works as current: null means default to sort by section_id, otherwise use the entered numeric sort order.
- add `detail_sort` to the section which will be editable in the ui by choosing a sort key: detail_id or title. null values are interpreted as by id, which is what happens currently.
- remove the unused work detail `sort_order` field.

have I interpreted correctly?

~

Yes, interpreted correctly, with one explicit correction from the earlier version: the current plan is **null `section_order` defaults to sorting by `section_id`**, not alpha by `section_title`.

Target model:

- Section-owned fields:
  - `section_id`
  - `work_id`
  - `details_subfolder`
  - `section_title`
  - `section_order`
  - `detail_sort`

- Detail-owned fields:
  - `detail_uid`
  - `work_id`
  - `detail_id`
  - `section_id`
  - `title`
  - `project_filename`
  - dimensions/derived metadata as needed

Semantics:

- `section_order`
  - numeric values sort sections explicitly
  - `null` falls back to current behavior: sort by `section_id`
  - replaces the current ambiguous section-level use of `sort_order`

- `detail_sort`
  - section-level enum: `detail_id` or `title`
  - `null` means `detail_id`
  - controls generated order of details inside that section
  - gives Studio a future UI hook without changing detail IDs

- Work detail `sort_order`
  - removed from detail records
  - no current data loss, because existing canonical values are all `null`
  - no current UI behavior loss, because details are currently sorted by `detail_id`

That is the right foundation before moving detail editing into work-editor modals.

~

edit sections:



new (file picker)
- subfolder
- filename
- section title: = subfolder
- title: = filename stem
- section sort order: inherited from existing section

title

___

> do we no longer have flags like --only-workids for the python scripts? may have deprecated those.

Not gone, but split/renamed.

What I found:

- No current `--only-workids`.
- The internal generator still has:
  - `--work-ids`
  - `--work-ids-file`
  - `--only work-json`
  - `--only works-index-json`
- But `generate_work_pages.py` is now guarded as an internal engine. If run directly, it tells you to use:
  - `studio/services/catalogue/catalogue_json_build.py --work-id <work_id> [--write]`

The newer public helper is singular:
```bash
$HOME/miniconda3/bin/python3 studio/services/catalogue/catalogue_json_build.py --work-id 00008 --write
```

For four unrelated work IDs, it looks like the supported path is currently four runs, not one plural run. The plural `--work-ids` still exists underneath, but behind the internal `--internal-json-source-run` path.

So yes, the old plural workflow was effectively de-emphasized. We may want a small ergonomic wrapper later, e.g. `--work-ids 00008,00160,00161,00163`, because this exact repair is a good example of where one targeted multi-work rebuild is useful.

-----


- the old downloads list didn't have view action. it didn't have any links in the rows. there was no way of knowing what the file actually was without looking via the works page.
- the add button asks for a typed-in filename and label. I assume this is the filename of the file that has been manually copied into a staging folder, i can't remember, it is so long since I did it and i can't find any documentation about it.
- the existing nerve.pdf download for work 00008 is saved remotely and the public work page links to it: `https://media.dotlineform.com/works/files/nerve.pdf`
- however, there is another problem, that link doesn't work. the actual media is at `https://media.dotlineform.com/works/files/00008-nerve.pdf`
so, the file naming must have changed at some point, because I wouldn't have renamed the file without a reason. but the public page hasn't been updated with the new link. something has drifted.
- The old delete button doesn't have permission to delete R2 objects, so probably it just clears the json field. because I _still_ haven't set up R2 api keys we can't implement proper file level delete yet.

---

> interesting. so this is not exactly what I expected, because I thought the component would take much more work away from the consumer, to the point where the consumer would just say 'here's what file to use for the data' as opposed to actually do the list population and search rules etc.

Right. What we extracted is a **UI interaction primitive**, not a complete “search this dataset” product component.

It takes away:

- popup rendering lifecycle
- focus behavior
- select-all-on-focus
- Escape reset
- Tab close/reset
- ArrowUp/ArrowDown behavior
- Enter commit
- active row scrolling
- pointer vs keyboard selection state
- ARIA wiring
- commit/cancel callbacks

It deliberately does **not** take away:

- where data comes from
- how records are shaped
- what field is committed
- matching rules
- row layout/content
- what committing means

That split is why the same primitive can support:
- folder prefix search in the file picker
- work id/title search in the Work editor
- later, maybe series/member search with different rules

If we made it “give me a JSON file and I’ll search it,” it would become a higher-level component. That may be useful, but it should probably be a wrapper on top of `search-list`, for example:

```js
bindRecordSearch(input, popup, {
  loadRecords,
  fields: ["title"],
  idField: "work_id",
  mode: "contains",
  renderRecord,
  onSelect
});
```

So the current component is the reusable engine. We can still build more opinionated components on top once two or three consumers prove the same data/search pattern is repeating.

> I suppose eventually you would get to a point where the component has evolved into a full-blown plugin

There’s a rough progression:

1. **Primitive**
   `search-list`: owns generic interaction behavior, knows nothing about works/folders/files.

2. **Pattern Component**
   `file-picker`: combines primitives into a reusable workflow, knows about folders/subfolders/files but not Studio project paths.

3. **App Adapter**
   `catalogue-project-media-picker`: maps the generic picker to Studio’s `project_folder/project_subfolder/project_filename` fields and Studio APIs.

4. **Plugin / Package**
   If the same thing needs to travel across apps or repos, it gets its own config, assets, tests, docs, versioning expectations, and integration contract.

The important bit is not to jump straight to stage 4. A plugin too early usually freezes bad assumptions. What we’re doing now is better: extract stable behavior once it repeats, then only promote it when the boundaries are proven.

---

on studio pages, there is no visible difference between an editable field and a read-only one. I was going to see if hiding the border would be effective, and I found this css:

.tagStudio__input--readonlyDisplay {
  background: transparent;
  border-color: transparent;
  color: inherit;
}

span.tagStudio__input--readonlyDisplay.tagStudio__input--defaultValue,
.tagStudio__input--readonlyDisplay.tagStudio__input--defaultValue {
  color: var(--studio-default-value);
}

span.tagStudio__input--readonlyDisplay {
  min-height: var(--studio-control-height);
  display: inline-flex;
  align-items: center;
}

~

The simple solution is to keep the class structure and only change the readonly modifier:

```css
.tagStudio__input--readonlyDisplay {
  border-color: transparent;
  background: transparent;
  color: inherit;
}
```

That is safer than `border: 0` because it hides the border without changing layout, height, wrapping, or alignment. The element still uses `.tagStudio__input` for sizing and padding, but visually stops looking editable.

What the existing CSS means:

- `.tagStudio__input` gives every field the shared box shape.
- `.tagStudio__input--readonlyDisplay` says “this is display-only”.
- `span.tagStudio__input--readonlyDisplay` only handles inline `<span>` read-only values so they keep the same height and vertical alignment as inputs.
- `--studio-default-value` is the muted color used for blank/default placeholder-like values. Keep it.

I would not remove the `span` selector or default-value rules. I’d just add `border-color: transparent` to the readonly modifier, then check Work, Series, Detail, and Moment editor pages.

~

## Temporary Workflow Change

During this refactor, the public-site GitHub Actions workflow should not run automatically on pushes to `main`.
The migration is expected to involve many local commits and local verification runs.
Automatic `main` push runs would add noise while the deploy root is being refactored.

The workflow should keep:

- `workflow_dispatch`, so the public-site validation/upload/deploy path can be run manually when needed;
- `pull_request`, so review branches can still get workflow feedback when relevant.

This is an intentional temporary change for the catalogue runtime migration.
After the refactor is complete, restore the `main` push trigger for `site/**`, `site-tools/**`, `bin/site-validate`, and `.github/workflows/public-site.yml`.

~

---

python update needed?


~

## VS Code menu ##

- **Commit**: saves the selected/staged changes into your local Git history only. Nothing goes to GitHub. No GitHub Actions run. No live site update.
- **Commit & Push**: commits locally, then sends the commit to GitHub. That can trigger GitHub Actions and, on `main`, the current legacy Pages publish path.
- **Commit & Sync**: commits, pushes your changes, and also pulls remote changes. Treat it as “commit plus network operations”.
- **Commit (Amend)**: rewrites the previous local commit. Useful only when you deliberately want to fold changes into the last commit.

~ 

Current public-site config lives in `public-site/config/public-site.json`. Current repo-root detection uses that file.

Still elsewhere:
- local filesystem roots and media-generation env var names
  those live in **[Pipeline Config JSON](/docs/?scope=studio&doc=config-pipeline-json)**
- Studio/search browser text and JSON path settings
  those live in **[Studio Config JSON](/docs/?scope=studio&doc=config-studio-config-json)**
- dedicated `/catalogue/search/` runtime policy
  that lives in **[Search Policy JSON](/docs/?scope=studio&doc=config-search-policy-json)**

~

> there is no longer any persistent 'index.html' files, they are html and js code embedded in the python builder?

Correct for the public route pages.

There are no longer persistent source `index.html` / Markdown-Liquid route files for routes like:

- `/`
- `/about/`
- `/series/`
- `/works/`
- `/work-details/`
- `/moments/`
- `/recent/`
- `/catalogue/search/`
- `/library/`
- `/analysis/`
- `/404.html`

Those HTML files are generated into `_public_site/` by the Python builder from code under `public-site/build/public_site_builder/`.

The JavaScript is not embedded into Python as large inline scripts. The route shells reference existing JS modules under `assets/js/` and Docs Viewer runtime files under `docs-viewer/runtime/js/`.

So the split is:

- HTML shell structure: Python builder
- route behavior: JS modules in `assets/js/` / `docs-viewer/runtime/js/`
- generated deployable files: `_public_site/**/*.html`
- persistent checked-in source route stubs: removed for the migrated public routes.

> so the design-time reference is actually the published html file. how do people conceptualise and work with this?

Yes, the design-time reference becomes the generated HTML artifact plus the renderer code that produced it.

People usually work with this in three layers:

1. **Renderer source**
   The durable source is the Python renderer, for example `public-site/build/public_site_builder/render.py`, `catalogue_routes.py`, `docs_routes.py`, etc. This is where shared layout, nav, page sections, attributes, script tags, and route shell structure are edited.

2. **Runtime modules and CSS**
   Visual and behavior iteration usually happens in `assets/css/main.css` and `assets/js/...`. For this site, that remains the more natural place for most design/runtime changes.

3. **Generated artifact**
   `_public_site/**/index.html` is the inspection target. You build it, open it, compare it, smoke it, and use it to understand final output. But you do not edit it directly.

Conceptually, this is like React/Vue/Svelte/static-site components, except the “components” are Python functions instead of JSX/templates. The generated HTML is the compiled output.

The practical workflow is:

```bash
bin/public-site-build --destination /tmp/dlf-public-site-build --audit
```

Then inspect:

```text
/tmp/dlf-public-site-build/series/index.html
/tmp/dlf-public-site-build/works/index.html
```

Or run:

```bash
bin/public-site-preview
```

and inspect in the browser.

The tradeoff is real: there is less casual “open `series/index.html` and edit markup” authoring. The upside is that the public shell is now explicit, testable, and generated from one controlled boundary instead of scattered Liquid pages/includes.

> so the public site has to be built as one artifact? the bulk of the public site is image assets and catalogue search json, which rarely change during development work, but get rebuilt and redeployed regardless. is this just a fact of life?

For GitHub Pages Actions, yes: the deploy unit is one complete artifact. `actions/upload-pages-artifact` uploads a whole directory, and `actions/deploy-pages` publishes that snapshot. There is no first-class “only update these three files” Pages deploy.

But it is not quite “everything gets rebuilt all the time”:

- unrelated commits now do not trigger the workflow, as you verified with `tmp.md`
- image assets and JSON are mostly copied into `_public_site/`, not regenerated
- the expensive part is only whatever upstream generation you run before committing, not the Pages deploy itself
- the artifact must still contain the complete public site so deletes, renames, and route changes are represented correctly

So the practical answer is:

- **Fact of life for GitHub Pages artifact deployment:** publish a complete artifact.
- **Not a fact of life for every commit:** path filters avoid unrelated rebuild/deploy runs.
- **Probably acceptable for now:** 6,912 files is not large for a Pages artifact unless Actions time or artifact size becomes painful.

If it does become painful, the clean optimizations are:

1. Keep large rarely-changing media on R2/CDN and reference it remotely.
2. Make the builder copy unchanged files more efficiently locally.
3. Keep tighter workflow path filters.
4. Move to a host with delta sync only if artifact size becomes a real operational problem.

I would not add incremental deploy complexity unless the current workflow is measurably slow or hitting Pages limits.

~

> _public_site/assets/data/search/catalogue/index.json is 1.5MB, which is probably not good for a runtime asset.

It is worth watching, but it is less bad than the raw file size suggests.

Current facts:
- raw JSON: about `1.5 MB`
- gzip-compressed locally: about `76 KB`
- live GitHub Pages response: `content-encoding: gzip`, `content-length: 83,735`
- entries: `2,135`
- loaded by the dedicated catalogue search page, not every route

So the network cost is roughly 80 KB, which is acceptable for a search page. The browser still has to parse 1.5 MB of JSON after decompression, but for 2,135 entries that is probably fine unless you see search-page delay on slower devices.

The main bloat is duplicated text:
- `search_terms`: ~296 KB raw
- `search_text`: ~237 KB raw

If we optimize later, I would look at:
1. Remove either `search_terms` or `search_text` if both are not needed.
2. Use shorter field names only if parse/download becomes measurable.
3. Split by kind only if the UI can search subsets.
4. Lazy-load only after the user focuses/types in search, if it is currently loaded immediately.

I would not rush to change it now. Because it is gzip-served and route-specific, this is more “worth a performance review” than “bad runtime asset.”

> is it lazy loaded at the moment, because that would be a quick optimisation?

No. The search index is loaded on catalogue search page init.

Current flow in `assets/js/catalogue-search.js`:

1. `DOMContentLoaded`
2. `initSearchPage()`
3. load search policy
4. set status to `loading search index...`
5. fetch `/assets/data/search/catalogue/index.json`
6. normalize all entries
7. render prompt/results

So it is route-scoped, but not interaction-lazy.

A quick optimisation would be to defer `loadScopedSearchEntries()` until either:

- the user types the first valid query, or
- the URL already has a search query parameter

That would make `/catalogue/search/` cheap when opened casually, while preserving direct query links. The UI would initially show “Enter a search query.” and only switch to “loading search index...” after input.

This is a sensible small follow-up. It touches only `assets/js/catalogue-search.js` plus a focused smoke/test around:
- empty search page does not fetch index on load
- typing fetches index once
- query-in-URL still fetches and renders immediately.






←

`studio/app/frontend/config/ui-text/catalogue-work-editor.json`
 "save_status_loaded": "Loaded work {work_id}.",

config keys report:
`var/ui-text-usage-map.md`

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

- `bin/site-validate`
- `bin/site-preview`

scripts:

./docs-viewer/build/build_docs.py --write
./docs-viewer/build/build_docs.py --scope studio
./docs-viewer/build/build_docs.py --scope studio --write
./docs-viewer/build/build_docs.py --scope studio --write --only-doc-ids example-doc
./docs-viewer/build/build_search.py

./studio/services/catalogue/search/build_search.py

./docs-viewer/build/build_docs.py --scope tmp --write

---