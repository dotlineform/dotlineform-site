const REPORT_SCHEMA = "docs_media_report_v1";
const DEFAULT_SCOPE = "dotlineform";
const DEFAULT_SORT_KEY = "type";
const DEFAULT_SORT_DIR = "asc";
const SORT_KEYS = Object.freeze(["type", "file", "documents"]);
const COLUMN_LABELS = Object.freeze({
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

function exactKeys(value, expected) {
  return Boolean(
    value
    && typeof value === "object"
    && !Array.isArray(value)
    && Object.keys(value).sort().join(",") === expected.slice().sort().join(",")
  );
}

function scopeTitle(value) {
  return cleanString(value).split(/[_-]+/).filter(Boolean).map((part) => (
    part.charAt(0).toUpperCase() + part.slice(1)
  )).join(" ");
}

function configuredScopes(context) {
  const configs = Array.isArray(context && context.scopeConfigs) ? context.scopeConfigs : [];
  return configs.map((config) => {
    const scopeId = cleanString(config && (config.scope_id || config.scopeId)).toLowerCase();
    return {
      scopeId,
      title: cleanString(config && config.title) || scopeTitle(scopeId)
    };
  }).filter((scope) => scope.scopeId);
}

function selectedScopeFromRoute(scopes) {
  const selected = cleanString(
    new URLSearchParams(window.location.search).get("report_scope")
  ).toLowerCase();
  if (scopes.some((scope) => scope.scopeId === selected)) return selected;
  if (scopes.some((scope) => scope.scopeId === DEFAULT_SCOPE)) return DEFAULT_SCOPE;
  return scopes[0] ? scopes[0].scopeId : "";
}

function replaceRouteParams(mutator) {
  const url = new URL(window.location.href);
  mutator(url.searchParams);
  window.history.replaceState({}, "", url.pathname + url.search + url.hash);
}

function persistSelectedScope(scopeId) {
  replaceRouteParams((params) => {
    if (scopeId) params.set("report_scope", scopeId);
    else params.delete("report_scope");
  });
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
    && typeof service.runDocsMedia === "function"
    && typeof service.openLocalTarget === "function"
  ) ? service : null;
}

function normalizeDocument(value, scope) {
  const target = value && value.target;
  const targetScope = cleanString(target && target.scope).toLowerCase();
  const subScope = cleanString(target && target.sub_scope).toLowerCase();
  const docId = cleanString(target && target.doc_id);
  const title = cleanString(value && value.title);
  const href = cleanString(value && value.href);
  if (
    !exactKeys(value, ["target", "title", "href"])
    || !exactKeys(target, ["scope", "sub_scope", "doc_id"])
    || targetScope !== scope
    || !docId
    || !title
    || !href.startsWith("/docs/?")
  ) {
    throw new Error("Docs Media document target is invalid.");
  }
  return {
    target: { scope: targetScope, subScope, docId },
    title,
    href
  };
}

function normalizeRow(value, reportScope) {
  const scope = cleanString(value && value.scope).toLowerCase();
  const mediaType = cleanString(value && value.media_type).toLowerCase();
  const identity = cleanString(value && value.identity);
  const localTarget = cleanString(value && value.local_target);
  const documents = value && value.documents;
  if (
    !exactKeys(value, ["scope", "media_type", "identity", "local_target", "documents"])
    || scope !== reportScope
    || !mediaType
    || !identity
    || identity.startsWith("/")
    || !localTarget.startsWith("docs-viewer/scopes/" + scope + "/source/media/")
    || !Array.isArray(documents)
  ) {
    throw new Error("Docs Media row is invalid.");
  }
  return {
    scope,
    mediaType,
    identity,
    localTarget,
    documents: documents.map((documentRecord) => normalizeDocument(documentRecord, scope))
  };
}

export function normalizeDocsMediaResponse(payload, requestedScope) {
  const report = payload && payload.report;
  const scope = cleanString(report && report.scope).toLowerCase();
  if (
    !exactKeys(payload, ["ok", "dry_run", "summary_text", "report"])
    || payload.ok !== true
    || !exactKeys(report, ["schema_version", "scope", "rows"])
    || report.schema_version !== REPORT_SCHEMA
    || scope !== cleanString(requestedScope).toLowerCase()
    || !Array.isArray(report.rows)
  ) {
    throw new Error("Docs Media report is invalid.");
  }
  return {
    scope,
    rows: report.rows.map((row) => normalizeRow(row, scope))
  };
}

function searchableText(row) {
  return [
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
  if (sortKey === "type") primary = collator.compare(left.mediaType, right.mediaType);
  else if (sortKey === "file") primary = collator.compare(left.identity, right.identity);
  else {
    const emptyOrder = Number(left.documents.length === 0) - Number(right.documents.length === 0);
    primary = emptyOrder || compareDocumentSets(collator, left.documents, right.documents);
  }
  if (primary) return primary * direction;
  const type = collator.compare(left.mediaType, right.mediaType);
  if (type) return type;
  return collator.compare(left.identity, right.identity);
}

export function buildDocsMediaProjection(rows, options) {
  const settings = options && typeof options === "object" ? options : {};
  const sortKey = SORT_KEYS.includes(settings.sortKey) ? settings.sortKey : DEFAULT_SORT_KEY;
  const sortDir = settings.sortDir === "desc" ? "desc" : DEFAULT_SORT_DIR;
  const searchText = cleanString(settings.searchText).toLocaleLowerCase();
  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  const projectedRows = (Array.isArray(rows) ? rows : [])
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
  link.dataset.docsMediaTarget = row.localTarget;
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
    link.dataset.docsViewerScope = documentRecord.target.scope;
    link.dataset.docsViewerSubscope = documentRecord.target.subScope;
    link.dataset.docsViewerDocId = documentRecord.target.docId;
    cell.appendChild(link);
  });
  rowNode.appendChild(cell);
}

function currentProjection(state) {
  return buildDocsMediaProjection(state.sourceRows, {
    searchText: state.searchText,
    sortDir: state.sortDir,
    sortKey: state.sortKey
  });
}

function renderRows(state) {
  const projection = currentProjection(state);
  renderHead(state);
  clearNode(state.rowsNode);
  state.emptyNode.hidden = projection.rows.length > 0;
  if (!projection.rows.length) {
    state.emptyNode.textContent = state.sourceRows.length
      ? "No Docs Media rows match the current search."
      : "No media files were found in " + state.selectedScope + ".";
    return;
  }
  projection.rows.forEach((row) => {
    const rowNode = document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.dataset.docsMediaType = row.mediaType;
    rowNode.dataset.docsMediaIdentity = row.identity;
    appendTextCell(rowNode, row.mediaType);
    appendFileCell(rowNode, row);
    appendDocumentsCell(rowNode, row);
    state.rowsNode.appendChild(rowNode);
  });
}

function resultStatus(state) {
  const count = state.sourceRows.length;
  return count + (count === 1 ? " media file in " : " media files in ") + state.selectedScope + ".";
}

function renderScopeSelect(state) {
  clearNode(state.scopeSelectNode);
  state.scopes.forEach((scope) => {
    const option = document.createElement("option");
    option.value = scope.scopeId;
    option.textContent = scope.title;
    state.scopeSelectNode.appendChild(option);
  });
  state.scopeSelectNode.value = state.selectedScope;
}

function updateControls(state) {
  state.scopeSelectNode.disabled = state.busy;
  state.runButton.disabled = state.busy;
  state.runButton.setAttribute("aria-busy", state.busy ? "true" : "false");
  state.searchInputNode.disabled = state.busy;
  state.searchClearNode.hidden = !state.searchText;
  state.searchClearNode.disabled = state.busy || !state.searchText;
  state.headNode.querySelectorAll("[data-report-sort]").forEach((button) => {
    button.disabled = state.busy;
  });
}

function setBusy(state, busy) {
  state.busy = Boolean(busy);
  updateControls(state);
}

function loadScope(state) {
  const service = reportService(state.context);
  if (!service) {
    state.statusNode.textContent = "Local docs-management server is not configured.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "Docs Media could not run in this viewer context.";
    return Promise.resolve();
  }
  setBusy(state, true);
  state.statusNode.textContent = "Loading Docs Media...";
  state.sourceRows = [];
  clearNode(state.rowsNode);
  state.emptyNode.hidden = true;
  return service.runDocsMedia({ scope: state.selectedScope })
    .then((payload) => normalizeDocsMediaResponse(payload, state.selectedScope))
    .then((report) => {
      state.sourceRows = report.rows;
      state.statusNode.textContent = resultStatus(state);
      renderRows(state);
    })
    .catch((error) => {
      state.sourceRows = [];
      clearNode(state.rowsNode);
      renderHead(state);
      state.statusNode.textContent = error && error.message
        ? error.message
        : "Docs Media refresh failed.";
      state.emptyNode.hidden = false;
      state.emptyNode.textContent = "The current Docs Media load could not complete.";
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
      state.statusNode.textContent = resultStatus(state);
    })
    .catch((error) => {
      state.statusNode.textContent = error && error.message
        ? error.message
        : "Open in Finder failed.";
    });
}

function attachEvents(state) {
  state.scopeSelectNode.addEventListener("change", () => {
    if (state.busy) return;
    state.selectedScope = cleanString(state.scopeSelectNode.value).toLowerCase();
    persistSelectedScope(state.selectedScope);
    loadScope(state);
  });
  state.runButton.addEventListener("click", () => {
    if (!state.busy) loadScope(state);
  });
  state.searchInputNode.addEventListener("input", () => {
    state.searchText = state.searchInputNode.value;
    renderRows(state);
    updateControls(state);
  });
  state.searchClearNode.addEventListener("click", () => {
    state.searchText = "";
    state.searchInputNode.value = "";
    renderRows(state);
    updateControls(state);
    state.searchInputNode.focus();
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
    openFile(state, cleanString(link.dataset.docsMediaTarget));
  });
}

function renderShell(root) {
  root.dataset.reportId = "docs_media";
  root.dataset.reportColumns = "3";
  root.innerHTML = [
    '<div class="docsViewerReport__toolbar">',
    '  <label class="docsViewerReport__selectLabel">Scope ',
    '    <select id="docsMediaReportScope" class="docsViewerReport__select"></select>',
    "  </label>",
    '  <button id="docsMediaReportRun" type="button" class="docsViewerReport__button docsViewerReport__button--pill" aria-label="Run/Refresh" title="Run/Refresh">🔄</button>',
    '  <span class="docsViewerReport__search">',
    '    <input id="docsMediaReportSearch" class="docsViewerReport__searchInput" type="search" placeholder="Search" aria-label="Search Docs Media">',
    '    <button type="button" class="docsViewerReport__searchClear" aria-label="Clear search" title="Clear search" hidden>×</button>',
    "  </span>",
    "</div>",
    '<p class="docsViewerReport__status"></p>',
    '<div class="docsViewerReport__table">',
    '  <div class="docsViewerReport__head"></div>',
    '  <ul class="docsViewerReport__rows"></ul>',
    "</div>",
    '<p class="docsViewerReport__empty" hidden></p>'
  ].join("");
  return {
    emptyNode: root.querySelector(".docsViewerReport__empty"),
    headNode: root.querySelector(".docsViewerReport__head"),
    rowsNode: root.querySelector(".docsViewerReport__rows"),
    runButton: root.querySelector("#docsMediaReportRun"),
    scopeSelectNode: root.querySelector("#docsMediaReportScope"),
    searchClearNode: root.querySelector(".docsViewerReport__searchClear"),
    searchInputNode: root.querySelector("#docsMediaReportSearch"),
    statusNode: root.querySelector(".docsViewerReport__status")
  };
}

export function mountDocsMediaReport(context) {
  const scopes = configuredScopes(context);
  const selectedScope = selectedScopeFromRoute(scopes);
  const routeSort = readRouteSort();
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    busy: false,
    context,
    scopes,
    searchText: "",
    selectedScope,
    sortDir: routeSort.sortDir,
    sortKey: routeSort.sortKey,
    sourceRows: []
  }, nodes);
  renderScopeSelect(state);
  renderHead(state);
  attachEvents(state);
  updateControls(state);
  if (!selectedScope) {
    state.statusNode.textContent = "No docs scopes are configured.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "Docs Media could not run in this viewer context.";
    return Promise.resolve();
  }
  return loadScope(state);
}
