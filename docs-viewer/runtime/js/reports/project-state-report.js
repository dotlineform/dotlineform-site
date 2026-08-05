const REPORT_SCHEMA = "docs_project_state_report_v1";
const LOOKUP_SCHEMA = "docs_project_state_folder_lookup_v1";
const LOCAL_TARGET_PREFIX = "dlf-local:";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function reportService(context) {
  return context && context.reportService && typeof context.reportService.runProjectState === "function"
    ? context.reportService
    : null;
}

function requireArray(value, label) {
  if (!Array.isArray(value)) throw new Error("Project State " + label + " is invalid.");
  return value;
}

function normalizeDocument(value) {
  const target = value && value.target;
  const docId = cleanString(target && target.doc_id);
  const title = cleanString(value && value.title);
  const href = cleanString(value && value.href);
  if (
    cleanString(target && target.scope) !== "dotlineform"
    || cleanString(target && target.sub_scope) !== "projects"
    || !docId
    || !title
    || !href
  ) {
    throw new Error("Project State document target is invalid.");
  }
  return { target, title, href };
}

function normalizeSeries(value) {
  const target = value && value.target;
  const seriesId = cleanString(target && target.target_id);
  const title = cleanString(value && value.title);
  const href = cleanString(value && value.href);
  const workCount = Number(value && value.work_count);
  if (
    cleanString(target && target.family) !== "catalogue"
    || cleanString(target && target.target_type) !== "series"
    || !seriesId
    || !title
    || !href
    || !Number.isInteger(workCount)
    || workCount < 1
  ) {
    throw new Error("Project State Series membership is invalid.");
  }
  return { target, title, href, workCount };
}

function normalizeRow(value) {
  const folder = value && value.folder;
  const key = cleanString(folder && folder.key);
  const label = cleanString(folder && folder.label);
  const href = cleanString(folder && folder.href);
  const states = value && value.states;
  const matchedWorkCount = Number(value && value.matched_work_count);
  if (
    !key.startsWith("projects/")
    || !label.startsWith("/")
    || !href.startsWith(LOCAL_TARGET_PREFIX)
    || !states
    || typeof states !== "object"
    || !Number.isInteger(matchedWorkCount)
    || matchedWorkCount < 0
  ) {
    throw new Error("Project State folder row is invalid.");
  }
  return {
    folder: { key, label, href },
    documents: requireArray(value.documents, "documents").map(normalizeDocument),
    series: requireArray(value.series, "Series").map(normalizeSeries),
    seriesIssues: requireArray(value.series_issues, "Series issues"),
    matchedWorkCount,
    reconciliation: cleanString(states.reconciliation)
  };
}

function normalizeResponse(payload) {
  const report = payload && payload.report;
  const lookup = payload && payload.lookup;
  const generation = cleanString(report && report.generation);
  const generatedAt = cleanString(report && report.generated_at);
  if (
    !payload
    || payload.ok !== true
    || !report
    || report.schema_version !== REPORT_SCHEMA
    || !lookup
    || lookup.schema_version !== LOOKUP_SCHEMA
    || cleanString(lookup.generation) !== generation
    || !generation
    || !generatedAt
  ) {
    throw new Error("Project State report and lookup did not agree.");
  }
  return {
    generatedAt,
    generation,
    summary: report.summary && typeof report.summary === "object" ? report.summary : {},
    rows: requireArray(report.rows, "rows").map(normalizeRow)
  };
}

function appendText(parent, className, text) {
  const node = document.createElement("span");
  node.className = className;
  node.textContent = text;
  parent.appendChild(node);
  return node;
}

function appendLink(parent, label, href) {
  const link = document.createElement("a");
  link.className = "docsViewerReport__cellLink";
  link.href = href;
  link.textContent = label;
  parent.appendChild(link);
  return link;
}

function publicPreviewHref(context, href) {
  const base = cleanString(context && context.publicPreviewBase).replace(/\/+$/, "");
  const path = cleanString(href);
  if (!base || !path.startsWith("/series/")) {
    throw new Error("Project State site preview is not configured.");
  }
  return new URL(path, base + "/").toString();
}

function appendFolderCell(rowNode, row) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  const link = appendLink(cell, row.folder.label.slice(1), "#");
  link.classList.add("docsViewerReport__title");
  link.dataset.docsViewerLocalTarget = row.folder.href.slice(LOCAL_TARGET_PREFIX.length);
  link.dataset.projectFolderKey = row.folder.key;
  rowNode.appendChild(cell);
}

function appendSeriesCell(rowNode, row, context) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  row.series.forEach((series) => {
    appendLink(cell, series.title, publicPreviewHref(context, series.href));
  });
  rowNode.appendChild(cell);
}

function appendDocumentsCell(rowNode, row) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  if (row.documents.length) {
    row.documents.forEach((documentRecord) => {
      const link = appendLink(cell, documentRecord.title, documentRecord.href);
      link.dataset.docsViewerScope = cleanString(documentRecord.target && documentRecord.target.scope);
      link.dataset.docsViewerSubscope = cleanString(documentRecord.target && documentRecord.target.sub_scope);
      link.dataset.docsViewerDocId = cleanString(documentRecord.target && documentRecord.target.doc_id);
    });
  }
  rowNode.appendChild(cell);
}

function renderRows(state) {
  clearNode(state.rowsNode);
  state.emptyNode.hidden = state.rows.length > 0;
  if (!state.rows.length) {
    state.emptyNode.textContent = "No immediate project folders were found.";
    return;
  }
  state.rows.forEach((row) => {
    const rowNode = document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    appendFolderCell(rowNode, row);
    appendSeriesCell(rowNode, row, state.context);
    appendDocumentsCell(rowNode, row);
    state.rowsNode.appendChild(rowNode);
  });
}

function integerSummary(summary, key) {
  const value = Number(summary && summary[key]);
  return Number.isInteger(value) && value >= 0 ? value : 0;
}

function runContext(report) {
  const generated = report.generatedAt.slice(0, 16).replace("T", " ");
  const folders = integerSummary(report.summary, "scanned_folder_count");
  const works = integerSummary(report.summary, "matched_work_count");
  const documents = integerSummary(report.summary, "matched_document_count");
  const folderLabel = folders === 1 ? "folder" : "folders";
  const workLabel = works === 1 ? "Work" : "Works";
  const documentLabel = documents === 1 ? "Doc" : "Docs";
  return generated + " · " + folders + " " + folderLabel + " · " + works + " " + workLabel + " · " + documents + " " + documentLabel;
}

function setBusy(state, busy) {
  state.busy = Boolean(busy);
  state.runButton.disabled = state.busy;
  state.runButton.setAttribute("aria-busy", state.busy ? "true" : "false");
}

function runReport(state) {
  const service = reportService(state.context);
  if (!service) {
    state.statusNode.textContent = "Local docs-management server is not configured.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "Project State could not run in this viewer context.";
    return Promise.resolve();
  }
  setBusy(state, true);
  state.statusNode.textContent = "Running Project State...";
  state.rows = [];
  clearNode(state.rowsNode);
  state.emptyNode.hidden = true;
  return service.runProjectState()
    .then(normalizeResponse)
    .then((report) => {
      state.rows = report.rows;
      state.statusNode.textContent = runContext(report);
      renderRows(state);
    })
    .catch((error) => {
      state.rows = [];
      clearNode(state.rowsNode);
      state.statusNode.textContent = error && error.message
        ? error.message
        : "Project State refresh failed.";
      state.emptyNode.hidden = false;
      state.emptyNode.textContent = "The current Project State run could not complete.";
    })
    .finally(() => {
      setBusy(state, false);
    });
}

function renderShell(root) {
  clearNode(root);
  root.dataset.reportId = "project_state";
  root.dataset.reportColumns = "3";

  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const runButton = document.createElement("button");
  runButton.id = "docsProjectStateReportRun";
  runButton.type = "button";
  runButton.className = "docsViewerReport__button docsViewerReport__button--pill";
  runButton.setAttribute("aria-label", "Run/Refresh");
  runButton.title = "Run/Refresh";
  runButton.textContent = "🔄";
  const status = document.createElement("p");
  status.className = "docsViewerReport__status";
  toolbar.appendChild(runButton);
  toolbar.appendChild(status);

  const table = document.createElement("div");
  table.className = "docsViewerReport__table";
  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  ["Folder", "Series", "Docs"].forEach((label) => {
    appendText(head, "docsViewerReport__headLabel", label);
  });
  const rows = document.createElement("ul");
  rows.className = "docsViewerReport__rows";
  const empty = document.createElement("p");
  empty.className = "docsViewerReport__empty";
  empty.hidden = true;
  table.appendChild(head);
  table.appendChild(rows);
  root.appendChild(toolbar);
  root.appendChild(table);
  root.appendChild(empty);
  return { runButton, statusNode: status, rowsNode: rows, emptyNode: empty };
}

export function mountProjectStateReport(context) {
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({ context, rows: [], busy: false }, nodes);
  state.runButton.addEventListener("click", () => {
    if (!state.busy) runReport(state);
  });
  return runReport(state);
}
