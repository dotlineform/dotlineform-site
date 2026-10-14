import { classifyDocsDocumentSubject } from "../shared/docs-document-subject.js";

/**
 * @typedef {{docId: string, title: string, href: string, subject: {kind: string, key: string}}} CoverageDocument
 * @typedef {{seriesId: string, title: string, documents: CoverageDocument[]}} CoverageRow
 * @typedef {{row: CoverageRow, document: CoverageDocument}} CoveragePlacement
 * @typedef {{rows: CoverageRow[], rowsByWorkId: Map<string, CoverageRow>,
 * placementsByDocId: Map<string, CoveragePlacement>, collator: Intl.Collator}} WorksSnapshot
 */

function compareDocuments(collator, left, right) {
  return collator.compare(left.title, right.title)
    || collator.compare(left.subject.key, right.subject.key)
    || collator.compare(left.docId, right.docId);
}

function placeDocument(snapshot, record, documentHref) {
  const subject = classifyDocsDocumentSubject(record, { folderSupported: true });
  if (subject.kind !== "work") return null;
  const row = snapshot.rowsByWorkId.get(subject.key);
  if (!row) return null;
  return {
    row,
    document: {
      docId: record.doc_id,
      title: record.title,
      href: documentHref(record.doc_id),
      subject
    }
  };
}

/** Join completed Refresh/Context handoffs once for this mounted report.
 * All saved Series establish rows, including empty Series. Only exact Work
 * subjects in supplied membership contribute coverage; labels pass unchanged.
 * @param {Object[]} seriesRecords Saved Series IDs, titles and member Work IDs.
 * @param {Object[]} documents Completed Context management metadata.
 * @param {(docId: string) => string} documentHref Exact Works viewer URL owner.
 * @returns {WorksSnapshot}
 */
export function buildWorksSnapshot(seriesRecords, documents, documentHref) {
  const rows = seriesRecords.map((series) => ({
    seriesId: series.series_id,
    title: series.title,
    documents: []
  }));
  const snapshot = {
    rows,
    rowsByWorkId: new Map(),
    placementsByDocId: new Map(),
    collator: new Intl.Collator("en", { numeric: true, sensitivity: "base" })
  };
  seriesRecords.forEach((series, index) => {
    series.work_ids.forEach((workId) => snapshot.rowsByWorkId.set(workId, rows[index]));
  });
  documents.forEach((record) => {
    const placement = placeDocument(snapshot, record, documentHref);
    if (!placement) return;
    placement.row.documents.push(placement.document);
    snapshot.placementsByDocId.set(record.doc_id, placement);
  });
  rows.forEach((row) => row.documents.sort((left, right) => compareDocuments(snapshot.collator, left, right)));
  rows.sort((left, right) => snapshot.collator.compare(left.title, right.title)
    || snapshot.collator.compare(left.seriesId, right.seriesId));
  return snapshot;
}

/** Update committed Context metadata against the mounted saved membership.
 * No reread/rejoin or Series-order sort. Removal preserves order, and insertion
 * sorts only its destination's document list. Irrelevant changes do not render.
 * @param {WorksSnapshot} snapshot Mounted coverage updated in place.
 * @param {Object} change Provider-owned committed metadata or deletion.
 * @param {(docId: string) => string} documentHref Exact Works viewer URL owner.
 * @returns {boolean} Whether displayed document membership or titles changed.
 */
export function commitWorksDocument(snapshot, change, documentHref) {
  if (change.target.collection !== "works") return false;
  const docId = change.target.doc_id;
  const previous = snapshot.placementsByDocId.get(docId);
  const next = change.deleted ? null : placeDocument(snapshot, change.record, documentHref);
  if (!previous && !next) return false;
  if (previous && next && previous.document.title === next.document.title
    && previous.document.subject.key === next.document.subject.key) return false;
  if (previous) {
    previous.row.documents = previous.row.documents.filter((record) => record.docId !== docId);
    snapshot.placementsByDocId.delete(docId);
  }
  if (next) {
    next.row.documents.push(next.document);
    next.row.documents.sort((left, right) => compareDocuments(snapshot.collator, left, right));
    snapshot.placementsByDocId.set(docId, next);
  }
  return true;
}
