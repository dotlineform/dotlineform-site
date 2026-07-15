---
doc_id: docs-viewer-index-multiple-selection
title: Index Multiple Selection
added_date: 2026-07-14
last_updated: 2026-07-14
ui_status: proposed
summary: Feature parent for proposed index selection and group-move work, separated from its shipped action-target foundation.
parent_id: docs-viewer-roadmap
viewable: true
---
# Index Multiple Selection

## Purpose

Add familiar desktop multiple selection to the manage-mode index, then let explicitly designed actions consume that selection.

This is the feature parent. It does not act as an implementation tracker.

## Feature Documents

- [Concept](/docs/?scope=studio&doc=docs-viewer-index-multiple-selection-concept) — desired interaction, product boundaries, and deferred choices.
- [Architecture](/docs/?scope=studio&doc=docs-viewer-index-multiple-selection-architecture) — proposed state, ownership, action-target, drag/drop, and service boundaries.
- [Docs Viewer Roadmap](/docs/?scope=studio&doc=docs-viewer-roadmap) — the completed prerequisite and unsequenced future outcomes.

## Current State

The action-target prerequisite is complete. `docs-viewer-action-definitions.js` now gives current controls one code-owned scope, active-document, or selection target policy without adding multiple-selection state. [Runtime Module Ownership](/docs/?scope=studio&doc=docs-viewer-runtime-module-ownership) is the durable owner for that shipped boundary.

Pointer selection, group drag/drop, plural move service behavior, and additional multi-document consumers are not implemented.

No delivery is active. When this feature becomes important, promote one finishable roadmap outcome and add only that delivery as a child here.
