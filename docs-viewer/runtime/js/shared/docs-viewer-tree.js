export function buildChildrenMap(docs) {
  var childrenByParent = new Map();
  docs.forEach(function (doc) {
    var parentId = doc.parent_id || "";
    if (!childrenByParent.has(parentId)) {
      childrenByParent.set(parentId, []);
    }
    childrenByParent.get(parentId).push(doc);
  });
  return childrenByParent;
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
