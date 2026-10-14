import { applySelectedDocumentChange, prepareSelectedDocuments } from "../shared/docs-selected-documents.js";
import { appendCollectionThumbnail, loadCatalogueCollectionThumbnailSettings } from "../shared/docs-collection-browsing.js";
import { catalogueWorkThumbnail } from "../shared/docs-viewer-catalogue-media.js";
import { requestUrl } from "../shared/docs-viewer-asset-url.js";

/** Mount a saved selection list; disposal ends its local/public retained lifetime. */
export async function mountSelectedDocumentsReport(context) {
  const root = context.reportRoot;
  const documentRef = root.ownerDocument;
  const mediaRoot = context.mediaRoot?.replace(/\/+$/, "");
  let data = null;
  let released = false;
  let initialLoading = true;
  let thumbnailSettings = null;
  let thumbnailSettingsRead = null;
  let thumbnailUpdate = null;
  const pendingThumbnails = new Set();
  root.dataset.reportId = "selected_documents";
  root.dataset.reportColumns = "1";

  function prepareThumbnail(row, revision) {
    pendingThumbnails.delete(row);
    if (row.has_thumbnail === true) {
      if (!mediaRoot) throw new Error("Selected Documents thumbnail media is not configured.");
      const owner = row.collection ? "collections/" + encodeURIComponent(row.collection) : "workspace";
      row.thumbnailSrc = requestUrl(mediaRoot + "/" + owner + "/thumbs/" + encodeURIComponent(row.doc_id + "-thumb.webp"), { reloadNonce: revision });
    } else if (row.thumbnailWorkId && thumbnailSettings) {
      row.thumbnailSrc = catalogueWorkThumbnail(row.thumbnailWorkId, row.title, thumbnailSettings).src;
    } else {
      row.thumbnailSrc = "";
      if (row.thumbnailWorkId) pendingThumbnails.add(row);
    }
  }

  async function resolvePendingThumbnails() {
    if (!pendingThumbnails.size) return;
    if (!thumbnailSettingsRead) thumbnailSettingsRead = loadCatalogueCollectionThumbnailSettings(context);
    const settings = await thumbnailSettingsRead;
    if (released) return;
    thumbnailSettings = settings;
    pendingThumbnails.forEach((row) => prepareThumbnail(row));
  }

  function render() {
    if (released) return;
    const reserveThumbnailSpace = data.rows.some((row) => row.thumbnailSrc);
    const list = documentRef.createElement("ul");
    list.className = "docsViewerReport__rows";
    data.rows.forEach(function (row) {
      const item = documentRef.createElement("li");
      item.className = "docsViewerReport__row";
      const link = documentRef.createElement("a");
      link.className = "docsViewerReport__cellLink docsViewerReport__collectionButton";
      link.href = row.href;
      if (reserveThumbnailSpace) appendCollectionThumbnail(link, row.thumbnailSrc || undefined);
      const title = documentRef.createElement("span");
      title.className = "docsViewerReport__title";
      title.textContent = row.title;
      link.appendChild(title);
      item.appendChild(link);
      list.appendChild(item);
    });
    if (data.rows.length) root.replaceChildren(list);
    else {
      const note = documentRef.createElement("p");
      note.className = "docsViewerReport__status";
      note.textContent = "No selected documents.";
      root.replaceChildren(note);
    }
  }

  function renderError(error) {
    if (released) return;
    const note = documentRef.createElement("p");
    note.className = "docsViewerReport__status";
    note.textContent = error.message;
    root.replaceChildren(note);
  }

  function updateView() {
    if (initialLoading || thumbnailUpdate) return;
    if (!pendingThumbnails.size) { render(); return; }
    thumbnailUpdate = resolvePendingThumbnails().then(render).catch(renderError).finally(() => {
      if (!released) thumbnailUpdate = null;
    });
  }

  context.registerRetainedView?.({
    id: "selected_documents",
    capture: () => null,
    restore: () => {},
    dispose: () => {
      released = true;
      data = null;
      pendingThumbnails.clear();
      thumbnailSettings = null;
      thumbnailSettingsRead = null;
      thumbnailUpdate = null;
    }
  });
  if (context.collectionProvider && context.collectionProvider.subscribeDocumentChanges) context.collectionProvider.subscribeDocumentChanges(function (change) {
    if (released || !data) return;
    const effect = applySelectedDocumentChange(data, change);
    if (!effect) return;
    if (effect.deleted) pendingThumbnails.delete(effect.row);
    else if (effect.thumbnailChanged) prepareThumbnail(effect.row, String(Date.now()));
    updateView();
  });

  try {
    if (released) return false;
    if (!context.selectedUrl) throw new Error("Selected Documents data is not configured.");
    const response = await fetch(context.selectedUrl, { headers: { Accept: "application/json" }, cache: "no-cache" });
    if (released) return false;
    if (!response.ok) throw new Error("Failed to load Selected Documents.");
    const payload = await response.json();
    if (released) return false;
    data = prepareSelectedDocuments(payload.docs, context.viewerUrlForDocument);
    data.rows.forEach((row) => prepareThumbnail(row));
    await resolvePendingThumbnails();
    if (released) return false;
    initialLoading = false;
    render();
    return true;
  } catch (error) {
    if (released) return false;
    data = null;
    pendingThumbnails.clear();
    throw error;
  }
}
