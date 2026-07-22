function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

export function collectDescendantDocIds(docs, docId, bucket) {
  var records = Array.isArray(docs) ? docs : [];
  var targetDocId = normalizeText(docId);
  var targetBucket = bucket instanceof Set ? bucket : new Set();
  if (!targetDocId) return targetBucket;
  records.forEach(function (candidate) {
    if (!candidate || (candidate.parent_id || "") !== targetDocId || targetBucket.has(candidate.doc_id)) return;
    targetBucket.add(candidate.doc_id);
    collectDescendantDocIds(records, candidate.doc_id, targetBucket);
  });
  return targetBucket;
}
