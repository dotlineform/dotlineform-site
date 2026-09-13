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

export function buildChildrenMap(docs) {
  var childrenByParent = new Map();
  docs.forEach(function (doc) {
    var parentId = doc.parent_id || "";
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

export function normalizeDocIdSet(values, fallback) {
  var source = Array.isArray(values) ? values : fallback;
  var ids = Array.isArray(source) ? source : [];
  return new Set(
    ids
      .map(function (value) { return String(value || "").trim(); })
      .filter(Boolean)
  );
}
