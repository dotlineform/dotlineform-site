import { selectedDocumentRows } from "../shared/docs-selected-documents.js";

export async function mountSelectedDocumentsReport(context) {
  const root = context.reportRoot;
  const documentRef = root.ownerDocument;
  if (!context.selectedUrl) throw new Error("Selected Documents data is not configured.");
  const response = await fetch(context.selectedUrl, { headers: { Accept: "application/json" }, cache: "no-store" });
  if (!response.ok) throw new Error("Failed to load Selected Documents.");
  const rows = selectedDocumentRows(await response.json());
  if (!root.isConnected) return false;
  const list = documentRef.createElement("ul");
  list.className = "docsViewerReport__rows";
  rows.forEach(function (row) {
    const item = documentRef.createElement("li");
    item.className = "docsViewerReport__row";
    const link = documentRef.createElement("a");
    link.className = "docsViewerReport__cellLink docsViewerReport__title";
    const url = new URL(context.viewerUrlForDocument(row.collection ? row.report_doc_id : row.doc_id), documentRef.baseURI);
    if (row.collection) url.searchParams.set("subdoc", row.doc_id);
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
  return true;
}
