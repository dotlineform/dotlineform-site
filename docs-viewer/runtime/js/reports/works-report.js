import { classifyDocsDocumentSubject } from "../shared/docs-document-subject.js";
import { appendProjectSubjectIcon } from "./project-subject-icons.js";
const CATALOGUE_SCHEMA = "catalogue_work_document_coverage_v1";
const WORKS_COLLECTION = "works";
const SERIES_ID_PATTERN = /^[0-9]{3}$/;
const WORK_ID_PATTERN = /^[0-9]{5}$/;
const DOC_ID_PATTERN = /^d-[0-9]{8}-[0-9]{6}-[0-9a-f]{6}$/;
function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function exactKeys(value, expected) {
  return Boolean(value && typeof value === "object" && !Array.isArray(value))
    && Object.keys(value).sort().join(",") === expected.slice().sort().join(",");
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

/** Normalize only the refreshed Catalogue identities, labels and membership used here. */
export function normalizeWorksCatalogueManifest(payload) {
  const message = "Work Document Coverage manifest is invalid.";
  if (payload?.header?.schema !== CATALOGUE_SCHEMA || !Array.isArray(payload.series)) {
    throw new Error(message);
  }
  const seenSeries = new Set();
  const seenWorks = new Set();
  return payload.series.map((value) => {
    if (!value || typeof value.series_id !== "string" || !SERIES_ID_PATTERN.test(value.series_id)
      || typeof value.title !== "string" || !cleanString(value.title)
      || !Array.isArray(value.work_ids) || seenSeries.has(value.series_id)) {
      throw new Error(message);
    }
    seenSeries.add(value.series_id);
    const workIds = value.work_ids.map((workId) => {
      if (typeof workId !== "string" || !WORK_ID_PATTERN.test(workId) || seenWorks.has(workId)) {
        throw new Error(message);
      }
      seenWorks.add(workId);
      return workId;
    });
    return { seriesId: value.series_id, title: value.title, workIds };
  });
}

function normalizeWorkDocument(value) {
  const keys = value && typeof value === "object" && !Array.isArray(value)
    ? Object.keys(value).filter((key) => !["draft", "has_thumbnail", "subject"].includes(key)).sort().join(",")
    : "";
  if (keys !== "doc_id,last_updated,title") {
    throw new Error("Working Works manifest is invalid.");
  }
  if (Object.hasOwn(value, "draft") && typeof value.draft !== "boolean") {
    throw new Error("Working Works manifest is invalid.");
  }
  if (Object.hasOwn(value, "has_thumbnail") && typeof value.has_thumbnail !== "boolean") {
    throw new Error("Working Works manifest is invalid.");
  }
  const docId = cleanString(value.doc_id);
  const title = cleanString(value.title);
  if (
    !DOC_ID_PATTERN.test(docId)
    || !title
    || typeof value.last_updated !== "string"
    || !/^\d{4}-\d{2}-\d{2}$/.test(value.last_updated)
  ) {
    throw new Error("Working Works manifest is invalid.");
  }
  const subject = classifyDocsDocumentSubject(value, {
    folderSupported: true,
    errorMessage: "Working Works manifest is invalid."
  });
  return { docId, subject, title };
}

export function normalizeWorksDocumentsManifest(payload) {
  if (
    !exactKeys(payload, ["docs"])
    || !Array.isArray(payload.docs)
  ) {
    throw new Error("Working Works manifest is invalid.");
  }
  const seen = new Set();
  return payload.docs.map((value) => {
    const documentRecord = normalizeWorkDocument(value);
    if (seen.has(documentRecord.docId)) {
      throw new Error("Working Works manifest is invalid.");
    }
    seen.add(documentRecord.docId);
    return documentRecord;
  });
}

function compareText(collator, left, right) {
  return collator.compare(cleanString(left), cleanString(right));
}

function compareDocuments(collator, left, right) {
  return compareText(collator, left.title, right.title)
    || compareText(collator, left.subject.kind, right.subject.kind)
    || compareText(collator, left.subject.key, right.subject.key)
    || compareText(collator, left.docId, right.docId);
}

/** Join generated Context subjects to refreshed Series membership, retaining empty rows. */
export function composeWorksProjection(seriesRecords, workDocuments) {
  const collator = new Intl.Collator("en", { numeric: true, sensitivity: "base" });
  const catalogueSeries = new Map();
  seriesRecords.forEach((series) => {
    catalogueSeries.set(series.seriesId, series);
  });
  const catalogueWorks = new Map();
  seriesRecords.forEach((series) => {
    series.workIds.forEach((workId) => catalogueWorks.set(workId, series.seriesId));
  });
  const documentsBySeries = new Map();
  catalogueSeries.forEach((_series, seriesId) => documentsBySeries.set(seriesId, new Map()));
  workDocuments.forEach((documentRecord) => {
    const subject = documentRecord.subject;
    if (subject.kind !== "work" || !catalogueWorks.has(subject.key)) return;
    const seriesId = catalogueWorks.get(subject.key);
    documentsBySeries.get(seriesId).set(documentRecord.docId, {
      docId: documentRecord.docId,
      subject: { kind: subject.kind, key: subject.key },
      title: documentRecord.title
    });
  });
  const rows = Array.from(catalogueSeries.values()).map((series) => {
    const documents = Array.from(documentsBySeries.get(series.seriesId).values());
    documents.sort((left, right) => compareDocuments(collator, left, right));
    return { documents, seriesId: series.seriesId, title: series.title };
  });
  rows.sort((left, right) => {
    return compareText(collator, left.title, right.title)
      || compareText(collator, left.seriesId, right.seriesId);
  });
  return { rowCount: rows.length, rows };
}

function configuredWorkingWorksManifestUrl(context) {
  const collections = context.workspaceConfig?.collections || [];
  const matches = collections.filter((record) => {
    return cleanString(record && record.collection).toLowerCase()
      === WORKS_COLLECTION;
  });
  const url = matches.length === 1
    ? cleanString(matches[0].manifest_url || matches[0].manifestUrl)
    : "";
  if (!url) throw new Error("Working Works manifest is not configured.");
  return url;
}

function fetchJson(url, message) {
  return fetch(url, {
    cache: "no-store",
    headers: { Accept: "application/json" }
  }).then((response) => {
    if (!response.ok) throw new Error(message);
    return response.json();
  }).catch((error) => {
    throw new Error(error && error.message ? error.message : message, { cause: error });
  });
}

function loadWorksInputs(context) {
  return Promise.all([
    context.reportService.readWorkDocumentCoverage().then(normalizeWorksCatalogueManifest),
    fetchJson(
      configuredWorkingWorksManifestUrl(context),
      "Failed to load Working Works manifest."
    ).then(normalizeWorksDocumentsManifest)
  ]);
}

function workDocumentHref(context, docId) {
  if (typeof context.viewerUrlForDocument !== "function") {
    throw new Error("Working Works document links are not configured.");
  }
  const raw = cleanString(context.viewerUrlForDocument(
    docId,
    { collection: "works" }
  ));
  const url = new URL(raw, "http://docs.local");
  if (
    url.searchParams.get("doc") !== docId || url.searchParams.get("collection") !== "works"
  ) {
    throw new Error("Working Works document links are not configured.");
  }
  return url.origin === "http://docs.local"
    ? url.pathname + url.search + url.hash
    : url.toString();
}

function appendDocumentsCell(state, rowNode, row) {
  const cell = rowNode.ownerDocument.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  if (!row.documents.length) cell.setAttribute("aria-label", "No Work documents");
  row.documents.forEach((documentRecord) => {
    const link = rowNode.ownerDocument.createElement("a");
    link.className = "docsViewerReport__cellLink";
    link.dataset.projectDocId = documentRecord.docId;
    link.dataset.projectSubjectKind = documentRecord.subject.kind;
    link.dataset.projectSubjectKey = documentRecord.subject.key;
    link.href = workDocumentHref(state.context, documentRecord.docId);
    appendProjectSubjectIcon(link, documentRecord.subject.kind);
    const label = rowNode.ownerDocument.createElement("span");
    label.textContent = documentRecord.title;
    link.appendChild(label);
    link.setAttribute(
      "aria-label",
      documentRecord.title + ", " + documentRecord.subject.kind + " subject "
        + documentRecord.subject.key
    );
    cell.appendChild(link);
  });
  rowNode.appendChild(cell);
}

function renderProjection(state, projection) {
  clearNode(state.rowsNode);
  state.emptyNode.hidden = projection.rows.length > 0;
  state.emptyNode.textContent = projection.rows.length ? "" : "No Series were found in refreshed Catalogue data.";
  projection.rows.forEach((row) => {
    const rowNode = state.rowsNode.ownerDocument.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.dataset.seriesId = row.seriesId;
    const seriesTitle = rowNode.ownerDocument.createElement("span");
    seriesTitle.className = "docsViewerReport__cellStack docsViewerReport__title";
    seriesTitle.dataset.seriesId = row.seriesId;
    seriesTitle.textContent = row.title;
    rowNode.appendChild(seriesTitle);
    appendDocumentsCell(state, rowNode, row);
    state.rowsNode.appendChild(rowNode);
  });
  state.statusNode.textContent = projection.rowCount === 1
    ? "1 Series"
    : projection.rowCount + " Series";
}

function loadWorksReport(state) {
  clearNode(state.rowsNode);
  state.emptyNode.hidden = true;
  state.statusNode.textContent = "Loading Works...";
  return loadWorksInputs(state.context).then((inputs) => {
    state.inputs = inputs;
    renderProjection(state, composeWorksProjection(inputs[0], inputs[1]));
  }).catch((error) => {
    clearNode(state.rowsNode);
    state.statusNode.textContent = error && error.message
      ? error.message
      : "Works report failed to load.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "The current Works report could not complete.";
  });
}

function renderShell(root) {
  root.dataset.reportId = "works";
  root.dataset.reportColumns = "2";
  root.innerHTML = [
    '<p class="docsViewerReport__status"></p>',
    '<div class="docsViewerReport__table"><div class="docsViewerReport__head">',
    '<span class="docsViewerReport__headLabel">Series</span>',
    '<span class="docsViewerReport__headLabel">Docs</span></div>',
    '<ul class="docsViewerReport__rows"></ul></div>',
    '<p class="docsViewerReport__empty" hidden></p>'
  ].join("");
  return {
    emptyNode: root.querySelector(".docsViewerReport__empty"),
    rowsNode: root.querySelector(".docsViewerReport__rows"),
    statusNode: root.querySelector(".docsViewerReport__status")
  };
}

export function mountWorksReport(context) {
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({ context }, nodes);
  if (context.collectionProvider && context.collectionProvider.subscribeDocumentChanges) context.collectionProvider.subscribeDocumentChanges(function (change) {
    if (!context.reportRoot.isConnected || !state.inputs || change.target.collection !== "works") return;
    var previous = state.inputs[1].find(function (record) { return record.docId === change.target.doc_id; });
    if (change.deleted && !previous) return;
    var subject = change.deleted ? null : classifyDocsDocumentSubject(change.record, { folderSupported: true });
    if (previous && !change.deleted && previous.title === change.record.title && previous.subject.kind === subject.kind && previous.subject.key === subject.key) return;
    state.inputs[1] = state.inputs[1].filter(function (record) { return record.docId !== change.target.doc_id; });
    if (!change.deleted) state.inputs[1].push({ docId: change.target.doc_id, title: change.record.title,
      subject: subject });
    renderProjection(state, composeWorksProjection(state.inputs[0], state.inputs[1]));
  });
  return loadWorksReport(state);
}
