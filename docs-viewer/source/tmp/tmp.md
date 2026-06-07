---
doc_id: tmp
title: "tmp"
added_date: 2026-05-26
last_updated: 2026-05-26
ui_status: draft
---


File	Focus
docs-viewer/runtime/js/docs-viewer-app-runtime.js	Private runtime coordination after route workflow and runtime-owner extraction; controller construction, config handoff, event binding, initial load sequencing, private callback handoffs, and returned app handle remain.
docs-viewer/runtime/js/docs-viewer-management-modals.js	management modal controller after transient modal shell and metadata parent-picker extraction.


# tmp

## Evidence Validity

Risk evidence must test whether scripts, config keys, generated config payloads, and generated artifacts have an active workflow purpose.
Ownership is necessary but not sufficient: a script, config key, or generated file can be correctly owned and still be harmful if its contract is speculative, unused, duplicated, or exposed to the wrong runtime surface.

For script, config, and generated-artifact evidence, summaries should distinguish:

- consumed by an active runtime, report, build, test, or documented operator workflow
- retained only as source-of-truth input
- browser-visible config or payload field with a current UI/runtime consumer
- server-only source path, write target, adapter contract, output pattern, metadata contract, or activity-emitter field
- transitional evidence with a retirement or migration task
- unconsumed output that should be removed, stopped at the producer, or replaced with a smaller contract

Temporary generated artifacts still need a consumer or explicit cleanup path.
Do not treat "has an owner" as proof that the artifact should continue to exist.
For browser-visible config evidence, record whether the field is part of an explicit whitelist or broad pass-through projection.

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

risk inventories should not be docs in the docs viewer scope.
- they should be saved in var/ as .md, and surfaced as readonly markdown in an Admin risk report page.
- they should not include tables, but lists formatted as columns - like they would be displayed in Terminal



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

Checked-in configuration artifacts that the current site and build scripts load directly:

site-wide Jekyll config in _config.yml
shared catalogue/media/runtime defaults in _data/pipeline.json
shared Studio/search browser config in assets/studio/data/studio_config.json
the Studio/search config loader in assets/studio/js/studio-config.js
Docs Viewer source scope config in docs-viewer/config/scopes/docs_scopes.json
Docs Viewer browser config defaults in docs-viewer/config/defaults/docs-viewer-config.json and docs-viewer/config/defaults/docs-viewer-public-config.json
Docs Viewer route-config registry in docs-viewer/config/routes/docs-viewer-routes.json
Docs Viewer service defaults/schema in docs-viewer/config/defaults/docs-viewer-service.json and docs-viewer/config/schema/docs-viewer-service.schema.json
Docs Viewer UI text in docs-viewer/config/ui-text/ui-text.json
dedicated /catalogue/search/ runtime policy in assets/data/search/policy.json
build-owned search source-family config in scripts/search/build_config.json
Library sharing profile config patterns in data-sharing/config/library-export-configs.json
Library sharing profile config schema in data-sharing/config/library-export-configs.schema.json
Data Sharing adapter dispatch in data-sharing/config/adapters.json
Data Sharing adapter schema in data-sharing/config/adapters.schema.json


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