---
doc_id: site-request-moments-composition-workspace-roadmap
title: Moments Composition Workspace Roadmap
added_date: 2026-07-12
last_updated: 2026-07-12
ui_status: proposed
parent_id: site-request-moments-composition-workspace
viewable: true
summary: Vertical roadmap from the first Moments word-axis editor through a reusable composition workspace, multiple engines, data visualisation, and complex generative output.
---
# Moments Composition Workspace Roadmap

Status: proposed

## Purpose

Sequence the [Moments Composition Workspace](/docs/?scope=studio&doc=site-request-moments-composition-workspace) from one small useful editor into a broader visual-composition environment without building an unused framework in advance.

Every phase should follow the same rhythm:

1. make the smallest shared refactor needed by the vertical feature
2. implement a complete usable feature
3. review the assumptions it exposed
4. refactor the now-proven ownership boundary
5. update the parent request and current architecture owner

Create a focused child request or task tracker only when a phase is ready to implement.

## Roadmap

| phase | usable outcome | architecture exercised |
| --- | --- | --- |
| 0. Visual proof | one authored Moment demonstrates the word-axis effect | scope-owned Moments CSS and portable `/moments/` plus `/docs/` presentation |
| 1. Basic axis editor | select an axis word, suggest line splits, apply and undo | source selection/range adapter, pure transformation model, commands inside an editable surface |
| 2. Composition workspace | plain-text editor and live axis preview with settings | document-mode layout intent, index restoration, internal split preview, info-panel settings |
| 3. Multiple engines | switch between axis and a seeded scatter engine | engine registry, lifecycle, settings projection, scoped assets, deterministic state |
| 4. Durable recipes and publication | save and reproduce DOM or static-HTML compositions | canonical text/recipe/output separation, stale-decision handling, public runtime or materialisation contract |
| 5. Data visualisation | map text or structured inputs into SVG, canvas, or interactive views | data adapters, visual scales, accessibility, responsive preview, richer engine settings |
| 6. Image output | generate and publish a visual artifact while retaining text | browser export, media metadata, asset containment, transcript and fallback behavior |
| 7. Complex composition | support spatial, animated, physical, or hybrid generative algorithms | performance budgets, isolation, reproducibility, advanced commands, output-specific limits |

## Phase 0: Visual Proof

Current proof:

- `moment-text` uses Moments prose typography in both public and management viewers
- `moment-text--axis` aligns manually split lines around a configurable percentage
- titles and dates can opt into the same reusable axis line
- narrow screens fall back to flowing text

This phase proves the visual idea only.
The authored spans are not the permanent multi-engine data model.

Completion state: complete as an experiment.

## Phase 1: Basic Axis Editor

Deliver the smallest editor assistance before introducing a full workspace.

Outcome:

- select a word and set it as the axis word for its source line
- run a measured-width suggestion across a block
- preserve blank-line groups
- correct a previous choice by selecting another word
- apply the change as one undoable action
- invoke the same operation by toolbar control and keyboard command

Architecture work should be limited to:

- complete-source and replace-range methods on the active source-editor adapter
- a pure axis analysis/recipe module
- command registration and editable-focus key handling
- direct Moments scope eligibility for the controls

Decision gate:

- choose the minimum recipe persistence shape before the editor permanently writes algorithm-specific markup

## Phase 2: Composition Workspace

Promote axis editing into a coordinated document mode.

Outcome:

- entering composition mode transiently hides the index
- the main workspace presents plain text and a live axis preview
- the info panel presents axis percentage and suggestion settings
- preview updates do not require rebuild or canonical save
- leaving restores prior panel state
- Apply and Save have explicit, separate meanings

Architecture work:

- mode-owned workspace layout intent
- transient panel-state restoration
- workspace-owned internal editor/preview split
- mode-owned default info view
- shared command dispatch for buttons and shortcuts

Decision gate:

- define which state is an unsaved workspace draft, which is a saved recipe, and which is derived preview output

## Phase 3: Multiple Engines

Add a deliberately contrasting second engine soon after axis.

Suggested proof engine:

- seeded scattering of words within a bounded preview
- adjustable density, displacement, rotation, or clustering
- deterministic rerendering from the same text, settings, and seed

Outcome:

- switch engines without changing the workspace shell
- unmount and clean up the previous preview
- project the new engine's settings and commands
- load only the engine assets needed by the active composition
- retain, discard, or convert prior engine state through an explicit choice

Decision gate:

- no workspace-shell branching on known engine ids
- no engine CSS added to the shared Docs Viewer stylesheet merely because loading ownership is unclear

## Phase 4: Durable Recipes And Publication

Make compositions reproducible beyond the current editing session.

Outcome:

- save engine id, version, settings, seed, and manual decisions
- detect when edited canonical text makes decisions stale
- rebuild the same composition deterministically
- render supported DOM or static-HTML engines on the public Moments route
- preserve plain text as the non-composed fallback

Decision gate:

- choose recipe storage and package/export behavior
- decide public runtime rendering versus rebuild-time materialisation for each supported output capability

## Phase 5: Data Visualisation

Allow engines to consume structured values as well as text tokens.

Possible first experiments:

- word frequency, rhythm, line length, or repeated-phrase maps
- timelines using Moment dates or authored sequence
- relationship or semantic-reference diagrams
- text positioned by numeric values rather than typographic flow

Outcome:

- an engine declares the data shape it accepts
- the workspace provides validated data without coupling the shell to one visualisation library
- SVG or canvas previews remain responsive and keyboard-accessible where interaction is exposed
- the plain-text or tabular meaning remains available as an accessible alternative

Decision gate:

- distinguish general composition inputs from domain-specific data adapters

## Phase 6: Image Output

Support compositions whose intended publication form is an image.

Outcome:

- generate a deterministic SVG or raster artifact in the browser
- preview the exact intended dimensions
- retain canonical text and composition recipe
- provide alt text or a transcript
- use an explicit manual asset step first if managed asset persistence is not yet justified

Decision gate:

- define the narrow generated-asset write, containment, metadata, replacement, and publish contract before automatic persistence

## Phase 7: Complex Composition

Open the engine boundary to more demanding first-party experiments without weakening the shell contract.

Possible directions:

- animated or time-based typography
- particle or force-directed word placement
- procedural paths and shapes
- layered text, image, and data compositions
- deterministic randomness with editable constraints
- hybrid DOM, SVG, canvas, audio, or image output

Architecture concerns become engine capabilities rather than assumptions applied to every workspace:

- animation and rendering performance budgets
- pause, reduced-motion, and non-animated fallbacks
- stronger CSS or DOM isolation where proven necessary
- large-document preview strategies
- output-specific undo, export, and publication limits

## Roadmap Completion

This roadmap is not complete merely because an abstract engine API exists.
It is complete when several materially different composition engines can use the same workspace, settings, command, recipe, preview, and output boundaries without feature-specific edits throughout the application shell.

Remove completed phase task detail after durable behavior has moved into current owner documents.
Keep this roadmap focused on the next meaningful vertical outcomes.

