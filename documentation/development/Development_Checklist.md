---
draft: false
doc_id: d-20260523-190651-7157ec
title: Development Checklist
added_date: "2026-05-23 19:06:51"
last_updated: "2026-11-18"
parent_id: d-20260419-000000-d2e47b

---
# Development Checklist

Apply the relevant gates to the actual change and credible failure modes. This is guidance for judgment, not a requirement to manufacture evidence for every item. [Workflow](Development_Workflow.md) owns planning/closeout; [Verification](Verification.md) owns current check selection.

## Before Editing A Material Change

- [ ] Name one complete outcome, its authoritative owner, write boundary and visible/generated results.
- [ ] State frontend responsibility and concrete server persistence/processing/transfer work before choosing a language or existing helper. Browser-owned choices stay in the browser when it already has their data.
- [ ] Inspect the smallest relevant reference and current code/configuration. Check the worktree and preserve unrelated edits and generated effects.
- [ ] Confirm meaningful risks, prerequisites, public/local exposure and stop conditions. Raise extensions to the agreed single-user operating model before implementing them.
- [ ] Identify required documentation, projection, lint or manual follow-through from the changed boundary. Do not turn readiness into an exhaustive inventory or implementation exercise.

## Workflow Ownership And Structure

- [ ] Give the operation one visible owner for consequential reads, transformations, writes and completion effects. Separate metadata discovery, selected preparation, rendering, persistence, transfer and explicit maintenance through narrow inputs/outputs.
- [ ] Carry loaded state, parsed records, configuration, selections and completed effects forward. Additional reads, hashes, scans, refreshes or rebuilds need a concrete operational purpose.
- [ ] Inspect reused helpers, constructors, mixins, shared state and default-input branches for hidden corpus loading, validation or rendering. Missing selected input must not silently broaden the operation.
- [ ] Refactor demonstrated ownership seams when doing so removes hidden work, duplicated decisions or coupling. More modules or shorter files alone do not establish improvement.
- [ ] Keep local workflows awaited through their required writes, generation, handoff and fresh display. Busy state ends at that completion boundary; the user does not coordinate background jobs.
- [ ] Stop at the failing phase and report its target and completed effects. Ordinary recovery is source/destination correction and the owning operation. Add stronger recovery, preflights, freshness checks or rollback only for an agreed requirement or demonstrated failure.
- [ ] Authoring/import owners establish domain validity. Downstream consumers trust completed application data/handoffs; retain parsing, request authority, confinement, sanitization and selected transfer checks at their real boundaries.
- [ ] Preserve supplied authored values and exact identities. Do not add coercion, fallback labels, silent repair or compatibility aliases to accommodate obsolete records/tests. Any proposed compatibility exception needs justification and removal criteria.

## Public Site And Local Apps

- [ ] `site/` is the tracked Pages artifact, with no deploy-time build/copy step. Public readers receive no local write capability, private configuration or management assets.
- [ ] Edit shared/public Docs Viewer runtime under `docs-viewer/`. For represented files, run the explicit [projection sequence](Verification.md#docs-viewer-site-code-projection) and inspect its exact tracked delta. Change the inventory explicitly for additions/removals/public-status changes.
- [ ] Keep browser-safe configuration a positive projection of one owner; exclude paths, secrets, operation logs and private package details. Config presence alone does not establish a consumer or capability.
- [ ] Local navigation stays on its owning route; links to public content use the configured public URL helper.
- [ ] Local web apps target laptop/desktop use; public `site/` owns mobile acceptance. Retain keyboard access, zoom, bounded overflow and ordinary desktop resizing.
- [ ] Native App and Processing retain their own instructions, build/test/release lifecycles and explicit cross-project integration boundaries.

## Browser JavaScript And Source Documentation

- [ ] Keep shells/controllers to boot, state handoff, event wiring, readiness and calls to focused owners. Keep transport and domain decisions explicit.
- [ ] Reuse real shared component/style contracts. `shared/frontend/` requires reviewed app-independent behaviour; a one-consumer exception needs an explicit shared responsibility. Keep app APIs, transport, mutation and workflow policy injected.
- [ ] Do not manufacture reuse by migrating unrelated UI. Remove obsolete callbacks/fields within the agreed scope; affected test work remains separate.
- [ ] Keep exact-target action visibility/enablement with the frontend action resolver. Public providers are read-only; Manage supplies authoring contributions and confirmed committed changes.
- [ ] Preserve retained-view/disposal boundaries and ignore late completion after disposal. Busy/readiness state is independent of transient status copy.
- [ ] Document materially changed public/exported APIs when names/types do not convey ownership, lifetime, ordering, effects, failure or privacy. Use JavaScript typedefs for stable shared shapes and Python annotations/docstrings for their respective meaning.
- [ ] Backfill valuable shared/stateful contracts rather than trivial accessors or generated/vendor/test boilerplate. TypeScript, `checkJs`, generated reference sites and Processing tooling require separate adoption.
- [ ] Lint new/materially changed Python/JavaScript paths explicitly. Use an adopted scope for a whole-boundary claim; keep suppressions rare, local and justified.
- [ ] CSS URL-valued custom properties crossing stylesheet owners use explicit root-relative/absolute URLs. Byte-identical projection alone does not establish browser asset resolution.

## Source, Writes, And Security

- [ ] Edit source/configuration/generators as authority. Keep logs/cache/staging under ignored `var/` or configured external owners.
- [ ] Local write services bind loopback and retain request authority, narrow allowlists, exact IDs and path/symlink confinement; keep CORS local.
- [ ] Preserve parser/sanitizer boundaries against executable content and path traversal. Logs omit full source/payloads while retaining useful target/phase/status evidence.
- [ ] Tracked examples contain no credentials, local usernames or private machine paths.
- [ ] Do not restore old ownership through copied editable files, aliases, broad fallback reads or static-serving shims. A narrow wrapper delegates to its current owner without a second route/data contract. Explicit runtime projection is a deployment artifact.
- [ ] Place work by app/domain, source versus generated role and actual consumer. The [repository map](../reference/Source_Tree_Ownership.md) owns roots; [lint targets](../../tooling/lint/targets.json) own adopted boundaries. New roots require review of the complete boundary and a passing lint result before adoption; generated/vendor/dependency/cache/data/retired/Processing paths remain outside Python/JavaScript coverage.

## Domain Owners

Detailed operation rules live with their current reference owner. Apply those contracts without duplicating their full procedures here.

| Changed boundary | Maintained owner |
| --- | --- |
| Source identities, controls, eligibility and collection registration | [Source Organisation](../reference/Source_Organisation.md) |
| Exact Save, Draft, New, Delete and fresh display | [Source editing](../reference/Source_Editing.md), [mutations](../reference/Source_Mutation_Endpoints.md) and [Runtime](../reference/Docs_Viewer_Runtime.md) |
| Generation, adoption, queues and publication | [Builder](../reference/Builder.md), [generated contracts](../reference/Generated_Data_Contracts.md) and [Catalogue lifecycle](../reference/Catalogue_Save_And_Refresh.md) |
| Work/definition authoring, literal values and source audit | [Source model](../reference/Catalogue_Source_Model.md) and [Work editor](../reference/Catalogue_Work_Editor.md) |
| Media preparation, references, removals and thumbnails | [Document media](../reference/Media_And_Asset_Handling.md) and [Catalogue media policy](../reference/Catalogue_Media_Pipeline_Config.md) |
| Discovery, collection browsing and return | [Reader discovery](../reference/Reader_Discovery_And_Return.md) |
| Saved reports, explicit scans and public promotion | [Reports](../reference/Reports.md) |
| Import, Review, Export and package authority | [Import](../reference/Docs_Import.md), [Review](../reference/Docs_Review.md), [Export](../reference/Export.md) and [packages](../reference/Document_Packages.md) |
| Configuration and presentation | [Configuration](../reference/Configuration_And_Extension_Points.md), [Shared UI](../reference/Shared_UI.md) and [CSS](../reference/CSS_Ownership.md) |

## End-Of-Delivery Review

For a material code/config delivery, retain a distinct review step after implementation and selected evidence. Resolve findings within its scope and rerun only checks affected by changes, failure or unresolved risk. Documentation-only closeout uses bounded source/link review and accepted implementation evidence.

### Redundancy And Defensive Behavior Review

- [ ] Trace normal and empty/unchanged paths through frontend, service and reused helpers. Identify repeated calls/reads and work unrelated to the request.
- [ ] Confirm browser/server ownership from the decision and available data; name the filesystem persistence, processing or transfer that still belongs on the server.
- [ ] Review dependencies beyond changed lines, including loaders/builders, constructors, mixins, shared state and default branches. Extractions must remove real coupling or work.
- [ ] For each material validation/audit, identify its rule owner, prevented failure and reason this operation must perform it. Remove duplicate validation of completed upstream handoffs.
- [ ] Challenge corpus scans, agreement checks, hashes and read-backs. Distinguish required aggregate I/O from audits; keep explicit maintenance outside routine operations.
- [ ] Challenge unagreed rejection, normalization, repair, fallback, concurrency and recovery behaviour.
- [ ] Verify target/phase reporting and completed effects without concealed errors or unnecessary recovery work.
- [ ] Record findings, removals and justified retained safeguards. Passing checks do not establish that behaviour is needed.

When normal-use acceptance is agreed, retain concrete observations and investigate demonstrated slowness or rejected valid work at that action's owning boundary. Static evidence is not live acceptance; unexercised behaviour does not justify a general monitoring or regression framework.

## Documentation And Closeout

- [ ] Update the relevant current owner; preserve useful rationale and unique evidence in Design/Deliveries. Links to those records are allowed when useful.
- [ ] Agree test work separately for a named failure that warrants automation. Use [Test Contract Discipline](Test_Contract_Discipline.md) for scope, isolation, coverage and run selection.
- [ ] Report the exact evidence, results, generated follow-through, omissions and manual gates. Keep a scoped result at its actual scope.
- [ ] Close only the complete outcome and separate follow-ons explicitly. Do not repeat implementation checks merely for a status edit.
