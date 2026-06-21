import {
  compareDocs,
  normalizeDocIdSet
} from "./docs-viewer-tree.js";
import {
  applyViewerRoute,
  buildViewerUrl,
  buildViewerUrlForScope,
  handleViewerPopstate,
  loadViewerDoc,
  resolveViewerRouteDocId,
  routeFromAnchorHref,
  setViewerHistory
} from "./docs-viewer-router.js";

function currentValue(value) {
  return typeof value === "function" ? value() : value;
}

function createRouteWorkflowStateBridge(inputs) {
  var routeSession = inputs.routeSession || {};
  var documentIndex = inputs.documentIndex || {};
  var selectedDocument = inputs.selectedDocument || {};
  var searchRecent = inputs.searchRecent || {};

  return {
    get managementContext() { return Boolean(routeSession.managementContext); },
    set managementContext(value) { routeSession.managementContext = Boolean(value); },
    get allDocs() { return documentIndex.allDocs || []; },
    set allDocs(value) { documentIndex.allDocs = value; },
    get docs() { return documentIndex.docs || []; },
    set docs(value) { documentIndex.docs = value; },
    get docsById() { return documentIndex.docsById || new Map(); },
    set docsById(value) { documentIndex.docsById = value; },
    get expandedDocIds() { return documentIndex.expandedDocIds || new Set(); },
    set expandedDocIds(value) { documentIndex.expandedDocIds = value; },
    get nonLoadableDocIds() { return documentIndex.nonLoadableDocIds || new Set(); },
    set nonLoadableDocIds(value) { documentIndex.nonLoadableDocIds = value; },
    get manageOnlyTreeRootIds() { return documentIndex.manageOnlyTreeRootIds || new Set(); },
    set manageOnlyTreeRootIds(value) { documentIndex.manageOnlyTreeRootIds = value; },
    get showUpdatedDate() { return documentIndex.showUpdatedDate; },
    set showUpdatedDate(value) { documentIndex.showUpdatedDate = value; },
    get selectedDocId() { return selectedDocument.selectedDocId || ""; },
    set selectedDocId(value) { selectedDocument.selectedDocId = value; },
    get payloadCache() { return selectedDocument.payloadCache || new Map(); },
    set payloadCache(value) { selectedDocument.payloadCache = value; },
    get requestId() { return selectedDocument.requestId || 0; },
    set requestId(value) { selectedDocument.requestId = value; },
    get reloadNonce() { return selectedDocument.reloadNonce || ""; },
    set reloadNonce(value) { selectedDocument.reloadNonce = value; },
    get reloadExpectedDocId() { return selectedDocument.reloadExpectedDocId || ""; },
    set reloadExpectedDocId(value) { selectedDocument.reloadExpectedDocId = value; },
    get searchQuery() { return searchRecent.searchQuery || ""; },
    set searchQuery(value) { searchRecent.searchQuery = value; },
    get searchVisibleCount() { return searchRecent.searchVisibleCount || 0; },
    set searchVisibleCount(value) { searchRecent.searchVisibleCount = value; },
    get searchRouteActive() { return Boolean(searchRecent.searchRouteActive); },
    set searchRouteActive(value) { searchRecent.searchRouteActive = Boolean(value); }
  };
}

export function initDocsViewerRouteWorkflow(context) {
  var state = createRouteWorkflowStateBridge({
    routeSession: context.routeSession,
    documentIndex: context.documentIndex,
    selectedDocument: context.selectedDocument,
    searchRecent: context.searchRecent
  });
  var window = context.window;
  var root = context.root;
  var content = context.content;
  var results = context.results;
  var more = context.more;
  var searchInput = context.searchInput;
  var scopeConfig = context.scopeConfig || {};
  var statusCommands = context.statusCommands || {};

  function viewerScope() {
    return currentValue(context.viewerScope);
  }

  function viewerBaseUrl() {
    return currentValue(context.viewerBaseUrl);
  }

  function routeViewerBaseUrl() {
    return currentValue(context.routeViewerBaseUrl);
  }

  function viewerPathname() {
    return currentValue(context.viewerPathname);
  }

  function includeScopeParam() {
    return Boolean(currentValue(context.includeScopeParam));
  }

  function defaultRouteDocId() {
    return currentValue(context.defaultRouteDocId) || "";
  }

  function allowManagement() {
    return Boolean(currentValue(context.allowManagement));
  }

  function allowScopeQuery() {
    return Boolean(currentValue(context.allowScopeQuery));
  }

  function indexTreeUrl() {
    return currentValue(context.indexTreeUrl);
  }

  function scopeConfigsById() {
    return scopeConfig.scopeConfigsById || new Map();
  }

  function setStatus(message, isError) {
    if (typeof statusCommands.setStatus === "function") {
      statusCommands.setStatus(message, isError);
    }
  }

  function startBusy() {
    if (typeof statusCommands.startBusy === "function") {
      return statusCommands.startBusy();
    }
    return function () {};
  }

  function currentDocId() {
    return new URLSearchParams(window.location.search).get("doc") || "";
  }

  function currentHash() {
    return window.location.hash ? window.location.hash.slice(1) : "";
  }

  function currentQuery() {
    return (new URLSearchParams(window.location.search).get("q") || "").trim();
  }

  function isManagementContext() {
    return allowManagement();
  }

  function hasCanonicalScopeInUrl() {
    if (!includeScopeParam() || !viewerScope()) return true;
    return new URLSearchParams(window.location.search).get("scope") === viewerScope();
  }

  function hasDisallowedModeInUrl() {
    return new URLSearchParams(window.location.search).has("mode");
  }

  function hasDisallowedScopeInUrl() {
    return !allowScopeQuery() && new URLSearchParams(window.location.search).has("scope");
  }

  function viewerUrl(docId, hash, query) {
    return buildViewerUrl({
      docId: docId,
      hash: hash,
      includeScopeParam: includeScopeParam(),
      origin: window.location.origin,
      query: query,
      viewerBaseUrl: viewerBaseUrl(),
      viewerScope: viewerScope()
    });
  }

  function viewerUrlForScope(scope, docId, options) {
    return buildViewerUrlForScope({
      allowManagement: allowManagement(),
      docId: docId,
      manage: Boolean(options && options.manage),
      origin: window.location.origin,
      routeViewerBaseUrl: routeViewerBaseUrl(),
      scope: scope,
      scopeConfigsById: scopeConfigsById(),
      viewerBaseUrl: viewerBaseUrl(),
      viewerScope: viewerScope()
    });
  }

  function setHistory(docId, hash, query, mode) {
    setViewerHistory({
      docId: docId,
      hash: hash,
      history: window.history,
      includeScopeParam: includeScopeParam(),
      mode: mode,
      origin: window.location.origin,
      query: query,
      viewerBaseUrl: viewerBaseUrl(),
      viewerScope: viewerScope()
    });
  }

  function resolveDocId() {
    return resolveViewerRouteDocId({
      requestedDocId: currentDocId(),
      docsById: state.docsById,
      defaultRouteDocId: defaultRouteDocId(),
      viewerScope: viewerScope(),
      resolveLoadableDocId: context.resolveLoadableDocId,
      defaultDocId: context.defaultDocId
    });
  }

  function clearManagementMessageForDocChange(docId) {
    if (typeof context.clearManagementMessageForDocChange === "function") {
      context.clearManagementMessageForDocChange(docId);
    }
  }

  function fetchDocPayload(doc, docId) {
    var stopBusy = startBusy();
    return context.generatedData.readDocumentPayload(doc, {
      docId: docId,
      viewerScope: viewerScope()
    }).finally(stopBusy);
  }

  function loadDoc(docId, options) {
    clearManagementMessageForDocChange(docId);
    return loadViewerDoc({
      docId: docId,
      expandTrailForDoc: context.expandTrail,
      expandTrail: !options || options.expandTrail !== false,
      fetchPayload: fetchDocPayload,
      handleMissingDoc: context.handleMissingDoc,
      handlePayloadError: context.handlePayloadError,
      hash: options && options.hash ? options.hash : "",
      historyMode: options && options.historyMode ? options.historyMode : "push",
      renderBookmarkUi: context.renderBookmarkUi,
      renderLoadingState: context.renderDocLoadingState,
      renderPayload: context.renderPayload,
      resolveLoadableDocId: context.resolveLoadableDocId,
      setHistory: setHistory,
      setRecentModeActive: context.setRecentModeActive,
      state: state
    });
  }

  function applyCurrentRoute(options) {
    var result = applyViewerRoute({
      applyDocVisibility: context.applyDocVisibility,
      currentDocId: currentDocId,
      currentHash: currentHash,
      currentQuery: currentQuery,
      defaultDocId: context.defaultDocId,
      defaultRouteDocId: defaultRouteDocId(),
      docHasParent: function (docId) {
        var doc = state.docsById.get(docId);
        return Boolean(doc && doc.parent_id);
      },
      expandTrail: context.expandTrail,
      hasActiveQuery: context.hasActiveQuery,
      hasCanonicalScopeInUrl: hasCanonicalScopeInUrl,
      hasDisallowedModeInUrl: hasDisallowedModeInUrl,
      hasDisallowedScopeInUrl: hasDisallowedScopeInUrl,
      hash: options && options.hash ? options.hash : "",
      historyMode: options && options.historyMode ? options.historyMode : "push",
      loadDoc: loadDoc,
      managementContextActive: isManagementContext,
      renderBookmarkUi: context.renderBookmarkUi,
      renderManagementUi: context.renderManagementUi,
      renderSearchMode: context.renderSearchMode,
      renderSidebar: context.renderSidebar,
      resolveLoadableDocId: context.resolveLoadableDocId,
      searchInput: searchInput,
      setHistory: setHistory,
      setRecentModeActive: context.setRecentModeActive,
      setStatus: setStatus,
      state: state,
      syncNonViewableVisibilityForRequestedDoc: context.syncNonViewableVisibilityForRequestedDoc,
      viewerScope: viewerScope()
    });
    if (typeof context.updateInfoPanel === "function") {
      context.updateInfoPanel();
    }
    return result;
  }

  function initializeIndex(payload) {
    state.managementContext = isManagementContext();
    var viewerOptions = payload && payload.viewer_options && typeof payload.viewer_options === "object"
      ? payload.viewer_options
      : {};
    state.nonLoadableDocIds = normalizeDocIdSet(viewerOptions.non_loadable_doc_ids, []);
    state.manageOnlyTreeRootIds = normalizeDocIdSet(viewerOptions.manage_only_tree_root_ids, []);
    state.showUpdatedDate = viewerOptions.show_updated_date !== false;
    state.allDocs = Array.isArray(payload.docs) ? payload.docs.slice().sort(compareDocs) : [];
    context.syncNonViewableVisibilityForRequestedDoc();
    context.applyDocVisibility();

    context.renderSidebar();
    context.renderBookmarkUi();

    if (state.docs.length === 0) {
      setStatus("No docs available.", true);
      return;
    }

    applyCurrentRoute({ historyMode: "replace", hash: currentHash() });
  }

  function loadIndex() {
    var stopBusy = startBusy();
    return context.generatedData.readDocsIndexTree({
      indexTreeUrl: indexTreeUrl(),
      viewerScope: viewerScope()
    })
      .then(function (payload) {
        initializeIndex(payload);
      })
      .catch(function (error) {
        state.reloadExpectedDocId = "";
        setStatus(error.message || "Failed to load docs index tree.", true);
        context.hideDocPane();
        if (content) content.textContent = "";
        throw error;
      })
      .finally(function () {
        stopBusy();
      });
  }

  function routeFromAnchor(anchor) {
    return routeFromAnchorHref(anchor.href, {
      allowManagement: allowManagement(),
      allowScopeQuery: allowScopeQuery(),
      currentHref: window.location.href,
      includeScopeParam: includeScopeParam(),
      origin: window.location.origin,
      viewerPathname: viewerPathname(),
      viewerScope: viewerScope()
    });
  }

  function shouldUseNativeNavigation(event, anchor) {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return true;
    }
    var target = anchor.getAttribute("target");
    return Boolean((target && target !== "_self") || anchor.hasAttribute("download"));
  }

  function bindRouteLinks() {
    root.addEventListener("click", function (event) {
      if (typeof context.handleManagementRootClick === "function" && context.handleManagementRootClick(event)) {
        return;
      }
      var toggle = event.target.closest("[data-toggle-doc-id]");
      if (toggle) {
        var toggleDocId = toggle.dataset.toggleDocId;
        if (state.expandedDocIds.has(toggleDocId)) {
          state.expandedDocIds.delete(toggleDocId);
        } else {
          state.expandedDocIds.add(toggleDocId);
        }
        context.renderSidebar();
        return;
      }

      var anchor = event.target.closest("a[href]");
      if (!anchor) return;
      if (shouldUseNativeNavigation(event, anchor)) return;

      var route = routeFromAnchor(anchor);
      if (!route) return;

      event.preventDefault();
      if (route.navigateUrl) {
        window.location.assign(route.navigateUrl);
        return;
      }
      context.cancelSearchDebounce();
      state.searchQuery = "";
      state.searchVisibleCount = context.searchBatchSize;
      if (searchInput) {
        searchInput.value = "";
      }
      loadDoc(route.docId, {
        historyMode: "push",
        hash: route.hash
      });
    });
  }

  function bindPopstate() {
    window.addEventListener("popstate", function () {
      handleViewerPopstate({
        allowScopeQuery: allowScopeQuery(),
        applyCurrentRoute: applyCurrentRoute,
        cancelSearchDebounce: context.cancelSearchDebounce,
        currentHash: currentHash,
        docsAvailable: function () { return state.docs.length > 0; },
        hideContextMenu: context.hideContextMenu,
        reloadWindow: function () { window.location.reload(); },
        routeScopeFromUrl: context.routeScopeFromUrl,
        setStatus: setStatus,
        viewerScope: viewerScope()
      });
    });
  }

  var commands = {
    applyCurrentRoute: applyCurrentRoute,
    loadDoc: loadDoc,
    loadIndex: loadIndex,
    resolveDocId: resolveDocId,
    setHistory: setHistory,
    viewerUrl: viewerUrl,
    viewerUrlForScope: viewerUrlForScope
  };

  return {
    bindPopstate: bindPopstate,
    bindRouteLinks: bindRouteLinks,
    commands: commands,
    currentDocId: currentDocId,
    currentHash: currentHash,
    currentQuery: currentQuery,
    hasCanonicalScopeInUrl: hasCanonicalScopeInUrl,
    hasDisallowedModeInUrl: hasDisallowedModeInUrl,
    hasDisallowedScopeInUrl: hasDisallowedScopeInUrl,
    initializeIndex: initializeIndex,
    isManagementContext: isManagementContext,
    routeFromAnchor: routeFromAnchor,
    shouldUseNativeNavigation: shouldUseNativeNavigation,
    viewerUrl: viewerUrl,
    viewerUrlForScope: viewerUrlForScope
  };
}
