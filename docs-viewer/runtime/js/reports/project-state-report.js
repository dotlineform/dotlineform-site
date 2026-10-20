import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { buildProjectStateSnapshot } from "./project-state-data.js";
import { createDocsViewerToolbarIcon } from "../shared/docs-viewer-toolbar-icon.js";
import {
  appendProjectSubjectIcon
} from "./project-subject-icons.js";

const COLUMN_LABELS = Object.freeze({
  folder: "Folder",
  series: "Series",
  docs: "Docs"
});
const SUBJECT_LABELS = Object.freeze({
  folder: "Folder",
  work: "Work"
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
  button.replaceChildren(createDocsViewerToolbarIcon(button.ownerDocument, icon));
  button.setAttribute("aria-label", label);
  button.title = label;
}

function reportService(context) {
  return context && context.reportService && typeof context.reportService.readProjectState === "function"
    && typeof context.reportService.refreshProjectState === "function"
    ? context.reportService
    : null;
}

function columnText(row, key) {
  return row.text[key];
}

function compareProjectionRows(collator, sortKey, sortDir, left, right) {
  const direction = sortDir === "desc" ? -1 : 1;
  const visibleComparison = collator.compare(columnText(left, sortKey), columnText(right, sortKey));
  if (visibleComparison) return visibleComparison * direction;
  const identityComparison = collator.compare(left.identities[sortKey], right.identities[sortKey]);
  if (identityComparison) return identityComparison * direction;
  return collator.compare(left.folderKey, right.folderKey);
}

function tsvCell(row, key) {
  return columnText(row, key).replace(/[\t\r\n]+/g, " ");
}

export function serializeProjectStateTsv(projection) {
  const { columns, rows } = projection;
  const lines = [columns.map((key) => COLUMN_LABELS[key]).join("\t")];
  rows.forEach((row) => {
    lines.push(columns.map((key) => tsvCell(row, key)).join("\t"));
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
  const link = appendLink(cell, row.folder.label, "#");
  link.classList.add("docsViewerReport__title");
  link.dataset.docsViewerLocalTarget = row.folder.localTarget;
  link.dataset.projectFolderKey = row.folder.key;
  rowNode.appendChild(cell);
}

function appendSeriesCell(rowNode, row) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  row.series.forEach((series) => {
    const label = document.createElement("span");
    label.textContent = series.title;
    cell.appendChild(label);
  });
  rowNode.appendChild(cell);
}

function appendDocumentSubjectCue(link, documentRecord) {
  appendProjectSubjectIcon(link, documentRecord.declaredSubject.kind);
}

function appendDocumentsCell(rowNode, row) {
  const cell = document.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  row.documents.forEach((documentRecord) => {
    const link = appendLink(cell, "", documentRecord.href);
    link.classList.add("docsViewerReport__projectStateDocumentLink");
    appendDocumentSubjectCue(link, documentRecord);
    const title = document.createElement("span");
    title.dataset.projectStateDocumentTitle = "true";
    title.textContent = documentRecord.title;
    link.appendChild(title);
    link.setAttribute("aria-label", [
      documentRecord.title,
      SUBJECT_LABELS[documentRecord.declaredSubject.kind] + " subject " + documentRecord.declaredSubject.key
    ].join(", "));
    link.dataset.docsViewerCollection = documentRecord.target.collection;
    link.dataset.docsViewerDocId = documentRecord.target.doc_id;
  });
  rowNode.appendChild(cell);
}

function appendColumnCell(rowNode, row, key) {
  if (key === "folder") appendFolderCell(rowNode, row);
  else if (key === "series") appendSeriesCell(rowNode, row);
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

function updateSort(state) {
  const rows = state.snapshot ? state.snapshot.groups[state.groupBy] : [];
  state.sortedRows = rows.slice().sort((left, right) => (
    compareProjectionRows(state.collator, state.sortKey, state.sortDir, left, right)
  ));
}

function currentProjection(state) {
  const searchText = visibleString(state.searchText).toLocaleLowerCase();
  return {
    columns: state.groupBy === "series" ? ["series", "folder", "docs"] : ["folder", "series", "docs"],
    rows: state.sortedRows.filter((row) => !searchText || row.searchText.includes(searchText))
  };
}

function renderRows(state) {
  const projection = currentProjection(state);
  state.projection = projection;
  renderHead(state);
  clearNode(state.rowsNode);
  state.emptyNode.hidden = projection.rows.length > 0;
  if (!projection.rows.length) {
    state.emptyNode.textContent = !state.snapshot
      ? "No saved Projects metadata. Use Run/Refresh to create it."
      : state.snapshot.rows.length
        ? "No Project State rows match the current search."
        : "No immediate project folders were found.";
    return;
  }
  projection.rows.forEach((row) => {
    const rowNode = document.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.dataset.projectFolderKey = row.folderKey;
    if (row.series[0]) {
      rowNode.dataset.projectSeriesId = row.series[0].seriesId;
    }
    projection.columns.forEach((key) => appendColumnCell(rowNode, row, key));
    state.rowsNode.appendChild(rowNode);
  });
}

function runContext(snapshot) {
  const generated = snapshot.generatedAt.slice(0, 16).replace("T", " ");
  const folders = snapshot.rows.length;
  const works = snapshot.workCount;
  const documents = snapshot.documentCount;
  const folderLabelText = folders === 1 ? "folder" : "folders";
  const workLabel = works === 1 ? "Work" : "Works";
  const documentLabel = documents === 1 ? "Doc" : "Docs";
  return "Last refreshed " + generated + " UTC · " + folders + " " + folderLabelText + " · " + works + " " + workLabel + " · " + documents + " " + documentLabel;
}

function updateControls(state) {
  state.runButton.disabled = state.busy;
  state.runButton.setAttribute("aria-busy", state.busy ? "true" : "false");
  const targetGroup = state.groupBy === "folder" ? "series" : "folder";
  const groupLabel = state.groupBy === "folder"
    ? "Grouped by Folder. Switch to Series."
    : "Grouped by Series. Switch to Folder.";
  state.groupToggleButton.dataset.groupTarget = targetGroup;
  setIconButton(state.groupToggleButton,
    state.groupBy === "series" ? "docsViewer__icon--dlf-series" : "docsViewer__icon--folder", groupLabel);
  state.groupToggleButton.disabled = state.busy;
  state.searchInputNode.disabled = state.busy;
  state.copyTableButton.disabled = state.busy || !state.snapshot;
  state.headNode.querySelectorAll("[data-report-sort]").forEach((button) => {
    button.disabled = state.busy;
  });
}

function setBusy(state, busy) {
  state.busy = Boolean(busy);
  updateControls(state);
}

function loadReport(state, refresh) {
  const service = reportService(state.context);
  if (!service) {
    state.statusNode.textContent = "Local docs-management server is not configured.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "Project State could not run in this viewer context.";
    return Promise.resolve();
  }
  setBusy(state, true);
  state.statusNode.textContent = "";
  return (refresh ? service.refreshProjectState() : service.readProjectState())
    .then((payload) => {
      if (state.released) return;
      const snapshot = payload.metadata === null ? null : buildProjectStateSnapshot(payload.metadata, state.documentHref);
      state.snapshot = snapshot;
      updateSort(state);
      state.statusNode.textContent = snapshot ? runContext(snapshot) : "";
      renderRows(state);
    })
    .catch((error) => {
      if (state.released) return;
      const message = error && error.message
        ? error.message
        : "Projects metadata could not load.";
      state.statusNode.textContent = state.snapshot ? runContext(state.snapshot) + " · " + message : message;
      if (!state.snapshot) {
        state.emptyNode.hidden = false;
        state.emptyNode.textContent = "Projects metadata could not load. Use Run/Refresh to try again.";
      }
    })
    .finally(() => {
      if (!state.released) setBusy(state, false);
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

function copyProjection(state) {
  return writeClipboard(state, serializeProjectStateTsv(state.projection)).catch(() => {
    state.statusNode.textContent = "Copy table failed.";
  });
}

function attachEvents(state) {
  state.runButton.addEventListener("click", () => {
    if (!state.busy) loadReport(state, true);
  });
  state.groupToggleButton.addEventListener("click", () => {
    if (state.busy) return;
    state.groupBy = state.groupBy === "folder" ? "series" : "folder";
    state.sortKey = state.groupBy;
    state.sortDir = "asc";
    updateSort(state);
    renderRows(state);
    updateControls(state);
  });
  state.searchInputNode.addEventListener("input", () => {
    state.searchText = state.searchInputNode.value;
    renderRows(state);
    updateControls(state);
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
    updateSort(state);
    renderRows(state);
    updateControls(state);
  });
  state.copyTableButton.addEventListener("click", () => copyProjection(state));
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
  runButton.className = "docsViewer__toolbarIconButton";
  runButton.setAttribute("aria-label", "Run/Refresh");
  runButton.title = "Run/Refresh";
  runButton.appendChild(createDocsViewerToolbarIcon(document, "docsViewer__icon--refresh-cw"));

  const groupToggle = document.createElement("button");
  groupToggle.id = "docsProjectStateReportGroup";
  groupToggle.type = "button";
  groupToggle.className = "docsViewer__toolbarIconButton";

  const search = document.createElement("span");
  search.className = "docsViewerReport__search";
  const searchInput = document.createElement("input");
  searchInput.id = "docsProjectStateReportSearch";
  searchInput.className = "docsViewerReport__searchInput";
  searchInput.type = "search";
  searchInput.placeholder = "Search";
  searchInput.setAttribute("aria-label", "Search Project State");
  search.appendChild(searchInput);
  mountSearchField(searchInput);

  const copyTable = document.createElement("button");
  copyTable.id = "docsProjectStateReportCopyTable";
  copyTable.type = "button";
  copyTable.className = "docsViewer__toolbarIconButton";
  setIconButton(copyTable, "docsViewer__icon--copy", "Copy table");

  toolbar.appendChild(runButton);
  toolbar.appendChild(groupToggle);
  toolbar.appendChild(search);
  toolbar.appendChild(copyTable);

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
    copyTableButton: copyTable,
    emptyNode: empty,
    groupToggleButton: groupToggle,
    headNode: head,
    rowsNode: rows,
    runButton,
    searchInputNode: searchInput,
    statusNode: status
  };
}

export function mountProjectStateReport(context) {
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    busy: false,
    context,
    documentHref: (docId) => context.viewerUrlForDocument(docId, { collection: "works" }),
    collator: new Intl.Collator(undefined, { numeric: true, sensitivity: "base" }),
    groupBy: "folder",
    projection: null,
    released: false,
    searchText: "",
    sortDir: "asc",
    sortKey: "folder",
    snapshot: null,
    sortedRows: []
  }, nodes);
  renderHead(state);
  if (context.registerRetainedView) context.registerRetainedView({
    id: "project-state",
    capture: function () { return { query: state.searchText, group: state.groupBy, key: state.sortKey, direction: state.sortDir }; },
    restore: function (saved) {
      const orderChanged = state.groupBy !== saved.group || state.sortKey !== saved.key || state.sortDir !== saved.direction;
      if (!orderChanged && state.searchText === saved.query) return;
      state.searchText = saved.query;
      state.groupBy = saved.group;
      state.sortKey = saved.key;
      state.sortDir = saved.direction;
      state.searchInputNode.value = saved.query;
      if (orderChanged) updateSort(state);
      renderRows(state);
      updateControls(state);
    },
    dispose: function () {
      state.released = true;
      state.snapshot = null;
      state.sortedRows = [];
      state.projection = null;
    }
  });
  attachEvents(state);
  updateControls(state);
  return loadReport(state, false);
}
