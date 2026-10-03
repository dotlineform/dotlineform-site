import { selectedDocumentRows } from "../shared/docs-selected-documents.js";

export async function mountSelectedDocumentsReport(context) {
  const root = context.reportRoot;
  const documentRef = root.ownerDocument;
  if (!context.selectedUrl) throw new Error("Selected Documents data is not configured.");
  const response = await fetch(context.selectedUrl, { headers: { Accept: "application/json" }, cache: "no-cache" });
  if (!response.ok) throw new Error("Failed to load Selected Documents.");
  let rows = selectedDocumentRows(await response.json());
  if (!root.isConnected) return false;
  function render() {
  const list = documentRef.createElement("ul");
  list.className = "docsViewerReport__rows";
  rows.forEach(function (row) {
    const item = documentRef.createElement("li");
    item.className = "docsViewerReport__row";
    const link = documentRef.createElement("a");
    link.className = "docsViewerReport__cellLink docsViewerReport__title";
    const url = new URL(context.viewerUrlForDocument(row.doc_id, { collection: row.collection || "" }), documentRef.baseURI);
    link.href = url.href;
    link.textContent = row.title;
    item.appendChild(link);
    list.appendChild(item);
  });
  if (rows.length) root.replaceChildren(list);
  else {
    const note = documentRef.createElement("p");
    note.className = "docsViewerReport__status";
    note.textContent = "No selected documents.";
    root.replaceChildren(note);
  }
  }
  render();
  if (context.collectionProvider && context.collectionProvider.subscribeDocumentChanges) context.collectionProvider.subscribeDocumentChanges(function (change) {
    if (!root.isConnected) return;
    rows = rows.filter(function (row) { return !change.deleted || row.doc_id !== change.target.doc_id || (row.collection || "") !== (change.target.collection || ""); }).map(function (row) {
      return row.doc_id === change.target.doc_id && (row.collection || "") === (change.target.collection || "") ? Object.assign({}, row, change.record) : row;
    });
    render();
  });
  return true;
}
