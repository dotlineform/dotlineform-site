import { buildViewerUrl } from "./docs-viewer-router.js";

function identity(value) {
  if (!value
    || Object.keys(value).sort().join(",") !== "collection,doc_id"
    || typeof value.collection !== "string" || !/^(?:[a-z][a-z0-9-]*)?$/.test(value.collection)
    || typeof value.doc_id !== "string"
    || !(value.collection === "catalogue" ? /^[0-9]{5}$/ : /^d-\d{8}-\d{6}-[a-f0-9]{6}$/).test(value.doc_id)) {
    throw new Error("Links requires an exact document identity.");
  }
  return {  collection: value.collection, doc_id: value.doc_id };
}

function sameTarget(left, right) {
  return left.collection === right.collection && left.doc_id === right.doc_id;
}

/** Validate the flat identity and title shared by all document summaries. */
export function docsViewerLinksDocumentSummary(value) {
  if (!value || Object.keys(value).sort().join(",") !== "collection,doc_id,title") {
    throw new Error("Links requires a flat document summary.");
  }
  var target = identity({ collection: value.collection, doc_id: value.doc_id });
  if (typeof value.title !== "string" || !value.title.trim()) throw new Error("Links document title is missing.");
  return { ...target, title: value.title };
}

/** Resolve a link from the reader's configured route and exact collection host. */
export function docsViewerLinksDocumentHref(value, config) {
  var target = identity({ collection: value && value.collection, doc_id: value && value.doc_id });
  if (!config || typeof config.viewerBaseUrl !== "string"
    || !config.viewerBaseUrl.startsWith("/") || config.viewerBaseUrl.startsWith("//")
    || /[\\\s]/.test(config.viewerBaseUrl)) {
    throw new Error("Links requires the configured viewer route.");
  }
  var base = new URL(config.viewerBaseUrl, "https://docs.invalid");
  if (base.searchParams.has("scope") || base.searchParams.has("stage")) {
    throw new Error("Links viewer route contains retired context.");
  }
  var docId = target.doc_id;
  if (target.collection) {
    var owners = (config.collections || []).filter(function (owner) { return owner.collection === target.collection; });
    if (owners.length !== 1 || !/^d-\d{8}-\d{6}-[a-f0-9]{6}$/.test(owners[0].reportHostDocId)) {
      throw new Error("Links requires an exact configured collection report host.");
    }
    docId = owners[0].reportHostDocId;
  }
  return buildViewerUrl({
    viewerBaseUrl: config.viewerBaseUrl, origin: "https://docs.invalid", docId: docId,
    reportParams: target.collection ? { subdoc: target.doc_id } : {}
  });
}

function category(document) {
  if (document.collection === "concepts") return "Concepts";
  if (document.collection === "works" || document.collection === "catalogue") return "Works";
  if (!document.collection) return "References";
  return "";
}

/** Validate one complete version-4 response and project shallow, title-sorted sections.
 * Combine both directions by exact identity; keep the supplied directional data unchanged.
 */
export function docsViewerLinksPresentation(payload, target) {
  var expected = identity(target);
  if (!payload || payload.schema_version !== 4 || !Array.isArray(payload.outgoing) || !Array.isArray(payload.incoming)) {
    throw new Error("Unsupported Links data. Expected schema version 4.");
  }
  var self = docsViewerLinksDocumentSummary(payload.self);
  if (!sameTarget(self, expected)) throw new Error("Links data does not match the displayed document.");
  var sections = new Map(["Concepts", "Works", "References"].map(function (label) { return [label, []]; }));
  var documents = new Map();
  ["outgoing", "incoming"].forEach(function (direction) {
    var seen = new Set();
    payload[direction].forEach(function (entry) {
      var document = docsViewerLinksDocumentSummary(entry);
      var key = JSON.stringify([document.collection, document.doc_id]);
      if (seen.has(key)) {
        throw new Error("Links contains an invalid counterpart entry.");
      }
      seen.add(key);
      if (!documents.has(key)) documents.set(key, document);
    });
  });
  documents.forEach(function (document) {
    var label = category(document);
    if (label) sections.get(label).push({ document: document });
  });
  return {
    title: self.title,
    sections: Array.from(sections, function ([label, entries]) {
      entries.sort(function (a, b) {
        return a.document.title.localeCompare(b.document.title, "en", { sensitivity: "base" })
          || JSON.stringify([a.document.collection, a.document.doc_id]).localeCompare(JSON.stringify([b.document.collection, b.document.doc_id]));
      });
      return { label: label, entries: entries };
    }).filter(function (section) { return section.entries.length; })
  };
}
