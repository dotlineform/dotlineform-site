---
doc_id: docs-viewer-management-write-model
title: Docs Viewer Management Write Model
added_date: 2026-05-19
last_updated: 2026-05-22
parent_id: docs-viewer-management
sort_order: 54300
---
# Docs Viewer Management Write Model

## Write Model

Phase 1 decision:

- use a dedicated docs-management local server first

The current repo already keeps new localhost write surfaces separate while domain contracts settle.
That same approach is appropriate here because docs management introduces a different write target and a different validation model from Studio catalogue or tag writes.

Required write-model properties:

- local-only write endpoints
- explicit scope-to-root allowlist
- backup before every write batch
- deterministic front matter rewrite behavior
- apply endpoints that can be mirrored with dry-run validation

## Command Semantics

Initial command semantics were defined for `new`, `archive`, and `delete`.
The implemented management surface now also includes metadata edit, leaf-doc drag/drop move, and draft viewability.

### `new`

- minimum required field from UI: `scope`
- server may accept omitted title and create `New Doc`
- default parent is the flat scope root
- default parent is blank unless created from a parent context
- default `sort_order` appends as the last sibling
- default title and `doc_id` use the normalized `New Doc` stem rule

### `archive`

- file does not move
- `published` does not change automatically
- tree position changes through `parent_id = archive`
- archived Studio docs remain discoverable in the normal docs tree under the Archive doc
- archived Library docs remain generated; public visibility depends on each doc's own `hidden` value
- `archive` is an ordinary doc id and can be hidden from public views with `hidden: true`

### `delete`

- delete is a hard file delete
- preview is required before apply
- child-doc dependencies block delete
- inbound markdown references are previewed as warnings

### `move` / drag and drop

- only leaf docs are draggable
- dropping on the upper half of a row changes `parent_id` to that target doc and appends as the target's last child
- dropping on the lower half of a row keeps the target's parent, shows an insert line after the target row, and places the moved doc after the target
- any node can become a parent through drag/drop; there is no `folder` source field
- when there is room between neighboring `sort_order` values, only the moved doc is rewritten
- the destination sibling set is normalized to sparse unique orders, currently `1000`, `2000`, `3000`, and so on, only when the numeric gap is exhausted or target ordering is ambiguous

## Data And Builder Implications

Phase 1 answers:

- the docs builder does not need nested source folders for tree meaning, but it currently uses `source_path` for relative markdown-link resolution
- flattening `_docs` is a prerequisite for Studio management mode
- `_docs_library` is already flat and does not need the same migration
- special names such as `archive` remain meaningful as `doc_id` values, not as required source folders
- the `archive` `doc_id` remains a conventional Archive command target, but it is not protected or non-loadable by name

Implementation consequence:

- write-enabled viewer management can now rely on a flat Studio source root
- any future layout change still requires relative-link review because nested-path assumptions can affect markdown source links
- viewer visibility comes from generated doc fields such as `hidden`, not from hard-coded source-folder names

## Related Work

Possible related tasks:

- flatten the `_docs` folder
- add a dedicated docs-management local server
- later evaluate whether docs-management should join the broader localhost-server consolidation work

The broader localhost-server consolidation question is still a separate planning track.
Flattening is no longer optional work here: it is a prerequisite for Studio docs management.

## Non-Goals

- turning the Docs Viewer into a full CMS
- multi-user or remote editing
- browser editing on the hosted public site
- solving cross-doc reference migration automatically
- introducing server-backed user accounts

## Phased Implementation Plan

### Phase 1

- flatten `_docs` for Studio
- rewrite or verify source-relative markdown links affected by flattening
- define management-mode query param
- define write boundary and local-only availability
- define semantics for `new`, `archive`, and `delete`
- define uniqueness and validation rules
- keep title edits independent from `doc_id` and filename
- define the conventional Archive command target id, `archive`
- define the localhost API contract for create/archive/delete

### Phase 2

- add management toolbar UI
- add create/archive/delete command flow
- implement the local service and backups for every write batch
- add delete preview with inbound reference reporting

Status:

- implemented

### Phase 3

- evaluate drag/drop reorder and reparent
- evaluate whether folder moves should exist at all
- implement `POST /docs/move` for front-matter-only tree moves
- add manage-mode drag/drop for leaf docs in the shared docs index

Status:

- implemented as a leaf-doc-only move flow
- docs with children remain non-draggable by design

### Phase 7

- let any node receive children through drag/drop without adding a source schema field

Status:

- implemented

## Decision Log

What is the canonical source of a managed doc: the markdown file path, front matter, or both together?  
A: front matter

Should management mutate only front matter and tree placement metadata, or also move files on disk?  
A: only front matter. this is one reason for flattening _docs: having folders which can easily drift from the hierarchy displayed in the viewer will be more confusing than just having a flat list of files in _docs

When creating a new doc, how is the filename chosen?  
A: 'new doc'. 'new doc 2' if 'new doc' already exists, etc

Is filename generation automatic from the title, from the doc_id, or user-specified?  
A: doc_id is slug friendly version of title. doc_id is used as file name stem

Which directory does a new doc go into by default?  
A: _docs/

If a doc is reparented in the viewer, does only parent_id change, or should the file also move into a different folder?  
A: file doesn't move on disk (flat structure).

If sort_order changes by drag/drop, should the system renumber sibling items automatically or preserve sparse numbering?  
A: drag/drop preserves sparse numbering when possible by assigning only the moved doc a value between neighboring siblings. If the numeric gap is exhausted or the target order is ambiguous, the destination sibling set is normalized to `1000`, `2000`, `3000`, and so on.

What does archive mean?  
A: parent_id becomes doc_id: archive. so it moves to the Archive folder in Doc Viewer, as the last sibling. file remains unmoved in _docs. published remains true, so that it is still visible unless `hidden: true` is set.

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
A: no rollback. backup before every write batch.

whether references should be checked first before delete?  
A: yes, preview references first. broken links can still be user-resolved, but delete should surface what will break before confirmation.

whether drag/drop can change both parent_id and sort_order?  
A: yes. if a leaf doc is dropped on the upper/main part of any doc row, it becomes the last child of that target doc. if it is dropped on the lower edge of a row, it is placed after that target doc.

whether folder moves happen automatically?  
A: there is no source-level folder flag. any node can become a parent through drag/drop, but docs that already have children still cannot be dragged in the current implementation.

does the docs builder assume source folder placement has semantic meaning beyond the doc tree?  
A: not in a flat structure.

does flattening _docs become a prerequisite, or is it a separate cleanup project?  
A: it becomes a pre-requisite.

are there any sections that depend on special folder names such as archive, _draft, or _dev?  
A: yes, but only in terms of doc_id. I have already mentioned archive, that needs to exist for the Archive command. if system finds that it doesn't exist, it fails with error. In terms of file structure, archive, _draft etc will disappear in flat structure.

Should `archive` be treated as a protected system doc?  
A: no. `archive` is required only as the conventional Archive command target. It should be editable like a normal doc, and public/search visibility should be controlled with `hidden: true`.

If a title changes later, should that mutate `doc_id` and filename?  
A: no. title changes do not mutate `doc_id` or filename.
