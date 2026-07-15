---
doc_id: analytics-tag-dimensions-concept
title: Tag Dimensions Concept
added_date: 2026-07-15
last_updated: 2026-07-15
ui_status: paused
parent_id: analytics-tag-dimensions
viewable: true
---
# Tag Dimensions Concept

## Core Model

```text
dimension semantics
  -> native representation
  -> preferred scoring control
  -> stored value
  -> explicit analytical or display projection
```

Meaning comes first. The user should not choose an arbitrary widget or data shape while scoring. Each accepted dimension must explain what it measures and why its native representation fits.

## Representation Vocabulary

- **unipolar scalar** — degree of one property;
- **bipolar scalar** — position between named poles;
- **paired independent scalars** — two properties that may coexist;
- **2D coordinate** — position in a field where both axes matter;
- **compositional vector** — parts of a constrained mixture;
- **categorical value** — named class without false numeric order;
- **derived value** — reproducible summary calculated from native fields.

These are design vocabulary, not a promised exhaustive enum.

## Availability

A future definition may be base, selectable, or experimental. Base means its applicability should be resolved during review; it does not mean every record receives a forced numeric score.

## Projection Rule

Native data must not be distorted to fit a shared chart. A radar view is suitable only for compatible scalar projections. Any derived display score must name its formula and information loss.

## Open Questions

- Which dimensions answer a real analytical question without overlapping each other?
- Does scoring belong at series, work, or both?
- How are applicability, uncertainty, missingness, and not-yet-scored kept distinct?
- Which representation and control make each meaning understandable?
- What evidence justifies promoting an experimental dimension?
- Which comparisons or visualisations are useful enough to retain?
