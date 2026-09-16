function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

export function normalizeDocsCollectionFilterValue(value) {
  return cleanString(value)
    .normalize("NFKC")
    .replace(/\s+/g, " ")
    .toLowerCase();
}

function documentTitle(documentRecord) {
  if (!documentRecord || typeof documentRecord !== "object") return "";
  if (Object.prototype.hasOwnProperty.call(documentRecord, "title")) {
    return documentRecord.title;
  }
  return documentRecord.record && documentRecord.record.title;
}

export function projectDocsCollectionDocuments(documents, filterState = {}) {
  var query = normalizeDocsCollectionFilterValue(filterState.query);
  return (Array.isArray(documents) ? documents : []).filter(function (documentRecord) {
    return !query || normalizeDocsCollectionFilterValue(
      documentTitle(documentRecord)
    ).startsWith(query);
  });
}
