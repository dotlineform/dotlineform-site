function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function optionalStringRecordValue(row, key) {
  var value = cleanString(row && row[key]);
  return value ? value : "";
}

function normalizeTreeDoc(row, parentId) {
  if (!row || typeof row !== "object" || Array.isArray(row)) return null;
  var docId = cleanString(row.doc_id);
  var title = cleanString(row.title);
  var contentUrl = cleanString(row.content_url);
  if (!docId || !title || !contentUrl) return null;
  if (optionalStringRecordValue(row, "parent_id")) {
    throw new Error("Docs index tree nodes must express parentage with nested children, not parent_id.");
  }
  var doc = {
    doc_id: docId,
    title: title,
    content_url: contentUrl
  };
  var uiStatus = optionalStringRecordValue(row, "ui_status");
  if (parentId) doc.parent_id = parentId;
  if (row.viewable === false) doc.viewable = false;
  if (uiStatus) doc.ui_status = uiStatus;
  return doc;
}

function flattenTreeDocs(rows, parentId, docs) {
  if (!Array.isArray(rows)) return docs;
  rows.forEach(function (row) {
    var doc = normalizeTreeDoc(row, parentId);
    if (!doc) return;
    docs.push(doc);
    flattenTreeDocs(row.children, doc.doc_id, docs);
  });
  return docs;
}

function normalizeRecentDoc(row) {
  if (!row || typeof row !== "object" || Array.isArray(row)) return null;
  var docId = cleanString(row.doc_id);
  var title = cleanString(row.title);
  var contentUrl = cleanString(row.content_url);
  var addedDate = cleanString(row.added_date);
  if (!docId || !title || !contentUrl || !addedDate) return null;
  var doc = {
    doc_id: docId,
    title: title,
    content_url: contentUrl,
    added_date: addedDate
  };
  var parentId = optionalStringRecordValue(row, "parent_id");
  var parentTitle = optionalStringRecordValue(row, "parent_title");
  if (parentId) doc.parent_id = parentId;
  if (parentTitle) doc.parent_title = parentTitle;
  return doc;
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
  var viewerOptions = payload.viewer_options && typeof payload.viewer_options === "object" && !Array.isArray(payload.viewer_options)
    ? payload.viewer_options
    : {};
  return {
    schema: "docs_index_tree_v1",
    generated_at: cleanString(payload.generated_at),
    viewer_options: viewerOptions,
    docs: flattenTreeDocs(payload.docs, "", [])
  };
}

export function normalizeRecentlyAddedPayload(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error("Recently-added docs payload must be a JSON object.");
  }
  if (cleanString(payload.schema) !== "docs_recently_added_v1") {
    throw new Error("Recently-added docs payload has an unsupported schema.");
  }
  if (!Array.isArray(payload.docs)) {
    throw new Error("Recently-added docs payload requires docs array.");
  }
  var limit = parseInt(payload.limit, 10);
  return {
    schema: "docs_recently_added_v1",
    generated_at: cleanString(payload.generated_at),
    limit: limit > 0 ? limit : payload.docs.length,
    docs: payload.docs.map(normalizeRecentDoc).filter(Boolean)
  };
}
