const WORKS_SCHEMA = "catalogue_source_works_v1";
const SERIES_SCHEMA = "catalogue_source_series_v1";
const WORK_ID_PATTERN = /^[0-9]{5}$/;
const SERIES_ID_PATTERN = /^[0-9]{3}$/;
const COLUMN_KEYS = Object.freeze(["work", "year", "title", "series", "storage"]);
const COLUMN_LABELS = Object.freeze({
  work: "Work",
  year: "Year",
  title: "Title",
  series: "Series",
  storage: "Storage"
});

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

function normalizeObjectMap(payload, options) {
  const settings = options || {};
  const mapKey = settings.mapKey;
  if (
    !exactKeys(payload, ["header", mapKey])
    || !exactKeys(payload.header, settings.headerKeys)
    || payload.header.schema !== settings.schema
    || !Number.isInteger(payload.header.count)
    || payload.header.count < 0
    || !payload[mapKey]
    || typeof payload[mapKey] !== "object"
    || Array.isArray(payload[mapKey])
    || payload.header.count !== Object.keys(payload[mapKey]).length
  ) {
    throw new Error(settings.errorMessage);
  }
  return Object.entries(payload[mapKey]).map(([key, value]) => {
    return settings.normalizeRecord(key, value);
  });
}

function normalizeWorkRecord(key, value) {
  const workId = cleanString(value && value.work_id);
  const title = visibleString(value && value.title);
  const status = cleanString(value && value.status);
  const year = Number(value && value.year);
  const yearDisplay = visibleString(value && value.year_display);
  const seriesIds = Array.isArray(value && value.series_ids) ? value.series_ids.slice() : [];
  const storage = visibleString(value && value.storage_location);
  if (
    !WORK_ID_PATTERN.test(key)
    || workId !== key
    || !title
    || !["draft", "published"].includes(status)
    || !Number.isInteger(year)
    || !yearDisplay
    || !Array.isArray(value && value.series_ids)
    || !Object.prototype.hasOwnProperty.call(value, "storage_location")
    || (value.storage_location !== null && typeof value.storage_location !== "string")
    || seriesIds.some((seriesId) => {
      return typeof seriesId !== "string" || !SERIES_ID_PATTERN.test(seriesId);
    })
    || new Set(seriesIds).size !== seriesIds.length
  ) {
    throw new Error("Catalogue Works input is invalid.");
  }
  return { seriesIds, status, storage, title, workId, year, yearDisplay };
}

function normalizeSeriesRecord(key, value) {
  const seriesId = cleanString(value && value.series_id);
  const title = visibleString(value && value.title);
  const status = cleanString(value && value.status);
  if (
    !SERIES_ID_PATTERN.test(key)
    || seriesId !== key
    || !title
    || !["draft", "published"].includes(status)
  ) {
    throw new Error("Catalogue Series input is invalid.");
  }
  return { seriesId, status, title };
}

export function normalizeCatalogueWorksInputs(worksPayload, seriesPayload) {
  const works = normalizeObjectMap(worksPayload, {
    errorMessage: "Catalogue Works input is invalid.",
    headerKeys: ["count", "schema"],
    mapKey: "works",
    normalizeRecord: normalizeWorkRecord,
    schema: WORKS_SCHEMA
  });
  const series = normalizeObjectMap(seriesPayload, {
    errorMessage: "Catalogue Series input is invalid.",
    headerKeys: ["count", "schema"],
    mapKey: "series",
    normalizeRecord: normalizeSeriesRecord,
    schema: SERIES_SCHEMA
  });
  const seriesById = new Map(series.map((record) => [record.seriesId, record]));

  return works.filter((work) => work.status === "published").map((work) => {
    const memberships = work.seriesIds.map((seriesId) => {
      const record = seriesById.get(seriesId);
      if (!record) throw new Error("Catalogue Works Series membership is invalid.");
      return { seriesId: record.seriesId, title: record.title };
    });
    return {
      series: memberships,
      storage: work.storage,
      title: work.title,
      workId: work.workId,
      year: work.year,
      yearDisplay: work.yearDisplay
    };
  });
}

function rowMatches(row, query) {
  if (!query) return false;
  return [
    row.workId,
    row.title,
    ...row.series.flatMap((record) => [record.seriesId, record.title])
  ].some((value) => searchString(value).includes(query));
}

function seriesSortValue(row) {
  return row.series.map((record) => record.title + " " + record.seriesId).join(" ");
}

function compareRows(collator, left, right, key) {
  if (key === "year") return left.year - right.year;
  const values = {
    work: [left.workId, right.workId],
    title: [left.title, right.title],
    series: [seriesSortValue(left), seriesSortValue(right)],
    storage: [left.storage, right.storage]
  };
  const pair = values[key] || values.work;
  return collator.compare(pair[0], pair[1]);
}

export function buildCatalogueWorksProjection(rows, options) {
  const settings = options || {};
  const query = searchString(settings.searchText);
  const sortKey = COLUMN_KEYS.includes(settings.sortKey) ? settings.sortKey : "work";
  const sortDir = settings.sortDir === "desc" ? "desc" : "asc";
  const collator = new Intl.Collator("en", { numeric: true, sensitivity: "base" });
  const matching = query ? rows.filter((row) => rowMatches(row, query)) : [];
  matching.sort((left, right) => {
    const primary = compareRows(collator, left, right, sortKey);
    if (primary !== 0) return sortDir === "asc" ? primary : -primary;
    return collator.compare(left.workId, right.workId);
  });
  return {
    columns: COLUMN_KEYS.slice(),
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

export function serializeCatalogueWorksTsv(projection) {
  const lines = [projection.columns.map((key) => COLUMN_LABELS[key]).join("\t")];
  projection.rows.forEach((row) => {
    lines.push([
      row.workId,
      row.yearDisplay,
      row.title,
      seriesCellText(row),
      storageCellText(row)
    ].map(tsvCell).join("\t"));
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

function studioReadUrl(context, key) {
  const url = new URL("/studio/api/catalogue/read", studioOrigin(context));
  url.searchParams.set("key", key);
  return url.toString();
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
  return Promise.all([
    fetchJson(studioReadUrl(context, "catalogue_works"), "Failed to load Catalogue Works."),
    fetchJson(studioReadUrl(context, "catalogue_series"), "Failed to load Catalogue Series.")
  ]).then((inputs) => normalizeCatalogueWorksInputs(inputs[0], inputs[1]));
}

function publicCatalogueHref(context, kind, recordId) {
  const base = cleanString(context && context.publicPreviewBase).replace(/\/+$/, "");
  let preview;
  try {
    preview = new URL(base);
  } catch (error) {
    throw new Error("Local site preview is not configured.", { cause: error });
  }
  if (
    !["http:", "https:"].includes(preview.protocol)
    || !preview.hostname
    || preview.username
    || preview.password
  ) {
    throw new Error("Local site preview is not configured.");
  }
  const path = kind === "work" ? "/works/" : "/series/";
  const key = kind === "work" ? "work" : "series";
  const url = new URL(path, preview.origin);
  url.searchParams.set(key, recordId);
  return url.toString();
}

function appendLink(cell, className, href, text) {
  const link = cell.ownerDocument.createElement("a");
  link.className = className;
  link.href = href;
  link.textContent = text;
  cell.appendChild(link);
  return link;
}

function appendSeriesCell(state, rowNode, row) {
  const cell = rowNode.ownerDocument.createElement("td");
  if (!row.series.length) {
    cell.className = "catalogueWorksReport__cellMeta";
    cell.textContent = "—";
    rowNode.appendChild(cell);
    return;
  }
  const list = rowNode.ownerDocument.createElement("span");
  list.className = "catalogueWorksReport__seriesList";
  row.series.forEach((record) => {
    const link = appendLink(
      list,
      "docsViewerReport__cellLink",
      publicCatalogueHref(state.context, "series", record.seriesId),
      record.title + " [" + record.seriesId + "]"
    );
    link.dataset.seriesId = record.seriesId;
  });
  cell.appendChild(list);
  rowNode.appendChild(cell);
}

function appendRow(state, row) {
  const rowNode = state.rowsNode.ownerDocument.createElement("tr");
  rowNode.dataset.workId = row.workId;

  const workCell = rowNode.ownerDocument.createElement("td");
  appendLink(
    workCell,
    "docsViewerReport__cellLink",
    publicCatalogueHref(state.context, "work", row.workId),
    row.workId
  );
  rowNode.appendChild(workCell);

  const yearCell = rowNode.ownerDocument.createElement("td");
  yearCell.className = "catalogueWorksReport__cellMeta";
  yearCell.textContent = row.yearDisplay;
  rowNode.appendChild(yearCell);

  const titleCell = rowNode.ownerDocument.createElement("td");
  appendLink(
    titleCell,
    "docsViewerReport__cellLink docsViewerReport__title",
    publicCatalogueHref(state.context, "work", row.workId),
    row.title
  );
  rowNode.appendChild(titleCell);

  appendSeriesCell(state, rowNode, row);

  const storageCell = rowNode.ownerDocument.createElement("td");
  storageCell.className = "catalogueWorksReport__cellMeta";
  storageCell.textContent = storageCellText(row);
  rowNode.appendChild(storageCell);
  state.rowsNode.appendChild(rowNode);
}

function renderHead(state) {
  clearNode(state.headRowNode);
  COLUMN_KEYS.forEach((key) => {
    const cell = state.headRowNode.ownerDocument.createElement("th");
    cell.scope = "col";
    cell.setAttribute("aria-sort", state.sortKey === key
      ? (state.sortDir === "asc" ? "ascending" : "descending")
      : "none");
    const button = state.headRowNode.ownerDocument.createElement("button");
    button.type = "button";
    button.className = "docsViewerReport__sortButton";
    button.dataset.reportSort = key;
    button.textContent = COLUMN_LABELS[key];
    const indicator = state.headRowNode.ownerDocument.createElement("span");
    indicator.className = "docsViewerReport__sortIndicator";
    indicator.setAttribute("aria-hidden", "true");
    indicator.textContent = state.sortKey === key ? (state.sortDir === "asc" ? "▲" : "▼") : "";
    button.appendChild(indicator);
    button.setAttribute(
      "aria-label",
      "Sort by " + COLUMN_LABELS[key] + (state.sortKey === key
        ? (state.sortDir === "asc" ? " descending" : " ascending")
        : " ascending")
    );
    if (state.sortKey === key) button.dataset.state = "active";
    button.disabled = state.busy;
    cell.appendChild(button);
    state.headRowNode.appendChild(cell);
  });
}

function currentProjection(state) {
  return buildCatalogueWorksProjection(state.sourceRows, {
    searchText: state.searchText,
    sortDir: state.sortDir,
    sortKey: state.sortKey
  });
}

function renderCurrent(state) {
  if (state.failed) return;
  const projection = currentProjection(state);
  state.projection = projection;
  renderHead(state);
  clearNode(state.rowsNode);
  if (!projection.searchText) {
    state.tableNode.hidden = true;
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "Search by Work or Series to show Catalogue Works.";
    state.statusNode.textContent = projection.totalCount === 1
      ? "1 published Work loaded."
      : projection.totalCount + " published Works loaded.";
  } else if (!projection.rows.length) {
    state.tableNode.hidden = true;
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "No Catalogue Works match the current search.";
    state.statusNode.textContent = "0 of " + projection.totalCount + " published Works";
  } else {
    projection.rows.forEach((row) => appendRow(state, row));
    state.tableNode.hidden = false;
    state.emptyNode.hidden = true;
    state.emptyNode.textContent = "";
    state.statusNode.textContent = projection.rows.length + " of "
      + projection.totalCount + " published Works";
  }
  updateControls(state);
}

function updateControls(state) {
  state.searchInputNode.disabled = state.busy || state.failed;
  state.searchClearNode.hidden = !state.searchText;
  state.searchClearNode.disabled = state.busy || state.failed || !state.searchText;
  state.copyButton.disabled = state.busy || state.failed || !state.projection.rows.length;
  state.headRowNode.querySelectorAll("[data-report-sort]").forEach((button) => {
    button.disabled = state.busy || state.failed;
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
  const projection = currentProjection(state);
  return Promise.resolve(clipboard.writeText(serializeCatalogueWorksTsv(projection))).then(() => {
    state.statusNode.textContent = projection.rows.length === 1
      ? "Copied 1 Catalogue Work."
      : "Copied " + projection.rows.length + " Catalogue Works.";
  }).catch(() => {
    state.statusNode.textContent = "Copy table failed.";
  });
}

function attachEvents(state) {
  state.searchInputNode.addEventListener("input", () => {
    state.searchText = state.searchInputNode.value;
    renderCurrent(state);
  });
  state.searchClearNode.addEventListener("click", () => {
    state.searchText = "";
    state.searchInputNode.value = "";
    renderCurrent(state);
    state.searchInputNode.focus();
  });
  state.headRowNode.addEventListener("click", (event) => {
    const button = event.target && typeof event.target.closest === "function"
      ? event.target.closest("[data-report-sort]")
      : null;
    if (!button || state.busy || state.failed) return;
    const key = cleanString(button.getAttribute("data-report-sort")).toLowerCase();
    if (!COLUMN_KEYS.includes(key)) return;
    if (state.sortKey === key) state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    else {
      state.sortKey = key;
      state.sortDir = "asc";
    }
    renderCurrent(state);
  });
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
  searchInput.placeholder = "Search";
  searchInput.setAttribute("aria-label", "Search Catalogue Works");
  const searchClear = root.ownerDocument.createElement("button");
  searchClear.id = "docsCatalogueWorksReportClear";
  searchClear.className = "docsViewerReport__searchClear";
  searchClear.type = "button";
  searchClear.setAttribute("aria-label", "Clear Catalogue Works search");
  searchClear.textContent = "×";
  search.appendChild(searchInput);
  search.appendChild(searchClear);
  const copyButton = root.ownerDocument.createElement("button");
  copyButton.id = "docsCatalogueWorksReportCopy";
  copyButton.className = "docsViewerReport__button";
  copyButton.type = "button";
  copyButton.textContent = "Copy table";
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

  root.appendChild(toolbar);
  root.appendChild(status);
  root.appendChild(table);
  root.appendChild(empty);
  return {
    copyButton,
    emptyNode: empty,
    headRowNode: headRow,
    rowsNode: body,
    searchClearNode: searchClear,
    searchInputNode: searchInput,
    statusNode: status,
    tableNode: table
  };
}

export function mountCatalogueWorksReport(context) {
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    busy: true,
    context,
    failed: false,
    projection: { columns: COLUMN_KEYS.slice(), rows: [] },
    searchText: "",
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
  return loadCatalogueWorks(context).then((rows) => {
    state.sourceRows = rows;
    state.busy = false;
    renderCurrent(state);
  }).catch((error) => {
    state.sourceRows = [];
    state.busy = false;
    state.failed = true;
    state.projection = { columns: COLUMN_KEYS.slice(), rows: [] };
    clearNode(state.rowsNode);
    state.tableNode.hidden = true;
    state.statusNode.textContent = error && error.message
      ? error.message
      : "Catalogue Works failed to load.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "The current Catalogue Works report could not complete.";
    updateControls(state);
  });
}
