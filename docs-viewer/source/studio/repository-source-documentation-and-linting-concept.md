---
doc_id: repository-source-documentation-and-linting-concept
title: Source Documentation and Linting Concept
added_date: 2026-07-13
last_updated: 2026-07-15
ui_status: draft
parent_id: repository-source-documentation-and-linting
---
# Source Documentation and Linting Concept

Status: note for future work

## Summary

Introduce consistent source-code documentation and real linting for the repository:

- JSDoc for JavaScript
- Python docstrings, supported by type hints
- Ruff for Python linting
- ESLint for JavaScript linting

The main purpose is to make unfamiliar and complex code easier to re-enter, review, refactor, and expose through useful function-reference documentation.

This should be a deliberate cleanup project. It does not need to avoid a substantial backfill, provided the work improves understanding, catches genuine problems, and leaves maintainable automated checks behind.

## Documentation Impact

This note owns the initial proposal.

When implementation begins, review whether the adopted rules also need to be recorded in:

- `development-checklist.md` for new and changed code
- the testing and checks documentation for lint commands and required profiles
- a focused JavaScript or Python source-documentation guide if the conventions need more detail than the checklist should carry

Do not update stable guidance until the conventions and tools have been tried on representative code.

## Principles

- Document contracts, intent, non-obvious data shapes, side effects, units, coordinate systems, and failure behaviour.
- Use type declarations for types and documentation for meaning. Do not repeat obvious type information in prose.
- Prefer one structured options object over a growing list of JavaScript parameters where that improves the API.
- Prefer typed value objects, dataclasses, or focused parameter objects over long Python argument lists where that improves the model.
- Documentation is not a substitute for simplifying code. If a function needs a long explanation because it owns several responsibilities, consider splitting it.
- Do not require comments on trivial accessors, obvious wrappers, one-line helpers, or every private function.
- Avoid bulk-generated comments that merely restate function names and signatures.

## JSDoc

### Convention

Use `/** ... */` JSDoc blocks for JavaScript APIs that another module, future maintainer, or documentation tool needs to understand.

Document, where relevant:

- a short statement of purpose and any non-obvious behaviour
- `@param` entries for semantic meaning, accepted ranges, units, defaults, or mutation
- `@returns` when the return contract is not obvious
- `@throws` for expected exceptional outcomes
- `@typedef` and `@property` for shared object shapes
- callbacks, event payloads, lifecycle expectations, and asynchronous behaviour

For complex functions, prefer a named `@typedef` for an options or result object instead of repeating a large inline object type.

JSDoc comments should be useful immediately in editor hover information and source review. Generating standalone reference pages can be added after the comment convention has proved useful; generation should not block the initial backfill.

### Introduction

1. Choose and record a small JSDoc convention using representative modules from the existing applications and the future Processing/p5.js work.
2. Configure ESLint so valid JSDoc and browser-specific globals are understood without broad file-level suppressions.
3. Require documentation for new or materially changed exported APIs and complex internal contracts.
4. Backfill existing high-value surfaces in bounded areas rather than adding shallow comments everywhere at once.
5. Assess a JSDoc reference generator and a Docs Viewer import/build path only after enough useful comments exist to judge the output.

## Python Docstrings

### Convention

Adopt one readable repository-wide docstring style. Google-style sections are a suitable starting point because they remain legible in source and are supported by common documentation tools.

Use Python type hints for parameter and return types. Use docstrings to explain:

- purpose and behaviour
- assumptions and invariants
- important parameter meaning, units, ranges, and defaults
- returned value semantics
- mutation, filesystem, network, or other side effects
- expected exceptions and failure behaviour

Use `Args:`, `Returns:`, `Raises:`, and similar sections only when they add information. A short one-line docstring is enough for a simple public function whose typed signature already explains most of the contract.

Module docstrings should explain the module's responsibility when that ownership is not clear from its path and name. Class docstrings should describe the object lifecycle, state ownership, or collaboration boundary rather than list every method.

### Introduction

1. Select representative service, adapter, builder, command, and data-model modules and agree the concrete docstring style from real examples.
2. Improve missing type hints where they are necessary to make the documented contract precise.
3. Require docstrings for new or materially changed public APIs and complex internal contracts.
4. Backfill high-value modules in bounded passes, reviewing responsibility and API design at the same time.
5. Assess `pdoc`, Sphinx autodoc, or another extractor and a Docs Viewer import/build path after the source convention is established.
6. Enable docstring-specific lint rules only when the intended coverage has been backfilled; do not begin by producing repository-wide missing-docstring noise.

## Backfill Priorities

Backfill should follow value and risk rather than alphabetical order or raw file count.

### Priority 1: Public and shared contracts

- exported JavaScript functions, classes, constants, callbacks, and shared object shapes
- public Python functions, classes, dataclasses, protocols, and service methods
- modules used across application or package boundaries
- extension points and APIs intended for future reuse

### Priority 2: Complex code

- functions with many parameters or branches
- functions that pass structured state through several transformations
- orchestration code with several collaborators
- stateful classes whose lifecycle or invariants are not obvious
- Processing/p5.js drawing code with important coordinate, timing, colour, randomness, or rendering assumptions

Complexity reports can help find candidates, but each candidate needs human review. Some should be documented; others should be simplified or split first.

### Priority 3: Boundary and side-effect code

- HTTP routes and request/response adapters
- filesystem readers and writers
- parsers, normalizers, serializers, builders, and import/export code
- commands, background processes, and build scripts
- code that mutates canonical data or generated artifacts
- error translation and recovery behaviour

### Priority 4: Re-entry value

- unfinished or dormant projects being restarted
- code that is hard to reconstruct from tests alone
- modules that repeatedly require source archaeology during maintenance
- reusable mathematical, visual, layout, or domain algorithms

### Usually Do Not Backfill

- trivial getters and setters
- obvious one-line helpers
- test functions whose names and fixtures already state the contract
- generated or vendored code
- private implementation details that are simpler to read than to describe
- comments that would only paraphrase the code

## Linters

### Python

Use Ruff as the Python linter and initially run it as an audit. The first configuration should include correctness rules, then deliberately expand into maintainability, modernization, import, naming, exception, and documentation categories.

Existing `# noqa` comments must be reviewed when their corresponding rules are enabled. Keep a suppression only when the exception is intentional and local; otherwise fix the cause. Safe automatic fixes may be applied in reviewable batches, but behavioural or ambiguous fixes require manual review.

### JavaScript

Use ESLint with an explicit configuration for the repository's browser modules, workers, server-side scripts if any, tests, and future Processing/p5.js globals.

Start with correctness and unused-code findings, then add maintainability rules. Complexity, nesting, and parameter-count rules are useful as review signals, but should not force mechanical rewrites or arbitrary APIs.

### Adoption Sequence

1. Add pinned development dependencies and explicit configuration files.
2. Produce a baseline report without changing code.
3. Group findings into genuine defects, safe mechanical cleanup, design review, and justified exceptions.
4. Fix and review one category or bounded source area at a time.
5. Format code in separate, clearly identified batches where practical so formatting does not hide behavioural edits.
6. Add linting to the smallest normal repository check once the baseline passes.
7. Require new and changed code to pass immediately.
8. Expand the enabled rule set only through deliberate follow-up changes.

## Reference Documentation

JSDoc and Python docstrings should remain valuable in the source even if generated reference pages are never published.

If reference generation is added, prefer a pipeline that:

- extracts only intentionally documented surfaces
- preserves stable source paths and symbol names
- produces Markdown or structured data that Docs Viewer can consume
- links reference entries back to source locations where practical
- keeps generated reference output separate from hand-written conceptual documentation
- can be rebuilt predictably as part of the existing Docs Viewer tooling

The first generated-reference experiment should use one bounded JavaScript area and one bounded Python area. Do not select a repository-wide generator until the resulting pages have been reviewed for actual usefulness.

## Decisions To Make When Work Starts

- the exact JSDoc convention and whether type checking through JSDoc is also wanted
- the exact Python docstring style and minimum type-hint expectations
- which Ruff and ESLint rule groups form the initial baseline
- whether formatting is included in the same project or handled separately
- which existing application or project is the first backfill area
- whether generated references should use JSDoc, `pdoc`, Sphinx, or a smaller custom extractor
- how generated reference material enters the Docs Viewer source/build pipeline

## Intended Outcome

- unfamiliar code can be understood from its public contracts before reading every implementation detail
- complex parameter and data flows are explicit and easier to simplify
- source documentation is useful in editors and in Docs Viewer reference pages
- linting catches cheap defects before tests or manual review
- suppressions are rare, local, and meaningful
- the cleanup leaves durable rules for future Python, JavaScript, and Processing/p5.js work
