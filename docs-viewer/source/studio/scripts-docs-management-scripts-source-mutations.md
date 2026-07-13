---
doc_id: scripts-docs-management-scripts-source-mutations
title: Source Mutation Scripts
added_date: 2026-06-07
last_updated: 2026-07-13
parent_id: scripts-docs-management-scripts
---
# Docs Viewer Source Mutation Scripts

## `docs-viewer/services/docs_management_mutation_service.py`

Purpose: service wrapper for source mutation plans and scope lifecycle apply actions.

Ownership: owns executing mutation plans and connecting them to rebuild/log side effects.

Responsibilities:

- calls planners from `docs_management_mutations.py`
- writes planned source file changes atomically
- deletes planned source files for confirmed deletes
- runs single-scope or multi-scope rebuild follow-through
- logs completed create, metadata, viewability, move, delete, and lifecycle actions when plans request it
- attaches rebuild output and dry-run state to endpoint responses

Not responsible for:

- building mutation plans
- parsing HTTP request bodies
- serving generated read endpoints

## `docs-viewer/services/docs_management_mutations.py`

Purpose: mutation planner for source doc create, metadata, viewability, move, and delete workflows.

Ownership: owns validation rules and planned response contracts for source doc mutations.

Responsibilities:

- validates target scopes and doc ids
- plans new source docs and unique ids
- plans supported front matter updates
- validates parent ids and rejects parent cycles
- plans single and bulk viewability changes
- plans reparenting without moving files
- plans delete previews and confirmed delete applies
- calculates affected docs payload ids and docs-search ids
- reports no-op requests without writes or rebuilds

Not responsible for:

- performing actual file writes
- running builder commands
- opening local editors

## `docs-viewer/services/docs_scope_manifest.py`

Purpose: shared top-level scope ownership manifest and lifecycle policy support.

Ownership: owns the manifest schema, backfill/loading, shared identity and publishing-mode validation, storage-path policy, and manifest/config record helpers.

Responsibilities:

- loads or backfills `docs-viewer/config/scopes/docs_scope_manifest.json`
- records ownership for user-created scopes
- validates scope ids, default doc ids, publishing modes, and route paths
- blocks deletion of system-owned scopes

Not responsible for:

- general source doc mutations inside existing scopes
- top-level scope create planning or apply
- top-level scope rename planning or apply
- top-level scope delete planning or apply
- HTTP dispatch
- browser rendering

## `docs-viewer/services/docs_scope_create.py`

Purpose: top-level scope creation planner and apply owner.

Responsibilities:

- validates the requested publishing and storage contract through manifest policy helpers
- plans source, config, generated, route, and public-publish files
- writes the initial source/config/manifest/route records after confirmation
- runs scoped rebuild and initial public-publish follow-through

## `docs-viewer/services/docs_scope_delete.py`

Purpose: top-level scope deletion planner and apply owner.

Responsibilities:

- validates manifest ownership and management-route protection
- resolves manifest-recorded delete and missing paths
- plans config, manifest, and public-route record changes
- deletes only the confirmed manifest-owned paths
- runs all-scope rebuild follow-through after removal

## `docs-viewer/services/docs_scope_rename.py`

Purpose: external-local top-level scope rename planner and apply owner.

Responsibilities:

- limits rename eligibility to user-created, tool-owned external-local scopes
- validates external source/media/generated target collisions
- moves the scope-owned external roots to the new scope folder name
- updates marker-rooted config, UI-status, nested sub-scope, and manifest records
- rebuilds docs and search for the new scope id

It does not own public-route changes, R2 operations, or link rewriting inside source documents.
