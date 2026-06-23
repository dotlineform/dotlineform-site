---
doc_id: docs-viewer-viewable-field
title: Viewable field
added_date: 2026-04-24
last_updated: 2026-06-23
parent_id: docs-viewer
---
# Viewable field

## Purpose

This document records the current `viewable` contract for Docs Viewer source docs, generated docs payloads, public snapshots, runtime navigation, and docs search.

The field is a visibility and discovery control.
It is not a security boundary and it is not a build-inclusion switch.

## Source Field

Docs source files support one viewability field:

```yaml
viewable: false
```

Current rules:

- omitted `viewable` means the doc is viewable
- `viewable: true` is accepted, but the normal source form is to omit the field
- `viewable: false` means generated but hidden from public/default discovery surfaces
- boolean-like false values such as `false`, `0`, `no`, and `off` are parsed as false by the Python source helpers
- there is no docs `published` field
- there is no docs lifecycle `status` field
- `ui_status` is a separate display/status-label field and does not affect build inclusion, tree visibility, or search inclusion

Management writes normalize the source:

- setting a doc viewable removes the `viewable` field
- setting a doc non-viewable writes `viewable: false`
- metadata editing can change the same field through the `non-viewable` checkbox

## Build Inclusion

The docs builder includes every configured Markdown source doc in the working generated docs payloads for the scope.
`viewable: false` does not stop a doc from being rendered.

Working docs payloads:

- `docs-viewer/generated/docs/<scope>/index-tree.json`
- `docs-viewer/generated/docs/<scope>/recently-added.json`
- `docs-viewer/generated/docs/<scope>/by-id/<doc_id>.json`
- `docs-viewer/generated/docs/<scope>/references/...`

The working index tree includes non-viewable docs.
Tree rows omit `viewable` for the default viewable state and include `viewable: false` only when the source doc is non-viewable.

The builder generates per-doc payloads for non-viewable docs so manage mode can open and review them.
For public read-only scopes such as Library and Analysis, by-id payloads are compact reader payloads and do not carry management metadata such as `doc_id`, `source_path`, `parent_id`, `ui_status`, or `viewable`.

The working `recently-added.json` payload is also generated from the configured docs set.
It should not be treated as the public visibility boundary; public filtering happens at runtime for navigation and at publish time for public snapshots.

## Public Snapshots

Public read-only routes read published snapshots under `site/assets/data/`, not the working generated root.
The docs publish gate filters the working payloads before writing those public snapshots.

For public snapshots, hidden doc ids are:

- every row with `viewable: false`
- every descendant of a row with `viewable: false`
- every configured `manage_only_tree_root_ids` root
- every descendant of a configured manage-only root

The publish gate:

- removes hidden rows from public `index-tree.json`
- removes hidden rows from public `recently-added.json`
- skips hidden `by-id/<doc_id>.json` payloads
- skips hidden `references/by-doc/<doc_id>.json` payloads
- removes hidden source references from `references/by-target/...`
- removes stale public files that no longer belong in the published snapshot

This means a non-viewable Library or Analysis doc can exist in the working generated data for local review while being absent from the public static payloads after publish.

## Runtime Visibility

The browser runtime loads the scope index and derives a visible document set.

Public/default contexts include a doc only when:

- the doc itself is viewable
- none of its ancestors is non-viewable
- the doc is not under a configured manage-only tree root

Manage contexts include all viewable docs and include non-viewable docs when the `show non-viewable` toggle is enabled.
That toggle is enabled by default in the management session.
If a manage-mode URL directly requests a non-viewable doc, the runtime enables non-viewable visibility so the requested doc can be selected.

Non-viewable rows are visually marked in the management index with the configured non-viewable marker and styling.

Direct public/default URLs to a non-viewable doc behave like URLs to any doc that is not in the current visible index: the viewer preserves the requested URL and renders the missing-document state.
The special default-doc fallback is limited to the existing default-route resolution path, not to arbitrary hidden docs.

## Search

Docs search is built from source front matter, not from the generated index tree.
The search builder reads the configured source root for the scope and applies the same hidden-root model used for public discovery.

Search excludes:

- docs with `viewable: false`
- descendants of docs with `viewable: false`
- docs under configured manage-only tree roots

Search includes one metadata-only record for each remaining viewable doc.
It indexes `doc_id`, title, parent title, and `last_updated` metadata; it does not index rendered body prose.

Targeted search updates can remove a doc when it becomes missing or non-viewable, but that removal requires `--remove-missing`.
Without that flag, targeted updates fail instead of silently deleting a search entry.

There is no separate manage-mode search path for non-viewable docs.

## Recently Added

Recently-added behavior differs by payload source:

- the working generated `recently-added.json` can include non-viewable docs because the builder emits from the generated docs set
- public snapshots filter hidden docs during publish
- the browser recently-added controller displays the entries provided by the payload it loads and then sorts/caps them

For public Library and Analysis routes, the loaded payload is the filtered public snapshot.
For local manage-mode generated reads, the loaded payload is the working generated payload.

## Create And Import Defaults

Default viewability for new managed docs is scope-specific:

- `library`: defaults to `viewable: false`
- `analysis`: defaults to `viewable: false`
- `studio`: defaults to viewable, so the field is omitted

HTML/source import uses the same scope default when creating a new doc.
Overwriting an existing imported doc preserves the existing viewability state.

## Make Viewable

Management endpoints support single-doc and bulk viewability updates.

When making a selected non-viewable doc viewable, the UI resolves the required target set before writing:

- required non-viewable ancestors are included after user confirmation, because the selected doc would still be hidden under a hidden parent
- descendants are optional and can be included by user choice
- unchanged docs are skipped by the server-side plan

The write path updates source front matter, rebuilds the affected docs payloads, and updates docs search for the affected ids.
Making a doc viewable removes `viewable: false`; making a doc non-viewable writes it.

## Parent And Descendant Semantics

The builder does not enforce a strict content workflow for viewable children under non-viewable parents.
It preserves source relationships and emits valid working payloads.

Visibility consumers are responsible for descendant hiding:

- public/default runtime hides a viewable child if any ancestor is non-viewable
- docs search hides descendants of non-viewable docs
- the public publish gate removes descendants of non-viewable docs from public snapshots
- manage mode can still show the original hierarchy for review

Changing a parent to viewable does not automatically change descendants.
Changing a parent to non-viewable does not rewrite descendants either; their effective public visibility changes because descendant filtering treats the parent as a hidden root.

## Risk Notes

`viewable: false` is suitable for keeping drafts and review material out of normal navigation, public snapshots, and docs search.
It is not suitable for private or sensitive material by itself.

Risk boundaries:

- non-viewable docs are still present in working generated payloads
- local manage-mode generated reads can serve those payloads
- public safety depends on runtime filtering for local/default views and publish-gate filtering for public read-only snapshots
- consumers that read working generated payloads directly must apply the same `viewable` and hidden-descendant rules if they expose discovery surfaces
