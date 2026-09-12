const DEFAULT_SORT_KEY = "title";
const DEFAULT_SORT_DIR = "asc";
const SORT_KEYS = Object.freeze(["title", "identity", "document"]);

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function requireAnalysisWorking(context) {
  if (context.viewerScope !== "analysis" || context.viewerStage !== "working") {
    throw new Error("Semantic Tokens is available only in Analysis Working.");
  }
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

/** Pair occurrences with response-owned source locations without guessing collection identity. */
export function readSemanticTokenRows(payload) {
  if (!payload || payload.scope !== "analysis" || payload.stage !== "working"
    || !Array.isArray(payload.occurrences) || !Array.isArray(payload.source_documents)) {
    throw new Error("Semantic-token report data does not match its scope/stage.");
  }
  const key = (target) => JSON.stringify([target.scope, target.sub_scope, target.doc_id]);
  const documents = new Map(payload.source_documents.map((document) => [key(document.target), document]));
  return payload.occurrences.map((row) => {
    const source = documents.get(key({ scope: row.source_scope, sub_scope: row.source_sub_scope || "", doc_id: row.source_doc_id }));
    if (!source) throw new Error("Semantic-token source document is unavailable.");
    return {
      family: cleanString(row.family),
      targetType: cleanString(row.target_type),
      targetId: cleanString(row.target_id),
      title: cleanString(row.title),
      sourceDocId: cleanString(row.source_doc_id),
      sourceSubScope: cleanString(row.source_sub_scope),
      sourceTitle: source.title,
      sourceHref: source.href,
      raw: cleanString(row.raw)
    };
  });
}

/** Read the Analysis Working inventory through the existing local report service. */
export async function loadSemanticTokenRows(context) {
  requireAnalysisWorking(context);
  const payload = await reportService(context).readSemanticTokens({ scope: "analysis", stage: "working" });
  return readSemanticTokenRows(payload);
}

function tokenIdentity(row) {
  return `${row.family}:${row.targetType}:${row.targetId}`;
}

function tokenLabel(row) {
  return row.title || tokenIdentity(row);
}

function documentLabel(row) {
  return row.sourceTitle || row.sourceDocId;
}

function sortValue(row, key) {
  if (key === "identity") return tokenIdentity(row);
  if (key === "document") return documentLabel(row);
  return tokenLabel(row);
}

function compareRows(state, left, right) {
  const direction = state.sortDir === "desc" ? -1 : 1;
  const primary = state.collator.compare(
    sortValue(left, state.sortKey),
    sortValue(right, state.sortKey)
  );
  if (primary !== 0) return primary * direction;
  for (const key of SORT_KEYS) {
    if (key === state.sortKey) continue;
    const fallback = state.collator.compare(
      sortValue(left, key),
      sortValue(right, key)
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

function appendDocumentCell(row, occurrence) {
  const link = document.createElement("a");
  link.className = "docsViewerReport__cellLink docsViewerReport__title";
  link.href = occurrence.sourceHref;
  link.textContent = documentLabel(occurrence);
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
    state.emptyNode.textContent = "No semantic tokens found in Analysis Working.";
    return;
  }
  rows.forEach((occurrence) => {
    const row = document.createElement("li");
    row.className = "docsViewerReport__row";
    row.dataset.reportDocId = occurrence.sourceDocId;
    appendTitleCell(row, occurrence);
    appendIdentityCell(row, occurrence);
    appendDocumentCell(row, occurrence);
    state.rowsNode.appendChild(row);
  });
}

function loadScope(state) {
  const service = reportService(state.context);
  if (!service) {
    return Promise.reject(new Error("Local docs-management server is not configured."));
  }
  state.statusNode.textContent = "Loading semantic tokens...";
  state.emptyNode.hidden = true;
  clearNode(state.rowsNode);
  return loadSemanticTokenRows(state.context).then((rows) => {
    state.occurrences = rows;
    renderRows(state);
  }).catch((error) => {
    state.occurrences = [];
    renderHead(state);
    state.statusNode.textContent = error && error.message
      ? error.message
      : "Failed to load semantic tokens.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "Semantic-token usage data is unavailable for this scope.";
  });
}

function attachEvents(state) {
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
  const status = document.createElement("p");
  status.className = "docsViewerReport__status";
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
    statusNode: status,
    headNode: head,
    rowsNode: rows,
    emptyNode: empty
  };
}

export function mountSemanticTokensReport(context) {
  requireAnalysisWorking(context);
  const routeSort = readRouteSort();
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    context,
    occurrences: [],
    collator: new Intl.Collator(undefined, { numeric: true, sensitivity: "base" }),
    sortKey: routeSort.sortKey,
    sortDir: routeSort.sortDir
  }, nodes);
  renderHead(state);
  attachEvents(state);
  return loadScope(state);
}
