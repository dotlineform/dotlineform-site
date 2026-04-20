---
doc_id: generic-llm-helper-pattern
title: "Generic LLM Helper Pattern"
last_updated: 2026-04-16
parent_id: llm
sort_order: 30
---
# Generic LLM Helper Pattern
Draft note for structured semantic orchestration

## Purpose

This note defines a generic helper pattern for invoking an LLM in a controlled, reusable way within the portfolio analysis system.

The aim is to support semantic tasks such as:

- recommending relevant dimensions
- recommending tags
- comparing candidate dimension shapes
- detecting registry strain
- summarising a series
- explaining why one dimension or representation type fits better than another

The helper should not operate as a freeform chat wrapper. It should act as a structured orchestration function with a clear contract between:

- input data
- task instruction
- output schema

---

## Core principle

Use a generic LLM orchestration helper with:

1. structured input JSON(s)
2. structured task/instruction JSON
3. structured output schema JSON

In compact form:

`inputs + instruction + output_schema -> validated LLM response`

This keeps the helper generic at the transport/orchestration layer while keeping each task specific at the application layer.

---

## Why this pattern is useful

The portfolio system involves multiple semantic reasoning tasks that share a common invocation pattern but differ in goal.

Examples:

- recommend dimensions for a work from images and production notes
- recommend tags for a work
- compare `order_disorder_axis` vs `order + chaoticity`
- detect repeated note patterns across a series
- identify likely base vs selectable dimensions
- explain semantic overlap between two dimensions

These tasks should not each require a completely separate ad hoc prompt implementation.

A generic helper allows:

- reuse
- versioning
- validation
- easier debugging
- task-level consistency
- model substitution later if needed

---

## Relationship to Codex skills

This pattern is conceptually related to Codex skills, but it is not the same thing.

### Similarity

Both patterns rely on structured, reusable task definitions.

Both aim to make model behaviour more reliable by providing:

- explicit context
- explicit instructions
- repeatable structure

### Difference

Codex skills package reusable agent workflows, instructions, resources, and optional scripts for use by Codex.

This helper pattern packages structured semantic tasks for use inside an application workflow.

A useful distinction is:

- **Codex skill** = reusable agent capability or workflow bundle
- **LLM helper** = reusable application-level reasoning call with constrained inputs and outputs

So the patterns are related, but they sit at different layers of the system.

---

## Recommended request envelope

The helper should accept a single request envelope containing three top-level sections.

### 1. Inputs

The data to be analysed.

This may include one or more structured JSON objects, for example:

- `work_context`
- `series_context`
- `image_summaries`
- `production_method`
- `existing_tags`
- `existing_dimensions`
- `registry_subset`
- `prior_notes`

### 2. Instruction

The task definition.

This should state:

- the task type
- the goal
- relevant constraints
- optional priorities or preferences

### 3. Output schema

The required shape of the response.

This should define:

- expected keys
- required vs optional fields
- field types
- allowed enumerations where relevant

---

## Recommended envelope shape

```json
{
  "inputs": {
    "work_context": {},
    "registry_subset": {}
  },
  "instruction": {
    "task_type": "recommend_dimensions",
    "goal": "Recommend relevant base and selectable dimensions for this work.",
    "constraints": {
      "use_registry_only": true,
      "return_reasoning": true,
      "return_confidence": true
    }
  },
  "output_schema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

This is only illustrative, but the pattern should remain stable.

---

## Recommended design rule

The helper should be generic in orchestration, but specific in task contracts.

This means:

- the transport wrapper can be reused
- task types should be enumerated or tightly controlled
- output schemas should be explicit
- the application should not rely on vague prose prompts alone

Do **not** make the helper fully open-ended if you want consistent downstream use.

---

## Suggested task types

Examples of plausible task types for this project:

- `recommend_dimensions`
- `recommend_tags`
- `compare_dimension_shapes`
- `detect_registry_strain`
- `series_dimension_summary`
- `explain_dimension_choice`
- `validate_score_consistency`
- `suggest_tier_assignment`
- `summarise_semantic_pattern`

These should be treated as application-level task contracts.

---

## Example use case

### Task

Recommend dimensions for a work from image summaries and production description.

### Example inputs

```json
{
  "work_context": {
    "work_id": "example_001",
    "title": "Untitled",
    "production_method": "Composite built from hundreds of celebrity photographs with repeated destructive transformations before layering.",
    "image_summaries": [
      "Dense composite portrait field with heavy visual interference.",
      "Figure partially visible through layered distortion."
    ]
  },
  "registry_subset": {
    "base_dimensions": [
      "perceptual_density",
      "structural_differentiation",
      "systemicity",
      "ambiguity"
    ],
    "selectable_dimensions": [
      "formal_complexity_axis",
      "figurative_abstract_axis",
      "semantic_stability_axis",
      "fragmentation"
    ]
  }
}
```

### Example instruction

```json
{
  "task_type": "recommend_dimensions",
  "goal": "Recommend relevant base and selectable dimensions for the work.",
  "constraints": {
    "use_registry_only": true,
    "return_reasoning": true,
    "return_confidence": true,
    "max_recommendations": 8
  }
}
```

### Example output schema

```json
{
  "type": "object",
  "properties": {
    "recommended_base_dimensions": { "type": "array" },
    "recommended_selectable_dimensions": { "type": "array" },
    "not_recommended_dimensions": { "type": "array" },
    "semantic_notes": { "type": "array" },
    "registry_strain_signals": { "type": "array" }
  },
  "required": [
    "recommended_base_dimensions",
    "recommended_selectable_dimensions",
    "semantic_notes"
  ]
}
```

## Recommended modular input structure

Do not force every task into one giant flat JSON object.

Prefer modular inputs that can be composed as needed.

For example:

- `work_context`
- `series_context`
- `registry_subset`
- `prior_annotations`
- `image_analysis`
- `task_context`

This allows different task types to consume only the data they need.

---

## Why explicit output schema matters

A helper that accepts only inputs and instructions is weaker than one that also accepts an explicit output schema.

Without an output schema, you risk:

- drift in response structure
- brittle parsing
- inconsistent field naming
- task-to-task incompatibility
- higher post-processing burden

With an output schema, the helper becomes suitable for:

- UI suggestions
- workflow chaining
- logging and audit
- later analytics

---

## Suggested metadata fields

The helper should probably include metadata for traceability, such as:

- `helper_version`
- `task_version`
- `registry_version`
- `model_version`
- `timestamp`
- `source_ids`

This is useful when comparing outputs across time or after changes to prompts, schemas, or registries.

---

## Relationship to the registry-driven scoring system

This helper should operate within the registry-driven scoring architecture.

That means:

- the registry remains the source of truth for available dimensions, tags, and representation types
- the helper should usually work against a supplied registry subset
- the helper should not silently invent canonical dimensions outside the system unless the task explicitly allows exploratory suggestions

A useful constraint flag is therefore:

- `use_registry_only: true|false`

This makes it clear whether the model should stay within the current controlled vocabulary or identify strain beyond it.

---

## Recommended caution

The helper should remain advisory and constrained.

Risks include:

- over-generalised semantic recommendations
- unstable outputs across model versions
- hidden prompt drift
- accidental expansion beyond the current registry
- false appearance of objective scoring

For this reason:

- task types should be explicit
- schemas should be explicit
- results should remain inspectable
- human review should remain central where recommendations affect scoring or governance

---

## Pattern summary

A generic LLM helper is appropriate when the system needs repeated semantic reasoning over structured data.

The preferred pattern is:

- structured inputs
- structured task instruction
- structured output schema

This makes the helper reusable without making it vague.

---

## Short note version

Use a generic LLM orchestration helper with structured input JSONs, structured task instructions, and structured output schemas. Keep the helper generic at the transport layer, but constrain task types and response contracts at the application layer.

---

## Next step

The next document should define either:

1. a concrete request/response envelope schema for the helper
2. a task catalog for supported `task_type` values
3. validation and logging rules for helper calls

---

## Note on relationship to Codex skills

The family resemblance to Codex skills is real. The closest analogy is:

- `SKILL.md` / `AGENTS.md`: reusable instructions for agent behavior and workflow routing
- your helper pattern: reusable structured contract for semantic reasoning inside your application

So these should be treated as parallel patterns at different layers, not as the same mechanism.
