import { createCollectionPresentation } from "../shared/docs-collection-browsing.js";
import { requestUrl } from "../shared/docs-viewer-asset-url.js";

/** Manage owns mutable inventory, indexed commits and thumbnail reload nonces. */
export function createManagedCollectionBrowsingData(options) {
  const presentation = createCollectionPresentation(options);
  let byId = new Map();
  const pendingThumbnails = new Set();
  let rows = [];
  let ids = [];
  let thumbnailSettings = null;
  let thumbnailCount = 0;

  function prepareRecord(record, revision, href) {
    const row = presentation.prepareRecord(record, href);
    row.revision = revision;
    if (row.authoredThumbnail && revision) {
      row.thumbnailSrc = requestUrl(row.thumbnailSrc, { assetVersion: "", reloadNonce: revision });
    }
    return row;
  }

  function prepareThumbnail(row) {
    pendingThumbnails.delete(row);
    if (!row.thumbnailWorkId) return;
    if (thumbnailSettings) row.thumbnailSrc = presentation.workThumbnail(row, thumbnailSettings);
    else pendingThumbnails.add(row);
  }

  return {
    get rows() { return rows; },
    get docIds() { return ids; },
    get hasThumbnails() { return thumbnailCount > 0; },
    get needsThumbnailSettings() { return pendingThumbnails.size > 0; },
    replace(records) {
      const previous = byId;
      byId = new Map(); pendingThumbnails.clear(); thumbnailCount = 0; ids = [];
      presentation.clearOrders();
      rows = records.map(record => {
        const known = previous.get(record.doc_id);
        const row = prepareRecord(record, known?.revision, known?.href);
        byId.set(row.docId, row); ids.push(row.docId);
        prepareThumbnail(row);
        thumbnailCount += Number(row.hasThumbnail);
        return row;
      });
    },
    apply(change, revision) {
      const old = byId.get(change.target.doc_id);
      if (change.deleted) {
        if (!old) return null;
        const index = rows.indexOf(old);
        rows.splice(index, 1); ids.splice(index, 1);
        byId.delete(old.docId); pendingThumbnails.delete(old);
        thumbnailCount -= Number(old.hasThumbnail);
        presentation.clearOrders();
        return { membershipChanged: true };
      }
      const next = prepareRecord(change.record, revision, old?.href);
      if (!old) {
        byId.set(next.docId, next); rows.push(next); ids.push(next.docId);
        prepareThumbnail(next);
        thumbnailCount += Number(next.hasThumbnail);
        presentation.clearOrders();
        return { membershipChanged: true };
      }
      if (old.title !== next.title) presentation.clearOrders();
      else if (old.updated !== next.updated) presentation.clearOrders("last-updated-desc");
      thumbnailCount += Number(next.hasThumbnail) - Number(old.hasThumbnail);
      Object.assign(old, next);
      prepareThumbnail(old);
      return { membershipChanged: false };
    },
    setThumbnailSettings(settings) {
      thumbnailSettings = settings;
      const changed = pendingThumbnails.size > 0;
      pendingThumbnails.forEach(prepareThumbnail);
      return changed;
    },
    project(query, sortMode) { return presentation.project(rows, query, sortMode); },
    clear() {
      rows = []; ids = []; byId.clear(); pendingThumbnails.clear();
      presentation.clearOrders(); thumbnailSettings = null; thumbnailCount = 0;
    }
  };
}

/** Wire local list effects explicitly; construction performs no reads or subscription. */
export function createDocsViewerManagementCollectionList(options) {
  const data = createManagedCollectionBrowsingData(options.browsingOptions);
  let projection = null;
  let projectedIds = [];
  let thumbnailUpdate = null;

  function inventoryChanged(reason, membershipChanged) {
    options.notify({ type: "refresh", docIds: data.docIds, membershipChanged, reason });
  }

  function renderCommittedChange() {
    if (!options.isReady() || !options.render("document-committed")) return;
    if (!data.needsThumbnailSettings || thumbnailUpdate) return;
    thumbnailUpdate = options.resolveThumbnails().then(changed => {
      if (changed && options.isMounted()) options.render("document-committed");
    }).catch(error => {
      options.fail(error, "thumbnail-policy-failed");
    }).finally(() => { thumbnailUpdate = null; });
  }

  return {
    data,
    get docIds() { return projectedIds; },
    connect() {
      // The reader's retained lifetime owns this subscription's cleanup.
      options.collectionProvider.subscribeDocumentChanges(change => {
        if (!options.isMounted() || change.target.collection !== options.collectionId) return;
        const effect = data.apply(change, String(Date.now()));
        if (!effect) return;
        inventoryChanged("document-committed", effect.membershipChanged);
        renderCommittedChange();
      });
    },
    inventoryChanged,
    prepareProjection(rows) {
      if (projection === rows) return;
      projection = rows;
      projectedIds = rows.map(row => row.docId);
    },
    projected(sort) {
      options.notify({ type: "projection", docIds: projectedIds, sort, reason: "filters-projected" });
    },
    refreshCollection(target) {
      const keys = Object.keys(target || {});
      if (keys.length !== 1 || keys[0] !== "collection" || target.collection !== options.collectionId) {
        throw new Error("Imported package target did not match the mounted collection.");
      }
      return options.loadManifest().then(loaded => {
        if (loaded) options.reveal();
        return { collection: options.collectionId };
      }).catch(error => {
        options.fail(error, "collection-refresh-failed");
        throw error;
      });
    },
    dispose() {
      projection = null; projectedIds = []; thumbnailUpdate = null;
    }
  };
}
