---
draft: false
doc_id: d-20260519-202931-66c794
title: Management Operations
added_date: "2026-05-19 20:29:31"
last_updated: "2026-10-13 15:47:31"
parent_id: d-20260424-000000-04d75e
---
# Docs Viewer Management Operations

The single configured Docs workspace owns Working source/generated operations. [Builder](Builder.md) owns Working generation and the Preview/publication lifecycle. Working Delete updates its own source/generated products; Publish owns Preview/public distribution. Public document-location JSON, its builder/picker and the legacy Catalogue document-URL refresh remain retired.

## Security Constraints

- HTTP access is provided by the standalone Docs Viewer service at `DOCS_VIEWER_BASE_URL`.
- Loopback binding, CORS, static-file routing, and request-size limits are enforced by `docs-viewer/services/docs_viewer_service.py`.
- Endpoint constants are allowlisted by `docs-viewer/services/docs_management_routes.py`.
- Docs source write targets are constrained by `docs-viewer/config/workspace/docs-workspace.json` and exact configured collection ownership.
- Direct Catalogue New/Delete remain Regenerate-owned. Ordinary editorial menu restrictions belong to the frontend; request/model integrity and confined paths belong to services.
- Source recovery relies on Git history, host/filesystem backups, or explicit manual copies made before risky operations.

Configured source storage beneath the existing `DOTLINEFORM_DOCS_BASE_DIR` is:

```text
working/source/documents/*.md
working/source/collections/<collection>/documents/*.md
```

Local operational write targets include:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/
var/docs/logs/
<configured Docs root>/working/generated/
<configured Docs root>/working/generated/collections/<collection>/
```

## Operational Notes

- `bin/local-studio` starts Docs Viewer services and renders configured links, but Local Studio does not host Docs Viewer management itself.
- `docs-viewer/bin/docs-viewer` serves `/docs/`, Docs Viewer static/runtime/config files, generated-data reads, and management endpoints.
- The old standalone `docs-viewer/services/docs_management_server.py` HTTP entrypoint remains removed.
- If the local service is unavailable, normal Docs Viewer reads can fall back to static generated JSON; manage mode remains read-only and shows an unavailable message.
- Application source writes await their required generated output through the existing build owners. The filesystem watcher and suppression markers are retired.

## Confirmed Document Delete

Ordinary confirmation uses the full already-loaded Index subtree, including collapsed descendants. Collection confirmation uses its singular exact flat target. Cancel performs no request or write; confirmation sends one `POST /docs/delete` with either `{doc_ids: ["<ordinary-root-id>"], confirm: true}` or `{collection: "<configured-id>", doc_id: "<id>", confirm: true}`. The service accepts exact nonempty ordinary ID arrays for subtree roots; displayed titles, filenames and current routes never supply fallback identity. Preview/apply routes, source revisions and a separate collection Delete capability request are retired without aliases.

The service resolves its configured owner once, reads the ordinary tree and Selected list once, expands subtree scope once and unlinks only exact confined source paths. Ordinary deletion updates `index-order.json`; both forms remove exact Selected identities. Deleting the configured ordinary default clears that setting and carries the known empty value into generated browser configuration and the response. The browser applies that returned change locally without a configuration reload. There is no protected-descendant editorial guard. Collection hosts retain frontend Delete restrictions; named collection deletion leaves its host, siblings and ordinary tree unchanged. Direct Catalogue deletion is rejected through the Regenerate boundary.

Known deleted IDs, the remaining parent map, updated Selected and resolved configuration feed the existing in-process document/Links builders. They remove exact by-ID/navigation or collection-manifest entries and the deleted documents' relationship records/contributions. They do not reopen sources to rediscover identities, render unrelated Markdown, audit saved navigation or preflight unrelated by-ID files. Links retains exact affected-neighbour maintenance. Saved Recent/Search and registered media production retain their separate owners; Publish later reconciles its prepared public set.

Execution stops at its failing phase and retains completed effects. Responses carry `target`, requested/actually deleted IDs, source/tree/Selected/generation completion flags and `phase`; a failing source target is included when applicable. Default clearing is reported only after its write completes. No restoration, recovery build, automatic retry, public-cleanup or lineage receipt is produced. Diagnose the reported target/phase and explicitly complete the owning repair or Build; success is returned only after required generation completes.

The browser forwards actual committed deletions to retained views even when later service work fails. After complete ordinary generation, it reads Index once. When the displayed document was removed, it awaits return to a surviving retained caller; otherwise it opens the collection host or surviving ordinary root, or hides an empty document pane. Deleted retained callers are released. The busy state covers service execution and display completion. Generation failures remain distinct from completed-delete projection/display failures, and listener failures are surfaced. [User Facing Rules](data/User_Facing_Rules.md) M.17 records implementation evidence and pending manual acceptance.

## Draft And Position

Draft submits its intended boolean with the exact ordinary or supported collection target. The service parses that source once, rewrites only its Draft field, preserves body/formatting/dates and hands prepared metadata/source/report input into exact in-process generation. The frontend uses the common committed-record projection and reports completed source writes separately from generation/projection failures. `unpublishable.json` is independent of readiness; otherwise permitted excluded documents can still change Draft. Star writes independent Selected membership; Unstar needs only the exact owner/identity and Selected list, while Star reads the metadata needed for its row.

Position accepts an exact ordinary ID, destination ID and Before/After/Inside placement. It moves the complete node once, checks destination/cycle integrity and projects saved navigation plus only the moved by-ID parent metadata, preserving Markdown/body/dates and Links. Collection-host root placement belongs to the frontend: Before/After another root or Inside Root. Common metadata projection and one awaited Index refresh complete the browser action. A failure after the canonical tree write reports `position_saved: true`, its committed record and unfinished generation without restoration.

## Subject Assignment In Source

**Assign Subject** belongs to the Source editor's Directives menu. `docs-viewer/runtime/js/management/source-editor/subject-modal.js` reads the captured unsaved buffer through `POST /docs/source/context`, then sends its selected Folder, Work or None as `subject_fields: {folder_path: "<path-or-empty>", work_id: "<five-digit-id-or-empty>"}` with that same buffer and its immutable document target. Only the selected field is nonempty. The exact configured collection's registered `authoring_subject` group owns availability and its metadata aspect owns value validation; `folder_subject_supported` projects whether its authoring fields include `folder_path`.

`docs-viewer/services/docs_management_source_service.py` uses the shared strict front-matter parser and span-preserving field writer to return the candidate `source_text`. It updates or clears only the Subject fields, preserves other metadata, body and timestamps, and performs no source write or generation. Apply replaces the current editor buffer only when its captured revision and mounted adapter still match. Cancel leaves it unchanged. Save owns canonical persistence, timestamps, exact document/Links generation and retained-list/display updates.

Work selection reuses the generated Catalogue provider and keeps exact five-digit identity strings. Folder preselects/prefills an existing declaration and accepts a decoded relative target, absolute path or file URL under the configured Projects root. The existing collection normaliser canonicalises it to a relative `folder_path` and clears `work_id`; unsupported collections omit the Folder choice and reject a Folder write through their metadata owner. None removes both declarations. The former blanket workspace rejection of Folder assignment is removed. Malformed/conflicting source must be corrected before its context can be read. Existing missing Work targets require a current Work, Folder or None before Apply.

The separate immediate-write `POST /docs/assign-field-group` endpoint, its client helper and mutation plan are retired without aliases. Source's ordinary Save/discard lifecycle handles Subject changes. **Open Subject folder** follows Assign Subject in Directives. Menu opening reads the current unsaved buffer through the same context service; only a valid Folder subject enables it. Activation awaits the existing local-link service to open that folder beneath the configured Projects root, with silent success and visible failures. Work, None, unsupported documents and invalid source remain disabled. The former Edit Finder item and unused Document Info metadata contribution/normalisation are retired. [Assign Subject In Source Editor](deliveries/Assign_Subject_In_Source_Editor.md) records this change and its evidence.

## Verification

Existing mutation, metadata, route and collection-delete tests include retired scope, revision, preview/apply and recovery contracts. They are unreviewed for this current boundary; migration, coverage specification and test execution require separately agreed work under [Test Contract Discipline](Test_Contract_Discipline.md). Do not use historical test names/profile membership as evidence of current behavior. Focused lint, syntax/import diagnostics and source review provide the implementation evidence recorded in [User Facing Rules](data/User_Facing_Rules.md); UI interaction and live failure behavior remain manual acceptance gates. Repository documentation edits use no Docs/Search rebuild.

## Related References

- [Endpoint Overview](Endpoint_Overview.md)
- [Script Overview](Scripts_Overview.md)
- [Scripts](Scripts.md)
- [Docs Viewer](Docs_Viewer.md)
