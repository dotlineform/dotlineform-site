const REPORT_SCHEMA = "docs_project_state_report_v2";
const LOOKUP_SCHEMA = "docs_project_state_folder_lookup_v2";
const LOCAL_TARGET_PREFIX = "dlf-local:";
const GROUP_KEYS = Object.freeze(["folder", "series"]);
const COLUMN_KEYS = Object.freeze(["folder", "series", "docs"]);
const COLUMN_LABELS = Object.freeze({
  folder: "Folder",
  series: "Series",
  docs: "Docs"
});
const CONTROL_ICON_MARKUP = Object.freeze({
  copy: [
    '<svg class="docsViewerReport__buttonIcon" data-report-icon="copy" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
    '  <rect x="9" y="9" width="10" height="10" rx="2"></rect>',
    '  <path d="M15 9V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"></path>',
    "</svg>"
  ].join(""),
  folder: [
    '<svg class="docsViewerReport__buttonIcon" data-report-icon="folder" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
    '  <path d="M3 7.5h18v10A1.5 1.5 0 0 1 19.5 19h-15A1.5 1.5 0 0 1 3 17.5z"></path>',
    '  <path d="M3 7.5v-1A1.5 1.5 0 0 1 4.5 5h5l2.5 2.5"></path>',
    "</svg>"
  ].join(""),
  list: [
    '<svg class="docsViewerReport__buttonIcon" data-report-icon="list" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
    '  <rect x="4" y="5" width="2.5" height="2.5" rx="1"></rect>',
    '  <rect x="4" y="10.75" width="2.5" height="2.5" rx="1"></rect>',
    '  <rect x="4" y="16.5" width="2.5" height="2.5" rx="1"></rect>',
    '  <path d="M10 6.25H20"></path>',
    '  <path d="M10 12H20"></path>',
    '  <path d="M10 17.75H20"></path>',
    "</svg>"
  ].join("")
});

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function visibleString(value) {
  return cleanString(value).replace(/\s+/g, " ");
}

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function setIconButton(button, icon, label) {
  button.innerHTML = CONTROL_ICON_MARKUP[icon] || "";
  button.setAttribute("aria-label", label);
  button.title = label;
}

function reportService(context) {
  return context && context.reportService && typeof context.reportService.runProjectState === "function"
    ? context.reportService
    : null;
}

function requireArray(value, label) {
  if (!Array.isArray(value)) throw new Error("Project State " + label + " is invalid.");
  return value;
}

function normalizeDocument(value) {
  const target = value && value.target;
  const declaredSubject = value && value.declared_subject;
  const docId = cleanString(target && target.doc_id);
  const title = cleanString(value && value.title);
  const href = cleanString(value && value.href);
  const subjectKind = cleanString(declaredSubject && declaredSubject.kind);
  const subjectKey = cleanString(declaredSubject && declaredSubject.key);
  const applicableSeriesIds = requireArray(
    value && value.applicable_series_ids,
    "document applicable Series"
  ).map(cleanString);
  if (
    cleanString(target && target.scope) !== "dotlineform"
    || cleanString(target && target.sub_scope) !== "projects"
    || !docId
    || !title
    || !href
    || !["folder", "work", "series"].includes(subjectKind)
    || !subjectKey
    || applicableSeriesIds.some((seriesId) => !seriesId)
    || new Set(applicableSeriesIds).size !== applicableSeriesIds.length
  ) {
    throw new Error("Project State document target is invalid.");
  }
  return {
    target,
    title,
    href,
    declaredSubject: { kind: subjectKind, key: subjectKey },
    applicableSeriesIds
  };
}

function normalizeSeries(value) {
  const target = value && value.target;
  const seriesId = cleanString(target && target.target_id);
  const title = cleanString(value && value.title);
  const href = cleanString(value && value.href);
  const workCount = Number(value && value.work_count);
  if (
    cleanString(target && target.family) !== "catalogue"
    || cleanString(target && target.target_type) !== "series"
    || !seriesId
    || !title
    || !href
    || !Number.isInteger(workCount)
    || workCount < 1
  ) {
    throw new Error("Project State Series membership is invalid.");
  }
  return { target, title, href, workCount };
}

function normalizeRow(value) {
  const folder = value && value.folder;
  const key = cleanString(folder && folder.key);
  const label = cleanString(folder && folder.label);
  const href = cleanString(folder && folder.href);
  const states = value && value.states;
  const matchedDocumentCount = Number(value && value.matched_document_count);
  const matchedWorkCount = Number(value && value.matched_work_count);
  const documents = requireArray(value && value.documents, "documents").map(normalizeDocument);
  const series = requireArray(value && value.series, "Series").map(normalizeSeries);
  const seriesIds = new Set(series.map((record) => cleanString(record.target && record.target.target_id)));
  if (
    !key.startsWith("projects/")
    || !label.startsWith("/")
    || !href.startsWith(LOCAL_TARGET_PREFIX)
    || !states
    || typeof states !== "object"
    || !Number.isInteger(matchedDocumentCount)
    || matchedDocumentCount !== documents.length
    || !Number.isInteger(matchedWorkCount)
    || matchedWorkCount < 0
    || documents.some((documentRecord) => (
      documentRecord.applicableSeriesIds.some((seriesId) => !seriesIds.has(seriesId))
    ))
  ) {
    throw new Error("Project State folder row is invalid.");
  }
  return {
    folder: { key, label, href },
    documents,
    series,
    seriesIssues: requireArray(value.series_issues, "Series issues"),
    matchedDocumentCount,
    matchedWorkCount,
    reconciliation: cleanString(states.reconciliation)
  };
}

function normalizeResponse(payload) {
  const report = payload && payload.report;
  const lookup = payload && payload.lookup;
  const generation = cleanString(report && report.generation);
  const generatedAt = cleanString(report && report.generated_at);
  if (
    !payload
    || payload.ok !== true
    || !report
    || report.schema_version !== REPORT_SCHEMA
    || !lookup
    || lookup.schema_version !== LOOKUP_SCHEMA
    || cleanString(lookup.generation) !== generation
    || !generation
    || !generatedAt
  ) {
    throw new Error("Project State report and lookup did not agree.");
  }
  return {
    generatedAt,
    generation,
    summary: report.summary && typeof report.summary === "object" ? report.summary : {},
    rows: requireArray(report.rows, "rows").map(normalizeRow)
  };
}

function publicPreviewHref(context, href) {
  const base = cleanString(context && context.publicPreviewBase).replace(/\/+$/, "");
  const path = cleanString(href);
  if (!base || !path.startsWith("/series/")) {
    throw new Error("Project State site preview is not configured.");
  }
  return new URL(path, base + "/").toString();
}

function folderLabel(row) {
  return cleanString(row && row.folder && row.folder.label).slice(1);
}

function projectionRow(row, series, documents) {
  return {
    folder: row.folder,
    documents,
    series,
    folderKey: row.folder.key
  };
}

function expandedRows(rows, groupBy) {
  const expanded = [];
  rows.forEach((row) => {
    if (groupBy !== "series") {
      expanded.push(projectionRow(row, row.series, row.documents));
      return;
    }
    if (!row.series.length) {
      expanded.push(projectionRow(row, [], row.documents));
      return;
    }
    row.series.forEach((series) => {
      const seriesId = cleanString(series.target && series.target.target_id);
      expanded.push(projectionRow(
        row,
        [series],
        row.documents.filter((documentRecord) => documentRecord.applicableSeriesIds.includes(seriesId))
      ));
    });
    const unroutedDocuments = row.documents.filter(
      (documentRecord) => !documentRecord.applicableSeriesIds.length
    );
    if (unroutedDocuments.length) expanded.push(projectionRow(row, [], unroutedDocuments));
  });
  return expanded;
}

function columnText(row, key) {
  if (key === "folder") return folderLabel(row);
  if (key === "series") return row.series.map((series) => visibleString(series.title)).join("; ");
  if (key === "docs") return row.documents.map((documentRecord) => visibleString(documentRecord.title)).join("; ");
  return "";
}

function columnIdentity(row, key) {
  if (key === "folder") return cleanString(row.folder && row.folder.key);
  if (key === "series") {
    return row.series.map((series) => cleanString(series.target && series.target.target_id)).join(";");
  }
  if (key === "docs") {
    return row.documents.map((documentRecord) => cleanString(documentRecord.target && documentRecord.target.doc_id)).join(";");
  }
  return "";
}

function searchableText(row) {
  return COLUMN_KEYS.map((key) => columnText(row, key)).join(" ").toLocaleLowerCase();
}

function compareProjectionRows(collator, sortKey, sortDir, left, right) {
  const direction = sortDir === "desc" ? -1 : 1;
  const visibleComparison = collator.compare(columnText(left, sortKey), columnText(right, sortKey));
  if (visibleComparison) return visibleComparison * direction;
  const identityComparison = collator.compare(columnIdentity(left, sortKey), columnIdentity(right, sortKey));
  if (identityComparison) return identityComparison * direction;
  return collator.compare(left.folderKey, right.folderKey);
}

export function buildProjectStateProjection(rows, options) {
  const settings = options && typeof options === "object" ? options : {};
  const groupBy = GROUP_KEYS.includes(settings.groupBy) ? settings.groupBy : "folder";
  const columns = groupBy === "series"
    ? ["series", "folder", "docs"]
    : ["folder", "series", "docs"];
  const sortKey = columns.includes(settings.sortKey) ? settings.sortKey : groupBy;
  const sortDir = settings.sortDir === "desc" ? "desc" : "asc";
  const searchText = visibleString(settings.searchText).toLocaleLowerCase();
  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  const sourceRows = Array.isArray(rows) ? rows : [];
  const projectedRows = expandedRows(sourceRows, groupBy)
    .filter((row) => !searchText || searchableText(row).includes(searchText))
    .sort((left, right) => compareProjectionRows(collator, sortKey, sortDir, left, right));
  return { columns, groupBy, rows: projectedRows, searchText, sortDir, sortKey };
}

function tsvCell(row, key) {
  return columnText(row, key).replace(/[\t\r\n]+/g, " ");
}

export function serializeProjectStateTsv(projection) {
  const columns = projection && Array.isArray(projection.columns) ? projection.columns : [];
  const rows = projection && Array.isArray(projection.rows) ? projection.rows : [];
  const lines = [columns.map((key) => COLUMN_LABELS[key] || key).join("\t")];
  rows.forEach((row) => {
    lines.push(columns.map((key) => tsvCell(row, key)).join("\t"));
  });
  return lines.join("\n");
}

function markdownText(value) {
  return visibleString(value)
    .replace(/\\/g, "\\\\")
    .replace(/\|/g, "\\|")
    .replace(/\[/g, "\\[")
    .replace(/\]/g, "\\]");
}

function markdownLink(label, href) {
  return "[" + markdownText(label) + "](" + cleanString(href) + ")";
}

function markdownCell(row, key, publicPreviewBase) {
  if (key === "folder") return markdownLink(folderLabel(row), row.folder.href);
  if (key === "series") {
    return row.series.map((series) => markdownLink(
      series.title,
      publicPreviewHref({ publicPreviewBase }, series.href)
    )).join("; ");
  }
  if (key === "docs") {
    return row.documents.map((documentRecord) => markdownLink(
      documentRecord.title,
      documentRecord.href
    )).join("; ");
  }
  return "";
}

function formatGeneratedGmt(value) {
  const date = new Date(cleanString(value));
  if (Number.isNaN(date.getTime())) throw new Error("Project State generation time is invalid.");
  const pad = (part) => String(part).padStart(2, "0");
  return [
    date.getUTCFullYear(),
    "-",
    pad(date.getUTCMonth() + 1),
    "-",
    pad(date.getUTCDate()),
    " ",
    pad(date.getUTCHours()),
    ":",
    pad(date.getUTCMinutes())
  ].join("");
}

export function serializeProjectStateMarkdown(projection, generatedAt, publicPreviewBase) {
  const columns = projection && Array.isArray(projection.columns) ? projection.columns : [];
  const rows = projection && Array.isArray(projection.rows) ? projection.rows : [];
  const headings = columns.map((key) => markdownText(COLUMN_LABELS[key] || key));
  const lines = [
    "Project State - " + formatGeneratedGmt(generatedAt),
    "",
    "| " + headings.join(" | ") + " |",
    "| " + columns.map(() => "---").join(" | ") + " |"
  ];
  rows.forEach((row) => {
    lines.push("| " + columns.map((key) => markdownCell(row, key, publicPreviewBase)).join(" | ") + " |");
  });
  return lines.join("\n");
}

function appendLink(parent, label, href) {
  const link = document.createElement("a");
  link.className = "docsViewerReport__cellLink";
  link.href = href;
  link.textContent = label;
  parent.appendChild(link);
  return link;
}

function appendFolderCell(rowNode, row) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  const link = appendLink(cell, folderLabel(row), "#");
  link.classList.add("docsViewerReport__title");
  link.dataset.docsViewerLocalTarget = row.folder.href.slice(LOCAL_TARGET_PREFIX.length);
  link.dataset.projectFolderKey = row.folder.key;
  rowNode.appendChild(cell);
}

function appendSeriesCell(rowNode, row, context) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  row.series.forEach((series) => {
    appendLink(cell, series.title, publicPreviewHref(context, series.href));
  });
  rowNode.appendChild(cell);
}

function appendDocumentsCell(rowNode, row) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  row.documents.forEach((documentRecord) => {
    const link = appendLink(cell, documentRecord.title, documentRecord.href);
    link.dataset.docsViewerScope = cleanString(documentRecord.target && documentRecord.target.scope);
    link.dataset.docsViewerSubscope = cleanString(documentRecord.target && documentRecord.target.sub_scope);
    link.dataset.docsViewerDocId = cleanString(documentRecord.target && documentRecord.target.doc_id);
  });
  rowNode.appendChild(cell);
}

function appendColumnCell(rowNode, row, key, context) {
  if (key === "folder") appendFolderCell(rowNode, row);
  else if (key === "series") appendSeriesCell(rowNode, row, context);
  else appendDocumentsCell(rowNode, row);
}

function sortButton(state, key) {
  const label = COLUMN_LABELS[key] || key;
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
    "Sort by " + label + (state.sortKey === key ? (state.sortDir === "asc" ? " descending" : " ascending") : " ascending")
  );
  if (state.sortKey === key) button.dataset.state = "active";
  button.disabled = state.busy;
  return button;
}

function renderHead(state) {
  clearNode(state.headNode);
  const columns = state.groupBy === "series"
    ? ["series", "folder", "docs"]
    : ["folder", "series", "docs"];
  columns.forEach((key) => state.headNode.appendChild(sortButton(state, key)));
}

function currentProjection(state) {
  return buildProjectStateProjection(state.sourceRows, {
    groupBy: state.groupBy,
    searchText: state.searchText,
    sortDir: state.sortDir,
    sortKey: state.sortKey
  });
}

function renderRows(state) {
  const projection = currentProjection(state);
  state.projection = projection;
  renderHead(state);
  clearNode(state.rowsNode);
  state.emptyNode.hidden = projection.rows.length > 0;
  if (!projection.rows.length) {
    state.emptyNode.textContent = state.sourceRows.length
      ? "No Project State rows match the current search."
      : "No immediate project folders were found.";
    return;
  }
  projection.rows.forEach((row) => {
    const rowNode = document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.dataset.projectFolderKey = row.folderKey;
    if (row.series[0]) {
      rowNode.dataset.projectSeriesId = cleanString(row.series[0].target && row.series[0].target.target_id);
    }
    projection.columns.forEach((key) => appendColumnCell(rowNode, row, key, state.context));
    state.rowsNode.appendChild(rowNode);
  });
}

function integerSummary(summary, key) {
  const value = Number(summary && summary[key]);
  return Number.isInteger(value) && value >= 0 ? value : 0;
}

function runContext(report) {
  const generated = report.generatedAt.slice(0, 16).replace("T", " ");
  const folders = integerSummary(report.summary, "scanned_folder_count");
  const works = integerSummary(report.summary, "matched_work_count");
  const documents = integerSummary(report.summary, "matched_document_count");
  const folderLabelText = folders === 1 ? "folder" : "folders";
  const workLabel = works === 1 ? "Work" : "Works";
  const documentLabel = documents === 1 ? "Doc" : "Docs";
  return generated + " · " + folders + " " + folderLabelText + " · " + works + " " + workLabel + " · " + documents + " " + documentLabel;
}

function updateControls(state) {
  state.runButton.disabled = state.busy;
  state.runButton.setAttribute("aria-busy", state.busy ? "true" : "false");
  const targetGroup = state.groupBy === "folder" ? "series" : "folder";
  const groupLabel = targetGroup === "series" ? "Group by Series" : "Group by Folder";
  state.groupToggleButton.dataset.groupTarget = targetGroup;
  setIconButton(state.groupToggleButton, targetGroup === "series" ? "list" : "folder", groupLabel);
  state.groupToggleButton.disabled = state.busy;
  state.searchInputNode.disabled = state.busy;
  state.searchClearNode.hidden = !state.searchText;
  state.searchClearNode.disabled = state.busy || !state.searchText;
  state.copyTableButton.disabled = state.busy || !state.generatedAt;
  state.copyMarkdownButton.disabled = state.busy || !state.generatedAt;
  state.headNode.querySelectorAll("[data-report-sort]").forEach((button) => {
    button.disabled = state.busy;
  });
}

function setBusy(state, busy) {
  state.busy = Boolean(busy);
  updateControls(state);
}

function runReport(state) {
  const service = reportService(state.context);
  if (!service) {
    state.statusNode.textContent = "Local docs-management server is not configured.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "Project State could not run in this viewer context.";
    return Promise.resolve();
  }
  setBusy(state, true);
  state.statusNode.textContent = "Running Project State...";
  state.sourceRows = [];
  state.generatedAt = "";
  state.projection = currentProjection(state);
  clearNode(state.rowsNode);
  state.emptyNode.hidden = true;
  return service.runProjectState()
    .then(normalizeResponse)
    .then((report) => {
      state.sourceRows = report.rows;
      state.generatedAt = report.generatedAt;
      state.statusNode.textContent = runContext(report);
      renderRows(state);
    })
    .catch((error) => {
      state.sourceRows = [];
      state.generatedAt = "";
      state.projection = currentProjection(state);
      clearNode(state.rowsNode);
      renderHead(state);
      state.statusNode.textContent = error && error.message
        ? error.message
        : "Project State refresh failed.";
      state.emptyNode.hidden = false;
      state.emptyNode.textContent = "The current Project State run could not complete.";
    })
    .finally(() => {
      setBusy(state, false);
    });
}

function clipboardWindow(state) {
  return state.context && state.context.window ? state.context.window : window;
}

function writeClipboard(state, text) {
  const windowRef = clipboardWindow(state);
  if (
    !windowRef.navigator
    || !windowRef.navigator.clipboard
    || typeof windowRef.navigator.clipboard.writeText !== "function"
  ) {
    return Promise.reject(new Error("Clipboard is unavailable."));
  }
  return Promise.resolve(windowRef.navigator.clipboard.writeText(text));
}

function copyProjection(state, format) {
  const projection = currentProjection(state);
  const text = format === "markdown"
    ? serializeProjectStateMarkdown(projection, state.generatedAt, state.context.publicPreviewBase)
    : serializeProjectStateTsv(projection);
  return writeClipboard(state, text).catch(() => {
    state.statusNode.textContent = format === "markdown"
      ? "Copy Markdown failed."
      : "Copy table failed.";
  });
}

function attachEvents(state) {
  state.runButton.addEventListener("click", () => {
    if (!state.busy) runReport(state);
  });
  state.groupToggleButton.addEventListener("click", () => {
    if (state.busy) return;
    state.groupBy = state.groupBy === "folder" ? "series" : "folder";
    state.sortKey = state.groupBy;
    state.sortDir = "asc";
    renderRows(state);
    updateControls(state);
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
    const button = event.target instanceof Element ? event.target.closest("[data-report-sort]") : null;
    if (!button || state.busy) return;
    const key = cleanString(button.getAttribute("data-report-sort")).toLowerCase();
    const columns = state.groupBy === "series"
      ? ["series", "folder", "docs"]
      : ["folder", "series", "docs"];
    if (!columns.includes(key)) return;
    if (state.sortKey === key) state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    else {
      state.sortKey = key;
      state.sortDir = "asc";
    }
    renderRows(state);
    updateControls(state);
  });
  state.copyTableButton.addEventListener("click", () => copyProjection(state, "tsv"));
  state.copyMarkdownButton.addEventListener("click", () => copyProjection(state, "markdown"));
}

function renderShell(root) {
  clearNode(root);
  root.dataset.reportId = "project_state";
  root.dataset.reportColumns = "3";

  const toolbar = document.createElement("div");
  toolbar.className = "docsViewerReport__toolbar";

  const runButton = document.createElement("button");
  runButton.id = "docsProjectStateReportRun";
  runButton.type = "button";
  runButton.className = "docsViewerReport__button docsViewerReport__button--pill";
  runButton.setAttribute("aria-label", "Run/Refresh");
  runButton.title = "Run/Refresh";
  runButton.textContent = "🔄";

  const groupToggle = document.createElement("button");
  groupToggle.id = "docsProjectStateReportGroup";
  groupToggle.type = "button";
  groupToggle.className = "docsViewerReport__button docsViewerReport__button--pill";

  const search = document.createElement("span");
  search.className = "docsViewerReport__search";
  const searchInput = document.createElement("input");
  searchInput.id = "docsProjectStateReportSearch";
  searchInput.className = "docsViewerReport__searchInput";
  searchInput.type = "search";
  searchInput.placeholder = "Search";
  searchInput.setAttribute("aria-label", "Search Project State");
  const searchClear = document.createElement("button");
  searchClear.type = "button";
  searchClear.className = "docsViewerReport__searchClear";
  searchClear.setAttribute("aria-label", "Clear search");
  searchClear.title = "Clear search";
  searchClear.textContent = "×";
  searchClear.hidden = true;
  search.appendChild(searchInput);
  search.appendChild(searchClear);

  const copyTable = document.createElement("button");
  copyTable.id = "docsProjectStateReportCopyTable";
  copyTable.type = "button";
  copyTable.className = "docsViewerReport__button docsViewerReport__button--pill";
  setIconButton(copyTable, "copy", "Copy table");

  const copyMarkdown = document.createElement("button");
  copyMarkdown.id = "docsProjectStateReportCopyMarkdown";
  copyMarkdown.type = "button";
  copyMarkdown.className = "docsViewerReport__button docsViewerReport__button--pill docsViewerReport__button--markdown";
  copyMarkdown.setAttribute("aria-label", "Copy Markdown");
  copyMarkdown.title = "Copy Markdown";
  copyMarkdown.textContent = "MD";

  toolbar.appendChild(runButton);
  toolbar.appendChild(groupToggle);
  toolbar.appendChild(search);
  toolbar.appendChild(copyTable);
  toolbar.appendChild(copyMarkdown);

  const status = document.createElement("p");
  status.className = "docsViewerReport__status";

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
  root.appendChild(status);
  root.appendChild(table);
  root.appendChild(empty);
  return {
    copyMarkdownButton: copyMarkdown,
    copyTableButton: copyTable,
    emptyNode: empty,
    groupToggleButton: groupToggle,
    headNode: head,
    rowsNode: rows,
    runButton,
    searchClearNode: searchClear,
    searchInputNode: searchInput,
    statusNode: status
  };
}

export function mountProjectStateReport(context) {
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    busy: false,
    context,
    generatedAt: "",
    groupBy: "folder",
    projection: null,
    searchText: "",
    sortDir: "asc",
    sortKey: "folder",
    sourceRows: []
  }, nodes);
  renderHead(state);
  attachEvents(state);
  updateControls(state);
  return runReport(state);
}
