---
doc_id: site-request-moments-composition-workspace
title: Moments Composition Workspace
added_date: 2026-07-12
last_updated: 2026-07-12
ui_status: proposed
parent_id: workspaces
viewable: true
summary: Proposed frontend workspace for composing stable Moments text through interchangeable visual algorithms, live previews, settings, commands, and multiple publication outputs.
---
# Moments Composition Workspace

Status: proposed

## Summary

Create a frontend composition workspace for Moments.
The workspace keeps authored text stable while allowing different composition engines to arrange, style, preview, and materialise it.

The first engine is a word-axis composition inspired by printed text whose lines are shifted around an invisible vertical fold.
The longer-term purpose is broader: support interchangeable typographic, spatial, data-led, randomised, interactive, and image-producing algorithms without rebuilding the editor and Docs Viewer shell for each idea.

This is not only a Moments formatting control.
It is the first concrete consumer of a general application-workspace model for coordinated panels, modes, controls, settings, commands, and previews.

See [Moments Composition Workspace Roadmap](/docs/?scope=studio&doc=site-request-moments-composition-workspace-roadmap) for the proposed vertical sequence.

## Starting Point

The current proof establishes that:

- Moments can use scope-owned CSS on both `/moments/` and `/docs/?scope=moments`
- `pre.moment-text` can inherit normal Moments typography instead of generic monospace code typography
- opt-in axis lines can align two spans around a shared `--moment-axis`
- titles and dates can opt into the same alignment without changing ordinary Moments documents
- the Markdown source editor exposes source selection and replacement behavior
- the semantic-reference editor demonstrates that source-editor selection can drive a separate frontend tool

The proof currently materialises algorithm-specific spans directly in Markdown.
That is useful for validating the visual effect, but it should not become the assumed canonical model for a workspace that can switch among unrelated algorithms.

## Intended Experience

### Basic Axis Editing

The first useful editor should support direct source actions:

- select a word and make it the first word after the axis
- reconstruct either a plain text line or an existing axis line around the selected word
- suggest an axis word for every line in a selected or enclosing text block
- retain blank-line group boundaries
- apply the transformation as one undoable editor action
- use the existing source save and rebuild workflow

The suggested split should use measured text width rather than character count.
It should reject overflowing halves, prefer a visually central boundary, and treat linguistic heuristics as weak suggestions rather than rules.

### Composition Workspace

The later workspace should provide:

- a stable plain-text editor
- an algorithm selector
- an engine-owned live preview
- an info-panel settings view for the active engine
- shared Apply, Save, Undo, Reset, and workspace-exit behavior where relevant
- engine-specific commands and keyboard actions through the shared command model
- restoration of the previous document and panel state on exit

Entering the workspace should be expressible as one document-mode transition:

- the index becomes transiently hidden
- the main region becomes a composition workspace
- the workspace divides its own region between editor and preview
- the info panel opens the active engine's settings view when appropriate
- leaving restores the previous index and info state without changing persisted preferences

The preview is a workspace-owned region inside the main panel.
It is not a fourth global application panel.

## Composition Model

The durable model should keep three layers separate.

### Canonical Content

The authored Moment remains stable plain text with its normal document identity and descriptive metadata.
Changing composition engines must not require reverse-parsing the previous engine's generated HTML.

### Composition Recipe

A recipe records the choices needed to reproduce a composition, such as:

- recipe schema and version
- engine id and engine version
- settings
- deterministic random seed where relevant
- manual per-line or per-token decisions
- source fingerprint used to detect stale decisions after text edits
- intended output kind

The persistence location and source-file representation are open decisions.
Large per-line decisions should not be forced into unreadable front matter merely to avoid defining an appropriate owned format.

### Materialised Output

An engine may produce:

- runtime DOM from plain text and a recipe
- static HTML
- SVG or canvas output
- an interactive visualisation
- a raster image
- more than one supported output from the same recipe

Materialised output is derived.
It must not become the only recoverable copy of the authored text or recipe.

## Composition Engines

Each engine may own:

- algorithm-specific JavaScript
- preview DOM construction and cleanup
- scoped preview and publication CSS
- default settings and validation
- a settings schema or custom settings view
- commands that operate within the workspace
- recipe normalisation and stale-state handling
- supported output kinds and materialisation behavior

Engines are registered explicitly in code and loaded through a narrow first-party registry.
The registry must not become a marketplace, package protocol, or arbitrary config-driven plugin loader.

The workspace shell must not branch on engine ids.
Switching engines should unmount the current engine, retain or reset state according to an explicit rule, load the next engine, mount its preview, and project its settings and commands.

The first two engines should be deliberately different:

- `word-axis` proves measured text, word-boundary decisions, HTML/CSS composition, and direct manual correction
- a small seeded scatter engine proves random but reproducible placement, arbitrary preview DOM, different settings, and a different output boundary

If the second engine requires engine-specific changes throughout the workspace shell, the engine boundary is incomplete.

## Application Architecture Requirements

### Mode And Layout

The active document mode should declare its layout intent and default info view.
Workspace code must not directly mutate index, main, or info shell elements.

The current fixed document layouts need a transient workspace profile and reliable previous-state restoration.
The mode-owned layout contract should remain narrow rather than growing into a general user-configurable grid system.

### Views And Settings

The existing info-panel host is the appropriate settings surface.
The composition settings view should consume the active engine's state through an explicit workspace context or adapter.

Simple engines may use a shared settings renderer.
Engines with unusual controls may provide a focused settings lifecycle module.

### Controls And Scope Eligibility

Workspace and engine controls should be normal registered controls.
The registry needs a direct way to express scope eligibility so Moments-only tools do not require scattered `viewerScope === "moments"` checks.

Adding a control should not require separate hardcoded renderer, projection, reference, event-router, and action-controller branches.
Controls should invoke named commands through a shared renderer and command dispatcher, with focused overrides only when presentation is genuinely specialised.

### Commands And Keyboard Behavior

Buttons and keyboard shortcuts must invoke the same command ids.
A command record needs:

- eligibility by route, scope, active view, and active mode
- enabled state
- execution handler
- optional key bindings
- an explicit decision about whether it may run while focus is inside an editable control

Keyboard dispatch should respect this priority:

1. active modal or popover
2. focused hosted view
3. active document mode or workspace
4. application-wide commands

Axis word selection and composition commands must work deliberately inside the source textarea.
Unrelated global shortcuts must not fire while authored text is being entered.

### CSS And Preview Isolation

Composition engines must not add all future presentation rules to the shared Docs Viewer or Moments stylesheet.
The engine asset contract needs to decide how algorithm CSS is scoped, loaded, reused for publication, and released or left cached when an engine changes.

An engine must render inside its assigned preview mount and clean up on unmount.
If a future engine genuinely requires stronger CSS or DOM isolation, a shadow-root or framed-preview option can be evaluated against publication fidelity; it should not be added speculatively for the axis engine.

## Output And Publication

DOM and static-HTML engines may remain entirely browser-rendered if the published Moments runtime can consume the recipe and engine safely.
Image-producing engines create an additional persistence boundary: the browser can generate the visual artifact, but saving and publishing that artifact needs a narrow, explicit asset workflow.

Image output must preserve:

- canonical text
- reproducible recipe and seed where applicable
- accessible alternative text or transcript
- dimensions and media metadata needed by the public page
- a clear distinction between preview output and the published asset

The first image experiment may use an explicit manual download and media-import step.
A server-backed asset write should be added only when the generated-asset contract and containment rules are understood.

## Decisions So Far

- Treat this as a composition workspace with interchangeable engines, not an axis-only editor.
- Keep the workspace editor algorithm-neutral and text-first.
- Keep canonical content, recipes, and materialised output separate.
- Use the existing Docs Viewer mode, panel, hosted-view, and toolbar foundations, extending proven gaps rather than bypassing them.
- Use vertical refactor-and-feature slices instead of completing an abstract framework first.
- Keep executable workspace and engine registration code-owned.
- Use deterministic seeds for random behavior that must be reproducible.
- Preserve plain text as an accessible fallback even when publication uses an image or complex visual output.

## Open Decisions

- Where the composition recipe is persisted and how it travels with document export, import, and publication.
- Whether the first DOM engines render from recipes at public runtime or materialise static HTML during rebuild.
- How manual decisions are remapped when edited text invalidates line or token positions.
- How engine-specific CSS is discovered and loaded without recreating the oversized shared-stylesheet problem.
- Whether switching engines retains one recipe per engine or replaces the active recipe after confirmation.
- Which commands are common workspace commands and which are engine-owned.
- Which preview isolation boundary is needed for unusually invasive engines.
- How generated image assets enter the managed media and publish workflow.
- What accessibility contract applies to interactive, animated, or data-driven composition.

## Non-Goals

- a third-party plugin system
- arbitrary module paths in route or scope config
- a general-purpose visual programming environment
- replacing the Markdown source editor for ordinary documents
- forcing every engine to serialize to Markdown
- silently publishing generated images or interactive output
- implementing every imagined algorithm before the axis workflow is usable

## Planned Focused Documents

Split this request as each boundary becomes implementation-ready:

- workspace mode, panel layout, and restoration contract
- command registry and keyboard dispatch
- composition recipe and canonical-text contract
- engine registry, lifecycle, settings, and asset loading
- word-axis editor and suggestion algorithm
- live preview and settings workspace
- DOM/static publication contract
- visualisation and generated-image output contract

Keep this parent decision-focused.
Phase checklists, file-level tasks, and verification records belong in focused child documents and should be removed when their durable outcomes have transferred to the owning architecture references.

