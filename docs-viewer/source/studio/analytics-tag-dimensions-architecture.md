---
doc_id: analytics-tag-dimensions-architecture
title: Tag Dimensions Architecture
added_date: 2026-07-15
last_updated: 2026-07-15
ui_status: proposed
parent_id: analytics-tag-dimensions
viewable: true
---
# Tag Dimensions Architecture

This is proposed structure. Analytics does not currently have a dimension registry, score model, editor, or visualisation workflow.

## Ownership

- Analytics owns dimension definitions, score records, review workflows, and analytical projections.
- Catalogue identities remain catalogue-owned inputs.
- Tags remain their existing registry-backed semantic system; dimensions do not silently replace or reinterpret them.
- Visualisations consume explicit projections and do not redefine canonical values.
- LLM assistance, if ever used, proposes values through the normal review boundary and does not become a scorer of record.

## Proposed Flow

```text
dimension definition
  -> eligible catalogue identity
  -> representation-specific scoring control
  -> validated native value plus applicability state
  -> stored Analytics score
  -> named projection for a compatible comparison or view
```

## Extension Method

Add a registry definition only with its semantics, subject eligibility, native representation, validation, scoring control, and supported projections. Begin with code or data structures that serve the first proven dimension set; do not design a universal ontology framework first.

## Weak Spots

- No canonical schema or owner path exists yet for definitions or scores.
- Candidate dimensions can overlap or change representation under different interpretations.
- Record level and inheritance rules are unresolved.
- Missingness and uncertainty can easily collapse into misleading zeroes.
- Cross-dimension normalization may compare unlike meanings.
- A generic framework could be built long before a useful analytical workflow is proven.
