import { normalizeDocsCollectionFilterValue } from "./docs-collection-report-filter.js";
import { catalogueWorkThumbnail } from "./docs-viewer-catalogue-media.js";
import { catalogueThumbnailSettings } from "./docs-viewer-catalogue-media-policy.js";
import { classifyDocsDocumentSubject } from "./docs-document-subject.js";
import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";
export const COLLECTION_PAGE_SIZE = 20;
export const COLLECTION_SEARCH_DELAY_MS = 180;

function compareText(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function publicWorkId(record) {
  if (Object.hasOwn(record, "subject") || Object.hasOwn(record, "work_id")) {
    throw new Error("Catalogue list data contains redundant Work identity. Rebuild its manifest.");
  }
  return record.doc_id;
}

/**
 * Prepare Works/Catalogue search values, dates and Work thumbnails once per manifest.
 * Catalogue adds Work-ID matching. Context uses scalar Subjects only when no
 * authored thumbnail is assigned; public Context rows contain one selected field.
 * @param {Object} options
 * @param {string} options.collectionId Exact works or catalogue collection.
 * @param {{base_url: string, size: number, suffix: string, format: string}} [options.thumbnailSettings]
 * @param {boolean} [options.managementContext=false] Permit Context Folder Subjects and both input assignments.
 * @param {function(Object): number} options.updatedTimestamp Validated document timestamp reader.
 * @param {function(Object): string} [options.workIdForDocument] Working-only authoring adapter.
 */
export function createCollectionBrowsingData(options) {
  if (!["works", "catalogue"].includes(options.collectionId)) {
    throw new Error("Unsupported collection browsing data.");
  }
  const catalogue = options.collectionId === "catalogue";
  const titleCollator = catalogue ? null : new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  const name = catalogue ? "Catalogue" : "Works";
  const settings = options.thumbnailSettings;
  const workIdForDocument = options.workIdForDocument || publicWorkId;
  let entries = new Map();
  return {
    prepare(documents) {
      const next = new Map();
      documents.forEach((doc) => {
        const workId = catalogue ? workIdForDocument(doc.record) : "";
        const subject = catalogue ? null : classifyDocsDocumentSubject(doc.record, {
          folderSupported: options.managementContext === true
        });
        if (!catalogue && options.managementContext !== true && doc.record.has_thumbnail === true && subject.kind !== "none") {
          throw new Error("Public Context rows must contain only the selected thumbnail field.");
        }
        const updated = options.updatedTimestamp(doc);
        if (!(catalogue ? /^[0-9]{5}$/.test(doc.docId) : /^d-\d{8}-\d{6}-[a-f0-9]{6}$/.test(doc.docId))
          || (catalogue && workId !== doc.docId)
          || !doc.title || next.has(doc.docId) || !Number.isFinite(updated)) {
          throw new Error(name + " list data requires distinct document IDs, titles and valid last_updated dates. Rebuild its manifest.");
        }
        const thumbnailWorkId = catalogue ? workId : doc.record.has_thumbnail !== true && subject.kind === "work" ? subject.key : "";
        const thumbnail = thumbnailWorkId ? catalogueWorkThumbnail(thumbnailWorkId, doc.title, settings) : null;
        next.set(doc.docId, {
          workId, updated, thumbnail,
          title: normalizeDocsCollectionFilterValue(doc.title)
        });
      });
      entries = next;
    },
    project(documents, query, sortMode) {
      if (!["title-asc", "last-updated-desc"].includes(sortMode)) {
        throw new Error("Unsupported collection sort mode: " + sortMode);
      }
      const normalized = normalizeDocsCollectionFilterValue(query);
      return documents.filter((doc) => {
        const entry = entries.get(doc.docId);
        return !normalized || entry.title.includes(normalized) || entry.workId.includes(normalized);
      }).sort((left, right) => {
        const a = entries.get(left.docId);
        const b = entries.get(right.docId);
        if (titleCollator) {
          return (sortMode === "last-updated-desc" ? b.updated - a.updated : 0)
            || titleCollator.compare(left.title, right.title)
            || compareText(left.docId, right.docId);
        }
        return (sortMode === "last-updated-desc" ? b.updated - a.updated : 0)
          || compareText(a.title, b.title) || compareText(left.title, right.title)
          || compareText(left.docId, right.docId);
      });
    },
    appendThumbnail(button, doc) {
      const thumbnail = entries.get(doc.docId).thumbnail;
      appendCollectionThumbnail(button, thumbnail ? thumbnail.src : undefined);
    },
    thumbnailForDocument(doc) {
      return entries.get(doc.docId).thumbnail;
    }
  };
}

/**
 * Append a decorative 64px thumbnail or an empty slot without an image request.
 * @param {HTMLElement} control Document navigation control.
 * @param {string} [src] Thumbnail URL; omission reserves the same layout space.
 */
export function appendCollectionThumbnail(control, src) {
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
  image.loading = "lazy";
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
    update(count, page, pending) {
      pageIndex = page;
      pageCount = Math.ceil(count / COLLECTION_PAGE_SIZE);
      root.hidden = pageCount <= 1;
      label.textContent = (page + 1) + "/" + pageCount;
      previous.disabled = pending || page === 0;
      next.disabled = pending || pageCount <= 1;
      const nextLabel = (pageCount > 1 && page + 1 >= pageCount ? "First " : "Next ") + collectionTitle + " page";
      next.setAttribute("aria-label", nextLabel);
      next.title = nextLabel;
    }
  };
}
