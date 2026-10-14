import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

function renderRows(state, rows) {
  const fragment = state.document.createDocumentFragment();
  rows.forEach(row => {
    const rowNode = state.document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.setAttribute("role", "row");
    const folderCell = state.document.createElement("span");
    folderCell.setAttribute("role", "cell");
    const link = state.document.createElement("a");
    link.className = "docsViewerReport__cellLink";
    link.href = "#";
    link.textContent = row.folder;
    link.title = "Open folder in Finder";
    link.dataset.folderTarget = row.local_target;
    folderCell.appendChild(link);
    const countCell = state.document.createElement("span");
    countCell.setAttribute("role", "cell");
    countCell.textContent = String(row.works_below);
    rowNode.append(folderCell, countCell);
    fragment.appendChild(rowNode);
  });
  state.rowsNode.replaceChildren(fragment);
  state.emptyNode.hidden = rows.length > 0;
}

function setBusy(state, busy) {
  state.busy = busy;
  state.root.setAttribute("aria-busy", String(busy));
  state.runButton.disabled = busy;
  state.runButton.setAttribute("aria-busy", String(busy));
  state.rowsNode.querySelectorAll("a").forEach(link => {
    link.setAttribute("aria-disabled", String(busy));
  });
}

async function runReport(state) {
  if (state.released) return;
  setBusy(state, true);
  state.statusNode.textContent = "";
  try {
    const payload = await state.service.runFoldersWithoutWorks();
    if (state.released) return;
    const rows = payload.report.rows;
    renderRows(state, rows);
    state.emptyNode.textContent = "No folders without directly registered Works were found.";
    state.statusNode.textContent = `${rows.length} ${rows.length === 1 ? "folder" : "folders"}`;
  } catch (error) {
    if (state.released) return;
    renderRows(state, []);
    state.statusNode.textContent = error.message || "Folders Without Works refresh failed.";
    state.emptyNode.textContent = "The folder scan could not complete.";
  } finally {
    if (!state.released) setBusy(state, false);
  }
}

async function openFolder(state, target) {
  if (state.released) return;
  setBusy(state, true);
  try {
    await state.service.openLocalTarget(target);
  } catch (error) {
    if (!state.released) state.statusNode.textContent = error.message || "Folder could not be opened in Finder.";
  } finally {
    if (!state.released) setBusy(state, false);
  }
}

function renderShell(root) {
  const document = root.ownerDocument;
  root.replaceChildren();
  root.dataset.reportId = "folders_without_works";
  root.dataset.reportColumns = "2";
  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const runButton = document.createElement("button");
  runButton.type = "button";
  runButton.className = "docsViewer__toolbarIconButton";
  runButton.title = "Run/Refresh";
  runButton.setAttribute("aria-label", "Run/Refresh");
  runButton.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));
  toolbar.appendChild(runButton);
  const statusNode = document.createElement("p");
  statusNode.className = "docsViewerReport__status";
  statusNode.setAttribute("role", "status");
  const table = document.createElement("div");
  table.className = "docsViewerReport__table";
  table.setAttribute("role", "table");
  table.setAttribute("aria-label", "Folders Without Works");
  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  head.setAttribute("role", "row");
  ["Folder", "Works below"].forEach(label => {
    const cell = document.createElement("span");
    cell.className = "docsViewerReport__headLabel";
    cell.textContent = label;
    cell.setAttribute("role", "columnheader");
    head.appendChild(cell);
  });
  const rowsNode = document.createElement("ul");
  rowsNode.className = "docsViewerReport__rows";
  rowsNode.setAttribute("role", "rowgroup");
  table.append(head, rowsNode);
  const emptyNode = document.createElement("p");
  emptyNode.className = "docsViewerReport__empty";
  emptyNode.hidden = true;
  root.append(toolbar, statusNode, table, emptyNode);
  return { document, emptyNode, root, rowsNode, runButton, statusNode };
}

/** Mount a live local scan; retained report navigation keeps the displayed run. */
export function mountFoldersWithoutWorksReport(context) {
  const service = context.reportService;
  if (!service || typeof service.runFoldersWithoutWorks !== "function" || typeof service.openLocalTarget !== "function") {
    throw new Error("Local docs-management server is not configured.");
  }
  const state = { ...renderShell(context.reportRoot), service, busy: false, released: false };
  state.runButton.addEventListener("click", () => {
    if (!state.busy) runReport(state);
  });
  state.rowsNode.addEventListener("click", event => {
    const link = event.target instanceof Element ? event.target.closest("[data-folder-target]") : null;
    if (!link) return;
    event.preventDefault();
    if (!state.busy) openFolder(state, link.dataset.folderTarget);
  });
  context.registerRetainedView?.({
    id: "folders_without_works",
    capture: () => null,
    restore: () => {},
    dispose: () => { state.released = true; }
  });
  return runReport(state);
}
