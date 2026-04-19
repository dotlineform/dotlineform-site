---
doc_id: docs-viewer-management
title: Docs Viewer Management
last_updated: 2026-04-19
parent_id: ui-requests
sort_order: 100
---

# Docs Viewer Management Task

Status:

- initial notes for Codex review
- to be turned into spec. Move to a full planning doc if scope too big for a 'UI request'

## Goal

Implement features which enable document management from a docs viewer instance.

- drag and drop of index items to change a doc sort order and parent
- new, archive and delete commands
- enforce unique filenames, doc_ids and titles
- the commands will be on a tool bar which can be shown/hidden by a url query string (default hidden)
- local server only

related tasks:

- flatten the _docs_src folder
