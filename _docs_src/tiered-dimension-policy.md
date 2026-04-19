---
doc_id: tiered-dimension-policy
title: "Tiered Dimension Policy"
last_updated: 2026-04-16
parent_id: studio
sort_order: 270
---
# Tiered Dimension Policy
Draft policy note for base, selectable, and experimental dimensions

## Purpose

This note defines a tiered policy for dimension availability in the portfolio scoring UI.

The aim is to balance three competing needs:

- **consistency** across the portfolio
- **flexibility** for different kinds of work and series
- **controlled experimentation** as the model evolves

The system should not present one undifferentiated list of all possible dimensions. Nor should it require the user to score every possible dimension for every work. Instead, dimensions should be organised into tiers that reflect their role in the model.

This tiering should help the user understand:

- which dimensions form the core comparative layer
- which dimensions are relevant only in some contexts
- which dimensions remain under active testing or development

---

## Core principle

A dimension should not be shown or required in the same way merely because it exists in the registry.

Dimensions should be assigned a **usage tier** according to:

- breadth of applicability across the portfolio
- semantic stability
- scoring reliability
- analytical usefulness
- maturity of definition and representation

The scoring UI should be driven by this tiering.

---

## The three main tiers

### 1. Base dimensions

Base dimensions form the minimal comparative backbone of the portfolio model.

These are dimensions that are expected to be useful across most or all works or series. They should be shown by default in the scoring UI.

Base dimensions should usually be:

- broadly applicable across the portfolio
- semantically stable
- relatively low-friction to score
- useful for cross-series comparison
- unlikely to be `not_applicable` in most cases

Base dimensions are **required for review workflow**, but this does **not** mean they must always receive a numeric score.

Instead, each base dimension must be explicitly resolved as one of:

- `scored`
- `unscored`
- `not_applicable`

This ensures consistent review coverage without forcing false precision.

#### Examples of likely base dimensions

Based on current discussions, these are plausible base candidates:

- `perceptual_density`
- `structural_differentiation`
- `systemicity`
- `ambiguity`

Possible additional base candidates, subject to testing:

- `semantic_stability_axis`
- `fragmentation`
- `seriality`

#### Why these may qualify

These dimensions appear to be:

- applicable across many different kinds of work
- usable without needing highly specialised conceptual framing
- likely to support comparison between series

For example:

- A composite image built from many transformed Kylie Minogue photographs could plausibly score high in `perceptual_density`, high in `structural_differentiation`, high in `ambiguity`, and moderate to high in `systemicity`.
- A QRNG dot-grid work could plausibly score low in `perceptual_density`, high in `systemicity`, moderate to high in `structural_differentiation`, and lower or mixed in `ambiguity`.

These dimensions help compare very different works without presupposing a narrow discourse.

---

### 2. Selectable context dimensions

Selectable context dimensions are dimensions that are meaningful for many works, but not necessarily across the whole portfolio.

They should be available through a structured checklist in the UI and activated when relevant to a particular work or series.

They are not part of the universal backbone, but they are part of normal scoring practice when context makes them useful.

Selectable dimensions may be:

- medium-breadth in applicability
- more interpretive or domain-specific
- strongly relevant for some series and weakly relevant for others
- useful when a body of work clearly activates the associated concern

#### Examples of likely selectable dimensions

Based on current discussions, likely candidates include:

- `formal_complexity_axis`
- `visual_complexity_axis`
- `systemic_complexity_axis`
- `order_disorder_axis`
- `figurative_abstract_axis`
- `organic_geometric_axis`
- `openness_closure_axis`
- `surface_encoded_axis`
- `manual_trace` if not promoted to base
- `random_determined_axis`

In some cases, paired alternatives may also belong here:

- `order` + `chaoticity`
- `randomness` + `determinacy`
- `manual_trace` + `systemicity` as a field relation

#### Why these fit the selectable tier

These dimensions are often clearly relevant, but not always.

Examples:

- `figurative_abstract_axis` is likely very relevant to image-derived or portrait-derived works, including composite portrait works, but may be less useful for some other series.
- `surface_encoded_axis` is especially relevant to works where visible austerity contrasts with conceptual or systemic depth, such as the QRNG dot-grid work.
- `formal_complexity_axis` may be useful in comparing minimal systems and visually overloaded composites, but it may need careful domain-specific guidance.
- `order_disorder_axis` may feel intuitive in some series, yet prove too reductive if order and chaos are strongly co-present.

These are dimensions that the user should be able to enable where appropriate, but they should not burden every scoring session by default.

---

### 3. Experimental dimensions

Experimental dimensions are dimensions that remain under active conceptual, representational, or workflow testing.

They should not be part of routine scoring by default, but they should be available when intentionally exploring model evolution.

Experimental dimensions may include:

- dimensions with unstable definitions
- dimensions where multiple representation modes are still being tested
- specialist dimensions only relevant to a small subset of work
- higher-complexity interfaces such as 2D fields or compositional scoring
- candidate dimensions arising from repeated note patterns

#### Examples of likely experimental dimensions

Based on current discussions:

- `formal_affect_field` as a 2D coordinate field
- `theme_mix` as a compositional vector
- `process_mix` as a compositional vector
- `order` + `chaoticity` when treated as paired independent forces
- `randomness` + `determinacy` when treated as paired independent forces
- `manual_systemic_field`
- future candidates such as `recursion`, `compressibility`, or `symbolic_opacity`

#### Why these fit the experimental tier

These dimensions may be analytically valuable, but they bring one or more of the following:

- higher scoring burden
- more complex UI requirements
- unresolved semantic status
- uncertain cross-portfolio applicability
- uncertain analytical payoff

They should therefore be available deliberately, not imposed routinely.

---

## Optional additional tier: recommended dimensions

A practical UI refinement may be to add a “recommended” layer between base and general selectable dimensions.

This would not be a distinct governance category in the registry unless needed, but it could be a useful interface behaviour.

For example:

- **Base dimensions**: always shown
- **Recommended for this series**: suggested based on known relevance
- **Other selectable dimensions**: available in checklist
- **Experimental dimensions**: collapsed or hidden by default

This could be driven by:

- prior use in the same series
- prior use in similar series
- tags already present
- registry metadata linking dimensions to known domains
- manual editorial curation

### Example

For a portrait-derived composite series, the UI might recommend:

- `formal_complexity_axis`
- `figurative_abstract_axis`
- `fragmentation`
- `semantic_stability_axis`

For a rule-based or data-derived series, the UI might recommend:

- `systemic_complexity_axis`
- `surface_encoded_axis`
- `random_determined_axis`
- `seriality`

This makes the checklist more usable without turning it into a flat and noisy control surface.

---

## Base-dimension policy

### Important clarification

A base dimension is not necessarily one that always receives a numeric score.

A base dimension is one that must always be **considered and explicitly resolved**.

That means every base dimension should end each scoring session in one of three states:

- `scored`
- `unscored`
- `not_applicable`

This prevents a bad workflow in which missing data is accidentally treated as a low score.

It also allows later analysis of:

- scoring coverage
- ambiguity hotspots
- over-broad or under-performing base dimensions

### Example

If `perceptual_density` is base, then every reviewed work should explicitly record whether:

- it has a valid `0..5` score
- it has been deferred (`unscored`)
- it does not meaningfully apply (`not_applicable`)

In most cases, a strong candidate for base status should rarely be `not_applicable`.

If a supposed base dimension repeatedly ends up unresolved or not applicable, that is evidence it may need demotion.

---

## Criteria for assigning base status

A dimension should qualify as **base** only if most or all of the following are true:

1. **Cross-portfolio applicability**  
   It is meaningfully relevant across most or all works or series.

2. **Low `not_applicable` expectation**  
   It is unlikely to be irrelevant for large parts of the portfolio.

3. **Semantic stability**  
   Its meaning is clear and durable enough for consistent reuse.

4. **Scoring reliability**  
   It can be scored without excessive ambiguity or repeated need for notes.

5. **Comparative usefulness**  
   It supports meaningful comparison across very different works.

6. **Low interface burden**  
   Its scoring control is simple enough to justify always showing it.

### Example of likely base fit

`systemicity`

Reason:
This appears broadly meaningful across manual, rule-based, composited, and data-derived works. Even if the degree varies dramatically, the dimension itself remains intelligible and comparative.

### Example of likely non-base fit

`surface_encoded_axis`

Reason:
This may be highly useful for some works, especially those involving data, hidden structure, or encoded conceptual systems, but it is probably too specialised to serve as a universal backbone.

---

## Criteria for assigning selectable status

A dimension should qualify as **selectable** if most of the following are true:

1. It is useful for a meaningful subset of works or series
2. It has reasonably stable semantics
3. It may be highly informative when relevant
4. It is not essential for universal cross-portfolio comparison
5. It may reasonably be omitted in some contexts without damaging the model

### Example

`formal_complexity_axis`

Reason:
Very useful for comparing certain works, including highly layered composites and minimal systems, but likely too semantically broad or context-sensitive to require across everything without further refinement.

---

## Criteria for assigning experimental status

A dimension should remain **experimental** when one or more of the following apply:

1. Definition remains unstable or under review
2. Multiple representation types are still being compared
3. The UI interaction model is not yet settled
4. Applicability is narrow or uncertain
5. Analytical usefulness is promising but unproven
6. Scoring burden is relatively high

### Example

`formal_affect_field`

Reason:
Potentially valuable as a 2D coordinate representation, but too complex and too speculative to impose as part of routine scoring until proven useful.

---

## Promotion and demotion

Tier assignment should not be treated as permanent.

Dimensions may move:

- from experimental to selectable
- from selectable to base
- from base back to selectable
- from active use to deprecated

### Promotion examples

A dimension such as `semantic_stability_axis` might begin as selectable. If it proves widely applicable, consistently scoreable, and highly useful for comparison across series, it may later be promoted to base.

A paired relation such as `order` + `chaoticity` might begin experimental. If repeated testing shows that it captures important co-presence effects better than `order_disorder_axis`, it might replace or reshape the simpler bipolar version.

### Demotion examples

A supposed base dimension such as `seriality` may need demotion if it turns out to be frequently irrelevant or `not_applicable` in too many series.

A selectable dimension such as `surface_encoded_axis` may remain selectable rather than promoted if its strength lies in being highly illuminating only for a specific subset of works.

---

## Suggested UI policy

The scoring UI should reflect tiering directly.

### Default structure

#### 1. Base dimensions
Always shown. Must be explicitly resolved as `scored`, `unscored`, or `not_applicable`.

#### 2. Recommended for this work or series
Suggested based on prior use, series context, tags, or manual editorial curation.

#### 3. Other selectable dimensions
Available through checklist with short descriptions and optional links to guidance.

#### 4. Experimental dimensions
Collapsed by default. Available only when intentionally exploring model development.

---

## Suggested checklist behaviour

The checklist should not be a flat list of dimension IDs.

Each selectable dimension should include:

- label
- brief description
- representation type
- short note on when it is useful
- link to more detailed guidance if needed

### Example checklist descriptions

- **Formal Complexity**  
  Use when the work meaningfully activates a contrast between simplicity and complexity in formal organisation.

- **Figurative / Abstract**  
  Use when the work operates in relation to recognisable depiction, abstraction, or instability between the two.

- **Surface / Encoded Depth**  
  Use when visible form and underlying system or conceptual encoding diverge in an important way.

- **Order and Chaoticity (paired)**  
  Use when order and chaos appear as co-present forces rather than a single continuum.

---

## Relationship to examples discussed in these chats

### Example 1: Kylie composite image

This work likely activates:

**Base candidates**
- `perceptual_density`
- `structural_differentiation`
- `systemicity`
- `ambiguity`

**Selectable candidates**
- `formal_complexity_axis`
- `figurative_abstract_axis`
- `semantic_stability_axis`
- `fragmentation`
- `order_disorder_axis`

Why:
The work appears visually dense, highly differentiated, semantically unstable, and strongly fragmented. It also meaningfully engages complexity, figuration, and disorder.

### Example 2: QRNG dot-grid work

This work likely activates:

**Base candidates**
- `perceptual_density`
- `structural_differentiation`
- `systemicity`

**Selectable candidates**
- `systemic_complexity_axis`
- `surface_encoded_axis`
- `random_determined_axis`
- `seriality`
- `order_disorder_axis` or `randomness` + `determinacy`

Why:
The work is visually austere but conceptually and systemically rich. This makes it a strong example of why some dimensions should be selectively activated rather than universally imposed.

---

## Policy summary

The portfolio model should use a **tiered dimension system**.

- **Base dimensions** form the minimal comparative backbone and are always presented.
- **Selectable dimensions** are activated when context makes them relevant.
- **Experimental dimensions** remain available for model growth without burdening routine scoring.

Base dimensions should be **required to resolve**, not always required to numerically score.

This allows the model to maintain consistency while avoiding false precision and excessive interface burden.

---

## Short policy version

> Dimensions should be organised into tiers rather than presented as a flat list. Base dimensions form the minimal comparative layer and are always presented, but need only be explicitly resolved as scored, unscored, or not applicable. Selectable dimensions are activated when relevant to particular works or series. Experimental dimensions remain available for controlled testing and model evolution.

---

## Next step

The next document should define the actual registry fields needed to implement tiering, for example:

- `usage_tier`
- `is_base`
- `is_recommended_for`
- `status`
- `representation_type`
- `preferred_input_control`
- `default_visibility`
- `guidance_summary`
- `guidance_url`