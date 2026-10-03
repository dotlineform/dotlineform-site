import { documentTarget } from "./docs-viewer-document-target.js";

/** Construct a destination in the active reader route; callers live only in history. */
export function buildViewerUrl(options) {
  var settings = options || {};
  var target = documentTarget({ doc_id: settings.docId, collection: settings.collection || "" }, { review: new URL(settings.viewerBaseUrl || "/docs/", "https://docs.invalid").pathname === "/docs-review/" });
  var url = new URL(settings.viewerBaseUrl || "/docs/", settings.origin || window.location.origin);
  url.search = "";
  Object.entries(settings.preservedQueryParams || {}).forEach(function (entry) {
    if (["scope", "stage", "subdoc", "collection", "doc"].includes(entry[0])) {
      throw new Error("Reader route contains retired or conflicting document context.");
    }
    if (entry[1]) url.searchParams.set(entry[0], entry[1]);
  });
  if (target.collection) url.searchParams.set("collection", target.collection);
  url.searchParams.set("doc", target.doc_id);
  if (settings.query) url.searchParams.set("q", settings.query.trim());
  url.hash = settings.hash || "";
  return url.pathname + url.search + url.hash;
}

/** Parse exact same-reader destinations; preserve native cross-route navigation. */
export function routeFromAnchorHref(href, options) {
  var settings = options || {};
  var url = new URL(href, settings.currentHref || window.location.href);
  if (url.origin !== (settings.origin || window.location.origin) || url.pathname !== settings.viewerPathname) return null;
  if (["scope", "stage", "subdoc", "mode"].some(function (key) { return url.searchParams.has(key); })) {
    return { error: "This Docs URL uses retired context; use a current document link." };
  }
  if (!url.searchParams.has("doc")) return null;
  if (settings.viewerPathname === "/docs-review/" && url.searchParams.get("package") !== new URL(settings.currentHref).searchParams.get("package")) return null;
  try {
    if (["doc", "collection"].some(function (key) { return url.searchParams.getAll(key).length > 1; })) {
      throw new Error("Document route contains repeated identity fields.");
    }
    var target = documentTarget({ doc_id: url.searchParams.get("doc"), collection: url.searchParams.get("collection") || "" }, { review: settings.viewerPathname === "/docs-review/" });
    return { target: target, hash: url.hash.slice(1) };
  } catch (error) {
    return { error: error.message };
  }
}
