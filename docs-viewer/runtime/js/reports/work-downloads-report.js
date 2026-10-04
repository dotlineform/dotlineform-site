import { buildViewerUrl } from "../shared/docs-viewer-router.js";
import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

const REPORT_SCHEMA = "docs_work_downloads_report_v1";
const WORK_ID_PATTERN = /^[0-9]{5}$/;
const SORTER = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

function exactKeys(value, keys) {
  return value && typeof value === "object" && !Array.isArray(value)
    && Object.keys(value).sort().join(",") === keys;
}

function isFilename(value) {
  return typeof value === "string" && value.length > 0 && value === value.trim()
    && ![".", ".."].includes(value) && !value.includes("/") && !value.includes("\\")
    && !Array.from(value).some((character) => character.charCodeAt(0) < 32 || character.charCodeAt(0) === 127);
}

function workText(row) {
  return row.work ? `${row.work.title} [${row.work.filename}]` : "";
}

/** Validate exact Work/file matches, then sort the two-column presentation. */
export function normalizeWorkDownloadsResponse(payload) {
  const report = payload && payload.report;
  if (!payload || payload.ok !== true || !exactKeys(report, "rows,schema_version")
    || report.schema_version !== REPORT_SCHEMA || !Array.isArray(report.rows)) {
    throw new Error("Work Downloads report is invalid.");
  }
  const rows = report.rows.map((row) => {
    if (!exactKeys(row, "file,work") || (row.file !== null && !isFilename(row.file))) {
      throw new Error("Work Downloads row is invalid.");
    }
    if (row.work !== null && (!exactKeys(row.work, "filename,title,work_id")
      || typeof row.work.work_id !== "string" || !WORK_ID_PATTERN.test(row.work.work_id)
      || typeof row.work.title !== "string" || !row.work.title.trim() || !isFilename(row.work.filename)
      || (row.file !== null && row.file !== row.work.filename))) {
      throw new Error("Work Downloads Work reference is invalid.");
    }
    if (row.work === null && row.file === null) throw new Error("Work Downloads row is empty.");
    return row;
  });
  return rows.sort((left, right) => {
    if (Boolean(left.work) !== Boolean(right.work)) return left.work ? -1 : 1;
    return SORTER.compare(workText(left), workText(right))
      || SORTER.compare(left.file || "", right.file || "")
      || (left.work?.work_id || "").localeCompare(right.work?.work_id || "");
  });
}

function reportService(context) {
  const service = context.reportService;
  if (!service || typeof service.runWorkDownloads !== "function" || typeof service.openWorkDownload !== "function") {
    throw new Error("Local docs-management server is not configured.");
  }
  return service;
}

function appendCell(state, rowNode, text, href, filename) {
  const cell = state.document.createElement("span");
  cell.setAttribute("role", "cell");
  if (text) {
    const link = state.document.createElement("a");
    link.className = "docsViewerReport__cellLink";
    link.textContent = text;
    link.href = href;
    if (filename) link.dataset.workDownloadFilename = filename;
    cell.appendChild(link);
  }
  rowNode.appendChild(cell);
}

function renderRows(state, rows) {
  state.rowsNode.replaceChildren();
  state.emptyNode.hidden = rows.length > 0;
  const workspace = state.context.workspaceConfig;
  if (rows.some((row) => row.work) && (!workspace?.viewerBaseUrl
    || !workspace.collections.some((entry) => entry.collection === "catalogue"))) {
    throw new Error("Working Catalogue is not configured.");
  }
  rows.forEach((row) => {
    const rowNode = state.document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.setAttribute("role", "row");
    const href = row.work ? buildViewerUrl({
      viewerBaseUrl: workspace.viewerBaseUrl,
      origin: new URL(state.document.baseURI).origin,
      docId: row.work.work_id,
      collection: "catalogue"
    }) : "";
    appendCell(state, rowNode, workText(row), href);
    appendCell(state, rowNode, row.file || "", "#", row.file);
    state.rowsNode.appendChild(rowNode);
  });
}

function setBusy(state, busy) {
  state.busy = busy;
  state.runButton.disabled = busy;
  state.runButton.setAttribute("aria-busy", busy ? "true" : "false");
  state.rowsNode.querySelectorAll("a").forEach((link) => {
    if (busy) link.setAttribute("aria-disabled", "true");
    else link.removeAttribute("aria-disabled");
  });
}

async function runReport(state) {
  setBusy(state, true);
  state.rowsNode.replaceChildren();
  state.emptyNode.hidden = true;
  state.statusNode.textContent = "Running Work Downloads...";
  try {
    const payload = await reportService(state.context).runWorkDownloads();
    renderRows(state, normalizeWorkDownloadsResponse(payload));
    state.statusNode.textContent = "";
  } catch (error) {
    state.rowsNode.replaceChildren();
    state.statusNode.textContent = error.message || "Work Downloads refresh failed.";
  } finally {
    setBusy(state, false);
  }
}

async function openFile(state, filename) {
  setBusy(state, true);
  state.statusNode.textContent = "";
  try {
    await reportService(state.context).openWorkDownload(filename);
  } catch (error) {
    state.statusNode.textContent = error.message || "Open in Finder failed.";
  } finally {
    setBusy(state, false);
  }
}

function renderShell(root) {
  const document = root.ownerDocument;
  root.replaceChildren();
  root.dataset.reportId = "work_downloads";
  root.dataset.reportColumns = "2";
  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const runButton = document.createElement("button");
  runButton.type = "button";
  runButton.className = "docsViewer__toolbarIconButton";
  runButton.setAttribute("aria-label", "Run/Refresh");
  runButton.title = "Run/Refresh";
  runButton.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));
  toolbar.appendChild(runButton);
  const statusNode = document.createElement("p");
  statusNode.className = "docsViewerReport__status";
  statusNode.setAttribute("aria-live", "polite");
  const table = document.createElement("div");
  table.className = "docsViewerReport__table";
  table.setAttribute("role", "table");
  table.setAttribute("aria-label", "Work Downloads");
  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  head.setAttribute("role", "row");
  ["Work", "File"].forEach((label) => {
    const heading = document.createElement("span");
    heading.className = "docsViewerReport__headLabel";
    heading.setAttribute("role", "columnheader");
    heading.textContent = label;
    if (label === "Work") heading.setAttribute("aria-sort", "ascending");
    head.appendChild(heading);
  });
  const rowsNode = document.createElement("ul");
  rowsNode.className = "docsViewerReport__rows";
  rowsNode.setAttribute("role", "rowgroup");
  table.append(head, rowsNode);
  const emptyNode = document.createElement("p");
  emptyNode.className = "docsViewerReport__empty";
  emptyNode.textContent = "No Work downloads or saved files were found.";
  emptyNode.hidden = true;
  root.append(toolbar, statusNode, table, emptyNode);
  return { document, emptyNode, rowsNode, runButton, statusNode };
}

/** Mount a live local inspection; all file actions stay behind the service. */
export function mountWorkDownloadsReport(context) {
  const state = { ...renderShell(context.reportRoot), busy: false, context };
  state.runButton.addEventListener("click", () => {
    if (!state.busy) runReport(state);
  });
  state.rowsNode.addEventListener("click", (event) => {
    const link = event.target instanceof Element ? event.target.closest("a") : null;
    if (!link) return;
    if (state.busy) {
      event.preventDefault();
      return;
    }
    if (!link.dataset.workDownloadFilename) return;
    event.preventDefault();
    openFile(state, link.dataset.workDownloadFilename);
  });
  return runReport(state);
}
