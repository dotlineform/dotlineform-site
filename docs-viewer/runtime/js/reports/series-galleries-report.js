import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import { createStudioWorkEditorLinks } from "./studio-work-editor-links.js";

const SORTER = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

function title(row, key) {
  return row[key] === null ? "" : row[key].title;
}

/** Ascending puts missing associations first; descending puts them last. */
function sortRows(state) {
  const secondary = state.sortKey === "series" ? "gallery" : "series";
  return state.rows.slice().sort((left, right) => {
    let primary;
    if (state.sortKey === "works") {
      primary = Number(left.gallery !== null) - Number(right.gallery !== null)
        || (left.gallery === null ? 0 : left.gallery.work_count) - (right.gallery === null ? 0 : right.gallery.work_count);
    } else {
      primary = Number(left[state.sortKey] !== null) - Number(right[state.sortKey] !== null)
        || SORTER.compare(title(left, state.sortKey), title(right, state.sortKey));
    }
    return primary * (state.sortDir === "desc" ? -1 : 1)
      || SORTER.compare(title(left, secondary), title(right, secondary))
      || (state.sortKey === "works" ? SORTER.compare(title(left, "gallery"), title(right, "gallery")) : 0)
      || (left.series === null ? "" : left.series.series_id).localeCompare(right.series === null ? "" : right.series.series_id)
      || (left.gallery === null ? "" : left.gallery.gallery_id).localeCompare(right.gallery === null ? "" : right.gallery.gallery_id);
  });
}

function current(state) {
  return !state.released && state.context.content.contains(state.root);
}

function setBusy(state, busy) {
  state.busy = busy;
  state.root.setAttribute("aria-busy", String(busy));
  state.searchInput.disabled = busy;
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
  state.rowsNode.querySelectorAll("a").forEach(link => {
    link.inert = busy;
    if (busy) link.setAttribute("aria-disabled", "true");
    else link.removeAttribute("aria-disabled");
  });
}

function renderRows(state) {
  const query = state.searchText.trim().toLocaleLowerCase();
  const rows = query ? state.rows.filter(row =>
    title(row, "series").toLocaleLowerCase().includes(query)
    || title(row, "gallery").toLocaleLowerCase().includes(query)) : state.rows;
  state.rowsNode.replaceChildren();
  state.emptyNode.textContent = state.rows.length && query
    ? "No Series or Galleries match the current search." : "No saved Series or Galleries.";
  state.emptyNode.hidden = rows.length > 0;
  state.tableNode.hidden = rows.length === 0;
  rows.forEach(row => {
    const rowNode = state.document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.setAttribute("role", "row");
    for (const key of ["series", "gallery"]) {
      const cell = state.document.createElement("span");
      cell.setAttribute("role", "cell");
      const record = row[key];
      if (key === "gallery" && record !== null) {
        const button = state.document.createElement("button");
        button.type = "button";
        button.className = "docsViewerReport__collectionButton docsViewerReport__cellLink";
        button.textContent = record.title;
        button.dataset.galleryId = record.gallery_id;
        cell.appendChild(button);
      } else if (record !== null) {
        const link = state.document.createElement("a");
        link.className = "docsViewerReport__cellLink";
        link.textContent = record.title;
        link.href = state.studioLinks.forSeries(record.series_id);
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.title = "Open Series in Studio (new tab)";
        cell.appendChild(link);
      } else cell.textContent = "—";
      rowNode.appendChild(cell);
    }
    const worksCell = state.document.createElement("span");
    worksCell.setAttribute("role", "cell");
    worksCell.textContent = row.gallery === null ? "—" : String(row.gallery.work_count);
    rowNode.appendChild(worksCell);
    state.rowsNode.appendChild(rowNode);
  });
  setBusy(state, state.busy);
}

async function readReport(state) {
  setBusy(state, true);
  state.statusNode.textContent = "";
  try {
    const payload = await state.context.reportService.readSeriesGalleries();
    if (!current(state)) return;
    state.rows = payload.rows;
    state.rows = sortRows(state);
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

/** Read saved associations; Series open local Studio, Galleries use the retained Media View. */
export function mountSeriesGalleriesReport(context) {
  if (!context.reportService?.readSeriesGalleries || typeof context.openMediaTarget !== "function") {
    throw new Error("Local Series and Galleries services are unavailable.");
  }
  const root = context.reportRoot;
  const document = root.ownerDocument;
  root.replaceChildren();
  root.dataset.reportColumns = "3";
  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const search = document.createElement("span");
  search.className = "docsViewerReport__search";
  const searchInput = document.createElement("input");
  searchInput.className = "docsViewerReport__searchInput";
  searchInput.type = "search";
  searchInput.placeholder = "Search";
  searchInput.setAttribute("aria-label", "Search Series and Galleries");
  search.appendChild(searchInput);
  mountSearchField(searchInput, { clearLabel: "Clear Series and Galleries search" });
  const refreshButton = document.createElement("button");
  refreshButton.type = "button";
  refreshButton.className = "docsViewer__toolbarIconButton";
  refreshButton.title = "Reload saved report";
  refreshButton.setAttribute("aria-label", refreshButton.title);
  refreshButton.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));
  const statusNode = document.createElement("p");
  statusNode.className = "docsViewerReport__status";
  statusNode.setAttribute("aria-live", "polite");
  toolbar.append(refreshButton, search, statusNode);
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
  const state = { root, document, context, searchInput, refreshButton, statusNode, tableNode, rowsNode, emptyNode,
    studioLinks: createStudioWorkEditorLinks(context.studioBaseUrl),
    busy: false, released: false, rows: [], searchText: "", sortKey: "series", sortDir: "asc", controls: [] };
  state.controls = [["series", "Series"], ["gallery", "Gallery"], ["works", "Works"]].map(([key, label]) => {
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
      state.rows = sortRows(state);
      renderRows(state);
    });
    return { key, label, cell, button, indicator };
  });
  searchInput.addEventListener("input", () => {
    state.searchText = searchInput.value;
    renderRows(state);
  });
  refreshButton.addEventListener("click", () => { if (!state.busy) void readReport(state); });
  rowsNode.addEventListener("click", event => {
    const button = event.target.closest("button[data-gallery-id]");
    if (button) void openGallery(state, button);
  });
  context.registerRetainedView?.({
    id: "series-galleries",
    capture: () => ({ query: state.searchText, key: state.sortKey, direction: state.sortDir }),
    restore: saved => {
      const orderChanged = state.sortKey !== saved.key || state.sortDir !== saved.direction;
      if (!orderChanged && state.searchText === saved.query) return;
      state.searchText = saved.query;
      searchInput.value = saved.query;
      state.sortKey = saved.key;
      state.sortDir = saved.direction;
      if (orderChanged) state.rows = sortRows(state);
      renderRows(state);
    },
    dispose: () => { state.released = true; }
  });
  return readReport(state);
}
