import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import {
  COLUMN_MODEL, COPY_COLUMN_IDS, PRESENTATION_COLUMNS,
  prepareCatalogueWorksRows, projectCatalogueWorks, serializeCatalogueWorksTsv
} from "./catalogue-works-data.js";

const PAGE_SIZE = 20;
const SEARCH_DELAY_MS = 180;

function columnDefinition(id) {
  return COLUMN_MODEL.find((column) => column.id === id);
}

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function studioOrigin(context) {
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
  return studio.origin;
}

function fetchJson(url, message) {
  return fetch(url, {
    cache: "no-store",
    headers: { Accept: "application/json" }
  }).then((response) => {
    if (!response.ok) throw new Error(message);
    return response.json();
  }).catch((error) => {
    throw new Error(error && error.message ? error.message : message, { cause: error });
  });
}

function loadCatalogueWorks(context) {
  const url = new URL("/studio/catalogue-output/reports/catalogue-works/metadata.json", studioOrigin(context));
  return fetchJson(url.toString(), "Failed to load Catalogue Works metadata.");
}

function appendLink(cell, className, href, text) {
  const link = cell.ownerDocument.createElement("a");
  link.className = className;
  link.href = href;
  link.textContent = text;
  cell.appendChild(link);
  return link;
}

function applyColumnPresentation(cell, columnId) {
  const column = columnDefinition(columnId);
  cell.dataset.reportColumnId = column.id;
  cell.dataset.reportColumnVisibility = column.visibility;
  return cell;
}

function appendTextCell(rowNode, columnId, text, className) {
  const cell = applyColumnPresentation(rowNode.ownerDocument.createElement("td"), columnId);
  if (className) cell.className = className;
  cell.textContent = text;
  rowNode.appendChild(cell);
  return cell;
}

function appendSeriesCell(rowNode, row) {
  const cell = applyColumnPresentation(rowNode.ownerDocument.createElement("td"), "series");
  if (!row.series.length) {
    cell.className = "catalogueWorksReport__cellMeta";
    cell.textContent = "—";
    rowNode.appendChild(cell);
    return;
  }
  const list = rowNode.ownerDocument.createElement("span");
  list.className = "catalogueWorksReport__seriesList";
  row.series.forEach((record) => {
    const label = cell.ownerDocument.createElement("span");
    label.textContent = record.title + " [" + record.seriesId + "]";
    label.dataset.seriesId = record.seriesId;
    list.appendChild(label);
  });
  cell.appendChild(list);
  rowNode.appendChild(cell);
}

function appendRow(state, row) {
  if (!state.documentLinks.has(row.workId)) {
    state.documentLinks.set(row.workId, state.context.viewerUrlForDocument(row.workId, { collection: "catalogue" }));
  }
  const documentHref = state.documentLinks.get(row.workId);
  const rowNode = state.rowsNode.ownerDocument.createElement("tr");
  rowNode.dataset.workId = row.workId;

  const workCell = applyColumnPresentation(rowNode.ownerDocument.createElement("td"), "work");
  appendLink(
    workCell,
    "docsViewerReport__cellLink",
    documentHref,
    row.workId
  );
  rowNode.appendChild(workCell);

  appendTextCell(rowNode, "year", row.yearDisplay, "catalogueWorksReport__cellMeta");

  const titleCell = applyColumnPresentation(rowNode.ownerDocument.createElement("td"), "title");
  appendLink(
    titleCell,
    "docsViewerReport__cellLink docsViewerReport__title",
    documentHref,
    row.title
  );
  rowNode.appendChild(titleCell);

  appendSeriesCell(rowNode, row);

  appendTextCell(rowNode, "storage", row.storage === null ? "" : row.storage, "catalogueWorksReport__cellMeta");
  appendTextCell(rowNode, "medium", row.medium === null ? "" : row.medium, "catalogueWorksReport__cellMeta");
  state.rowsNode.appendChild(rowNode);
}

function mountHead(state) {
  state.sortControls = [];
  COLUMN_MODEL.forEach((column) => {
    const key = column.id;
    const cell = applyColumnPresentation(state.headRowNode.ownerDocument.createElement("th"), key);
    cell.scope = "col";
    if (!column.sortable) {
      cell.textContent = column.label;
      state.headRowNode.appendChild(cell);
      return;
    }
    const button = state.headRowNode.ownerDocument.createElement("button");
    button.type = "button";
    button.className = "docsViewerReport__sortButton";
    button.dataset.reportSort = key;
    button.textContent = column.label;
    const indicator = state.headRowNode.ownerDocument.createElement("span");
    indicator.className = "docsViewerReport__sortIndicator";
    indicator.setAttribute("aria-hidden", "true");
    button.appendChild(indicator);
    cell.appendChild(button);
    state.headRowNode.appendChild(cell);
    state.sortControls.push({ column, cell, button, indicator });
  });
}

function projectionSettings(state) {
  return { searchText: state.searchText, sortDir: state.sortDir, sortKey: state.sortKey };
}

function refreshProjection(state) {
  if (state.released || state.busy || state.failed) return;
  state.projection = projectCatalogueWorks(state.sourceRows, state.projection, projectionSettings(state));
  state.pageIndex = 0;
  renderCurrent(state);
}

function renderCurrent(state) {
  if (state.released || state.failed) return;
  const projection = state.projection;
  const pageCount = Math.max(1, Math.ceil(projection.rows.length / PAGE_SIZE));
  state.pageIndex = Math.min(state.pageIndex, pageCount - 1);
  state.pageLabelNode.textContent = (state.pageIndex + 1) + "/" + pageCount;
  state.pageLabelNode.setAttribute("aria-label", "Page " + (state.pageIndex + 1) + " of " + pageCount);
  clearNode(state.rowsNode);
  if (!projection.searchText) {
    state.tableNode.hidden = true;
    state.emptyNode.hidden = true;
    state.emptyNode.textContent = "";
    state.statusNode.textContent = projection.totalCount === 1
      ? "1 work"
      : projection.totalCount + " works";
  } else if (!projection.rows.length) {
    state.tableNode.hidden = true;
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "No Catalogue Works match the current search.";
    state.statusNode.textContent = "0 of " + projection.totalCount + " Works";
  } else {
    const start = state.pageIndex * PAGE_SIZE;
    projection.rows.slice(start, start + PAGE_SIZE).forEach((row) => appendRow(state, row));
    state.tableNode.hidden = false;
    state.emptyNode.hidden = true;
    state.emptyNode.textContent = "";
    state.statusNode.textContent = projection.rows.length + " of "
      + projection.totalCount + " Works";
  }
  updateControls(state);
  state.presentationListeners.forEach((listener) => listener());
}

function updateControls(state) {
  const resultsUnavailable = state.busy || state.failed || state.searchTimer !== null;
  state.searchInputNode.disabled = state.busy || state.failed;
  state.copyButton.disabled = resultsUnavailable || !state.projection.rows.length;
  const pageCount = Math.ceil(state.projection.rows.length / PAGE_SIZE);
  state.paginationNode.hidden = pageCount <= 1;
  state.previousPageButton.disabled = resultsUnavailable || state.pageIndex === 0;
  state.nextPageButton.disabled = resultsUnavailable || pageCount <= 1;
  const nextLabel = pageCount > 1 && state.pageIndex + 1 >= pageCount ? "First page" : "Next page";
  state.nextPageButton.setAttribute("aria-label", nextLabel);
  state.nextPageButton.title = nextLabel;
  state.sortControls.forEach(({ column, cell, button, indicator }) => {
    const active = state.sortKey === column.id;
    cell.setAttribute("aria-sort", active ? (state.sortDir === "asc" ? "ascending" : "descending") : "none");
    indicator.textContent = active ? (state.sortDir === "asc" ? "▲" : "▼") : "";
    button.dataset.state = active ? "active" : "";
    button.setAttribute("aria-label", "Sort by " + column.label
      + (active && state.sortDir === "asc" ? " descending" : " ascending"));
    button.disabled = resultsUnavailable;
  });
}

function clipboardWindow(state) {
  return state.context && state.context.window ? state.context.window : window;
}

function copyCurrentTable(state) {
  if (state.released || state.busy || state.failed || state.searchTimer !== null) return Promise.resolve();
  const windowRef = clipboardWindow(state);
  const clipboard = windowRef.navigator && windowRef.navigator.clipboard;
  if (!clipboard || typeof clipboard.writeText !== "function") {
    state.statusNode.textContent = "Copy table failed.";
    return Promise.resolve();
  }
  const projection = state.projection;
  const expanded = Boolean(state.tableNode.closest(".docsViewerReport__expandedViewport"));
  const columns = expanded
    ? COLUMN_MODEL.filter((column) => column.copy === "both" || column.copy === "expanded").map((column) => column.id)
    : projection.columns;
  return Promise.resolve(clipboard.writeText(serializeCatalogueWorksTsv(projection.rows, columns))).then(() => {
    if (state.released) return;
    state.statusNode.textContent = projection.rows.length === 1
      ? "Copied 1 Catalogue Work."
      : "Copied " + projection.rows.length + " Catalogue Works.";
  }).catch(() => {
    if (!state.released) state.statusNode.textContent = "Copy table failed.";
  });
}

function attachEvents(state) {
  function applySearch() {
    clearTimeout(state.searchTimer);
    state.searchTimer = null;
    refreshProjection(state);
  }

  state.searchInputNode.addEventListener("input", () => {
    if (state.released || state.busy || state.failed) return;
    state.searchText = state.searchInputNode.value;
    state.pageIndex = 0;
    clearTimeout(state.searchTimer);
    if (!state.searchText.trim()) {
      applySearch();
      return;
    }
    state.searchTimer = setTimeout(applySearch, SEARCH_DELAY_MS);
    updateControls(state);
  });
  state.headRowNode.addEventListener("click", (event) => {
    const button = event.target && typeof event.target.closest === "function"
      ? event.target.closest("[data-report-sort]")
      : null;
    if (!button || state.released || state.busy || state.failed || state.searchTimer !== null) return;
    const key = button.dataset.reportSort;
    if (state.sortKey === key) state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    else {
      state.sortKey = key;
      state.sortDir = "asc";
    }
    refreshProjection(state);
  });
  function changePage(step) {
    if (state.released || state.busy || state.failed || state.searchTimer !== null) return;
    const nextPage = state.pageIndex + step;
    const pageIndex = step > 0 && nextPage * PAGE_SIZE >= state.projection.rows.length ? 0 : nextPage;
    if (pageIndex < 0 || pageIndex * PAGE_SIZE >= state.projection.rows.length) return;
    state.pageIndex = pageIndex;
    renderCurrent(state);
  }
  state.previousPageButton.addEventListener("click", () => changePage(-1));
  state.nextPageButton.addEventListener("click", () => changePage(1));
  state.copyButton.addEventListener("click", () => copyCurrentTable(state));
}

function renderShell(root) {
  clearNode(root);
  root.dataset.reportId = "catalogue_works";
  root.dataset.reportPresentation = "table";

  const toolbar = root.ownerDocument.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const search = root.ownerDocument.createElement("span");
  search.className = "docsViewerReport__search";
  const searchInput = root.ownerDocument.createElement("input");
  searchInput.id = "docsCatalogueWorksReportSearch";
  searchInput.className = "docsViewerReport__searchInput";
  searchInput.type = "search";
  searchInput.placeholder = "work";
  searchInput.setAttribute("aria-label", "Search Catalogue Works");
  search.appendChild(searchInput);
  mountSearchField(searchInput, { clearLabel: "Clear Catalogue Works search" });
  const copyButton = root.ownerDocument.createElement("button");
  copyButton.id = "docsCatalogueWorksReportCopy";
  copyButton.className = "docsViewer__toolbarIconButton";
  copyButton.type = "button";
  copyButton.setAttribute("aria-label", "Copy table");
  copyButton.title = "Copy table";
  copyButton.appendChild(createDocsViewerToolbarIcon(root.ownerDocument, "docsViewer__icon--copy"));
  toolbar.appendChild(search);
  toolbar.appendChild(copyButton);

  const status = root.ownerDocument.createElement("p");
  status.className = "docsViewerReport__status";
  status.setAttribute("aria-live", "polite");
  const table = root.ownerDocument.createElement("table");
  table.className = "catalogueWorksReport__table";
  const head = root.ownerDocument.createElement("thead");
  const headRow = root.ownerDocument.createElement("tr");
  head.appendChild(headRow);
  const body = root.ownerDocument.createElement("tbody");
  table.appendChild(head);
  table.appendChild(body);
  const empty = root.ownerDocument.createElement("p");
  empty.className = "docsViewerReport__empty";

  const pagination = root.ownerDocument.createElement("nav");
  pagination.className = "catalogueWorksReport__pagination";
  pagination.setAttribute("aria-label", "Catalogue Works pages");
  const previousPageButton = root.ownerDocument.createElement("button");
  previousPageButton.type = "button";
  previousPageButton.className = "docsViewer__toolbarIconButton";
  previousPageButton.setAttribute("aria-label", "Previous page");
  previousPageButton.title = "Previous page";
  previousPageButton.appendChild(createDocsViewerToolbarIcon(root.ownerDocument, "docsViewer__icon--chevron-left"));
  const pageLabel = root.ownerDocument.createElement("span");
  pageLabel.className = "catalogueWorksReport__pageLabel";
  pageLabel.setAttribute("aria-live", "polite");
  pageLabel.setAttribute("aria-atomic", "true");
  const nextPageButton = root.ownerDocument.createElement("button");
  nextPageButton.type = "button";
  nextPageButton.className = "docsViewer__toolbarIconButton";
  nextPageButton.setAttribute("aria-label", "Next page");
  nextPageButton.title = "Next page";
  nextPageButton.appendChild(createDocsViewerToolbarIcon(root.ownerDocument, "docsViewer__icon--chevron-right"));
  pagination.append(previousPageButton, pageLabel, nextPageButton);

  root.appendChild(toolbar);
  root.appendChild(status);
  const freshness = root.ownerDocument.createElement("p");
  freshness.className = "docsViewerReport__status";
  freshness.textContent = "Catalogue data reflects the last Refresh Catalogue in Studio; the Work editor may have newer saved changes.";
  freshness.hidden = true;
  root.appendChild(freshness);
  root.appendChild(table);
  root.appendChild(empty);
  root.appendChild(pagination);
  return {
    copyButton,
    emptyNode: empty,
    freshnessNode: freshness,
    headRowNode: headRow,
    nextPageButton,
    pageLabelNode: pageLabel,
    paginationNode: pagination,
    previousPageButton,
    rowsNode: body,
    searchInputNode: searchInput,
    statusNode: status,
    tableNode: table,
    toolbarNode: toolbar
  };
}

export function mountCatalogueWorksReport(context) {
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    busy: true,
    context,
    documentLinks: new Map(),
    failed: false,
    released: false,
    pageIndex: 0,
    presentationListeners: new Set(),
    projection: { columns: COPY_COLUMN_IDS, rows: [] },
    searchText: "",
    searchTimer: null,
    sortDir: "asc",
    sortKey: "work",
    sourceRows: []
  }, nodes);
  if (context.registerRetainedView) context.registerRetainedView({
    id: "catalogue-works",
    capture: function () { return { query: state.searchText, key: state.sortKey, direction: state.sortDir, page: state.pageIndex }; },
    restore: function (saved) {
      if (state.released) return;
      if (state.searchTimer === null && state.searchText === saved.query && state.sortKey === saved.key && state.sortDir === saved.direction && state.pageIndex === saved.page) return;
      clearTimeout(state.searchTimer); state.searchTimer = null;
      state.searchText = saved.query; state.sortKey = saved.key; state.sortDir = saved.direction;
      state.searchInputNode.value = saved.query;
      state.pageIndex = saved.page;
      if (state.busy || state.failed) return;
      state.projection = projectCatalogueWorks(state.sourceRows, state.projection, projectionSettings(state));
      renderCurrent(state);
    },
    dispose: function () {
      state.released = true;
      clearTimeout(state.searchTimer); state.searchTimer = null;
      state.sourceRows = [];
      state.projection = { columns: COPY_COLUMN_IDS, rows: [] };
      state.documentLinks.clear();
      state.presentationListeners.clear();
    }
  });
  if (state.released) return Promise.resolve();
  attachEvents(state);
  mountHead(state);
  state.tableNode.hidden = true;
  state.emptyNode.hidden = true;
  state.statusNode.textContent = "Loading Catalogue Works...";
  updateControls(state);
  return loadCatalogueWorks(context).then((payload) => {
    if (state.released) return undefined;
    state.sourceRows = prepareCatalogueWorksRows(payload);
    state.busy = false;
    state.freshnessNode.hidden = false;
    state.projection = projectCatalogueWorks(state.sourceRows, null, projectionSettings(state));
    renderCurrent(state);
    return {
      expandedPresentation: {
        columns: PRESENTATION_COLUMNS,
        kind: "semantic-table",
        label: "Catalogue Works",
        toolbar: state.toolbarNode,
        subscribe: (listener) => {
          if (state.released) throw new Error("Catalogue Works report is unavailable.");
          if (typeof listener !== "function") {
            throw new Error("Catalogue Works presentation refresh requires a listener.");
          }
          state.presentationListeners.add(listener);
          return () => state.presentationListeners.delete(listener);
        },
        table: state.tableNode
      }
    };
  }).catch((error) => {
    if (state.released) return undefined;
    state.sourceRows = [];
    state.documentLinks.clear();
    state.busy = false;
    state.failed = true;
    state.projection = { columns: COPY_COLUMN_IDS, rows: [] };
    clearNode(state.rowsNode);
    state.tableNode.hidden = true;
    state.statusNode.textContent = error && error.message
      ? error.message
      : "Catalogue Works failed to load.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "The current Catalogue Works report could not complete.";
    updateControls(state);
    return undefined;
  });
}
