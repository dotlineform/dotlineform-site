---
doc_id: processing-app-design-episodic-semantic
title: "Processing App Design — Episodic vs Semantic Modes"
added_date: "2026-07-14 17:57"
last_updated: "2026-07-14 17:57"
parent_id: unsorted
---
# Processing App Design — Episodic vs Semantic Modes

> [2025-09-08 23:30:57 BST] Original prompt: "Spin into a second HTML page focused purely on UI/algorithm design for the Processing app (episodic vs semantic modes, attention gates, reconsolidation noise schedule, schema-first layout templates)."

This document reframes the episodic–semantic distinction into actionable Processing design modules.

## Episodic Mode

- **Frame-by-frame recall**: each composite represents a unique “event” (layer stack).
- **Attention gates**: emphasize salient regions (contrast edges, faces, motion hotspots).
- **Context encoding**: preserve timestamp metadata, source-file origin, and color/emotion filters.
- **Reconsolidation jitter**: each re-export applies subtle transformation (e.g., warp ±1%, random opacity shifts) to mimic fragile recall.
- **UI metaphor**: “Timeline scrubber” that lets user move through episodes like autobiographical filmstrip.

## Semantic Mode

- **Concept-driven layout**: composites arranged by schema (grid, circle, radial fan) rather than raw chronology.
- **Knowledge accumulation**: generate averaged textures/palettes from many episodes to extract enduring patterns.
- **Decontextualization**: strip away metadata/time, present distilled structures (shapes, color fields, frequency counts).
- **Shared knowledge mode**: templates driven by external “concept map” CSV (keywords → arrangement rules).
- **UI metaphor**: “Atlas view” or “encyclopedia grid” of composites.

## Cross-Mode Functions

- **Switch toggle**: episodic ↔ semantic view (user can flip between filmstrip and atlas).
- **Feedback loop**: episodic composites feed semantic averages; semantic schemas bias episodic layering.
- **Blend strategies**: episodic = sequential overlays; semantic = weighted averaging.
- **Noise schedule**: adjustable slider controlling reconsolidation drift (episodic) vs. stability (semantic).

## Algorithm Hooks

- **Attention scoring**: salience function (Sobel edges, face-detect, brightness variance) → weight layers.
- **Reconsolidation transform**: per-frame random affine transform & opacity jitter.
- **Schema templates**: pre-defined layouts (grid, radial, hierarchical tree) mapped from keywords.
- **Knowledge fusion**: mean texture/palette extraction across frames for semantic distillation.

Processing design module — Episodic vs Semantic implementation notes. © 2025-09-08
