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

function documentGroup(documentRecord) {
  if (!documentRecord || typeof documentRecord !== "object") return "";
  if (Object.prototype.hasOwnProperty.call(documentRecord, "group")) {
    return documentRecord.group;
  }
  return documentRecord.record && documentRecord.record.group;
}

export function projectDocsSubscopeDocuments(documents, filterState = {}) {
  var query = normalizeDocsSubscopeFilterValue(filterState.query);
  var group = normalizeDocsSubscopeFilterValue(filterState.group);
  return (Array.isArray(documents) ? documents : []).filter(function (documentRecord) {
    var titleMatches = !query || normalizeDocsSubscopeFilterValue(
      documentTitle(documentRecord)
    ).startsWith(query);
    var groupMatches = !group || normalizeDocsSubscopeFilterValue(
      documentGroup(documentRecord)
    ) === group;
    return titleMatches && groupMatches;
  });
}
