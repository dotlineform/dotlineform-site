---
doc_id: dev-home
title: Dev Home
added_date: 2026-04-19
last_updated: 2026-05-23
summary: This section contains technical reference documents that apply to the repo as a whole.
parent_id: ""
sort_order: 1000
viewable: true
---
# Dev Home

This section contains technical design guidance for the repo, which is the source for the dotlineform website and deployed via GitHub Pages. The site is served on the domain [dotlineform.com](https://www.dotlineform.com).

The repo also contains the locally run web app **[Studio](/docs/?scope=studio&doc=studio)**, which manages the data for the site.

## Docs Viewer

**[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)** is a shared module used to publish source markdown documents. Documents are imported and organised using the 'manage mode'. This is hosted by Studio.

Note on document structure:

- document metadata saved in front-matter YML.
- `parent_id` is used to create a hierarchical structure to group related documents. Parent documents are often referred to as 'folders' or 'sections', because this is how they appear in the Docs Viewer index-tree. The source Markdown files are saved in a flat folder `_docs/...`

## Key Documents

- **[UI](/docs/?scope=studio&doc=ui)**
  site-wide UI framework and maintenance
- **[Change Requests](/docs/?scope=studio&doc=change-requests)**
  proposed and in-progress request docs, including UI request specs and task breakdowns.
- **[Development Workflow](/docs/?scope=studio&doc=development-workflow)**
  repo implementation lifecycle guide for scoping, verification, documentation, and closeout.
- **[Development Checklist](/docs/?scope=studio&doc=development-checklist)**
  detailed implementation rules for local Studio route migration, public/local URL boundaries, route builders, and UI Catalogue demo visibility.
- **[Architecture](/docs/?scope=studio&doc=architecture)**
  route/runtime building blocks, shared shell behavior, and generated-artifact flow into the live site.
- **[Config](/docs/?scope=studio&doc=config)**
  checked-in config files and loader modules, what reads them, and when.
- **[Data Models](/docs/?scope=studio&doc=data-models)**
  the main reference for generated/runtime data contracts and source-data records.
- **[Scripts](/docs/?scope=studio&doc=scripts)**
  repo scripts, their flags, outputs, and operational responsibilities.
- **[Docs Viewer](/docs/?scope=studio&doc=docs-viewer)**
  the shared docs module used by `/docs/` and other installed scopes (e.g. `/library/`).
- **[Search](/docs/?scope=studio&doc=search)**
  dedicated catalogue search plus inline docs-domain search.
