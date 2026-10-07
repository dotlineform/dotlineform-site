---
draft: false
doc_id: d-20261002-214356-1ea4a2
title: Catalogue Documents And Metadata
added_date: "2026-10-02 21:43:56"
last_updated: "2026-10-07 19:20:15"
summary: Define a Regenerate-owned Catalogue Entry token with a Work H1, metadata and H2 resource sections, followed by the separate Related links directive.
ui_status: planned
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Documents And Metadata

Status: design decisions closed, with a proposed delivery and manual `00008` pilot, parented to [Planned Features](Planned_Features.md). The agreed syntax is `[[catalogue:entry:work:<work_id>]]`. Catalogue Entry is a Regenerate-owned token used only in generated Catalogue documents, without an authoring UI or modal. It retains the current visible metadata, private storage context and technical image dimensions; duration and depth remain supported fields for future use. Series presentation stays with reports and existing Series–Gallery linking. Duration presentation and EPUB/export mappings are future work rather than prerequisites. The separately requested `provenance` and `artist` retirement, single `medium` migration and unused generated Work `documents` retirement are complete. Delivery has not started; implementation still follows the baseline and pilot gates below.

## Intended Outcome

A Catalogue document is the definitive document for a Work. Its title defines the document, its image illustrates the Work, and its metadata describes the Work. It should remain meaningful when read on the public site or exported outside Docs Viewer.

The initial public Catalogue metadata keeps the current selection: displayed year/date, Medium, supported physical dimensions and Catalogue number. The Work title is the document H1, and downloads, external links and direct Galleries have their own sections. Storage location remains private inventory context in the local Manage report and is excluded from the public Work projection and Entry. Pixel dimensions remain technical image-layout inputs rather than visible metadata. Duration and depth are retained for future use; an empty field is not a reason to remove an agreed capability. On 2026-10-07 the user requested retirement of `provenance` and `artist`, then migration of corrected `medium_caption` descriptions to `medium` and retirement of the separate `medium_type` category. No further canonical field removal is agreed.

The generation and rendering model expresses this purpose explicitly through a separate **Catalogue Entry** token. Regenerate inserts it into Catalogue documents; it is not an ordinary authoring tool. **Catalogue Image** remains an image inserted into body content, with an optional figure caption and selected metadata. The builder executes each token's declared meaning without changing an image token's semantics according to the collection hosting the document.

## Current Findings

Catalogue regeneration currently produces a Work image token followed by `[[links|related links]]`. The Work title is repeated in document front matter and the figure caption, but the caption renders as a styled span inside `figcaption`, rather than a document heading. The figure's selected metadata is limited to displayed year, medium description, physical dimensions and Catalogue number. Related links currently renders its heading as H3; the agreed Catalogue document structure requires H2.

The local [Catalogue Works report](/docs/?doc=d-20260810-222148-99daec) has Work, Year, Title, Series and Storage columns, plus Medium in its expanded presentation. Its generated metadata is local-only. [Catalogue Works](Catalogue_Works.md) describes this current contract; the agreed Entry design preserves its private storage context.

The public consumer Work JSON contains more information than the Catalogue document renders. Duration, pixel dimensions, links and downloads are already projected when populated. The single descriptive `medium` field is projected and displayed in the Catalogue body and Media View. Storage location is deliberately omitted from the projection. Artist, provenance and the separate Medium category are retired. Series identity is projected for its current Media View consumer; a Series title is not included in the complete Work record and is not part of the initial Entry metadata selection.

The archived Work renderer derives an image aspect ratio from `width_px / height_px` and supplies it to CSS to reserve space during image loading. The current Docs Viewer responsive-image helper sets image width/height only after the Work JSON is fetched; generated Catalogue image HTML starts with a hidden image and no dimensions. The Entry design must reserve image space in its built HTML from the start, rather than waiting for the runtime lookup.

“Public consumer projection” below means the generated Work JSON intended for public readers. It does not establish that the latest generated values have been published or deployed. Empty optional values are omitted from that JSON.

## Work Metadata Inventory

This inventory was checked against the canonical Work fields, active editor definitions, generated Work projection, private report projection and image-token renderer on 2026-10-02, with the retired fields and single Medium model updated on 2026-10-07. “Catalogue body” refers to the generated figure and Related links content, rather than all metadata used elsewhere in Docs Viewer.

| Field or relationship | Public consumer projection today | Catalogue body today | Proposed treatment or decision |
| --- | --- | --- | --- |
| `work_id` | Exact five-digit identity | Catalogue number | Retain as the document identity and visible Catalogue number; preserve leading zeroes. |
| `title` | Work title | Figure caption; also document metadata title | Retain as the document's H1, with its visual style controlled separately. |
| `year`, `year_display` | Numeric year and display text | Display text only | Retain the distinction if numeric sorting and a richer displayed date are both needed; show the readable date without duplicating it as another visible number. |
| `medium_type` | Retired | Omitted | Separate category removed on 2026-10-07. |
| `medium` | Present when populated | Medium description | Corrected `medium_caption` values migrated exactly on 2026-10-07. Use **Medium** as the label; the old field name is retired without an alias. |
| `height_cm`, `width_cm`, `depth_cm` | Present when populated | Height × width, with depth when supplied; requires height and width | Retain all three fields, including depth for future use. Preserve the current display: height × width × optional depth in cm when height and width are available; do not add a new partial-dimension presentation in this delivery. |
| `duration` | Present when populated | Omitted | Retain for future time-based Works. Keep it out of the initial visible metadata selection; define units/format and presentation when duration is introduced. |
| `artist` | Retired | Omitted | Removed from canonical data, editor and public projection on 2026-10-07. |
| `provenance` | Retired | Omitted | Removed from canonical data and editor on 2026-10-07, including its one populated value. |
| `storage_location` | Omitted | Omitted; available as Storage in Manage report | Retain as private inventory context in canonical data, the editor and local report. Keep it out of the public Work JSON and Catalogue Entry. |
| `series_id` and Series title | ID present; title not in complete Work record | Not rendered by the figure; Media View uses the ID for Series-related Galleries | Retain `series_id` for existing consumers, including reports and Series–Gallery linking. Series is not needed in Catalogue documents; Entry adds no Series metadata or title projection. |
| Direct Gallery memberships | Gallery identities and titles in `galleries` | Not rendered by the figure; accessible in Media View | Render an H2 Galleries section with a list of links to each exact Gallery in Media View, below Downloads and Links. Reuse existing memberships and Gallery targets. |
| Series-related Galleries | Separate generated Series–Gallery index | Accessible through Media View, rather than figure metadata | Keep this derived context with the existing Series–Gallery linking and Media View owners. Entry lists direct `work.galleries` only and does not add Series-derived Galleries. |
| `links` | URL/label entries when populated | Omitted by the figure | Render an H2 Links section and list using the stored labels/URLs, below Downloads. Keep these external resources distinct from Docs Viewer Related links. |
| `downloads` | Filename/label entries with generated public URLs | Omitted by the figure | Render an H2 Downloads section and list using the stored labels/generated URLs, below the image and before Links. Export packaging is a separate consumer requirement. |
| `width_px`, `height_px` | Present when populated | Omitted as visible metadata | Retain as technical image dimensions. Build uses their ratio to reserve the image frame and emits intrinsic image width/height before loading; do not add visible pixel-dimension lines or confuse them with physical Work measurements. |
| `media_source_id`, `project_folder`, `project_subfolder`, `project_filename` | Omitted | Omitted | These resolve the source image for the production pipeline. Review under the technical-data boundary below; they are not a reason to keep descriptive Work metadata private. |
| `media_version` | Present when populated | Omitted | Retain the technical image revision needed by media readers; it is not a descriptive Catalogue line. |
| Docs Viewer document relationships | Maintained by the separate Links owner; the unused Work `documents` array is retired | Rendered by the Related links directive | Keep `[[links|related links]]` separate, after the Entry token, with an H2 heading in Catalogue documents. Preserve the existing Links authority; do not add relationships to the Entry or reinterpret external `links` as document relationships. |

### Population Snapshot

The 2026-10-02 read-only canonical snapshot contained 4,616 Works. Storage location was populated for 481 Works; provenance for one. Artist, duration and depth were empty for every Work. Both medium fields and both year fields were populated for every Work. Physical height and width were each populated for 1,935 Works. Four Works had downloads and three had external links. The 2026-10-07 retirement removed `provenance` and `artist` from the then-current 4,618 Works; these historical population counts do not describe the current source shape.

These historical counts describe populated values, not usefulness, validity or permission to publish. Duration and depth are explicitly retained despite their empty historical values because future Works will use them. Populated fields require a value review before removal or wider publication; no storage or provenance values are reproduced in this planning document. Before the Medium migration, the user corrected the two empty descriptions and the typo; all 4,618 corrected descriptions are retained exactly, while the category distinction is deliberately removed.

### Agreed Metadata And Technical Data Boundary

The public Entry presents the agreed descriptive metadata and reader resources. Private storage administration retains its existing canonical/editor/report owners. Image production also needs source selection, filenames, measurements and image revisions; those values support making the public Work record without all becoming visible lines in it.

A retained technical field belongs to its production/configuration consumer. In particular, `width_px` and `height_px` are public-safe inputs for responsive image selection and layout reservation, and `media_version` identifies the image revision. Local source-selection paths remain pipeline inputs. The public serializer continues to select consumer fields explicitly; do not publish raw canonical records, private report metadata or storage locations.

## Agreed Catalogue Entry Design

The Entry has one fixed semantic purpose: render the principal record of one Work in its generated Catalogue document. Regenerate inserts one Entry into each new Catalogue document, targeting the Work with the same exact five-digit identity as the document. The implementation must also convert existing generated Catalogue documents so there is one maintained body format. The agreed syntax is `[[catalogue:entry:work:<work_id>]]`, for example `[[catalogue:entry:work:03565]]`. The token needs only Work identity, with presentation owned by Catalogue CSS. It does not store another copy of the title, metadata or resource lists.

There is no Add/Edit Catalogue Entry UI, modal, insertion-menu item or author-selected layout, caption or metadata option. Catalogue Image remains available to authors illustrating ordinary documents. Its existing caption/metadata controls do not govern Entry content, and adding Entry does not expand Image semantics.

Build resolves the Entry from the generated `working/generated/catalogue/works/index/<work_id>.json` record, reusing the existing cached Work lookup. The Work record remains authoritative for title, agreed descriptive metadata, downloads, external links and direct Gallery memberships. Do not read private report metadata or introduce another Work store.

| Capability | Catalogue Image | Catalogue Entry |
| --- | --- | --- |
| Purpose | Illustrate body content | Present the principal Work record in a generated Catalogue document |
| Title role | Optional figure caption | Required principal document heading |
| Metadata role | Optional selected caption information | Agreed public Work metadata and resources |
| Creation | Existing Add/Edit Catalogue Image UI | Regenerate inserts the token; no authoring UI or modal |
| Presentation controls | Existing caption, metadata and placement options | Catalogue CSS; no token presentation options |
| Heading behavior | Does not define the document title | Emits the Work H1 explicitly |

### Document Structure And Presentation

| Content | Source | Semantic markup |
| --- | --- | --- |
| Work title | `work.title` | One H1 |
| Work image | Existing image resolution from Work identity and media policy | Figure/media control with appropriate alt text and existing Media View activation |
| Work metadata | `year_display`, `medium`, supported physical dimensions and `work_id` | Body content in the current order; a definition list can express name/value pairs |
| Downloads | `work.downloads` | H2 Downloads, followed by a list of labelled resource links |
| External links | `work.links` | H2 Links, followed by a list of labelled external links |
| Direct Galleries | `work.galleries` | H2 Galleries, followed by a list of Gallery-title links opening each Gallery in Media View |
| Related documents | Separate `[[links|related links]]` directive and existing Links records | H2 related links, followed by the existing relationship list |

The Work title is an `h1` even when its visual appearance is 16px bold. Subsequent resource and relationship headings are `h2`. Heading levels express the document hierarchy; CSS owns their visual size. The Work heading belongs to the Entry/document structure, not inside a figure caption. [W3C heading guidance](https://www.w3.org/WAI/tutorials/page-structure/headings/) explains the structural role.

Give the Entry a dedicated CSS wrapper for Catalogue presentation. Preserve the current image and accompanying title/metadata arrangement, placing the H1 above the metadata in the text column. Downloads, Links and Galleries follow in that order below the image, aligned with the image column. Keep this structure meaningful in document order independently of the grid layout. Ordinary Catalogue Image figures retain their current styling and behavior.

Omit each empty resource list together with its heading. Galleries uses the direct memberships already present in `work.galleries`. Series and additional Series-derived Gallery context stay with reports and the existing Series–Gallery linking/Media View owners, rather than appearing in the Catalogue document.

Keep the initial metadata order as displayed year/date (`year_display`), Medium (`medium`), physical dimensions and Catalogue number (`work_id`). Omit absent optional values. Preserve current physical-dimension formatting: height × width, followed by depth when supplied, with cm units; require height and width for that line. Storage stays private, numeric `year` is not repeated beside its readable date, and no Series title or pixel-dimension line is added. Duration remains supported in the data model but is deferred from this initial presentation until its units/format are defined.

### Image Space Reservation

Build reads validated positive `width_px` and `height_px` from the same captured Work record used for Entry content. Emit intrinsic `width` and `height` attributes on the image and reserve a proportional image frame using that width/height ratio in the initial built markup. Responsive CSS sizes the frame to the image column, with proportional height and no distortion.

The reserved frame must remain in the layout while runtime media lookup and image loading are pending, even when the image itself is hidden. Loading/error content can occupy the frame without collapsing it, so Downloads, Links, Galleries and other following content do not jump when the image appears. This layout use does not expose pixel dimensions as visible metadata or introduce a second media pipeline.

### Separate Related Links Directive

Keep `[[links|related links]]` outside the Entry token and after it in the generated source body. Catalogue Entry owns Work content; the directive owns presentation of incoming/outgoing Docs Viewer document relationships through the existing Links authority. It must not read external `work.links`, and Entry must not recreate a document relationship list. Empty Related links continues to produce no section.

The agreed generated source shape is:

```text
[[catalogue:entry:work:03565]]

[[links|related links]]
```

The Entry spelling, separate Related links directive and its position are agreed. Implementation must render the directive's Catalogue heading as H2 while preserving its independent relationship ownership and ordinary-document behavior.

Reuse existing Work lookup, exact identity validation, image resolution, Media View activation and token relationship extraction. The new token must participate in existing relationship handling, including suppression of a Work document's self-reference. A separate semantic token does not require another media pipeline, Work store or relationship graph. Existing Image tokens in ordinary documents remain valid because they retain their own purpose.

## Data And Build Ownership

Keep one canonical Work model with explicit public and private projections. Catalogue documents render the agreed public metadata and resources; the local Manage report retains private storage administration. The public Entry does not depend on that report. Duration and depth remain in their current data owners for future use, while technical image dimensions serve layout and media readers.

| Owner | Required change |
| --- | --- |
| Studio canonical source and Work editor | Remove only agreed fields, retain validated useful metadata and define field meanings/units. Keep editing authoritative here. |
| Refresh Catalogue | Retain the current public Work fields and resource/Gallery labels, including technical pixel dimensions. Keep storage exclusively in its private report projection. No additional Series-title projection is required by the initial Entry design. |
| Catalogue Regenerate and document Build | Insert one Entry token followed by the separate Related links directive into new documents; convert existing generated bodies during the initial full reconciliation. Resolve Entry content from captured Work JSON and Related links from its existing owner. Avoid a runtime fetch of private report metadata. |
| Docs Viewer runtime and CSS | Present the semantic H1/H2 document structure with Catalogue-specific Entry styling and reuse existing image and Gallery Media View behavior. Public readers require no Studio API. |
| Publish and distribution | Carry the approved public projection and rendered documents through the existing completed Preview and publication inventory. Do not publish raw source or the private report aggregate by accident. |
| Static/export consumers | Future export design owns portable image/resource preparation and structural mappings. The initial Entry delivery does not extend export consumers. |

[Catalogue Save And Refresh](Catalogue_Save_And_Refresh.md) remains the lifecycle authority: Save changes canonical data; Refresh generates reader data; Regenerate updates Catalogue sources and builds documents; Publish distributes the completed snapshot. This feature should fit those boundaries rather than introducing implicit Refresh, Regenerate or Search work into Publish.

Retain exact Work/document identities, routes and existing date policy. Generated body or formatting maintenance preserves document dates; a Work-derived title change advances `last_updated`. Full reconciliation currently owns replacement of generated Catalogue bodies, so determine whether any manually added body content needs preservation before the token conversion.

## Future Duration And Export Work

Duration remains a supported Work field. Its units, display format and visible presentation will be decided when it is needed for time-based Works. That future presentation does not hold up Entry implementation or remove the field.

EPUB is a later idea. Document/chapter structure, navigation, heading mappings, relationship inclusion and image/download packaging belong to the future export design. This delivery supplies meaningful H1/H2 document structure without choosing an EPUB mapping or extending export consumers. [Export](Export.md) retains ownership of the current static HTML workflow.

The current interactive media reader and Build-time image-space reservation do not, by themselves, define portable image/resource preparation. That consumer policy will be specified when export work is designed, rather than treated as a prerequisite for Catalogue Entry.

## Agreed Decisions

- [x] Keep the current public metadata selection and explicit public/private projections; retain storage administration in the private report and technical image fields with their media/layout consumers.
- [x] Retire `provenance` and `artist` from canonical Works, the Work editor and affected field/projection owners, including removal of the populated provenance value.
- [x] Retain `storage_location` as private inventory context, excluded from public Work JSON and Catalogue Entry.
- [x] Retain duration and depth for future use despite currently empty historical values; no field removal is planned.
- [x] Migrate corrected `medium_caption` descriptions to one `medium` field labelled Medium and retire `medium_type` throughout active source, editor, generated projections and readers.
- [x] Retire the unused generated Work `documents` array and URL/title normalization; retain document relationships under the existing Links owner.
- [x] Preserve `year_display` without repeating numeric year, and preserve the current physical-dimension display with optional depth and no new partial-measurement format.
- [x] Defer duration units/format and visible presentation until the field is needed; retain the field and keep this future work outside the initial Entry.
- [x] Use Catalogue Entry only in generated Catalogue documents, inserted by Regenerate, with one principal Entry per document and no authoring UI, modal or token presentation controls.
- [x] Render the Work title as H1 and resource/relationship section headings as H2; use Catalogue CSS to preserve the image/title/metadata arrangement and place Downloads, Links and Galleries below the image.
- [x] Map Downloads, Links and direct Galleries from Work JSON into ordered sections, omitting empty lists and headings.
- [x] Keep `[[links|related links]]` separate after the Entry, using its existing relationship owner and an H2 heading in Catalogue documents.
- [x] Keep Entry metadata ordered as displayed year/date, Medium, supported physical dimensions and Catalogue number, without adding Series title, storage or visible pixel dimensions.
- [x] Retain `width_px`/`height_px` as technical data and use them at Build time to reserve image space in the initial rendered HTML.
- [x] Keep Series out of Catalogue documents; retain existing report and Series–Gallery linking consumers and list direct `work.galleries` only in Entry.
- [x] Use the identity-only `[[catalogue:entry:work:<work_id>]]` syntax, preserving exact five-digit Work IDs.
- [x] Defer EPUB and portable image/resource/structural mappings to their future export design.

## Delivery Scope And Process

The initial delivery produces the agreed Catalogue Entry renderer, Regenerate body generation, Catalogue styling and converted Working Catalogue documents. It reuses current Work JSON, direct Gallery targets and the separate Related links owner. Ordinary Catalogue Image remains a supported body illustration. Series remains outside Catalogue document presentation; Entry uses direct `work.galleries` only. Duration presentation and EPUB/portable export preparation are future work with their own designs, rather than unresolved decisions for this delivery.

Before development, the user runs Regenerate to process the existing accumulated updates and clear the pending queue. Development then uses Work `00008` as the sole manual pilot. Codex converts only its Catalogue source to the new Entry token and rebuilds that document while the renderer and CSS are refined. The remaining Catalogue documents retain their current Image tokens until the user accepts the pilot. Once ready, one intentional Full reconciliation converts all generated Catalogue sources and builds the complete collection.

Regenerate currently has Pending updates and Full reconciliation modes, without a single-Work selector. Starting from an empty queue, the user's edits to `00008` follow Save Work → Refresh Catalogue → Regenerate Pending updates, provided no other Works have become pending. If other Works are queued, use the exact targeted Build for the pilot rather than assuming Pending updates will select only the displayed Work. No additional Regenerate mode or selection UI is needed for this delivery.

### Manual Pilot And Verification Budget

The user owns manual visual and interaction review of `00008`, which currently provides two downloads, one external link and one direct Gallery. Review the H1/title and metadata placement, image proportions and reserved space while loading, H2 resource sections in their agreed order, download/external destinations, Gallery Media View activation and the separate Related links section when populated. Empty-resource presentation can be reviewed through user-controlled edits to the same Work if needed. The pilot uses real Working data rather than fabricated test records.

The refinement loop depends on the change:

| Change | Required follow-through |
| --- | --- |
| User edits Work metadata or resources | Save in the Work editor, Refresh Catalogue, then Pending updates when only `00008` is queued; otherwise use the exact targeted Build |
| Entry token/parser/renderer changes | Rebuild `00008` directly; code changes alone do not add a pending Work |
| Pilot Markdown changes | Let the running source watcher rebuild it and inspect that output; use the targeted Build only if the watcher is unavailable |
| Catalogue CSS changes | Reload the viewer to load the changed stylesheet; document regeneration is unnecessary for styling alone |

The existing targeted Build command runs from the repository root:

```bash
set -a
source .env.local
set +a
$HOME/miniconda3/bin/python3 docs-viewer/build/build_docs.py --stage working --write --collection catalogue --only-doc-ids 00008 --skip-media-builds
```

This is a document-generation action, not a new automated test. It writes the selected Working document and affected saved collection metadata through the existing builder, skips registered media producers and does not rebuild Search or Publish. Do not repeat it solely to confirm a watcher or Pending updates Build that already succeeded.

Selected implementation evidence is manual pilot review, focused generated HTML/source inspection, changed-source lint and relevant syntax checks, plus `git diff --check`. These address semantic markup, safe resource rendering, parser/module mistakes and accidental changes outside the intended owners. Manual review costs a few minutes per iteration, with total time dependent on refinement; single-document and final collection Build durations have not been measured. No new or changed automated tests, fixtures, harnesses, temporary regression scripts or browser smokes are prescribed. Any later test-code work needs its own agreed specification under [Test Contract Discipline](Test_Contract_Discipline.md).

The pilot is intentionally limited to `00008`; it is not evidence for every Work shape, malformed inputs, network failures or portable exports. Source review owns the general omit-empty and validation rules. The final Full reconciliation exercises generation across the collection, while manual visual acceptance remains the user's responsibility.

## Proposed Delivery Steps

The steps below are not started. Design-decision checkboxes above record agreement, rather than implementation completion.

### CE-0 — Readiness And Baseline

- [ ] Check current owners against the agreed identity-only Entry syntax, direct-Gallery scope and existing source/date preservation policy.
- [ ] Review the broad token/Build, Regenerate, Links and shared CSS owners against the agreed design; identify any ownership conflict before implementation.
- [ ] User completes the baseline Regenerate and clears the existing pending queue before the pilot starts.

**Gate:** the agreed implementation scope matches the current owners and the Working baseline is ready. Duration presentation and export work stay outside this slice; Series remains with its existing report and linking owners. **Record:** design decisions closed; readiness inspection and baseline Regenerate have not been confirmed.

### CE-1 — Entry Rendering And Generation

- [ ] Implement identity parsing and cached Work resolution without an authoring UI or modal.
- [ ] Render the H1, current metadata selection, reserved image frame and populated H2 Downloads/Links/direct-Galleries lists with escaped labels and validated targets.
- [ ] Reuse existing image and Gallery Media View behavior and token relationship extraction, including Catalogue self-reference suppression.
- [ ] Change Regenerate's body generator to emit Entry followed by the separate Related links directive; provide the Catalogue directive's H2 heading.
- [ ] Add Catalogue Entry CSS preserving the current image/title/metadata arrangement and placing resource sections below the image.

**Verification:** changed-source lint/syntax and bounded source review; inspect the pilot output in CE-2. **Gate:** the implementation is ready for `00008` without converting the rest of the Catalogue. **Record:** not started.

### CE-2 — Work 00008 Pilot And Refinement

- [ ] Convert only the `00008` Catalogue source to Entry plus Related links, preserving its identity and source dates.
- [ ] Produce its Working output through the watcher or exact targeted Build as appropriate.
- [ ] User reviews the token output and CSS using the manual loop above, editing `00008` through the Work editor when needed.
- [ ] Resolve pilot findings and record the accepted manual outcome and any remaining evidence limits.

**Verification:** user manual review and focused source/generated-HTML inspection, with only the necessary targeted rebuilds. **Gate:** the user accepts the pilot before collection-wide conversion. **Record:** not started.

### CE-3 — Code Review And Public Code Projection

- [ ] Review the final bounded diff for explicit token semantics, data/Links ownership, safe resources, image reservation, date preservation and compatibility residue.
- [ ] Resolve findings and rerun only checks affected by those changes.
- [ ] Project changed shared/public runtime and CSS through `bin/site-code-update`, inspect the exact tracked `site/` delta, then run `bin/site-code-update --check` and `bin/site-validate`.

**Verification:** final diff review and the required code-projection/static-reference checks; this does not Publish Catalogue data. **Gate:** no unresolved findings remain within this delivery and the public code projection agrees with its canonical owner. **Record:** not started.

### CE-4 — Full Reconciliation And Closeout

- [ ] Once the pilot and code review are accepted, run one Full reconciliation to convert all generated Catalogue bodies and build the complete collection.
- [ ] Confirm the operation's completion, pending-list outcome and preserved identity/date policy without adding a duplicate full build.
- [ ] Update durable token, Catalogue and regeneration owners to describe the delivered contract and record final evidence and limits.
- [ ] Close the delivery only when the complete Working Catalogue uses Entry plus the separate Related links directive.

**Verification:** the owning Full reconciliation result and bounded inspection of representative converted source/HTML; visual review remains manual. **Gate:** the initial result described below is delivered. Publish, Git commit/push and deployment remain separate explicit actions. **Record:** not started.

The initial result is complete when new and existing Catalogue documents use the Entry token followed by the separate Related links directive, each rendered document has its Work H1, agreed metadata and populated H2 resource/relationship sections, and image space is reserved before media loading. Storage stays private, duration and depth remain supported fields, and retained consumers read the agreed model. Entry has no authoring UI or modal, and ordinary Catalogue Image semantics remain intact. Field removal must leave no active editor, projection or report references; generated data must be reconciled after schema changes. Manual review owns visual fit. Any executable verification or test work will be selected and specified proportionately when implementation is approved, following [Test Contract Discipline](Test_Contract_Discipline.md).

## Inspection Basis

The field and ownership findings come from [canonical Work fields](../../studio/services/catalogue/catalogue_source.py), [Work editor definitions](../../studio/app/frontend/js/catalogue-work-fields.js), [public scalar projection](../../studio/services/catalogue/catalogue_generation_records.py), [complete Work assembly](../../studio/services/catalogue/generate_work_pages.py), [private report projection](../../studio/services/catalogue/catalogue_works_metadata.py), [Catalogue body generation](../../docs-viewer/services/docs_catalogue_work_record.py), [token rendering](../../docs-viewer/build/docs_builder/semantic_tokens.py), [regeneration](../../docs-viewer/services/docs_catalogue_regeneration.py) and [rendered heading extraction](../../docs-viewer/services/docs_document_packages/rendered_content.py). The 2026-10-02 population counts came from a read-only inspection of canonical `works.json`. The separately authorized 2026-10-07 retirements and Medium migration changed canonical source, field owners and documentation. The [Catalogue Source Model](Catalogue_Source_Model.md#validation-and-field-changes) records the delivered field boundary.

The image-space findings come from the [archived Work renderer](../../site/archive/assets/js/catalogue/routes/work-page.js), [archived primary-media component](../../site/archive/assets/js/catalogue/components/primary-media.js), [archived Catalogue CSS](../../site/archive/assets/css/catalogue.css), current token rendering and the [responsive-image helper](../../docs-viewer/runtime/js/shared/docs-viewer-responsive-image.js). Source inspection confirmed the old pixel-ratio CSS input and current runtime width/height assignment; no browser measurement or layout test ran. The initial metadata selection, private storage boundary and retention of duration/depth were agreed by the user on 2026-10-07.

Medium migration evidence: all 4,618 corrected descriptions were preserved exactly and all unrelated canonical metadata, IDs, ordering and the header were unchanged. The read-only canonical and field-inventory validators, explicit changed-source JavaScript/Python lint, Python syntax and whitespace checks passed. Local Refresh wrote 4,618 Work JSON records, regenerated private report metadata, deleted no generated files and queued all 4,618 Works for document Regenerate. A focused generated Work/report read confirmed the new schema and Medium shape. The single shared Media View runtime change was projected to `site/`; `bin/site-code-update --check` and `bin/site-validate` passed. Bounded code review traced current field ownership, exact request allowlists, generator/report agreement, six-column presentation and metadata readers, with no remaining findings. Tests and fixtures retain old field references and were neither changed nor run under the separate test-work policy; visual review remains manual. Restart Local Studio and hard-refresh the editor/Docs Viewer to load the changed server modules and browser assets. Regenerate, Publish, commit/push and public deployment remain separate actions; release the new public runtime together with the matching published Work JSON.

Generated Work `documents` retirement evidence: changed-source Python lint, syntax compilation and whitespace checks passed. Local Refresh wrote all 4,618 Work records as `work_record_v11`, changed no other generated payloads or private report metadata, deleted no files and queued all Works for Regenerate. A focused read of Work `00008` confirmed omission of `documents` and retained Series, links, downloads and direct Galleries. Bounded code review found no remaining active helper references or consumers requiring the retired field; document relationships retain the existing Links owner. Historical tests still reference the retired helper and field and were neither changed nor run. No shared runtime or tracked public projection changed; Regenerate, Publish, commit and push did not run.
