import { buildViewerUrl } from "../shared/docs-viewer-router.js";
import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

const SORTER = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

function workTitle(row) {
  return row.work ? row.work.title : "";
}

/** Sort the displayed column, keeping its blank cells last in both directions. */
export function sortWorkResourceRows(rows, key, direction) {
  const value = row => key === "work" ? workTitle(row) : row.label;
  return rows.slice().sort((left, right) => {
    const leftValue = value(left);
    const rightValue = value(right);
    const emptyOrder = Number(!leftValue) - Number(!rightValue);
    if (emptyOrder) return emptyOrder;
    const primary = SORTER.compare(leftValue, rightValue);
    if (primary) return primary * (direction === "desc" ? -1 : 1);
    return SORTER.compare(workTitle(left), workTitle(right))
      || SORTER.compare(left.label || left.identity, right.label || right.identity)
      || left.identity.localeCompare(right.identity)
      || (left.work?.work_id || "").localeCompare(right.work?.work_id || "");
  });
}

function updateControls(state) {
  state.controls.forEach(({ key, label, cell, button, indicator }) => {
    const active = key === state.sortKey;
    cell.setAttribute("aria-sort", active ? (state.sortDir === "asc" ? "ascending" : "descending") : "none");
    button.dataset.state = active ? "active" : "";
    button.disabled = state.busy;
    button.setAttribute("aria-label", `Sort by ${label} ${active && state.sortDir === "asc" ? "descending" : "ascending"}`);
    indicator.textContent = active ? (state.sortDir === "asc" ? "▲" : "▼") : "";
  });
}

function appendCell(state, rowNode, text, href, options = {}) {
  const cell = state.document.createElement("span");
  cell.setAttribute("role", "cell");
  if (text) {
    const link = state.document.createElement("a");
    link.className = "docsViewerReport__cellLink";
    link.textContent = text;
    link.href = href;
    if (options.filename) link.dataset.workDownloadFilename = options.filename;
    if (options.external) {
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
    cell.appendChild(link);
  }
  rowNode.appendChild(cell);
}

function renderRows(state) {
  const workspace = state.context.workspaceConfig;
  if (state.rows.some(row => row.work) && (!workspace?.viewerBaseUrl
    || !workspace.collections.some(entry => entry.collection === "catalogue"))) {
    throw new Error("Working Catalogue is not configured.");
  }
  state.rowsNode.replaceChildren();
  state.emptyNode.hidden = state.rows.length > 0;
  sortWorkResourceRows(state.rows, state.sortKey, state.sortDir).forEach(row => {
    const workHref = row.work ? buildViewerUrl({
      viewerBaseUrl: workspace.viewerBaseUrl,
      origin: new URL(state.document.baseURI).origin,
      docId: row.work.work_id,
      collection: "catalogue"
    }) : "";
    const rowNode = state.document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.setAttribute("role", "row");
    appendCell(state, rowNode, workTitle(row), workHref);
    appendCell(state, rowNode, row.label, row.href, row);
    state.rowsNode.appendChild(rowNode);
  });
  updateControls(state);
}

function setBusy(state, busy) {
  state.busy = busy;
  state.runButton.disabled = busy;
  state.runButton.setAttribute("aria-busy", busy ? "true" : "false");
  updateControls(state);
  state.rowsNode.querySelectorAll("a").forEach(link => {
    if (busy) link.setAttribute("aria-disabled", "true");
    else link.removeAttribute("aria-disabled");
  });
}

async function runReport(state) {
  setBusy(state, true);
  state.rows = [];
  state.rowsNode.replaceChildren();
  state.emptyNode.hidden = true;
  state.statusNode.textContent = `Running ${state.options.title}...`;
  try {
    state.rows = await state.options.readRows();
    renderRows(state);
    state.statusNode.textContent = "";
  } catch (error) {
    state.rows = [];
    state.rowsNode.replaceChildren();
    state.emptyNode.hidden = true;
    state.statusNode.textContent = error.message || `${state.options.title} refresh failed.`;
  } finally {
    setBusy(state, false);
  }
}

function renderShell(root, options) {
  const document = root.ownerDocument;
  root.replaceChildren();
  root.dataset.reportId = options.reportId;
  root.dataset.reportColumns = "2";
  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const runButton = document.createElement("button");
  runButton.type = "button";
  runButton.className = "docsViewer__toolbarIconButton";
  runButton.setAttribute("aria-label", "Run/Refresh");
  runButton.title = "Run/Refresh";
  runButton.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));
  const statusNode = document.createElement("p");
  statusNode.className = "docsViewerReport__status";
  statusNode.setAttribute("aria-live", "polite");
  toolbar.append(runButton, statusNode);
  const table = document.createElement("div");
  table.className = "docsViewerReport__table";
  table.setAttribute("role", "table");
  table.setAttribute("aria-label", options.title);
  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  head.setAttribute("role", "row");
  const rowsNode = document.createElement("ul");
  rowsNode.className = "docsViewerReport__rows";
  rowsNode.setAttribute("role", "rowgroup");
  table.append(head, rowsNode);
  const emptyNode = document.createElement("p");
  emptyNode.className = "docsViewerReport__empty";
  emptyNode.textContent = options.emptyText;
  emptyNode.hidden = true;
  root.append(toolbar, table, emptyNode);
  return { document, emptyNode, head, rowsNode, runButton, statusNode };
}

/** Share local Work report presentation; producers and file actions keep their owners. */
export function mountWorkResourcesReport(context, options) {
  const state = { ...renderShell(context.reportRoot, options), context, options,
    busy: false, rows: [], controls: [], sortKey: "work", sortDir: "asc" };
  state.controls = [["work", "Work"], ["resource", options.resourceHeading]].map(([key, label]) => {
    const cell = state.document.createElement("span");
    cell.className = "docsViewerReport__headLabel";
    cell.setAttribute("role", "columnheader");
    const button = state.document.createElement("button");
    button.type = "button";
    button.className = "docsViewerReport__sortButton";
    button.textContent = label;
    const indicator = state.document.createElement("span");
    indicator.className = "docsViewerReport__sortIndicator";
    indicator.setAttribute("aria-hidden", "true");
    button.appendChild(indicator);
    cell.appendChild(button);
    state.head.appendChild(cell);
    button.addEventListener("click", () => {
      if (state.busy) return;
      state.sortDir = state.sortKey === key && state.sortDir === "asc" ? "desc" : "asc";
      state.sortKey = key;
      renderRows(state);
    });
    return { key, label, cell, button, indicator };
  });
  state.runButton.addEventListener("click", () => {
    if (!state.busy) runReport(state);
  });
  state.rowsNode.addEventListener("click", async event => {
    const link = event.target instanceof Element ? event.target.closest("a") : null;
    if (!link) return;
    if (state.busy) {
      event.preventDefault();
      return;
    }
    const filename = link.dataset.workDownloadFilename;
    if (!filename) return;
    event.preventDefault();
    setBusy(state, true);
    state.statusNode.textContent = "";
    try {
      await options.openFile(filename);
    } catch (error) {
      state.statusNode.textContent = error.message || "Open in Finder failed.";
    } finally {
      setBusy(state, false);
    }
  });
  if (context.registerRetainedView) context.registerRetainedView({
    id: options.reportId,
    capture: () => ({ key: state.sortKey, direction: state.sortDir }),
    restore: saved => {
      if (state.sortKey === saved.key && state.sortDir === saved.direction) return;
      state.sortKey = saved.key;
      state.sortDir = saved.direction;
      renderRows(state);
    }
  });
  return runReport(state);
}
