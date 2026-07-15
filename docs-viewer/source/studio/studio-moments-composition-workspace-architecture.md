---
doc_id: studio-moments-composition-workspace-architecture
title: Moments Composition Workspace Architecture
added_date: 2026-07-15
last_updated: 2026-07-15
ui_status: proposed
parent_id: studio-moments-composition-workspace
viewable: true
---
# Moments Composition Workspace Architecture

This is proposed structure, not current-state authority. The code and current Docs Viewer architecture documents remain authoritative until a delivery ships.

## Ownership

- Docs Viewer owns the application shell, document modes, hosted info views, registered controls, commands, and source-editor adapters.
- The Moments workspace owns its internal editor/preview layout, draft state, engine selection, and restoration lifecycle.
- Each engine owns its algorithm, preview lifecycle, settings validation, engine commands, recipe normalization, scoped assets, and supported outputs.
- Canonical Moments source remains document-owned. Generated output is derived.
- Managed media owns any future persisted image asset boundary.

## Proposed Execution Path

```text
registered Moments mode
  -> mount composition workspace in the main region
  -> load selected first-party engine from a code-owned registry
  -> pass canonical text plus validated recipe to the engine
  -> mount preview and project settings/commands
  -> apply an explicit source or recipe change
  -> use the existing save and rebuild boundary
  -> unmount and restore previous application state on exit
```

## Extension Method

An engine registration may declare its id, loader, recipe validator, settings surface, commands, assets, and output capabilities. The workspace shell must not branch on known engine ids.

The registry is a narrow first-party extension point. It is not a marketplace, package protocol, or config-driven plugin loader.

## Methodology

- Prove shared structure through vertical feature deliveries.
- Make controls and shortcuts invoke the same command ids.
- Keep workspace layout intent in the active mode rather than mutating shell elements directly.
- Keep simple settings reusable while permitting a focused custom lifecycle for unusual controls.
- Scope engine DOM and CSS to its assigned preview mount.

## Pressure Points

- Current layout and restoration contracts may not yet support a transient split workspace cleanly.
- Command eligibility inside editable controls needs explicit focus precedence.
- Recipe persistence and stale-decision handling are unresolved.
- Public rendering and rebuild-time materialisation have different asset and security boundaries.
- Image output introduces containment, metadata, replacement, and publication ownership.
- A generic engine abstraction could grow before two materially different engines prove it.
