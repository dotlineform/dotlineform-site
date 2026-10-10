import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";

const SORTER = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

function title(row, key) {
  return row[key]?.title || "";
}

/** Ascending puts missing associations first; descending puts them last. */
function sortRows(state) {
  const secondary = state.sortKey === "series" ? "gallery" : "series";
  return state.rows.slice().sort((left, right) => {
    const first = title(left, state.sortKey);
    const second = title(right, state.sortKey);
    const primary = Number(Boolean(first)) - Number(Boolean(second)) || SORTER.compare(first, second);
    return primary * (state.sortDir === "desc" ? -1 : 1)
      || SORTER.compare(title(left, secondary), title(right, secondary))
      || (left.series?.series_id || "").localeCompare(right.series?.series_id || "")
      || (left.gallery?.gallery_id || "").localeCompare(right.gallery?.gallery_id || "");
  });
}

function current(state) {
  return !state.released && state.context.content.contains(state.root);
}

function setBusy(state, busy) {
  state.busy = busy;
  state.root.setAttribute("aria-busy", String(busy));
  state.refreshButton.disabled = busy;
  state.refreshButton.setAttribute("aria-busy", String(busy));
  state.controls.forEach(({ button, cell, indicator, key, label }) => {
    const active = key === state.sortKey;
    cell.setAttribute("aria-sort", active ? (state.sortDir === "asc" ? "ascending" : "descending") : "none");
    indicator.textContent = active ? (state.sortDir === "asc" ? "▲" : "▼") : "";
    button.dataset.state = active ? "active" : "";
    button.disabled = busy;
    button.setAttribute("aria-label", `Sort by ${label} ${active && state.sortDir === "asc" ? "descending" : "ascending"}`);
  });
  state.rowsNode.querySelectorAll("button").forEach(button => { button.disabled = busy; });
}

function renderRows(state) {
  state.rowsNode.replaceChildren();
  state.emptyNode.hidden = state.rows.length > 0;
  state.tableNode.hidden = state.rows.length === 0;
  sortRows(state).forEach(row => {
    const rowNode = state.document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.setAttribute("role", "row");
    for (const key of ["series", "gallery"]) {
      const cell = state.document.createElement("span");
      cell.setAttribute("role", "cell");
      if (key === "gallery" && row.gallery) {
        const button = state.document.createElement("button");
        button.type = "button";
        button.className = "docsViewerReport__collectionButton docsViewerReport__cellLink";
        button.textContent = row.gallery.title;
        button.dataset.galleryId = row.gallery.gallery_id;
        cell.appendChild(button);
      } else cell.textContent = title(row, key) || "—";
      rowNode.appendChild(cell);
    }
    state.rowsNode.appendChild(rowNode);
  });
  setBusy(state, state.busy);
}

async function readReport(state) {
  setBusy(state, true);
  state.statusNode.textContent = "Loading Series and Galleries…";
  try {
    const payload = await state.context.reportService.readSeriesGalleries();
    if (!current(state)) return;
    const header = payload?.header;
    const headerKeys = header && typeof header === "object" && !Array.isArray(header) ? Object.keys(header) : [];
    if (headerKeys.length !== 2 || !headerKeys.includes("schema") || !headerKeys.includes("generated_at_utc")
      || header.schema !== "catalogue_series_galleries_report_v2"
      || typeof header.generated_at_utc !== "string" || !header.generated_at_utc.trim()
      || !Array.isArray(payload.rows)) {
      throw new Error("Invalid saved Series and Galleries data.");
    }
    state.rows = payload.rows;
    renderRows(state);
    state.statusNode.textContent = "";
  } catch (error) {
    if (!current(state)) return;
    state.statusNode.textContent = error.message || "Series and Galleries could not load.";
  } finally {
    if (current(state)) setBusy(state, false);
  }
}

async function openGallery(state, button) {
  if (state.busy || !current(state)) return;
  setBusy(state, true);
  state.statusNode.textContent = "";
  try {
    await state.context.openMediaTarget({
      mediaTarget: { kind: "catalogue-gallery", id: button.dataset.galleryId },
      invocationControl: button,
      documentTarget: { collection: "", docId: state.context.doc.doc_id },
      isCurrentDocument: () => current(state) && state.rowsNode.contains(button)
    });
  } catch (error) {
    if (current(state)) state.statusNode.textContent = error.message || "Gallery could not open.";
  } finally {
    if (current(state)) setBusy(state, false);
  }
}

/** Read a saved private snapshot and open exact Galleries through the existing Media View. */
export function mountSeriesGalleriesReport(context) {
  if (!context.reportService?.readSeriesGalleries || typeof context.openMediaTarget !== "function") {
    throw new Error("Local Series and Galleries services are unavailable.");
  }
  const root = context.reportRoot;
  const document = root.ownerDocument;
  root.replaceChildren();
  root.dataset.reportColumns = "2";
  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const refreshButton = document.createElement("button");
  refreshButton.type = "button";
  refreshButton.className = "docsViewer__toolbarIconButton";
  refreshButton.title = "Reload saved report";
  refreshButton.setAttribute("aria-label", refreshButton.title);
  refreshButton.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));
  const statusNode = document.createElement("p");
  statusNode.className = "docsViewerReport__status";
  statusNode.setAttribute("aria-live", "polite");
  toolbar.append(refreshButton, statusNode);
  const tableNode = document.createElement("div");
  tableNode.className = "docsViewerReport__table";
  tableNode.setAttribute("role", "table");
  tableNode.setAttribute("aria-label", "Series and Galleries");
  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  head.setAttribute("role", "row");
  const rowsNode = document.createElement("ul");
  rowsNode.className = "docsViewerReport__rows";
  rowsNode.setAttribute("role", "rowgroup");
  tableNode.append(head, rowsNode);
  const emptyNode = document.createElement("p");
  emptyNode.className = "docsViewerReport__empty";
  emptyNode.textContent = "No saved Series or Galleries.";
  emptyNode.hidden = true;
  root.append(toolbar, tableNode, emptyNode);
  const state = { root, document, context, refreshButton, statusNode, tableNode, rowsNode, emptyNode,
    busy: false, released: false, rows: [], sortKey: "series", sortDir: "asc", controls: [] };
  state.controls = [["series", "Series"], ["gallery", "Gallery"]].map(([key, label]) => {
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
  refreshButton.addEventListener("click", () => { if (!state.busy) void readReport(state); });
  rowsNode.addEventListener("click", event => {
    const button = event.target.closest("button[data-gallery-id]");
    if (button) void openGallery(state, button);
  });
  context.registerRetainedView?.({
    id: "series-galleries",
    capture: () => ({ key: state.sortKey, direction: state.sortDir }),
    restore: saved => {
      if (state.sortKey === saved.key && state.sortDir === saved.direction) return;
      state.sortKey = saved.key;
      state.sortDir = saved.direction;
      renderRows(state);
    },
    dispose: () => { state.released = true; }
  });
  return readReport(state);
}
