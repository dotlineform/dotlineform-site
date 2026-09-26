import { normalizeDocsCollectionFilterValue } from "./docs-collection-report-filter.js";
import { catalogueWorkThumbnail } from "./docs-viewer-catalogue-media.js";
import { catalogueThumbnailSettings } from "./docs-viewer-catalogue-media-policy.js";
import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";

export const COLLECTION_PAGE_SIZE = 20;
export const COLLECTION_SEARCH_DELAY_MS = 180;

function compareText(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function publicWorkId(record) {
  if (Object.hasOwn(record, "subject")) {
    throw new Error("Catalogue list data contains the retired subject field. Rebuild its manifest.");
  }
  return record.work_id;
}

/**
 * Prepare Works/Catalogue search values and dates once per manifest. Catalogue
 * alone adds Work-ID matching and thumbnails; public rows never read authoring data.
 * @param {Object} options
 * @param {string} options.collectionId Exact works or catalogue collection.
 * @param {{base_url: string, size: number, suffix: string, format: string}} [options.thumbnailSettings]
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
        const updated = options.updatedTimestamp(doc);
        if (!/^d-\d{8}-\d{6}-[a-f0-9]{6}$/.test(doc.docId)
          || !doc.title || next.has(doc.docId) || !Number.isFinite(updated)) {
          throw new Error(name + " list data requires distinct document IDs, titles and valid last_updated dates. Rebuild its manifest.");
        }
        const thumbnail = catalogue ? catalogueWorkThumbnail(workId, doc.title, settings) : null;
        next.set(doc.docId, {
          workId, updated, thumbnail,
          title: normalizeDocsCollectionFilterValue(doc.title)
        });
      });
      entries = next;
    },
    project(documents, query, sortMode, compareCustom) {
      const normalized = normalizeDocsCollectionFilterValue(query);
      return documents.filter((doc) => {
        const entry = entries.get(doc.docId);
        return !normalized || entry.title.includes(normalized) || entry.workId.includes(normalized);
      }).sort((left, right) => {
        if (!["title-asc", "last-updated-desc"].includes(sortMode) && (catalogue || sortMode !== "title-desc")) {
          if (typeof compareCustom !== "function") throw new Error("Unsupported collection sort mode: " + sortMode);
          const comparison = compareCustom(left, right);
          if (!Number.isFinite(comparison)) throw new Error("Collection comparator must return a finite number.");
          return comparison;
        }
        const a = entries.get(left.docId);
        const b = entries.get(right.docId);
        if (titleCollator) {
          return (sortMode === "last-updated-desc" ? b.updated - a.updated : 0)
            || titleCollator.compare(left.title, right.title) * (sortMode === "title-desc" ? -1 : 1)
            || compareText(left.docId, right.docId);
        }
        return (sortMode === "last-updated-desc" ? b.updated - a.updated : 0)
          || compareText(a.title, b.title) || compareText(left.title, right.title)
          || compareText(left.docId, right.docId);
      });
    },
    appendThumbnail(button, doc) {
      const thumbnail = entries.get(doc.docId).thumbnail;
      const image = button.ownerDocument.createElement("img");
      image.className = "docsViewerReport__catalogueThumbnail";
      image.alt = "";
      image.width = 64;
      image.height = 64;
      image.loading = "lazy";
      image.decoding = "async";
      image.addEventListener("error", () => { image.style.visibility = "hidden"; }, { once: true });
      image.src = thumbnail.src;
      button.appendChild(image);
    }
  };
}

/**
 * Read one stage's existing media policy. Public transport remains static-file-only.
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
 * Compact page controls; the collection owner supplies cached results and navigation.
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
  const label = documentRef.createElement("span");
  label.className = "docsViewerReport__collectionPageLabel";
  function arrow(name, direction, offset) {
    const button = documentRef.createElement("button");
    button.className = "docsViewer__toolbarIconButton";
    button.type = "button";
    button.setAttribute("aria-label", name);
    button.title = name;
    button.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--chevron-" + direction));
    button.addEventListener("click", () => onPage(pageIndex + offset));
    return button;
  }
  const previous = arrow("Previous " + collectionTitle + " page", "left", -1);
  const next = arrow("Next " + collectionTitle + " page", "right", 1);
  root.append(previous, label, next);
  return {
    root,
    update(count, page, pending) {
      pageIndex = page;
      const pages = Math.ceil(count / COLLECTION_PAGE_SIZE);
      root.hidden = count === 0;
      label.textContent = (page + 1) + "/" + pages;
      previous.disabled = pending || page === 0;
      next.disabled = pending || page + 1 >= pages;
    }
  };
}
