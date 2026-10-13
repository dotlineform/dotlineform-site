/**
 * Select reader thumbnail metadata from a complete committed document summary.
 * Authored assignments take precedence over Context Work subjects. Folder
 * subjects are omitted; Catalogue thumbnails use the selected document ID.
 * @param {Object} record Committed source metadata.
 * @param {string} collection Exact collection identity, or empty for ordinary docs.
 * @returns {Object} Optional has_thumbnail or Work subject, never both.
 */
export function selectedDocumentThumbnailMetadata(record, collection) {
  if (record.has_thumbnail === true) {
    return { has_thumbnail: true };
  }
  if (collection === "works" && /^[0-9]{5}$/.test(record.subject)) return { subject: record.subject };
  return {};
}

/** Order completed selection rows for report presentation. */
export function sortSelectedDocumentRows(rows) {
  return rows.slice().sort(function (a, b) {
    return b.last_updated.localeCompare(a.last_updated)
      || (a.collection || "").localeCompare(b.collection || "")
      || a.doc_id.localeCompare(b.doc_id);
  });
}
