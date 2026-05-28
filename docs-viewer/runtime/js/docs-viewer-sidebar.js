import {
  isDocHidden,
  isDocViewable
} from "./docs-viewer-tree.js";

export function initDocsViewerSidebarRenderer(context) {
  var documentIndex = context.documentIndex;
  var selectedDocument = context.selectedDocument;
  var scopeConfig = context.scopeConfig;
  var nav = context.nav;
  var meta = context.meta;
  var pathEl = context.pathEl;
  var updatedEl = context.updatedEl;
  var summaryEl = context.summaryEl;

  function managementText() {
    return scopeConfig && scopeConfig.managementText ? scopeConfig.managementText : {};
  }

  function managementTextValue(key) {
    return String(managementText()[key] || "");
  }

  function showUpdatedDate() {
    return !scopeConfig || scopeConfig.showUpdatedDate !== false;
  }

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
    buildTrail(docId).forEach(function (doc) {
      if (docChildren(doc.doc_id).length > 0) {
        documentIndex.expandedDocIds.add(doc.doc_id);
      }
    });
  }

  function renderSidebar() {
    nav.textContent = "";
    if (documentIndex.docs.length === 0) {
      return;
    }

    nav.appendChild(renderNavList(""));
    context.updateNavDragState();
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
      if (isDocHidden(doc)) {
        row.className += " is-draft";
      }
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
      if (doc.doc_id === selectedDocument.selectedDocId) {
        link.className += " is-active";
        link.setAttribute("aria-current", "page");
      }
      if (isDocHidden(doc)) {
        link.setAttribute("data-draft-doc", "true");
        link.title = managementTextValue("metadataHiddenLabel");
      }
      link.href = context.viewerUrl(context.viewerTargetDocId(doc.doc_id));
      link.dataset.docId = doc.doc_id;
      if (context.canDragCurrentDoc(doc)) {
        link.draggable = true;
        link.dataset.dragDocId = doc.doc_id;
      }
      link.textContent = "";
      var uiStatus = context.statusForIndexDoc(doc);
      if (uiStatus) {
        var statusIcon = document.createElement("span");
        statusIcon.className = "docsViewer__navStatus";
        statusIcon.setAttribute("aria-hidden", "true");
        statusIcon.textContent = uiStatus.emoji;
        link.appendChild(statusIcon);
      }
      if (isDocHidden(doc)) {
        var draftIcon = document.createElement("span");
        draftIcon.className = "docsViewer__draftPrefix";
        draftIcon.setAttribute("aria-hidden", "true");
        draftIcon.textContent = managementTextValue("docHiddenEmoji");
        link.appendChild(draftIcon);
      }
      link.appendChild(document.createTextNode(doc.title));
      row.appendChild(link);
      item.appendChild(row);

      if (hasChildren && documentIndex.expandedDocIds.has(doc.doc_id)) {
        item.appendChild(renderNavList(doc.doc_id));
      }

      list.appendChild(item);
    });

    return list;
  }

  function renderMeta(doc) {
    var trail = buildTrail(doc.doc_id).slice(0, -1);
    pathEl.textContent = "";
    pathEl.hidden = trail.length === 0;

    trail.forEach(function (entry, index) {
      if (index > 0) {
        var separator = document.createElement("span");
        separator.className = "docsViewer__pathSep";
        separator.textContent = "/";
        pathEl.appendChild(separator);
      }

      var link = document.createElement("a");
      link.href = context.viewerUrl(context.viewerTargetDocId(entry.doc_id));
      link.dataset.docId = entry.doc_id;
      link.textContent = entry.title;
      pathEl.appendChild(link);
    });

    var hiddenLabel = managementTextValue("metadataHiddenLabel");
    if (!showUpdatedDate()) {
      updatedEl.textContent = isDocHidden(doc) ? hiddenLabel : "";
      updatedEl.hidden = isDocViewable(doc);
    } else if (doc.last_updated) {
      updatedEl.textContent = (isDocHidden(doc) ? hiddenLabel + " • " : "") + "Updated " + doc.last_updated;
      updatedEl.hidden = false;
    } else {
      updatedEl.textContent = isDocHidden(doc) ? hiddenLabel : "";
      updatedEl.hidden = isDocViewable(doc);
    }
    if (summaryEl) {
      var summary = String(doc.summary || "").trim();
      summaryEl.textContent = summary;
      summaryEl.hidden = !summary;
    }
    meta.hidden = false;
    context.renderBookmarkToggle();
    context.renderStatusPills();
  }

  return {
    buildTrail: buildTrail,
    expandTrail: expandTrail,
    renderMeta: renderMeta,
    renderSidebar: renderSidebar
  };
}
