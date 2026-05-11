export function normalizeSortOrderValue(value) {
  return value == null ? "" : String(value);
}

export function moveUndoRecordChanged(record, nextRecord) {
  if (!record || !nextRecord) return false;
  return (
    String(record.parent_id || "") !== String(nextRecord.parent_id || "") ||
    normalizeSortOrderValue(record.sort_order) !== normalizeSortOrderValue(nextRecord.sort_order)
  );
}

export function normalizeMoveUndoRecords(records) {
  if (!Array.isArray(records)) return [];
  var seen = new Set();
  return records.reduce(function (acc, record) {
    if (!record || !record.doc_id) return acc;
    var docId = String(record.doc_id || "").trim();
    if (!docId || seen.has(docId)) return acc;
    seen.add(docId);
    acc.push({
      doc_id: docId,
      title: String(record.title || docId),
      parent_id: String(record.parent_id || ""),
      sort_order: normalizeSortOrderValue(record.sort_order)
    });
    return acc;
  }, []);
}

export function moveUndoPayloadRecords(undoRecords) {
  return undoRecords.map(function (record) {
    return {
      doc_id: record.doc_id,
      parent_id: record.parent_id || "",
      sort_order: normalizeSortOrderValue(record.sort_order)
    };
  });
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
  return position === "inside" || position === "after";
}

export function currentDropTargetFromEvent(event, fallback, options) {
  var row = event && event.target ? event.target.closest("[data-doc-row-id]") : null;
  if (row) {
    return {
      targetDocId: row.dataset.docRowId || "",
      position: rowDropPosition(row, event, options)
    };
  }
  return {
    targetDocId: fallback && fallback.targetDocId || "",
    position: fallback && fallback.position || ""
  };
}
