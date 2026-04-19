---
doc_id: dimension-visualisation-projection
title: Dimension Visualisation Projection Table
last_updated: 2026-04-16
parent_id: studio
sort_order: 250
---

# Dimension Visualisation Projection Table
Draft for linking native dimension types to shared diagrams

## Purpose

This table defines how heterogeneous portfolio dimensions may or may not be resolved into common visual forms.

The key distinction is between:

- **native representation**: the semantically correct stored form of the dimension
- **display projection**: a rule for converting native values into a visual form
- **preferred visualisation**: the chart or glyph type that best preserves meaning
- **information-loss risk**: the risk introduced when forcing a dimension into an incompatible shared diagram

This table is intended to support a later spec covering:

- UI rendering rules
- data model fields for display metadata
- rules for what can appear in a shared radar/profile diagram
- rules for when multiple coordinated diagrams are required

---

## Working assumptions

- The base data model should store dimensions in their **native semantic form**, not in whatever shape is most convenient for a radar chart.
- A **single classic radar chart** is only valid for a subset of dimensions, mainly scalar dimensions that can be meaningfully normalised onto a common outward scale.
- Some dimensions may need:
  - a different chart type
  - a derived display score
  - multiple adjacent views
  - or a hybrid summary glyph rather than a pure radar

---

## Projection table

| Dimension / property | Native representation | Radar compatible? | Projection rule if included in shared profile | Preferred visualisation | Information-loss risk if forced into classic radar | Notes |
|---|---|---:|---|---|---|---|
| Perceptual density | unipolar scalar | yes | normalise `0..5 -> 0..1` | classic radar or scalar profile | low | clean example of a radar-compatible field |
| Structural differentiation | unipolar scalar | yes | normalise `0..5 -> 0..1` | classic radar or scalar profile | low | suitable for shared formal-profile radar |
| Systemicity | unipolar scalar | yes | normalise `0..5 -> 0..1` | classic radar or scalar profile | low | one of the strongest shared-profile candidates |
| Ambiguity | unipolar scalar | yes | normalise `0..5 -> 0..1` | classic radar or scalar profile | low | works well as scalar intensity |
| Fragmentation | unipolar scalar | yes | normalise `0..5 -> 0..1` | classic radar or scalar profile | low | radar-compatible if clearly defined |
| Seriality | unipolar scalar | yes | normalise `0..5 -> 0..1` | classic radar or scalar profile | low | good candidate for formal/systemic profile |
| Manual trace | unipolar scalar | yes | normalise `0..5 -> 0..1` | classic radar or scalar profile | low | only if defined as visible/manual trace, not full process ontology |
| Semantic stability axis | bipolar scalar | conditional | either (a) map position `0..5 -> 0..1`, or (b) split into `stability` / `instability` display fields | centred bar, bipolar strip, or separate axis-family plot | medium | direct radar use is possible, but the spoke means position on a continuum, not “more of a thing” |
| Formal complexity axis | bipolar scalar | conditional | map position `0..5 -> 0..1` with explicit anchor labels retained in legend | bipolar strip, centred bar, or axis-family radar | medium | radar can work only if viewers understand low = simple, high = complex |
| Visual complexity axis | bipolar scalar | conditional | map position `0..5 -> 0..1` | bipolar strip or axis-family radar | medium | acceptable for shared profile if all axes in that chart are also bipolar-position axes |
| Systemic complexity axis | bipolar scalar | conditional | map position `0..5 -> 0..1` | bipolar strip or axis-family radar | medium | should not be mixed naively with pure presence scales unless legend is clear |
| Figurative / abstract axis | bipolar scalar | conditional | map position `0..5 -> 0..1` | centred bar, bipolar strip, or semantic-position chart | medium | better in a semantic-position panel than a formal-intensity radar |
| Organic / geometric axis | bipolar scalar | conditional | map position `0..5 -> 0..1` | centred bar or axis-family radar | medium | similar issue: it is positional, not additive |
| Openness / closure axis | bipolar scalar | conditional | map position `0..5 -> 0..1` | centred bar or semantic-position panel | medium | midpoint interpretation must be documented |
| Affective temperature axis | bipolar scalar | conditional | map position `0..5 -> 0..1` | centred bar or affective-position strip | medium | works visually, but more subjective than formal axes |
| Order / disorder axis | bipolar scalar | conditional | map position `0..5 -> 0..1` | centred bar or semantic-position panel | high | may be misleading if works can be strongly ordered and strongly chaotic simultaneously |
| Order + chaoticity | paired independent scalars | no, not as one spoke | either (a) show as two separate scalar axes, or (b) derive display measures such as `dominance` and `tension` | paired sliders, 2D point, or twin bars | high | collapsing to one spoke destroys co-presence information |
| Randomness + determinacy | paired independent scalars | no, not as one spoke | either keep as two axes or derive secondary display metrics | paired bars or 2D point | high | same issue as order/chaoticity |
| Manual trace + systemicity | paired independent scalars | no, not as one spoke | keep as two axes, or plot as point in a 2D field | 2D map or paired bars | medium | good example of a semantic field rather than a single continuum |
| Formal affect field | 2D coordinate | no, not directly | either (a) keep native `(x,y)`, or (b) derive distance-from-centre and quadrant/angle summaries | 2D map | high | direct radar inclusion loses directionality |
| Local / global legibility | bipolar scalar or 2D candidate | conditional | if bipolar, map `0..5 -> 0..1`; if dual, keep as pair | centred bar or 2D map | medium to high | depends on whether local/global really behaves as one continuum |
| Surface / encoded depth | bipolar scalar | conditional | map position `0..5 -> 0..1` | centred bar or semantic-position panel | medium | may be too interpretive for a generic radar unless well explained |
| Theme mix | compositional vector | no, not as one axis | either show each component separately, or derive concentration/diversity metrics | stacked bar, ternary plot, composition strip | high | radar can only work if components become separate spokes, which changes the meaning |
| Process mix | compositional vector | no, not as one axis | either show each component separately, or derive concentration/diversity metrics | stacked bar, composition strip, simplex/ternary if appropriate | high | best treated as composition, not scalar intensity |
| Dominant mark system | categorical | no | no scalar projection unless converted into derived indicators | label, chip, enum badge | high | categorical data should not be forced into a spoke-based profile |
| Derived visual complexity | derived scalar | yes | normalise derived result to `0..1` | radar or summary badge | medium | only valid if derivation formula is explicit and stable |
| Derived systemic complexity | derived scalar | yes | normalise derived result to `0..1` | radar or summary badge | medium | useful as summary, but not a substitute for native fields |
| Derived diversity / entropy metric | derived scalar from vector | yes | compute and normalise | radar, badge, or summary line | medium | can summarise mixtures without plotting all components |

---

## Practical visual families

The table suggests that dimensions should be grouped into **visual families** rather than all forced into one chart.

### 1. Scalar intensity family
Best suited to classic radar or scalar profile chart.

Examples:
- perceptual_density
- structural_differentiation
- systemicity
- ambiguity
- fragmentation
- seriality
- manual_trace

### 2. Bipolar position family
Best suited to centred bars, bipolar strips, or a dedicated “position” radar where all axes are explicitly positional.

Examples:
- formal_complexity_axis
- semantic_stability_axis
- figurative_abstract_axis
- organic_geometric_axis
- openness_closure_axis

### 3. Co-presence / tension family
Best suited to paired bars or 2D point maps.

Examples:
- order + chaoticity
- randomness + determinacy
- manual_trace + systemicity

### 4. Coordinate-field family
Best suited to 2D maps.

Examples:
- formal_affect_field
- any future semantic plane using x/y coordinates

### 5. Composition family
Best suited to stacked or compositional diagrams.

Examples:
- theme_mix
- process_mix

### 6. Categorical annotation family
Best suited to labels, chips, or badges.

Examples:
- dominant_mark_system

---

## Draft design implications

### A. A single classic radar chart should only be used for radar-compatible dimensions
That usually means:

- unipolar scalar dimensions
- and, only with caution, bipolar dimensions that have been explicitly projected as positional scalars

### B. There should not be one universal “master radar” by default
Instead, the system should support either:

- multiple coordinated sub-diagrams
- or a hybrid summary card made of several visual zones

### C. If bipolar dimensions are included in a radar, the chart legend must state that the values indicate **position on a continuum**, not amount of an inherently positive quantity

### D. Paired and 2D dimensions should generally keep their native structure in the display layer
If they are scalarised for summaries, the projection rule must be explicitly defined in the registry or display spec

### E. Derived display metrics are allowed, but they must not silently replace native semantics
The spec should distinguish:

- native stored value
- derived display value
- derived analytical summary

---

## Suggested next-step spec fields

A later registry/display spec should probably include fields like:

| Field | Purpose |
|---|---|
| `dimension_id` | stable identifier |
| `native_representation` | unipolar_scalar / bipolar_scalar / paired_scalar / coordinate_2d / compositional_vector / categorical / derived |
| `radar_compatible` | yes / conditional / no |
| `display_family` | scalar_intensity / bipolar_position / copresence / coordinate_field / composition / categorical |
| `projection_rule` | how native value becomes display value(s) |
| `preferred_visualisation` | radar / bipolar_strip / twin_bar / 2d_map / stacked_bar / badge |
| `information_loss_risk` | low / medium / high |
| `display_order` | placement within a chart or card |
| `display_group` | which shared diagram or summary family it belongs to |

---

## Provisional conclusion

The portfolio model should not assume that all dimensions can be honestly resolved into one classic radar chart.

Some dimensions can share a radar because they already behave like comparable scalar intensities.

Others can only appear in a common display if a **projection layer** explicitly maps their native shapes into a compatible display grammar.

So the design problem is not simply:

“Can all dimensions be converted to numbers?”

It is:

“Which dimensions can share the same visual grammar without semantic distortion, and what explicit projection rules are needed for those that cannot?”