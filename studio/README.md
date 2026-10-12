# Studio Development

Studio is the local Catalogue authoring and maintenance app. It owns canonical Work, Series, Gallery and membership records, validated mutations, media preparation, and the selected Catalogue Refresh handoff. Docs Viewer separately owns document browsing, Catalogue document regeneration and the unified Publish operation. Durable development documentation lives in [documentation/studio](../documentation/studio/).

## Repository structure

| Path | Responsibility |
| --- | --- |
| `app/frontend/` | Studio shell, registered route template, browser configuration, Work editor and focused browser helpers. |
| `app/assets/` | Studio-owned stylesheets. |
| `app/server/studio/` | Loopback HTTP server, runtime-config projection, Catalogue API adapter and bounded multipart uploads. |
| `services/catalogue/` | Canonical validation and transactions, Work/Series/Gallery operations, live lookups, media completion, incremental queues, Refresh and maintenance commands. |
| `services/media/` | Derivative generation utilities and remote media transport. |
| `data/canonical/catalogue/` | Authoritative Catalogue JSON. |
| `data/config/catalogue/` | Checked Catalogue field/artifact inventory. |
| `shared/python/` | Studio-owned path, environment, pipeline, media, logging and other shared helpers. |
| `tests/` | Existing Python, JavaScript and route-boundary checks, subject to the maintained test policy. |

`studio_python_paths.py` establishes the service/shared import paths for entrypoints. Domain modules use the established `catalogue.*`, `media.*` and shared imports; failures propagate without retrying another package name. App-neutral browser components belong under repository `shared/frontend/` when their contract warrants sharing. [Source Tree Ownership](../documentation/studio/Source_Tree_Ownership.md) owns placement rules.

## Run the local app

Run project commands from the repository root:

```bash
bin/local-studio
```

The runner loads `.env.local` and starts the loopback server. Open the printed `/studio/catalogue-work/` URL. The Work editor is the sole registered Studio route; Series and Gallery workflows are embedded in that editor. The former Studio home and field-registry pages are retired.

`STUDIO_APP_HOST` and `STUDIO_APP_PORT` select the local binding, `STUDIO_APP_ENABLED=0` suppresses startup, and `STUDIO_APP_ACCESS_LOG=1` enables ordinary access logs. The server validates loopback binding. It serves Studio shells/static assets, confined project-media reads, runtime configuration, and Catalogue APIs; there is no offline editing or save fallback.

Start sibling surfaces independently:

```bash
docs-viewer/bin/docs-viewer
bin/site-preview
```

Docs Viewer serves `/docs/` and Docs Review. Site preview serves the tracked `site/` artifact. Studio does not proxy those services or serve the deployed public reader. [Local Studio App](../documentation/studio/Local_Studio_App.md) owns startup and server boundaries; [Studio Runtime](../documentation/studio/Studio_Runtime.md) owns browser composition.

## Configuration and storage

| Owner | Responsibility |
| --- | --- |
| [app/frontend/config/studio-config.json](app/frontend/config/studio-config.json) | Checked route registry, template/script selection and route-ready identity. |
| `app/server/studio/studio_app_config.py` | Route validation and browser-safe runtime projection from configuration, environment, pipeline settings and code-owned values. |
| [data/config/catalogue/catalogue-field-registry.json](data/config/catalogue/catalogue-field-registry.json) | Canonical field and artifact-family inventory interpreted by Catalogue services. |
| [_data/pipeline.json](../_data/pipeline.json) | Logical Work-media source roots, staging layout, image variants and encoding policy. |
| [docs-viewer/config/workspace/docs-workspace.json](../docs-viewer/config/workspace/docs-workspace.json) | Working/Preview reader output, Work asset locations and public destinations. |

The checked Studio JSON is not the complete browser payload. The server supplies `/studio/runtime-config.json`; `studio-config.js` loads it for the shell and route. Runtime values are not copied back into the source JSON. Route copy, controls, service endpoints and executable behavior remain with their code owners. [Studio Config JSON](../documentation/studio/Studio_Config_JSON.md) describes the projection contract.

Canonical sources are the repository files `works.json`, `series.json`, `galleries.json`, `galleries-by-work.json` and `series-galleries.json` beneath `data/canonical/catalogue/`. A Work belongs to at most one Series and may belong to multiple Galleries; definitions may be empty. Exact IDs and explicit memberships own these relationships. [Catalogue Source Model](../documentation/studio/Catalogue_Source_Model.md) owns their schemas.

Set the independent external roots in `.env.local`:

- `DOTLINEFORM_PROJECTS_BASE_DIR` owns original project media and `catalogue/media-staging/`. The pipeline registers logical `projects` and `processing` media-source identities beneath this root.
- `DOTLINEFORM_DOCS_BASE_DIR` selects the existing Docs workspace directly. Refresh writes Catalogue reader JSON under `working/generated/catalogue/` and selected Work media under `working/assets/works/`. Publish retains a separate `preview/` snapshot and `preview/assets/works/`.

Neither root is a fallback for the other. Configured source identities and confined paths are validated; unavailable storage fails without manufacturing a replacement workspace. Local operational reports, logs and caches belong under ignored `var/` or the configured external owners. Remote credentials remain local and outside tracked configuration. [Catalogue Media Pipeline Config](../documentation/studio/Catalogue_Media_Pipeline_Config.md) and [Media And Asset Handling](../documentation/studio/Media_And_Asset_Handling.md#workspace-configuration-and-storage) own media policy.

## Reads, Save and Refresh

Studio editor, Work/Series search and focused record reads use live canonical server projections. They have no persisted lookup-directory fallback. Docs Viewer Catalogue and report readers consume separately refreshed output; they can lag behind a successful Save until Refresh completes. [Catalogue Architecture](../documentation/studio/Catalogue_Architecture.md) owns that distinction.

The normal workflow is:

| Operation | Completed outcome |
| --- | --- |
| Save or Delete | Validated canonical mutation, required media staging, known-effect queue updates and fresh editor records. |
| Refresh Catalogue | Selected Working metadata/media, compact and relationship indexes, private report inputs and Work readiness. |
| Regenerate in Docs Viewer | Refreshed queued Catalogue Work sources/documents and completed selections forwarded to publication. |
| Docs Publish | Each queued Work's Preview/repository/R2 output, followed by shared Preview preparation and distribution. |

Each application operation is awaited through its required completion. Create/Save/Delete check exact targets and their operation-specific requirements through focused services and the canonical transaction owner, without complete canonical family audits. Work and Gallery Save trust the UI's authoring choices; Series writes and definition deletions retain their stated title/revision/member checks. New media is prepared in Projects-owned staging and can display there immediately; Refresh transfers selected bytes into Working. Save does not publish public data or upload media to R2.

`working/catalogue-updates-pending.json` and `working/catalogue-publish-pending.json` are private workflow state beneath the Docs root. Mutations record known Work, Gallery, Series, media and shared-output effects. Normal operations consume those supplied selections; missing or malformed queues stop rather than becoming an empty queue or triggering discovery. Full reconciliation and repair remain explicitly selected maintenance.

Refresh also owns private aggregate report inputs and Work Document Coverage. Report readers use saved Catalogue projections while their explicitly owned filesystem inspection remains live. Private report output does not enter the public Catalogue artifact inventory. [Catalogue Save And Refresh](../documentation/studio/Catalogue_Save_And_Refresh.md) owns selection, readiness, reader timing and recovery.

## Publication and recovery

Complete Save/Delete → Refresh Catalogue → Regenerate before using Docs Viewer's single Publish action. Publish does not implicitly Refresh or Regenerate. Docs Viewer owns its empty-object `/docs/publish` request, completes each queued Work's Preview and distribution, then prepares/distributes shared output once. [Catalogue Deployment](../documentation/studio/Catalogue_Deployment.md) owns the exact repository/R2 selections and completion rules.

Public Catalogue JSON and thumbnails are tracked under `site/assets/data/catalogue/`; primary images and downloads use configured R2 destinations. Catalogue document payloads reach the configured public Docs output. The frozen legacy `site/archive/` tree is outside active generation. Studio frontend/server code is local-only and is not a public runtime projection.

Failures retain completed effects and accurate pending selections. Fix the reported source, producer or destination and rerun the owning operation. Interrupted Work distribution retains its Preview progress; complete that Publish before returning to authoring, Refresh or Regenerate. Shared preparation failure prevents shared distribution, while a distribution failure retains completed Preview. Media cleanup remains an explicit separate operation.

Review the resulting repository output with `bin/site-preview`. Git commit and push remain explicit actions. Deploy Public is the separate manually triggered GitHub Pages workflow over committed `site/`, with no deploy-time build or external-workspace access. A successful local Publish is not a Git commit or public deployment.

## Explicit maintenance and development checks

The normal queue-selected Refresh has a CLI equivalent:

```bash
python3 studio/services/catalogue/catalogue_json_build.py --write
```

This command writes to the configured Working workspace; it is not a dry-run or full reconciliation. Its mutually exclusive `--compact-indexes`, `--series-galleries`, `--gallery-records`, `--private-report-inputs` and `--work-document-coverage` flags select explicit family repair. Choose a family only when its baseline or design needs maintenance, and follow its owning prerequisites.

For the intentional read-only **Catalogue source audit**, run from the repository root:

```bash
python3 studio/services/catalogue/validate_catalogue_source.py
```

This audits all five canonical stores, with optional `--source-dir <path>` and no family selector. It prints validation results and exits `0` for valid data or nonzero for invalid/unreadable input, without generating output, changing queues, scanning media or requesting remote URLs. Download/link labels are UI guidance rather than model requirements. Ordinary Create/Save/Delete and normal Refresh never call the complete audit functions; the five explicit family-repair modes above retain their documented input audits. [Catalogue Source Model](../documentation/studio/Catalogue_Source_Model.md#catalogue-source-audit) owns the full CLI contract and audit scopes.

The separate read-only field-inventory audit is:

```bash
python3 studio/services/catalogue/verify_catalogue_field_registry.py
```

Standalone derivative and R2 utilities under `services/media/` are explicit maintenance tools; they do not replace normal Save, Refresh or Docs Publish. Inspect their current command contracts and write/network effects before using them.

Use [Development Checklist](../documentation/studio/Development_Checklist.md) for implementation guardrails and [Testing](../documentation/studio/Testing.md) for evidence selection. Repository lint tooling lives in `tooling/lint/` and is invoked through `bin/lint`, `bin/lint-python` or `bin/lint-js`. Select the smallest existing check that addresses a concrete changed contract; test creation, updates and profile changes need separately agreed specifications. Existing historical tests are not automatically accepted current coverage. Ordinary visual and interaction review remains manual.

Keep durable documentation in `documentation/studio/` and edit it directly; those repository edits require no Docs/Search generation. New route behavior belongs in a focused browser/domain owner before it is wired through the shell or HTTP adapter. Keep canonical source, live editor projections, refreshed reader data and published output distinct when extending the app.
