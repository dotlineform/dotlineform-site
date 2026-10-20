/**
 * @typedef {{target: {collection: string, doc_id: string}, title: string, sortTitle: string,
 * href: string, applicableSeriesIds: string[]}} ProjectDocument
 * @typedef {{folder: {key: string, label: string, localTarget: string}, seriesIds: string[],
 * series: {seriesId: string, title: string}[], documents: ProjectDocument[]}} ProjectFolder
 * @typedef {{generatedAt: string, rows: ProjectFolder[], workCount: number, documentCount: number,
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
  });
  return groups;
}

/** Compose one mounted dataset from the service's saved metadata snapshot.
 * Keep every scanned folder. Work references and Gallery mentions contribute
 * Series, which place documents in all folders containing that Series' Works.
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
    workCount: 0,
    documentCount: 0
  };
  const foldersByKey = new Map(rows.map((row) => [row.folder.key, row]));
  const worksById = new Map(inputs.works.map((work) => [work.work_id, work]));
  const foldersBySeries = new Map();
  const seriesByGallery = new Map();
  Object.entries(inputs.series_galleries).forEach(([seriesId, galleryIds]) => {
    galleryIds.forEach((galleryId) => {
      if (!seriesByGallery.has(galleryId)) seriesByGallery.set(galleryId, []);
      seriesByGallery.get(galleryId).push(seriesId);
    });
  });
  inputs.works.forEach((work) => {
    if (!work.project_folder) return;
    const row = foldersByKey.get("projects/" + work.project_folder);
    if (!row) return;
    const seriesIds = seriesById.has(work.series_id) ? [work.series_id] : [];
    snapshot.workCount += 1;
    if (seriesIds.length && !row.seriesIds.includes(work.series_id)) {
      row.seriesIds.push(work.series_id);
      if (!foldersBySeries.has(work.series_id)) foldersBySeries.set(work.series_id, []);
      foldersBySeries.get(work.series_id).push(row);
    }
  });
  rows.forEach((row) => {
    row.seriesIds.sort();
    row.series = row.seriesIds.map((seriesId) => ({ seriesId, title: seriesById.get(seriesId) }));
  });
  inputs.documents.forEach((record) => {
    const placements = new Map();
    const relatedSeries = new Set(record.targets.flatMap((target) => (
      target.kind === "catalogue-work"
        ? [worksById.get(target.id)?.series_id]
        : seriesByGallery.get(target.id) || []
    )));
    relatedSeries.forEach((seriesId) => {
      (foldersBySeries.get(seriesId) || []).forEach((row) => {
        if (!placements.has(row)) placements.set(row, []);
        placements.get(row).push(seriesId);
      });
    });
    if (!placements.size) return;
    const document = {
      target: { collection: "works", doc_id: record.doc_id },
      title: record.title,
      sortTitle: record.title.toLowerCase(),
      href: documentHref(record.doc_id)
    };
    placements.forEach((applicableSeriesIds, row) => row.documents.push({ ...document, applicableSeriesIds }));
    snapshot.documentCount += 1;
  });
  rows.forEach((row) => row.documents.sort(compareDocuments));
  snapshot.groups = prepareGroups(rows);
  return snapshot;
}
