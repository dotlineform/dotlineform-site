function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function optionalStringRecordValue(row, key) {
  var value = cleanString(row && row[key]);
  return value ? value : "";
}

function normalizeTreeDoc(row, parentId, depth, treeOrder) {
  if (!row || typeof row !== "object" || Array.isArray(row)) return null;
  var docId = cleanString(row.doc_id);
  var title = cleanString(row.title);
  if (!docId || !title) return null;
  if (optionalStringRecordValue(row, "parent_id")) {
    throw new Error("Docs index tree nodes must express parentage with nested children, not parent_id.");
  }
  var doc = {
    doc_id: docId,
    title: title,
    tree_depth: depth,
    tree_order: treeOrder
  };
  var uiStatus = optionalStringRecordValue(row, "ui_status");
  var reportId = optionalStringRecordValue(row, "report_id");
  if (parentId) doc.parent_id = parentId;
  if (typeof row.draft === "boolean") doc.draft = row.draft;
  if (uiStatus) doc.ui_status = uiStatus;
  if (reportId) doc.report_id = reportId;
  return doc;
}

function flattenTreeDocs(rows, parentId, docs, depth) {
  if (!Array.isArray(rows)) return docs;
  rows.forEach(function (row) {
    var doc = normalizeTreeDoc(row, parentId, depth, docs.length);
    if (!doc) return;
    docs.push(doc);
    flattenTreeDocs(row.children, doc.doc_id, docs, depth + 1);
  });
  return docs;
}

export function normalizeDocsIndexTreePayload(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Docs index tree payload must be a JSON object.");
  }
  if (cleanString(payload.schema) !== "docs_index_tree_v1") {
    throw new Error("Docs index tree payload has an unsupported schema.");
  }
  if (!Array.isArray(payload.docs)) {
    throw new Error("Docs index tree payload requires docs array.");
  }
  return {
    schema: "docs_index_tree_v1",
    generated_at: cleanString(payload.generated_at),
    docs: flattenTreeDocs(payload.docs, "", [], 0)
  };
}
