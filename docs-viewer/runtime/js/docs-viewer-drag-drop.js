export function canDragDoc(doc, options) {
  var settings = options || {};
  if (settings.dragEnabled === false || !doc) return false;
  return true;
}

function parentWouldCreateCycle(parentId, dragDoc, docsById) {
  if (!parentId) return false;
  var current = docsById.get(parentId);
  var visited = new Set();
  while (current && current.doc_id && !visited.has(current.doc_id)) {
    if (current.doc_id === dragDoc.doc_id) return true;
    visited.add(current.doc_id);
    current = current.parent_id ? docsById.get(current.parent_id) : null;
  }
  return false;
}

export function canDropOnParent(parentId, options) {
  var settings = options || {};
  var docsById = settings.docsById;
  if (!settings.dragDocId || settings.dragEnabled === false) return false;
  if (!docsById || typeof docsById.get !== "function") return false;

  var dragDoc = docsById.get(settings.dragDocId);
  if (!dragDoc || !canDragDoc(dragDoc, settings)) return false;
  var normalizedParentId = String(parentId || "").trim();
  if (!normalizedParentId) return String(dragDoc.parent_id || "").trim() !== "";
  if (dragDoc.doc_id === normalizedParentId) return false;
  if (!docsById.has(normalizedParentId)) return false;
  if (parentWouldCreateCycle(normalizedParentId, dragDoc, docsById)) return false;
  return String(dragDoc.parent_id || "").trim() !== normalizedParentId;
}

export function rowDropParentIdFromEvent(row, event, options) {
  var settings = options || {};
  if (settings.dragEnabled === false) return "";
  if (!row) return "";

  var docId = row.dataset.docRowId || "";
  if (!docId) return "";
  if (settings.docsById && !settings.docsById.has(docId)) return "";
  if (settings.dragDocId === docId) return "";
  return docId;
}

function rootNavList(nav) {
  if (!nav || !nav.children) return null;
  for (var index = 0; index < nav.children.length; index += 1) {
    var child = nav.children[index];
    if (child && child.matches && child.matches(".docsViewer__navList")) return child;
  }
  return null;
}

export function terminalRootDropTargetFromEvent(event, options) {
  var settings = options || {};
  var target = event && event.target;
  if (!target || !target.closest) return null;
  if (target.closest("[data-doc-row-id]")) return null;

  var nav = settings.nav || null;
  var rootList = rootNavList(nav);
  var list = target.closest(".docsViewer__navList");
  if (!list && nav && (target === nav || nav.contains(target))) {
    list = rootList;
  }
  if (!list || list !== rootList) return null;

  return { parentId: "" };
}

export function currentDropTargetFromEvent(event, fallback, options) {
  var row = event && event.target ? event.target.closest("[data-doc-row-id]") : null;
  if (row) {
    return {
      parentId: rowDropParentIdFromEvent(row, event, options)
    };
  }
  var terminalTarget = terminalRootDropTargetFromEvent(event, options);
  if (terminalTarget) return terminalTarget;
  return {
    parentId: fallback && Object.prototype.hasOwnProperty.call(fallback, "parentId") ? fallback.parentId : ""
  };
}
