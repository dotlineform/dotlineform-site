---
draft: false
doc_id: d-20260523-190651-7157ec
title: Development Checklist
added_date: "2026-05-23 19:06:51"
last_updated: "2026-10-03 21:27:23"
parent_id: d-20260419-000000-d2e47b

---
# Development Checklist

Apply only the sections relevant to the actual change and its credible failure modes. This is a reference for judgment, not a requirement to manufacture evidence for every checkbox on every delivery.

For application operations, let explicit product requirements and demonstrated failure modes determine planning, failure handling and verification. The default is to act on the request using the inputs it needs, validate them as they are used, stop on failure, and report success when the required work completes. Do not add preview/dry-run phases, saved execution plans, freshness rechecks, rollback/retry machinery, or post-action read-backs as a general pattern. Add a specific safeguard only when its need and boundary can be shown, such as protection of irretrievable data or an explicitly required publication guarantee.

When reviewing an existing workflow, identify planning, recovery and verification passes that repeat work or add code complexity and runtime cost. Keep each pass only if an explicit requirement or demonstrated risk justifies it; otherwise simplify the workflow without weakening input validation or its stated completion contract. A failure stops at the point reached, with completed effects left for diagnosis and a manual retry unless that workflow explicitly requires stronger recovery.

This checklist and the durable Studio development documentation are maintained directly in repository `documentation/studio/`. Studio Markdown filenames use concise readable titles with underscores. Retain each existing `doc_id` and `title` in front matter and update file links when renaming. Read and edit these repository files in place; their updates do not use the Docs source service, watcher, or Docs/Search rebuilds. Links below point to the corresponding Markdown files in this directory.

## Before Editing A Material Change

- [ ] Name the outcome, broad authoritative owner, write boundary, and user-visible or generated deliverables.
- [ ] Read the smallest durable doc that maps those owners; inspect only the code/config/tests needed for the next safe change.
- [ ] Confirm this is one finishable slice and note the credible blast radius or stop condition. Put broader discussion and internal sequence in the concept or feature parent.
- [ ] For a [Planned](Planned_Features.md) feature delivery, keep the initial readiness step read-only and concise. Exact file inventories, line estimates, frozen code, fixtures, prototypes, generated deltas, and complete test architecture are implementation work, not approval prerequisites.
- [ ] Confirm the feature is marked ready and its scheduling dependencies satisfied before implementing a proposed delivery.
- [ ] State meaningful benefits, risks, and public/local or security impact.
- [ ] Check the dirty worktree and preserve unrelated changes/generated watcher output.
- [ ] If removing/moving config or code, scan active loaders/call sites/services/tests before deciding it is stale.
- [ ] Identify documentation, linting, type-checking, or reference-generation follow-through only when the changed contract requires it.

## Ownership Gates

### User-Visible Operation Ordering

- [ ] Keep application workflows synchronous from the user's perspective: start A, wait for its complete outcome, then allow B. This applies across the app, including Save, Build, Refresh and the complete preparation/distribution Publish operation.
- [ ] Local workflows are synchronous and edits are unavailable until completion. Read the inputs required by the action and carry their results through the operation. Do not add concurrency checks, repeated input/snapshot scans, hashes or file-metadata freshness checks between internal calls. Validate inputs as they are used; verify writes or transfers only where the owning contract explicitly requires it.
- [ ] Keep the operation busy until all required writes, derived-data updates and other follow-through have completed and the outcome is known. Make controls available again only at that completion boundary; reporting success means the operation's required results are ready to use.
- [ ] Prefer straightforward awaited server operations. Server-side background work should not outlive the user action by default. Any necessary internal asynchronous work remains hidden within the same operation and completes before the UI returns to ready; the user does not coordinate pending jobs or delayed consistency.
- [ ] For Docs Source Save, the agreed required result is the validated combined metadata/body write to canonical source. End Save busy state and return to rendered display at that boundary. Existing watcher document/Links generation and automatic viewer refresh run independently; do not await or suppress them, rebuild Search, or turn a later generated-output failure into a failed Save. Other operations retain their own required completion boundaries.
- [ ] For Catalogue Save, the required result is the exact canonical mutation, required shared local media and current editor records. Keep generated Catalogue JSON and private Docs metadata in the explicit awaited Refresh Catalogue operation, with its local freshness receipt. Do not make persisted Studio lookup files an editor fallback or make Docs Publish implicitly refresh Catalogue readers. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns failure and reader timing.
- [ ] For Catalogue Refresh and Regenerate, require the private Working `updates-pending.json` list and fail on missing or malformed state. Refresh accumulates exact generated Work by-ID writes/deletions; Regenerate clears entries only after required source/delete and Build work succeeds. Diagnose partial failures manually without automatic repair. Do not make Refresh or Regenerate part of Publish. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) owns the current workflow.

### Public Site And Local Apps

- [ ] `site/` remains the checked GitHub Pages artifact; GitHub Pages has no deploy-time copy/build layer. Any tracked development projection is generated, reviewed, and committed before preview or deployment.
- [ ] Public routes use site-owned assets/config/data and never local write services or management capability probes.
- [ ] Local app links to public content use the configured public-site URL helper, not the local app origin or an unconditional production host.
- [ ] Local navigation remains on the owning app route.
- [ ] Local app routes, including Docs Viewer Manage and Docs Review, target laptop/desktop use. Do not add phone-width breakpoints, touch-only interaction branches, mobile route acceptance, or responsive-layout tests to them.
- [ ] Public `site/` routes retain mobile responsibility. Shared CSS or browser behavior that varies for mobile must target the public composition explicitly rather than imposing that contract on local apps.
- [ ] Desktop-only does not relax keyboard access, browser zoom, bounded overflow, or ordinary resizing of a desktop window; classify those separately from mobile-specific behavior.
- [ ] Processing remains a separate project.

### Configuration And Projection

- [ ] Working publication policy belongs to its configured ordinary `working/source/documents/unpublishable.json` and document `draft` state. Ordinary and other collection sources require an explicit boolean `draft`; Catalogue sources reject the field, generated document metadata omit it and Catalogue documents have fixed eligibility. Source reads and saves reject invalid readiness. Prepare Preview excludes ignored ordinary roots and their descendants, draft subtrees, and collections whose host is excluded, including Catalogue. Deploy Repo distributes that complete prepared set. Do not restore `publishable`, per-report `access`, inferred report exclusions or downstream eligibility filters.
- [ ] The single Docs workspace has Working source/generated storage and a read-only `preview/` artifact directly beneath the existing `DOTLINEFORM_DOCS_BASE_DIR`. Working registers collections and media once; Preview derives preparation configuration. One empty-body `/docs/publish` action captures current inputs, builds in temporary storage, validates and replaces Preview, records completion after byte verification and passes that completed snapshot directly to distribution. Keep the UI busy until both phases finish. No separate preparation/distribution endpoints, stage selector, Preview browsing or intermediate confirmation remain. Review through site-preview; Git/public deployment remains separate. Works owns Subject specialisation; ordinary documents retain authored fields unchanged.
- [ ] Collection creation, registration changes and retirement are explicitly scoped deliveries. Define the exact owner, report host, source/generated/media boundaries, producers/customisations, configuration/public projections and cleanup/recovery for each collection. Do not add generic collection create/delete UI actions, service endpoints or creation receipts. [Source Organisation](Source_Organisation.md#collection-deliveries) owns this boundary.
- [ ] Local document targets are `{doc_id}` or `{collection, doc_id}`; collection targets are `{}` or `{collection}`. Local readers/authoring resolve Working at their storage owner, public readers resolve repository/public output, and neither accepts publishing-stage context. Build/storage/completion provenance may retain internal stage roles. Reject retired request fields without defaults or aliases.
- [ ] Document routes use exact `doc` or `collection`/`doc` identity and configured by-ID reads without a list-manifest prerequisite. Retain only the current document/report and one consumable caller; release discarded mounts, payloads, subscriptions and adapters. Content Detail returns within its document without a history slot. Keep Index selection independent, restore the retained caller without discovery scans, and forward only confirmed committed metadata/deletions to list owners. Coordinate changed public runtime, browser config and generated link contracts through the same authorized Publish before release. [Runtime](Docs_Viewer_Runtime.md#exact-document-navigation-and-return) owns navigation and Save/projection completion semantics.
- [ ] Publish preparation failure prevents distribution. Distribution failure retains completed Preview and reports incomplete publication; repository and R2 effects are not atomic. Fix the owning input/destination and run a fresh Publish. Do not add automatic backup trees, rollback, retry ledgers or shared/remote asset deletion.
- [ ] Deploy Repo counts accepted by-ID documents directly. Public document-location JSON, its unused picker and legacy Catalogue document-URL refresh are retired; do not restore the UAC-1 pause or old Catalogue schema writer. Current Catalogue deployment copies only inventory-selected Preview Catalogue bytes into `site/assets/data/catalogue/` through the existing Publish owner.
- [ ] Keep ready media in the configured shared `assets/` families, with one current local copy and exact workspace/collection ownership. Studio Save prepares required complete Work rendition sets with canonical dimensions/versions, without R2; the later explicit Refresh generates Working Catalogue JSON. Prepare Preview captures declared Catalogue JSON and sorted asset identities, without copying assets or retaining asset hashes/history. Publish transfers referenced current bytes without version changes or automatic shared/remote asset deletion; the R2-before-Actions timing gap is accepted. Editable build inputs, Projects originals and canonical Catalogue records retain their own owners.
- [ ] Keep by-ID Docs links and Docs-owned media root independent: render internal Docs targets as query-only viewer links and media as `docs-media:` identities; local/public readers resolve their configured viewer and media roots before mounting, while Export and Review resolve their own destinations. Public Docs media keys mirror local `workspace/` and `collections/<collection>/` suffixes beneath their configured roots; do not restore the retired `sub-scopes` R2 path or a by-ID `viewer_url`.
- [ ] Document Subjects are Work, configured Folder or None, with exactly `work_id` and `folder_path` in the assignment field group. Reject retired document `series_id` declarations and normalized Series subjects without aliases or automatic conversion. Keep Studio Series membership and plain-text report Series columns; Projects derives associations through Work/Folder and Works coverage through member Works. [Subject Associations](data/subject-associations.md) owns the current contract.
- [ ] Catalogue Media View tokens target exact Works or Galleries; Work presentations show direct Gallery links followed by distinct links from explicit canonical Series–Gallery pairs. Series remains a Catalogue grouping, with no document Subject, token target, by-ID media reader, gallery presentation or Media View opener. Do not infer a Gallery from Series membership or rewrite authored Series tokens to another identity. [Catalogue Media View](Catalogue_Media_View.md) owns the current reader and authoring boundary.
- [ ] The Works in a Series report and generated Series by-ID/compact member-Works index files are retired. Publish inventories the current Work and Gallery Catalogue JSON plus the explicit Series–Gallery relation index. Keep that index derived only from canonical Series–Gallery pairs and current Gallery titles; do not revive the old Series member-Works index as a compatibility payload.
- [ ] Working alone builds Search. Select ordinary IDs from the current Working tree with inherited draft/unpublishable exclusions, then flat eligible subdocs from explicitly included collections whose configured hosts survive. Catalogue subdocs have fixed eligibility and no draft field; other collections use their boolean draft state. Use the workspace's shared collection inclusion decision; registration alone never opts in. Read selected source/by-ID content only after metadata selection, and fail on selected inconsistencies without a full-source fallback. Prepare Preview captures the existing index with its plan, copies exact bytes and records them in the completed snapshot; Deploy Repo copies the same file unchanged. Do not rebuild or filter Search during copying or impose freshness after ordinary edits. Document completeness does not depend on Search membership.
- [ ] Recents shares Search's metadata eligibility and collection coverage. Full Working document builds reuse ordinary metadata and compact included-collection management manifests before sorting/limiting; they do not reopen collection bodies. Refresh required collection metadata before Recents generation. Source saves, watcher passes, targeted and collection-only builds preserve the saved file. Prepare Preview captures it with Search and binds both into the plan; Preview and Deploy Repo copy the exact stage-independent bytes without re-filtering, relabeling or URL rewriting. Missing/invalid payloads fail without fallback generation. Readers own routes; no separate publication Recents variant remains.
- [ ] Selected Documents membership belongs only to Working `source/documents/selected.json`, independently of Search/Recents coverage. Star writes preserve document modification dates; document builds refresh selected metadata and Delete removes exact deleted targets. Prepare Preview filters selections against its prepared document set while retaining excluded Working selections; Publish copies the resulting stage-independent file unchanged. The report reads the list when opened. [Source Organisation](Source_Organisation.md) owns the durable contract.
- [ ] Classify each field as checked source config, environment, server-only policy/path, runtime projection, browser-safe static config, generated data, or UI copy.
- [ ] Keep one owner; project a safe subset rather than copying the same key into another app config.
- [ ] Keep Docs Search JSON independent of stage and routes. Readers resolve exact document/collection/report-host IDs through their active context; snapshot manifests retain provenance. Search format changes do not implicitly authorize coverage, ranking or build-ownership changes. [Search Index](Docs_Search_Index.md) owns the payload contract.
- [ ] Browser config/API projections use positive allowlists and exclude source paths, write targets, secrets, workspace roots, operation-log internals, and package implementation detail.
- [ ] Presence in config/runtime output is not proof of active capability; confirm a consumer.
- [ ] For changed configuration boundaries, select proportionate existing validation. New or changed tests require their own agreed specification; a config change does not authorize them automatically.

[Configuration Map](Configuration_Map.md) finds the main registries.

### Browser JavaScript

- [ ] Name the complete responsibility and its owner after the change.
- [ ] Keep route shells/controllers to boot, state handoff, required event wiring, ready/busy projection, and calls to focused owners.
- [ ] Put domain logic, validation, rendering, modal lifecycle, service orchestration, result shaping, and import/export workflows in focused modules when they are real responsibilities.
- [ ] Prefer explicit inputs/outputs over helpers that mutate broad route state.
- [ ] Reuse shared components/styles; do not add a one-off rule/selector without checking its owner.
- [ ] Remove obsolete callbacks/fields/aliases within the product scope; fixture convenience is not a compatibility contract. Identify affected tests, but retarget them only within approved test work.
- [ ] If this change exposes an ownership seam, improve that seam in the same bounded slice or record one concrete follow-up; do not defer routine cohesion to a future full-scale audit.
- [ ] After a sizeable first-pass module works, review cohesion before adding more scope.

### Source Documentation And Linting

- [ ] Add concise JSDoc or Python docstrings to new or materially changed exported/public APIs when callers need contract meaning that types and names do not convey.
- [ ] Document ownership, lifecycle, ordering, side effects, failure behavior, invariants, privacy, and constrained values but do not restate signatures or obvious code.
- [ ] Use JavaScript typedefs for stable shared object/callback shapes. Let Python annotations carry types and use docstrings for domain behavior.
- [ ] Update source documentation with the contract change and retain current code/config plus focused executable evidence as behavior authority.
- [ ] Pass every new or materially changed source path explicitly to `bin/lint-js <path> [path ...]` or `bin/lint-python <path> [path ...]`. Both commands deliberately fail without a target.
- [ ] When a whole adopted boundary changed or is being promoted, pass `bin/lint --scope <scope-id>` and report the resolved maintained roots. Scope ownership lives in `tooling/lint/targets.json`.
- [ ] Treat explicit-path results as evidence only for the submitted paths and maintained-scope results as evidence only for the configured boundary. A fixed specimen or earlier subset remains proving history, not current tool ownership.
- [ ] Keep suppressions rare, local, and justified.
- [ ] Use this capability from the start of major new Python/JavaScript features; historical documentation backfill must not block adoption.
- [ ] Backfill existing source documentation by value and risk: shared and cross-application contracts; exported JavaScript options, callbacks, events, controllers, and lifecycle boundaries; Python services, adapters, value objects, write plans, builders, commands, and error translation; stateful or side-effectful modules that repeatedly require source archaeology; then complex code where documenting the contract exposes a useful simplification.
- [ ] Do not backfill trivial accessors, obvious wrappers, generated or vendor source, or test functions whose names and fixtures already state the contract.
- [ ] Use of TypeScript, `checkJs`, a `jsconfig.json`, generated API/reference sites, and Java/Processing tooling requires a separate adoption decision.

### Docs Viewer Runtime

- [ ] Shared/public Docs Viewer JavaScript and stylesheets are edited under `docs-viewer/`. When a represented canonical file changes, run `bin/site-code-update`, inspect the exact tracked `site/docs-viewer/` delta, then run `bin/site-code-update --check` and `bin/site-validate` before handoff.
- [ ] CSS custom properties that carry asset URLs across stylesheet owners use explicit root-relative or absolute URLs. A relative URL is resolved from the consuming stylesheet; canonical/public byte equality alone does not prove that a browser can load the referenced artwork.
- [ ] Treat `site-tools/config/site-code-update.json` as the sole canonical-to-site runtime inventory. Change it explicitly when a represented file is added, removed, or changes public status; do not add local-only code from mixed runtime or stylesheet directories.
- [ ] Identify app context, provider, service adapter, state domain, controller, hosted view, and backend/generated contract involved.
- [ ] Public installs remain read-only and receive no management assets, services, local generated-read URLs, or write-capable handles.
- [ ] Management writes/import/settings/rebuild/source-open operations go through the management client and validated server endpoints.
- [ ] Route features are allowlisted; disabled features do not construct controllers, bind events, or require payloads.
- [ ] Generated collection reads use a named provider and the generated-data runtime; do not spread transport/retry logic.
- [ ] Ordinary local/public reads open the requested file within their configured owner. Do not inspect a completion manifest, scan/hash a snapshot or read an index to permit a by-ID read. Publication owns snapshot/output verification; retain request identity, path confinement and requested-payload validation. Preview browsing routes remain retired.
- [ ] Ordinary Working document reads open the exact generated by-ID file; do not read the index or validate its stored URL as a prerequisite. Retain immutable request identity and explicit Working ownership.
- [ ] Serve allowlisted local static assets before workspace-dependent route resolution. JavaScript, CSS and icons do not require workspace configuration loading or validation on each request; retain the static allowlist and repository path confinement.
- [ ] Use normal browser caching for local browsing: one-day app assets, long-lived versioned Catalogue primary images, and ETag revalidation for mutable reader data, configuration, shells and unversioned media. Source/management operations keep current-state reads. Preserve Save/watcher freshness and CORS on conditional responses; do not introduce workspace scans or process payload caches. [Runtime](Docs_Viewer_Runtime.md#local-http-caching) owns the exact policy and development refresh procedure.
- [ ] Do not add feature lifecycle ownership to `docs-viewer-app-runtime.js`.
- [ ] Public-safe and manage-only meanings of one UI slot use separate or explicitly shaped view contracts.

[Docs Viewer Overview](Docs_Viewer_Overview.md) and [Runtime](Docs_Viewer_Runtime.md) own the architecture map.

### Docs Import, Docs Review, And Document Packages

- [ ] Refer to [Docs Import Architecture](Docs_Import_Architecture.md), [Docs Review](Docs_Review.md).
- [ ] Keep preview/planning write-free and apply explicit about collisions, parent dependencies, media, decisions, and partial failure.
- [ ] Use normalized `ImportContent` between package adapters and collection planning.
- [ ] Keep the shipped **Review package** boundary: one explicit Working collection package is prepared for read-only Docs Review, while normal full-package Import owns returned content, summary, parent, and supported publication eligibility changes together without record selection or skip.
- [ ] Docs Review remains read-only and passes safe package identity only—not paths, staged filenames, decisions, or write authority.
- [ ] New formats or package shapes get one parser/profile owner, not branches in generic coordinators. Specify any proposed parser/profile test work separately and implement only after approval.
- [ ] Export-only profiles remain explicitly non-importable until a complete review/apply contract exists.
- [ ] Collection preparation stays confined to one configured flat collection, retains the explicit Working stage and exact `collection` through provenance, and gains `supports_return_import: true` only when both the package profile and exact collection opt in. Capability projection alone is not mutation authority; returned-package planning and apply must retain the same exact target. Packages with retired scope or sub-scope provenance require re-export and a new Review package.

### Generated Data

- [ ] Collection builds produce only the current operation's manifest: management metadata in Working, public reader metadata in temporary publication builds. Targeted Working builds merge and render from saved management metadata alone; preserve identity/date validation without public-manifest prerequisites or agreement checks. [Generated Data Contracts](Generated_Data_Contracts.md#collection-manifest-ownership) owns this boundary.
- [ ] Keep document relationship construction independent of destination existence and link-validity checks. Link validity belongs to authoring and Broken Links; explicit document deletion still cleans up its record and associated relationships. Related links directives alone do not create graph records.
- [ ] Edit canonical source/config/generator, never generated output as authority.
- [ ] Run a generator dry-run before writing only when an explicit requirement or demonstrated risk calls for it; support for a dry-run is not itself a reason to run one.
- [ ] Check generated shape and projection boundaries to address a named contract or credible failure mode; do not add a second full pass solely to confirm an operation's reported success.
- [ ] Update contract fixtures/audits only for current positive behavior.
- [ ] Let Docs watcher output stand; do not revert expected generated changes.
- [ ] When Docs watcher has already generated the intended document projections, inspect those outputs and do not rerun the builder solely to prove idempotence. Search remains unchanged until an explicit Manage Rebuild or direct complete-scope search build.
- [ ] If Docs watcher is unavailable, use a targeted document build with exact changed IDs and `--skip-media-builds` for ordinary doc-only edits. Use a full-scope or media-inclusive build only for a named global, reconciliation, or registered-media risk; a manually required search build remains complete-scope because postings are atomic.

### Source, Writes, And Security

- [ ] Public-only assets stay under `site/`; shared/public Docs Viewer runtime code stays with its `docs-viewer/` owner and reaches `site/` only through the explicit tracked projection. App-specific and management-only code stays with its owner.
- [ ] Local outputs/logs/staging stay under ignored `var/` or configured external workspaces.
- [ ] Write services bind loopback, validate paths/IDs, use narrow allowlists, and keep CORS local.
- [ ] Logs omit full payload/source content and keep useful method/path/status evidence for errors.
- [ ] Tracked examples/docs contain no credentials, private paths, local usernames, tokens, or machine-specific roots.
- [ ] Sanitization/parser changes preserve executable HTML/script and path traversal boundaries.

[Source Tree Ownership](Source_Tree_Ownership.md) owns the directory map.

## Verification Gate

- [ ] Treat creating, updating, refactoring, deleting, or expanding tests, fixtures, harnesses, and collection membership as test delivery work requiring an agreed specification. Approval of the product fix does not authorize that work, including temporary regression scripts. Reuse existing approval within its scope.
- [ ] Keep the test specification and current coverage record under Testing or its durable app/domain owner, outside delivery documents, following [Test Contract Discipline](Test_Contract_Discipline.md). Record exact selectors/membership, scenarios, inputs, assertions, fixtures/mocks, real systems, side effects, exclusions, commands/triggers, and costs. A delivery links to that record; it does not become the test's only documentation.
- [ ] Before non-trivial execution, select the exact existing evidence and explain the risk it addresses, actual coverage, side effects, and proportionate setup/runtime/resource/token/diagnosis cost or unknowns. Keep the verification budget short; use a table only when useful. Test authoring and maintenance costs belong in the test specification. Do not benchmark to fill an estimate.
- [ ] Do not create or run evidence outside the accepted budget merely to improve a green count. Record a newly discovered risk before proposing more work. Documentation-only or trivial steps may require no executable tests; an unapproved test proposal does not block a complete fix unless the user made it an acceptance requirement.
- [ ] For each non-trivial check, name the plausible failure it can uncover and the specific behavior or output it exercises. If neither is concrete, do not count the result as evidence.
- [ ] Report a green result at its actual scope. A pilot specimen, happy-path assertion, generated-page build, or aggregate test count is not subsystem-wide confidence.
- [ ] Name materially relevant omissions and evidence gaps. Do not use documentation completeness, check volume, or a familiar profile name as a proxy for correctness.
- [ ] Retain a permanent check only when it can fail for a plausible regression in an owned contract. Label setup/toolchain smokes as smokes rather than coverage.
- [ ] Choose the lowest layer that proves the contract: pure function, service/API, generator, then browser only when necessary.
- [ ] Permanent tests protect data/response/schema/parser/ownership/route-module contracts, not ordinary UI choreography.
- [ ] No test layer or profile is an automatic closeout gate. Inspect the actual coverage and cost before selecting an existing check; profile membership or a name such as quick does not establish value.
- [ ] Use the narrowest justified existing command or selection and stop when its evidence is sufficient. Repeat only after a relevant change, failure, or unresolved risk. Report the profile and summary path when `run_checks.py` is used.
- [ ] Treat a failure outside the changed contract as a separate finding; do not expand scope silently.
- [ ] Run `git diff --check` when code/config or a substantial text edit makes whitespace defects a plausible failure; do not use it as automatic status-only closeout evidence.

[Testing](Testing.md) owns selection policy.

## End-Of-Delivery Review

For every material code/config delivery, include a distinct code-review step after implementation and selected evidence, and before closeout. Approval of readiness and a passing test run do not replace review. For a status-only documentation closeout, mark code review not applicable with the reason, perform a bounded source/diff review, and reuse accepted implementation evidence instead of repeating delivery verification.

- [ ] Review the changed contract and relevant final diff as an independent reviewer. Look for ownership drift, duplicated contracts, hidden coupling, compatibility residue, dead paths, and missing failure evidence within the delivery boundary; do not expand this into a repository audit.
- [ ] When test changes are approved, review their diff against the agreed specification and durable coverage record for duplicated coverage, UI choreography, unnecessary fixtures, collection expansion, and unjustified cost. Resolve findings within that approved scope; otherwise propose bounded test work rather than silently editing tests.
- [ ] Record review findings and their resolutions in the delivery's code-review step, then rerun only checks affected by review changes.
- [ ] Reconcile every completion claim with the exact evidence and inspected surface. Remove or narrow any statement that reads as broader confidence than the work can support.
- [ ] Record a documentation, linting, type, or reference-boundary follow-up only when the delivery produced concrete evidence of a gap; do not require a speculative adoption review at every closeout.
- [ ] Confirm remaining risks, omissions, and evidence gaps are visible before closeout.

## Documentation And Closeout

- [ ] Update one durable owner when behavior/architecture/methodology/extension/gaps changed.
- [ ] Do not mirror exhaustive code/config inventories into overview docs or add generic Related lists.
- [ ] Update delivery status only when its outcome or suggested order actually changed.
- [ ] Report outcome, changed owners, exact check targets/results, generated follow-through, risks, named omissions, and separate next outcomes; do not present scoped evidence as an application-wide green light.
- [ ] Close only a complete outcome; reshape the feature delivery rather than leaving it half-finished.
- [ ] Treat closeout as proportional bookkeeping: confirm the status edit and expected watcher output, and add rebuilds, generated-record audits, lint, tests, or diff checks only when they address a concrete risk introduced by that edit.

:::report
id: docs_backlinks
:::
