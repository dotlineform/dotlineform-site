export function buildViewerUrl(options) {
  var settings = options || {};
  var url = new URL(settings.viewerBaseUrl || "/docs/", settings.origin || window.location.origin);
  Object.entries(settings.preservedQueryParams || {}).forEach(function (entry) {
    var key = String(entry[0] || "").trim();
    var value = String(entry[1] == null ? "" : entry[1]).trim();
    if (key === "scope" || key === "stage") throw new Error("This Docs URL uses retired context.");
    if (key && value) url.searchParams.set(key, value);
  });
  url.searchParams.set("doc", settings.docId || "");
  if (typeof settings.query === "string" && settings.query.trim()) {
    url.searchParams.set("q", settings.query.trim());
  }
  Object.entries(settings.reportParams || {}).forEach(function (entry) {
    var key = String(entry[0] || "").trim();
    var value = String(entry[1] == null ? "" : entry[1]).trim();
    if (key === "scope" || key === "stage") throw new Error("This Docs URL uses retired context.");
    if (key && value) url.searchParams.set(key, value);
  });
  url.hash = settings.hash || "";
  return url.pathname + url.search + url.hash;
}

export function buildViewerUrlForDocument(options) {
  var settings = options || {};
  return buildViewerUrl({
    viewerBaseUrl: settings.viewerBaseUrl,
    origin: settings.origin,
    docId: settings.docId
  });
}

export function routeFromAnchorHref(href, options) {
  var settings = options || {};
  var url = new URL(href, settings.currentHref || window.location.href);
  var origin = settings.origin || window.location.origin;
  if (url.origin !== origin) return null;
  if (url.pathname !== settings.viewerPathname) return null;

  if (url.searchParams.has("scope") || url.searchParams.has("stage")) {
    return { error: "This Docs URL uses retired context; use a current document link." };
  }
  url.searchParams.delete("mode");

  var docId = url.searchParams.get("doc");
  if (!docId) return null;
  var subdoc = String(url.searchParams.get("subdoc") || "").trim();

  return {
    docId: docId,
    reportParams: subdoc ? { subdoc: subdoc } : {},
    hash: url.hash ? url.hash.slice(1) : ""
  };
}

export function writeViewerHistory(history, docId, url, hash, query, mode, reportParams, indexViewId) {
  if (mode === "none") return;
  var nextState = { docId: docId, hash: hash || "", q: query || "", reportParams: reportParams || {}, indexViewId: indexViewId || "index-tree" };
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
    settings.mode,
    settings.reportParams,
    settings.indexViewId
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

/** Apply Index history independently; open a document only when its exact displayed route changed. */
export function applyViewerRoute(options) {
  var settings = options || {};
  var state = settings.state;
  var routeHash = settings.hash || (typeof settings.currentHash === "function" ? settings.currentHash() : "");
  var historyMode = settings.historyMode || "push";

  if (state && typeof settings.managementContextActive === "function") {
    state.managementContext = settings.managementContextActive();
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
      route: route
    };
  }

  var query = typeof settings.currentQuery === "function" ? settings.currentQuery() : "";
  settings.syncIndexRoute(query);

  var shouldReplaceHistory = route.corrected;
  if (!shouldReplaceHistory && typeof settings.hasDisallowedModeInUrl === "function") {
    shouldReplaceHistory = settings.hasDisallowedModeInUrl();
  }
  if (shouldReplaceHistory && typeof settings.setHistory === "function") {
    settings.setHistory(docId, routeHash, query, "replace");
  }

  var loading = null;
  if (!settings.isCurrentDocumentRoute(docId, routeHash)) {
    loading = settings.loadDoc(docId, {
      historyMode: historyMode,
      hash: routeHash
    });
  }

  return {
    docId: docId,
    route: route,
    loading: loading
  };
}

/** Open the requested document through the existing cache/read path while retaining the Index view/query. */
export function loadViewerDoc(options) {
  var settings = options || {};
  var state = settings.state;
  var docId = settings.docId || "";
  var mode = settings.historyMode || "push";
  var hash = settings.hash || "";
  var targetDocId = typeof settings.resolveLoadableDocId === "function" ? settings.resolveLoadableDocId(docId) : "";

  if (targetDocId && targetDocId !== docId) {
    return loadViewerDoc(Object.assign({}, settings, {
      docId: targetDocId,
      historyMode: mode === "none" ? "replace" : mode,
      hash: hash,
      reportParams: settings.reportParams
    }));
  }

  var doc = state && state.docsById ? state.docsById.get(docId) : null;
  var requestId = state.requestId + 1;
  state.requestId = requestId;
  state.selectedDocId = docId;
  if (!doc) {
    if (typeof settings.setHistory === "function") {
      settings.setHistory(docId, hash, state.searchQuery, mode, settings.reportParams || {});
    }
    settings.trackSidebarSelection();
    if (typeof settings.handleMissingDoc === "function") {
      settings.handleMissingDoc();
    }
    return Promise.resolve(null);
  }

  if (typeof settings.renderBookmarkUi === "function") {
    settings.renderBookmarkUi();
  }
  if (typeof settings.setHistory === "function") {
    settings.setHistory(docId, hash, state.searchQuery, mode, settings.reportParams || {});
  }
  settings.trackSidebarSelection();

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
