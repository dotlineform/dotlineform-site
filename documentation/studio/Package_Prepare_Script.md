---
draft: false
doc_id: d-20260503-150500-b0f1df
title: Package Prepare Script
added_date: "2026-05-03 15:05:00"
last_updated: "2026-10-20"
parent_id: d-20260424-000000-50b63f
---
# Package Prepare Script

`docs-viewer/services/docs_document_packages/export.py` owns the shared package producer and ordinary Working CLI. [Package Prepare](Package_Prepare.md) owns the Manage workflow; [Package Prepare Profiles](Package_Prepare_Profiles.md) owns the two current profiles. Preparation reads document inputs and writes disposable package artifacts, preserving source, generated documents, Search and publication state.

## Inputs And Workspace

Profiles belong to `docs-viewer/config/document-packages/profiles.json`. `docs-viewer/config/workspace/docs-workspace.json` resolves the existing Docs workspace and exact configured collections beneath `DOTLINEFORM_DOCS_BASE_DIR`. Retired scope/stage storage and request aliases are not supported.

The existing absolute `DOTLINEFORM_PROJECTS_BASE_DIR` independently resolves the readable/writable `data-sharing/` workspace. There is no repository fallback or automatic replacement workspace. Package and metadata paths stay beneath its configured boundaries:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/
  exports/<local timestamp>-documents-<profile id>.json[l]
  meta/<export_id>.meta.json
```

Output filenames use the local runtime timezone. Metadata `generated_at` and `export_id` use UTC; the ID is `ds_YYYYMMDDTHHMMSSZ`. [Package Export Metadata](Package_Export_Metadata.md) owns `data_sharing_export_meta_v4`, exact optional collection provenance and returned Review/Import capabilities. Output and metadata collisions prevent writing.

## Application Preparation

One `POST /docs/packages/prepare-options` receives captured `doc_ids` and required exact `collection`. It resolves the owner once and returns profiles, workspace availability and only the checked flat metadata needed by the modal. It reads confined source fields without ordinary Index traversal, body rendering, general source-model/Subject/readiness validation, generated manifest/Links reads or Catalogue setup. The Index package entry point and flat-versus-tree request mode are retired without aliases.

The modal owns missing-summary filtering and document-count limits over the captured checked IDs. One `POST /docs/packages/prepare` then receives required `collection`, final `profile_id`, explicit `doc_ids`, `target_format`, `content_format` and optional `dry_run`. Application requests carry no `select_all`, summary-filter or publication-eligibility flags. The producer does not repeat those choices, expand selection or silently skip missing selected input.

Application Prepare resolves its exact collection owner and reads each selected source once, retaining strict front-matter parsing, exact ID/filename binding, string Title representation and configured path/symlink confinement. Tree output needs no saved manifest or renderer. Content output consumes saved collection management metadata for link identities, opens only required selected saved Links, and constructs one lazy collection content renderer/cache. This preserves report/token rendering, URL safety, escaping and Summary policy without building unused by-ID metadata or rendering unselected bodies.

## CLI Selection

The CLI remains an independent ordinary Working selection owner. It uses its full source context and existing validation/rendering path, applies explicit/all and supported summary choices, and retains tree-profile descendant expansion. It delegates completed selection to the same profile/format/output producer as the application. It does not accept a scope/stage picker. Its ordinary packages have no application Import entry point now that both application intake actions require a configured collection.

Inspect current flags:

```bash
python3 docs-viewer/services/docs_document_packages/export.py --help
```

Prepare an explicit ordinary document without writing:

```bash
python3 docs-viewer/services/docs_document_packages/export.py --config-id document-content --doc-id d-20260426-164043-e14f49
```

Select all ordinary documents, optionally applying the CLI summary filter:

```bash
python3 docs-viewer/services/docs_document_packages/export.py --config-id document-content --all --missing-summary-only
```

Write JSON content with plain-text body conversion when the profile supports both choices:

```bash
python3 docs-viewer/services/docs_document_packages/export.py --config-id document-content --all --format json --content-format plain_text --write
```

The default is dry-run. `--write` writes only package/metadata artifacts. `--include-summary-complete` disables a profile's default missing-summary choice; `--doc-id` is repeatable and `--doc-ids` accepts comma-separated IDs. Config/repository overrides remain explicit CLI flags.

## Producer And Output

The common producer validates the selected enabled profile, supported target/content formats, configured mapped fields/transforms, output paths and collisions. Mapping/rendering failures prevent output. Summary is flattened to one paragraph for package fields and expanded package-only Summary text; canonical source is unchanged. Per-record content truncation retains the profile's paragraph boundary and marker.

Document-row JSONL begins with a `data_sharing_header` carrying export/profile/content identity. JSON document-row output carries top-level schema/export identity and records. The tree profile writes JSON tree structure without body content and remains export-only. Internal metadata preserves exact prepared IDs, source timestamps and Review/Import capability/provenance. Returned-package parsing, provenance and current-source validation remain with their existing full-package owners; this cleanup does not weaken them.

The report includes `ok`, `dry_run`, `export_id`, CLI `config_id` or application `profile_id`, resolved formats, paths, selected/exported IDs, warnings/errors, issue counts and `output_written`. Collection reports carry their exact configured collection. Counts retain:

```text
selected = exported + failed + skipped
truncated <= exported
```

Application `skipped` is zero because modal exclusions precede submission. CLI selection retains its skipped records and warnings. Missing/unreadable/malformed selected inputs fail source-context loading before record counts; a record-mapping failure increments `failed`. The CLI exits 0 for a valid report, 1 for command/runtime failure, and 2 for reported validation errors that prevent output.

## Ownership And Verification

`selected_sources.py` owns application metadata discovery and selected source handoff. `source_context.py` retains CLI/returned full context. `rendered_content.py` owns cached HTML/headings/text extraction; `export.py` separates selection owners from the common producer. Preparation runs no Build, Search, media production or source/relationship writes.

[User Facing Rules](data/User_Facing_Rules.md) M.06/M.22 records focused lint, compilation/import diagnostics and distinct final source/diff review. No tests or live package writes ran. Existing package tests include retired scope and discovery contracts and need separately agreed review/migration before they can serve as current evidence. Manual acceptance remains for the Manage selection/options flow, content/tree formats, Summary and relationship output, rendering/input failures and confined output/collision reporting.
