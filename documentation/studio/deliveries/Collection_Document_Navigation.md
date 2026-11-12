---
draft: false
doc_id: d-20261112-090442-74e21c
title: Collection Document Navigation
added_date: "2026-11-12 09:04:42"
last_updated: "2026-11-12"
parent_id: d-20260428-000000-f5ff18
---
# Collection Document Navigation

Complete and accepted on 2026-11-12. The runtime documentation owns the current behavior. Retain this delivery for manual archive. [Planned Features](../Planned_Features.md#ad-hoc-deliveries) · [Runtime behavior](../Docs_Viewer_Runtime.md#collection-previous-and-next)

- [x] **Readiness.** The shared report owns the ordered document results before pagination. Book already owns saved heading order. The reader can carry that context through its existing document openings and immediate-caller Back. The browser has the required list data and server work is unnecessary.
- [x] **Implementation.** Replace Book’s private navigator with the shared row. Book supplies the selected heading order through its existing inventory index. The other collection reports supply the filtered and sorted documents across pages. Book mounts the row above the body. Manage and public mount it below the body for other collections.
- [x] **Static verification.** Changed-file JavaScript lint passed for the shared collection report, navigation row, route workflow and document controller, and for the Manage Book tools, collection list and document report composition. Whitespace, public projection consistency and deploy-root validation passed. The tracked public projection contains the four shared modules and viewer stylesheet.
- [x] **Code and redundancy review.** Traced collection entry, adjacent navigation, direct and modified-link entry, immediate Back, Source redisplay, collection projection changes, and the first, last and single-document cases. Only registered document anchors supply a sequence. The existing route parser still owns exact destination and native link behavior. The report copies only document IDs, links and titles once per entered projection. Book reuses the loaded ID index and resolves only the chosen heading’s placements. The reader carries the compact list and current position through its existing retained entries, with no collection lookup on document open or Previous and Next. Removed Book’s private click listener, pending chapter state, detail mount hook and styling. The existing bounded history remains the limit on sequence restoration.
- [x] **Closeout.** The user confirmed the extra spacing above the bottom row and accepted the delivery after the muted grey link refinement. Both stylesheet changes passed projection, consistency and site validation. Individual sequence, link-entry, history and narrow-width scenarios remain for normal use.
