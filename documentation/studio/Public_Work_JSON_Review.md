---
draft: false
doc_id: d-20261007-221414-48ff3f
title: Public Work JSON Review
added_date: "2026-10-07 22:14:14"
last_updated: "2026-10-19"
summary: Live Work resolution in Manage, shared browser rendering, and ordered delivery of one static preparation owner for queued Publish and collection Export.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Public Work JSON Review

## Purpose And Status

Manage resolves all Work-derived presentation from current Working Work records, configured media policy/relationships and ready Working media. Working Build retains Work references and document-authored choices; it bakes no Work metadata. Work changes do not require rebuilding referring Working documents merely to display current Work data.

Publish and Export share one static preparation owner. It resolves selected generated documents against current Working inputs and returns complete static presentation plus exact required media. Publish prepares only queued documents and transfers the resulting artifacts through Preview. Export prepares only its checked collection documents and packages their referenced media.

Manage and public retain shared browser rendering components with separate live and prepared providers. Public renders its own document and opens its embedded Work Media View without fetching Work JSON, media policy or Series–Gallery metadata. Normal image requests, responsive selection and navigation remain browser responsibilities.

The design below resolves the runtime contracts, shared-code boundary, navigation and transfer handoffs. **Open issue OP-1 gates payload conversion and public activation:** the user must agree the initial conversion/publication selection and accept the Working snapshot it will publish. Implementation may proceed locally against the resolved design, but no conversion, publication or deployment is authorized by this document update. Existing lifecycle documentation still describes shipped behavior; [Builder](Builder.md), [Catalogue Deployment](Catalogue_Deployment.md), [Export](Export.md) and the [Development Checklist](Development_Checklist.md) change with implementation.

## Operating Model And Fixed Boundaries

| Owner | Responsibility |
| --- | --- |
| Studio Save / Refresh | Save canonical records and staged media, then explicitly hand selected ready inputs to Working through Refresh. Preserve the implemented [Save/Refresh boundary](Catalogue_Save_And_Refresh.md). |
| Working Build / Catalogue Regenerate | Build document-authored structure and Catalogue reference slots. Preserve required source generation, normal queue-only Regenerate and existing generation-to-queue handoffs. |
| Manage live provider | Resolve all Work-derived fields from available Working inputs on document activation or Media View activation; supply presentation to shared components. |
| Shared browser components | Display Entry, image, caption and Media View presentation; own responsive image behavior, interaction, navigation and disposal. |
| Shared static preparer | Read the selected generated documents and exact required Working Catalogue inputs; produce static payloads and required media identities for Publish or Export. |
| Publish | Read the existing queues once, prepare each selected current document/Work unit, persist prepared artifacts/media in Preview, transfer them and complete successful units under existing rules. |
| Export | Capture checked collection IDs, invoke static preparation, and use the existing Preview/Apply snapshot planner and writer. |
| Git / Deploy Public | Remain separate explicit actions over the committed `site/` artifact; there is no deploy-time document build. |

The queue is the complete authority for publication scope. Preserve its producers, schemas, selection rules, processing order, success removal and failure retention. Do not discover affected documents, queue referring documents automatically, rebuild during Publish or add another queue/ledger. Unqueued documents receive no preparation or publication work. Empty queues return before preparation or transfer setup.

The existing `PublicationPreparation` in [docs_publication_preparation.py](../../docs-viewer/services/docs_publication_preparation.py) owns Build-to-queue effects. It remains that owner. The new static presentation preparer is a separate responsibility, invoked by Publish and Export; its name must not conceal generation, eligibility calculation or queue mutation.

An already mounted Manage view retains the existing activation/refresh behavior. Reuse concurrent reads and loaded values within one resolution operation; a later activation resolves current Working inputs again. Do not retain a completed Work presentation as a freshness cache across activations or add mutation subscriptions.

Document-authored front matter, summary, link labels and layout remain document-owned. An authored document title remains source metadata even where Catalogue Regenerate originally supplied it; Work-derived Entry headings and captions resolve live. This delivery does not retitle navigation, Search or Recent independently of their existing owners.

## Resolved Design Contracts

These are the implementation contracts. Internal helper names and module layout may follow the existing owners; they must not change the behavior or handoffs specified here.

### 1. Working Reference Contract

Add an optional `catalogue` envelope to by-ID document JSON, omitted when the document contains no supported Catalogue references. It carries `schema: "docs_catalogue_presentation_v1"` and an ordered `references` array. Each reference has:

| Field | Meaning |
| --- | --- |
| `reference_id` | `c1`, `c2`, etc. in source occurrence order within the document, shared by the record and an HTML slot's `data-docs-catalogue-ref` attribute. Repeated references to the same Work retain separate authored options. |
| `target` | Existing exact Catalogue target: `kind` and `id`, using `catalogue-work` or `catalogue-gallery`. |
| `presentation` | `entry`, `image` or `media`, following the current semantic-token restrictions. Gallery remains a Media View target, not a Work Entry or image. |
| `options` | Only applicable authored fields: `use_work_title_caption`, `summary_html` (already rendered restricted HTML), `placement`, `fill_width` and `label` (authored Media View link text). Omit inapplicable fields. |

Build emits the slots and these records without opening Work records to fill them. It renders authored summary formatting once and preserves the existing token grammar/authoring authority. Work titles, alt text, intrinsic image dimensions, URLs, Entry metadata/resources and Gallery relationships are absent from the Working reference values. A Work ID is an identity, not baked metadata.

Build no longer calls Work presentation preparation for semantic rendering. Existing subject, relationship, discovery and queue owners retain their separately required work; this change does not remove a Work read needed by another demonstrated responsibility.

### 2. Resolved Presentation And Public Payload

Manage's live provider and the public prepared provider expose the same Work presentation contract, `schema_version: "docs_media_view_v2"`: `target`, `label` (Work title), `image`, `new_tab_target` and `galleries`, retaining the existing image-candidate, navigation-target and Gallery-link shapes. An Entry adds `entry` with `metadata_lines` and ordered `resources`; each resource carries `kind` (`download` or `link`), `label` and `url`. The unused top-level descriptive `metadata` array is removed. It contains no canonical source paths or authoring state. There is no v1 compatibility branch.

Entry formatting preserves the current display: title; year-display text; optional medium; non-null height/width/depth in that order joined by ` × ` with `cm`, omitting a trailing decimal zero; Catalogue number, separated from the preceding descriptive rows by the existing blank line; downloads followed by links in supplied order, with their supplied labels. Work Media View shows title, `cat.` and Gallery links, without the unused descriptive `metadata` array. Image-title captions/alt text use the resolved Work title. Authored summary, caption enablement, placement and fill-width remain independent options.

Static preparation adds a `presentations` map to the `catalogue` envelope, keyed as `<target.kind>:<target.id>` (for example `catalogue-work:00008`), and replaces each Work reference slot in `content_html` with complete visible markup. Working omits this map. A prepared document has one resolved presentation per distinct Work, with Entry fields included when its references require them. Preserve reference records so shared browser components can bind each occurrence without parsing its visible caption. Gallery-only references need no embedded Work presentation.

A prepared Catalogue Work document always includes its own resolved Work presentation, including the Media View fields needed when that Work is selected from a Gallery. A Work Media View link also has an embedded presentation even if no image appears inline. Gallery links retain their target and authored label; they do not embed an entire Gallery or its member Works.

Public uses only embedded Work presentations. It does not fall back to old Work JSON when a presentation is absent. Missing required selected input stops preparation under the existing error/completion model; it does not cause a source rebuild or another reader path. Documents without Catalogue references preserve their existing payload bytes when no other transformation is required.

### 3. Shared Rendering And Language Boundary

Keep the shared browser renderer and Media View components in canonical `docs-viewer/` runtime modules. Inject a presentation provider rather than letting those components perform Catalogue metadata reads. Manage's provider resolves live Working records; public's provider returns embedded presentation and reads another prepared document only on navigation.

Use one Python static preparation service for both Publish and Export. It performs selected filesystem reads, resolves current Work data and serializes complete HTML/presentation. It has no queue or destination writes. Existing Python workflows call it directly; this design adds no Node service, browser automation, server DOM engine or general template engine.

There are two required serialization adapters: browser JavaScript mounts live presentation, and Python emits static markup. They follow the same field/formatting contract, HTML slot/class contract, canonical media policy and icon assets. Share browser rendering between Manage/public and Python preparation between Publish/Export; do not claim executable code is shared across Python and JavaScript. This bounded duplication of serialization is deliberate. Do not create separate field-selection or formatting rules for Publish and Export, duplicate policy constants, or move Manage reads to Python merely to reuse a helper.

The shared browser mount binds prepared public markup and Media View data without another metadata lookup or an unnecessary replacement of complete static content. Manage fills the same presentation structure from its live provider. Preserve shared styles, image layout, event/disposal handling and new-tab behavior.

### 4. Preparation Inputs, Outputs And Media Handoff

The static preparation interface accepts an exact document target and already loaded generated payload, resolved Working/media configuration, and operation-local Catalogue input reuse. Its caller owns selection. Resolve each distinct required Work, policy and relationship input once within the operation and carry those values forward. Load nothing for unrelated Works or documents without relevant references.

Return a prepared payload object, including final `content_html` and embedded presentation, plus distinct media descriptors. Each descriptor identifies the configured owner/type and exact object identity; it contains no byte totals or persistent provenance. Publish serializes the payload once, writes those JSON bytes to Preview and transfers the same bytes. Export uses the carried payload directly, with no JSON reparse or second Work resolver.

Catalogue media retains its Work owner and `document_media: false` boundary. Ordinary document media retains its existing owner and queue selection. Do not copy Work images into document-media folders, restore the retired by-ID media list, or infer media through remote URL requests.

For a Docs-queue document referencing a Work, preparation supplies its required ready rendition/file objects as part of that document's transfer unit, even if there is no pending Catalogue Work image selection. These operation-local inputs do not enqueue another Work or change the saved queue schema. For an existing Catalogue Work unit, preserve its queued image/file selection facts: unchanged images/downloads do not gain a blanket transfer merely because metadata was prepared. Merge actual required transfers and deduplicate exact owner/object identities across the operation, reusing completed transfer effects.

Prepare and complete units in the existing order: Catalogue Work units, Docs document/deletion/shared units, then Catalogue shared output. Resolve/prep a current unit before its required Preview writes/transfers; do not prepare every queued unit in advance. Remove only the fully successful unit. A failure leaves that unit pending and retains prior completed effects. Deletion/shared-only units keep their existing paths and do not invoke Work baking. Empty queues do no preparation.

Retain selected input parsing, escaping/URL safety, configured ownership, path/symlink confinement, actual missing-input errors and selected transfer verification. Domain validation stays upstream. No content audits, freshness scans, canonical source reads, full inventories, additional hashes or retry/rollback machinery belong in preparation/transfer. Export's existing exact-bytes confirmation remains intentional.

### 5. Public Navigation And Inventory

Resolve a Work selected from a public Gallery by reading its prepared Catalogue document through the existing exact document target `collection: catalogue, doc_id: <work_id>`, then selecting its embedded Work presentation. This is navigation to another prepared target, not a Work JSON lookup or a rebuild. Share the existing Gallery paging/navigation UI.

Retain existing Gallery membership JSON and its policy-based thumbnail path for Gallery browsing. That navigation may load its Gallery record and required thumbnail policy; opening a document's own embedded Work presentation does not. Do not eagerly read every Gallery member's document or embed all member presentations in each referring document.

Remove the public provider's Work-record and Series–Gallery resolution paths from document/Work presentation. Retain those paths in Manage's live provider. Public media policy remains available for Gallery and other active thumbnail consumers, so it is not removed wholesale.

**Inventory decision:** keep the existing physical Catalogue JSON distribution and its queue selections in this delivery. Working Work JSON remains required by Manage; public Work/Series–Gallery files cease to be dependencies of the new document renderer, but their physical publication/removal is a separate cleanup after cutover and consumer review. No legacy reader fallback or alias is retained. Cleanup removal criteria are: new reader and prepared payload cutover accepted, all remaining public consumers mapped, and explicit output-removal scope agreed. Do not turn that cleanup into queue schema or selection changes during this delivery.

### 6. Export Adapter And Confirmation

Export invokes the same static preparer once for each checked generated document, sharing operation-local inputs across the selection. Its existing media pass maps the returned Work-media descriptors and document-owned references to deterministic package paths. Read each distinct selected object once per request, package only emitted candidates/linked files, and retain existing behavior for unrelated external dependencies.

The browseable snapshot contains visible images, captions and summaries without Docs Viewer JavaScript. Convert Work image/text Media View openers to ordinary links to their packaged largest-image target while retaining the image or authored label. Gallery Media View controls retain their authored text without interactive Gallery browsing; Export does not fetch/package every Gallery member. The text-first `portable.html` retains its existing intentional image-placeholder contract.

Preview remains write-free. Apply reruns preparation once against the same selected targets, and the existing plan revision covers prepared titles/HTML and packaged media bytes so a meaningful Work change invalidates the earlier confirmation. Carry prepared values through that request's writing and final verification. Preserve replacement decisions, destination checks, final file-set/byte verification and all six accepted Export cleanups.

## Open Issue OP-1: Initial Conversion And Public Activation

Existing Working payloads may lack authored reference options, and existing public payloads lack embedded presentations. The new providers must not infer lost options from old HTML or keep an old-payload Work lookup fallback. Explicit selected generation is needed to introduce the Working contract, and queued preparation is needed before affected public payloads can use the new reader.

**Recommendation:** agree one explicit conversion selection, generate those Working targets under the new contract through ordinary owners, and use the resulting existing queues for a one-time publication of the affected approved public documents. Ship the prepared repository payloads and projected public reader together through the ordinary explicit Git/deployment workflow. After cutover, every Publish again consumes only its normal current queues.

**Decision required:** which exact Working targets may be regenerated and which public targets may be republished from current Working content/data, including any unpublished edits already present, and when public activation is authorized. The selection must cover affected existing public targets before switching their reader. This document does not authorize or silently insert a bulk conversion, queue expansion, publication or deployment.

Publish continues to consume both complete existing queues. The cutover decision must therefore account for entries already pending and the ordinary queue effects of approved generation; it cannot pick a migration subset at Publish time. Do not filter, clear or rewrite existing selections to manufacture a separate cutover batch. If their combined publication is not approved, defer activation until that scope is agreed.

OP-1 blocks the conversion/public-activation step, not local code delivery. If the full affected public selection is not yet approved, keep the new reader local/unactivated; do not introduce a compatibility mode or partially activate it against unsupported payloads. Existing current media locations remain in use; this is not an immutable historical snapshot/version-store project.

## Delivery Summary

- Live Work resolution in Manage.
- Shared rendering with separate data providers.
- One static preparation owner for Publish and Export.
- **Build:** retains Work references and authored choices; bakes no Work metadata.
- **Manage:** resolves all Work-derived presentation through the live provider.
- **Publish Preparation:** bakes current Working data into static output for queued documents. Export invokes the same preparation for its snapshots.
- **Queues:** retain their current selection and completion behavior. Only queued documents are prepared and published.

## Workflow Changes

- **Build:** replace Work metadata lookups/rendered values with explicit reference slots and authored options.
- **Manage:** resolve Work titles, captions, Entry metadata/resources, images and Media View relationships through the live provider.
- **Shared runtime:** inject live/prepared providers into the shared renderer and keep public Work resolution out of its import path.
- **Publish:** call static preparation inside each existing current unit before Preview persistence/transfer, carrying exact prepared values through completion.
- **Export:** call that same preparer, package configured Work media and make static Work openers ordinary image links.
- **Public navigation:** read a selected Work's prepared Catalogue document; retain Gallery membership/thumbnail inputs and existing physical Catalogue JSON distribution.
- **Cutover:** perform only an explicitly agreed conversion/queued publication and activate the public reader with its prepared payloads.

## Implementation Sequence And Completion Gates

Each unchecked step is a delivery with named inputs, outputs and completion criteria. These are ordered implementation results, not further product-design tasks. No implementation, generation or publication has occurred in this documentation revision.

### 1. Confirm The Contract And Owner Map

- [ ] **Inputs:** the resolved contracts above and current Build, provider, publication and Export owners.
- **Delivers:** a concise mapping of those contracts to the existing owners, an explicit new static-preparer boundary separate from Build-to-queue `PublicationPreparation`, and confirmation that OP-1 is the only outstanding release decision.
- **Done when:** each input read, output write, reference/presentation field and queue completion effect has one owner; no queue, full-build, discovery or runtime dependency expansion has been introduced. Stop and raise any material contradiction rather than resolving it through a hidden fallback.

### 2. Deliver Reference-Only Working Build

- [ ] **Inputs:** selected Markdown documents, validated semantic tokens and their authored options.
- **Delivers:** `catalogue.references`, deterministic HTML slots and document-authored markup; removal of Work presentation reads/values from semantic Build output.
- **Done when:** Entry, image, Work Media View link, repeated Work references and Gallery link references retain all applicable authored choices; no Work title, caption value, Entry metadata/resources, image dimensions/URLs or relationship labels are resolved by Build. Unrelated document metadata, generation and queue producers retain current behavior. OP-1 controls writes to existing Working documents.

### 3. Deliver Live Manage And Shared Browser Rendering

- [ ] **Inputs:** new Working reference records, current Working Work/policy/relationship inputs and the existing shared document/Media View components.
- **Delivers:** the Manage-only live provider, provider-driven shared Entry/image/Media View rendering, and the public provider interface for embedded presentation; removal of the unused Media View descriptive metadata array.
- **Done when:** Work-derived fields resolve at each ordinary document/media activation without rebuilding the referring document, each operation reuses its loaded inputs, authored choices remain intact, and shared rendering performs no Work metadata reads. Preserve error/disposal/activation behavior and the Entry/Image/Media View presentation distinctions.

### 4. Deliver The Shared Static Preparer

- [ ] **Inputs:** explicit selected targets and already loaded payloads, resolved Working/media configuration and operation-local Catalogue inputs.
- **Delivers:** one Python entry point returning complete static payloads plus exact configured media descriptors, including visible image markup and embedded Work presentation.
- **Done when:** Entry, image and Work-link output uses the same field/formatting contract as Manage; distinct Work reads are reused; image candidates and linked files have exact owners; no input payload, queue or destination is mutated. A document without references needs no Work/policy read. Both Publish and Export can consume the same result without another resolver.

### 5. Deliver Queue-Preserving Publish Integration

- [ ] **Inputs:** the unchanged Docs/Catalogue queues, existing current/deleted/shared selections, the static preparer and configured Preview/public destinations.
- **Delivers:** per-current-unit preparation followed by existing Preview/transfer/completion paths, with operation-local media merging/deduplication.
- **Done when:** both Catalogue Work and Docs document units receive the correct prepared output; a referring document can carry required Work media without another Work queue entry; metadata-only Work selections do not acquire blanket media uploads; deletes/shared-only units bypass baking; empty queues remain a no-op. Preparation/transfer failure retains the current unit and prior successful effects. Queue schemas, producers, selected document sets, processing order and completion rules are unchanged; no unqueued document is opened or built.

### 6. Deliver Export Preparation And Work-Media Packaging

- [ ] **Inputs:** the existing checked collection selection, generated metadata/payloads, shared preparation results and snapshot Preview/Apply machinery.
- **Delivers:** static Catalogue images/Entry content and usable Work image links in browseable snapshots, exact Work/document media packaging and confirmation based on prepared output.
- **Done when:** snapshots need no viewer runtime or public image download; repeated references share packaged objects; a Work presentation/media change between Preview and Apply changes the confirmed plan; replacement and final verification retain current behavior. `portable.html`, unrelated external dependencies and queue state retain their stated contracts.

### 7. Deliver Public Prepared Navigation And Runtime Projection

- [ ] **Inputs:** prepared document payloads, the shared browser renderer, configured Catalogue document/Gallery roots and the site-code projection inventory.
- **Delivers:** the public embedded-presentation provider, Gallery-to-prepared-Work loading, public import separation and the tracked runtime/config projection.
- **Done when:** initial document/own Work Media View requires no Work JSON, policy or Series–Gallery read; selecting another Work reads only its prepared Catalogue payload; Gallery browsing stays lazy and retains required membership/thumbnail data. Public has no management/live Work capability, Working inputs remain available to Manage, and physical Catalogue JSON distribution remains unchanged. Projection/check/site validation pass; public activation remains gated by OP-1.

### 8. Complete Review, Cutover Readiness And Acceptance

- [ ] **Inputs:** completed steps 1–7, the acceptance/evidence plan below and an explicit OP-1 decision for any existing-payload conversion or public activation.
- **Delivers:** a distinct redundancy/defensive review, updated durable contracts, selected verification results, and an explicit code-ready versus activated/accepted status. If OP-1 remains open, record local code readiness and leave activation pending.
- **Done when:** review covers normal/empty/failed selected-unit paths and reused helpers, resolves duplicated reads/rendering/validation, and justifies retained safeguards. Update Generated Data Contracts, media/Media View, Builder, Catalogue Save/Refresh/Deployment, Export and Development Checklist ownership; run applicable source lint/syntax and runtime projection checks. Perform only approved conversion/queued publication/deployment and record actual user acceptance separately. Do not mark the whole delivery complete while required cutover/acceptance remains pending.

## Acceptance And Evidence Plan

No new or changed tests, fixtures, temporary regression scripts or browser automation are authorized by this plan. Implementation uses focused source/diff review, changed-file Python/JavaScript lint, applicable syntax/import diagnostics and the existing site-code projection/site validation commands. Choose any existing documented test selection separately by demonstrated need and cost; test additions/changes require their own approved specification.

Manual acceptance covers these distinct boundaries using agreed representative documents, with Work `00008`, nerve, and Context document `d-20260801-073846-e0a9ec` available as presentation references:

| Boundary | Required observation |
| --- | --- |
| Manage live resolution | After an ordinary saved Work change and Refresh, reopen an unchanged referring document: Entry/title caption/image/Media View use the available current Work data without its Build. Authored summary/layout remain unchanged. |
| Public snapshot | A queued Publish embeds the current Work data. Later Working changes do not trigger a Work metadata lookup from that published document. Image bytes retain the existing publication/location model. |
| Queue scope/completion | With one selected current unit, unqueued documents are not read, prepared, built or written; empty queues perform no preparation. A failure retains its unit and previously completed effects under existing rules. |
| Media ownership | A queued referring document can publish/export its actual Work rendition/file references without a separate Work image selection; an unchanged Catalogue Work image selection causes no blanket transfer. |
| Export | Browseable output shows Catalogue images/Entry content and packaged Work links without viewer JavaScript. Preview/Apply detects changes to prepared content/media; portable output keeps its text-first behavior. |
| Public navigation | Open embedded Work Media View, then a Gallery and another Work: lazy Gallery browsing and prepared Catalogue-target loading work without a public Work-record reader. |
| Cutover | Every approved affected public target has the prepared contract before the new reader activates. Conversion/publication selections and actual Git/deployment actions match the OP-1 decision. |

These are acceptance outcomes, not permission to run live Save, Refresh, Build, Export, Publish or deployment in this documentation task. Future verification must state exact targets, costs and write/network effects before execution. Keep static diagnostics, manual product observations and publication/deployment evidence distinct.

## Review Evidence

The original review established the nerve presentation reference. The 2026-10-19 discussion settled live Manage resolution of all Work presentation, no Work metadata baking in Build, shared browser rendering and shared static Publish/Export preparation with unchanged queue behavior. Scoped source review checked semantic rendering/selected inputs, workspace/media providers, Build-to-queue handoffs, both publication unit owners and Export planning.

This revision changes documentation only. It resolves the design contracts and replaces the former workstream checklist with ordered input/output/completion deliveries. OP-1 is explicitly open. No product code, generated payloads, media, queues, snapshots or public destinations are changed. Code review is not applicable; bounded documentation/source review and whitespace checking apply. No tests or live workflow/deployment operations ran.
