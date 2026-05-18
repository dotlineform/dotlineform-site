---
doc_id: site-request-docs-markdown-package-import
title: Docs Markdown Package Import Request
added_date: 2026-05-17
last_updated: 2026-05-17
parent_id: change-requests
sort_order: 47000
---
# Docs Markdown Package Import Request

Status:

- proposed

## Summary

Add a Docs Import path for folder-based Markdown packages, with Apple Notes Markdown exports as the primary case.

Apple Notes can export a note as a folder containing:

- one Markdown file
- one or more image files in a subfolder
- relative Markdown image links pointing at those files
- unreadable generated image filenames

The importer should stage the whole exported folder, import the Markdown as a normal Docs Viewer source doc, rename package images to readable docs-media filenames, and rewrite image links to the existing Docs Viewer media-token format.

## Problem

The current Docs Import workflow is built around one staged file at a time.
That works for HTML, Markdown, text, SVG, standalone images, and downloadable files, but it does not preserve the relationship between an exported Markdown file and its companion image folder.

Apple Notes Markdown exports are otherwise a good source format:

- the prose is already Markdown
- headings and lists survive better than in PDF extraction
- images are real files rather than embedded base64
- relative links identify where each image belongs in the document

The friction is the package shape.
The current staged-file listing scans only top-level files under `var/docs/import-staging/`, while the Notes export needs a staged directory boundary with internal relative paths.

## Product Goal

Make Apple Notes Markdown export the preferred import route when available.

The desired user workflow:

1. Export a note from Apple Notes as Markdown.
2. Copy the whole exported folder under `var/docs/import-staging/`.
3. Open the Docs Viewer import modal.
4. Select the staged package.
5. Choose the docs scope.
6. Import the package.
7. Receive a normal Docs Viewer Markdown source doc plus a media handoff list for renamed images.
8. Copy and convert the staged/renamed media files to the configured media store when required by the scope storage mode. Images need to be converted to webp, sized to maximum 800px wide (if bigger).

## Proposed Behavior

For a staged package such as:

```text
var/docs/import-staging/my-note/
   My Note.md
   images/
      E142C224-F4A4-4889-8835-CE21B6F163D4.png
      F1E9F92E-538C-4C7D-8B90-E67265B646FF.jpeg
   attachments/
      D6199E27-07B2-4045-B09B-2EF5E64920DC.pdf
```

And Markdown such as:

```md
# My Note

Some text.


![F1E9F92E-538C-4C7D-8B90-E67265B646FF](images/F1E9F92E-538C-4C7D-8B90-E67265B646FF.jpg)
 <span style="font-size: 11.285714;">
     3 symbols
 </span>
 <span style="font-size: 11.285714;text-align: left;">
```

Note that the exported markdown may include a \<span> for the image caption. When this present, it will need converting to use the site's main.css font size --font-caption token.

The importer should create source Markdown like:

<pre><code># My Note

Some text.

![Diagram](&#91;&#91;media:docs/library/img/my-note-image-01.png&#93;&#93;)</code></pre>

And report media plans such as:

<pre><code>{
  "source_path": "my-note-image-01.png",
  "source_original_path": "my-note/Attachments/90C4730D6D1445B9B2776E2F9F7E3A1D.png",
  "media_path": "docs/library/img/my-note-image-01.png",
  "media_token": "&#91;&#91;media:docs/library/img/my-note-image-01.png&#93;&#93;",
  "title": "Diagram"
}</code></pre>

## Scope

Included:

- staged directory packages under `var/docs/import-staging/`
- package detection and listing in the Docs Import modal
- one Markdown source file per package
- relative Markdown image / attachment link resolution
- image copy or materialization into the import staging area using readable generated filenames
- link rewriting from package-relative paths to docs media tokens or public repo-asset paths
- existing create, overwrite, collision, backup, rebuild, and search rebuild behavior
- clear warnings for unresolved links, unsupported image types, duplicate targets, or ambiguous package structure

Excluded:

- arbitrary filesystem browsing outside the repo staging directory
- importing multiple Markdown files from one package in v1
- preserving Apple Notes attachment filenames
- uploading media automatically to external locations
- OCR
- PDF content extraction in this request
- table or rich-layout reconstruction beyond what the exported Markdown already contains

## Package Rules

Initial package recognition:

- a package is a direct child directory of `var/docs/import-staging/`
- the package must contain exactly one primary `.md` or `.markdown` file, or the importer must return an ambiguity warning
- image and attachment links are resolved relative to the Markdown file's directory
- resolved image/attachment paths must remain inside the package directory

Supported image extensions should match existing Docs Import raster image support:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`
- `.gif`

## Filename Rules

Generated image filenames should follow the existing readable inline-media convention:

- base name: proposed doc id
- suffix: `image-NN`
- extension: normalized from the original image extension

Examples:

- `my-note-image-01.png`
- `my-note-image-02.jpg`

If a generated filename already exists in `var/docs/import-staging/`, the importer should use the next available increment.
The importer should not use opaque hashes for v1 unless a later collision case proves they are needed.

## Implementation Steps

1. Add a package source format.
   Extend the Docs Import source registry so it can represent directory-backed import sources, not only files. Return package records from `GET /docs/import-source-files` with a distinct source format such as `markdown_package`.

2. Add safe package resolution.
   Create a resolver that accepts a staged package name, resolves it under `var/docs/import-staging/`, rejects path traversal, rejects symlink escapes, and confirms the package directory exists.

3. Detect the primary Markdown file.
   Find the package's primary Markdown file. For v1, require exactly one Markdown file unless a clear Apple Notes naming rule is available. Return a blocking warning when the package has none or more than one.

4. Parse Markdown image references.
   Reuse the existing Markdown image-link pattern where practical, but resolve only local relative image targets. Leave external URLs unchanged. Treat data URLs through the existing inline raster extraction path.

5. Plan package media.
   For each resolved package image, generate a readable filename, build a normal docs image media plan, and record the original package-relative source path for reporting.

6. Rewrite Markdown links.
   Replace each resolved local image target with the generated docs media link. Preserve alt text. Keep unresolved or unsupported links in place and add warnings.

7. Materialize images during write.
   During create or overwrite, copy each package image to the planned staging filename for `staging_manual`, or to the configured repo asset path for `repo_assets`, using the same allowlist and collision checks as existing media materialization.

8. Integrate with create and overwrite flow.
   Keep target scope validation, source doc front matter, collision handling, replacement id handling, backups, source writes, docs rebuilds, and search rebuilds in the existing import source service.

9. Update the Docs Import modal.
   Show package records alongside files, label them clearly as Markdown packages, and keep the prompt/meta toggle hidden because it is HTML-only.

10. Add focused tests.
    Cover package listing, safe path rejection, primary Markdown detection, image renaming, link rewriting, unresolved-image warnings, create writes, overwrite writes, collision replacement, and storage-mode behavior.

11. Update stable docs after implementation.
    Once implemented, update the Docs Viewer media handling and import source registry docs with the final package contract.

## UI Requirements

The import modal should:

- list Markdown packages with a clear source-format label
- allow selecting one package or all staged import sources if the current bulk flow still applies cleanly
- show warnings for ambiguous packages before writing
- render every generated media plan in the result panel
- include original package-relative image paths in result details or warnings when useful
- keep the existing source-doc link result behavior

## Benefits

This change should:

- make Apple Notes Markdown export the preferred Docs Viewer ingestion path
- preserve more document structure than PDF extraction
- replace unreadable Apple-generated image filenames with stable docs-media names
- reuse the existing media-token and manual-copy workflow
- keep imported source Markdown editable and reviewable

## Risks

Main risks:

- supporting directories weakens the current simple flat-staging boundary unless path checks are strict
- Apple Notes export shapes may vary by macOS version or note content
- Markdown image parsing can miss edge cases such as reference-style links or URLs with unusual escaping
- copying package images during write can leave unused staged files if an import is abandoned after preview
- bulk import behavior may need limits if a staging folder contains many package directories

The first implementation should prefer a narrow package contract with explicit warnings rather than trying to parse every Markdown variant.

## Future: PDF Import Fallback

PDF import should be a separate future request.

It is still useful when the PDF is all that exists, or for similar non-Apple-Notes PDFs, but it should be treated as best-effort extraction rather than equivalent source import.

A future PDF importer could:

- use a dedicated PDF dependency such as PyMuPDF
- extract selectable text page by page
- extract embedded raster images
- generate readable image filenames using the same `<doc_id>-image-NN` convention
- produce a normal Markdown doc with warnings about reading order, sparse text, scanned pages, and layout loss
- keep OCR, table reconstruction, and high-fidelity page layout out of v1

Markdown package import should come first because it preserves source structure and fits the existing Docs Import media model with less ambiguity.
