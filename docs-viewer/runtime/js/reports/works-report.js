import { normalizeDocsViewerAuthoringSubject } from "../management/docs-viewer-management-document-subject.js";
import { appendProjectSubjectIcon } from "./project-subject-icons.js";

const SERIES_SCHEMA = "studio_catalogue_lookup_series_search_v1";
const WORK_SCHEMA = "studio_catalogue_lookup_work_search_v1";
const PROJECTS_SCOPE = "dotlineform";
const PROJECTS_SUB_SCOPE = "projects";
const PROJECTS_CUSTOMISATION = "dotlineform_projects";
const PROJECTS_REPORT_DOC_ID = "d-20260801-073826-8865a8";
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

function normalizeLookupPayload(payload, options) {
  const settings = options || {};
  if (
    !exactKeys(payload, ["header", "items"])
    || !exactKeys(payload.header, ["count", "schema"])
    || payload.header.schema !== settings.schema
    || !Number.isInteger(payload.header.count)
    || payload.header.count < 0
    || !Array.isArray(payload.items)
    || payload.header.count !== payload.items.length
  ) {
    throw new Error(settings.errorMessage);
  }
  const seen = new Set();
  return payload.items.map((value) => {
    const item = settings.normalizeItem(value);
    const identity = item[settings.identityKey];
    if (seen.has(identity)) throw new Error(settings.errorMessage);
    seen.add(identity);
    return item;
  });
}

function normalizeSeriesItem(value) {
  if (!exactKeys(value, ["primary_work_id", "series_id", "series_type", "status", "title"])) {
    throw new Error("Works Series lookup is invalid.");
  }
  const seriesId = cleanString(value.series_id);
  const title = cleanString(value.title);
  const status = cleanString(value.status);
  if (
    !SERIES_ID_PATTERN.test(seriesId)
    || !title
    || !status
    || typeof value.primary_work_id !== "string"
    || typeof value.series_type !== "string"
  ) {
    throw new Error("Works Series lookup is invalid.");
  }
  return { seriesId, status, title };
}

function normalizeWorkItem(value) {
  if (!exactKeys(value, ["series_ids", "status", "title", "work_id", "year_display"])) {
    throw new Error("Works Work lookup is invalid.");
  }
  const workId = cleanString(value.work_id);
  const title = cleanString(value.title);
  const status = cleanString(value.status);
  const seriesIds = Array.isArray(value.series_ids) ? value.series_ids.slice() : [];
  if (
    !WORK_ID_PATTERN.test(workId)
    || !title
    || !status
    || typeof value.year_display !== "string"
    || !Array.isArray(value.series_ids)
    || seriesIds.some((seriesId) => {
      return typeof seriesId !== "string" || !SERIES_ID_PATTERN.test(seriesId);
    })
    || new Set(seriesIds).size !== seriesIds.length
  ) {
    throw new Error("Works Work lookup is invalid.");
  }
  return { seriesIds, status, title, workId };
}

export function normalizeWorksSeriesLookup(payload) {
  return normalizeLookupPayload(payload, {
    errorMessage: "Works Series lookup is invalid.",
    identityKey: "seriesId",
    normalizeItem: normalizeSeriesItem,
    schema: SERIES_SCHEMA
  });
}

export function normalizeWorksWorkLookup(payload) {
  return normalizeLookupPayload(payload, {
    errorMessage: "Works Work lookup is invalid.",
    identityKey: "workId",
    normalizeItem: normalizeWorkItem,
    schema: WORK_SCHEMA
  });
}

function normalizeProjectDocument(value) {
  if (!exactKeys(value, ["authoring_subject", "doc_id", "last_updated", "title", "ui_status"])) {
    throw new Error("Works Projects manifest is invalid.");
  }
  const docId = cleanString(value.doc_id);
  const title = cleanString(value.title);
  if (
    !DOC_ID_PATTERN.test(docId)
    || !title
    || typeof value.last_updated !== "string"
    || typeof value.ui_status !== "string"
  ) {
    throw new Error("Works Projects manifest is invalid.");
  }
  const subject = normalizeDocsViewerAuthoringSubject(value.authoring_subject, {
    errorMessage: "Works Projects manifest is invalid."
  });
  return { docId, subject, title };
}

export function normalizeWorksProjectsManifest(payload) {
  if (
    !exactKeys(payload, ["customisation", "docs", "subject_generation"])
    || !exactKeys(payload.customisation, ["data", "id"])
    || payload.customisation.id !== PROJECTS_CUSTOMISATION
    || !payload.customisation.data
    || typeof payload.customisation.data !== "object"
    || Array.isArray(payload.customisation.data)
    || typeof payload.subject_generation !== "string"
    || !payload.subject_generation.startsWith("sha256:")
    || !Array.isArray(payload.docs)
  ) {
    throw new Error("Works Projects manifest is invalid.");
  }
  const seen = new Set();
  return payload.docs.map((value) => {
    const documentRecord = normalizeProjectDocument(value);
    if (seen.has(documentRecord.docId)) {
      throw new Error("Works Projects manifest is invalid.");
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

export function composeWorksProjection(seriesRecords, workRecords, projectDocuments) {
  const collator = new Intl.Collator("en", { numeric: true, sensitivity: "base" });
  const publishedSeries = new Map();
  seriesRecords.forEach((series) => {
    if (series.status === "published") publishedSeries.set(series.seriesId, series);
  });
  const publishedWorks = new Map();
  workRecords.forEach((work) => {
    if (work.status === "published") publishedWorks.set(work.workId, work);
  });
  const documentsBySeries = new Map();
  publishedSeries.forEach((_series, seriesId) => documentsBySeries.set(seriesId, new Map()));
  projectDocuments.forEach((documentRecord) => {
    const subject = documentRecord.subject;
    if (subject.state !== "valid") return;
    let seriesIds = [];
    if (subject.kind === "series" && publishedSeries.has(subject.key)) {
      seriesIds = [subject.key];
    } else if (subject.kind === "work" && publishedWorks.has(subject.key)) {
      seriesIds = publishedWorks.get(subject.key).seriesIds.filter((seriesId) => {
        return publishedSeries.has(seriesId);
      });
    }
    seriesIds.forEach((seriesId) => {
      documentsBySeries.get(seriesId).set(documentRecord.docId, {
        docId: documentRecord.docId,
        subject: { kind: subject.kind, key: subject.key },
        title: documentRecord.title
      });
    });
  });
  const rows = Array.from(publishedSeries.values()).map((series) => {
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

function configuredProjectsManifestUrl(context) {
  const configs = Array.isArray(context && context.scopeConfigs) ? context.scopeConfigs : [];
  const scopeMatches = configs.filter((config) => {
    return cleanString(config && (config.scope_id || config.scopeId)).toLowerCase() === PROJECTS_SCOPE;
  });
  const subScopes = scopeMatches.length === 1 && Array.isArray(scopeMatches[0].subScopes)
    ? scopeMatches[0].subScopes
    : [];
  const matches = subScopes.filter((record) => {
    return cleanString(record && (record.sub_scope || record.subScope)).toLowerCase()
      === PROJECTS_SUB_SCOPE;
  });
  const url = matches.length === 1
    ? cleanString(matches[0].manifest_url || matches[0].manifestUrl)
    : "";
  if (!url) throw new Error("Works Projects manifest is not configured.");
  return url;
}

function studioReadUrl(context, key) {
  const base = cleanString(context && context.studioBaseUrl).replace(/\/+$/, "");
  let studio;
  try {
    studio = new URL(base);
  } catch (error) {
    throw new Error("Local Studio is not configured.", { cause: error });
  }
  if (
    studio.protocol !== "http:"
    || !["127.0.0.1", "localhost", "::1", "[::1]"].includes(studio.hostname)
    || studio.username
    || studio.password
    || studio.pathname !== "/"
    || studio.search
    || studio.hash
  ) {
    throw new Error("Local Studio is not configured.");
  }
  const url = new URL("/studio/api/catalogue/read", studio.origin);
  url.searchParams.set("key", key);
  return url.toString();
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

function loadWorksProjection(context) {
  return Promise.all([
    fetchJson(
      studioReadUrl(context, "catalogue_lookup_series_search"),
      "Failed to load Works Series lookup."
    ).then(normalizeWorksSeriesLookup),
    fetchJson(
      studioReadUrl(context, "catalogue_lookup_work_search"),
      "Failed to load Works Work lookup."
    ).then(normalizeWorksWorkLookup),
    fetchJson(
      configuredProjectsManifestUrl(context),
      "Failed to load Works Projects manifest."
    ).then(normalizeWorksProjectsManifest)
  ]).then((inputs) => composeWorksProjection(inputs[0], inputs[1], inputs[2]));
}

function seriesHref(context, seriesId) {
  const base = cleanString(context && context.publicPreviewBase).replace(/\/+$/, "");
  let preview;
  try {
    preview = new URL(base);
  } catch (error) {
    throw new Error("Local site preview is not configured.", { cause: error });
  }
  if (!preview.hostname || !["http:", "https:"].includes(preview.protocol)) {
    throw new Error("Local site preview is not configured.");
  }
  return new URL("/series/?series=" + encodeURIComponent(seriesId), preview.origin).toString();
}

function projectDocumentHref(context, docId) {
  if (typeof context.viewerUrlForScope !== "function") {
    throw new Error("Projects document links are not configured.");
  }
  const raw = cleanString(context.viewerUrlForScope(
    PROJECTS_SCOPE,
    PROJECTS_REPORT_DOC_ID,
    { manage: true }
  ));
  const url = new URL(raw, "http://docs.local");
  if (
    url.searchParams.get("scope") !== PROJECTS_SCOPE
    || url.searchParams.get("doc") !== PROJECTS_REPORT_DOC_ID
  ) {
    throw new Error("Projects document links are not configured.");
  }
  url.searchParams.set("subdoc", docId);
  return url.origin === "http://docs.local"
    ? url.pathname + url.search + url.hash
    : url.toString();
}

function appendDocumentsCell(state, rowNode, row) {
  const cell = rowNode.ownerDocument.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  if (!row.documents.length) cell.setAttribute("aria-label", "No Project documents");
  row.documents.forEach((documentRecord) => {
    const link = rowNode.ownerDocument.createElement("a");
    link.className = "docsViewerReport__cellLink";
    link.dataset.projectDocId = documentRecord.docId;
    link.dataset.projectSubjectKind = documentRecord.subject.kind;
    link.dataset.projectSubjectKey = documentRecord.subject.key;
    link.href = projectDocumentHref(state.context, documentRecord.docId);
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
  state.emptyNode.textContent = projection.rows.length ? "" : "No published Series were found.";
  projection.rows.forEach((row) => {
    const rowNode = state.rowsNode.ownerDocument.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.dataset.seriesId = row.seriesId;
    const seriesLink = rowNode.ownerDocument.createElement("a");
    seriesLink.className = "docsViewerReport__cellLink docsViewerReport__title";
    seriesLink.dataset.seriesId = row.seriesId;
    seriesLink.href = seriesHref(state.context, row.seriesId);
    seriesLink.textContent = row.title;
    rowNode.appendChild(seriesLink);
    appendDocumentsCell(state, rowNode, row);
    state.rowsNode.appendChild(rowNode);
  });
  state.statusNode.textContent = projection.rowCount === 1
    ? "1 published Series"
    : projection.rowCount + " published Series";
}

function setBusy(state, busy) {
  state.busy = Boolean(busy);
  state.refreshButton.disabled = state.busy;
  state.refreshButton.setAttribute("aria-busy", state.busy ? "true" : "false");
}

function refreshWorksReport(state) {
  clearNode(state.rowsNode);
  state.emptyNode.hidden = true;
  state.statusNode.textContent = "Loading Works...";
  setBusy(state, true);
  return loadWorksProjection(state.context).then((projection) => {
    renderProjection(state, projection);
  }).catch((error) => {
    clearNode(state.rowsNode);
    state.statusNode.textContent = error && error.message
      ? error.message
      : "Works refresh failed.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "The current Works report could not complete.";
  }).finally(() => {
    setBusy(state, false);
  });
}

function renderShell(root) {
  root.dataset.reportId = "works";
  root.dataset.reportColumns = "2";
  root.innerHTML = [
    '<div class="docsViewerReport__toolbar">',
    '<button id="docsWorksReportRefresh" type="button"',
    ' class="docsViewerReport__button docsViewerReport__button--pill"',
    ' aria-label="Run/Refresh" title="Run/Refresh">🔄</button></div>',
    '<p class="docsViewerReport__status"></p>',
    '<div class="docsViewerReport__table"><div class="docsViewerReport__head">',
    '<span class="docsViewerReport__headLabel">Series</span>',
    '<span class="docsViewerReport__headLabel">Docs</span></div>',
    '<ul class="docsViewerReport__rows"></ul></div>',
    '<p class="docsViewerReport__empty" hidden></p>'
  ].join("");
  return {
    emptyNode: root.querySelector(".docsViewerReport__empty"),
    refreshButton: root.querySelector("#docsWorksReportRefresh"),
    rowsNode: root.querySelector(".docsViewerReport__rows"),
    statusNode: root.querySelector(".docsViewerReport__status")
  };
}

export function mountWorksReport(context) {
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({ busy: false, context }, nodes);
  state.refreshButton.addEventListener("click", () => {
    if (!state.busy) refreshWorksReport(state);
  });
  return refreshWorksReport(state);
}
