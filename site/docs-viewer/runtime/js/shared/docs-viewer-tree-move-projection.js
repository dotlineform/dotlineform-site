import {
  compareDocs
} from "./docs-viewer-tree.js";

function cleanId(value) {
  return String(value == null ? "" : value).trim();
}

function directChildByClass(parent, className) {
  if (!parent) return null;
  return Array.from(parent.children).find(function (child) {
    return child.classList && child.classList.contains(className);
  }) || null;
}

function directItemRow(item) {
  return directChildByClass(item, "docsViewer__navRow");
}

function directItemForDoc(list, docId) {
  var targetDocId = cleanId(docId);
  if (!list || !targetDocId) return null;
  return Array.from(list.children).find(function (item) {
    var row = directItemRow(item);
    return row && cleanId(row.dataset.docRowId) === targetDocId;
  }) || null;
}

function rowForDoc(nav, docId, cssEscape) {
  var targetDocId = cleanId(docId);
  if (!nav || !targetDocId) return null;
  return nav.querySelector('[data-doc-row-id="' + cssEscape(targetDocId) + '"]');
}

function childListForItem(item) {
  return directChildByClass(item, "docsViewer__navList--child");
}

function rootList(nav) {
  return directChildByClass(nav, "docsViewer__navList");
}

function replaceParentControl(row, nextControl) {
  var currentControl = Array.from(row.children).find(function (child) {
    return child.classList && (
      child.classList.contains("docsViewer__toggle")
      || child.classList.contains("docsViewer__toggleSpacer")
    );
  }) || null;
  if (currentControl) {
    currentControl.replaceWith(nextControl);
  } else {
    row.prepend(nextControl);
  }
}

function createToggle(documentRef, docId, expanded) {
  var toggle = documentRef.createElement("button");
  toggle.type = "button";
  toggle.className = "docsViewer__toggle";
  toggle.dataset.toggleDocId = docId;
  toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
  toggle.setAttribute("aria-label", expanded ? "Collapse section" : "Expand section");
  toggle.textContent = expanded ? "▼" : "►";
  return toggle;
}

function createSpacer(documentRef) {
  var spacer = documentRef.createElement("span");
  spacer.className = "docsViewer__toggleSpacer";
  spacer.setAttribute("aria-hidden", "true");
  spacer.textContent = "";
  return spacer;
}

function syncParentChrome(options, parentId) {
  var targetParentId = cleanId(parentId);
  if (!targetParentId) return;
  var row = rowForDoc(options.nav, targetParentId, options.cssEscape);
  if (!row) {
    throw new Error("Move projection parent row is not mounted: " + targetParentId);
  }
  var item = row.closest(".docsViewer__navItem");
  if (!item) {
    throw new Error("Move projection parent item is not mounted: " + targetParentId);
  }

  var children = options.documentIndex.childrenByParent.get(targetParentId) || [];
  if (children.length === 0) {
    options.documentIndex.expandedDocIds.delete(targetParentId);
    replaceParentControl(row, createSpacer(options.document));
    var emptyList = childListForItem(item);
    if (emptyList) emptyList.remove();
    return;
  }

  var expanded = options.documentIndex.expandedDocIds.has(targetParentId);
  replaceParentControl(row, createToggle(options.document, targetParentId, expanded));
}

function destinationList(options, parentId, movedItem) {
  var targetParentId = cleanId(parentId);
  if (!targetParentId) {
    var list = rootList(options.nav);
    if (!list) throw new Error("Move projection root list is not mounted.");
    return list;
  }

  var parentRow = rowForDoc(options.nav, targetParentId, options.cssEscape);
  var parentItem = parentRow ? parentRow.closest(".docsViewer__navItem") : null;
  if (!parentItem) {
    throw new Error("Move projection destination is not mounted: " + targetParentId);
  }
  var list = childListForItem(parentItem);
  if (list) return list;

  list = options.renderNavList(targetParentId);
  if (!list || !list.classList || !list.classList.contains("docsViewer__navList")) {
    throw new Error("Move projection could not render the destination child list: " + targetParentId);
  }
  var generatedMovedItem = directItemForDoc(list, options.projection.docId);
  if (generatedMovedItem) generatedMovedItem.replaceWith(movedItem);
  parentItem.appendChild(list);
  return list;
}

function insertInModelOrder(list, movedItem, projection, documentIndex) {
  var siblings = documentIndex.childrenByParent.get(projection.parentId) || [];
  var movedIndex = siblings.findIndex(function (doc) {
    return cleanId(doc && doc.doc_id) === projection.docId;
  });
  if (movedIndex === -1) {
    throw new Error("Move projection destination model does not contain " + projection.docId + ".");
  }

  for (var i = movedIndex + 1; i < siblings.length; i += 1) {
    var nextItem = directItemForDoc(list, siblings[i].doc_id);
    if (nextItem) {
      list.insertBefore(movedItem, nextItem);
      return;
    }
  }
  list.appendChild(movedItem);
}

function modelLocations(childrenByParent, docId) {
  var locations = [];
  childrenByParent.forEach(function (children, parentId) {
    children.forEach(function (doc, index) {
      if (cleanId(doc && doc.doc_id) === docId) {
        locations.push({ parentId: cleanId(parentId), index: index, doc: doc });
      }
    });
  });
  return locations;
}

function assertDestinationIsValid(state, docId, parentId) {
  if (!parentId) return;
  if (parentId === docId) throw new Error("Move projection cannot parent a document to itself.");
  if (!state.docsById.has(parentId)) {
    throw new Error("Move projection destination is not in the current index model: " + parentId);
  }
  var visited = new Set([docId]);
  var current = state.docsById.get(parentId);
  while (current && current.doc_id) {
    var currentId = cleanId(current.doc_id);
    if (visited.has(currentId)) {
      throw new Error("Move projection would create a cycle for " + docId + ".");
    }
    visited.add(currentId);
    current = current.parent_id ? state.docsById.get(cleanId(current.parent_id)) : null;
  }
}

export function projectCommittedTreeMoveModel(state, record) {
  var moveRecord = record && typeof record === "object" ? record : null;
  var docId = cleanId(moveRecord && moveRecord.doc_id);
  if (!docId || !moveRecord || !Object.prototype.hasOwnProperty.call(moveRecord, "parent_id")) {
    throw new Error("Committed move record requires doc_id and parent_id.");
  }
  var parentId = cleanId(moveRecord.parent_id);
  var allDoc = state.allDocsById.get(docId) || null;
  var visibleDoc = state.docsById.get(docId) || null;
  if (!allDoc || !visibleDoc) {
    throw new Error("Committed move document is not in the current index model: " + docId);
  }
  assertDestinationIsValid(state, docId, parentId);

  var locations = modelLocations(state.childrenByParent, docId);
  if (locations.length !== 1) {
    throw new Error("Committed move document must have exactly one current child collection: " + docId);
  }
  var location = locations[0];
  var previousParentId = cleanId(allDoc.parent_id);
  if (previousParentId === parentId) {
    return {
      changed: false,
      docId: docId,
      oldCollectionParentId: location.parentId,
      previousParentId: previousParentId,
      parentId: parentId
    };
  }

  var oldChildren = state.childrenByParent.get(location.parentId) || [];
  oldChildren.splice(location.index, 1);
  if (oldChildren.length === 0) state.childrenByParent.delete(location.parentId);

  allDoc.parent_id = parentId;
  if (visibleDoc !== allDoc) visibleDoc.parent_id = parentId;
  var nextChildren = state.childrenByParent.get(parentId);
  if (!nextChildren) {
    nextChildren = [];
    state.childrenByParent.set(parentId, nextChildren);
  }
  nextChildren.push(visibleDoc);
  nextChildren.sort(compareDocs);

  return {
    changed: true,
    docId: docId,
    oldCollectionParentId: location.parentId,
    previousParentId: previousParentId,
    parentId: parentId
  };
}

export function projectCommittedTreeMoveDom(options = {}) {
  var projection = options.projection || {};
  if (!projection.changed) return null;
  var nav = options.nav;
  var documentIndex = options.documentIndex || {};
  var cssEscape = typeof options.cssEscape === "function" ? options.cssEscape : function (value) { return value; };
  var renderNavList = options.renderNavList;
  var documentRef = options.document || (nav && nav.ownerDocument);
  if (!nav || !documentRef || typeof renderNavList !== "function") {
    throw new Error("Move projection requires the mounted nav and sidebar renderer.");
  }

  var movedRow = rowForDoc(nav, projection.docId, cssEscape);
  var movedItem = movedRow ? movedRow.closest(".docsViewer__navItem") : null;
  if (!movedItem) {
    throw new Error("Committed move subtree is not mounted: " + projection.docId);
  }

  movedItem.remove();
  var targetList = destinationList({
    cssEscape: cssEscape,
    document: documentRef,
    documentIndex: documentIndex,
    nav: nav,
    projection: projection,
    renderNavList: renderNavList
  }, projection.parentId, movedItem);
  if (!movedItem.parentNode) {
    insertInModelOrder(targetList, movedItem, projection, documentIndex);
  }
  syncParentChrome({
    cssEscape: cssEscape,
    document: documentRef,
    documentIndex: documentIndex,
    nav: nav
  }, projection.oldCollectionParentId);
  syncParentChrome({
    cssEscape: cssEscape,
    document: documentRef,
    documentIndex: documentIndex,
    nav: nav
  }, projection.parentId);
  return movedItem;
}

export function treeMoveAffectsDoc(docsById, movedDocId, candidateDocId) {
  var movedId = cleanId(movedDocId);
  var currentId = cleanId(candidateDocId);
  var visited = new Set();
  while (currentId && !visited.has(currentId)) {
    if (currentId === movedId) return true;
    visited.add(currentId);
    var current = docsById.get(currentId);
    currentId = current ? cleanId(current.parent_id) : "";
  }
  return false;
}

export function createDocsViewerTreeMoveProjection(options = {}) {
  var documentIndex = options.documentIndex || {};
  var documentIndexState = options.documentIndexState || {};
  var selectedDocument = options.selectedDocument || {};
  var sidebar = options.sidebar || {};

  function project(record) {
    if (typeof documentIndex.projectCommittedMove !== "function" || typeof sidebar.projectCommittedMove !== "function") {
      throw new Error("Docs Viewer local move projection is unavailable.");
    }
    var projection = documentIndex.projectCommittedMove(record);
    sidebar.projectCommittedMove(projection);
    var selectedDocId = cleanId(selectedDocument.selectedDocId);
    if (treeMoveAffectsDoc(documentIndexState.docsById, projection.docId, selectedDocId)) {
      var selectedDoc = documentIndexState.docsById.get(selectedDocId) || null;
      if (selectedDoc && typeof options.renderMeta === "function") options.renderMeta(selectedDoc);
      if (typeof options.updateInfoPanel === "function") options.updateInfoPanel();
    }
    return projection;
  }

  return {
    project: project
  };
}
