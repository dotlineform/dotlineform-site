import { normalizeDocsCollectionFilterValue } from "./docs-collection-report-filter.js";
import { catalogueWorkThumbnail } from "./docs-viewer-catalogue-media.js";
import { catalogueThumbnailSettings } from "./docs-viewer-catalogue-media-policy.js";
import { requestUrl } from "./docs-viewer-asset-url.js";
import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";
export const COLLECTION_PAGE_SIZE = 20;
export const COLLECTION_SEARCH_DELAY_MS = 180;

function compareText(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

/**
 * Shared presentation over completed records: exact URLs, thumbnail choices,
 * search keys and cached ordering. Inventory and edit ownership stay with callers.
 * Catalogue adds Work-ID matching; Context retains numeric-aware title collation.
 * @param {Object} options
 * @param {string} options.collectionId Exact configured collection.
 * @param {string} [options.mediaRoot] Configured authored-thumbnail media root.
 * @param {function(string): string} options.documentHref Exact reader route owner.
 */
export function createCollectionPresentation(options) {
  const catalogue = options.collectionId === "catalogue";
  const works = options.collectionId === "works";
  const titleCollator = works ? new Intl.Collator(undefined, { numeric: true, sensitivity: "base" }) : null;
  const mediaRoot = options.mediaRoot?.replace(/\/+$/, "");
  const orders = new Map();
  let projection = null;

  function prepareRecord(record, href) {
    const searchTitle = normalizeDocsCollectionFilterValue(record.title);
    const authoredThumbnail = !catalogue && record.has_thumbnail === true;
    const workId = catalogue ? record.doc_id : "";
    const thumbnailWorkId = catalogue ? workId
      : works && !authoredThumbnail && /^[0-9]{5}$/.test(record.subject) ? record.subject : "";
    const row = {
      docId: record.doc_id, title: record.title, record,
      href: href === undefined ? options.documentHref(record.doc_id) : href,
      searchTitle, workId, updated: record.last_updated || "",
      sortTitle: catalogue ? searchTitle : record.title.trim().normalize("NFKC").toLowerCase(),
      rawTitle: catalogue ? record.title : record.title.trim(),
      authoredThumbnail, thumbnailWorkId,
      hasThumbnail: authoredThumbnail || Boolean(thumbnailWorkId), thumbnailSrc: ""
    };
    if (row.authoredThumbnail) {
      if (!mediaRoot) throw new Error("Document thumbnail media is not configured.");
      row.thumbnailSrc = requestUrl(mediaRoot + "/collections/" + encodeURIComponent(options.collectionId)
        + "/thumbs/" + encodeURIComponent(row.docId + "-thumb.webp"));
    }
    return row;
  }

  function compareTitle(left, right) {
    return (titleCollator ? titleCollator.compare(left.rawTitle, right.rawTitle)
      : compareText(left.sortTitle, right.sortTitle) || compareText(left.rawTitle, right.rawTitle))
      || compareText(left.docId, right.docId);
  }

  return {
    prepareRecord,
    workThumbnail(row, settings) {
      return catalogueWorkThumbnail(row.thumbnailWorkId, row.title, settings).src;
    },
    clearOrders(sortMode) {
      if (!sortMode || projection?.ordered === orders.get(sortMode)) projection = null;
      if (sortMode) orders.delete(sortMode);
      else orders.clear();
    },
    project(rows, query, sortMode) {
      let ordered = orders.get(sortMode);
      if (!ordered) {
        ordered = rows.slice().sort((left, right) =>
          (sortMode === "last-updated-desc" ? compareText(right.updated, left.updated) : 0) || compareTitle(left, right));
        orders.set(sortMode, ordered);
      }
      const normalized = normalizeDocsCollectionFilterValue(query);
      if (projection?.ordered === ordered && projection.query === normalized) return projection.rows;
      const matches = normalized ? ordered.filter(row => row.searchTitle.includes(normalized) || row.workId.includes(normalized)) : ordered;
      projection = { ordered, query: normalized, rows: matches };
      return matches;
    }
  };
}

/** Read-only inventory for public browsing; no edit index, selection IDs or revisions. */
export function createCollectionBrowsingData(options) {
  const presentation = createCollectionPresentation(options);
  let rows = [];
  let pendingThumbnails = [];
  let hasThumbnails = false;
  return {
    get rows() { return rows; },
    get hasThumbnails() { return hasThumbnails; },
    get needsThumbnailSettings() { return pendingThumbnails.length > 0; },
    replace(records) {
      presentation.clearOrders();
      pendingThumbnails = []; hasThumbnails = false;
      rows = records.map(record => {
        const row = presentation.prepareRecord(record);
        if (row.thumbnailWorkId) pendingThumbnails.push(row);
        hasThumbnails ||= row.hasThumbnail;
        return row;
      });
    },
    setThumbnailSettings(settings) {
      const changed = pendingThumbnails.length > 0;
      pendingThumbnails.forEach(row => { row.thumbnailSrc = presentation.workThumbnail(row, settings); });
      pendingThumbnails = [];
      return changed;
    },
    project(query, sortMode) { return presentation.project(rows, query, sortMode); },
    clear() {
      rows = []; pendingThumbnails = []; hasThumbnails = false;
      presentation.clearOrders();
    }
  };
}

/**
 * Append a decorative 64px thumbnail or an empty slot without an image request.
 * @param {HTMLElement} control Document navigation control.
 * @param {string} [src] Thumbnail URL; omission reserves the same layout space.
 * @param {"eager"|"lazy"} [loading="lazy"] Eager for the bounded current page.
 */
export function appendCollectionThumbnail(control, src, loading = "lazy") {
  control.classList.add("docsViewerReport__collectionButton--thumbnail");
  if (!src) {
    const slot = control.ownerDocument.createElement("span");
    slot.className = "docsViewerReport__documentThumbnail";
    slot.setAttribute("aria-hidden", "true");
    control.appendChild(slot);
    return;
  }
  const image = control.ownerDocument.createElement("img");
  image.className = "docsViewerReport__documentThumbnail";
  image.alt = "";
  image.width = 64;
  image.height = 64;
  image.loading = loading;
  image.decoding = "async";
  image.addEventListener("error", () => { image.style.visibility = "hidden"; }, { once: true });
  image.src = src;
  control.appendChild(image);
}

/**
 * Read the configured media policy. Public transport remains static-file-only.
 * @param {Object} context Report context with collectionProvider and routeContext.
 */
export async function loadCatalogueCollectionThumbnailSettings(context) {
  const provider = context.collectionProvider;
  if (!provider || typeof provider.readCatalogueMediaConfig !== "function") {
    throw new Error("Catalogue thumbnail policy reader is unavailable.");
  }
  const policy = await provider.readCatalogueMediaConfig();
  return catalogueThumbnailSettings(policy, context.routeContext?.routeConfig?.catalogueWorkThumbnailsBaseUrl);
}

/**
 * Compact controls over cached results. Next wraps to the first of multiple pages;
 * Previous stops at the first page. The collection owner supplies navigation.
 * Updates supply the current pagination mode; only enabled multi-page results show controls.
 * @param {Document} documentRef
 * @param {string} collectionTitle Accessible name of the collection.
 * @param {function(number): void} onPage Receives a zero-based page index.
 */
export function createCollectionPager(documentRef, collectionTitle, onPage) {
  const root = documentRef.createElement("nav");
  root.className = "docsViewerReport__collectionPagination";
  root.setAttribute("aria-label", collectionTitle + " pages");
  root.hidden = true;
  let pageIndex = 0;
  let pageCount = 0;
  const label = documentRef.createElement("span");
  label.className = "docsViewerReport__collectionPageLabel";
  function arrow(name, direction, offset) {
    const button = documentRef.createElement("button");
    button.className = "docsViewer__toolbarIconButton";
    button.type = "button";
    button.setAttribute("aria-label", name);
    button.title = name;
    button.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--chevron-" + direction));
    button.addEventListener("click", () => {
      const target = pageIndex + offset;
      onPage(offset > 0 && target >= pageCount ? 0 : target);
    });
    return button;
  }
  const previous = arrow("Previous " + collectionTitle + " page", "left", -1);
  const next = arrow("Next " + collectionTitle + " page", "right", 1);
  root.append(previous, label, next);
  return {
    root,
    update(count, page, pending, enabled) {
      pageIndex = page;
      pageCount = Math.ceil(count / COLLECTION_PAGE_SIZE);
      root.hidden = !enabled || pageCount <= 1;
      label.textContent = (page + 1) + "/" + pageCount;
      previous.disabled = pending || page === 0;
      next.disabled = pending || pageCount <= 1;
      const nextLabel = (pageCount > 1 && page + 1 >= pageCount ? "First " : "Next ") + collectionTitle + " page";
      next.setAttribute("aria-label", nextLabel);
      next.title = nextLabel;
    }
  };
}
