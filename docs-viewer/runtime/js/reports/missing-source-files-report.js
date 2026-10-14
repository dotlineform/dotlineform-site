import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function reportService(context) {
  const service = context && context.reportService;
  return service && typeof service.runMissingSourceFiles === "function" ? service : null;
}

function studioWorkHref(context, workId) {
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
  return new URL(
    "/studio/catalogue-work/?work=" + encodeURIComponent(workId),
    studio.origin
  ).toString();
}

function appendWorkCell(state, rowNode, row) {
  const cell = document.createElement("span");
  const link = document.createElement("a");
  link.className = "docsViewerReport__cellLink";
  link.href = studioWorkHref(state.context, row.work_id);
  link.textContent = row.work_id;
  cell.appendChild(link);
  rowNode.appendChild(cell);
}

function appendTextCell(rowNode, value) {
  const cell = document.createElement("span");
  cell.textContent = value;
  rowNode.appendChild(cell);
}

function renderRows(state) {
  clearNode(state.rowsNode);
  state.emptyNode.hidden = state.rows.length > 0;
  if (!state.rows.length) {
    state.emptyNode.textContent = "No missing source files were found.";
    return;
  }
  state.rows.forEach((row) => {
    const rowNode = document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    appendWorkCell(state, rowNode, row);
    appendTextCell(rowNode, row.work_title);
    appendTextCell(rowNode, row.expected_source_path);
    state.rowsNode.appendChild(rowNode);
  });
}

function setBusy(state, busy) {
  state.busy = Boolean(busy);
  state.runButton.disabled = state.busy;
  state.runButton.setAttribute("aria-busy", state.busy ? "true" : "false");
}

function runReport(state) {
  const service = reportService(state.context);
  state.rows = [];
  clearNode(state.rowsNode);
  state.emptyNode.hidden = true;
  if (!service) {
    state.statusNode.textContent = "Local docs-management server is not configured.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "The current Missing Source Files run could not complete.";
    return Promise.resolve();
  }
  setBusy(state, true);
  state.statusNode.textContent = "Running Missing Source Files...";
  return service.runMissingSourceFiles()
    .then((payload) => {
      state.rows = payload.report.rows;
      state.statusNode.textContent = "";
      renderRows(state);
    })
    .catch((error) => {
      state.rows = [];
      clearNode(state.rowsNode);
      state.statusNode.textContent = error && error.message
        ? error.message
        : "Missing Source Files refresh failed.";
      state.emptyNode.hidden = false;
      state.emptyNode.textContent = "The current Missing Source Files run could not complete.";
    })
    .finally(() => {
      setBusy(state, false);
    });
}

function attachEvents(state) {
  state.runButton.addEventListener("click", () => {
    if (!state.busy) runReport(state);
  });
}

function renderShell(root) {
  clearNode(root);
  root.dataset.reportId = "missing_source_files";
  root.dataset.reportColumns = "3";

  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const runButton = document.createElement("button");
  runButton.id = "docsMissingSourceFilesReportRun";
  runButton.type = "button";
  runButton.className = "docsViewer__toolbarIconButton";
  runButton.setAttribute("aria-label", "Run/Refresh");
  runButton.title = "Run/Refresh";
  runButton.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));
  toolbar.appendChild(runButton);

  const status = document.createElement("p");
  status.className = "docsViewerReport__status";

  const table = document.createElement("div");
  table.className = "docsViewerReport__table";
  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  ["Work ID", "Work title", "Expected source path"].forEach((label) => {
    const heading = document.createElement("span");
    heading.className = "docsViewerReport__headLabel";
    heading.textContent = label;
    head.appendChild(heading);
  });
  const rows = document.createElement("ul");
  rows.className = "docsViewerReport__rows";
  const empty = document.createElement("p");
  empty.className = "docsViewerReport__empty";
  empty.hidden = true;
  table.appendChild(head);
  table.appendChild(rows);

  root.appendChild(toolbar);
  root.appendChild(status);
  root.appendChild(table);
  root.appendChild(empty);
  return {
    emptyNode: empty,
    rowsNode: rows,
    runButton,
    statusNode: status
  };
}

export function mountMissingSourceFilesReport(context) {
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    busy: false,
    context,
    rows: []
  }, nodes);
  attachEvents(state);
  setBusy(state, false);
  return runReport(state);
}
