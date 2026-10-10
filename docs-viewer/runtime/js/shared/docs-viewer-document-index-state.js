import {
  buildChildrenMap
} from "./docs-viewer-tree.js";

export function createDocsViewerDocumentIndexState(options) {
  var state = options.state;

  function updateDocumentIndex() {
    state.docsById = new Map(
      state.docs.map(function (doc) {
        return [doc.doc_id, doc];
      })
    );
    state.childrenByParent = buildChildrenMap(state.docs);
    if (!state.docsById.has(state.indexSelectedDocId)) state.indexSelectedDocId = "";
    state.expandedDocIds = new Set(Array.from(state.expandedDocIds).filter(function (docId) { return state.docsById.has(docId); }));
  }

  function statusForIndexDoc(doc) {
    if (!doc) return null;
    var statusValue = String(doc.ui_status || "").trim();
    return statusValue ? state.uiStatusByValue.get(statusValue) || null : null;
  }

  function defaultDocId() {
    var roots = state.childrenByParent.get("") || [];
    var doc = roots[0] || state.docs[0];
    return doc ? doc.doc_id : "";
  }

  return {
    updateDocumentIndex: updateDocumentIndex,
    defaultDocId: defaultDocId,
    statusForIndexDoc: statusForIndexDoc
  };
}
