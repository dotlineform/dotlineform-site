---
doc_id: analytics-dimension-exploration
title: Dimension Model Exploration
added_date: 2026-07-15
last_updated: 2026-07-15
ui_status: paused
parent_id: analytics
viewable: true
---
# Dimension Model Exploration

## Status: Paused, Not Implemented

Analytics does not currently have a dimension registry, scoring data model, dimension editor, or visualisation workflow. The implemented scoring code measures tag completeness only.

This page records the useful conclusions reached during early design. Do not treat it as a runtime contract, delivery plan, or reason to extend current tag code. When dimension work becomes active, start a bounded concept/architecture request from current needs and code rather than trying to implement this note wholesale.

## Core Conclusion

```text
dimension semantics
  -> native representation
  -> preferred scoring control
  -> stored value
  -> explicit analytical/display projection
```

Meaning comes first. The user should not choose an arbitrary widget or data shape while scoring. Each accepted dimension needs a registry definition that explains what it measures and why its native representation fits.

## Candidate Representation Families

- **unipolar scalar** — degree of one property;
- **bipolar scalar** — position between named poles;
- **paired independent scalars** — two properties that may coexist rather than cancel out;
- **2D coordinate** — position in a field where both axes matter;
- **compositional vector** — parts of a constrained mixture;
- **categorical value** — named class without false numeric order;
- **derived value** — reproducible summary calculated from native fields.

These are design vocabulary, not an exhaustive future enum.

## Availability Tiers

A future registry may distinguish:

- **base** — broadly applicable, stable dimensions shown by default;
- **selectable** — useful in specific series/work contexts;
- **experimental** — actively testing semantics, representation, or value.

“Base” should mean the review must resolve applicability/state, not that every record must receive a forced numeric score. Promotion between tiers would require evidence of semantic stability and analytical usefulness.

## Projection Rule

Native data must not be distorted merely to fit a shared chart. A classic radar view is suitable only for compatible scalar projections. Bipolar axes need retained anchor meaning; paired, coordinate, compositional, and categorical values usually need different views. Any derived display score must name its formula and information loss.

## Weak Spots To Resolve Before Delivery

- No canonical owner or schema exists for dimension definitions or scores.
- Many candidate dimensions overlap semantically or change shape depending on interpretation.
- It is unclear whether scoring belongs at series, work, or both.
- Applicability, uncertainty, missingness, and “not scored” need distinct states.
- LLM recommendations could accelerate review but also invent plausible-sounding ontology without operational reliability.
- Cross-dimension normalisation can make attractive visualisations that compare unlike meanings.
- A large generic framework would be easy to build before proving one useful end-to-end workflow.

## Restart Boundary

When this becomes active:

1. choose one concrete analytical question and a very small dimension set;
2. define canonical ownership and one native representation per dimension;
3. deliver one finishable scoring/review workflow;
4. test whether the resulting data supports a useful decision or comparison;
5. only then generalise registry tiers, controls, projections, or LLM assistance.

The deleted draft tables and candidate lists were exploration, not commitments. Git history remains available if a specific example is needed later.
