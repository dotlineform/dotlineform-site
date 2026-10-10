---
draft: false
doc_id: d-20260519-202931-66c794
title: Management Operations
added_date: "2026-05-19 20:29:31"
last_updated: "2026-10-10 17:06:58"
parent_id: d-20260424-000000-04d75e
---
# Docs Viewer Management Operations

Current boundary, 24 September 2026: the scope-era operation descriptions and test inventory below are historical. [Builder](Builder.md) owns the current Working → Preview → Deploy Repo lifecycle. Working Delete no longer prunes Preview/public output. Public document-location JSON, its builder/picker and the legacy Catalogue document-URL refresh are retired; their historical tests have not been migrated or removed by this cleanup.

## Security Constraints

- HTTP access is provided by the standalone Docs Viewer service at `DOCS_VIEWER_BASE_URL`.
- Loopback binding, CORS, static-file routing, and request-size limits are enforced by `docs-viewer/services/docs_viewer_service.py`.
- Endpoint constants are allowlisted by `docs-viewer/services/docs_management_routes.py`.
- Docs source write targets are constrained by `docs-viewer/config/scopes/docs_scopes.json`.
- Scope lifecycle ownership is recorded in `docs-viewer/config/scopes/docs_scope_manifest.json`; system-owned scopes are not delete-eligible.
- Source recovery relies on Git history, host/filesystem backups, or explicit manual copies made before risky operations.

Configured source roots in this repo are:

```text
docs-viewer/scopes/studio/source/documents/*.md
docs-viewer/scopes/analysis/source/documents/*.md
```

Local operational write targets include:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/
var/docs/logs/
docs-viewer/scopes/*/published/
site/assets/data/docs/scopes/<scope>/media/<type>/
```

## Operational Notes

- `bin/local-studio` starts Docs Viewer services and renders configured links, but Local Studio does not host Docs Viewer management itself.
- `docs-viewer/bin/docs-viewer` serves `/docs/`, Docs Viewer static/runtime/config files, generated-data reads, and management endpoints.
- The old standalone `docs-viewer/services/docs_management_server.py` HTTP entrypoint remains removed.
- If the local service is unavailable, normal Docs Viewer reads can fall back to static generated JSON; manage mode remains read-only and shows an unavailable message.
- Application source writes await their required generated output through the existing build owners. The filesystem watcher and suppression markers are retired.

## Confirmed Document Delete

Parent Index Delete accepts only exact checked IDs and expands their owned descendants once. Default sub-scope Delete accepts one exact `{scope, sub_scope, doc_id}` and applies only against its previewed source revision. Both existing controls use the shared `/docs/delete-preview` and `/docs/delete-apply` routes; displayed rows, titles, filenames, and current routes are never fallback identity.

For an exact configured public collection, preview adds `public_cleanup` derived from current public products. Confirmed apply commits the canonical source deletion and existing working rebuild first, then removes exact public by-ID and owned Mermaid products, filters only affected public inventories, and performs required Catalogue document-URL follow-through before returning success. Parent Delete updates tree, Recent, search, locations, and affected Catalogue URLs. Child Delete updates its manifest, by-ID, locations, and affected Catalogue URLs without changing its host, siblings, or parent inventories. A deleted public report host loses its routes and derived child URLs while surviving child files remain independently owned. Local collections report public cleanup as not applicable.

Only after any required public cleanup succeeds, a configured lineage child Delete applies the exact Working-owned v3 follow-through. Working Delete removes its complete record without deleting independently canonical Editorial or public documents. Editorial Delete removes only the exact child and drops the record when no children remain. A changed table rebuilds only the configured Working collection; direct non-lineage and unrelated collection deletes leave the table untouched. The response carries a nested `lineage` receipt only for a matched Working or Editorial collection.

Public or Catalogue cleanup failure after source commit is a non-success with `committed: true` and `retry_delete: false`; it leaves private lineage unchanged and is not reported as a safe repeat of the irreversible Delete. The browser retains its existing selection, confirmation, cancel focus, fallback/reconciliation, and refresh owners while presenting exact public impact from the server receipt.

Scope-wide **Publish** remains the only positive public promotion. Its negative plan removes only current explicit `publishable: false` exclusions and reports `excluded`/`excluded_count`. Public files absent from canonical source for any other reason are retained and unreported; supported document Delete has already completed its own exact negative cleanup.

## Subject Assignment In Source

**Assign Subject** belongs to the Source editor's Directives menu. `docs-viewer/runtime/js/management/source-editor/subject-modal.js` reads the captured unsaved buffer through `POST /docs/source/context`, then sends its selected Folder, Work or None as `subject_fields: {folder_path: "<path-or-empty>", work_id: "<five-digit-id-or-empty>"}` with that same buffer and its immutable document target. Only the selected field is nonempty. The exact configured collection's registered `authoring_subject` group owns availability and its metadata aspect owns value validation; `folder_subject_supported` projects whether its authoring fields include `folder_path`.

`docs-viewer/services/docs_management_source_service.py` uses the shared strict front-matter parser and span-preserving field writer to return the candidate `source_text`. It updates or clears only the Subject fields, preserves other metadata, body and timestamps, and performs no source write or generation. Apply replaces the current editor buffer only when its captured revision and mounted adapter still match. Cancel leaves it unchanged. Save owns canonical persistence, timestamps, exact document/Links generation and retained-list/display updates.

Work selection reuses the generated Catalogue provider and keeps exact five-digit identity strings. Folder preselects/prefills an existing declaration and accepts a decoded relative target, absolute path or file URL under the configured Projects root. The existing collection normaliser canonicalises it to a relative `folder_path` and clears `work_id`; unsupported collections omit the Folder choice and reject a Folder write through their metadata owner. None removes both declarations. The former blanket workspace rejection of Folder assignment is removed. Malformed/conflicting source must be corrected before its context can be read. Existing missing Work targets require a current Work, Folder or None before Apply.

The separate immediate-write `POST /docs/assign-field-group` endpoint, its client helper and mutation plan are retired without aliases. Source's ordinary Save/discard lifecycle handles Subject changes. **Open Subject folder** follows Assign Subject in Directives. Menu opening reads the current unsaved buffer through the same context service; only a valid Folder subject enables it. Activation awaits the existing local-link service to open that folder beneath the configured Projects root, with silent success and visible failures. Work, None, unsupported documents and invalid source remain disabled. The former Edit Finder item and unused Document Info metadata contribution/normalisation are retired. [Assign Subject In Source Editor](deliveries/Assign_Subject_In_Source_Editor.md) records this change and its evidence.

## Verification

Focused tests cover the current boundary:

- `docs-viewer/tests/python/test_docs_management_metadata.py`
- `docs-viewer/tests/python/test_docs_document_subjects.py`
- `docs-viewer/tests/python/test_docs_dotlineform_projects_customisation.py`
- `docs-viewer/tests/python/test_docs_management_routes.py`
- `docs-viewer/tests/python/test_docs_public_delete_cleanup.py`
- `docs-viewer/tests/python/test_docs_document_publication_lineage.py`
- `docs-viewer/tests/python/test_docs_publish_gate.py`
- `docs-viewer/tests/python/test_docs_management_mutations.py`
- `docs-viewer/tests/python/test_docs_management_subscope_delete.py`
- `docs-viewer/tests/python/test_docs_scope_lifecycle.py`
- `docs-viewer/tests/python/test_build_document_locations.py`
- `docs-viewer/tests/python/test_docs_catalogue_document_urls.py`
- `docs-viewer/tests/python/test_docs_subscope_customisations.py`
- `docs-viewer/tests/python/test_docs_viewer_public_runtime_boundaries.py`
- `docs-viewer/tests/smoke/docs_viewer_service_manage.py`
- `docs-viewer/tests/python/test_docs_import_service.py`
- `docs-viewer/tests/python/test_docs_export.py`
- `docs-viewer/tests/python/test_docs_import.py`

The `docs` check profile runs parser and docs service checks. Use the narrowest relevant check for source-only documentation edits, and rebuild generated Docs Viewer payloads only when the task explicitly calls for that follow-through.

## Related References

- [Endpoint Overview](Endpoint_Overview.md)
- [Script Overview](Scripts_Overview.md)
- [Scripts](Scripts.md)
- [Docs Viewer](Docs_Viewer.md)
