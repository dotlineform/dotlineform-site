import { selectedDocumentRows, selectedDocumentThumbnailMetadata } from "../shared/docs-selected-documents.js";
import { appendCollectionThumbnail, loadCatalogueCollectionThumbnailSettings } from "../shared/docs-collection-browsing.js";
import { catalogueWorkThumbnail } from "../shared/docs-viewer-catalogue-media.js";
import { requestUrl } from "../shared/docs-viewer-asset-url.js";

function documentThumbnailUrl(context, row, settings, revision) {
  if (row.has_thumbnail === true) {
    const mediaRoot = String(context.mediaRoot || "").replace(/\/+$/, "");
    if (!mediaRoot) throw new Error("Selected Documents thumbnail media is not configured.");
    const owner = row.collection ? "collections/" + encodeURIComponent(row.collection) : "workspace";
    return requestUrl(mediaRoot + "/" + owner + "/thumbs/" + encodeURIComponent(row.doc_id + "-thumb.webp"), { reloadNonce: revision });
  }
  const workId = row.collection === "catalogue" ? row.doc_id : row.subject;
  return workId ? catalogueWorkThumbnail(workId, row.title, settings).src : "";
}

/** Mount the selected list with collection thumbnail presentation and exact links. */
export async function mountSelectedDocumentsReport(context) {
  const root = context.reportRoot;
  const documentRef = root.ownerDocument;
  if (!context.selectedUrl) throw new Error("Selected Documents data is not configured.");
  const response = await fetch(context.selectedUrl, { headers: { Accept: "application/json" }, cache: "no-cache" });
  if (!response.ok) throw new Error("Failed to load Selected Documents.");
  let rows = selectedDocumentRows(await response.json());
  const thumbnailSettings = rows.some((row) => ["works", "catalogue"].includes(row.collection))
    ? await loadCatalogueCollectionThumbnailSettings(context) : null;
  const thumbnailRevisions = new Map();
  if (!root.isConnected) return false;
  root.dataset.reportId = "selected_documents";
  root.dataset.reportColumns = "1";
  function render() {
    const thumbnails = rows.map((row) => documentThumbnailUrl(context, row, thumbnailSettings, thumbnailRevisions.get((row.collection || "") + "/" + row.doc_id)));
    const reserveThumbnailSpace = thumbnails.some(Boolean);
    const list = documentRef.createElement("ul");
    list.className = "docsViewerReport__rows";
    rows.forEach(function (row, index) {
      const item = documentRef.createElement("li");
      item.className = "docsViewerReport__row";
      const link = documentRef.createElement("a");
      link.className = "docsViewerReport__cellLink docsViewerReport__collectionButton";
      const url = new URL(context.viewerUrlForDocument(row.doc_id, { collection: row.collection || "" }), documentRef.baseURI);
      link.href = url.href;
      if (reserveThumbnailSpace) appendCollectionThumbnail(link, thumbnails[index] || undefined);
      const title = documentRef.createElement("span");
      title.className = "docsViewerReport__title";
      title.textContent = row.title;
      link.appendChild(title);
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
    const collection = change.target.collection || "";
    const key = collection + "/" + change.target.doc_id;
    if (!rows.some((row) => row.doc_id === change.target.doc_id && (row.collection || "") === collection)) return;
    if (change.deleted) thumbnailRevisions.delete(key);
    else thumbnailRevisions.set(key, String(Date.now()));
    rows = rows.filter(function (row) { return !change.deleted || row.doc_id !== change.target.doc_id || (row.collection || "") !== collection; }).map(function (row) {
      if (row.doc_id !== change.target.doc_id || (row.collection || "") !== collection) return row;
      const updated = Object.assign({}, row, { title: change.record.title, last_updated: change.record.last_updated });
      delete updated.has_thumbnail;
      delete updated.subject;
      return Object.assign(updated, selectedDocumentThumbnailMetadata(change.record, collection));
    });
    rows = selectedDocumentRows({ schema: "docs_selected_v1", docs: rows });
    render();
  });
  return true;
}
