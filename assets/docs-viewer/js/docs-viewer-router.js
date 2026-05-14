export function buildViewerUrl(options) {
  var settings = options || {};
  var url = new URL(settings.viewerBaseUrl || "/docs/", settings.origin || window.location.origin);
  if (settings.includeScopeParam && settings.viewerScope) {
    url.searchParams.set("scope", settings.viewerScope);
  }
  if (settings.managementMode) {
    url.searchParams.set("mode", settings.managementModeValue || "manage");
  }
  url.searchParams.set("doc", settings.docId || "");
  if (typeof settings.query === "string" && settings.query.trim()) {
    url.searchParams.set("q", settings.query.trim());
  }
  url.hash = settings.hash || "";
  return url.pathname + url.search + url.hash;
}

export function buildViewerUrlForScope(options) {
  var settings = options || {};
  var targetScope = String(settings.scope || settings.viewerScope || "").trim().toLowerCase();
  var targetConfig = settings.scopeConfigsById ? settings.scopeConfigsById.get(targetScope) : null;
  var useManage = Boolean(settings.manage && settings.allowManagement);
  var baseUrl = useManage
    ? (settings.routeViewerBaseUrl || settings.viewerBaseUrl || "/docs/")
    : ((targetConfig && targetConfig.viewerBaseUrl) || settings.viewerBaseUrl || "/docs/");
  var url = new URL(baseUrl, settings.origin || window.location.origin);
  if (useManage) {
    url.searchParams.set("scope", targetScope);
    url.searchParams.set("mode", settings.managementModeValue || "manage");
  } else if (targetConfig && targetConfig.includeScopeParam && targetScope) {
    url.searchParams.set("scope", targetScope);
  }
  url.searchParams.set("doc", settings.docId || "");
  return url.pathname + url.search;
}

export function routeFromAnchorHref(href, options) {
  var settings = options || {};
  var url = new URL(href, settings.currentHref || window.location.href);
  var origin = settings.origin || window.location.origin;
  if (url.origin !== origin) return null;
  if (url.pathname !== settings.viewerPathname) return null;

  var scope = String(url.searchParams.get("scope") || "").trim();
  var linkMode = String(url.searchParams.get("mode") || "");
  var currentMode = String(settings.currentMode || "");
  var managementModeValue = settings.managementModeValue || "manage";
  if (settings.allowManagement && linkMode && linkMode !== currentMode) return null;
  if (settings.includeScopeParam && scope && scope !== settings.viewerScope) {
    if (!settings.allowScopeQuery || !settings.allowManagement || currentMode !== managementModeValue || linkMode) {
      return null;
    }
    url.searchParams.set("mode", managementModeValue);
    return {
      navigateUrl: url.pathname + url.search + url.hash
    };
  }

  var docId = url.searchParams.get("doc");
  if (!docId) return null;

  return {
    docId: docId,
    hash: url.hash ? url.hash.slice(1) : ""
  };
}

export function writeViewerHistory(history, docId, url, hash, query, mode) {
  if (mode === "none") return;
  var nextState = { docId: docId, hash: hash || "", q: query || "" };
  if (mode === "replace") {
    history.replaceState(nextState, "", url);
    return;
  }
  history.pushState(nextState, "", url);
}
