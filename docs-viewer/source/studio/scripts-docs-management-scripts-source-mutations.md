---
doc_id: scripts-docs-management-scripts-source-mutations
title: Docs Viewer Source Mutation Scripts
added_date: 2026-06-07
last_updated: 2026-06-07
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

Purpose: scope ownership manifest and scope lifecycle planner/apply helper.

Ownership: owns manifest schema, lifecycle validation, and scope create/delete file plans.

Responsibilities:

- loads or backfills `docs-viewer/config/scopes/docs_scope_manifest.json`
- records ownership for user-created scopes
- validates scope ids, default doc ids, publishing modes, and route paths
- previews create and delete file/config changes
- applies scope creation and deletion after confirmation
- blocks deletion of system-owned scopes

Not responsible for:

- general source doc mutations inside existing scopes
- HTTP dispatch
- browser rendering
