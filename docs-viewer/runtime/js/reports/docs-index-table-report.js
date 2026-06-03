const PRESETS = {
  library_documents_admin: {
    columns: ["title", "doc_id", "viewable"],
    filters: ["non_viewable"],
    sortable: ["title", "doc_id", "viewable"],
    defaultSort: "doc_id",
    defaultDir: "asc",
    linkMode: "manage"
  },
  az_index: {
    columns: ["title"],
    filters: [],
    sortable: ["title"],
    defaultSort: "title",
    defaultDir: "asc",
    linkMode: "auto"
  }
};

const DEFAULT_PRESET = PRESETS.library_documents_admin;

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function docId(doc) {
  return cleanString(doc && doc.doc_id);
}

function docTitle(doc) {
  return cleanString(doc && doc.title) || docId(doc);
}

function docAddedDate(doc) {
  return cleanString(doc && doc.added_date);
}

function docIsViewable(doc) {
  return Boolean(doc) && doc.viewable !== false;
}

function docIsNonViewable(doc) {
  return !docIsViewable(doc);
}

function buildParentIdSet(docs) {
  const ids = new Set(docs.map(docId).filter(Boolean));
  const parentIds = new Set();
  docs.forEach((doc) => {
    const parentId = cleanString(doc && doc.parent_id);
    if (parentId && ids.has(parentId)) parentIds.add(parentId);
  });
  return parentIds;
}

function docIsParent(state, doc) {
  return state.parentIds.has(docId(doc));
}

function filterCounts(state) {
  return {
    non_viewable: state.docs.filter((doc) => docIsNonViewable(doc)).length
  };
}

function docMatchesFilters(state, doc) {
  if (state.activeFilters.has("non_viewable") && !docIsNonViewable(doc)) return false;
  if (state.activeFilters.has("parent") && !docIsParent(state, doc)) return false;
  return true;
}

function compareDocs(state, a, b) {
  let av = "";
  let bv = "";
  if (state.sortKey === "added_date") {
    av = docAddedDate(a);
    bv = docAddedDate(b);
  } else if (state.sortKey === "title") {
    av = docTitle(a);
    bv = docTitle(b);
  } else if (state.sortKey === "viewable") {
    av = docIsViewable(a) ? "1" : "0";
    bv = docIsViewable(b) ? "1" : "0";
  } else {
    av = docId(a);
    bv = docId(b);
  }
  const primary = state.collator.compare(av, bv);
  if (primary !== 0) return state.sortDir === "asc" ? primary : -primary;
  return state.collator.compare(docId(a), docId(b));
}

function readRouteState(preset) {
  const params = new URLSearchParams(window.location.search);
  let sortKey = cleanString(params.get("report_sort")).toLowerCase();
  if (!preset.sortable.includes(sortKey)) sortKey = preset.defaultSort;
  let sortDir = cleanString(params.get("report_dir")).toLowerCase();
  if (sortDir !== "asc" && sortDir !== "desc") sortDir = preset.defaultDir;
  const validFilters = new Set(preset.filters);
  const activeFilters = new Set(
    cleanString(params.get("report_filter"))
      .split(",")
      .map((item) => cleanString(item).toLowerCase())
      .filter((item) => validFilters.has(item))
  );
  return { sortKey, sortDir, activeFilters };
}

function persistRouteState(state) {
  const url = new URL(window.location.href);
  if (state.sortKey === state.preset.defaultSort && state.sortDir === state.preset.defaultDir) {
    url.searchParams.delete("report_sort");
    url.searchParams.delete("report_dir");
  } else {
    url.searchParams.set("report_sort", state.sortKey);
    url.searchParams.set("report_dir", state.sortDir);
  }
  if (state.activeFilters.size) {
    url.searchParams.set("report_filter", Array.from(state.activeFilters).sort().join(","));
  } else {
    url.searchParams.delete("report_filter");
  }
  window.history.replaceState({}, "", url.pathname + url.search + url.hash);
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function appendTextCell(row, className, text) {
  const cell = document.createElement("span");
  cell.className = className;
  cell.textContent = text;
  row.appendChild(cell);
}

function appendLinkCell(row, state, className, doc, text) {
  const link = document.createElement("a");
  link.className = className;
  link.href = state.context.viewerUrlForScope(state.sourceScope, docId(doc), {
    manage: state.preset.linkMode === "manage" || (state.preset.linkMode === "auto" && state.context.managementMode)
  });
  link.textContent = text;
  row.appendChild(link);
}

function renderFilters(state) {
  clearNode(state.filtersNode);
  const counts = filterCounts(state);
  state.preset.filters.forEach((filter) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "docsViewerReport__filter";
    button.dataset.reportFilter = filter;
    button.setAttribute("aria-pressed", state.activeFilters.has(filter) ? "true" : "false");
    button.textContent = `${filter} [${Number(counts[filter] || 0)}]`;
    state.filtersNode.appendChild(button);
  });
  state.filtersNode.hidden = state.preset.filters.length === 0;
}

function appendHeaderCell(state, row, column) {
  const label = column === "doc_id" ? "doc_id" : column.replace(/_/g, " ");
  if (state.preset.sortable.includes(column)) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "docsViewerReport__sortButton";
    button.dataset.reportSort = column;
    button.textContent = label;
    const indicator = document.createElement("span");
    indicator.className = "docsViewerReport__sortIndicator";
    indicator.setAttribute("aria-hidden", "true");
    indicator.textContent = state.sortKey === column ? (state.sortDir === "asc" ? "▲" : "▼") : "";
    button.appendChild(indicator);
    if (state.sortKey === column) button.dataset.state = "active";
    row.appendChild(button);
    return;
  }
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__headLabel";
  cell.textContent = label;
  row.appendChild(cell);
}

function appendDataCell(state, row, doc, column) {
  if (column === "doc_id") {
    appendLinkCell(row, state, "docsViewerReport__cellLink docsViewerReport__docId", doc, docId(doc));
  } else if (column === "added_date") {
    appendTextCell(row, "docsViewerReport__cellMeta docsViewerReport__date", docAddedDate(doc));
  } else if (column === "parent") {
    appendTextCell(row, "docsViewerReport__cellMeta docsViewerReport__parent", docIsParent(state, doc) ? "parent" : "");
  } else if (column === "viewable") {
    const cell = document.createElement("span");
    cell.className = "docsViewerReport__viewable" + (docIsViewable(doc) ? " is-viewable" : "");
    cell.setAttribute("aria-label", docIsViewable(doc) ? "viewable" : "not viewable");
    row.appendChild(cell);
  } else if (column === "non_viewable") {
    appendTextCell(row, "docsViewerReport__cellMeta docsViewerReport__viewable", docIsNonViewable(doc) ? "non-viewable" : "");
  } else {
    appendLinkCell(row, state, "docsViewerReport__cellLink docsViewerReport__title", doc, docTitle(doc));
  }
}

function renderRows(state) {
  const visibleDocs = state.docs
    .filter((doc) => docMatchesFilters(state, doc))
    .slice()
    .sort((a, b) => compareDocs(state, a, b));

  state.statusNode.textContent = visibleDocs.length === 1 ? "1 document" : `${visibleDocs.length} documents`;
  clearNode(state.headNode);
  clearNode(state.rowsNode);

  state.preset.columns.forEach((column) => appendHeaderCell(state, state.headNode, column));

  visibleDocs.forEach((doc) => {
    const row = document.createElement("li");
    row.className = "docsViewerReport__row";
    row.dataset.reportDocId = docId(doc);
    state.preset.columns.forEach((column) => appendDataCell(state, row, doc, column));
    state.rowsNode.appendChild(row);
  });
}

function attachEvents(state) {
  state.headNode.addEventListener("click", (event) => {
    const button = event.target instanceof Element ? event.target.closest("[data-report-sort]") : null;
    if (!button) return;
    const key = cleanString(button.getAttribute("data-report-sort")).toLowerCase();
    if (!state.preset.sortable.includes(key)) return;
    if (state.sortKey === key) {
      state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    } else {
      state.sortKey = key;
      state.sortDir = "asc";
    }
    persistRouteState(state);
    renderRows(state);
  });

  state.filtersNode.addEventListener("click", (event) => {
    const button = event.target instanceof Element ? event.target.closest("[data-report-filter]") : null;
    if (!button) return;
    const key = cleanString(button.getAttribute("data-report-filter")).toLowerCase();
    if (!state.preset.filters.includes(key)) return;
    if (state.activeFilters.has(key)) {
      state.activeFilters.delete(key);
    } else {
      state.activeFilters.add(key);
    }
    persistRouteState(state);
    renderFilters(state);
    renderRows(state);
  });
}

function renderShell(root, preset) {
  clearNode(root);
  root.dataset.reportColumns = String(preset.columns.length);

  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";

  const filters = document.createElement("div");
  filters.className = "docsViewerReport__filters";
  filters.setAttribute("aria-label", "Report filters");

  const status = document.createElement("p");
  status.className = "docsViewerReport__status";

  toolbar.appendChild(filters);
  toolbar.appendChild(status);

  const table = document.createElement("div");
  table.className = "docsViewerReport__table";

  const head = document.createElement("div");
  head.className = "docsViewerReport__head";
  head.setAttribute("role", "group");
  head.setAttribute("aria-label", "Sort report rows");

  const rows = document.createElement("ul");
  rows.className = "docsViewerReport__rows";

  table.appendChild(head);
  table.appendChild(rows);
  root.appendChild(toolbar);
  root.appendChild(table);

  return {
    filtersNode: filters,
    statusNode: status,
    headNode: head,
    rowsNode: rows
  };
}

export function mountDocsIndexTableReport(context) {
  const preset = PRESETS[context.reportMeta.preset] || DEFAULT_PRESET;
  const sourceScope = context.reportMeta.scope || context.viewerScope;
  const routeState = readRouteState(preset);
  const nodes = renderShell(context.reportRoot, preset);

  const state = Object.assign({
    context,
    preset,
    sourceScope,
    docs: [],
    parentIds: new Set(),
    collator: new Intl.Collator(undefined, { numeric: true, sensitivity: "base" })
  }, routeState, nodes);

  return context.fetchDocsIndex(sourceScope).then((payload) => {
    state.docs = Array.isArray(payload && payload.docs)
      ? payload.docs.filter((doc) => docId(doc))
      : [];
    state.parentIds = buildParentIdSet(state.docs);
    renderFilters(state);
    renderRows(state);
    attachEvents(state);
  });
}
