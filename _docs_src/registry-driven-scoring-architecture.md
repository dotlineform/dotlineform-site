---
doc_id: registry-driven-scoring-architecture
title: Registry-Driven Scoring Architecture
last_updated: 2026-04-16
parent_id: studio
sort_order: 200
---
# Registry-Driven Scoring Architecture
Draft design note for semantic-to-UI mapping

## Purpose

This note defines the architectural principle that links dimension meaning, data shape, scoring interface, and analytics.

The goal is to avoid a system in which the user is asked to choose a scoring shape at the point of tagging. Instead, each dimension should already carry a semantically justified native representation, from which the preferred UI and analytical treatment are derived.

This supports consistency in scoring, reduces cognitive burden during review, and allows the model to evolve in a controlled way through the registry rather than through ad hoc choices in the scoring session.

---

## Core principle

A dimension is defined first by its semantics, then by its native representation. The scoring UI is derived from that representation, not chosen ad hoc by the user. Analytics should preserve native representations where possible, with simplified views, projections, and composites treated as secondary analytical layers.

In compact form:

**semantics -> native representation -> preferred scoring UI -> analytics and display projections**

---

## Why this principle is needed

An exploratory portfolio model naturally produces many candidate dimensions and many possible scoring shapes. If all representation choices are exposed directly to the user at scoring time, several problems follow:

- inconsistent scoring across sessions
- hidden ontology changes during review
- increased cognitive burden
- poor comparability across works and series
- unstable analytics because data shape varies arbitrarily

For this reason, the system should not function as a toolbox of interchangeable scoring widgets.

Instead, it should function as a curated interpretive system in which:

- each dimension has a declared semantic type
- that semantic type implies a native data shape
- the native data shape implies a preferred input control
- the resulting data shape informs the appropriate analytics and visualisations

Experimentation remains possible, but it happens at the registry/spec level rather than through ad hoc interface choices during tagging.

---

## Architectural layers

The model can be understood as four linked layers.

### 1. Semantic layer

Defines what the dimension means.

This includes:

- label
- semantic question
- interpretation scope
- scoring guidance
- anchor meanings if bipolar
- distinction from nearby dimensions

Examples:

- `perceptual_density` asks how much visual information competes for attention
- `formal_complexity_axis` asks where the work sits between simplicity and complexity in formal organisation
- `order` and `chaoticity` may be treated as co-present forces rather than one continuum

The semantic layer is primary. All downstream choices should follow from it.

### 2. Representation layer

Defines the native data shape that best expresses the semantic claim of the dimension.

Possible native representations include:

- unipolar scalar
- bipolar scalar
- paired independent scalars
- 2D coordinate
- compositional vector
- categorical classification
- derived field

The representation layer should not be selected for UI convenience alone. It is part of the meaning of the dimension.

Examples:

- a presence-like property tends toward unipolar scalar
- a continuum-like property tends toward bipolar scalar
- co-present forces tend toward paired scalars
- field-like relations tend toward 2D coordinates
- mixtures tend toward compositional vectors

### 3. Interaction layer

Defines the preferred scoring UI for the chosen native representation.

The user should normally not choose this representation interactively. The interface should be rendered from registry metadata.

Typical mappings:

- unipolar scalar -> stepped slider
- bipolar scalar -> anchored bipolar slider
- paired scalars -> paired sliders or dual-value editor
- 2D coordinate -> point picker or coordinate plane
- compositional vector -> weighted composition editor
- categorical classification -> dropdown, chips, or enum selector

The interaction layer should be curated and declarative.

### 4. Analytics and display layer

Defines how native values are analysed, compared, and visualised.

This layer should preserve native form first, and only then allow derived display projections such as:

- classic radar charts for compatible scalar families
- bipolar strips or centred bars for positional axes
- 2D maps for coordinate fields or co-presence pairs
- stacked bars for compositional vectors
- hybrid summary cards composed of multiple visual zones
- derived scalar summaries such as visual or systemic complexity

Analytics should not flatten native representations too early.

---

## Main design rule

The user should score the dimension through the interface that best matches the declared semantics of that dimension.

The user should **not** normally be asked:

- whether a dimension should be unipolar or bipolar
- whether a pair should be entered as a point or as two sliders
- whether a dimension should be projected into a radar-friendly form

Those are registry-level decisions, not day-to-day scoring decisions.

---

## Controlled experimentation model

This architecture still supports experimentation, but in a governed way.

The experimental unit is not:
“which widget shall I choose right now?”

The experimental unit is:
“is this dimension correctly specified in meaning, representation, and scoring interface?”

That means candidate and experimental dimensions may still exist, but each should already declare:

- its semantic intention
- its provisional native representation
- its preferred scoring UI
- its analytical family

This allows real testing without allowing arbitrary scoring inconsistency.

---

## Practical implications for the registry

The dimension registry should become the authoritative source of truth linking semantics, representation, UI, and analytics.

A dimension definition should therefore include fields such as:

| Field | Purpose |
|---|---|
| `dimension_id` | stable identifier |
| `label` | display name |
| `semantic_question` | what the dimension asks |
| `semantic_notes` | scope, caveats, exclusions |
| `native_representation` | unipolar_scalar / bipolar_scalar / paired_scalar / coordinate_2d / compositional_vector / categorical / derived |
| `preferred_input_control` | slider / anchored_slider / paired_slider / point_picker / composition_editor / select |
| `anchors` | labels for poles or axis ends where relevant |
| `value_schema` | expected storage shape |
| `analytics_family` | scalar_intensity / bipolar_position / copresence / coordinate_field / composition / categorical |
| `projection_options` | optional derived simplifications for display |
| `status` | candidate / experimental / active / derived / deprecated |
| `null_policy` | scored / unscored / not_applicable handling |
| `scoring_guidance` | short user-facing interpretation help |

This registry-driven structure prevents the UI and analytics from diverging from the semantic definition.

---

## Practical implications for the scoring UI

The scoring interface should be curated, not open-ended.

For each dimension, the UI should render:

- label
- semantic question
- scale anchors or value labels where needed
- short scoring guidance
- appropriate control type based on native representation
- state control for `scored`, `unscored`, and `not_applicable`

The UI should not expose a general “choose scoring mode” option for normal use.

Possible future admin or design tools may allow registry editing, but that is a different layer of the system.

---

## Practical implications for analytics

Analytics should operate on native representations where possible.

Examples:

- a unipolar scalar should remain a scalar
- a bipolar scalar should remain a position on a continuum
- paired scalars should preserve co-presence
- 2D coordinates should preserve field position
- compositional vectors should preserve mixture structure

Only after native analysis should the system derive simplified comparative views such as:

- profile radars
- summary badges
- composite scores
- clustered families
- display projections

This preserves semantic fidelity while still allowing simplification for overview and communication.

---

## Relationship to shared diagrams

This architecture also clarifies how shared diagrams should be handled.

A single diagram should not be assumed to be the natural endpoint for all dimensions.

Instead:

- some dimensions are naturally compatible with a shared scalar profile
- some fit a shared positional panel
- some require paired or field-based displays
- some are best displayed as composition or categorical annotation
- some may be projected into summary views only through explicit display rules

The visualisation layer must therefore be registry-aware, not generic.

---

## Summary statement

The portfolio scoring system should be **registry-driven** rather than **widget-driven**.

This means:

- the semantics of the dimension determine the native data shape
- the native data shape determines the preferred scoring UI
- the scoring UI should be curated and rendered automatically
- analytics should preserve native form first
- simplified views and composites should be treated as secondary projections

This is the preferred architecture because it supports both experimental development and scoring consistency without collapsing semantics into arbitrary interface choice.

---

## Short policy version

Use this version where a compact statement is needed:

> Dimension semantics determine native representation. Native representation determines preferred scoring UI. Users should score through curated controls derived from the registry, not by selecting representation type ad hoc. Analytics should preserve native representation first and derive simplified comparative views second.

---

## Next step

The next document should specify the actual registry schema and work-level value schema needed to implement this architecture, including:

1. dimension definition fields
2. native value storage formats
3. UI control mapping rules
4. null-state handling
5. projection/display metadata