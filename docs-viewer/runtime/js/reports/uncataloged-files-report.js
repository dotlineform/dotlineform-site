import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function reportService(context) {
  const service = context && context.reportService;
  return (
    service
    && typeof service.readUncatalogedFiles === "function"
    && typeof service.runUncatalogedFiles === "function"
    && typeof service.openLocalTarget === "function"
  ) ? service : null;
}

function appendTextCell(rowNode, value) {
  const cell = document.createElement("span");
  cell.textContent = value;
  rowNode.appendChild(cell);
}

function appendFileCell(rowNode, row) {
  const cell = document.createElement("span");
  const link = document.createElement("a");
  link.className = "docsViewerReport__cellLink";
  link.href = "#";
  link.textContent = row.file_name;
  link.dataset.uncatalogedFileTarget = row.local_target;
  cell.appendChild(link);
  rowNode.appendChild(cell);
}

function renderRows(state) {
  clearNode(state.rowsNode);
  const rows = state.report ? state.report.rows : [];
  state.emptyNode.hidden = rows.length > 0;
  if (!rows.length) {
    state.emptyNode.textContent = state.report
      ? "No uncatalogued images were found."
      : "Refresh to generate this report.";
    return;
  }
  rows.forEach((row) => {
    const rowNode = document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    appendTextCell(rowNode, row.folder.replace(/^projects\//, ""));
    appendFileCell(rowNode, row);
    state.rowsNode.appendChild(rowNode);
  });
}

function setBusy(state, busy) {
  state.busy = Boolean(busy);
  state.runButton.disabled = state.busy;
  state.runButton.setAttribute("aria-busy", state.busy ? "true" : "false");
}

function loadReport(state, refresh = false) {
  const service = reportService(state.context);
  if (!service) {
    state.statusNode.textContent = "Local docs-management server is not configured.";
    return Promise.resolve();
  }
  setBusy(state, true);
  state.statusNode.textContent = "";
  return (refresh ? service.runUncatalogedFiles() : service.readUncatalogedFiles())
    .then((payload) => {
      state.report = payload.report;
      state.statusNode.textContent = "";
      renderRows(state);
    })
    .catch((error) => {
      const message = error && error.message
        ? error.message
        : "Uncatalogued Images could not complete the request.";
      state.statusNode.textContent = message + (state.report ? " Showing the last saved report." : "");
    })
    .finally(() => {
      setBusy(state, false);
    });
}

function openFile(state, target) {
  const service = reportService(state.context);
  if (!service) {
    state.statusNode.textContent = "Open in Finder is unavailable.";
    return Promise.resolve();
  }
  return service.openLocalTarget(target)
    .then(() => {
      state.statusNode.textContent = "";
    })
    .catch((error) => {
      state.statusNode.textContent = error && error.message
        ? error.message
        : "Open in Finder failed.";
    });
}

function attachEvents(state) {
  state.runButton.addEventListener("click", () => {
    if (!state.busy) loadReport(state, true);
  });
  state.rowsNode.addEventListener("click", (event) => {
    const link = event.target instanceof Element
      ? event.target.closest("[data-uncataloged-file-target]")
      : null;
    if (!link || state.busy) return;
    event.preventDefault();
    openFile(state, link.dataset.uncatalogedFileTarget);
  });
}

function renderShell(root) {
  clearNode(root);
  root.dataset.reportId = "uncataloged_files";
  root.dataset.reportColumns = "2";

  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const runButton = document.createElement("button");
  runButton.id = "docsUncatalogedFilesReportRun";
  runButton.type = "button";
  runButton.className = "docsViewer__toolbarIconButton";
  runButton.setAttribute("aria-label", "Refresh");
  runButton.title = "Refresh";
  runButton.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));
  toolbar.appendChild(runButton);

  const status = document.createElement("p");
  status.className = "docsViewerReport__status";

  const table = document.createElement("div");
  table.className = "docsViewerReport__table";
  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  ["Folder", "File name"].forEach((label) => {
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

export function mountUncatalogedFilesReport(context) {
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    busy: false,
    context,
    report: null
  }, nodes);
  attachEvents(state);
  setBusy(state, false);
  renderRows(state);
  return loadReport(state);
}
