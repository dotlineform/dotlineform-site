const DEFAULT_SORT_KEY = "title";
const DEFAULT_SORT_DIR = "asc";
const SORT_KEYS = Object.freeze(["title", "identity", "document"]);

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function configuredScopes(context) {
  const scopes = Array.isArray(context && context.scopeConfigs) ? context.scopeConfigs : [];
  return scopes.map((scope) => ({
    scopeId: cleanString(scope && (scope.scope_id || scope.scopeId)).toLowerCase(),
    title: cleanString(scope && scope.title) || cleanString(scope && (scope.scope_id || scope.scopeId))
  })).filter((scope) => scope.scopeId);
}

function selectedScopeFromRoute(scopes, fallbackScope) {
  const params = new URLSearchParams(window.location.search);
  const selected = cleanString(params.get("report_scope")).toLowerCase();
  if (scopes.some((scope) => scope.scopeId === selected)) return selected;
  const fallback = cleanString(fallbackScope).toLowerCase();
  if (scopes.some((scope) => scope.scopeId === fallback)) return fallback;
  return scopes[0] ? scopes[0].scopeId : "";
}

function persistSelectedScope(scopeId) {
  const url = new URL(window.location.href);
  if (scopeId) url.searchParams.set("report_scope", scopeId);
  else url.searchParams.delete("report_scope");
  window.history.replaceState({}, "", url.pathname + url.search + url.hash);
}

function reportService(context) {
  return context && context.reportService && typeof context.reportService.readSemanticTokens === "function"
    ? context.reportService
    : null;
}

function readRouteSort() {
  const params = new URLSearchParams(window.location.search);
  const requestedKey = cleanString(params.get("report_sort")).toLowerCase();
  const requestedDir = cleanString(params.get("report_dir")).toLowerCase();
  return {
    sortKey: SORT_KEYS.includes(requestedKey) ? requestedKey : DEFAULT_SORT_KEY,
    sortDir: requestedDir === "desc" ? "desc" : DEFAULT_SORT_DIR
  };
}

function persistSort(state) {
  const url = new URL(window.location.href);
  if (state.sortKey === DEFAULT_SORT_KEY && state.sortDir === DEFAULT_SORT_DIR) {
    url.searchParams.delete("report_sort");
    url.searchParams.delete("report_dir");
  } else {
    url.searchParams.set("report_sort", state.sortKey);
    url.searchParams.set("report_dir", state.sortDir);
  }
  window.history.replaceState({}, "", url.pathname + url.search + url.hash);
}

function flattenDocs(rows, target) {
  (Array.isArray(rows) ? rows : []).forEach((row) => {
    if (!row || typeof row !== "object") return;
    const docId = cleanString(row.doc_id);
    if (docId) target.set(docId, cleanString(row.title) || docId);
    flattenDocs(row.children, target);
  });
  return target;
}

function normalizeOccurrences(payload) {
  const rows = Array.isArray(payload && payload.occurrences) ? payload.occurrences : [];
  return rows.map((row) => ({
    family: cleanString(row && row.family),
    targetType: cleanString(row && row.target_type),
    targetId: cleanString(row && row.target_id),
    title: cleanString(row && row.title),
    sourceDocId: cleanString(row && row.source_doc_id),
    raw: cleanString(row && row.raw)
  })).filter((row) => row.family && row.targetType && row.targetId && row.sourceDocId);
}

function tokenIdentity(row) {
  return `${row.family}:${row.targetType}:${row.targetId}`;
}

function tokenLabel(row) {
  return row.title || tokenIdentity(row);
}

function documentLabel(state, row) {
  return state.documentTitles.get(row.sourceDocId) || row.sourceDocId;
}

function sortValue(state, row, key) {
  if (key === "identity") return tokenIdentity(row);
  if (key === "document") return documentLabel(state, row);
  return tokenLabel(row);
}

function compareRows(state, left, right) {
  const direction = state.sortDir === "desc" ? -1 : 1;
  const primary = state.collator.compare(
    sortValue(state, left, state.sortKey),
    sortValue(state, right, state.sortKey)
  );
  if (primary !== 0) return primary * direction;
  for (const key of SORT_KEYS) {
    if (key === state.sortKey) continue;
    const fallback = state.collator.compare(
      sortValue(state, left, key),
      sortValue(state, right, key)
    );
    if (fallback !== 0) return fallback;
  }
  return 0;
}

function appendTitleCell(row, occurrence) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__title";
  cell.textContent = tokenLabel(occurrence);
  row.appendChild(cell);
}

function appendIdentityCell(row, occurrence) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellMeta";
  cell.textContent = tokenIdentity(occurrence);
  row.appendChild(cell);
}

function appendDocumentCell(row, state, occurrence) {
  const link = document.createElement("a");
  link.className = "docsViewerReport__cellLink docsViewerReport__title";
  link.href = state.context.viewerUrlForScope(
    state.selectedScope,
    occurrence.sourceDocId,
    { manage: true }
  );
  link.textContent = documentLabel(state, occurrence);
  row.appendChild(link);
}

function sortButton(state, key, label) {
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
  if (state.sortKey === key) button.dataset.state = "active";
  return button;
}

function renderHead(state) {
  clearNode(state.headNode);
  state.headNode.appendChild(sortButton(state, "title", "title"));
  state.headNode.appendChild(sortButton(state, "identity", "identity"));
  state.headNode.appendChild(sortButton(state, "document", "document"));
}

function renderRows(state) {
  renderHead(state);
  clearNode(state.rowsNode);
  const rows = state.occurrences.slice().sort((left, right) => compareRows(state, left, right));
  state.statusNode.textContent = rows.length === 1 ? "1 semantic token" : `${rows.length} semantic tokens`;
  state.emptyNode.hidden = rows.length > 0;
  if (!rows.length) {
    state.emptyNode.textContent = `No resolved semantic tokens found in ${state.selectedScope}.`;
    return;
  }
  rows.forEach((occurrence) => {
    const row = document.createElement("li");
    row.className = "docsViewerReport__row";
    row.dataset.reportDocId = occurrence.sourceDocId;
    appendTitleCell(row, occurrence);
    appendIdentityCell(row, occurrence);
    appendDocumentCell(row, state, occurrence);
    state.rowsNode.appendChild(row);
  });
}

function renderScopeSelect(state) {
  clearNode(state.scopeSelectNode);
  state.scopes.forEach((scope) => {
    const option = document.createElement("option");
    option.value = scope.scopeId;
    option.textContent = scope.title || scope.scopeId;
    state.scopeSelectNode.appendChild(option);
  });
  state.scopeSelectNode.value = state.selectedScope;
}

function loadScope(state) {
  const service = reportService(state.context);
  if (!service) {
    return Promise.reject(new Error("Local docs-management server is not configured."));
  }
  state.statusNode.textContent = "Loading semantic tokens...";
  state.emptyNode.hidden = true;
  clearNode(state.rowsNode);
  return Promise.all([
    service.readSemanticTokens({ scope: state.selectedScope }),
    state.context.fetchDocsIndexTree(state.selectedScope)
  ]).then(([payload, indexPayload]) => {
    state.occurrences = normalizeOccurrences(payload);
    state.documentTitles = flattenDocs(indexPayload && indexPayload.docs, new Map());
    renderRows(state);
  }).catch((error) => {
    state.occurrences = [];
    state.documentTitles = new Map();
    renderHead(state);
    state.statusNode.textContent = error && error.message
      ? error.message
      : "Failed to load semantic tokens.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "Semantic-token usage data is unavailable for this scope.";
  });
}

function attachEvents(state) {
  state.scopeSelectNode.addEventListener("change", () => {
    state.selectedScope = cleanString(state.scopeSelectNode.value).toLowerCase();
    persistSelectedScope(state.selectedScope);
    loadScope(state);
  });
  state.headNode.addEventListener("click", (event) => {
    const button = event.target instanceof Element ? event.target.closest("[data-report-sort]") : null;
    if (!button) return;
    const key = cleanString(button.getAttribute("data-report-sort")).toLowerCase();
    if (!SORT_KEYS.includes(key)) return;
    if (state.sortKey === key) state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    else {
      state.sortKey = key;
      state.sortDir = "asc";
    }
    persistSort(state);
    renderRows(state);
  });
}

function renderShell(root) {
  clearNode(root);
  root.dataset.reportId = "semantic_tokens";
  root.dataset.reportColumns = "3";

  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";
  const label = document.createElement("label");
  label.className = "docsViewerReport__selectLabel";
  label.textContent = "Scope ";
  const select = document.createElement("select");
  select.className = "docsViewerReport__select";
  label.appendChild(select);
  const status = document.createElement("p");
  status.className = "docsViewerReport__status";
  toolbar.appendChild(label);
  toolbar.appendChild(status);

  const table = document.createElement("div");
  table.className = "docsViewerReport__table";
  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  const rows = document.createElement("ul");
  rows.className = "docsViewerReport__rows";
  const empty = document.createElement("p");
  empty.className = "docsViewerReport__empty";
  empty.hidden = true;
  table.appendChild(head);
  table.appendChild(rows);
  root.appendChild(toolbar);
  root.appendChild(table);
  root.appendChild(empty);
  return {
    scopeSelectNode: select,
    statusNode: status,
    headNode: head,
    rowsNode: rows,
    emptyNode: empty
  };
}

export function mountSemanticTokensReport(context) {
  const scopes = configuredScopes(context);
  const selectedScope = selectedScopeFromRoute(
    scopes,
    cleanString(context.reportMeta && context.reportMeta.scope) || cleanString(context.viewerScope)
  );
  const routeSort = readRouteSort();
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    context,
    scopes,
    selectedScope,
    occurrences: [],
    documentTitles: new Map(),
    collator: new Intl.Collator(undefined, { numeric: true, sensitivity: "base" }),
    sortKey: routeSort.sortKey,
    sortDir: routeSort.sortDir
  }, nodes);
  renderScopeSelect(state);
  renderHead(state);
  attachEvents(state);
  if (!selectedScope) {
    state.statusNode.textContent = "No docs scopes are configured.";
    return Promise.resolve();
  }
  return loadScope(state);
}
