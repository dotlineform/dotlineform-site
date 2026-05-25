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

export function setViewerHistory(options) {
  var settings = options || {};
  var nextUrl = buildViewerUrl(settings);
  writeViewerHistory(
    settings.history || window.history,
    settings.docId,
    nextUrl,
    settings.hash,
    settings.query,
    settings.mode
  );
  return nextUrl;
}

export function resolveViewerRouteDocId(options) {
  var settings = options || {};
  var requestedDocId = settings.requestedDocId || "";
  var resolvedDocId = requestedDocId;
  var docsById = settings.docsById;
  var defaultRouteDocId = settings.defaultRouteDocId || "";
  var resolveLoadableDocId = settings.resolveLoadableDocId;
  var defaultDocId = settings.defaultDocId;

  if (!docsById || typeof docsById.has !== "function") {
    return {
      requestedDocId: requestedDocId,
      docId: "",
      corrected: Boolean(requestedDocId)
    };
  }

  if (requestedDocId && !docsById.has(requestedDocId)) {
    return {
      requestedDocId: requestedDocId,
      docId: requestedDocId,
      corrected: false,
      missing: true
    };
  }

  if (!docsById.has(resolvedDocId) && defaultRouteDocId && docsById.has(defaultRouteDocId)) {
    resolvedDocId = defaultRouteDocId;
  }
  if (docsById.has(resolvedDocId) && typeof resolveLoadableDocId === "function") {
    resolvedDocId = resolveLoadableDocId(resolvedDocId) || "";
  }
  if (!resolvedDocId && defaultRouteDocId && docsById.has(defaultRouteDocId) && typeof resolveLoadableDocId === "function") {
    resolvedDocId = resolveLoadableDocId(defaultRouteDocId);
  }
  if (!resolvedDocId && typeof defaultDocId === "function") {
    resolvedDocId = defaultDocId();
  }
  return {
    requestedDocId: requestedDocId,
    docId: resolvedDocId,
    corrected: resolvedDocId !== requestedDocId
  };
}

export function applyViewerRoute(options) {
  var settings = options || {};
  var state = settings.state;
  var routeHash = settings.hash || (typeof settings.currentHash === "function" ? settings.currentHash() : "");
  var historyMode = settings.historyMode || "push";

  if (typeof settings.setRecentModeActive === "function") {
    settings.setRecentModeActive(false);
  }
  if (state && typeof settings.managementModeActive === "function") {
    state.managementMode = settings.managementModeActive();
  }
  if (typeof settings.syncHiddenVisibilityForRequestedDoc === "function") {
    settings.syncHiddenVisibilityForRequestedDoc();
  }
  if (typeof settings.applyDocVisibility === "function") {
    settings.applyDocVisibility();
  }

  var route = resolveViewerRouteDocId({
    requestedDocId: typeof settings.currentDocId === "function" ? settings.currentDocId() : "",
    docsById: state ? state.docsById : null,
    defaultRouteDocId: settings.defaultRouteDocId,
    resolveLoadableDocId: settings.resolveLoadableDocId,
    defaultDocId: settings.defaultDocId
  });
  var docId = route.docId;
  if (!docId) {
    if (typeof settings.setStatus === "function") {
      settings.setStatus("No docs available.", true);
    }
    return {
      docId: "",
      route: route,
      searchRouteActive: false
    };
  }

  var query = typeof settings.currentQuery === "function" ? settings.currentQuery() : "";
  var searchRouteActive = typeof settings.hasActiveQuery === "function"
    ? settings.hasActiveQuery(query)
    : Boolean(String(query || "").trim());

  if (state) {
    state.searchQuery = query;
    state.searchRouteActive = searchRouteActive;
    state.selectedDocId = docId;
  }
  if (settings.searchInput) {
    settings.searchInput.value = query;
  }

  if (typeof settings.expandTrail === "function") {
    settings.expandTrail(docId);
  }
  if (typeof settings.renderSidebar === "function") {
    settings.renderSidebar();
  }
  if (typeof settings.renderBookmarkUi === "function") {
    settings.renderBookmarkUi();
  }
  if (typeof settings.renderManagementUi === "function") {
    settings.renderManagementUi();
  }

  var shouldReplaceHistory = route.corrected;
  if (!shouldReplaceHistory && typeof settings.hasCanonicalScopeInUrl === "function") {
    shouldReplaceHistory = !settings.hasCanonicalScopeInUrl();
  }
  if (!shouldReplaceHistory && typeof settings.hasDisallowedModeInUrl === "function") {
    shouldReplaceHistory = settings.hasDisallowedModeInUrl();
  }
  if (!shouldReplaceHistory && typeof settings.hasDisallowedScopeInUrl === "function") {
    shouldReplaceHistory = settings.hasDisallowedScopeInUrl();
  }
  if (shouldReplaceHistory && typeof settings.setHistory === "function") {
    settings.setHistory(docId, routeHash, query, "replace");
  }

  if (searchRouteActive) {
    if (typeof settings.renderSearchMode === "function") {
      settings.renderSearchMode();
    }
    return {
      docId: docId,
      route: route,
      searchRouteActive: true
    };
  }

  if (typeof settings.loadDoc === "function") {
    settings.loadDoc(docId, {
      historyMode: historyMode,
      hash: routeHash,
      expandTrail: typeof settings.docHasParent === "function" ? settings.docHasParent(docId) : true
    });
  }

  return {
    docId: docId,
    route: route,
    searchRouteActive: false
  };
}

export function loadViewerDoc(options) {
  var settings = options || {};
  var state = settings.state;
  var docId = settings.docId || "";
  var mode = settings.historyMode || "push";
  var hash = settings.hash || "";
  var shouldExpandTrail = settings.expandTrail !== false;
  var expandTrail = typeof settings.expandTrailForDoc === "function"
    ? settings.expandTrailForDoc
    : (typeof settings.expandTrail === "function" ? settings.expandTrail : null);
  var targetDocId = typeof settings.resolveLoadableDocId === "function" ? settings.resolveLoadableDocId(docId) : "";

  if (typeof settings.setRecentModeActive === "function") {
    settings.setRecentModeActive(false);
  }

  if (targetDocId && targetDocId !== docId) {
    return loadViewerDoc(Object.assign({}, settings, {
      docId: targetDocId,
      historyMode: mode === "none" ? "replace" : mode,
      hash: hash,
      expandTrail: shouldExpandTrail
    }));
  }

  var doc = state && state.docsById ? state.docsById.get(docId) : null;
  if (!doc) {
    if (typeof settings.setHistory === "function") {
      settings.setHistory(docId, hash, "", mode);
    }
    if (typeof settings.handleMissingDoc === "function") {
      settings.handleMissingDoc();
    }
    return Promise.resolve(null);
  }

  if (state) {
    state.selectedDocId = docId;
  }
  if (shouldExpandTrail && expandTrail) {
    expandTrail(docId);
  }
  if (typeof settings.renderBookmarkUi === "function") {
    settings.renderBookmarkUi();
  }
  if (typeof settings.setHistory === "function") {
    settings.setHistory(docId, hash, "", mode);
  }

  if (state && state.payloadCache && state.payloadCache.has(docId)) {
    if (typeof settings.renderPayload === "function") {
      settings.renderPayload(doc, state.payloadCache.get(docId), hash);
    }
    return Promise.resolve(state.payloadCache.get(docId));
  }

  if (typeof settings.renderLoadingState === "function") {
    settings.renderLoadingState(doc);
  }

  if (!state || typeof settings.fetchPayload !== "function") {
    return Promise.resolve(null);
  }

  var requestId = state.requestId + 1;
  state.requestId = requestId;

  return settings.fetchPayload(doc, docId)
    .then(function (payload) {
      if (state.requestId !== requestId) return null;
      if (state.payloadCache) {
        state.payloadCache.set(docId, payload);
      }
      state.reloadNonce = "";
      state.reloadExpectedDocId = "";
      if (typeof settings.renderPayload === "function") {
        settings.renderPayload(doc, payload, hash);
      }
      return payload;
    })
    .catch(function (error) {
      if (state.requestId !== requestId) return null;
      if (typeof settings.handlePayloadError === "function") {
        settings.handlePayloadError(error);
      }
      return null;
    });
}

export function handleViewerPopstate(options) {
  var settings = options || {};
  if (typeof settings.docsAvailable === "function" && !settings.docsAvailable()) return;
  if (settings.allowScopeQuery) {
    try {
      if (typeof settings.routeScopeFromUrl === "function" && settings.routeScopeFromUrl() !== settings.viewerScope) {
        if (typeof settings.reloadWindow === "function") {
          settings.reloadWindow();
        }
        return;
      }
    } catch (error) {
      if (typeof settings.setStatus === "function") {
        settings.setStatus(error.message || "Unknown docs scope.", true);
      }
      return;
    }
  }
  if (typeof settings.hideContextMenu === "function") {
    settings.hideContextMenu();
  }
  if (typeof settings.cancelSearchDebounce === "function") {
    settings.cancelSearchDebounce();
  }
  if (typeof settings.applyCurrentRoute === "function") {
    settings.applyCurrentRoute({
      historyMode: "none",
      hash: typeof settings.currentHash === "function" ? settings.currentHash() : ""
    });
  }
}
