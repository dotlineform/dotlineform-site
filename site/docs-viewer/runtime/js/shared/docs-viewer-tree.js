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
