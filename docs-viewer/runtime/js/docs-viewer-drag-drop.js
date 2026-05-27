export function normalizeSortOrderValue(value) {
  return value == null ? "" : String(value);
}

export function canDragDoc(doc, options) {
  var settings = options || {};
  if (settings.dragEnabled === false || !doc) return false;
  if (typeof settings.hasChildren === "function" && settings.hasChildren(doc.doc_id)) return false;
  return true;
}

export function rowDropPosition(row, event, options) {
  var settings = options || {};
  if (settings.dragEnabled === false) return "";
  if (!row) return "";

  var docId = row.dataset.docRowId || "";
  if (!docId) return "";
  if (settings.docsById && !settings.docsById.has(docId)) return "";
  if (settings.dragDocId === docId) return "";

  var rect = row.getBoundingClientRect();
  var clientY = event && typeof event.clientY === "number" ? event.clientY : rect.top + (rect.height / 2);
  var afterThresholdY = rect.top + (rect.height * 0.5);
  if (clientY >= afterThresholdY && rowHasVisibleChildList(row)) return "inside-start";
  return clientY >= afterThresholdY ? "after" : "inside";
}

export function canDropOnDoc(docId, position, options) {
  var settings = options || {};
  var docsById = settings.docsById;
  if (!settings.dragDocId || settings.dragEnabled === false) return false;
  if (!docsById || typeof docsById.get !== "function") return false;

  var dragDoc = docsById.get(settings.dragDocId);
  var targetDoc = docsById.get(docId);
  if (!dragDoc || !targetDoc) return false;
  if (!canDragDoc(dragDoc, settings)) return false;
  if (dragDoc.doc_id === targetDoc.doc_id) return false;
  return position === "inside" || position === "inside-start" || position === "after";
}

function rowHasVisibleChildList(row) {
  var item = row && row.parentElement;
  if (!item || !item.children) return false;
  return Array.prototype.some.call(item.children, function (child) {
    return child && child.matches && child.matches(".docsViewer__navList--child");
  });
}

function directListRows(list) {
  var rows = [];
  if (!list || !list.children) return rows;
  Array.prototype.forEach.call(list.children, function (item) {
    if (!item || !item.children) return;
    Array.prototype.some.call(item.children, function (child) {
      if (child && child.matches && child.matches("[data-doc-row-id]")) {
        rows.push(child);
        return true;
      }
      return false;
    });
  });
  return rows;
}

function rootNavList(nav) {
  if (!nav || !nav.children) return null;
  for (var index = 0; index < nav.children.length; index += 1) {
    var child = nav.children[index];
    if (child && child.matches && child.matches(".docsViewer__navList")) return child;
  }
  return null;
}

export function terminalListDropTargetFromEvent(event, options) {
  var settings = options || {};
  var target = event && event.target;
  if (!target || !target.closest) return null;
  if (target.closest("[data-doc-row-id]")) return null;

  var nav = settings.nav || null;
  var list = target.closest(".docsViewer__navList");
  if (!list && nav && (target === nav || nav.contains(target))) {
    list = rootNavList(nav);
  }
  if (!list || (nav && !nav.contains(list))) return null;

  var rows = directListRows(list);
  var lastRow = rows.length ? rows[rows.length - 1] : null;
  if (!lastRow) return null;

  var rect = lastRow.getBoundingClientRect();
  var clientY = event && typeof event.clientY === "number" ? event.clientY : rect.bottom;
  if (clientY < rect.top + (rect.height * 0.5)) return null;

  return {
    targetDocId: lastRow.dataset.docRowId || "",
    position: "after"
  };
}

export function currentDropTargetFromEvent(event, fallback, options) {
  var row = event && event.target ? event.target.closest("[data-doc-row-id]") : null;
  if (row) {
    return {
      targetDocId: row.dataset.docRowId || "",
      position: rowDropPosition(row, event, options)
    };
  }
  var terminalTarget = terminalListDropTargetFromEvent(event, options);
  if (terminalTarget) return terminalTarget;
  return {
    targetDocId: fallback && fallback.targetDocId || "",
    position: fallback && fallback.position || ""
  };
}
