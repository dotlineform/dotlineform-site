---
doc_id: docs-viewer-management
title: Docs Viewer Management
last_updated: 2026-04-19
parent_id: ui-requests
sort_order: 100
---

# Docs Viewer Management

Status:

- planning skeleton
- needs product decisions before implementation
- likely larger than a simple UI request

## Summary

This document scopes a possible management mode for the shared Docs Viewer.

The feature would allow a local user to manage docs directly from a viewer instance rather than editing source files by hand first.

This is not only a UI change. It potentially affects:

- the shared Docs Viewer UI
- the `_docs_src` source tree
- docs metadata conventions
- the docs builder assumptions
- the local write-service boundary

## Goal

Implement a local-only management mode for the Docs Viewer that can expose document-management actions from within the viewer.

Candidate actions:

- drag and drop of index items to change `sort_order` and `parent_id`
- `new`
- `archive`
- `delete`

Required guardrails:

- enforce unique filenames
- enforce unique `doc_id` values
- define whether titles must also be unique
- expose management commands only when an explicit query param enables management mode

## Why This Needs A Real Spec

This request is bigger than a normal UI enhancement because it mixes:

- viewer interaction design
- source-of-truth file writes
- metadata validation
- file-system mutation rules
- archive/delete semantics

The toolbar itself is straightforward. The hard part is defining what these actions mean on disk and in the generated docs tree.

## Scope

Included:

- a management toolbar in the shared Docs Viewer shell
- a URL query switch that enables management mode
- local-server-only write behavior
- source metadata updates needed for supported management actions
- validation for filename and `doc_id` uniqueness
- tree operations that affect `parent_id` and `sort_order`

Potentially included, but needs a decision:

- drag-and-drop tree reordering and reparenting
- title uniqueness enforcement

Excluded for the first implementation unless later promoted:

- remote multi-user editing
- GitHub Pages hosted write behavior
- server-side auth and permissions
- collaborative conflict resolution
- inline markdown body editing
- publish workflow beyond local doc metadata mutations

## Primary Surfaces

- `/docs/`
- `/library/`
- shared Docs Viewer shell and runtime
- local docs-management service, if introduced

## Assumptions

- management mode is for local admin/developer use only
- the feature is unavailable on the static hosted site
- the current shared Docs Viewer model should remain shared unless management mode forces a deeper fork
- source docs remain file-backed under `_docs_src`

## Core Questions To Answer

### Source Of Truth

- What is the canonical source of a managed doc: the markdown file path, front matter, or both together?
- Should management mutate only front matter and tree placement metadata, or also move files on disk?

### File Creation

- When creating a new doc, how is the filename chosen?
- Is filename generation automatic from the title, from the `doc_id`, or user-specified?
- Which directory does a new doc go into by default?

### Tree Changes

- If a doc is reparented in the viewer, does only `parent_id` change, or should the file also move into a different folder?
- If `sort_order` changes by drag/drop, should the system renumber sibling items automatically or preserve sparse numbering?

### Archive

- What does `archive` mean?
- Move the file into `_docs_src/_archive/`?
- Set `published: false`?
- Change `parent_id` to `_archive`?
- Some combination of the above?

### Delete

- Is delete a real file deletion or a soft-delete workflow?
- If soft-delete, where does the doc go?
- If hard-delete, what protections are required?

### Uniqueness Rules

- Filenames should be unique: yes or no?
- `doc_id` values should be unique: yes or no?
- Titles should be unique: yes or no?

### Management Mode

- What is the query string key that enables management mode?
- Should management mode be visible only when the local write server is available?
- Should the mode fail closed when the server is unavailable?

## Recommended Initial Narrowing

To reduce implementation risk, a first pass should probably avoid drag/drop until the write semantics are stable.

Safer first pass:

- show management toolbar behind a query param
- support `new`
- support `archive`
- support `delete`
- support metadata validation
- defer drag/drop reorder/reparent until command semantics are proven

This keeps the first implementation focused on explicit commands rather than high-risk tree mutation UX.

## Write Model

This section should be completed before implementation.

Questions to answer:

- Is a dedicated docs-management local server needed, or should this extend an existing local Studio/tag server?
- What exact commands does the browser send?
- What validation happens before write?
- What rollback/backup behavior is required before file mutations?

Likely requirements:

- local-only write endpoint
- explicit write allowlist under `_docs_src`
- backup before destructive mutations
- deterministic rewrite behavior for front matter fields such as `doc_id`, `parent_id`, `sort_order`, and possibly `published`

## Command Semantics

This section should define exact behavior for each action.

### `new`

Questions:

- minimum required fields
- default folder
- default parent
- default `sort_order`
- default title and `doc_id`

### `archive`

Questions:

- whether the file moves
- whether `published` changes
- whether tree position changes
- how archived docs remain discoverable in the docs viewer

### `delete`

Questions:

- soft vs hard delete
- confirmation requirements
- whether references should be checked first

### `move` / drag and drop

Questions:

- whether drag/drop can change both `parent_id` and `sort_order`
- whether folder moves happen automatically
- whether the drag target is sibling ordering only in v1

## Data And Builder Implications

This section should be answered before implementation:

- does the docs builder assume source folder placement has semantic meaning beyond the doc tree?
- does flattening `_docs_src` become a prerequisite, or is it a separate cleanup project?
- are there any sections that depend on special folder names such as `_archive`, `_draft`, or `_dev`?

## Related Work

Possible related tasks:

- flatten the `_docs_src` folder

This should be treated as a separate planning track unless management mode truly depends on it.

## Non-Goals For First Pass

- turning the Docs Viewer into a full CMS
- multi-user or remote editing
- browser editing on the hosted public site
- solving cross-doc reference migration automatically
- introducing server-backed user accounts

## Phased Implementation Plan

### Phase 1

- define management-mode query param
- define write boundary and local-only availability
- define semantics for `new`, `archive`, and `delete`
- define uniqueness and validation rules

### Phase 2

- add management toolbar UI
- add create/archive/delete command flow
- add local service and backups

### Phase 3

- evaluate drag/drop reorder and reparent
- evaluate whether folder moves should exist at all

### Phase 4

- decide whether `_docs_src` flattening is still needed after real usage

## Decision Log

What is the canonical source of a managed doc: the markdown file path, front matter, or both together?  
A: front matter

Should management mutate only front matter and tree placement metadata, or also move files on disk?  
A: only front matter. this is one reason for flattening _docs_src: having folders which can easily drift from the hierarchy displayed in the viewer will be more confusing than just having a flat list of files in _docs_src

When creating a new doc, how is the filename chosen?  
A: 'new doc'. 'new doc 2' if 'new doc' already exists, etc

Is filename generation automatic from the title, from the doc_id, or user-specified?  
A: doc_id is slug friendly version of title. doc_id is used as file name stem

Which directory does a new doc go into by default?  
A: _docs_src/

If a doc is reparented in the viewer, does only parent_id change, or should the file also move into a different folder?  
A: file doesn't move on disk (flat structure).

If sort_order changes by drag/drop, should the system renumber sibling items automatically or preserve sparse numbering?  
A: currently, user (i.e. me) would preserve sparse numbering and pick a suitable mid-range sort_order. however a renumber siblings loop should be implemented to guarantee no conflicts ever happen. 

What does archive mean?  
A: parent_id becomes doc_id: _archive. so it moves to the Archive folder in Doc Viewer, as the last sibling. file remains unmoved in _docs_src. published remains true, so that it is still viewable.

Is delete a real file deletion or a soft-delete workflow?  
A: real file deletion. warning prompt.

Filenames should be unique: yes or no?  
A: yes (flat structure)

doc_id values should be unique: yes or no?  
A: yes

Titles should be unique: yes or no?  
A: no. agree with your comment, it's not necessary. it's a valid thing to do if docs have different parents, but this doesn't need to be enforced by the system. It's up to the user to decide.

What is the query string key that enables management mode?  
A: ?...&mode=manage

Should management mode be visible only when the local write server is available?  
A: yes this is better than my initial idea of having visibility determined by scope.

Should the mode fail closed when the server is unavailable?  
A: yes if user manually calls url with query string and server is not available, then 'server unavailable' message is displayed.

Is a dedicated docs-management local server needed, or should this extend an existing local Studio/tag server?  
A: If we follow current approach of creating a dedicated server for each new major requirement, then yes a dedicated server is needed. We already have a future task documented to consider merging dedicated servers into one. A decision is needed about when that point is reached. I will defer to your advice.

What exact commands does the browser send?  
A: whatever you think is best

What validation happens before write?  
A: unqiue filename and doc_id. unless there are security related reasons to additionally validate content or file name.

What rollback/backup behavior is required before file mutations?  
A: no rollback. backup on delete only.

whether references should be checked first before delete?  
A: no. broken links are for user to sort out.

whether drag/drop can change both parent_id and sort_order?  
A: yes. if doc is dropped onto a collapsed folder, it becomes the last sibling in that folder. if doc is dropped onto a visible doc, it is placed next to (after) that doc.

whether folder moves happen automatically?  
A: folders cannot be created, moved, or deleted. attempting to drag a folder is uneffective. the visible tree structure can only be changed manually by editing the front matter.

does the docs builder assume source folder placement has semantic meaning beyond the doc tree?  
A: not in a flat structure.

does flattening _docs_src become a prerequisite, or is it a separate cleanup project?  
A: it becomes a pre-requisite.

are there any sections that depend on special folder names such as _archive, _draft, or _dev?  
A: yes, but only in terms of doc_id. I have already mentioned _archive, that needs to exist for the Archive command. if system finds that it doesn't exist, it fails with error. In terms of file structure, _archive, _draft etc will disappear in flat structure.







