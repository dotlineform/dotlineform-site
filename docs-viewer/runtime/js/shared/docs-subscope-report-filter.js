function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

export function normalizeDocsSubscopeFilterValue(value) {
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

export function projectDocsSubscopeDocuments(documents, filterState = {}) {
  var query = normalizeDocsSubscopeFilterValue(filterState.query);
  return (Array.isArray(documents) ? documents : []).filter(function (documentRecord) {
    return !query || normalizeDocsSubscopeFilterValue(
      documentTitle(documentRecord)
    ).startsWith(query);
  });
}
