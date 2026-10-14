import { buildWorksSnapshot, commitWorksDocument } from "./works-report-data.js";
import { appendProjectSubjectIcon } from "./project-subject-icons.js";

function clearNode(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
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

async function loadWorksInputs(context) {
  const collection = context.workspaceConfig.collectionsById.get("works");
  if (!collection) throw new Error("Working Works manifest is not configured.");
  return Promise.all([
    context.reportService.readWorkDocumentCoverage(),
    fetchJson(collection.manifestUrl, "Failed to load Working Works manifest.")
  ]);
}

function appendDocumentsCell(rowNode, row) {
  const cell = rowNode.ownerDocument.createElement("span");
  cell.className = "docsViewerReport__cellStack";
  if (!row.documents.length) cell.setAttribute("aria-label", "No Work documents");
  row.documents.forEach((documentRecord) => {
    const link = rowNode.ownerDocument.createElement("a");
    link.className = "docsViewerReport__cellLink";
    link.dataset.projectDocId = documentRecord.docId;
    link.dataset.projectSubjectKind = documentRecord.subject.kind;
    link.dataset.projectSubjectKey = documentRecord.subject.key;
    link.href = documentRecord.href;
    appendProjectSubjectIcon(link, documentRecord.subject.kind);
    const label = rowNode.ownerDocument.createElement("span");
    label.textContent = documentRecord.title;
    link.appendChild(label);
    link.setAttribute(
      "aria-label",
      documentRecord.title + ", " + documentRecord.subject.kind + " subject "
        + documentRecord.subject.key
    );
    cell.appendChild(link);
  });
  rowNode.appendChild(cell);
}

function renderProjection(state, projection) {
  clearNode(state.rowsNode);
  state.emptyNode.hidden = projection.rows.length > 0;
  state.emptyNode.textContent = projection.rows.length ? "" : "No Series were found in refreshed Catalogue data.";
  projection.rows.forEach((row) => {
    const rowNode = state.rowsNode.ownerDocument.createElement("li");
    rowNode.className = "docsViewerReport__row";
    rowNode.dataset.seriesId = row.seriesId;
    const seriesTitle = rowNode.ownerDocument.createElement("span");
    seriesTitle.className = "docsViewerReport__cellStack docsViewerReport__title";
    seriesTitle.dataset.seriesId = row.seriesId;
    seriesTitle.textContent = row.title;
    rowNode.appendChild(seriesTitle);
    appendDocumentsCell(rowNode, row);
    state.rowsNode.appendChild(rowNode);
  });
  state.statusNode.textContent = projection.rows.length === 1
    ? "1 Series"
    : projection.rows.length + " Series";
}

function loadWorksReport(state) {
  if (state.released) return Promise.resolve();
  state.snapshot = null;
  clearNode(state.rowsNode);
  state.emptyNode.hidden = true;
  state.statusNode.textContent = "Loading Works...";
  return loadWorksInputs(state.context).then((inputs) => {
    if (state.released) return;
    state.snapshot = buildWorksSnapshot(inputs[0].series, inputs[1].docs, state.documentHref);
    renderProjection(state, state.snapshot);
  }).catch((error) => {
    if (state.released) return;
    state.snapshot = null;
    clearNode(state.rowsNode);
    state.statusNode.textContent = error && error.message
      ? error.message
      : "Works report failed to load.";
    state.emptyNode.hidden = false;
    state.emptyNode.textContent = "The current Works report could not complete.";
  });
}

function renderShell(root) {
  root.dataset.reportId = "works";
  root.dataset.reportColumns = "2";
  root.innerHTML = [
    '<p class="docsViewerReport__status"></p>',
    '<div class="docsViewerReport__table"><div class="docsViewerReport__head">',
    '<span class="docsViewerReport__headLabel">Series</span>',
    '<span class="docsViewerReport__headLabel">Docs</span></div>',
    '<ul class="docsViewerReport__rows"></ul></div>',
    '<p class="docsViewerReport__empty" hidden></p>'
  ].join("");
  return {
    emptyNode: root.querySelector(".docsViewerReport__empty"),
    rowsNode: root.querySelector(".docsViewerReport__rows"),
    statusNode: root.querySelector(".docsViewerReport__status")
  };
}

export function mountWorksReport(context) {
  const nodes = renderShell(context.reportRoot);
  const state = Object.assign({
    context,
    released: false,
    snapshot: null,
    documentHref: (docId) => context.viewerUrlForDocument(docId, { collection: "works" })
  }, nodes);
  const unsubscribe = context.collectionProvider?.subscribeDocumentChanges?.((change) => {
    if (!context.reportRoot.isConnected || !state.snapshot) return;
    if (commitWorksDocument(state.snapshot, change, state.documentHref)) renderProjection(state, state.snapshot);
  });
  context.registerRetainedView?.({
    id: "works",
    capture: () => null,
    restore: () => {},
    dispose: () => {
      state.released = true;
      state.snapshot = null;
      unsubscribe?.();
    }
  });
  return loadWorksReport(state);
}
