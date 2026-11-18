---
draft: false
doc_id: d-20260602-111803-019594
title: Local Studio APIs
added_date: "2026-06-02 11:18:03"
last_updated: "2026-10-11 00:00:00"
summary: Exact loopback Studio app and catalogue API inventory, adapter boundaries, and extension rules.
parent_id: d-20260522-080600-a2b102

---
# Local Studio APIs

## Authority

`studio_app_server.py` owns HTTP dispatch. `studio_catalogue_api.py` owns the Catalogue adapter. Its dispatch branches and `catalogue_write_service.py` define the active endpoint surface.

## App Endpoints

| method | path | purpose |
| --- | --- | --- |
| `GET` | `/health` | Studio app health |
| `GET` | `/studio/runtime-config.json` | validated browser runtime config |

## Catalogue Reads

| method | path | purpose |
| --- | --- | --- |
| `GET` | `/studio/api/catalogue/health` | catalogue service availability |
| `GET` | `/studio/api/catalogue/read` | allowlisted catalogue source and lookup reads |
| `GET` | `/studio/api/catalogue/project-media` | confined project folder and image selection |

The `read` endpoint accepts only server-owned keys and any required record id. It is not an arbitrary path reader. Studio's former `catalogue_work_detail_record` key is retired; the focused Work response uses `studio_catalogue_work_record_v3` without Detail sections.

## Catalogue Operations

| group | POST paths |
| --- | --- |
| work | `/work/create`, `/work/create-batch`, `/work/save` |
| series | `/series/create`, `/series/save` |
| gallery | `/gallery/create`, `/gallery/save`, `/gallery/delete` |
| bulk edit | `/bulk-save` |
| delete | `/delete-apply` |

Every path is beneath `/studio/api/catalogue`. Work deletion uses `{ "kind": "works", "ids": ["00001", "00002"] }` for the exact distinct saved Work IDs selected in the editor. It returns the same `kind` and `ids` with `deleted: true`. Series deletion uses `{ "kind": "series", "series_id": "009" }` after the editor confirms from its saved membership map that the Series is empty. Gallery deletion takes only `gallery_id` on its own route. The service requires the exact existing targets and owns canonical persistence and local completion. Responses distinguish saved data with incomplete completion from a rejected mutation. Refresh Catalogue updates generated readers separately. [Catalogue Source Model](Catalogue_Source_Model.md#save-and-delete)

Generated Catalogue thumbnail reads use the confined local `/studio/catalogue-output/` route, separate from mutation APIs.

## Adapter Boundary

The HTTP adapter parses the named request and delegates:

- catalogue mutations to `catalogue_write_service.py`
- the write dispatcher to Work, Series, Gallery, Work bulk-edit and delete services, followed by shared output completion

The adapter does not own source schemas, mutation policy, build planning, or public projection.

## Safety And Extension

- endpoints are loopback-only and accept explicit JSON objects or allowlisted query keys
- filesystem and environment paths are resolved on the server
- destructive requests validate exact selected IDs, current canonical data and allowed write targets before writing
- source writes use focused validation and atomic catalogue transactions
- browser visibility does not grant authority

To add an operation, define its domain owner first, add one narrow adapter branch, expose a browser client method only when needed, and cover the service contract directly. Update this inventory when the HTTP surface changes.

## Browser Transport

`studio-transport.js` owns the browser's named Catalogue endpoint constants. The server dispatches those requests through the focused Catalogue adapter and domain services. Runtime config supplies site/media/pipeline/route values; it does not publish a second service endpoint map.
