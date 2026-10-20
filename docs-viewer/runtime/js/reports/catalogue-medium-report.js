import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

const SORTER = new Intl.Collator("en", { numeric: true, sensitivity: "base" });

/** Count exact Refresh-owned values, keeping explicit null separate from authored text. */
export function prepareCatalogueMediumRows(payload) {
  const groups = new Map();
  for (const { medium } of Object.values(payload.works)) {
    const row = groups.get(medium);
    if (row) row.works += 1;
    else groups.set(medium, { medium, label: medium === null ? "No medium" : medium, works: 1 });
  }
  return Array.from(groups.values());
}

function compareMedium(left, right) {
  return SORTER.compare(left.label, right.label)
    || (left.label < right.label ? -1 : left.label > right.label ? 1 : 0)
    || Number(left.medium !== null) - Number(right.medium !== null);
}

/** Order prepared groups without recounting or fetching; count ties use Medium ascending. */
export function orderCatalogueMediumRows(rows, key = "medium", direction = "asc") {
  const sign = direction === "desc" ? -1 : 1;
  return rows.slice().sort((left, right) => key === "works"
    ? (left.works - right.works) * sign || compareMedium(left, right)
    : compareMedium(left, right) * sign);
}

function updateControls(state) {
  state.root.setAttribute("aria-busy", String(state.busy));
  state.reloadButton.disabled = state.busy;
  state.reloadButton.setAttribute("aria-busy", String(state.busy));
  for (const { key, label, cell, button, indicator } of state.controls) {
    const active = state.sortKey === key;
    cell.setAttribute("aria-sort", active ? (state.sortDir === "asc" ? "ascending" : "descending") : "none");
    indicator.textContent = active ? (state.sortDir === "asc" ? "▲" : "▼") : "";
    button.dataset.state = active ? "active" : "";
    button.disabled = state.busy;
    button.setAttribute("aria-label", `Sort by ${label} ${active && state.sortDir === "asc" ? "descending" : "ascending"}`);
  }
}

function renderRows(state) {
  const fragment = state.document.createDocumentFragment();
  for (const row of orderCatalogueMediumRows(state.rows, state.sortKey, state.sortDir)) {
    const item = state.document.createElement("li");
    item.className = "docsViewerReport__row";
    item.setAttribute("role", "row");
    for (const value of [row.label, row.works]) {
      const cell = state.document.createElement("span");
      cell.setAttribute("role", "cell");
      cell.textContent = value;
      item.appendChild(cell);
    }
    fragment.appendChild(item);
  }
  state.rowsNode.replaceChildren(fragment);
  state.tableNode.hidden = state.rows.length === 0;
  state.emptyNode.hidden = state.rows.length > 0;
  updateControls(state);
}

async function readReport(state) {
  if (state.released) return;
  state.busy = true;
  state.statusNode.textContent = "";
  updateControls(state);
  try {
    const payload = await state.context.reportService.readCatalogueWorks();
    if (state.released) return;
    state.rows = prepareCatalogueMediumRows(payload);
    renderRows(state);
  } catch (error) {
    if (state.released) return;
    state.statusNode.textContent = error.message || "Catalogue Medium could not load.";
  } finally {
    if (!state.released) {
      state.busy = false;
      updateControls(state);
    }
  }
}

/** Inspect saved Medium usage through the existing local Catalogue metadata service. */
export function mountCatalogueMediumReport(context) {
  if (typeof context.reportService?.readCatalogueWorks !== "function") {
    throw new Error("Local Catalogue metadata services are unavailable.");
  }
  const root = context.reportRoot;
  const document = root.ownerDocument;
  root.replaceChildren();
  root.dataset.reportColumns = "2";
  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const reloadButton = document.createElement("button");
  reloadButton.type = "button";
  reloadButton.className = "docsViewer__toolbarIconButton";
  reloadButton.title = "Reload saved metadata";
  reloadButton.setAttribute("aria-label", reloadButton.title);
  reloadButton.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));
  const statusNode = document.createElement("p");
  statusNode.className = "docsViewerReport__status";
  statusNode.setAttribute("aria-live", "polite");
  toolbar.append(reloadButton, statusNode);
  const tableNode = document.createElement("div");
  tableNode.className = "docsViewerReport__table";
  tableNode.setAttribute("role", "table");
  tableNode.setAttribute("aria-label", "Catalogue Medium");
  tableNode.hidden = true;
  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  head.setAttribute("role", "row");
  const rowsNode = document.createElement("ul");
  rowsNode.className = "docsViewerReport__rows";
  rowsNode.setAttribute("role", "rowgroup");
  tableNode.append(head, rowsNode);
  const emptyNode = document.createElement("p");
  emptyNode.className = "docsViewerReport__empty";
  emptyNode.textContent = "No saved Works.";
  emptyNode.hidden = true;
  root.append(toolbar, tableNode, emptyNode);
  const state = { root, document, context, reloadButton, statusNode, tableNode, rowsNode, emptyNode,
    busy: true, released: false, rows: [], sortKey: "medium", sortDir: "asc", controls: [] };
  state.controls = [["medium", "Medium"], ["works", "Works"]].map(([key, label]) => {
    const cell = document.createElement("span");
    cell.className = "docsViewerReport__headLabel";
    cell.setAttribute("role", "columnheader");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "docsViewerReport__sortButton";
    button.textContent = label;
    const indicator = document.createElement("span");
    indicator.className = "docsViewerReport__sortIndicator";
    indicator.setAttribute("aria-hidden", "true");
    button.appendChild(indicator);
    cell.appendChild(button);
    head.appendChild(cell);
    button.addEventListener("click", () => {
      if (state.busy) return;
      state.sortDir = state.sortKey === key && state.sortDir === "asc" ? "desc" : "asc";
      state.sortKey = key;
      renderRows(state);
    });
    return { key, label, cell, button, indicator };
  });
  reloadButton.addEventListener("click", () => { if (!state.busy) void readReport(state); });
  context.registerRetainedView?.({
    id: "catalogue-medium",
    capture: () => ({ key: state.sortKey, direction: state.sortDir }),
    restore: saved => {
      if (state.released || (state.sortKey === saved.key && state.sortDir === saved.direction)) return;
      state.sortKey = saved.key;
      state.sortDir = saved.direction;
      if (!state.busy) renderRows(state);
    },
    dispose: () => { state.released = true; state.rows = []; }
  });
  return readReport(state);
}
