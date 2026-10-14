/**
 * Select reader thumbnail metadata from a complete committed document summary.
 * Authored assignments take precedence over Context Work subjects. Folder
 * subjects are omitted; Catalogue thumbnails use the selected document ID.
 * @param {Object} record Committed source metadata.
 * @param {string} collection Exact collection identity, or empty for ordinary docs.
 * @returns {Object} Optional has_thumbnail or Work subject, never both.
 */
function selectedDocumentThumbnailMetadata(record, collection) {
  if (record.has_thumbnail === true) {
    return { has_thumbnail: true };
  }
  if (collection === "works" && /^[0-9]{5}$/.test(record.subject)) return { subject: record.subject };
  return {};
}

/** Order completed selection rows for report presentation. */
function sortSelectedDocumentRows(rows) {
  return rows.slice().sort(function (a, b) {
    return b.last_updated.localeCompare(a.last_updated)
      || (a.collection || "").localeCompare(b.collection || "")
      || a.doc_id.localeCompare(b.doc_id);
  });
}

/**
 * @typedef {{doc_id: string, title: string, last_updated: string, collection?: string, has_thumbnail?: boolean, subject?: string}} SelectedDocumentRow
 * @typedef {SelectedDocumentRow & {key: string, href: string, thumbnailWorkId: string, thumbnailSrc: string}} PreparedSelectedDocumentRow
 * @typedef {{rows: PreparedSelectedDocumentRow[], byKey: Map<string, PreparedSelectedDocumentRow>}} SelectedDocumentsData
 */

function selectedKey(collection, docId) {
  return (collection || "") + "/" + docId;
}

function thumbnailWorkId(row) {
  if (row.has_thumbnail === true) return "";
  return row.collection === "catalogue" ? row.doc_id : row.subject || "";
}

/** Prepare completed rows once; exact route ownership remains with the reader.
 * @param {SelectedDocumentRow[]} rows Saved selection rows, without another schema audit.
 * @param {function(string, {collection: string}): string} viewerUrlForDocument Active reader's route owner.
 * @returns {SelectedDocumentsData} Ordered view-owned rows with indexed identities.
 */
export function prepareSelectedDocuments(rows, viewerUrlForDocument) {
  const prepared = rows.map((row) => ({
    ...row, key: selectedKey(row.collection, row.doc_id),
    href: viewerUrlForDocument(row.doc_id, { collection: row.collection || "" }),
    thumbnailWorkId: thumbnailWorkId(row), thumbnailSrc: ""
  }));
  return { rows: sortSelectedDocumentRows(prepared), byKey: new Map(prepared.map((row) => [row.key, row])) };
}

/** Apply one committed effect; title/thumbnail updates do not affect date ordering.
 * Authored thumbnail assignments still reload on a committed update. Deletion
 * preserves the remaining order. Membership additions remain with normal reload.
 * @param {SelectedDocumentsData} data Prepared retained-view state, mutated in place.
 * @param {object} change Collection provider's complete committed document change.
 * @returns {{row: PreparedSelectedDocumentRow, deleted: boolean, thumbnailChanged: boolean}|null} A relevant effect, or no work.
 */
export function applySelectedDocumentChange(data, change) {
  const row = data.byKey.get(selectedKey(change.target.collection, change.target.doc_id));
  if (!row) return null;
  if (change.deleted) {
    data.byKey.delete(row.key);
    data.rows = data.rows.filter((candidate) => candidate !== row);
    return { row, deleted: true, thumbnailChanged: false };
  }
  const metadata = selectedDocumentThumbnailMetadata(change.record, change.target.collection || "");
  const orderChanged = row.last_updated !== change.record.last_updated;
  const thumbnailChanged = metadata.has_thumbnail === true
    || row.has_thumbnail !== metadata.has_thumbnail || row.subject !== metadata.subject;
  if (!orderChanged && !thumbnailChanged && row.title === change.record.title) return null;
  row.title = change.record.title;
  row.last_updated = change.record.last_updated;
  delete row.has_thumbnail;
  delete row.subject;
  Object.assign(row, metadata);
  row.thumbnailWorkId = thumbnailWorkId(row);
  if (orderChanged) data.rows = sortSelectedDocumentRows(data.rows);
  return { row, deleted: false, thumbnailChanged };
}
