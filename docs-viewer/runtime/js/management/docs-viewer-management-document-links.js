function cleanText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizedPathname(value) {
  var pathname = cleanText(value) || "/";
  return pathname.replace(/\/+$/, "/");
}

export function resolveManagedDocsViewerDocumentHref(href, options = {}) {
  var rawHref = cleanText(href);
  var viewerUrlForDocument = options.viewerUrlForDocument;
  if (!rawHref || typeof viewerUrlForDocument !== "function") return "";

  var currentUrl;
  var targetUrl;
  try {
    currentUrl = new URL(options.currentHref || window.location.href);
    targetUrl = new URL(rawHref, currentUrl);
  } catch (_error) {
    return "";
  }
  var publicUrl;
  try { publicUrl = new URL(options.publicViewerBaseUrl, currentUrl); } catch (_error) { return ""; }
  var docId = cleanText(targetUrl.searchParams.get("doc"));
  if (!options.publicViewerBaseUrl || !docId || targetUrl.origin !== currentUrl.origin
      || normalizedPathname(targetUrl.pathname) !== normalizedPathname(publicUrl.pathname)
      || targetUrl.searchParams.has("scope") || targetUrl.searchParams.has("stage")) return "";

  var managedUrl;
  try {
    managedUrl = new URL(
      viewerUrlForDocument(docId, { manage: true }),
      currentUrl
    );
  } catch (_error) {
    return "";
  }
  var subdoc = cleanText(targetUrl.searchParams.get("subdoc"));
  if (subdoc) managedUrl.searchParams.set("subdoc", subdoc);
  managedUrl.hash = targetUrl.hash;
  return managedUrl.pathname + managedUrl.search + managedUrl.hash;
}

export function mountManagedDocsViewerDocumentLinks(root, options = {}) {
  if (!root || typeof root.querySelectorAll !== "function") return 0;
  var mounted = 0;
  root.querySelectorAll("a[href]").forEach(function (link) {
    var managedHref = resolveManagedDocsViewerDocumentHref(
      link.getAttribute("href"),
      options
    );
    if (!managedHref) return;
    link.setAttribute("href", managedHref);
    mounted += 1;
  });
  return mounted;
}
