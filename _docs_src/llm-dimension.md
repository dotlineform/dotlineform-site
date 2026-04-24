---
doc_id: llm-dimension
title: "LLM-Assisted Dimension Recommendation"
added_date: 2026-04-16
last_updated: 2026-04-16
parent_id: llm
sort_order: 10
---
# LLM-Assisted Dimension Recommendation
Draft workflow note for semantic support in portfolio scoring

## Purpose

This note defines a formal role for LLM assistance in the portfolio scoring system.

The aim is to use an LLM where it is strongest:

- semantic interpretation
- relation between visual qualities and conceptual vocabulary
- distinction between nearby terms
- recommendation of relevant dimensions and tags
- detection of semantic strain in the current model

This note does **not** propose that the LLM becomes the canonical scorer. Instead, it should function as an interpretive assistant that supports human review and model development.

---

## Why LLM support is relevant here

Some scoring decisions are not primarily computational or purely visual. They depend on semantic judgement.

Examples include:

- whether a work is better described through `visual_complexity_axis` or `systemic_complexity_axis`
- whether `order_disorder_axis` is adequate, or whether `order` and `chaoticity` should be treated as co-present
- whether a work activates `surface_encoded_axis`
- whether a term such as “complexity” is functioning as a tag, a dimension, or a source of model strain

These are questions about meaning, interpretation, and relations between concepts.

An LLM is useful here because it can combine:

- visual description
- short production descriptions
- semantic comparison between candidate dimensions
- explanation of why one representation may fit better than another

---

## Core principle

LLM output should be **advisory**, not **authoritative**.

The LLM should propose, explain, and justify candidate dimensions, tags, and notes. The human scorer should remain responsible for accepting, rejecting, editing, or ignoring those suggestions.

The system should treat LLM assistance as:

- semantic support for scoring
- semantic support for registry refinement
- semantic support for governance and model evolution

It should **not** treat LLM output as automatically final truth.

---

## Main use case

### Input
- one or more images of a work
- short description of production method
- optional title, series, tags, or context text
- optional existing dimension/taxonomy registry

### Output
- recommended base dimensions
- recommended selectable dimensions
- dimensions probably not useful here
- possible candidate tags
- semantic notes and caveats
- confidence indicators
- warnings about semantic overlap or ambiguity
- possible registry strain signals

### Example use case from current discussions

#### Example 1: composite image built from many transformed Kylie Minogue photographs

Likely outputs:
- recommend `perceptual_density`
- recommend `structural_differentiation`
- recommend `ambiguity`
- recommend `fragmentation`
- suggest `formal_complexity_axis`
- suggest `figurative_abstract_axis`
- note that complexity appears primarily visual, layered, and semantically unstable

#### Example 2: grid of tiny black/white dots derived from a quantum random binary sequence

Likely outputs:
- recommend `systemicity`
- recommend `structural_differentiation`
- suggest `systemic_complexity_axis`
- suggest `surface_encoded_axis`
- suggest `random_determined_axis`
- note that complexity appears encoded/systemic rather than visually dense

---

## Recommended LLM roles

### 1. Dimension recommendation

The LLM identifies which dimensions are likely relevant to the work and explains why.

Example:
- `perceptual_density` recommended because the work contains many competing visual fragments
- `systemic_complexity_axis` recommended because the work’s complexity lies in procedure or encoded structure rather than visible density

### 2. Semantic disambiguation

The LLM helps distinguish between nearby dimensions or terms.

Examples:
- `visual_complexity_axis` vs `systemic_complexity_axis`
- `ambiguity` vs `semantic_stability_axis`
- `order_disorder_axis` vs `order` + `chaoticity`
- `random_determined_axis` vs `randomness` + `determinacy`

### 3. Dimension-shape advice

The LLM may suggest whether a concept appears to behave more like:

- a unipolar scalar
- a bipolar scalar
- paired co-present forces
- a field relation
- a compositional mix

This is useful when deciding whether a dimension’s current representation type is semantically appropriate.

### 4. Tag suggestion

The LLM may propose likely tags separately from dimensions.

This is important because:
- tags answer what is in play
- dimensions answer how something is realised or to what degree it is present

### 5. Registry strain detection

The LLM may identify repeated semantic patterns that suggest the current registry is under strain.

Examples:
- repeated notes about hidden structure vs visible austerity
- repeated confusion around complexity, chaos, and density
- repeated need to distinguish co-presence from single-axis polarity

These outputs can support later governance decisions.

### 6. Series-level synthesis

After several works in a series have been reviewed, the LLM may help summarise:

- recurring dimensions
- recurring tags
- unstable dimensions
- likely recommended dimension sets for the series
- possible candidates for promotion/demotion in tiering

---

## Recommended workflow

### Step 1. Human provides source material
The system receives:
- work image(s)
- short production description
- optional context

### Step 2. LLM produces structured recommendations
The system calls an LLM and requests:
- candidate dimensions
- candidate tags
- reasoning
- confidence
- caveats
- possible non-recommendations

### Step 3. UI presents advisory suggestions
The UI displays:
- recommended dimensions
- suggested tags
- reasons
- optional warnings or caveats

The user can then:
- accept
- reject
- edit
- ignore

### Step 4. Human completes scoring
The human scorer remains the final decision-maker.

### Step 5. Optional recommendation trace is stored
The system may optionally store:
- LLM recommendation payload
- timestamp
- model/version
- accepted/rejected suggestions

This can later support audit, registry refinement, and prompt improvement.

---

## Suggested output structure

A structured machine-readable output is strongly preferable.

Example shape:

```json
{
  "recommended_base_dimensions": [
    {
      "dimension_id": "perceptual_density",
      "reason": "The work contains many competing visual fragments and a crowded image field.",
      "confidence": 0.92
    }
  ],
  "recommended_selectable_dimensions": [
    {
      "dimension_id": "formal_complexity_axis",
      "reason": "The work appears strongly weighted toward formal complexity rather than simplicity.",
      "confidence": 0.87
    }
  ],
  "not_recommended_dimensions": [
    {
      "dimension_id": "organic_geometric_axis",
      "reason": "This contrast does not appear central to the work's dominant structure.",
      "confidence": 0.61
    }
  ],
  "candidate_tags": [
    {
      "tag_id": "theme:complexity",
      "reason": "Complexity appears to be a central conceptual concern.",
      "confidence": 0.94
    },
    {
      "tag_id": "form:fragmentation",
      "reason": "The work appears composed through discontinuous, layered image parts.",
      "confidence": 0.90
    }
  ],
  "semantic_notes": [
    "Complexity appears primarily visual and fragmentary rather than encoded/systemic."
  ],
  "registry_strain_signals": [
    "This work may require clearer distinction between visual complexity and systemic complexity."
  ]
}

This structure is only illustrative, but the output should clearly separate:

- recommendations
- non-recommendations
- notes
- strain signals

## Recommended UI behaviour

LLM suggestions should appear as **proposals**, not as already-applied scores.

The UI might show sections such as:

- Suggested base dimensions
- Suggested additional dimensions
- Suggested tags
- Semantic notes
- Cautions / possible ambiguity

Each suggestion should include:

- label
- short explanation
- confidence indicator if used
- accept / dismiss / edit action

The user should remain able to proceed without accepting any suggestion.

## Relationship to scoring architecture

This note fits the registry-driven scoring architecture already defined.

The LLM does not replace the registry. It operates within it.

The registry remains the source of truth for:

- dimension definitions
- representation types
- preferred input controls
- tier status
- display/analytics metadata

The LLM helps choose among available dimensions and tags, and may identify where the registry itself needs refinement.

In compact form:

- registry defines the language
- LLM helps navigate the language
- human makes the decision

## Relationship to governance

LLM outputs may also support model governance.

Repeated recommendation patterns may reveal:

- dimensions that should become recommended for certain series
- dimensions that should be promoted or demoted between tiers
- dimensions that may be redundant or unclear
- candidate new dimensions
- repeated note patterns suggesting glossary refinement

This makes the LLM useful not only for scoring support, but also for evolution of the model.

## Important caution

LLM recommendations are probabilistic and language-sensitive. They may reflect plausible semantic fits rather than ground truth.

Risks include:

- overconfident but weakly grounded suggestions
- semantic drift across prompts or model versions
- tendency to over-generalise from conceptual language
- confusing presence of a theme with suitability of a dimension
- recommending dimensions that sound right linguistically but are poor operational fits

For this reason:

- recommendations should remain advisory
- human review must remain central
- prompt design and structured outputs matter
- recommendation traces should be inspectable where possible

## Example interpretation from current discussions

### Kylie composite example

**Input:**

- image of layered composite portrait built from many transformed source photos
- short note about repeated destructive transformations and compositing

**Likely LLM recommendation:**

- base: `perceptual_density`, `structural_differentiation`, `ambiguity`
- selectable: `formal_complexity_axis`, `figurative_abstract_axis`, `fragmentation`, `semantic_stability_axis`
- tags: `theme:complexity`, `form:composite`, `form:fragmentation`, `process:destructive-transformation`
- note: complexity appears primarily visual, layered, and semantically unstable

### QRNG dot-grid example

**Input:**

- image of large field/grid of very small black/white dots
- short note explaining binary sequence from a quantum random number generator

**Likely LLM recommendation:**

- base: `systemicity`, `structural_differentiation`
- selectable: `systemic_complexity_axis`, `surface_encoded_axis`, `random_determined_axis`, `seriality`
- tags: `theme:complexity`, `theme:randomness`, `theme:information`, `form:grid`
- note: complexity appears encoded and procedural rather than visually dense

## Policy summary

LLM assistance is appropriate where scoring depends on semantics, interpretation, and relations between candidate concepts rather than on simple visual recognition alone.

The preferred role of the LLM is to:

- recommend
- explain
- compare
- caution
- detect registry strain

It should not silently assign canonical scores.

## Short policy version

LLM assistance may be used to generate structured recommendations for dimensions, tags, and semantic notes from images and production descriptions. These recommendations are advisory. They should support human scoring, registry refinement, and detection of semantic strain, rather than acting as canonical scores.

## Next step

The next document should define either:

1. the API-facing request/response schema for LLM-assisted recommendation  
2. the prompt design and orchestration workflow for combining image analysis, registry lookup, and structured semantic recommendation
