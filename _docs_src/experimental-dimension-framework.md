---
doc_id: experimental-dimension-framework
title: Experimental Dimension Framework
last_updated: 2026-04-16
parent_id: studio
sort_order: 210
---
# Experimental Dimension Framework
Draft v1 for UI, Data Model, and Representation Testing

## Purpose

This document defines a formal working table for candidate dimension properties in the portfolio analysis system. Its purpose is not to freeze the final ontology of dimensions, but to support an experimental framework in which multiple representation types can be tested from the start.

This approach is intended to avoid repeated full rescoring passes whenever a new scale type or dimension mode is introduced. The system should therefore support multiple representational forms from the beginning, while keeping the registry, UI, and stored values structurally coherent.

## Core principle

A dimension is not just a score field. It is a representational choice about how variation in a property should be modelled.

Different properties may require different forms, including:

- unipolar scalar
- bipolar scalar
- paired independent scalars
- 2D coordinate
- compositional vector
- categorical classification
- derived profile

The registry must therefore hold representation metadata, and the UI must render controls according to that metadata.

---

## Representation types

### 1. Unipolar scalar

Measures degree of presence of a single property.

Question form:
How much of X is present?

Typical scale:
0 = none or minimal presence  
5 = dominant presence

Example:
`perceptual_density`

### 2. Bipolar scalar

Measures position between two named poles.

Question form:
Where does the work sit between A and B?

Typical scale:
0 = strongly aligned with pole A  
5 = strongly aligned with pole B

Example:
`formal_complexity_axis` with `simple <-> complex`

### 3. Paired independent scalars

Measures two potentially co-present properties separately.

Question form:
How much of X is present, and how much of Y is present?

Typical scale:
`x: 0–5`
`y: 0–5`

Example:
`order` and `chaoticity`

### 4. 2D coordinate

Represents a work as a point in a semantic field defined by two independent axes.

Question form:
Where does the work sit in relation to two interacting dimensions?

Typical structure:
`(x, y)`

Example:
`sparse <-> dense` on x-axis, `ordered <-> chaotic` on y-axis

### 5. Compositional vector

Represents proportional mixture across several components.

Question form:
What is the relative composition of this work across several factors?

Typical structure:
set of values summing to 100 or 1.0

Example:
manual / algorithmic / appropriated / chance-based process mix

### 6. Categorical classification

Represents class membership rather than scalar degree.

Question form:
Which dominant category applies?

Example:
primary mark system = line / dot / grid / field / text / fragment

### 7. Derived profile

Computed from other stored fields rather than directly scored.

Question form:
What higher-order pattern is inferred from lower-level dimensions?

Example:
`visual_complexity`
`systemic_complexity`

---

## Formal working table

| Property ID | Label | Semantic question | Candidate representation types | Preferred initial mode | Example value structure | Why this mode may fit | Key ambiguity to test | Example portfolio relevance | UI implication | Data model implication |
|---|---|---|---|---|---|---|---|---|---|---|
| `perceptual_density` | Perceptual Density | How much visual information competes for attention? | unipolar scalar | unipolar scalar | `0..5` | Clear degree-of-presence logic | Sparse but visually intense works may complicate interpretation | dense composites, sparse fields, dot grids | simple stepped slider | single numeric value |
| `structural_differentiation` | Structural Differentiation | How many distinct elements, states, or micro-variations are present? | unipolar scalar | unipolar scalar | `0..5` | Useful for visible or systemic variety | Hidden internal differentiation may not match appearance | QRNG work, layered composites, serial systems | simple stepped slider | single numeric value |
| `systemicity` | Systemicity | How strongly is the work governed by a system, rule, or procedure? | unipolar scalar | unipolar scalar | `0..5` | Strong and broadly applicable | Implicit systems in intuitive/manual works may be harder to score | sequences, grids, algorithmic or constrained works | simple stepped slider | single numeric value |
| `semantic_stability_axis` | Semantic Stability | Does the work remain referentially stable, or become unstable? | bipolar scalar | bipolar scalar | `0..5`, anchors `stable <-> unstable` | Better framed as a continuum than presence/absence | midpoint meaning must be defined carefully | image/abstraction oscillation, unstable figuration | anchored bipolar slider | single numeric value plus anchor metadata |
| `formal_complexity_axis` | Formal Complexity | Does the work sit closer to simplicity or complexity in formal organisation? | bipolar scalar, domain-specific variants | bipolar scalar for testing | `0..5`, anchors `simple <-> complex` | More interpretable than `complexity = 0` | may collapse multiple domains of complexity into one axis | composite image works, reduced systems, minimal grids | anchored bipolar slider | single numeric value plus anchor metadata |
| `visual_complexity_axis` | Visual Complexity | Does the work appear visually simple or visually complex? | bipolar scalar, unipolar scalar | bipolar scalar | `0..5`, anchors `simple <-> complex` | Useful for visible surface-level reading | may overlap with density and differentiation | composites vs sparse prints | anchored bipolar slider | single numeric value plus anchor metadata |
| `systemic_complexity_axis` | Systemic Complexity | Is the underlying system or procedure simple or complex? | bipolar scalar | bipolar scalar | `0..5`, anchors `simple <-> complex` | Useful where visual austerity hides procedural complexity | may require process knowledge not visible in the work alone | QRNG dot grid, rule-based works | anchored bipolar slider with help text | single numeric value plus anchor metadata |
| `order_disorder_axis` | Order/Disorder | Is the dominant character more ordered or more chaotic? | bipolar scalar, paired scalars | bipolar scalar for testing | `0..5`, anchors `ordered <-> chaotic` | Strong intuitive anchors | many works may contain both strongly | grids with disturbance, constrained composites | anchored bipolar slider | single numeric value plus anchor metadata |
| `order` + `chaoticity` | Order and Chaoticity | How much order is present, and how much chaos is present? | paired independent scalars | paired scalars for testing | `{ "order": 0..5, "chaoticity": 0..5 }` | Better if both forces can coexist | more complex to compare than one slider | works where system and noise are both central | two linked sliders or 2D point option | pair of numeric values |
| `figurative_abstract_axis` | Figurative/Abstract | Does the work sit closer to figuration or abstraction? | bipolar scalar | bipolar scalar | `0..5`, anchors `figurative <-> abstract` | Familiar and intuitive continuum | some works may be strongly both or unstable | portrait-derived composites, reduced images | anchored bipolar slider | single numeric value plus anchor metadata |
| `manual_trace` | Manual Trace | How strongly does manual mark-making or touch register in the work? | unipolar scalar | unipolar scalar | `0..5` | Clear degree property | must distinguish visible trace from production method | drawings, manipulated images, composite works | simple stepped slider | single numeric value |
| `manual_systemic_field` | Manual/Systemic Relation | What is the relation between manual trace and systemic organisation? | paired scalars, 2D coordinate | paired scalars initially, 2D later | `{ "manual_trace": 0..5, "systemicity": 0..5 }` | Strong presence of both may matter more than a continuum | one bipolar line may be too reductive | rule-based drawings, manually executed systems | two sliders, optionally plotted in 2D | pair of numeric values or derived point |
| `random_determined_axis` | Random/Determined | Is the work more driven by chance or by determination? | bipolar scalar, paired scalars | bipolar scalar for testing | `0..5`, anchors `random <-> determined` | Intuitive starting point | many works may combine chance and control | QRNG works, procedural composites, chance operations | anchored bipolar slider | single numeric value plus anchor metadata |
| `randomness` + `determinacy` | Randomness and Determinacy | How much randomness is present, and how much determinacy is present? | paired independent scalars | paired scalars for testing | `{ "randomness": 0..5, "determinacy": 0..5 }` | Better if both co-exist materially or conceptually | may be harder for raters at first | chance-within-system works | two linked sliders | pair of numeric values |
| `openness_closure_axis` | Openness/Closure | Does the work feel open-ended or resolved/closed? | bipolar scalar | bipolar scalar | `0..5`, anchors `closed <-> open` | Useful interpretive field | may mix formal, semantic, and experiential meanings | evolving systems, unresolved abstractions | anchored bipolar slider | single numeric value plus anchor metadata |
| `ambiguity` | Ambiguity | How strongly does the work resist singular interpretation? | unipolar scalar | unipolar scalar | `0..5` | Good presence scale | overlap risk with semantic instability | unstable subject matter, symbolic works | simple stepped slider | single numeric value |
| `fragmentation` | Fragmentation | How strongly is the work constituted by broken, discontinuous, or segmented structure? | unipolar scalar | unipolar scalar | `0..5` | Clear descriptive property | may overlap with density or instability | destructively transformed composites, segmented image works | simple stepped slider | single numeric value |
| `seriality` | Seriality / Repetition | How strongly does repetition or serial logic organise the work? | unipolar scalar | unipolar scalar | `0..5` | Strong and broadly useful | visible repetition vs conceptual seriality must be distinguished | grids, repeated marks, sequences | simple stepped slider | single numeric value |
| `organic_geometric_axis` | Organic/Geometric | Does the work sit closer to organic or geometric form? | bipolar scalar | bipolar scalar | `0..5`, anchors `organic <-> geometric` | Strong visual anchors | some works contain both in different layers | curve drawings, grids, structured abstractions | anchored bipolar slider | single numeric value plus anchor metadata |
| `legibility_scale_axis` | Local/Global Legibility | Is structure grasped immediately at local scale or mainly through aggregation/global scale? | bipolar scalar, 2D coordinate | bipolar scalar for testing | `0..5`, anchors `local <-> global` | Useful for scale-dependent perception | may really require separate local/global scores | dot grids, large fields, large composites | anchored bipolar slider with explanatory text | single numeric value plus anchor metadata |
| `surface_encoded_axis` | Surface/Encoded Depth | Is meaning carried mainly by visible surface or underlying encoded structure? | bipolar scalar, paired scalars | bipolar scalar for testing | `0..5`, anchors `surface-led <-> encoded-system-led` | Good for contrasting minimal surface with conceptual depth | may become too interpretive without guidance | QRNG work, data-derived images | anchored bipolar slider with help text | single numeric value plus anchor metadata |
| `affective_temperature_axis` | Affective Temperature | Does the work feel cold, neutral, or hot/intense? | bipolar scalar, centred signed scale | bipolar scalar initially | `0..5`, anchors `cold <-> hot` | Intuitive phenomenological continuum | culturally and subjectively variable | austere systems vs charged composites | anchored bipolar slider | single numeric value plus anchor metadata |
| `theme_mix` | Theme Composition | What is the relative thematic composition of the work? | compositional vector | later experiment | `{ "memory": 0.4, "system": 0.35, "media": 0.25 }` | Better than forcing a single dominant theme | high scoring burden and lower consistency | later-stage thematic synthesis | multi-value editor with sum validation | vector of weighted values |
| `process_mix` | Process Composition | What is the process mixture in the work? | compositional vector | later experiment | `{ "manual": 0.3, "algorithmic": 0.5, "appropriated": 0.2 }` | Good for hybrid production methods | burdensome at early stage | mixed-process works | multi-value editor with sum validation | vector of weighted values |
| `formal_affect_field` | Formal Affect Field | Where does the work sit in a two-axis semantic field? | 2D coordinate | later experiment, design now | `{ "x": value, "y": value }` with defined axis anchors | Useful where quadrants are meaningful | requires careful choice of axes | e.g. `sparse <-> dense` × `ordered <-> chaotic` | point-on-plane UI | coordinate pair |
| `dominant_mark_system` | Dominant Mark System | What primary mark or structuring system dominates? | categorical classification | later, optional | one-of enum | Some properties are better classified than scaled | may oversimplify mixed works | line, dot, grid, field, fragment | dropdown or chip selector | enum / category |

---

## Recommended experimental priority

### v1 active experiment set

These are the strongest candidates for immediate testing across series because they cover several representation types without excessive UI burden.

| Property ID | Preferred initial mode | Priority |
|---|---|---|
| `perceptual_density` | unipolar scalar | active |
| `structural_differentiation` | unipolar scalar | active |
| `systemicity` | unipolar scalar | active |
| `semantic_stability_axis` | bipolar scalar | active |
| `formal_complexity_axis` | bipolar scalar | active test |
| `order_disorder_axis` | bipolar scalar | active test |
| `figurative_abstract_axis` | bipolar scalar | active test |
| `manual_trace` | unipolar scalar | active |
| `ambiguity` | unipolar scalar | active |
| `fragmentation` | unipolar scalar | active |
| `seriality` | unipolar scalar | active |
| `organic_geometric_axis` | bipolar scalar | active test |

### v1 comparative test set

These should be available from the start where needed, because they test whether some apparently bipolar concepts are better represented as co-present forces or coordinate fields.

| Property ID | Preferred initial mode | Priority |
|---|---|---|
| `order` + `chaoticity` | paired independent scalars | comparative test |
| `randomness` + `determinacy` | paired independent scalars | comparative test |
| `manual_systemic_field` | paired scalars, later 2D view | comparative test |
| `formal_affect_field` | 2D coordinate | exploratory test |

### later-stage extensions

| Property ID | Preferred initial mode | Priority |
|---|---|---|
| `theme_mix` | compositional vector | later |
| `process_mix` | compositional vector | later |
| `dominant_mark_system` | categorical classification | later |

---

## Spec implications for the UI

The UI should not assume that every dimension is a simple single numeric slider. It should render controls from registry metadata.

### Minimum UI control types required from the start

1. Unipolar stepped slider  
   For dimensions such as `perceptual_density`, `systemicity`, `ambiguity`

2. Bipolar anchored slider  
   For dimensions such as `formal_complexity_axis`, `semantic_stability_axis`, `figurative_abstract_axis`

3. Paired scalar editor  
   For dimensions such as `order` + `chaoticity`, `randomness` + `determinacy`

4. Optional 2D plotting view  
   Not necessarily required for first data entry, but should be anticipated in the spec for later visualisation and comparison

### UI guidance requirement

Each dimension should display:

- label
- semantic question
- representation type
- anchors or scale labels
- short scoring guidance
- score state control: scored / unscored / not applicable

### Null-state handling in the UI

The UI should distinguish:

- scored value
- unscored
- not applicable

A score of `0` must always be treated as a real score, never as a blank or skipped field.

---

## Spec implications for the data model

The data model should be registry-driven and polymorphic at the representation layer.

### Registry-level requirement

Each dimension definition should include metadata such as:

| Field | Purpose |
|---|---|
| `dimension_id` | stable identifier |
| `label` | display name |
| `semantic_question` | what the dimension asks |
| `representation_type` | unipolar_scalar, bipolar_scalar, paired_scalar, coordinate_2d, compositional_vector, categorical, derived |
| `anchors` | min/max labels, axis labels, or component labels |
| `status` | candidate, active, derived, deprecated |
| `scope` | global, subset, experimental |
| `scoring_guidance` | short interpretation help |
| `null_policy` | rules for scored / unscored / not_applicable |
| `value_schema` | expected storage shape |

### Work-level data implication

Work records should not hard-code one single field shape for every dimension. Instead, values should be stored in a way compatible with the registry.

At minimum, the model should support:

- single numeric value
- numeric pair
- coordinate pair
- weighted vector
- category value

---

## Provisional design principle

The base system should support multiple dimension representations from the start, even if only a subset is heavily used at first.

This is necessary because the portfolio review process is itself exploratory. The system should therefore support comparison between representation modes without requiring repeated schema redesign or repeated full rescoring.

The point of v1 is not to decide the final best model in advance. The point is to create a structured environment in which different semantic representations can be tested against real series.

---

## Next step

The next document should define:

1. a registry schema for dimension definitions
2. a work-level value schema for storing different representation types
3. UI rendering rules linking `representation_type` to control type
4. scoring-state rules for `0`, `null`, and `not_applicable`
5. promotion rules for moving experimental dimensions toward stable active status