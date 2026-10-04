import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import { buildDocsMediaSnapshot } from "./docs-media-data.js";
const DEFAULT_SORT_KEY = "type";
const DEFAULT_SORT_DIR = "asc";
const SORT_KEYS = Object.freeze(["collection", "type", "file", "documents"]);
const COLUMN_LABELS = Object.freeze({
  collection: "Collection",
  type: "Type",
  file: "File name",
  documents: "Documents"
});

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function replaceRouteParams(mutator) {
  const url = new URL(window.location.href);
  mutator(url.searchParams);
  window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
}

function readRouteSort() {
  const params = new URLSearchParams(window.location.search);
  const sortKey = cleanString(params.get("report_sort")).toLowerCase();
  const sortDir = cleanString(params.get("report_dir")).toLowerCase();
  return {
    sortKey: SORT_KEYS.includes(sortKey) ? sortKey : DEFAULT_SORT_KEY,
    sortDir: sortDir === "desc" ? "desc" : DEFAULT_SORT_DIR
  };
}

function persistSort(state) {
  replaceRouteParams((params) => {
    if (state.sortKey === DEFAULT_SORT_KEY && state.sortDir === DEFAULT_SORT_DIR) {
      params.delete("report_sort");
      params.delete("report_dir");
    } else {
      params.set("report_sort", state.sortKey);
      params.set("report_dir", state.sortDir);
    }
  });
}

function reportService(context) {
  const service = context && context.reportService;
  return (
    service
    && typeof service.readMediaMetadata === "function"
    && typeof service.refreshMediaMetadata === "function"
    && typeof service.openDocsMediaSource === "function"
  ) ? service : null;
}

function searchableText(row) {
  return [
    row.collectionTitle,
    row.identity,
    ...row.documents.map((documentRecord) => documentRecord.title)
  ].map(cleanString).join(" ").toLocaleLowerCase();
}

function compareDocumentSets(collator, left, right) {
  const count = Math.min(left.length, right.length);
  for (let index = 0; index < count; index += 1) {
    const title = collator.compare(left[index].title, right[index].title);
    if (title) return title;
    const href = collator.compare(left[index].href, right[index].href);
    if (href) return href;
  }
  return left.length - right.length;
}

function compareRows(collator, sortKey, sortDir, left, right) {
  const direction = sortDir === "desc" ? -1 : 1;
  let primary;
  if (sortKey === "collection") primary = collator.compare(left.collectionTitle, right.collectionTitle);
  else if (sortKey === "type") primary = collator.compare(left.mediaType, right.mediaType);
  else if (sortKey === "file") primary = collator.compare(left.identity, right.identity);
  else {
    const emptyOrder = Number(left.documents.length === 0) - Number(right.documents.length === 0);
    primary = emptyOrder || compareDocumentSets(collator, left.documents, right.documents);
  }
  if (primary) return primary * direction;
  const collection = collator.compare(left.collectionTitle, right.collectionTitle)
    || collator.compare(left.collection, right.collection)
    || left.collection.localeCompare(right.collection);
  if (collection) return collection;
  const type = collator.compare(left.mediaType, right.mediaType);
  if (type) return type;
  return collator.compare(left.identity, right.identity)
    || left.identity.localeCompare(right.identity)
    || left.mediaTarget.role.localeCompare(right.mediaTarget.role);
}

export function buildDocsMediaProjection(rows, options) {
  const settings = options && typeof options === "object" ? options : {};
  const sortKey = SORT_KEYS.includes(settings.sortKey) ? settings.sortKey : DEFAULT_SORT_KEY;
  const sortDir = settings.sortDir === "desc" ? "desc" : DEFAULT_SORT_DIR;
  const searchText = cleanString(settings.searchText).toLocaleLowerCase();
  const collectionFilter = settings.collectionFilter == null ? "*" : settings.collectionFilter;
  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  const projectedRows = (Array.isArray(rows) ? rows : [])
    .filter((row) => collectionFilter === "*" || row.collection === collectionFilter)
    .filter((row) => !searchText || searchableText(row).includes(searchText))
    .sort((left, right) => compareRows(collator, sortKey, sortDir, left, right));
  return { rows: projectedRows, searchText, sortDir, sortKey };
}

function sortButton(state, key) {
  const label = COLUMN_LABELS[key];
  const button = document.createElement("button");
  button.type = "button";
  button.className = "docsViewerReport__sortButton";
  button.dataset.reportSort = key;
  button.textContent = label;
  const indicator = document.createElement("span");
  indicator.className = "docsViewerReport__sortIndicator";
  indicator.setAttribute("aria-hidden", "true");
  indicator.textContent = state.sortKey === key ? (state.sortDir === "asc" ? "▲" : "▼") : "";
  button.appendChild(indicator);
  button.setAttribute(
    "aria-label",
    "Sort by " + label + (state.sortKey === key
      ? (state.sortDir === "asc" ? " descending" : " ascending")
      : " ascending")
  );
  if (state.sortKey === key) button.dataset.state = "active";
  button.disabled = state.busy;
  return button;
}

function renderHead(state) {
  clearNode(state.headNode);
  SORT_KEYS.forEach((key) => state.headNode.appendChild(sortButton(state, key)));
}

function appendTextCell(rowNode, value) {
  const cell = document.createElement("span");
  cell.textContent = value;
  rowNode.appendChild(cell);
}

function appendFileCell(rowNode, row) {
  const cell = document.createElement("span");
  const link = document.createElement("a");
  link.className = "docsViewerReport__cellLink docsViewerReport__title";
  link.href = "#";
  link.textContent = row.identity;
  link.dataset.docsMediaTarget = JSON.stringify(row.mediaTarget);
  cell.appendChild(link);
  rowNode.appendChild(cell);
}

function appendDocumentsCell(rowNode, row) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  row.documents.forEach((documentRecord) => {
    const link = document.createElement("a");
    link.className = "docsViewerReport__cellLink";
    link.href = documentRecord.href;
    link.textContent = documentRecord.title;
    link.dataset.docsViewerCollection = documentRecord.target.collection;
    link.dataset.docsViewerDocId = documentRecord.target.docId;
    cell.appendChild(link);
  });
  rowNode.appendChild(cell);
}

function currentProjection(state) {
  return buildDocsMediaProjection(state.sourceRows, {
    searchText: state.searchText,
    collectionFilter: state.collectionFilter,
    sortDir: state.sortDir,
    sortKey: state.sortKey
  });
}

function renderRows(state) {
  const projection = currentProjection(state);
  renderHead(state);
  clearNode(state.rowsNode);
  state.emptyNode.hidden = projection.rows.length > 0 || state.sourceRows.length === 0;
  if (!projection.rows.length) {
    state.emptyNode.textContent = "No Docs Media rows match the current filters.";
    return;
  }
  projection.rows.forEach((row) => {
    const rowNode = document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.dataset.docsMediaType = row.mediaType;
    rowNode.dataset.docsMediaIdentity = row.identity;
    rowNode.dataset.docsMediaCollection = row.collection;
    appendTextCell(rowNode, row.collectionTitle);
    appendTextCell(rowNode, row.mediaType);
    appendFileCell(rowNode, row);
    appendDocumentsCell(rowNode, row);
    state.rowsNode.appendChild(rowNode);
  });
}

function resultStatus(state) {
  const rows = state.sourceRows.filter((row) => state.collectionFilter === "*" || row.collection === state.collectionFilter);
  const orphans = rows.filter((row) => row.documents.length === 0).length;
  const counts = orphans + "/" + rows.length + " orphaned files.";
  if (!state.snapshot) return counts;
  const refreshedAt = new Date(state.snapshot.refreshedAt).toLocaleString("en-GB", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit", hour12: false
  });
  return "Last refreshed: " + refreshedAt + "\n\n" + counts;
}

function renderResultStatus(state) {
  const parts = [];
  if (state.resultMessage) parts.push(state.resultMessage);
  if (state.snapshot || !state.resultMessage) parts.push(resultStatus(state));
  state.statusNode.textContent = parts.join("\n\n");
}

function renderCollectionFilter(state) {
  clearNode(state.collectionFilterNode);
  [{ collection: "*", title: "All" }, ...state.snapshot.owners].forEach((owner) => {
    const option = document.createElement("option");
    option.value = owner.collection;
    option.textContent = owner.title;
    state.collectionFilterNode.appendChild(option);
  });
  state.collectionFilterNode.value = state.collectionFilter;
}

function updateControls(state) {
  state.runButton.disabled = state.busy;
  state.runButton.setAttribute("aria-busy", state.busy ? "true" : "false");
  state.searchInputNode.disabled = state.busy;
  state.collectionFilterNode.disabled = state.busy || !state.snapshot;
  state.headNode.querySelectorAll("[data-report-sort]").forEach((button) => {
    button.disabled = state.busy;
  });
}

function setBusy(state, busy) {
  state.busy = Boolean(busy);
  updateControls(state);
}

function loadMedia(state, refresh = false) {
  const service = reportService(state.context);
  if (!service) {
    state.statusNode.textContent = "Local docs-management server is not configured.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "Docs Media could not run in this viewer context.";
    return Promise.resolve();
  }
  setBusy(state, true);
  state.statusNode.textContent = refresh ? "Refreshing Docs Media..." : "Loading saved Docs Media...";
  if (!state.snapshot) state.emptyNode.hidden = true;
  return (refresh ? service.refreshMediaMetadata() : service.readMediaMetadata())
    .then((payload) => buildDocsMediaSnapshot(payload, state.context))
    .then((snapshot) => {
      if (!snapshot) {
        if (refresh) throw new Error("Docs Media refresh returned no saved metadata.");
        state.resultMessage = "";
        renderResultStatus(state);
        renderRows(state);
        return;
      }
      state.snapshot = snapshot;
      state.sourceRows = snapshot.rows;
      if (state.collectionFilter !== "*" && !snapshot.owners.some((owner) => owner.collection === state.collectionFilter)) {
        state.collectionFilter = "*";
      }
      renderCollectionFilter(state);
      state.resultMessage = "";
      renderResultStatus(state);
      renderRows(state);
    })
    .catch((error) => {
      const message = error && error.message
        ? error.message
        : "Docs Media could not complete the request.";
      state.resultMessage = message + (state.snapshot ? " Showing the saved report." : " Use Run/Refresh to generate the report.");
      renderResultStatus(state);
      if (!state.snapshot) {
        state.emptyNode.hidden = false;
        state.emptyNode.textContent = "Saved Docs Media is unavailable.";
      }
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
  return service.openDocsMediaSource(target)
    .then(() => {
      state.resultMessage = "";
      if (state.snapshot) renderResultStatus(state);
    })
    .catch((error) => {
      state.resultMessage = error && error.message
        ? error.message
        : "Open in Finder failed.";
      renderResultStatus(state);
    });
}

function attachEvents(state) {
  state.runButton.addEventListener("click", () => {
    if (!state.busy) loadMedia(state, true);
  });
  state.collectionFilterNode.addEventListener("change", () => {
    state.collectionFilter = state.collectionFilterNode.value;
    renderResultStatus(state);
    renderRows(state);
    updateControls(state);
  });
  state.searchInputNode.addEventListener("input", () => {
    state.searchText = state.searchInputNode.value;
    renderRows(state);
    updateControls(state);
  });
  state.headNode.addEventListener("click", (event) => {
    const button = event.target instanceof Element
      ? event.target.closest("[data-report-sort]")
      : null;
    if (!button || state.busy) return;
    const key = cleanString(button.getAttribute("data-report-sort")).toLowerCase();
    if (!SORT_KEYS.includes(key)) return;
    if (state.sortKey === key) state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    else {
      state.sortKey = key;
      state.sortDir = "asc";
    }
    persistSort(state);
    renderRows(state);
    updateControls(state);
  });
  state.rowsNode.addEventListener("click", (event) => {
    const link = event.target instanceof Element
      ? event.target.closest("[data-docs-media-target]")
      : null;
    if (!link || state.busy) return;
    event.preventDefault();
    openFile(state, JSON.parse(link.dataset.docsMediaTarget));
  });
}

function renderShell(root) {
  root.dataset.reportId = "docs_media";
  root.dataset.reportColumns = "4";
  root.innerHTML = [
    '<div class="docsViewerReport__toolbar">',
    '  <button id="docsMediaReportRun" type="button" class="docsViewer__toolbarIconButton" aria-label="Refresh" title="Refresh"></button>',
    '  <label class="docsViewerReport__selectLabel">Collection <select id="docsMediaReportCollection" class="docsViewerReport__collectionSelect"><option value="*">All</option></select></label>',
    '  <span class="docsViewerReport__search">',
    '    <input id="docsMediaReportSearch" class="docsViewerReport__searchInput" type="search" placeholder="Search" aria-label="Search Docs Media">',
    "  </span>",
    "</div>",
    '<p class="docsViewerReport__status"></p>',
    '<div class="docsViewerReport__table">',
    '  <div class="docsViewerReport__head"></div>',
    '  <ul class="docsViewerReport__rows"></ul>',
    "</div>",
    '<p class="docsViewerReport__empty" hidden></p>'
  ].join("");
  root.querySelector("#docsMediaReportRun").appendChild(createDocsViewerToolbarIcon(root.ownerDocument, "docsViewer__icon--refresh-cw"));
  mountSearchField(root.querySelector("#docsMediaReportSearch"));
  return {
    emptyNode: root.querySelector(".docsViewerReport__empty"),
    headNode: root.querySelector(".docsViewerReport__head"),
    rowsNode: root.querySelector(".docsViewerReport__rows"),
    runButton: root.querySelector("#docsMediaReportRun"),
    collectionFilterNode: root.querySelector("#docsMediaReportCollection"),
    searchInputNode: root.querySelector("#docsMediaReportSearch"),
    statusNode: root.querySelector(".docsViewerReport__status")
  };
}

export function mountDocsMediaReport(context) {
  const routeSort = readRouteSort();
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    busy: false,
    context,
    collectionFilter: "*",
    snapshot: null,
    resultMessage: "",
    searchText: "",
    sortDir: routeSort.sortDir,
    sortKey: routeSort.sortKey,
    sourceRows: []
  }, nodes);
  renderHead(state);
  if (context.registerRetainedView) context.registerRetainedView({
    id: "docs-media",
    capture: function () { return { query: state.searchText, collection: state.collectionFilter, key: state.sortKey, direction: state.sortDir }; },
    restore: function (saved) {
      if (state.searchText === saved.query && state.collectionFilter === saved.collection && state.sortKey === saved.key && state.sortDir === saved.direction) return;
      state.searchText = saved.query; state.collectionFilter = saved.collection; state.sortKey = saved.key; state.sortDir = saved.direction;
      state.collectionFilterNode.value = saved.collection;
      state.searchInputNode.value = saved.query;
      if (!state.busy) renderResultStatus(state);
      renderRows(state); updateControls(state);
    }
  });
  attachEvents(state);
  updateControls(state);
  if (!context.managementContext) {
    state.statusNode.textContent = "Docs Media requires Working.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "Docs Media could not run in this viewer context.";
    return Promise.resolve();
  }
  return loadMedia(state);
}
