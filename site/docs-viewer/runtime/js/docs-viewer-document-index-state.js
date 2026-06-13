import {
  buildChildrenMap,
  hasNonViewableAncestor,
  compareDocs,
  isDocNonViewable,
  isDocViewable
} from "./docs-viewer-tree.js";

export function createDocsViewerDocumentIndexState(options) {
  var settings = options || {};
  var state = settings.state;

  function isManageOnlyTreeDoc(doc) {
    if (!doc || state.manageOnlyTreeRootIds.size === 0) return false;
    var visited = new Set();
    var current = doc;
    while (current && current.doc_id && !visited.has(current.doc_id)) {
      if (state.manageOnlyTreeRootIds.has(current.doc_id)) return true;
      visited.add(current.doc_id);
      current = current.parent_id ? state.allDocsById.get(current.parent_id) : null;
    }
    return false;
  }

  function shouldIncludeDoc(doc) {
    if (!state.managementMode && isManageOnlyTreeDoc(doc)) return false;
    if (!state.managementMode) return isDocViewable(doc) && !hasNonViewableAncestor(doc, state.allDocsById);
    return isDocViewable(doc) || state.showNonViewable;
  }

  function applyDocVisibility() {
    state.allDocsById = new Map(
      state.allDocs.map(function (doc) {
        return [doc.doc_id, doc];
      })
    );
    state.docs = state.allDocs.filter(shouldIncludeDoc).slice().sort(compareDocs);
    state.docsById = new Map(
      state.docs.map(function (doc) {
        return [doc.doc_id, doc];
      })
    );
    state.childrenByParent = buildChildrenMap(state.docs, {
      managementMode: state.managementMode,
      showNonViewable: state.showNonViewable
    });
  }

  function findAllDocById(docId) {
    for (var i = 0; i < state.allDocs.length; i += 1) {
      if (state.allDocs[i].doc_id === docId) return state.allDocs[i];
    }
    return null;
  }

  function syncNonViewableVisibilityForRequestedDoc(getCurrentDocId) {
    if (!state.managementMode) return;
    var requestedDocId = typeof getCurrentDocId === "function" ? getCurrentDocId() : "";
    if (!requestedDocId) return;
    var requestedDoc = findAllDocById(requestedDocId);
    if (requestedDoc && isDocNonViewable(requestedDoc)) {
      state.showNonViewable = true;
    }
  }

  function isNonLoadableDoc(doc) {
    return Boolean(doc) && state.nonLoadableDocIds.has(doc.doc_id);
  }

  function statusForIndexDoc(doc) {
    if (!doc || isNonLoadableDoc(doc)) return null;
    if (!state.managementMode && isManageOnlyTreeDoc(doc)) return null;
    if (!isDocViewable(doc) && !state.managementMode) return null;
    var statusValue = String(doc.ui_status || "").trim();
    return statusValue ? state.uiStatusByValue.get(statusValue) || null : null;
  }

  function firstLoadableDescendantDocId(parentId) {
    var children = state.childrenByParent.get(parentId) || [];
    for (var i = 0; i < children.length; i += 1) {
      var child = children[i];
      if (!isNonLoadableDoc(child)) {
        return child.doc_id;
      }
      var nestedDocId = firstLoadableDescendantDocId(child.doc_id);
      if (nestedDocId) {
        return nestedDocId;
      }
    }
    return "";
  }

  function resolveLoadableDocId(docId) {
    var doc = state.docsById.get(docId);
    if (!doc) return "";
    if (!isNonLoadableDoc(doc)) return doc.doc_id;
    return firstLoadableDescendantDocId(doc.doc_id);
  }

  function flattenRoots() {
    var roots = state.childrenByParent.get("") || [];
    if (roots.length > 0) return roots;
    return state.docs.slice().sort(compareDocs);
  }

  function defaultDocId() {
    var roots = flattenRoots();
    for (var i = 0; i < roots.length; i += 1) {
      var docId = resolveLoadableDocId(roots[i].doc_id);
      if (docId) {
        return docId;
      }
    }
    return "";
  }

  function viewerTargetDocId(docId) {
    var targetDocId = resolveLoadableDocId(docId);
    if (targetDocId) return targetDocId;

    var doc = state.docsById.get(docId);
    if (isNonLoadableDoc(doc)) {
      return defaultDocId();
    }

    return docId;
  }

  return {
    applyDocVisibility: applyDocVisibility,
    defaultDocId: defaultDocId,
    findAllDocById: findAllDocById,
    isManageOnlyTreeDoc: isManageOnlyTreeDoc,
    isNonLoadableDoc: isNonLoadableDoc,
    resolveLoadableDocId: resolveLoadableDocId,
    statusForIndexDoc: statusForIndexDoc,
    syncNonViewableVisibilityForRequestedDoc: syncNonViewableVisibilityForRequestedDoc,
    viewerTargetDocId: viewerTargetDocId
  };
}
