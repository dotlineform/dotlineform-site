---
doc_id: docs-viewer-import-source-registry-spec
title: Import Source Registry Spec
added_date: 2026-05-14
last_updated: 2026-07-11
parent_id: docs-viewer
viewable: true
---
# Docs Viewer Import Source Registry Spec

The Docs Viewer import source registry is the server-side format contract for staged source files imported through Docs Viewer management mode.

The registry currently lives in `docs-viewer/services/docs_html_import.py`.
The service boundary that turns previews into source writes lives in `docs-viewer/services/docs_import_source_service.py` and is exposed through the standalone Docs Viewer service.

## Goals

The registry must:

- list every staged source format accepted from `var/docs/import-staging/`
- map file extensions to a stable `source_format`
- expose `source_format` in staged-file listings and preview/write responses
- keep media-producing formats explicit
- keep HTML prompt/meta handling explicit
- send every format through one preview contract before write
- keep create, collision, overwrite, source-write, and rebuild behavior outside individual format converters

The registry is intentionally small.
It describes supported formats and dispatch metadata; it is not a plugin loader or an open-ended import execution surface.

## Planned External Staging Root

[Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package) will move every registered Docs Import format from `var/docs/import-staging/` to the existing shared user drop-zone:

```text
$DOTLINEFORM_PROJECTS_BASE_DIR/data-sharing/import-staging/
```

Docs Import will reuse the W0 adapter already consumed by Docs Review: `configured_workspace_paths(repo_root).import_staging` from `data-sharing/services/paths.py`. Listing, source resolution, direct-child Markdown packages, interactive companions, and `staging_manual` media materialization must all use that resolved root. Responses use `marker_path()` rather than absolute paths.

The folder is application-neutral staging despite its existing `data-sharing/` namespace. Which workflow consumes a file depends on supported format/schema and the user action. There will be no Docs-specific external resolver and no fallback or compatibility reads from `var/docs/import-staging/`.

## Planned Data Sharing Collection Source

[Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package) adds supported Data Sharing documents JSON/JSONL as a collection source format.

The current registry treats `.json` and `.jsonl` as generic downloadable files and imports one primary source at a time. The planned implementation will detect supported Data Sharing headers and trusted export metadata before that generic fallback, parse the immutable staged file into normalized document records, and apply it as a collection.

The same JSONL parser/normalizer will feed both the persistent read-only Docs Review projection and Docs Import. Import reads the staged JSONL, never `import-preview/<package_id>/source/*.md`. Shared lower-level services continue to own renderer validation, data-URL image extraction, collision handling, source formatting, writes, and rebuilds.

Each selected record can create, explicitly overwrite, or skip. A collision must require a user choice rather than silently selecting an action.

## Registry Shape

The registry is represented by `SourceImporter` records:

```python
@dataclass(frozen=True)
class SourceImporter:
    source_format: str
    suffixes: set[str]
    include_prompt_meta: bool = False
    creates_remote_media_plan: bool = False
```

Current registry entries:

| `source_format` | Extensions | Prompt/meta option | Media plan |
| --- | --- | --- | --- |
| `html` | `.html`, `.htm` | yes | inline raster extraction can emit `media_plans` |
| `markdown` | `.md`, `.markdown` | no | inline raster extraction can emit `media_plans` |
| `markdown_package` | direct child directories containing one Markdown file | no | package images and attachments emit `media_plans` |
| `text` | `.txt` | no | no |
| `svg` | `.svg` | no | no |
| `image` | `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif` | no | singular `media_plan` |
| `file` | `.pdf`, `.zip`, `.csv`, `.tsv`, `.json`, `.jsonl`, `.docx`, `.xlsx`, `.pptx` | no | singular `media_plan` |

`SOURCE_IMPORTER_BY_SUFFIX` is derived from this registry and is the canonical suffix lookup.
`SUPPORTED_STAGED_SUFFIXES` is the union used by staging resolution and staged-file listing.

## Staging Contract

All managed imports read from:

- `var/docs/import-staging/`

`resolve_staged_import_source()` requires the staged filename to resolve inside that directory and to use a supported suffix, unless the source is a supported Markdown package directory.
Markdown package directories must be direct children of the staging folder.
Nested paths, path traversal, unsupported extensions, and package directory escapes are rejected before conversion.

`list_staged_import_source_files()` returns only supported files and includes:

- `filename`
- `path`
- `source_format`
- `size_bytes`
- `modified_utc`

Markdown package records also include:

- `package_file_count`
- `package_markdown_count`

The local management service exposes that list through `GET /docs/import-source-files`.
`GET /docs/import-html-files` remains a compatibility alias.

## Preview Dispatch

`generate_import_preview()` resolves the `source_format` and delegates to the format-specific preview builder.

The current dispatch functions are:

- `generate_html_import_preview()`
- `generate_markdown_import_preview()`
- `generate_markdown_package_import_preview()`
- `generate_text_import_preview()`
- `generate_svg_import_preview()`
- `generate_image_import_preview()`
- `generate_file_media_import_preview()`

Every preview is validated through `validate_markdown_preview()` before it is returned as successful.
That helper renders generated preview Markdown through the shared Python Markdown renderer and records the explicit import sanitizer boundary.
Preview generation does not write source docs.
For inline raster data URLs, preview generation plans media output but write-time materialization is handled later by the service.

## Shared Preview Contract

Every format returns a preview dictionary with the same core fields:

- `scope`
- `source_format`
- `source_path`
- `staging_root`
- `title`
- `title_source`
- `proposed_doc_id`
- `proposed_doc_id_source`
- `source_stats`
- `image_summary`
- `warnings`
- `markdown_preview`
- `tag_counts`
- `comment_count`
- `markdown_validation`

Optional fields are format-specific:

- `source_html` for HTML imports
- `source_markdown` for Markdown imports
- `package_path` and `package_markdown_path` for Markdown package imports
- `source_text` for text imports
- `source_svg` for standalone SVG imports
- `source_media` for image and file-media imports
- `media_plan` for standalone image and file-media wrappers
- `media_plans` for extracted inline raster images and Markdown package media

The service adds collision and write-flow fields after loading the target scope:

- `doc_id_collision`
- `replacement_doc_id_required`
- `replacement_title_required`

## Format Behavior

HTML imports parse the source with Beautiful Soup, convert supported structures to Markdown, optionally keep identifiable prompt/meta blocks, preserve safe inline SVG, and extract Markdown-image-form inline raster data URLs into planned media files.

Markdown imports treat the staged file as body Markdown without front matter.
The first `# H1` becomes the title when present; otherwise the title is derived from the filename.
Inline raster data URLs are planned the same way as HTML imports.

Markdown package imports treat a direct child directory of `var/docs/import-staging/` as one source when it contains exactly one Markdown file.
Local Markdown image links are resolved inside the package, renamed to readable `<doc_id>-image-NN.webp` outputs, rewritten to docs media links, and converted to WebP at write time with a maximum width of 800px.
The rewritten Markdown image alt text and title use readable `<doc_id> image NN` text instead of opaque exported filenames.
Local Markdown links to supported downloadable files are treated as attachments, renamed to `<doc_id>-attachment-NN.<ext>`, rewritten to docs media links, and copied unchanged at write time.
External links, anchors, mail links, unresolved package links, and unsupported package media stay in place with warnings where useful.

Text imports treat `.txt` content as prose, derive the title from a short first non-empty line when available, and convert plain `http://` and `https://` URLs to Markdown autolinks.

SVG imports sanitize a standalone `<svg>` with the same SVG serialization and safety rules used for HTML inline SVG.
The wrapper Markdown body contains a heading and the sanitized SVG block.

Image imports create a wrapper Markdown document with one image reference.
File-media imports create a wrapper Markdown document with one download link.
They do not parse or transform the media file contents.

## Media Planning

Image and file-media imports use `build_media_plan()` to describe the expected target media location and rendered link.

For the current site config, `staging_manual` mode writes media tokens:

<pre><code>![Example](&#91;&#91;media:docs/library/img/example.png&#93;&#93;)
[Download Example](&#91;&#91;media:docs/library/files/example.pdf&#93;&#93;)</code></pre>

The preview reports:

- `storage_mode`
- `manual_copy_required`
- `source_path`
- `media_path`
- `media_token`
- `media_link`
- `title`
- `repo_asset_path`
- `public_path`

When `storage_mode` is `staging_manual`, source media files are not copied by the importer.
The user copies them to the reported media store path after import.

When `storage_mode` is `repo_assets`, write-time media handling may copy source media or decoded inline media into the configured repo asset prefix after path allowlist checks.
`r2_upload` is reserved in config but is not operational.

## Inline Raster Extraction

HTML and Markdown imports can extract images that appear as Markdown image data URLs:

```md
![Alt](data:image/png;base64,...)
```

Supported inline raster subtypes are PNG, JPEG, WebP, and GIF.
Preview replaces each data URL with a configured media link and records a `media_plans` array.
Generated filenames use the final proposed `doc_id` plus an incrementing suffix:

- `<doc_id>-image-01.png`
- `<doc_id>-image-02.jpg`

Write-time materialization is performed by `materialize_inline_raster_media()`.
If a collision replacement changes the final doc id, `retarget_inline_raster_media_plans()` updates the generated filenames and media tokens before write.

## Collision And Write Boundary

Format preview builders do not create, overwrite, back up, or rebuild docs.
Those responsibilities belong to `handle_import_source()`.

The service:

- loads docs for the selected scope
- detects collisions against existing `doc_id` values and Markdown filename stems
- requires a replacement doc id or explicit overwrite confirmation when the proposed target collides
- creates new source docs with standard Docs Viewer front matter
- preserves existing identity, parent, order, and visibility metadata on overwrite
- materializes inline raster media during create or overwrite
- writes the source Markdown atomically
- rebuilds same-scope docs payloads and targeted docs-search entries after successful writes
- relies on Git history, host/filesystem backups, or explicit manual copies for source recovery

The normal UI collision recovery path uses `replacement_doc_id`.
`replacement_title` remains as a compatibility fallback for older callers.

## Security Rules

The registry and service enforce narrow inputs before conversion:

- staged source filenames must stay under `var/docs/import-staging/`
- supported extensions come from the registry
- media filenames must remain plain filenames when copied or materialized
- repo asset writes must stay under the configured repo asset prefix
- generated Markdown must pass the Python renderer validation used by Docs Viewer payload generation

SVG safety is shared by HTML inline SVG and standalone SVG imports:

- `<script>` content is stripped
- `on*` event-handler attributes are stripped
- external SVG references are reported as warnings
- safe SVG `<title>` and `<desc>` content can be preserved

## Adding A Format

To add a new source format:

1. Add a `SourceImporter` entry with a unique `source_format` and suffix set.
2. Add a preview builder that returns the shared preview contract.
3. Add dispatch in `generate_import_preview()`.
4. Decide whether the format uses `media_plan`, `media_plans`, or neither.
5. Add tests for staged-file listing, preview, collision behavior, and write behavior when applicable.
6. Update [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import) and [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server).

New formats should not write files directly from preview builders.
Keep writes in the service layer so source-write, rebuild, and search behavior remain consistent across formats.

## Related References

- [Docs Viewer](/docs/?scope=studio&doc=docs-viewer)
- [Docs Import](/docs/?scope=studio&doc=user-guide-docs-html-import)
- [Docs Management Service](/docs/?scope=studio&doc=scripts-docs-management-server)
- [Docs Viewer Config](/docs/?scope=studio&doc=config-docs-viewer)
- [Docs Import Reviewed Package](/docs/?scope=studio&doc=site-request-docs-import-reviewed-package)
