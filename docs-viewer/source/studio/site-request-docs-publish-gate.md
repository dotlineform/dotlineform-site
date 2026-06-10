---
doc_id: site-request-docs-publish-gate
title: Docs Public Publish Gate
added_date: 2026-06-10
last_updated: 2026-06-10
ui_status: draft
parent_id: change-requests
viewable: true
---
# Docs Public Publish Gate

current docs viewer public scopes display changes as soon the the generated files are rebuilt. we need to change this to a gated publish, where the generated files are owned by docs viewer and manage mode shows changes on rebuild (or by docs watcher), and the docs are published on the live public scopes by user clicking a Publish menu item. This will copy the generated json from docs viewer `docs-viewer/generated` to public site `assets/data/docs`.