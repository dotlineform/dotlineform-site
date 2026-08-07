const REPORT_SCHEMA = "docs_uncataloged_files_report_v1";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function reportService(context) {
  const service = context && context.reportService;
  return (
    service
    && typeof service.runUncatalogedFiles === "function"
    && typeof service.openLocalTarget === "function"
  ) ? service : null;
}

function normalizeRow(value) {
  const keys = value && typeof value === "object" && !Array.isArray(value)
    ? Object.keys(value).sort()
    : [];
  const folder = cleanString(value && value.folder);
  const fileName = cleanString(value && value.file_name);
  const localTarget = cleanString(value && value.local_target);
  if (
    keys.join(",") !== "file_name,folder,local_target"
    || !folder
    || folder.startsWith("/")
    || folder.startsWith("projects/")
    || !fileName
    || fileName.includes("/")
    || !localTarget.startsWith("projects/")
  ) {
    throw new Error("Uncataloged Files row is invalid.");
  }
  return { fileName, folder, localTarget };
}

export function normalizeUncatalogedFilesResponse(payload) {
  const report = payload && payload.report;
  if (
    !payload
    || payload.ok !== true
    || !report
    || Object.keys(report).sort().join(",") !== "rows,schema_version"
    || report.schema_version !== REPORT_SCHEMA
    || !Array.isArray(report.rows)
  ) {
    throw new Error("Uncataloged Files report is invalid.");
  }
  return report.rows.map(normalizeRow);
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
  link.textContent = row.fileName;
  link.dataset.uncatalogedFileTarget = row.localTarget;
  cell.appendChild(link);
  rowNode.appendChild(cell);
}

function renderRows(state) {
  clearNode(state.rowsNode);
  state.emptyNode.hidden = state.rows.length > 0;
  if (!state.rows.length) {
    state.emptyNode.textContent = "No uncataloged files were found.";
    return;
  }
  state.rows.forEach((row) => {
    const rowNode = document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    appendTextCell(rowNode, row.folder);
    appendFileCell(rowNode, row);
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
    state.emptyNode.textContent = "The current Uncataloged Files run could not complete.";
    return Promise.resolve();
  }
  setBusy(state, true);
  state.statusNode.textContent = "Running Uncataloged Files...";
  return service.runUncatalogedFiles()
    .then(normalizeUncatalogedFilesResponse)
    .then((rows) => {
      state.rows = rows;
      state.statusNode.textContent = "";
      renderRows(state);
    })
    .catch((error) => {
      state.rows = [];
      clearNode(state.rowsNode);
      state.statusNode.textContent = error && error.message
        ? error.message
        : "Uncataloged Files refresh failed.";
      state.emptyNode.hidden = false;
      state.emptyNode.textContent = "The current Uncataloged Files run could not complete.";
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
    if (!state.busy) runReport(state);
  });
  state.rowsNode.addEventListener("click", (event) => {
    const link = event.target instanceof Element
      ? event.target.closest("[data-uncataloged-file-target]")
      : null;
    if (!link || state.busy) return;
    event.preventDefault();
    openFile(state, cleanString(link.dataset.uncatalogedFileTarget));
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
  runButton.className = "docsViewerReport__button docsViewerReport__button--pill";
  runButton.setAttribute("aria-label", "Run/Refresh");
  runButton.title = "Run/Refresh";
  runButton.textContent = "🔄";
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
    rows: []
  }, nodes);
  attachEvents(state);
  setBusy(state, false);
  return runReport(state);
}
