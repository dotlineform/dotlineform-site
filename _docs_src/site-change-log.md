---
doc_id: site-change-log
title: Site Change Log
last_updated: 2026-03-29
parent_id: ""
sort_order: 20
---

# Site Change Log

## [2026-03-29] Normalized published site and Studio doc references to docs-viewer links

**Status:** implemented

**Area:** architecture

**Summary:**  
Updated published site and Studio docs so references to other published docs now use `/docs/?doc=...` links instead of raw filenames or legacy doc URLs.

**Reason:**  
The docs set is increasingly used through the in-site viewer. Linking published docs through the viewer makes cross-document navigation consistent and keeps repo file references reserved for actual source files and unpublished notes.

**Effect:**  
Published docs now read more cleanly as a connected documentation system, while literal output paths, unpublished docs, and non-doc repo files remain explicit where needed.

**Affected files/docs:**  
- [Site Change Log Guidance](/docs/?doc=site-change-log-guidance)
- [Scripts Overview](/docs/?doc=scripts-overview)
- [UI Framework](/docs/?doc=ui-framework)
- [CSS Audit Spec](/docs/?doc=css-audit-spec)
- [Studio](/docs/?doc=studio)
- [Tag Editor](/docs/?doc=tag-editor)
- [Series Tags](/docs/?doc=series-tags)

**Notes:**  
This change updates documentation navigation only; it does not change site runtime or pipeline behaviour.

## [2026-03-29] Established a dedicated site-wide change log for non-search history

**Status:** implemented

**Area:** architecture

**Summary:**  
Added a dedicated [Site Change Log](/docs/?doc=site-change-log) plus supporting guidance so meaningful non-search site and Studio changes now have a focused historical record separate from search.

**Reason:**  
Search has become complex enough to justify its own subsystem log. The rest of the site still needs a concise historical record, but should not be mixed into the search log.

**Effect:**  
Future review of non-search development can now happen without reconstructing history from scattered commits or overloading the search change log.

**Affected files/docs:**  
- [Site Change Log](/docs/?doc=site-change-log)
- [Site Change Log Guidance](/docs/?doc=site-change-log-guidance)
- `AGENTS.md`

**Notes:**  
This log should be updated for meaningful non-search site, Studio, and pipeline changes as part of normal close-out.

## [2026-03-20] Moved work-detail runtime to per-work JSON and retired the old aggregate work-details flow

**Status:** implemented

**Area:** works

**Summary:**  
Shifted work-detail runtime behaviour so work detail pages resolve from per-work JSON instead of relying on the old aggregate work details index flow.

**Reason:**  
The older aggregate flow added unnecessary coupling and no longer matched the JSON-first direction of the site data model.

**Effect:**  
Work detail runtime became simpler and closer to the canonical per-work data flow. The retired aggregate path and related sitemap/runtime dependencies were removed.

**Affected files/docs:**  
- `_layouts/work_details.html`
- `_layouts/work.html`
- `scripts/generate_work_pages.py`
- `scripts/audit_site_consistency.py`
- [Data Flow](/docs/?doc=data-flow)

**Notes:**  
This was part of the wider JSON-first site architecture shift.

## [2026-03-29] Search-specific history moved out of the general site history

**Status:** implemented

**Area:** architecture

**Summary:**  
Confirmed that search history should live in [Search Change Log](/docs/?doc=search-change-log) rather than the broader site log.

**Reason:**  
Search now has its own artifact, UI surface, policy surface, and document set, so combining it with wider site history would make both logs less useful.

**Effect:**  
The site log remains focused on the wider site and non-search Studio development, while search history is reviewed through its own dedicated log.

**Affected files/docs:**  
- [Search Change Log](/docs/?doc=search-change-log)
- [Site Change Log](/docs/?doc=site-change-log)
- [Site Change Log Guidance](/docs/?doc=site-change-log-guidance)

**Notes:**  
For changes that materially affect both areas, add short entries to both logs.

## [2025-08-19] Adopted JSON-first site data flow for works, series, and moments indexes

**Status:** implemented

**Area:** build pipeline

**Summary:**  
Shifted the main site toward generated JSON artifacts as the primary runtime data layer for works, series, and moments, with lighter collection stubs and index-driven runtime behaviour.

**Reason:**  
The site needed a more consistent and maintainable data flow than page-heavy or mixed-source runtime patterns.

**Effect:**  
The site now relies more heavily on generated JSON contracts and index artifacts, which simplified runtime logic and created a clearer basis for later features such as Studio tooling and search.

**Affected files/docs:**  
- `scripts/generate_work_pages.py`
- `assets/data/works_index.json`
- `assets/data/series_index.json`
- `assets/data/moments_index.json`
- [Data Flow](/docs/?doc=data-flow)
- [Scripts Overview](/docs/?doc=scripts-overview)

**Notes:**  
This entry summarizes the broader architectural shift rather than one single commit.
