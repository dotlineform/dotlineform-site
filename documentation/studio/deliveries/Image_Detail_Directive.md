---
draft: false
doc_id: d-20261018-191000-ae6351
title: Image Detail Directive
added_date: "2026-10-18 19:10:00"
last_updated: "2026-10-18"
summary: Reuse the SVG Content Detail panel for directive-selected document images.
parent_id: d-20260428-000000-f5ff18
---
# Image Detail Directive

## Current And Next State

Implemented and reviewed on 2026-10-18; awaiting normal-use confirmation of optional SVG behavior. Source **Image detail** inserts the agreed comment directive. One shared image-detail adapter handles directive-selected SVG and raster images through the existing Content Detail panel, with its button above the image. Automatic SVG overlays are removed. Back/title/Open are centered in the top row, while Manage Actions and the theme control stay on the right. Changed-owner lint, Python syntax, whitespace, tracked projection and site validation passed. Next: force reload Public/Manage and confirm SVGs with and without the directive, opening, Back and new-tab behavior. Existing generated payloads remain usable without reconciliation; normal Source Save includes a newly authored directive. Retain this delivery for acceptance/evidence lookup pending manual archive.

## Requirements And Deliverables

- `<!-- dotlineform:image-detail -->` adds one small Open image control above the immediately following standalone Markdown image or Docs-owned image token, allowing blank lines. Prose/other intervening blocks do not acquire a control or cause a later image to be selected.
- Reuse the SVG panel, Back, Open in new tab and the existing image element; derive the displayed title from alt text. SVG and raster images both require the directive; neither receives an automatic overlay. Preserve Public/Manage ownership.
- Keep selection and view state in the browser using the rendered comment/image and supplied document target. Python has no new persistence, parsing, processing or transfer work. Do not add a new endpoint, renderer, panel, image variants or fallback original.
- Generalize the demonstrated shared image/SVG responsibility, remove the former SVG-only module path without an alias, update its explicit public inventory and document the durable owner.

## Process

Insert Image detail from Source Directives immediately before an existing image and Save. Open image enters the current document's Content Detail presentation; Back restores it, and Open in new tab uses the captured file URL. Public authored changes use ordinary Publish; runtime/style deployment uses the tracked projection.

## Delivery Steps

- [x] Readiness: existing SVG detail already moves an ordinary image into the shared host. The rendered document contains the comment and image needed for browser-owned selection; no server work is needed. User content and unrelated generated output remain outside implementation writes.
- [x] Implementation: Source insertion, directive association, above-image control, generic image adapter/host wiring, explicit current collection identity and public manifest rename are implemented. The old mount-generation alternate input and silent missing-request callback were removed from the reused adapter; its sole document-controller composer supplies both dependencies directly. The approved follow-up removes automatic SVG selection, SVG-only control/label/layout branches, unused data attributes and the generated SVG marker from both Markdown-media and semantic-image renderers. The renderer's unused `svg` argument is removed with its sole production call site; no alias or automatic source migration is introduced.
- [x] Verification: changed-owner JavaScript/Python lint, Python syntax, whitespace, explicit projection, projection check and site validation passed. These address syntax, import/wiring and public-asset defects at seconds-scale cost; effects are tool caches and tracked runtime/style projection only. No tests, fixtures or browser scripts were created, changed or run. The existing `test_persistent_diagram_detail_is_shared_by_public_and_manage_but_not_review` selector in `docs-viewer/tests/python/test_docs_viewer_public_runtime_boundaries.py` still names the retired SVG-only module and imports a retired customisation module. `test_python_docs_builder_writes_docs_payloads_and_semantic_token_usage` in `docs-viewer/tests/python/test_build_docs_payloads.py` asserts the retired automatic-SVG marker and older scope-bearing output. Both are unreviewed and left unchanged under the separate test-work policy.
- [x] Code review: traced literal/unmatched directives, standalone-image/figure selection, SVG/raster association, DOM movement/restoration, current collection identity, release and public/local ownership. The bounded Redundancy And Defensive Behavior Review confirmed that the existing HTML mount retains comment nodes while resolving image URLs, so no server parser, second rendering pass, source read or new request is needed. Review corrected the figure wrapper's fill-width/natural-width, right-column and public narrow-screen participation; it also removed unused light/dark SVG URL attributes from the reused HTML mount owner, which had no active producer. The optional-SVG follow-up reuses the directive's selected-image set directly, removing the complete image scan, SVG role lookup for Markdown decoration, automatic-marker producers and overlay CSS. The media-role helper remains for actual semantic image-owner validation. The old module path, SVG-only adapter names, alternate mount-generation input and silent missing-request callback have no compatibility aliases. Retained safeguards are literal-container exclusion and exact next-block shape checks, which define the directive's scope, plus current document/collection/mount and active-presentation guards, which prevent stale controls from moving another image. Existing loaded source/alt text and completed image URLs are reused without file checks, audits, repair or recovery work. No new raw HTML or dynamic markup is accepted; the control icon is fixed and labels use text/attribute APIs.
- [x] Closeout: durable syntax, scope, ownership, layout and lifecycle live in Document Image Detail, with Source menu/Runtime/diagram links updated. Implementation and required projection are complete; visual/interaction and live Save confirmation remain manual. Keep this delivery for acceptance/evidence lookup and recommend manual archive after acceptance; no delivery document is deleted.

## Verification Record

- Maintained JavaScript lint passed for the ten changed owners: shared `docs-viewer-image-detail.js`, `docs-viewer-content-detail-view.js`, `docs-viewer-document-controller.js`, `docs-viewer-app-boot.js`, `docs-viewer-app-runtime.js`, `docs-viewer-table-detail.js`, `docs-viewer-asset-url.js`; Public `docs-viewer-public.js`; Manage `docs-viewer-manage.js`; and Source `source-editor/directive-actions.js`. The project Miniconda Python invoked `tooling/lint/run_lint.py --language javascript --paths ...`. Only the subsequently changed image and asset helpers were relinted after their review changes.
- The optional-SVG follow-up passed JavaScript lint for `docs-viewer-image-detail.js`, Python lint and `py_compile` for `docs_builder/rendering.py` and `docs_builder/semantic_tokens.py`. Active runtime/build/service reference inspection found no remaining automatic-SVG marker, kind or explicit-versus-overlay class consumers/producers. Old generated HTML may retain an unused marker; the reader does not inspect it, so no complete document rebuild is required. `git diff --check` passed.
- `bin/site-code-update` projected the module rename, seven changed JavaScript files and the shared CSS: one new module, eight changed files and one retired module in total. The tracked delta was inspected. `bin/site-code-update --check` reports all 104 projected files current; `bin/site-validate` passes with 60 required files, 7 required directories, 104 projected files, 71 runtime modules and the maintained public route.
- The optional-SVG follow-up projected only the image adapter and shared CSS; both projected changes were inspected. Projection check and site validation passed again with the same maintained inventory. No source documents or generated document payloads were changed for this follow-up.
- No tests, browser automation, live source/media writes, document generation, Search rebuild, Publish, commit, push or deployment ran. Source insertion and the actual control/Back/new-tab/focus/caption behaviors remain normal-use confirmation; static evidence does not establish them.

## Follow-On

Linked-image directives, arbitrary HTML wrappers, zoom/pan controls, higher-resolution source recovery and test migration/expansion require their own scope. Durable syntax, ownership and extension behavior live in [Document Image Detail](../Document_Image_Detail.md).
