export function sortKey(doc) {
  return [
    String(doc.title || "").toLowerCase(),
    String(doc.doc_id || "")
  ];
}

export function compareDocs(left, right) {
  var leftKey = sortKey(left);
  var rightKey = sortKey(right);
  for (var i = 0; i < leftKey.length; i += 1) {
    if (leftKey[i] < rightKey[i]) return -1;
    if (leftKey[i] > rightKey[i]) return 1;
  }
  return 0;
}

export function buildChildrenMap(docs, options) {
  var settings = options || {};
  var childrenByParent = new Map();
  var visibleDocIds = new Set(docs.map(function (doc) {
    return doc.doc_id;
  }));
  docs.forEach(function (doc) {
    var parentId = doc.parent_id || "";
    if (settings.managementContext && !settings.showNonViewable && parentId && !visibleDocIds.has(parentId)) {
      parentId = "";
    }
    if (!childrenByParent.has(parentId)) {
      childrenByParent.set(parentId, []);
    }
    childrenByParent.get(parentId).push(doc);
  });
  childrenByParent.forEach(function (group) {
    group.sort(compareDocs);
  });
  return childrenByParent;
}

export function isDocViewable(doc) {
  return !isDocNonViewable(doc);
}

export function isDocNonViewable(doc) {
  if (!doc) return false;
  return doc.viewable === false;
}

export function hasNonViewableAncestor(doc, docsById) {
  if (!doc || !doc.parent_id || !docsById) return false;
  var visited = new Set([doc.doc_id]);
  var current = docsById.get(doc.parent_id);
  while (current && current.doc_id && !visited.has(current.doc_id)) {
    if (!isDocViewable(current)) return true;
    visited.add(current.doc_id);
    current = current.parent_id ? docsById.get(current.parent_id) : null;
  }
  return false;
}

export function normalizeDocIdSet(values, fallback) {
  var source = Array.isArray(values) ? values : fallback;
  var ids = Array.isArray(source) ? source : [];
  return new Set(
    ids
      .map(function (value) { return String(value || "").trim(); })
      .filter(Boolean)
  );
}
