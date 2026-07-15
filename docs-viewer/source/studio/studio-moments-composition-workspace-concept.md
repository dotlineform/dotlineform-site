---
doc_id: studio-moments-composition-workspace-concept
title: Moments Composition Workspace Concept
added_date: 2026-07-12
last_updated: 2026-07-15
ui_status: proposed
parent_id: studio-moments-composition-workspace
viewable: true
---
# Moments Composition Workspace Concept

## Aim

Keep authored Moments text stable while different first-party composition engines arrange, style, preview, and materialise it.

The first engine is a word-axis composition inspired by printed text aligned around an invisible vertical fold. Later engines may be typographic, spatial, data-led, randomised, interactive, or image-producing. They should reuse one proven workspace rather than each inventing a new Docs Viewer shell.

## Intended Experience

- edit stable plain text;
- choose an available composition engine;
- see a live engine-owned preview;
- adjust engine settings in the existing info-panel surface;
- invoke the same commands from controls and keyboard actions;
- apply or save through explicit, reversible actions;
- leave the workspace and restore the previous document and panel state.

The preview is a workspace-owned region inside the main panel, not another global application panel.

## Content Model

Keep three things separate:

1. **Canonical content** — stable authored text and normal document identity.
2. **Composition recipe** — engine, settings, reproducible seed, and any manual decisions.
3. **Materialised output** — runtime DOM, static HTML, SVG, canvas, interactive output, or an image.

Changing engines must not require reverse-parsing generated output. Materialised output must never become the only recoverable copy of the text or recipe.

## Direction

- Begin with direct word-axis editing before introducing the whole workspace.
- Add the smallest shared refactor needed by each vertical outcome.
- Test the engine boundary with a deliberately different second engine.
- Use deterministic seeds for random output that must be reproducible.
- Preserve plain text as the accessible fallback.
- Add automatic generated-asset persistence only after its containment and publishing contract is understood.

## Open Questions

- Where should recipes live, and how should they travel through export, import, and publication?
- Should initial DOM engines render at public runtime or materialise during rebuild?
- How should manual decisions survive edited text?
- How should engine-specific CSS be loaded and reused for publication?
- What isolation is genuinely needed by unusually invasive engines?
- How do generated image assets enter the managed media workflow?
- What accessibility contract applies to interactive or animated compositions?

## Non-Goals

- a third-party plugin system;
- arbitrary module paths in route or scope config;
- a general-purpose visual programming environment;
- replacing ordinary Markdown source editing;
- forcing every engine to serialize to Markdown;
- silently publishing generated output;
- implementing every imagined engine before the first workflow is useful.
