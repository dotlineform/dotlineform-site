import { classifyDocsDocumentSubject } from "../shared/docs-document-subject.js";

/**
 * @typedef {{target: {collection: string, doc_id: string}, title: string, sortTitle: string,
 * href: string, declaredSubject: {kind: string, key: string}, applicableSeriesIds: string[]}} ProjectDocument
 * @typedef {{folder: {key: string, label: string, localTarget: string}, seriesIds: string[],
 * series: {seriesId: string, title: string}[], documents: ProjectDocument[]}} ProjectFolder
 * @typedef {{row: ProjectFolder, document: ProjectDocument}} DocumentPlacement
 * @typedef {{generatedAt: string, rows: ProjectFolder[], foldersByKey: Map<string, ProjectFolder>,
 * worksById: Map<string, {row: ProjectFolder, seriesIds: string[]}>,
 * placementsByDocId: Map<string, DocumentPlacement>, workCount: number,
 * groups: {folder: Object[], series: Object[]}}} ProjectStateSnapshot
 */

function compareText(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function compareDocuments(left, right) {
  return compareText(left.sortTitle, right.sortTitle)
    || compareText(left.title, right.title)
    || compareText(left.target.doc_id, right.target.doc_id);
}

function placeDocument(snapshot, record, documentHref) {
  const subject = classifyDocsDocumentSubject(record, { folderSupported: true });
  const work = subject.kind === "work" ? snapshot.worksById.get(subject.key) : null;
  const row = subject.kind === "folder" ? snapshot.foldersByKey.get(subject.key) : work?.row;
  if (!row) return null;
  return {
    row,
    document: {
      target: { collection: "works", doc_id: record.doc_id },
      title: record.title,
      sortTitle: record.title.toLowerCase(),
      href: documentHref(record.doc_id),
      declaredSubject: subject,
      applicableSeriesIds: subject.kind === "folder" ? row.seriesIds : work.seriesIds
    }
  };
}

function projectionRow(row, series, documents) {
  const visibleTitle = (record) => record.title.trim().replace(/\s+/g, " ");
  const text = {
    folder: row.folder.label,
    series: series.map(visibleTitle).join("; "),
    docs: documents.map(visibleTitle).join("; ")
  };
  return {
    folder: row.folder,
    folderKey: row.folder.key,
    documents,
    series,
    text,
    identities: {
      folder: row.folder.key,
      series: series.map((record) => record.seriesId).join(";"),
      docs: documents.map((record) => record.target.doc_id).join(";")
    },
    searchText: [text.folder, text.series, text.docs].join(" ").toLocaleLowerCase()
  };
}

function prepareGroups(rows) {
  const groups = { folder: [], series: [] };
  rows.forEach((row) => {
    const folderRow = projectionRow(row, row.series, row.documents);
    groups.folder.push(folderRow);
    if (!row.series.length) {
      groups.series.push(folderRow);
      return;
    }
    row.series.forEach((series) => {
      groups.series.push(projectionRow(row, [series], row.documents.filter(
        (record) => record.applicableSeriesIds.includes(series.seriesId)
      )));
    });
    const unrouted = row.documents.filter((record) => !record.applicableSeriesIds.length);
    if (unrouted.length) groups.series.push(projectionRow(row, [], unrouted));
  });
  return groups;
}

/** Compose one mounted dataset from the service's completed, read-only handoff.
 * Keep every scanned folder and place Folder/Work subjects against saved Work
 * membership. No additional requests, response audits or persistent caches.
 * @param {Object} inputs Completed folders, document metadata, Works and Series.
 * @param {(docId: string) => string} documentHref Exact Works viewer URL owner.
 * @returns {ProjectStateSnapshot}
 */
export function buildProjectStateSnapshot(inputs, documentHref) {
  const seriesById = new Map(inputs.series.map((record) => [record.series_id, record.title]));
  const rows = inputs.folders.map((folder) => ({
    folder: {
      key: folder.key,
      label: folder.key.slice("projects/".length),
      localTarget: folder.local_target
    },
    seriesIds: [],
    documents: []
  }));
  const snapshot = {
    generatedAt: inputs.generated_at,
    rows,
    foldersByKey: new Map(rows.map((row) => [row.folder.key, row])),
    worksById: new Map(),
    placementsByDocId: new Map(),
    workCount: 0
  };
  inputs.works.forEach((work) => {
    if (!work.project_folder) return;
    const row = snapshot.foldersByKey.get("projects/" + work.project_folder);
    if (!row) return;
    const seriesIds = seriesById.has(work.series_id) ? [work.series_id] : [];
    snapshot.worksById.set(work.work_id, { row, seriesIds });
    snapshot.workCount += 1;
    if (seriesIds.length && !row.seriesIds.includes(work.series_id)) row.seriesIds.push(work.series_id);
  });
  rows.forEach((row) => {
    row.seriesIds.sort();
    row.series = row.seriesIds.map((seriesId) => ({ seriesId, title: seriesById.get(seriesId) }));
  });
  inputs.documents.forEach((record) => {
    const placement = placeDocument(snapshot, record, documentHref);
    if (!placement) return;
    placement.row.documents.push(placement.document);
    snapshot.placementsByDocId.set(record.doc_id, placement);
  });
  rows.forEach((row) => row.documents.sort(compareDocuments));
  snapshot.groups = prepareGroups(rows);
  return snapshot;
}

/** Apply committed metadata using the same placement owner and last scan's Works.
 * Removal preserves document order; only an insertion's folder needs sorting.
 * @param {ProjectStateSnapshot} snapshot Mounted dataset updated in place.
 * @param {Object} change Provider-owned committed document metadata or deletion.
 * @param {(docId: string) => string} documentHref Exact Works viewer URL owner.
 * @returns {boolean} Whether displayed document membership or titles changed.
 */
export function commitProjectStateDocument(snapshot, change, documentHref) {
  if (change.target.collection !== "works") return false;
  const docId = change.target.doc_id;
  const previous = snapshot.placementsByDocId.get(docId);
  const next = change.deleted ? null : placeDocument(snapshot, change.record, documentHref);
  if (!previous && !next) return false;
  if (previous && next && previous.document.title === next.document.title
    && previous.document.declaredSubject.kind === next.document.declaredSubject.kind
    && previous.document.declaredSubject.key === next.document.declaredSubject.key) return false;
  if (previous) {
    previous.row.documents = previous.row.documents.filter((record) => record.target.doc_id !== docId);
    snapshot.placementsByDocId.delete(docId);
  }
  if (next) {
    next.row.documents.push(next.document);
    next.row.documents.sort(compareDocuments);
    snapshot.placementsByDocId.set(docId, next);
  }
  snapshot.groups = prepareGroups(snapshot.rows);
  return true;
}
