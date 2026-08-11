function cleanText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizedPathname(value) {
  var pathname = cleanText(value) || "/";
  return pathname.replace(/\/+$/, "/");
}

function configuredPublicScope(targetUrl, currentUrl, scopeConfigsById) {
  if (!(scopeConfigsById instanceof Map) || targetUrl.origin !== currentUrl.origin) {
    return "";
  }
  var currentPathname = normalizedPathname(currentUrl.pathname);
  var targetPathname = normalizedPathname(targetUrl.pathname);
  var matches = [];
  scopeConfigsById.forEach(function (config, configuredScopeId) {
    var scopeId = cleanText(config && config.scopeId || configuredScopeId).toLowerCase();
    var viewerBaseUrl = cleanText(config && config.viewerBaseUrl);
    if (!scopeId || !viewerBaseUrl) return;
    var configuredUrl;
    try {
      configuredUrl = new URL(viewerBaseUrl, currentUrl);
    } catch (_error) {
      return;
    }
    var configuredPathname = normalizedPathname(configuredUrl.pathname);
    if (
      configuredPathname !== currentPathname
      && configuredPathname === targetPathname
    ) {
      matches.push(scopeId);
    }
  });
  return matches.length === 1 ? matches[0] : "";
}

export function resolveManagedDocsViewerDocumentHref(href, options = {}) {
  var rawHref = cleanText(href);
  var viewerUrlForScope = options.viewerUrlForScope;
  if (!rawHref || typeof viewerUrlForScope !== "function") return "";

  var currentUrl;
  var targetUrl;
  try {
    currentUrl = new URL(options.currentHref || window.location.href);
    targetUrl = new URL(rawHref, currentUrl);
  } catch (_error) {
    return "";
  }
  var scopeId = configuredPublicScope(
    targetUrl,
    currentUrl,
    options.scopeConfigsById
  );
  var docId = cleanText(targetUrl.searchParams.get("doc"));
  if (!scopeId || !docId) return "";

  var managedUrl;
  try {
    managedUrl = new URL(
      viewerUrlForScope(scopeId, docId, { manage: true }),
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
