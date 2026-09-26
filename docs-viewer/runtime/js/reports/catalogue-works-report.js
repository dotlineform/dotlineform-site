import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import { mountDocsViewerMediaLinks } from "../shared/docs-viewer-media-detail.js";
import { loadWorkingCatalogueDocumentLinks } from "../management/docs-viewer-management-catalogue-document-links.js";

const METADATA_SCHEMA = "catalogue_works_report_metadata_v1";
const WORK_ID_PATTERN = /^[0-9]{5}$/;
const SERIES_ID_PATTERN = /^[0-9]{3}$/;
const PAGE_SIZE = 20;
const SEARCH_DELAY_MS = 180;
const SORT_COLLATOR = new Intl.Collator("en", { numeric: true, sensitivity: "base" });
const COLUMN_MODEL = Object.freeze([
  { id: "work", label: "Work", visibility: "both", sortable: true, copy: "both" },
  { id: "year", label: "Year", visibility: "both", sortable: true, copy: "both" },
  { id: "title", label: "Title", visibility: "both", sortable: true, copy: "both" },
  { id: "series", label: "Series", visibility: "both", sortable: true, copy: "both" },
  { id: "storage", label: "Storage", visibility: "both", sortable: true, copy: "both" },
  { id: "medium_type", label: "Medium type", visibility: "expanded", sortable: false, copy: "expanded" },
  { id: "medium_caption", label: "Medium caption", visibility: "expanded", sortable: false, copy: "expanded" }
].map((column) => Object.freeze(column)));
const SORTABLE_COLUMN_IDS = Object.freeze(COLUMN_MODEL.filter((column) => column.sortable).map((column) => column.id));
const COPY_COLUMNS = Object.freeze(COLUMN_MODEL.filter((column) => column.copy === "both"));
const PRESENTATION_COLUMNS = Object.freeze(COLUMN_MODEL.map((column) => Object.freeze({
  id: column.id,
  label: column.label,
  visibility: column.visibility
})));

function columnDefinition(id) {
  return COLUMN_MODEL.find((column) => column.id === id);
}

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function visibleString(value) {
  return cleanString(value).replace(/\s+/g, " ");
}

function searchString(value) {
  return visibleString(value).normalize("NFKC").toLocaleLowerCase("en");
}

function exactKeys(value, expected) {
  return Boolean(value && typeof value === "object" && !Array.isArray(value))
    && Object.keys(value).sort().join(",") === expected.slice().sort().join(",");
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

/** Validate generated metadata and prepare per-field search/sort values once per load. */
export function normalizeCatalogueWorksMetadata(payload) {
  if (
    !exactKeys(payload, ["header", "works"])
    || !exactKeys(payload.header, ["schema", "count", "version"])
    || payload.header.schema !== METADATA_SCHEMA
    || !Number.isInteger(payload.header.count)
    || payload.header.count < 0
    || typeof payload.header.version !== "string"
    || !/^[0-9a-f]{64}$/.test(payload.header.version)
    || !payload.works
    || typeof payload.works !== "object"
    || Array.isArray(payload.works)
    || payload.header.count !== Object.keys(payload.works).length
  ) {
    throw new Error("Catalogue Works metadata is invalid.");
  }
  return Object.entries(payload.works).map(([key, value]) => normalizeWorkRecord(key, value));
}

function normalizeWorkRecord(key, value) {
  if (!exactKeys(value, ["work_id", "title", "year", "year_display", "storage_location", "medium_type", "medium_caption", "series"])) {
    throw new Error("Catalogue Works metadata row is invalid.");
  }
  const workId = cleanString(value && value.work_id);
  const title = visibleString(value && value.title);
  const year = value.year;
  const yearDisplay = visibleString(value && value.year_display);
  const storage = visibleString(value && value.storage_location);
  const mediumType = visibleString(value && value.medium_type);
  const mediumCaption = visibleString(value && value.medium_caption);
  if (
    !WORK_ID_PATTERN.test(key)
    || value.work_id !== key
    || typeof value.title !== "string"
    || !title
    || !Number.isInteger(year)
    || typeof value.year_display !== "string"
    || !yearDisplay
    || (value.storage_location !== null && typeof value.storage_location !== "string")
    || (value.medium_type !== null && typeof value.medium_type !== "string")
    || (value.medium_caption !== null && typeof value.medium_caption !== "string")
    || !Array.isArray(value.series)
    || value.series.length > 1
  ) {
    throw new Error("Catalogue Works metadata row is invalid.");
  }
  const series = value.series.map((record) => {
    if (!exactKeys(record, ["series_id", "title"])
      || typeof record.series_id !== "string" || !SERIES_ID_PATTERN.test(record.series_id)
      || typeof record.title !== "string" || !visibleString(record.title)) {
      throw new Error("Catalogue Works metadata Series is invalid.");
    }
    return { seriesId: record.series_id, title: visibleString(record.title) };
  });
  const searchValues = [workId, title, ...series.flatMap((record) => [record.seriesId, record.title])].map(searchString);
  const seriesSortValue = series.map((record) => record.title + " " + record.seriesId).join(" ");
  return { mediumCaption, mediumType, searchValues, series, seriesSortValue, storage, title, workId, year, yearDisplay };
}

function rowMatches(row, query) {
  return row.searchValues.some((value) => value.includes(query));
}

function compareRows(left, right, key) {
  if (key === "year") return left.year - right.year;
  const field = key === "work" ? "workId" : key === "series" ? "seriesSortValue" : key;
  return SORT_COLLATOR.compare(left[field], right[field]);
}

/** Filter prepared rows across the whole dataset; retain all sorted matches for paging and Copy table. */
export function buildCatalogueWorksProjection(rows, options) {
  const settings = options || {};
  const query = searchString(settings.searchText);
  const sortKey = SORTABLE_COLUMN_IDS.includes(settings.sortKey) ? settings.sortKey : "work";
  const sortDir = settings.sortDir === "desc" ? "desc" : "asc";
  const matching = query ? rows.filter((row) => rowMatches(row, query)) : [];
  matching.sort((left, right) => {
    const primary = compareRows(left, right, sortKey);
    if (primary !== 0) return sortDir === "asc" ? primary : -primary;
    return SORT_COLLATOR.compare(left.workId, right.workId);
  });
  return {
    columns: COPY_COLUMNS.map((column) => column.id),
    rows: matching,
    searchText: visibleString(settings.searchText),
    sortDir,
    sortKey,
    totalCount: rows.length
  };
}

function seriesCellText(row) {
  return row.series.length
    ? row.series.map((record) => record.title + " [" + record.seriesId + "]").join("; ")
    : "—";
}

function storageCellText(row) {
  return row.storage || "—";
}

function tsvCell(value) {
  return visibleString(value).replace(/\t/g, " ");
}

function copyCellText(row, columnId) {
  const values = {
    work: row.workId,
    year: row.yearDisplay,
    title: row.title,
    series: seriesCellText(row),
    storage: storageCellText(row),
    medium_type: row.mediumType || "—",
    medium_caption: row.mediumCaption || "—"
  };
  return values[columnId] || "";
}

export function serializeCatalogueWorksTsv(projection) {
  const lines = [projection.columns.map((key) => columnDefinition(key).label).join("\t")];
  projection.rows.forEach((row) => {
    lines.push(projection.columns.map((key) => copyCellText(row, key)).map(tsvCell).join("\t"));
  });
  return lines.join("\n");
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
  return Promise.all([
    fetchJson(url.toString(), "Failed to load Catalogue Works metadata."),
    loadWorkingCatalogueDocumentLinks({ stageConfigs: context.stageConfigs, document: context.content.ownerDocument })
  ]).then((inputs) => ({
    rows: normalizeCatalogueWorksMetadata(inputs[0]),
    documentLinks: inputs[1]
  }));
}

function appendLink(cell, className, href, text) {
  const link = cell.ownerDocument.createElement(href ? "a" : "span");
  link.className = href ? className : className.replace("docsViewerReport__cellLink", "").trim();
  if (href) link.href = href;
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
    const marker = cell.ownerDocument.createElement("span");
    marker.dataset.docsContentDetail = "media";
    marker.dataset.docsMediaKind = "catalogue-series";
    marker.dataset.docsMediaId = record.seriesId;
    const link = cell.ownerDocument.createElement("button");
    link.type = "button";
    link.className = "docsViewer__mediaTextLink docsViewerReport__cellLink";
    link.dataset.docsMediaOpen = "true";
    link.textContent = record.title + " [" + record.seriesId + "]";
    link.dataset.seriesId = record.seriesId;
    marker.appendChild(link);
    list.appendChild(marker);
  });
  cell.appendChild(list);
  rowNode.appendChild(cell);
}

function appendRow(state, row) {
  const rowNode = state.rowsNode.ownerDocument.createElement("tr");
  rowNode.dataset.workId = row.workId;

  const workCell = applyColumnPresentation(rowNode.ownerDocument.createElement("td"), "work");
  appendLink(
    workCell,
    "docsViewerReport__cellLink",
    state.documentLinks.get(row.workId),
    row.workId
  );
  rowNode.appendChild(workCell);

  appendTextCell(rowNode, "year", row.yearDisplay, "catalogueWorksReport__cellMeta");

  const titleCell = applyColumnPresentation(rowNode.ownerDocument.createElement("td"), "title");
  appendLink(
    titleCell,
    "docsViewerReport__cellLink docsViewerReport__title",
    state.documentLinks.get(row.workId),
    row.title
  );
  rowNode.appendChild(titleCell);

  appendSeriesCell(rowNode, row);

  appendTextCell(rowNode, "storage", storageCellText(row), "catalogueWorksReport__cellMeta");
  appendTextCell(rowNode, "medium_type", row.mediumType || "—", "catalogueWorksReport__cellMeta");
  appendTextCell(rowNode, "medium_caption", row.mediumCaption || "—", "catalogueWorksReport__cellMeta");
  state.rowsNode.appendChild(rowNode);
}

function renderHead(state) {
  clearNode(state.headRowNode);
  COLUMN_MODEL.forEach((column) => {
    const key = column.id;
    const cell = applyColumnPresentation(state.headRowNode.ownerDocument.createElement("th"), key);
    cell.scope = "col";
    if (!column.sortable) {
      cell.textContent = column.label;
      state.headRowNode.appendChild(cell);
      return;
    }
    cell.setAttribute("aria-sort", state.sortKey === key
      ? (state.sortDir === "asc" ? "ascending" : "descending")
      : "none");
    const button = state.headRowNode.ownerDocument.createElement("button");
    button.type = "button";
    button.className = "docsViewerReport__sortButton";
    button.dataset.reportSort = key;
    button.textContent = column.label;
    const indicator = state.headRowNode.ownerDocument.createElement("span");
    indicator.className = "docsViewerReport__sortIndicator";
    indicator.setAttribute("aria-hidden", "true");
    indicator.textContent = state.sortKey === key ? (state.sortDir === "asc" ? "▲" : "▼") : "";
    button.appendChild(indicator);
    button.setAttribute(
      "aria-label",
      "Sort by " + column.label + (state.sortKey === key
        ? (state.sortDir === "asc" ? " descending" : " ascending")
        : " ascending")
    );
    if (state.sortKey === key) button.dataset.state = "active";
    button.disabled = state.busy;
    cell.appendChild(button);
    state.headRowNode.appendChild(cell);
  });
}

function refreshProjection(state) {
  state.projection = buildCatalogueWorksProjection(state.sourceRows, {
    searchText: state.searchText,
    sortDir: state.sortDir,
    sortKey: state.sortKey
  });
  state.pageIndex = 0;
  renderCurrent(state);
}

function renderCurrent(state) {
  if (state.failed) return;
  const projection = state.projection;
  const pageCount = Math.max(1, Math.ceil(projection.rows.length / PAGE_SIZE));
  state.pageIndex = Math.min(state.pageIndex, pageCount - 1);
  state.pageLabelNode.textContent = (state.pageIndex + 1) + "/" + pageCount;
  state.pageLabelNode.setAttribute("aria-label", "Page " + (state.pageIndex + 1) + " of " + pageCount);
  renderHead(state);
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
    mountDocsViewerMediaLinks({
      content: state.rowsNode,
      documentTarget: { stage: state.context.viewerStage, collection: "", docId: state.context.doc.doc_id },
      isCurrentDocument: () => state.context.content.contains(state.rowsNode),
      openMediaTarget: state.context.openMediaTarget
    });
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
  state.searchClearNode.hidden = !state.searchText;
  state.searchClearNode.disabled = state.busy || state.failed || !state.searchText;
  state.copyButton.disabled = resultsUnavailable || !state.projection.rows.length;
  state.paginationNode.hidden = !state.projection.rows.length;
  state.previousPageButton.disabled = resultsUnavailable || state.pageIndex === 0;
  state.nextPageButton.disabled = resultsUnavailable || (state.pageIndex + 1) * PAGE_SIZE >= state.projection.rows.length;
  state.headRowNode.querySelectorAll("[data-report-sort]").forEach((button) => {
    button.disabled = resultsUnavailable;
  });
}

function clipboardWindow(state) {
  return state.context && state.context.window ? state.context.window : window;
}

function copyCurrentTable(state) {
  const windowRef = clipboardWindow(state);
  const clipboard = windowRef.navigator && windowRef.navigator.clipboard;
  if (!clipboard || typeof clipboard.writeText !== "function") {
    state.statusNode.textContent = "Copy table failed.";
    return Promise.resolve();
  }
  const projection = state.projection;
  const expanded = Boolean(state.tableNode.closest(".docsViewerReport__expandedViewport"));
  const copyProjection = Object.assign({}, projection, {
    columns: COLUMN_MODEL.filter((column) => {
      return column.copy === "both" || (expanded && column.copy === "expanded");
    }).map((column) => column.id)
  });
  return Promise.resolve(clipboard.writeText(serializeCatalogueWorksTsv(copyProjection))).then(() => {
    state.statusNode.textContent = projection.rows.length === 1
      ? "Copied 1 Catalogue Work."
      : "Copied " + projection.rows.length + " Catalogue Works.";
  }).catch(() => {
    state.statusNode.textContent = "Copy table failed.";
  });
}

function attachEvents(state) {
  function applySearch() {
    clearTimeout(state.searchTimer);
    state.searchTimer = null;
    if (!state.context.reportRoot.isConnected) return;
    refreshProjection(state);
  }

  state.searchInputNode.addEventListener("input", () => {
    state.searchText = state.searchInputNode.value;
    clearTimeout(state.searchTimer);
    if (!state.searchText.trim()) {
      applySearch();
      return;
    }
    state.searchTimer = setTimeout(applySearch, SEARCH_DELAY_MS);
    updateControls(state);
  });
  state.searchClearNode.addEventListener("click", () => {
    state.searchText = "";
    state.searchInputNode.value = "";
    applySearch();
    state.searchInputNode.focus();
  });
  state.headRowNode.addEventListener("click", (event) => {
    const button = event.target && typeof event.target.closest === "function"
      ? event.target.closest("[data-report-sort]")
      : null;
    if (!button || state.busy || state.failed || state.searchTimer !== null) return;
    const key = cleanString(button.getAttribute("data-report-sort")).toLowerCase();
    if (!SORTABLE_COLUMN_IDS.includes(key)) return;
    if (state.sortKey === key) state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    else {
      state.sortKey = key;
      state.sortDir = "asc";
    }
    refreshProjection(state);
  });
  function changePage(step) {
    if (state.busy || state.failed || state.searchTimer !== null) return;
    const pageIndex = state.pageIndex + step;
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
  const searchClear = root.ownerDocument.createElement("button");
  searchClear.id = "docsCatalogueWorksReportClear";
  searchClear.className = "docsViewer__toolbarIconButton docsViewerReport__searchClear";
  searchClear.type = "button";
  searchClear.setAttribute("aria-label", "Clear Catalogue Works search");
  searchClear.title = "Clear Catalogue Works search";
  searchClear.appendChild(createDocsViewerToolbarIcon(root.ownerDocument, "docsViewer__icon--x"));
  search.appendChild(searchInput);
  search.appendChild(searchClear);
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
  root.appendChild(table);
  root.appendChild(empty);
  root.appendChild(pagination);
  return {
    copyButton,
    emptyNode: empty,
    headRowNode: headRow,
    nextPageButton,
    pageLabelNode: pageLabel,
    paginationNode: pagination,
    previousPageButton,
    rowsNode: body,
    searchClearNode: searchClear,
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
    pageIndex: 0,
    presentationListeners: new Set(),
    projection: { columns: COPY_COLUMNS.map((column) => column.id), rows: [] },
    searchText: "",
    searchTimer: null,
    sortDir: "asc",
    sortKey: "work",
    sourceRows: []
  }, nodes);
  attachEvents(state);
  renderHead(state);
  state.tableNode.hidden = true;
  state.emptyNode.hidden = true;
  state.statusNode.textContent = "Loading Catalogue Works...";
  updateControls(state);
  return loadCatalogueWorks(context).then((data) => {
    state.sourceRows = data.rows;
    state.documentLinks = data.documentLinks;
    state.busy = false;
    refreshProjection(state);
    return {
      expandedPresentation: {
        columns: PRESENTATION_COLUMNS,
        kind: "semantic-table",
        label: "Catalogue Works",
        toolbar: state.toolbarNode,
        subscribe: (listener) => {
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
    state.sourceRows = [];
    state.busy = false;
    state.failed = true;
    state.projection = { columns: COPY_COLUMNS.map((column) => column.id), rows: [] };
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
