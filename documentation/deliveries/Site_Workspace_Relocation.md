---
draft: false
doc_id: d-20261119-153500-a5d7c0
title: Site Workspace Relocation
added_date: "2026-11-19 15:35:00"
last_updated: "2026-11-19"
ui_status: done
---

# Site workspace relocation

Group Catalogue media staging, Data Sharing and Docs Export under `dotlineform-site/` inside the configured Projects root. The Library inbox and the original media roots stay at their current locations. The Docs Viewer data checkout keeps its separate root.

- [x] Define the site subdirectory once and wire it into the existing Catalogue, export and package path owners. The local service supplies relative import paths in management capabilities. The browser uses them to remember and navigate the selected folder.
- [x] Update the [local setup](../reference/Local_Setup.md#environment) and owning workflow references.
- [x] Move the three iCloud directories in place and verify that the current path owners resolve them.

The import modal reuses the loaded management capability. Package markers use the resolved package root supplied by the caller. The service still confines browsing to Data Sharing and resolves package paths within that workspace. The browser discards remembered folders outside the supplied root.

Python and JavaScript lint passed for the changed files. Read-only service checks confirmed Data Sharing availability, import staging, rejection of browsing above Data Sharing, package marker resolution, a Library snapshot preview at the new destination, and Catalogue staging with both original-media roots. The move preserved the 12 existing export directories. Verification covered local filesystem and service reads. Browser interaction, workflow writes and iCloud replication to other devices remain outside that evidence.
