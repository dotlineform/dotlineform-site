---
draft: false
doc_id: d-20261007-221414-48ff3f
title: Public Work JSON Review
added_date: "2026-10-07 22:14:14"
last_updated: "2026-10-08 17:14:37"
summary: Review the Studio Refresh handoff, complete rendered Work media, consistent updates and shared Full Rebuild optimisation.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Public Work JSON Review

## Purpose And Status

Review whether readers or generation need separate Work by-ID JSON in either Working or public output when Catalogue documents already contain rendered Work content. The intended improvement is simpler loading and a clear, consistent point at which Catalogue changes appear in document text, images and Media View. The agreed presentation direction follows the current representation of Work `00008`, nerve: full descriptive Work metadata in the Catalogue document, title/`cat.`/Gallery links in Media View, and title with optional authored summary in an illustrative Catalogue Image token.

Full Rebuild performance is a shared concern regardless of what calls it. Regenerate would reconcile Catalogue sources and invoke that same operation. Optimising Full Rebuild therefore benefits both direct rebuilds and Catalogue regeneration; this review does not require a separate Regenerate-specific rendering strategy.

The broader data, publication and rebuild proposals remain a feature review rather than an approved implementation specification. The self-contained Catalogue Image metadata removal was approved and implemented on 2026-10-08, as recorded below. [Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md), [Catalogue Deployment](Catalogue_Deployment.md) and [Catalogue Documents And Metadata](Catalogue_Documents_And_Metadata.md) describe the current workflow and agreed Catalogue Entry presentation.

## Agreed Studio And Docs Boundary

Retain explicit Studio Refresh as the handoff to Docs. Individual Work editing must not incur complete report JSON generation or the aggregate handoff. Studio owns canonical Catalogue authoring; Docs owns consumption of the refreshed inputs and rendering its documents. Docs Build, Regenerate, authoring/validation providers and Publish consume supplied Working data without reading Studio canonical files directly.

| Operation | Target responsibility |
| --- | --- |
| Studio Save | Persist the Work edit, complete required local media and update editor records. Keep full report generation and the Docs handoff outside this operation. |
| Studio Refresh | Copy `works.json` into the private Docs Working input boundary, provide accompanying Catalogue relationship/media data and regenerate the existing report manifests/metadata. This replaces the proposed generated Work by-ID handoff. |
| Catalogue Regenerate | Reconcile Catalogue source documents from the refreshed input, then call the shared Full Rebuild operation across ordinary documents and every configured collection. |
| Full Rebuild | Own complete workspace rebuild orchestration and its shared performance improvements, whether invoked directly or by Regenerate. |
| Document Rebuild | Apply document-only source changes using the existing refreshed Catalogue input, then produce the selected document's complete presentation. |
| Docs Publish | Capture the supplied Working inputs and prepare/distribute the finished document snapshot through its existing owner. Refresh remains a separate explicit action. |

This separation remains valuable if the Studio editor is later hosted within Docs Viewer. App placement and server composition do not change which operation owns expensive generation or which data Docs consumes. The existing report-manifest direction is part of this boundary, rather than a reason for Docs to reach back into Studio's source storage.

### Optional Studio-Owned Media Handoff

For complete Studio/Docs data separation, Studio could also own its prepared Work media in an explicitly configured external location outside the repository. Studio Save would update the editor's own ready renditions, thumbnails and managed downloads there. Refresh would then copy the required media into the Docs-owned ready-media boundary alongside the aggregate Catalogue input and report JSON. Project originals retain their existing Projects owner; this proposal concerns the prepared media and managed files consumed by the editor and Docs.

| Owner or operation | Optional media boundary |
| --- | --- |
| Studio | Canonical authoring and an external editor-owned prepared-media set. Save changes these without changing Docs' supplied media. |
| Docs | Refreshed Catalogue/report inputs and its own matching ready-media set. Readers, Builds and Publish consume only this supplied set. |
| Refresh | The sole Studio → Docs data bridge, transferring JSON and its required media in one awaited operation. This bridge remains explicit if the Studio UI moves into Docs Viewer. |

This would remove the current timing gap where Save changes shared media before Refresh advances the generated JSON's media version. A successful Refresh would leave the supplied Catalogue JSON and media aligned. It does not by itself rebuild previously rendered documents; Catalogue Regenerate advances their baked text, versioned image references and Media View presentations under the target workflow below.

Incremental media transfer is a requirement if this optional handoff is implemented. The user reports approximately 1.7 GB of media; a quick Refresh must not recopy that corpus. Copy the required rendition/thumbnail set only for changed or new images, and supply any required media missing from the Docs destination. Skip unchanged images. A metadata-only Refresh must transfer no image bytes. Managed downloads also need an explicit changed/new-file transfer rule.

Identify transfer candidates from image identity/version or explicit change information; do not replace the avoided bulk copy with a mandatory read/hash of every media file on each quick Refresh. The proposed change-selection approach is described below; exact missing-file handling remains design work. Initial population necessarily copies the required media once; that does not justify a full recopy during routine Refresh.

The cost is maintaining two current media sets, extra storage and transfer work for changed media. Exact storage configuration, transfer selection, completion/failure behaviour and migration of the currently shared assets would need a bounded delivery. The transfers are not inherently atomic merely because one button awaits them.

This is an optional extension, not a prerequisite for replacing Work by-ID JSON or baking document media. Keeping the current shared-media boundary remains acceptable for the initial work. No external location has been chosen or created and no media migration is approved.

#### Pending Changes And Media Selection

Reuse the existing per-Work change-tracking approach, while keeping the completion owners distinct. Today's `updates-pending.json` accumulates changed/deleted Work IDs from Refresh's generated-file writes/deletions and clears them only after the required Catalogue Regenerate source/Build work completes. A title, descriptive-field, resource or direct Gallery change can queue a Work without any image change. An unchanged image would therefore be recopied unnecessarily if every pending Work were treated as pending media, including on repeated Refreshes before Regenerate.

For the aggregate handoff, calculate one Refresh change set against the previous supplied Working data. Use meaningful Work/relationship changes to accumulate the existing document pending list. Derive the image-transfer subset from new Work images or a changed `media_version`, and include required destination files that are missing. Studio's existing media completion advances `media_version` when rendition bytes change; metadata-only edits do not require image transfer. Relationship changes can require a rebuilt presentation without requiring new pixels.

The refreshed aggregate can provide the comparison baseline, so a second persistent media pending queue is not inherently required. Compare the new Studio data with the previous supplied aggregate before replacing it, and advance the media comparison baseline only after the required transfers succeed. A successful Refresh satisfies media transfer, while document changes remain queued until Regenerate succeeds. Repeated Refresh without another image change must transfer no image bytes even if document regeneration is still pending.

Exact completion ordering and partial-failure handling must preserve that distinction without adding automatic retry markers or a second recovery ledger. Image `media_version` does not track download content or every rendition-policy change; those require their own transfer-selection rules. This is a proposed selection design, not an approved schema or implementation change. [Pending updates](../../studio/services/catalogue/catalogue_pending_updates.py) and [image version completion](../../studio/services/catalogue/catalogue_media_version.py) are the current owners inspected for this review.

## Agreed Presentation Direction

| Surface | Work information to display |
| --- | --- |
| Catalogue document | Full agreed descriptive metadata and resources, through its principal Catalogue Entry. |
| Work Media View | Title, `cat.` link and Gallery links; no year, medium or physical-dimension metadata. |
| Illustrative Catalogue Image token | Work-title caption and optional authored summary text; no full Work metadata or additional `cat.` display. |
| Work Media View link token | Its authored link label opens the Media View described above; no full metadata expansion. |

Gallery links remain navigation rather than descriptive Work metadata. Catalogue Entry is the principal-record token inside a Catalogue document and remains the explicit owner of full metadata; the restricted token display applies to illustrative images and Work media references. Keep the current title-caption, authored-summary and placement controls. The clarified reference design retains `cat.` in Media View and does not propose a new optional `cat.` control for Catalogue Image tokens. Existing Working image tokens have received the one-time metadata-field removal recorded below.

### Reference Work: 00008, nerve

The user identified these existing local presentations as the target design:

| Reference | Local route | Target presentation |
| --- | --- | --- |
| Catalogue document, nerve | `/docs/?collection=catalogue&doc=00008` | Full descriptive metadata and resources in the principal Catalogue Entry. |
| Media View for Work 00008 | Open the Work image or its Media View link | Title, `cat. 00008` link and Gallery links. |
| Context document, nerve | `/docs/?collection=works&doc=d-20260801-073846-e0a9ec` | Catalogue Image with title and optional authored summary; no descriptive Work metadata. |

At the 2026-10-07 review, the Context source had `use_work_title_caption=true`, `include_work_metadata=false` and populated summary text. The 2026-10-08 migration removed the retired metadata field and retained its caption and summary. Its Working rendered figure contains the title and summary without a Work-metadata block. This is an existing Working reference, not a claim that the draft Context document is published. The completed image simplification generalises this example; baking and update consistency remain separate architectural decisions.

## Current Public Data And Consumers

Two public files exist for each Work, for example:

| File | Current purpose |
| --- | --- |
| `site/assets/data/catalogue/works/index/00001.json` | Structured generated Work record used by the shared Catalogue media reader. It is already a selected projection, rather than the entire canonical authoring record. |
| `site/assets/data/docs/catalogue/by-id/00001.json` | Rendered Catalogue document, including its Entry heading, metadata, resources and separate document relationships. Its main image is currently an identity-marked placeholder without a baked image URL. |

The public Work reader supports initial image loading in Catalogue entries and embedded Catalogue images, opening Work Media View links, and selecting Works while browsing a Gallery. Inline image loading reads the Work record and media policy; a Work with `series_id` also causes a Series–Gallery index read, even though initial image display only needs image data. Clicking an inline image reads the presentation again. Reads retain only in-flight requests, rather than a document-lifetime Work cache. Gallery entry loads its membership record without reading every member Work; selecting a member loads that Work.

The runtime derives versioned rendition URLs from Work identity, intrinsic dimensions, `media_version` and media policy. It combines direct Gallery memberships with the Series–Gallery map. No other active public consumer of the Work by-ID record was found in the scoped reader inspection. This does not establish that every other published Catalogue index is needed; the final public inventory remains a review decision.

### Media View Actually Displays

The current Work Media View renderer shows the Work title, a `cat.` link opening the Catalogue document, direct Gallery links and Series-related Gallery links. It does not render year, medium or physical dimensions. This matches the user's current observation.

The presentation adapter nevertheless constructs year, medium, dimensions and Catalogue number in a `metadata` array, and the presentation normalizer requires and validates that array. These descriptive fields are processed without being displayed. The agreed presentation boundary supports retiring that unused work; the validator and presentation contract would need to change together. It does not imply removing descriptive metadata from canonical Catalogue records or Catalogue Entry documents.

Numeric `year`, `duration`, Work `links`, Work `downloads` and the Work header are not used by this browser media presentation. Links and downloads are already rendered into the Catalogue document. Downloads still have a separate publication role: captured Work records identify the managed files that Publish must distribute.

Source evidence: [media reads and inline loading](../../docs-viewer/runtime/js/shared/docs-viewer-media-detail.js), [Work presentation construction](../../docs-viewer/runtime/js/shared/docs-viewer-catalogue-media.js), [presentation validation](../../docs-viewer/runtime/js/shared/docs-viewer-media-presentation.js) and [publication asset selection](../../docs-viewer/services/docs_catalogue_artifacts.py).

## Current Update Timing

| Operation or reader event | What becomes current |
| --- | --- |
| Catalogue Save | Canonical records, required shared local media and editor records. Generated reader JSON and rendered Docs are not rebuilt. |
| Refresh Catalogue | Working Work/Gallery JSON, related Gallery data and private Catalogue report metadata. It queues changed/deleted Work IDs for Catalogue Regenerate. |
| Next document load or fresh mount after Refresh | The inline image resolves current generated Work data without requiring that document to be rebuilt. A retained document mount may still hold its prior image. |
| Opening a Work Media View or selecting a Gallery member after Refresh | A new media read uses current generated data. Clicking an inline image also updates its inline presentation. Already displayed media does not automatically subscribe to Refresh. |
| Build of a referring document | Work-title captions and optional embedded metadata are resolved from generated Catalogue data again. They can remain older than the image until this Build occurs. |
| Regenerate Catalogue | Pending mode reconciles the queued Catalogue documents and runs their required Build; Full reconciliation covers the complete Catalogue collection. It does not rebuild every ordinary document that refers to a Work. |
| Docs Publish | Captures current Working inputs, rebuilds eligible documents in temporary storage and distributes the completed snapshot to configured destinations. It does not run Catalogue Refresh or Regenerate. |
| Public deployment and next reader fetch | The deployed static document and Catalogue data become available to public readers. Publish, Git actions and public deployment remain distinct operations. |

This permits mixed local presentation: an embedded Work-title caption or metadata can still reflect the last document Build while its image and Media View use a later Catalogue Refresh. Refresh alone does not live-update an already mounted document or Media View. Shared image bytes can also change during Save before generated JSON carries the new image version; the current versioned cache policy makes Refresh and the next media read significant.

The target workflow below coordinates title, caption, versioned image references, descriptive metadata, resources and Gallery membership through rendered document updates. This changes the current independent media-read behaviour. Complete alignment of image bytes with the supplied Catalogue input also requires the optional media ownership change described above.

## Baking Media Into Rendered Documents

The proposed reader contract is that displaying a rendered document and opening its own Media View requires no additional Catalogue data requests. The document carries its complete prepared presentation. Image-file and app-asset loading still happen normally, and browser layout still determines responsive rendition selection. Opening a Gallery or selecting another Work is navigation to different content and may fetch that target's prepared presentation.

Image URL construction can happen during Build or Publish preparation. Emit `src`, rendition candidates or `srcset`, intrinsic dimensions, alternative text and the largest-image new-tab URL from the captured Work and media policy. Responsive selection still belongs to the browser: the current runtime measures the displayed slot to set `sizes`, and the browser selects a rendition for layout and screen density. This does not require a Work-record request.

A rendered document could also carry a structured Media View presentation containing identity, title and resolved Gallery links. The same prepared data should serve inline image loading and opening Media View, avoiding another lookup or parsing visible caption HTML. Whether the presentation is a document JSON field or an embedded structured block remains open; keep one generation owner and explicit payload validation.

| Approach | Benefit | Cost or unresolved boundary |
| --- | --- | --- |
| Retain current Work records and runtime construction | Local media follows Refresh independently of document Build; Gallery selection reads a small exact record. | Extra requests, policy/membership resolution in the browser, and different update timing for document text and media. |
| Publish a smaller dedicated media record | Removes unrelated fields and unused descriptive metadata while retaining direct Gallery-member loading. | A second public record family and runtime construction remain; it does not by itself resolve mixed update timing. |
| Bake image and Media View data into rendered documents | Initial document images and their Media View use one built state and need no additional Catalogue metadata requests. The public Work record family may become unnecessary. | Embedded presentations repeat some generated data across referring documents. Local updates require an explicit rebuild policy; Gallery selection still needs a source for the selected Work's presentation. |

The preferred direction to investigate is baked public document media. For Gallery selection, consider reading the selected Catalogue document's structured media presentation directly by ID, or retaining a compact media record if fetching rendered document content proves unnecessarily expensive. Do not fetch every Gallery member's document up front. Removing the Work record family requires resolving Work text links and Gallery-member navigation as well as initial inline images.

## Does Working Need Work By-ID JSON?

The old site used Work records to render pages dynamically from URL-query selection. Docs now resolves URL identity to a rendered document by ID. That removes the original browser-page-rendering reason for a second Work record family, and brings the persisted Working intermediate into this review as well as its public copy.

Working `generated/catalogue/works/index/<work_id>.json` currently remains an input to newer code. These are dependencies to redesign, rather than proof that a per-Work generated file is intrinsically needed:

| Current consumer | Requirement to preserve if the files are removed |
| --- | --- |
| Catalogue Entry and Catalogue Image builders | Resolve an exact Work's title, descriptive fields, resources and media from validated Catalogue inputs. |
| Working media reads and authoring previews | Supply the agreed presentation and safe exact target/image validation. Built readers can use document presentations; authoring needs an explicit provider and must not become circular with document creation. |
| Regenerate Catalogue | Obtain current Work identities and titles to create, retitle, rebuild and delete Catalogue documents. |
| Broken Links | Validate Work references and available media without relying on the existence of the retired generated record. |
| Refresh and pending updates | Preserve exact changed/deleted Work tracking. The current pending list derives IDs from generated Work-file writes and deletions, so that signal needs an explicit replacement. |
| Publish preparation and asset selection | Capture coherent Work data and derive exact image/download references, without requiring it to be distributed as public Work JSON. |

A possible simpler flow is Studio-owned canonical Catalogue data → explicit Studio Refresh → one private aggregate Catalogue input plus report/relationship data in Working → rendered Catalogue documents and embedded presentations. A shared Work projection can remain as code or in-memory build data without becoming a persistent by-ID file family. Canonical records remain the editable authority; rendered document HTML must not become the source for generating its own Catalogue Entry or for reconstructing Work metadata.

### Aggregate Catalogue Input Through Refresh

The agreed direction is for Studio Refresh to copy the complete `works.json` across as a private Docs input alongside report JSON, replacing thousands of generated Work files. The file already contains a map keyed by exact Work ID. Load and validate the supplied input once for an operation, retain that parsed map through its selected renderers, and resolve requested IDs directly. Regenerate can reconcile selected Work documents; targeted Builds can render selected document IDs and resolve only the Work presentations they use. A targeted run still reads/parses the whole aggregate; it does not have to regenerate every Work or document.

`works.json` alone does not contain Gallery definitions, Work–Gallery membership, Series–Gallery relationships or rendition policy. Refresh must supply the accompanying data coherently, including Series identities needed to validate relationships. Studio owns loading/validating its canonical source and producing the handoff. Docs validates the supplied data contract and exact identities without loading Studio source paths or substituting live canonical data when supplied inputs are missing. Public rendering continues to select its agreed fields; the aggregate remains a private input.

The Refresh handoff is selected. Its stored aggregate is a replaceable, read-only input from Docs' perspective, not another editable authority. Save changes Studio data; a successful Refresh advances the Catalogue/report inputs available to Docs; Build/Regenerate advances rendered document content. Exact storage, payload contracts and Refresh completion details remain to be specified. Moving Studio's UI into Docs Viewer must preserve this producer/consumer separation rather than make Docs operations read current Studio source directly.

Regenerate and its required Build should consume the same supplied Catalogue input. Separate builder processes may each parse the captured file once; that differs from repeatedly reading Work files or reloading the source for every token. Do not add a stale process-lifetime cache to make “loaded once” span unrelated operations. Publish captures the refreshed Working inputs before preparing one coherent snapshot and distributes only finished output, without reading Studio canonical data during preparation or distribution.

The current by-ID files make selected Work reads small. Replacing them with the aggregate trades that selected-file read cost for one larger parse and fewer generated files, per-file versions and freshness boundaries. No performance improvement is claimed without evidence, and canonical storage migration is not required by this proposal. Exact changed/deleted Work tracking still needs an explicit replacement for source reconciliation and pending updates. The full document rebuild proposed below covers referring documents without a new dependency index.

Source evidence: [builder Work lookup](../../docs-viewer/build/docs_builder/semantic_tokens.py), [Regenerate](../../docs-viewer/services/docs_catalogue_regeneration.py), [authoring media support](../../docs-viewer/runtime/js/management/source-editor/catalogue-media-support.js), [Broken Links](../../docs-viewer/services/docs_broken_links.py), [Refresh](../../studio/services/catalogue/catalogue_refresh_service.py) and [pending updates](../../studio/services/catalogue/catalogue_pending_updates.py).

### Consistent Local Updates

The agreed target separates Catalogue input freshness from rendered document freshness:

1. **Studio Refresh brings the Docs copy of Catalogue source data up to date.** Studio Save already owns canonical authoring changes. Refresh supplies the saved aggregate, relationships/policy and reports; the optional media handoff would supply changed media here too. Refresh does not rebuild document content.
2. **Catalogue Regenerate brings all documents up to date with that supplied data.** Reconcile Catalogue source documents, then run one full document rebuild across ordinary documents and every configured collection. This includes Context documents and any other referring documents automatically, without dependency discovery or affected-document selection. Clear pending Catalogue changes only after the complete rebuild succeeds.
3. **Document Rebuild applies document-only updates.** Use the existing refreshed Catalogue input when rebuilding changed Markdown or token content. A document-only edit does not require another Studio Refresh or Catalogue Regenerate. The existing watcher may perform this Build automatically; the explicit Rebuild action remains available.

Working and public readers should consume the same complete built presentation contract. Refresh alone therefore no longer advances an existing document's Media View or inline presentation through independent Catalogue data reads. Regenerate owns advancing Catalogue-dependent rendered content; Rebuild owns document-only changes. Publish retains its existing capture, preparation and distribution responsibilities, and public deployment remains separate. Search freshness remains separately scoped.

Regenerate should reconcile its sources and call the shared Full Rebuild owner once, avoiding a separate Catalogue build followed by another build of Catalogue within the workspace operation. Pending versus Full reconciliation can still determine which Catalogue sources are created, updated or removed; that source selection is separate from the full rendering scope. Referring documents are covered by Full Rebuild without adding dependency discovery to Regenerate.

This is the proposed lifecycle, not current Regenerate behaviour: today's Regenerate only reconciles/builds the Catalogue collection and does not update referring Context/ordinary documents. Its Full mode is a complete Catalogue collection build, not a workspace-wide rebuild. The current workspace Rebuild service combines ordinary/collection document builds with Search and registered media work, while its `include_search=False` path only builds ordinary documents. Review that orchestration and any scope changes as part of the shared Full Rebuild contract. Calling it from Regenerate does not itself justify excluding Search or media work; those responsibilities and their optimisation belong to the shared operation. [Rebuild orchestration](../../docs-viewer/services/docs_write_rebuild.py) and [Manage Rebuild](../../docs-viewer/services/docs_management_service.py) are the current owners.

The delivery must specify Regenerate completion/pending handling and how already mounted readers adopt newly built payloads; rebuilding stored JSON alone does not replace a displayed document. A complete Docs Build must not be folded into Refresh.

### Shared Full Rebuild Optimisation

Optimise Full Rebuild independently of its caller while preserving complete workspace coverage and successful completion semantics. A full operation should bring all documents up to date; its implementation can avoid repeated input reads, parsing, validation and production of unchanged output where correctness is established. Do not make Regenerate own a second rebuild pipeline or its own performance cache.

The refreshed aggregate offers one opportunity: load and validate Catalogue inputs once for the rebuild operation, share the parsed map and resolved media/relationship data across renderers, and reuse prepared Work presentations when several documents reference the same Work. Current collection subprocesses may each parse the aggregate once, so operation-wide reuse needs a deliberate shared execution design rather than assuming a per-process cache achieves it. Other candidates include repeated source/manifest reads, duplicate collection work, output writes and registered media processing. These are investigation areas, not measured bottlenecks or approved implementation changes. Search and media costs must be considered within their shared responsibilities.

Keep any reusable data bounded to the operation so a subsequent Refresh or source edit is visible to the next rebuild. The performance review should establish the actual costs and a bounded change set before implementation; no benchmark or test work is authorised by this documentation review. Direct Full Rebuild and Regenerate then receive the same improvements.

### Publication And Ownership

Preserve the validated Work inputs needed by document rendering and asset selection internally, without assuming they must remain generated by-ID JSON. In particular, removing public `downloads` must not stop download distribution. If Working records are retired, replace preparation's captured Work input and asset-selection contract explicitly. Construct any new public projection during preparation, then distribute the same completed bytes through the existing Publish owner; do not add a second transformation or source read during distribution.

Public inventory, route configuration, shared runtime projection and generated payloads must change together before removal. Resolve local versus public image URL ownership and exact identity validation. Retire displaced paths and unused presentation fields rather than introducing compatibility aliases or a shadow public copy.

## Catalogue Image Metadata Change

Implemented on 2026-10-08 as a self-contained simplification. Add and Edit Catalogue image no longer expose **Include Work metadata**. Python and JavaScript parsing/serialization no longer accept or emit `include_work_metadata`, and the illustrative-image renderer no longer builds its metadata block. Title-derived alt text, the optional Work-title caption, authored static summary, placement and fill-width controls remain.

The one-time source migration removed the field from 19 tokens in 15 Working documents: one ordinary document and 14 Context documents. Eleven occurrences previously selected metadata and eight omitted it. Exact Work identities, caption choices, authored summaries and layout fields were preserved. The existing watcher rebuilt their document projections; no manual document or Search rebuild was invoked. Tokens containing the retired field are unsupported literal source if reintroduced, without a compatibility alias.

Illustrative figures now follow the nerve Context example: image, optional Work-title caption and optional authored static summary. Full descriptive information remains in Catalogue Entry, reached through the existing `cat.` link in Media View. Existing Preview and published snapshots retain their previously generated HTML until a separate Publish. The broader Work JSON, media baking, Media View contract and rebuild proposals remain open.

Catalogue Entry has its own fixed principal-record purpose and retains its metadata/resources and canonical fields. [Semantic Tokens Architecture](Semantic_Tokens_Architecture.md) owns the reduced grammar and rendering; [Semantic Tokens Source Editor UI](Semantic_Tokens_Source_Editor_UI.md) owns Add/Edit controls; [Catalogue Documents And Metadata](Catalogue_Documents_And_Metadata.md) records the Entry/Image distinction. The historical [Catalogue Image Token Metadata delivery](Catalogue_Image_Token_Metadata_Delivery.md) is superseded for its metadata choice.

Verification: lint passed for the changed Python builder module and three management JavaScript modules. Read-only inspection found no retired fields in Working Markdown or active code and no metadata blocks in the 15 rebuilt payloads. The inspected formerly metadata-enabled figures retain title captions; nerve retains its authored summary; the captionless ordinary example omits figcaption. Code review covered parser/serializer agreement, shared Add/Edit hydration and insertion, source migration and the retained Catalogue Entry helper; no unresolved code finding remains. Management-only JavaScript and Python builder changes require no public runtime projection. Tests, browser interaction, Publish, commit and push were not performed. Existing Python/JavaScript token tests inspected during this change still describe older literal-alt/Detail grammar and were left unchanged under the separate test-work policy. Restart Local Studio and hard-refresh Docs Viewer before manual Add/Edit review.

## Decisions Before A Delivery

- [x] Agree the presentation boundary using Work `00008`, nerve: full metadata in the Catalogue document; title, `cat.` and Gallery links in Media View; title and optional summary in the Context Catalogue Image token.
- [x] Preserve explicit Studio Refresh as the aggregate Catalogue/report handoff, keeping complete generation outside individual Work Save and Docs consumption separate from Studio canonical storage even if the editor moves into Docs Viewer.
- [x] Agree the target update workflow: Studio Refresh supplies current Catalogue inputs; Catalogue Regenerate reconciles Catalogue sources and invokes a full document rebuild, including referring documents; Rebuild applies document-only changes using the supplied inputs.
- [x] Use the same complete built presentation contract for Working and public readers.
- [x] Treat Full Rebuild optimisation as shared work independent of its caller; Regenerate invokes that operation after Catalogue source reconciliation.
- [ ] Review shared Full Rebuild costs and specify a bounded optimisation while preserving its complete coverage and agreed Search/media responsibilities.
- [ ] Specify reuse of shared Full Rebuild orchestration, Regenerate completion/pending handling and how already mounted readers adopt newly built content. Regenerate needs no separate referring-document dependency index.
- [ ] Choose the baked document media representation and the Gallery-member loading path.
- [ ] Specify replacement of Working Work by-ID JSON with the Refresh-supplied private aggregate input, its storage and accompanying relationships/policy, authoring/validation providers, exact change tracking and completion timing.
- [ ] Specify retirement of the unused descriptive Media View metadata contract while preserving its title, `cat.` link and Gallery navigation.
- [x] Remove Include Work metadata from Add/Edit Catalogue image and its token/build contract; migrate existing Working tokens while preserving title-caption, optional summary and layout behaviour.
- [ ] Establish the smallest public Catalogue inventory that still supports all approved readers and publication asset selection.
- [ ] Define a bounded implementation outcome, migration, durable documentation updates and proportionate verification. Test changes require their own agreed specification; ordinary UI presentation remains a user manual-review gate.

## Review Evidence

The review is based on scoped source/configuration, representative published-payload inspection, Working Work-record consumer inspection and the exact Working Context source/rendered figure for nerve on 2026-10-07, plus the user's observation of Media View, selection of Work `00008` as the target example and explanation of the old site's Work-record purpose. The renderer confirms the title, Catalogue link and Gallery presentation and its omission of descriptive metadata. No browser automation, tests, performance measurements, actual Save/Refresh/Build/Publish operation or product changes were performed for this review. Request reduction is an architectural expectation, not a measured latency improvement.
