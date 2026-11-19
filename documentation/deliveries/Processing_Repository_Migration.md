---
draft: false
doc_id: d-20261119-170000-9eb8ac
title: Processing Repository Migration
added_date: "2026-11-19 17:00:00"
last_updated: "2026-11-19"
ui_status: done
---

# Processing repository migration

The standalone `dotlineform-processing` repository owns the sketchbook and Processing documentation. Studio continues to use the external Projects `processing/` media source for finished works.

- [x] Extract the Processing source and documentation history from site `main` in an isolated clone. Follow the setup document through its earlier paths and exclude the retired render directories `processing/exports/` and `processing/previews/`.
- [x] Make the new repository root the sketchbook, update its docs and ignore rules, and record the MIT, historical CC0 and ControlP5 licence scopes. Carry the ignored InkEngine output configuration into the new local checkout and update Processing's sketchbook preference.
- [x] Push the verified standalone `main` and update the site working tree to point at it. The site-side removals and documentation updates are ready for a site commit. [Standalone migration commit](https://github.com/dotlineform/dotlineform-processing/commit/960ebf9c2c3744a808eede58c1eea46f7924adfb) · [Studio handoff](../reference/Source_Tree_Ownership.md#processing)

The isolated extraction retained 11 source and documentation commits with new Git identities. Before the standalone setup commit, all 442 current source and documentation files matched their site blobs. The 27 retired render blobs were absent from reachable history. GitHub reported the new repository as public with MIT detected, and the local `main` tracks its published branch.

InkEngine compiled from the new sketchbook and its existing `OutputWorkspaceTest` passed 26 assertions. The site validator passed. This verification covered compilation and the output path helper. GUI rendering and export remain a separate manual review.
