/** Keep All (null), ordinary (empty string), and exact child filters distinct. */
export function filterDocumentLinkTargets(documents, query, collection = null) {
  var search = String(query || "").trim().toLowerCase();
  return documents.filter(function (record) {
    return (collection === null || record.target.collection === collection)
      && (!search || record.title.toLowerCase().includes(search) || record.target.doc_id.includes(search));
  }).sort(function (left, right) {
    return left.title.localeCompare(right.title) || left.target.collection.localeCompare(right.target.collection)
      || left.target.doc_id.localeCompare(right.target.doc_id);
  });
}

/** Insert the document title as literal inline text and preserve the supplied ordinary href. */
export function documentLinkMarkdown(record) {
  var title = record.title.replace(/\s+/g, " ").trim()
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/([\\[\]`*_])/g, "\\$1");
  return "[" + title + "](<" + record.href + ">)";
}

/** Use the editor's revision-checked replacement only while its exact mount is still active. */
export function insertDocumentLink(adapter, capture, record, isCurrent) {
  if (!isCurrent()) throw new Error("The source document is no longer active. Cancel and try again.");
  if (!adapter.replaceCapturedSelection(capture, documentLinkMarkdown(record))) {
    throw new Error("Markdown source changed while this modal was open. Cancel and try again.");
  }
}
