---
draft: false
doc_id: d-20260519-000000-a0da45
title: Catalogue Source Model
added_date: "2026-05-19 00:00:00"
last_updated: "2026-11-18"
parent_id: d-20260423-000000-d015e6

---

# Catalogue Source Model

## Canonical Families

The five canonical stores live in `studio/data/canonical/catalogue/`. Studio owns their edits and live lookup projections.

| Store | Schema | Contents |
| --- | --- | --- |
| `works.json` | `catalogue_source_works_v2` | Work map keyed by exact five-digit `work_id`. |
| `series.json` | `catalogue_source_series_v2` | Series map with `series_id` and `title`. |
| `galleries.json` | `catalogue_source_galleries_v1` | Gallery definitions with `gallery_id`, `title` and optional creation `added_date`, `description` and `marker`. |
| `galleries-by-work.json` | `catalogue_source_galleries_by_work_v1` | Work IDs mapped to direct Gallery ID arrays. |
| `series-galleries.json` | `catalogue_source_series_galleries_v1` | `pairs_by_series` maps Series to explicitly relevant Gallery IDs. |

Headers carry schema identity. The serializers own stable field and record order. [Work and Series source](../../studio/services/catalogue/catalogue_source.py) · [Gallery source](../../studio/services/catalogue/catalogue_galleries.py) · [Relevance source](../../studio/services/catalogue/catalogue_series_galleries.py)

## Relationships And Identity

Each Work belongs to exactly one existing Series. Series and Galleries can be empty. A Work may appear in several Galleries, including groups spanning Series. Its Gallery IDs live in the membership store, while its `series_id` lives on the Work.

Series–Gallery relevance is authored independently. It makes a Gallery relevant to the Series' Works without changing the Gallery's direct member selection. Moving a Work between Series preserves those independent choices. Document Subjects and authored Catalogue references have their own owners. [Document associations](Document_And_Catalogue_References.md#catalogue-identity-and-document-associations)

## Metadata And Ordering

Work fields are defined in `catalogue_source.py`. They include identity and Series, Title, Year/Year display, Medium, Duration, Storage location, physical dimensions, original-media location, intrinsic pixel dimensions, `media_version`, `image_staged`, downloads and links. A Work's `media_source_id` is omitted for the configured default and names an exact non-default root when supplied. [Field definition](../../studio/services/catalogue/catalogue_source.py) · [Media roots](Catalogue_Media_Pipeline_Config.md#work-media-sources)

The browser owns nonblank Title, whole-Year/Year-display completion, numeric physical fields and loaded Series/Gallery choices. Persistence preserves authored metadata and source-path spelling. Optional scalar fields follow serializer omission rules. Height, width and depth remain Work metadata, while Save measures intrinsic pixels from the original image.

Downloads and links are optional arrays of objects. An absent field means no entries. Explicit null or malformed array/object representation fails. Downloads retain their filename and label with a server-owned `staged` flag. Links retain label and URL. Empty arrays are omitted on serialization. The editor owns resource authoring feedback, browser consumers own URL safety, and file owners retain upload/path/required-byte checks.

An omitted update preserves a value; clearing an optional scalar sends request null and removes its canonical key. Preserve supplied zero/false and authored text literally, including source-path components, resource labels and filenames. Consumer formatting may escape output and derive query/sort values, but does not trim, coerce, repair or substitute fallback content. Optional resource groups may be absent; their explicit values must remain arrays of objects.

Physical height, width and depth are independently optional. Display supplied values in that order without requiring a pair or applying a second range/completeness rule downstream. Save's file-measured pixels and server staging/media versions have separate ownership from authored dimensions.

Series definitions contain ID and Title. Gallery descriptions are optional nonempty trimmed single lines, and markers are `brush`, `video` or `square-library`. Repeated titles are allowed. Selection uses IDs. The editor sorts its member list by title, while generated membership lists use Work ID order. [Editor selection](Catalogue_Work_Editor.md#work-lookup-and-selection)

## Save And Delete

Work requests identify an exact existing Work, or a collision-free new ID, and carry authored fields in `record`. Gallery replacement lists are separate `gallery_ids`. Work metadata and changed membership share the source transaction. Series Create/Save takes `series_id` and a title-only `record`. Gallery Create/Save carries identity, title, the Series/relevance choice and optional presentation fields. [API and persistence trace](Catalogue_Services.md)

Work Delete removes the selected records and their direct memberships and carries captured media descriptors onward. Definition deletion removes that definition and its current relationship entries. The UI establishes the empty-Series precondition from saved Works. Direct service callers must honor that precondition. Existing services address exact saved targets and carry before/after state through completion. [Delete and recovery](Catalogue_Work_Editor.md#delete)

## Validation And Field Changes

### Catalogue Source Audit

After deliberate external canonical edits or when diagnosing source integrity, the existing audit reads all five families.

```bash
python3 studio/services/catalogue/validate_catalogue_source.py
```

Use the project interpreter from the repository root. `--source-dir <path>` selects another existing source directory. The audit checks allowed fields, ID/key agreement, required Series endpoints, configured media-source IDs, positive media versions, explicit staging booleans and resource representation. Gallery checks cover definition/presentation values and distinct known membership endpoints. Relevance checks cover known endpoints and sorted unique pairs. Success prints counts and `Validation passed.` with exit 0. Validation or input failure exits nonzero. It reads no media bytes and writes no source, output or queues. [Audit implementation](../../studio/services/catalogue/validate_catalogue_source.py)

Routine Save and queued Refresh trust completed authoring and inspect the inputs they need. Explicit family repair has a broader audit scope. Private-report maintenance audits Works/Series, compact-index repair additionally audits Gallery definitions/memberships, and relationship/Gallery-record repair audits all five stores. These commands write their selected output family. [Repair commands and prerequisites](Catalogue_Save_And_Refresh.md#private-report-input-maintenance)

### Field Changes

The checked `catalogue_field_registry_v2` inventory lists Work/Series fields and output families. The source owner defines and serializes the fields. Mutation and queue code selects effects. Update the editor, source, consumers and inventory together when changing a field.

```bash
python3 studio/services/catalogue/verify_catalogue_field_registry.py
```

This read-only verifier compares the inventory's families and field sets with the canonical constants and checks declared artifact-family names. [Inventory](../../studio/data/config/catalogue/catalogue-field-registry.json) · [Verifier](../../studio/services/catalogue/verify_catalogue_field_registry.py)

## Output Boundary

Save completes canonical state and selected staged media. Refresh projects the selected reader records and private inputs into Working, then Regenerate prepares Catalogue documents. Publish consumes their completed selections. [Implementation trace](Catalogue_Services.md#follow-a-work-save-and-refresh) · [Generated read models](Catalogue_Indexes_And_Payloads.md#generated-read-models) · [Historical field migrations](../deliveries/Studio_And_Catalogue_Ownership_Review.md#source-migrations)
