import {
  isDocNonViewable
} from "./docs-viewer-tree.js";

export function initDocsViewerSidebarRenderer(context) {
  var documentIndex = context.documentIndex;
  var selectedDocument = context.selectedDocument;
  var nav = context.nav;
  var toolbar = context.toolbar;
  var pathEl = context.pathEl;

  function managementTextValue(key, fallback) {
    var text = context.scopeConfig && context.scopeConfig.managementText;
    if (text && Object.prototype.hasOwnProperty.call(text, key)) {
      return String(text[key] == null ? fallback || "" : text[key]);
    }
    return String(fallback || "");
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
      if (isDocNonViewable(doc)) {
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
      if (isDocNonViewable(doc)) {
        link.setAttribute("data-draft-doc", "true");
        link.title = managementTextValue("metadataNonViewableLabel", "non-viewable");
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
      if (isDocNonViewable(doc)) {
        var draftIcon = document.createElement("span");
        draftIcon.className = "docsViewer__draftPrefix";
        draftIcon.setAttribute("aria-hidden", "true");
        draftIcon.textContent = managementTextValue("docNonViewableEmoji", "\uD83D\uDEAB");
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

    if (toolbar) toolbar.hidden = toolbar.hasAttribute("data-docs-viewer-toolbar-disabled");
    context.renderBookmarkToggle();
  }

  return {
    buildTrail: buildTrail,
    expandTrail: expandTrail,
    renderMeta: renderMeta,
    renderSidebar: renderSidebar
  };
}
