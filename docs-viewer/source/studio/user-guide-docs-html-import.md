---
doc_id: user-guide-docs-html-import
title: Docs Import
added_date: 2026-04-24
last_updated: 2026-07-14
summary: Stage source material, review the import decisions, and write it into a configured Docs Viewer scope.
parent_id: docs-viewer
viewable: true
---
# Docs Import

Docs Import turns staged source material into canonical Markdown documents and associated media. It runs inside Docs Viewer management; there is no separate import route.

Open the target `/docs/?scope=<scope>` page and choose the Import toolbar action or `Actions` > `Import`.

## Workflow

```text
stage source
    |
    v
open Import -> choose target scope and source
    |
    +-- Files ----------------> convert and validate
    |                              |
    |                              +-- collision? -> rename or replace
    |                              v
    |                         write + rebuild -> result
    |
    +-- Data Sharing package -> plan whole collection
                                   |
                                   +-- blockers? -> stop and correct package
                                   +-- decisions? -> overwrite or skip
                                   v
                              confirm -> re-plan -> ordered apply -> result report
```

The browser presents choices. The local Docs Viewer service resolves staged paths, validates targets, creates the authoritative plan, performs writes, and rebuilds generated docs.

## Stage The Source

Put source material in the shared drop-zone:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/
```

Ordinary files must be direct children. A Markdown package is a direct-child folder containing one Markdown file plus its local images or attachments. The picker shows only formats the server currently accepts; [Docs Import Architecture](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec) points to the code-owned format registry.

Do not add Docs Viewer front matter to staged Markdown. Import creates the target document front matter and treats the staged Markdown as its body.

## Import Files

Use `Files` for HTML, Markdown, text, SVG, images, downloadable files, and Markdown packages.

1. Select one or more staged sources.
2. Choose the target scope.
3. For HTML, decide whether obvious prompt/meta sections belong in the document.
4. Choose `Import selected`.
5. Resolve any filename collision when prompted.
6. Inspect the result and open the imported document.

Multi-file runs process the selected files in list order. A failure stops the run; successfully completed earlier imports remain. Docs Viewer refreshes the target index once and selects the final successful document.

The staged filename normally supplies the new `doc_id` and Markdown filename. HTML can supply its title; Markdown uses its first H1 when present; other formats use the best available source title or a humanized filename.

New documents in public scopes are created non-viewable so they can be checked in management mode before publication.

### Filename Collisions

When the proposed Markdown filename already exists, nothing is written until you choose:

- enter another `doc_id` to create a different document
- choose `Replace` to overwrite the colliding canonical source
- cancel that file

Replacing preserves the existing document identity and parent while replacing its body with the imported content. Recover unwanted overwrites through Git or filesystem backups; Docs Import does not create a separate backup bundle.

## Import A Reviewed Collection

Use `Data Sharing packages` for a trusted returned documents package. Docs Review can open the modal with its matching staged package selected, but the handoff contains only the package identity; Docs Import resolves the actual staged source again.

The collection path is deliberately plan-first:

1. Choose the package and target scope.
2. Review every record, parent resolution, warning, and blocker.
3. For collisions, choose `Overwrite`, `Skip`, or `Cancel`. `Apply to all` affects only the remaining document collisions.
4. For invalid records, choose `Skip` or `Cancel`; a skip may include a note.
5. Review the complete resolved plan and confirm apply.

The plan covers the whole collection. There is no ordinary subset selection, automatic overwrite, replacement `doc_id`, or `Create as new` path. Missing undeclared parents, hierarchy cycles, unsafe identities, and package-shape errors block confirmation.

On confirmation the service rereads the staged package and recomputes the target plan. If package identity, collisions, hierarchy, or blockers changed, it returns the refreshed plan without writing. Otherwise it applies records in package order and rebuilds once.

Collection apply is synchronous, not transactional. A source-write failure preserves earlier writes and reports later records as not attempted. Generation failure is reported separately and does not undo successful source changes.

## Media And Companion Assets

Media behavior comes from the target scope configuration:

- public scopes can publish record-owned media to R2 before committing the source
- repo-backed scopes copy media into their configured repo assets
- external-local scopes copy media into their external media root
- `staging_manual` leaves an explicit copy instruction in the result

Markdown packages convert supported images to readable, 800px-maximum WebP outputs and copy supported attachments unchanged. HTML and Markdown can also extract inline raster data URLs. Exact paths, storage modes, collision rules, and media limitations belong to [Media Handling](/docs/?scope=studio&doc=docs-viewer-media-handling).

A standalone HTML file marked with:

```html
<meta name="dlf:docs-import-role" content="interactive-html">
```

is treated as a companion asset rather than a selectable source. A normal file import copies marked companions into the target scope's interactive-assets folder after any required overwrite confirmation. Add the resulting `interactive-html` token to the document manually; import does not decide where the iframe belongs.

## Results And Recovery

An ordinary result identifies the created or overwritten document, target scope, viewer link, media actions, and conversion warnings. A collection result groups created, overwritten, skipped, failed, and not-attempted records and writes a Markdown report under `import-staging/results/`.

The terminal result remains in the modal until `Close`. Reopen the modal to refresh the staged-source list and start another run.

Docs Import is best-effort conversion. Normal prose, headings, lists, links, simple tables, Markdown, and supported media are reliable inputs. Presentation-heavy HTML, interactive UI, unresolved package links, and unsupported assets may need source editing after import. The generated Markdown is always checked by the shared Python renderer before a source write.

For implementation boundaries, extension methods, and known structural weak spots, see [Docs Import Architecture](/docs/?scope=studio&doc=docs-viewer-import-source-registry-spec).
