---
draft: false
doc_id: d-20260607-222033-dd2265
title: Rebuild Follow-Through Scripts
added_date: "2026-06-07 22:20:33"
last_updated: "2026-10-08 19:10:43"
parent_id: d-20260607-222033-2a494e
---
# Docs Viewer Rebuild Follow-Through Scripts

`docs-viewer/services/docs_document_rebuild.py` resolves one exact Working document and requires authoring capability before calling the shared document/Links rebuild owner. Source Save and Draft reuse its resolved-target helper without a second source-resolution pass. Ordinary targets use `rebuild_working_outputs` with one ID, Search excluded and media skipped; named targets use `rebuild_collection_outputs` with the same exact document and Links selection.

`docs-viewer/services/docs_write_rebuild.py` owns awaited builder command shapes, source-write follow-through, existing mutation-specific recovery and diagnostics. Normal writes rebuild required document/Links outputs without Search or media production. Multi-collection relocation writes once and builds the destination before the former owner processes its Links deletion. The filesystem watcher, suppression markers and suppression-only arguments are retired.

The explicit **Rebuild docs and Search** action calls the same orchestration owner with a complete Working request. It builds the ordinary owner and every configured collection, regenerates referenced registered media through their producer owners, updates Recents and aggregate Links, builds Search, and records completion after required outputs succeed. [Source Organisation](Source_Organisation.md#explicit-external-edit-and-media-rebuilds) owns the agreed rare persistent-media workflow and its broader writes/cost.

`docs-viewer/build/build_docs.py` owns document rendering, management/tree metadata and document relationships. Exact selectors preserve unselected payloads and saved discovery outputs; missing targeted prerequisites request an explicit complete Build. `--skip-media-builds` prevents registered media inventory and producer work. `--diagnostics` adds machine-readable details to the normal compact console summary. [Builder](Builder.md) owns these contracts.

`docs-viewer/build/build_search.py` independently produces the complete stage-independent `docs_viewer_search_index_v4` Working index. Source Save and other normal authoring writes leave Search unchanged. Publish copies its existing bytes; it does not rebuild Search. Browser display/navigation remains owned by [Runtime](Docs_Viewer_Runtime.md), and source candidate validation remains owned by [Source Editor Endpoints](Source_Editor_Endpoints.md).
