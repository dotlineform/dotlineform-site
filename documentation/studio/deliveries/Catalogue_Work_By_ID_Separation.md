---
draft: false
doc_id: d-20261109-103636-3a356c
title: Catalogue Work By-ID Separation
added_date: "2026-11-09 10:36:36"
last_updated: "2026-11-09"
summary: Adopt Studio Work records at Catalogue Regenerate and serve document rendering, Media View, Publish and Export from adopted Catalogue documents.
ui_status: proposed
parent_id: d-20260428-000000-f5ff18
---
# Catalogue Work By-ID Separation

## Current And Next State

Status is proposed. Working currently resolves Work presentation from live Studio-generated records. Public documents embed a full presentation for every distinct Work they reference. Public Media View already loads the selected Work’s Catalogue document for Gallery member navigation, and both readers load Gallery membership separately. Publish, Export and content-bearing Prepare Package still prepare presentations from the raw Working Work records. Publish also copies raw Work records to Preview and the public repository.

This delivery takes over the Work adoption, document reader and downstream preparation changes currently grouped into GO.2 of [Docs Viewer Gallery Ownership](Docs_Viewer_Gallery_Ownership.md). The first step is to confirm the payload boundary, existing Gallery handoff and cutover selection against the current owners. [Planned Features](../Planned_Features.md) is the parent. [Development Workflow](../Development_Workflow.md) and [Development Checklist](../Development_Checklist.md) govern implementation and review.

## Regenerate Owns Work Adoption

Studio Save and Refresh continue to prepare media and generate `working/generated/catalogue/works/index/<work_id>.json`. Within Docs Viewer, Catalogue Regenerate is the sole reader of those raw Work records. It consumes the completed Studio selection, adopts the selected Work facts and resource identities into Working Catalogue `documents/by-id/<work_id>.json`, applies exact deletions and completes the existing publication handoff. The last successful Regenerate defines the Work facts available to Docs Viewer. Ordinary Build preserves adopted facts. Missing adopted input is reported at the operation that needs it.

The Work’s Catalogue document is the canonical Docs Viewer read model. It supplies the page’s Entry and the full Work Media View presentation, including responsive image data, the full-image target and direct and Series-related Gallery IDs and labels. Keep those Gallery references distinct from the adopted Work facts so the later Gallery owner can update them independently. During this delivery Studio still owns Gallery production. Confirm how the existing Refresh selections carry all affected Work projections through the handoff, including a Gallery rename, membership change or Series association change with unchanged Work facts. Use the existing completion boundaries and exact affected selections.

## Document Rendering And Media View

- **Referring document.** Its own by-ID JSON carries the data needed to render it. An inline Work image carries portable rendition references, dimensions, alt text and any rendered caption. A Work or Gallery text link carries the authored label and exact target. Retain the typed references needed by the existing build and preparation workflows. The document carries no copy of the full Work Media View presentation or the Work’s Gallery links. Working and public can render a prepared referring document without fetching its referenced Works on page load.
- **Work selection.** Opening Media View from an image or Work text link resolves the exact Catalogue document for that Work ID. Reuse the payload when it is already loaded, including when the opener is on the Work’s own Catalogue page. Selecting a Gallery member or using Previous/Next uses the same Work-document read. On a cold first click from a referring document this adds one Work-document request and removes the need to carry every referenced Work’s full presentation on the page.
- **Gallery selection.** Opening a Gallery from a document or from a Work loads `galleries/index/<gallery_id>.json` and uses the existing thumbnail policy. The Gallery record supplies member IDs and titles. The grid, pagination and neighbour controls use the loaded member list, and only selected Works need full presentations. Preserve direct versus Series-related links, Gallery browsing context and Back to document.

Build and selected preparation project the visible fields of referring documents from adopted Work data using the existing selection rules. A Work update alone does not rebuild or requeue its referrers. A referring document’s inline render data follows its own build and publication lifecycle, while Media View uses the selected Work’s available Catalogue document in Working or public. A deleted Work leaves existing authored references for Broken Links and author resolution. [Catalogue Media View](../Catalogue_Media_View.md) and [Generated Data Contracts](../Generated_Data_Contracts.md#catalogue-reference-and-presentation) own the current reader contracts.

### Portable Catalogue Media References

Preparation selects the exact responsive renditions from the shared media policy and records the candidate list in document JSON. Each candidate carries its portable asset identity and width descriptor. The image data also carries its version for cache invalidation, intrinsic dimensions, and the selected default and full-image targets where used. Working, Preview and public carry the same portable references. A policy change takes effect in a document when its candidates are prepared again.

The shared browser reader resolves each prepared reference against the configured Catalogue asset base URL. It builds `src` and `srcset` from the supplied candidates, sets `sizes` for the rendered layout, and resolves full-image and owned download targets from their portable identities. Authored external links keep their supplied URLs. This follows the established [portable Docs media contract](../Catalogue_Work_Document_Links.md#cwid-3--portable-document-and-media-references). Confirm the Catalogue identity syntax and configuration wiring at readiness, with the roots available to the reader without a per-Work lookup.

## Publish, Export And Other Consumers

- **Publish.** Prepare only queued documents from the adopted Catalogue snapshots, resolving each required Work once per operation and reusing already loaded payloads. Prepare full presentations for selected Catalogue documents and render-only payloads for selected referring documents. Carry the portable references through to Preview and public, and use their exact identities for configured media transfers. A referring document selects the media its rendered content uses. The Work’s own publication supplies its Media View assets, including for text-only openers. Preserve existing queue units, eligibility, Work-before-referrer ordering for jointly selected items, Gallery artifact publication and successful-unit completion. A public Work opener now depends on the target Catalogue document being public. Confirm that dependency in the cutover selection and retain the normal unavailable-target behavior for missing targets. End the raw Work record copies and agree the exact Preview/public cleanup, including removal from the public artifact inventory. The upstream Working input remains part of Studio’s handoff.
- **Collection Export.** Prepare the selected Working documents from the same adopted snapshots. Static HTML converts Work image and text openers to links to the packaged standard rendition, currently 800px, and retains Gallery opener text. Export therefore still resolves the exact Work image and owned download identities required by its output, even when a browser text link carries only a label and ID. Pass the selected assets into the existing HTML/media rewrite as operation inputs. Preserve Browseable and Portable output, selected-file packaging and Preview/Apply revision and verification semantics. Resolve media from the configured Working owners.
- **Prepare Package and diagnostics.** Switch content-bearing Prepare Package to adopted Work presentation for rendered Entry, image and caption fields. Preserve its format and selection behavior. Broken Links checks the exact adopted Catalogue target and keeps its separate Gallery checks. Remove the live Work read route after its callers move. Scope compact picker and report inputs by their existing owners and keep the adopted Catalogue document as the presentation authority.

Working and public use the same reader contract. Route configuration supplies the resource roots and capabilities. Private source paths stay within Working. The browser owns selection, URL resolution, rendering and retained Gallery state. Python owns the selected adoption, projection, persistence and transfer work. [Publish Workflow](../Publish_Workflow.md), [Export](../Export.md) and [Package Prepare](../Package_Prepare.md) own the surrounding workflows.

## Public Rollout

1. Finish the frontend change and project it into `site/` through the normal site tooling.
2. Complete the one-time Working conversion and queue the converted Catalogue documents and affected referring documents. Include the exact Catalogue documents that public Work openers will load.
3. Run normal queue-driven Publish and confirm that the selected JSON and media transfers completed. If the conversion queues the full Catalogue, this Publish run processes the full Catalogue through the same workflow.
4. Verify the projected frontend against the published payloads in site preview. Deploy the frontend and published JSON together in the same site release so the new reader has the payloads it expects when it goes live.

## Delivery Steps

- [ ] **WJ.0 — Readiness.** Confirm the document render data, Work presentation and resource identity contract. Trace the existing Studio Gallery handoff and all raw Work consumers. Agree the initial snapshot and public rollout selections. Account for reference-only Working referrers and ensure that published Work openers have their exact Catalogue targets at reader cutover. Agree bounded payload and request-path evidence for cold first click, Gallery navigation and reuse of loaded data. Treat new queues, broad dependency scans and Gallery ownership changes as separate scope decisions.
- [ ] **WJ.1 — Adopt and project.** Add queue-selected adoption through the document writer, including deletion and ordinary Build preservation. Seed the explicitly agreed Work baseline and prepare the selected Working referrers before switching readers. Produce render-ready referring documents and complete Catalogue Work documents from the adopted data. Keep existing pending effects and the Gallery handoff intact.
- [ ] **WJ.2 — Switch readers and preparation.** Use the document contracts in Working and public Media View. Switch Publish, Export, content-bearing Prepare Package and Broken Links. Retire the raw Work read route and public copy path after consumer and cutover review. Project and validate the public runtime through the normal site tooling.
- [ ] **WJ.3 — Verify and review.** Compare selected payloads and request traces for an inline image, a text opener, direct Catalogue entry and Gallery traversal. Confirm that the same prepared candidates resolve against the configured Working and public roots. Exercise the agreed selected Publish and Export cases, including a Work text link’s packaged image and a selected Work removal. Confirm the adoption boundary, exact transfer completion and absence of referrer fanout. Complete the mandatory Redundancy And Defensive Behavior Review before acceptance. Agree live writes and any test or benchmark work separately.
- [ ] **WJ.4 — Closeout.** Update the durable reader and preparation contracts and reconcile the Gallery Ownership delivery’s scope. Follow the [public rollout](#public-rollout) and record conversion, runtime projection, Publish and deployment evidence as separate outcomes.

## Follow-on

- **Display Gallery links on Catalogue pages.** The Work’s Catalogue JSON already needs these references for Media View. A page section could use the same references to open the selected Gallery, with membership loaded on activation. The existing **context** list remains the related-document section.
- **Move Gallery ownership to Docs Viewer.** The separate [Gallery Ownership delivery](Docs_Viewer_Gallery_Ownership.md) owns source migration, Gallery production and management UI.
- **Investigate Related Links in Media View.** Reuse the Work’s document relationships where appropriate and define what makes a document related to a Gallery. This follows separately from Work adoption and Gallery production.
