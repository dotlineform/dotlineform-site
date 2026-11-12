/** Project the displayed document into the mounted Index tree. */
export function initDocsViewerSidebarRenderer(context) {
  var documentIndex = context.documentIndex;
  var nav = context.nav;
  var toolbar = context.toolbar;
  var mountedRows = new Map();
  var markedDocId = "";

  function docChildren(docId) {
    return documentIndex.childrenByParent.get(docId) || [];
  }

  function buildTrail(docId) {
    var trail = [];
    var current = documentIndex.docsById.get(docId);
    while (current) {
      trail.unshift(current);
      current = current.parent_id ? documentIndex.docsById.get(current.parent_id) : null;
    }
    return trail;
  }

  function expandTrail(docId) {
    var ancestors = buildTrail(docId);
    ancestors.pop();
    ancestors.forEach(function (doc) {
      if (!documentIndex.expandedDocIds.has(doc.doc_id)) {
        documentIndex.expandedDocIds.add(doc.doc_id);
        updateBranch(doc.doc_id);
      }
    });
  }

  function renderSidebar() {
    nav.textContent = "";
    mountedRows.clear();
    markedDocId = "";
    if (documentIndex.docs.length === 0) {
      return;
    }

    nav.appendChild(renderNavList(""));
    trackLocation();
  }

  function updateBranch(docId) {
    var mounted = mountedRows.get(docId);
    if (!mounted || !mounted.toggle) return;
    var expanded = documentIndex.expandedDocIds.has(docId);
    mounted.toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
    mounted.toggle.setAttribute("aria-label", expanded ? "Collapse section" : "Expand section");
    mounted.toggle.textContent = expanded ? "▼" : "►";
    if (expanded && !mounted.children) {
      mounted.children = renderNavList(docId);
      mounted.item.appendChild(mounted.children);
    }
    if (mounted.children) mounted.children.hidden = !expanded;
  }

  function toggleBranch(docId) {
    if (documentIndex.expandedDocIds.has(docId)) documentIndex.expandedDocIds.delete(docId);
    else documentIndex.expandedDocIds.add(docId);
    updateBranch(docId);
  }

  function markLocation(docId, current) {
    var mounted = mountedRows.get(docId);
    if (!mounted) return;
    mounted.link.classList.toggle("is-active", Boolean(current));
    if (current) mounted.link.setAttribute("aria-current", current);
    else mounted.link.removeAttribute("aria-current");
  }

  function scrollLocationIntoView(docId) {
    var mounted = mountedRows.get(docId);
    if (!mounted) return;
    var row = mounted.row.getBoundingClientRect();
    if (!row.height) return;
    var bounds = nav.getBoundingClientRect();
    var top = Math.max(bounds.top, 0);
    var bottom = Math.min(bounds.bottom, nav.ownerDocument.defaultView.innerHeight);
    if (row.top < top) nav.scrollTop -= top - row.top;
    else if (row.bottom > bottom) nav.scrollTop += row.bottom - bottom;
  }

  /** Mark the current row while hidden and reveal its path when the tree is visible. */
  function trackLocation() {
    var displayed = context.selectedDocument.displayedRecord;
    var collection = displayed?.collection;
    var rowId = collection
      ? context.workspaceConfig.activeConfig?.collectionsById.get(collection)?.reportHostDocId
      : displayed?.doc_id;
    var docId = documentIndex.docsById.has(rowId) ? rowId : "";
    var visible = !nav.closest("[hidden]");
    if (visible && docId) expandTrail(docId);
    if (markedDocId !== docId) markLocation(markedDocId, "");
    markLocation(docId, collection ? "location" : "page");
    markedDocId = docId;
    if (visible) scrollLocationIntoView(docId);
  }

  function renderNavList(parentId) {
    var list = document.createElement("ul");
    list.className = parentId ? "docsViewer__navList docsViewer__navList--child" : "docsViewer__navList";

    var docs = documentIndex.childrenByParent.get(parentId) || [];
    docs.forEach(function (doc) {
      var item = document.createElement("li");
      item.className = "docsViewer__navItem";
      var row = document.createElement("div");
      row.className = "docsViewer__navRow";
      row.dataset.docRowId = doc.doc_id;
      var children = docChildren(doc.doc_id);
      var hasChildren = children.length > 0;

      if (hasChildren) {
        var toggle = document.createElement("button");
        toggle.type = "button";
        toggle.className = "docsViewer__toggle";
        toggle.dataset.toggleDocId = doc.doc_id;
        toggle.setAttribute("aria-expanded", documentIndex.expandedDocIds.has(doc.doc_id) ? "true" : "false");
        toggle.setAttribute("aria-label", documentIndex.expandedDocIds.has(doc.doc_id) ? "Collapse section" : "Expand section");
        toggle.textContent = documentIndex.expandedDocIds.has(doc.doc_id) ? "▼" : "►";
        row.appendChild(toggle);
      } else {
        var spacer = document.createElement("span");
        spacer.className = "docsViewer__toggleSpacer";
        spacer.setAttribute("aria-hidden", "true");
        spacer.textContent = "";
        row.appendChild(spacer);
      }

      var link = document.createElement("a");
      link.className = "docsViewer__navLink";
      link.href = context.viewerUrl(doc.doc_id);
      link.dataset.docId = doc.doc_id;
      link.draggable = false;
      link.textContent = "";
      var uiStatus = context.statusForIndexDoc(doc);
      if (uiStatus) {
        var statusIcon = document.createElement("span");
        statusIcon.classList.add("docsViewer__listIcon", "docsViewer__navStatus", uiStatus.artwork);
        statusIcon.setAttribute("aria-hidden", "true");
        statusIcon.title = uiStatus.label;
        link.appendChild(statusIcon);
      }
      if (doc.draft === true) {
        var draftIcon = document.createElement("span");
        draftIcon.className = "docsViewer__listIcon docsViewer__draftIndicator docsViewer__icon--circle-dashed-check";
        draftIcon.setAttribute("aria-hidden", "true");
        draftIcon.title = "Draft";
        link.appendChild(draftIcon);
      }
      if (doc.report_id === "docs_collection") {
        var collection = context.workspaceConfig.activeConfig.collectionsByReportHostId.get(doc.doc_id);
        if (!collection) throw new Error("Collection report is missing its configured index icon: " + doc.doc_id);
        var reportIcon = document.createElement("span");
        reportIcon.className = "docsViewer__listIcon docsViewer__navReportIcon";
        reportIcon.style.maskImage = 'url("' + collection.iconUrl + '")';
        reportIcon.setAttribute("aria-hidden", "true");
        link.appendChild(reportIcon);
        var reportLabel = document.createElement("span");
        reportLabel.className = "visually-hidden";
        reportLabel.textContent = "Collection report: ";
        link.appendChild(reportLabel);
      }
      link.appendChild(document.createTextNode(doc.title));
      row.appendChild(link);
      var mounted = { item: item, row: row, link: link, toggle: hasChildren ? toggle : null, children: null };
      mountedRows.set(doc.doc_id, mounted);
      item.appendChild(row);

      if (hasChildren && documentIndex.expandedDocIds.has(doc.doc_id)) {
        mounted.children = renderNavList(doc.doc_id);
        item.appendChild(mounted.children);
      }

      list.appendChild(item);
    });

    return list;
  }

  function renderMeta() {
    if (toolbar) toolbar.hidden = toolbar.hasAttribute("data-docs-viewer-toolbar-disabled");
  }

  return {
    buildTrail: buildTrail,
    renderMeta: renderMeta,
    renderSidebar: renderSidebar,
    toggleBranch: toggleBranch,
    trackLocation: trackLocation
  };
}
