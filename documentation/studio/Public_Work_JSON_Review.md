---
draft: false
doc_id: d-20261007-221414-48ff3f
title: Public Work JSON Review
added_date: "2026-10-07 22:14:14"
last_updated: "2026-10-19"
summary: Complete and user-accepted; live Manage Work resolution and shared static preparation for Publish, Export and Prepare package.
ui_status: done
parent_id: d-20260428-000000-f5ff18
---
# Public Work JSON Review

## Purpose And Status

Manage resolves all Work-derived presentation from current Working Work records, configured media policy/relationships and ready Working media. Working Build retains Work references and document-authored choices; it bakes no Work metadata. Work changes do not require rebuilding referring Working documents merely to display current Work data.

Publish and Export share one static preparation owner. It resolves selected generated documents against current Working inputs and returns complete static presentation plus exact required media. Publish prepares only queued documents and transfers the resulting artifacts through Preview. Export prepares only its checked collection documents and packages their referenced media.

Manage and public retain shared browser rendering components with separate live and prepared providers. Public renders its own document and opens its embedded Work Media View without fetching Work JSON, media policy or Series–Gallery metadata. Normal image requests, responsive selection and navigation remain browser responsibilities.

Status: complete and user-accepted on 2026-10-19. Implementation, distinct source review, Working payload conversion, normal Publish, Export creation/replacement and the approved Prepare package adapter are complete. The user accepted the 800px Export correction, confirmed the restored compact Catalogue Related Links styling and requested closeout, with remaining checks continuing through normal use. Commit, push and deployment remain separate explicit actions and were not performed.

Current contracts are maintained in [Generated Data Contracts](Generated_Data_Contracts.md#catalogue-reference-and-presentation), [Catalogue Media View](Catalogue_Media_View.md), [Builder](Builder.md#publish-preparation), [Catalogue Deployment](Catalogue_Deployment.md), [Export](Export.md), [Package Prepare](Package_Prepare.md) and [Related Links](Related_Links.md). This closed delivery and its [retired handoff](Public_Work_JSON_Handoff.md) are retained for evidence lookup pending manual archive.

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

The browseable snapshot contains visible images, captions and summaries without Docs Viewer JavaScript. Convert Work image/text Media View openers to ordinary links to the packaged standard `image.src` rendition, currently 800px, while retaining the image or authored label. Export omits larger responsive candidates, original dimensions and the viewer's fixed frame ratio; images retain their natural size and shrink proportionally to the available page width. Gallery Media View controls retain their authored text without interactive Gallery browsing; Export does not fetch/package every Gallery member. The text-first `portable.html` retains its existing intentional image-placeholder contract.

Preview remains write-free. Apply reruns preparation once against the same selected targets, and the existing plan revision covers prepared titles/HTML and packaged media bytes so a meaningful Work change invalidates the earlier confirmation. Carry prepared values through that request's writing and final verification. Preserve replacement decisions, destination checks, final file-set/byte verification and all six accepted Export cleanups.

## Initial Payload Conversion And Public Activation

The user-confirmed empty queues supplied the cutover baseline. Affected Working payloads were converted to the new reference/options contract and normal Publish produced the prepared public payloads. Conversion and publication are complete; Git/deployment remain separate explicit release actions.

Conversion used existing generation owners, including Catalogue's explicit design-maintenance owner, with current Working sources/data. It preserved draft/exclusion policy and ordinary generation-to-queue effects, without inferring authored options from old HTML, adding a legacy lookup fallback or running media production.

Normal Publish consumed the resulting queues, preparing only selected documents with its existing selection/completion behavior. The one-time generation belonged to contract conversion; ordinary Publish never discovers or rebuilds referring documents. No migration queue, queue filtering, forced selection or queue reset was added.

The prepared repository payloads and projected public reader must ship together through the ordinary explicit Git/deployment workflow. No commit, push or deployment ran during this delivery. There is no additional cutover approval mechanism or freshness audit; Build, Publish and deployment retain their ordinary explicit execution boundaries.

Existing current media locations remain in use; this is not an immutable historical snapshot/version-store project. New queues populated by subsequent ordinary work continue to be handled normally.

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
- **Cutover:** convert affected Working payloads from the clean baseline, publish through the normal queues and deploy the public reader with its prepared payloads.

## Implementation Sequence And Completion Gates

All eight implementation and closeout steps are complete. The user approved the Prepare package adapter through the shared static preparer and accepted delivery closeout on 2026-10-19. Remaining behavioral checks will accumulate through normal use; explicit Git/deployment is separate from this completed delivery.

Checkmarks record completed implementation, review and accepted closeout, rather than claiming every acceptance scenario was exercised. Conversion, normal Publish, Export creation/replacement and two Prepare package dry-runs completed. The shared `Open <Work title>` label, 800px Export image/fitting styles and wrapper-aware compact Related Links styling are delivered. The nerve snapshot contains eight files/three media objects. Recorded evidence and the remaining normal-use observations are below.

### 1. Confirm The Contract And Owner Map

- [x] **Inputs:** the resolved contracts above and current Build, provider, publication and Export owners.
- **Delivers:** a concise mapping of those contracts to the existing owners and an explicit new static-preparer boundary separate from Build-to-queue `PublicationPreparation`. Use the user-confirmed empty-queue baseline for planned conversion.
- **Done when:** each input read, output write, reference/presentation field and queue completion effect has one owner; no queue, full-build, discovery or runtime dependency expansion has been introduced. Stop and raise any material contradiction rather than resolving it through a hidden fallback.

**Owner map:** `docs_builder.semantic_tokens` and `payloads` own reference records/slots and authored markup; `docs_generation` and `PublicationPreparation` retain generation-to-queue effects. The workspace provider supplies data to shared browser rendering/Media View; Manage resolves Working inputs and public consumes embedded presentations. A separate static presentation service will return prepared payloads/media to `docs_catalogue_publication`, `docs_selected_publication` and `docs_static_html_export`; these callers retain their existing persistence, transfer and completion responsibilities. The empty-queue conversion baseline remains the user-confirmed baseline; no queue read or live operation was needed for readiness.

**Agreed Prepare package boundary:** content-bearing Prepare package requests use the same static preparer before their existing output transformations, preserving Work titles/captions and Catalogue Entry content. The adapter carries selected renderer output and its reference envelope into preparation, reuses operation-local inputs, and adds no media packaging, generation, queue changes or separate Work formatter. Tree-only output retains its existing metadata owner. The user approved this addition on 2026-10-19.

### 2. Deliver Reference-Only Working Build

- [x] **Inputs:** selected Markdown documents, validated semantic tokens and their authored options.
- **Delivers:** `catalogue.references`, deterministic HTML slots and document-authored markup; removal of Work presentation reads/values from semantic Build output.
- **Done when:** Entry, image, Work Media View link, repeated Work references and Gallery link references retain all applicable authored choices; no Work title, caption value, Entry metadata/resources, image dimensions/URLs or relationship labels are resolved by Build. Unrelated document metadata, generation and queue producers retain current behavior. Existing payload conversion is completed in step 8.

### 3. Deliver Live Manage And Shared Browser Rendering

- [x] **Inputs:** new Working reference records, current Working Work/policy/relationship inputs and the existing shared document/Media View components.
- **Delivers:** the Manage-only live provider, provider-driven shared Entry/image/Media View rendering, and the public provider interface for embedded presentation; removal of the unused Media View descriptive metadata array.
- **Done when:** Work-derived fields resolve at each ordinary document/media activation without rebuilding the referring document, each operation reuses its loaded inputs, authored choices remain intact, and shared rendering performs no Work metadata reads. Preserve error/disposal/activation behavior and the Entry/Image/Media View presentation distinctions.

### 4. Deliver The Shared Static Preparer

- [x] **Inputs:** explicit selected targets and already loaded payloads, resolved Working/media configuration and operation-local Catalogue inputs.
- **Delivers:** one Python entry point returning complete static payloads plus exact configured media descriptors, including visible image markup and embedded Work presentation.
- **Done when:** Entry, image and Work-link output uses the same field/formatting contract as Manage; distinct Work reads are reused; image candidates and linked files have exact owners; no input payload, queue or destination is mutated. A document without references needs no Work/policy read. Both Publish and Export can consume the same result without another resolver.

### 5. Deliver Queue-Preserving Publish Integration

- [x] **Inputs:** the unchanged Docs/Catalogue queues, existing current/deleted/shared selections, the static preparer and configured Preview/public destinations.
- **Delivers:** per-current-unit preparation followed by existing Preview/transfer/completion paths, with operation-local media merging/deduplication.
- **Done when:** both Catalogue Work and Docs document units receive the correct prepared output; a referring document can carry required Work media without another Work queue entry; metadata-only Work selections do not acquire blanket media uploads; deletes/shared-only units bypass baking; empty queues remain a no-op. Preparation/transfer failure retains the current unit and prior successful effects. Queue schemas, producers, selected document sets, processing order and completion rules are unchanged; no unqueued document is opened or built.

### 6. Deliver Export Preparation And Work-Media Packaging

- [x] **Inputs:** the existing checked collection selection, generated metadata/payloads, shared preparation results and snapshot Preview/Apply machinery.
- **Delivers:** static Catalogue images/Entry content and usable Work image links in browseable snapshots, exact Work/document media packaging and confirmation based on prepared output.
- **Done when:** snapshots need no viewer runtime or public image download; repeated references share packaged objects; a Work presentation/media change between Preview and Apply changes the confirmed plan; replacement and final verification retain current behavior. `portable.html`, unrelated external dependencies and queue state retain their stated contracts.

### 7. Deliver Public Prepared Navigation And Runtime Projection

- [x] **Inputs:** prepared document payloads, the shared browser renderer, configured Catalogue document/Gallery roots and the site-code projection inventory.
- **Delivers:** the public embedded-presentation provider, Gallery-to-prepared-Work loading, public import separation and the tracked runtime/config projection.
- **Done when:** initial document/own Work Media View requires no Work JSON, policy or Series–Gallery read; selecting another Work reads only its prepared Catalogue payload; Gallery browsing stays lazy and retains required membership/thumbnail data. Public has no management/live Work capability, Working inputs remain available to Manage, and physical Catalogue JSON distribution remains unchanged. Projection/check/site validation pass. Runtime and prepared payloads must ship together through the separate explicit Git/deployment workflow.

### 8. Complete Review, Payload Conversion And Acceptance

- [x] **Inputs:** completed steps 1–7, current Working sources/data from the clean baseline, affected Catalogue-reference targets and the acceptance/evidence plan below.
- **Delivers:** a distinct redundancy/defensive review, updated durable contracts, converted Working payloads, normally queued/prepared public payloads and recorded acceptance. Keep code, conversion, Publish and Git/deployment completion distinguishable.
- **Done when:** review covers normal/empty/failed selected-unit paths and reused helpers, resolves duplicated reads/rendering/validation, and justifies retained safeguards. Durable ownership, applicable source diagnostics, runtime projection checks, affected-document conversion and ordinary queued Publish are complete. Record the user's accepted closeout with remaining checks continuing through normal use. Commit, push and deployment remain separate explicit actions. No queue selection/schema/completion changes or special approval gate are introduced.

## Acceptance And Evidence Plan

No new or changed tests, fixtures, temporary regression scripts or browser automation are authorized by this plan. Implementation uses focused source/diff review, changed-file Python/JavaScript lint, applicable syntax/import diagnostics and the existing site-code projection/site validation commands. Choose any existing documented test selection separately by demonstrated need and cost; test additions/changes require their own approved specification.

The user accepted closeout and will cover remaining behavioral observations through normal use. These boundaries remain the evidence map, with Work `00008`, nerve, and Context document `d-20260801-073846-e0a9ec` available as presentation references:

| Boundary | Normal-use observation |
| --- | --- |
| Manage live resolution | After an ordinary saved Work change and Refresh, reopen an unchanged referring document: Entry/title caption/image/Media View use the available current Work data without its Build. Authored summary/layout remain unchanged. |
| Public snapshot | A queued Publish embeds the current Work data. Later Working changes do not trigger a Work metadata lookup from that published document. Image bytes retain the existing publication/location model. |
| Queue scope/completion | With one selected current unit, unqueued documents are not read, prepared, built or written; empty queues perform no preparation. A failure retains its unit and previously completed effects under existing rules. |
| Media ownership | A queued referring document can publish/export its actual Work rendition/file references without a separate Work image selection; an unchanged Catalogue Work image selection causes no blanket transfer. |
| Export | Browseable output shows Catalogue images/Entry content and packaged Work links without viewer JavaScript. Preview/Apply detects changes to prepared content/media; portable output keeps its text-first behavior. |
| Public navigation | Open embedded Work Media View, then a Gallery and another Work: lazy Gallery browsing and prepared Catalogue-target loading work without a public Work-record reader. |
| Cutover | Affected Working documents have the new reference contract, their ordinary queued publication produces prepared public payloads, and the new public reader deploys with those payloads. Queue behavior is unchanged. |

The accepted closeout does not establish unexercised outcomes. Keep static diagnostics, manual product observations and publication/deployment evidence distinct. Any future Codex-run verification must have a proportionate stated purpose, selection, cost and effects; no additional test work or live operation was performed solely for closeout.

## Review Evidence

The original review established the nerve presentation reference. The 2026-10-19 discussion settled live Manage resolution of all Work presentation, no Work metadata baking in Build, shared browser rendering and shared static Publish/Export preparation with unchanged queue behavior. Scoped source review checked semantic rendering/selected inputs, workspace/media providers, Build-to-queue handoffs, both publication unit owners and Export planning.

Implementation now covers reference-only Build, live Manage/prepared public providers, shared browser rendering, one static preparer, queued Publish, collection Export and the approved Prepare package adapter. Work-record/Series–Gallery public reader paths and v1 Work presentation handling are removed; physical Catalogue JSON distribution remains. Lint passed for 21 changed Python and nine canonical JavaScript owners; compilation/import diagnostics, distinct source review, runtime projection and site validation passed. Tests remain unchanged and unrun.

The existing builder's read-only selections for Catalogue `00008` and Works `d-20260801-073846-e0a9ec` passed without warnings. Conversion then wrote 4,618 Catalogue, nine exact Works and one ordinary Working payload through existing Build owners with media builds skipped; all three operations reported zero warnings/removals. Normal Publish completed 4,623 units with 40 media transfers and no removals: all Catalogue documents and five eligible referring documents. The five other converted Works documents remain drafts. Representative output inspection confirmed Working reference-only slots and the public nerve payload's complete visible Entry, embedded v2 presentation, compact dimensions and ordered resources.

The initial write-free Catalogue `00008` Export preview failed the existing readable/writable check for the configured export workspace outside this session's writable roots. The user authorized a retry with broader filesystem access; it succeeded with one document, five packaged media objects, zero external dependencies and an absent destination. No fallback or configuration change was needed. Existing `document-content` Prepare package dry-runs for Catalogue `00008` and Works `d-20260801-073846-e0a9ec`, using JSON/Markdown, each exported one record with no warnings, errors, skips or truncation. They wrote no package files; the service appended its normal local operation log.

The user then confirmed creating the previewed nerve snapshot. Ordinary Apply consumed the exact preview revisions and created `$DOTLINEFORM_PROJECTS_BASE_DIR/docs-export/catalogue selection - 2026-10-19/`: one document, five media objects, ten files, no external dependencies and no replacement. Its existing final file-set/byte verification passed. Required output inspection confirmed relative packaged image/srcset/download links and a largest-image opener, and found that the anchor retained its Media View accessibility label. The user approved the simpler `Open <Work title>` form for both main code and Export. The browser renderer and Python preparer now emit that shared form, retaining existing title escaping without an Export-specific formatter. Focused lint/compilation, source review and runtime projection/site validation passed. The same affected document selections were handed through normal Build/Publish to refresh prepared markup: Working bytes remained unchanged, all builds reported zero warnings/removals, and Publish completed 4,623 units with its existing 40 selected-media completion effects. No source or queue contract changed.

A fresh ordinary replacement preview for the nerve snapshot reported the same one document/five media objects/zero external dependencies and the existing directory target. The user's requested label correction was completed through ordinary Apply with those exact revisions and replacement enabled; the ten-file snapshot passed final file-set/byte verification. Inspection confirmed `aria-label="Open nerve"` in both prepared public output and exported HTML. Live Work mutation/Refresh, broader browser interactions, stale-preview rejection/failure variants and actual package-file creation remain outside the recorded evidence and will continue through normal use. No commit, push or deployment ran; runtime and prepared payloads must ship together through those separate explicit actions.

The user then reported the Export image choosing 1600px and overflowing the page, and requested the standard 800px image. The Export adapter now links to the already supplied `image.src`, omits Work image responsive candidates/original dimensions and the generated frame ratio, and applies proportional maximum-width CSS. Focused lint/compilation passed. Fresh ordinary Preview/Apply replaced the same snapshot with one document, three media objects, eight files and zero external dependencies; final file-set/byte verification passed. Output inspection confirmed the image and opener both use the packaged 800px rendition, with no fixed image dimensions and the width-limit rule present. This Export-only correction required no document Build, Publish or public runtime projection. The user accepted the correction and authorized continuation, later accepting closeout with the other behavioral checks continuing through normal use. Explicit Git/deployment remains separate.

The user subsequently reported that Catalogue Related Links had regained the large `context` heading/divider and body-size links. The new reference wrapper separated the Entry from its related-links sibling, so the two existing compact-style selectors no longer matched. Shared CSS now selects the reference wrapper containing the Entry before its related-links sibling. The original font, divider and padding rules are retained; no document markup/data or pin behavior changed. The exact tracked public CSS projection was inspected, and projection check, site validation and scoped whitespace checks passed. No document rebuild, Publish or tests ran. The user confirmed the styling fix and requested delivery closeout.

### Code Review And Defensive Behavior

The distinct source/diff review traced reference generation, live activation/disposal, static serialization, package transformations, current/deleted/shared/empty publication paths and snapshot media planning. It removed Build's Work-cache plumbing, repeated Work metadata reads during physical Catalogue JSON publication, unused public route readers/configuration and static policy revalidation of producer-owned fields. Icon artwork was extracted from Markdown parsing so selected static preparation does not inherit a builder/bootstrap dependency. Public prepared markup binds once; Gallery navigation reads the selected prepared Catalogue target, and retained Manage activation creates a fresh live operation.

Retained safeguards are selected JSON parsing and actual missing-input errors, confined configured paths and selected object identities, HTML escaping/resource URL safety, existing icon sanitization, responsive-image/Media View disposal and selected Preview/transfer verification. These protect concrete filesystem, markup and transfer boundaries; there are no new corpus audits, fallback readers, queue ledgers, automatic repair or recovery policies. Export retains its agreed exact-bytes Preview/Apply confirmation and reads each emitted object once. Static checks do not establish live Work mutation, UI presentation, real failure retention or deployed cutover behavior.

The label follow-up received a separate bounded source review after focused diagnostics. Both changes are serialization expressions using the already escaped Work title; Export inherits the result through the existing shared preparer. No additional lookup, markup rewrite rule, fallback or validation was added. Public refresh used existing queue producers and normal Publish, and snapshot replacement used the existing Preview/Apply comparison and verification.

The Export sizing follow-up received a distinct bounded source/diff and redundancy/defensive review after its diagnostics and actual replacement. The existing HTML pass selects the carried standard image URL before collecting media, so unused larger renditions are neither read nor packaged. Generated Work controls alone lose viewer dimensions/frame styling; ordinary image URLs retain their existing handling and the shared snapshot CSS constrains image width. No second Work resolution, image-policy constant, image-byte processing, extra validation, compatibility path or rebuild was added. Existing confined object reads, exact-byte confirmation and final verification remain justified at the export filesystem boundary.

The continuation update records the user's acceptance of the Export correction and reconciles current delivery status. Code review is not applicable to this status-only update because no code changed; bounded documentation review reuses the implementation evidence above. No repeat generation, Publish, test run or deployment was performed.

The Related Links follow-up received a distinct bounded CSS/source review after projection and diagnostics. Both live and prepared renderers retain the same reference wrapper around Entry; the revised selectors follow that current structure, including the reader-inserted heading/pin wrapper, and override the generic H2 rules with the existing compact styles. The obsolete direct-Entry sibling selectors were replaced without compatibility alternatives. Presentation remains CSS-owned, with no added browser/server calls, validation, scanning, fallback or generated-data work. Ordinary related-links sections, pin behavior and empty-section omission retain their existing owners.

## Accepted Closeout

The user confirmed the restored Catalogue Related Links presentation and explicitly requested closeout on 2026-10-19, with remaining checks continuing through normal use. No unresolved implementation issue remains. Live Work mutation/Refresh, repeated references, lazy Gallery navigation/public prepared reads, changed-preview and failure/empty-unit variants, and actual package-file output remain outside the recorded behavioral evidence; these omissions do not hold the accepted delivery open.

This closeout changes documentation only. Code review is not applicable because no implementation changed; bounded source/status/link review reuses the completed implementation and projection evidence. No test, generator, Publish, commit, push or deployment was repeated or performed for closeout. The closed delivery and retired temporary handoff remain available pending manual archive; durable owners linked above maintain current behavior.
