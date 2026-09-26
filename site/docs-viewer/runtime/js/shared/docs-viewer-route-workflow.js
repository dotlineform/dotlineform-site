import {
  normalizeDocIdSet
} from "./docs-viewer-tree.js";
import {
  applyViewerRoute,
  buildViewerUrl,
  buildViewerUrlForDocument,
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
  var searchInput = context.searchInput;
  var statusCommands = context.statusCommands || {};
  var loadedIndex = "";
  var indexRefreshTimer = null;
  var indexRefreshRunning = false;

  function viewerStage() {
    return currentValue(context.viewerStage);
  }

  function viewerBaseUrl() {
    return currentValue(context.viewerBaseUrl);
  }

  function viewerPathname() {
    return currentValue(context.viewerPathname);
  }

  function preservedQueryParams() {
    var names = currentValue(context.preserveQueryParams);
    var current = new URLSearchParams(window.location.search);
    var preserved = {};
    (Array.isArray(names) ? names : []).forEach(function (name) {
      var value = current.get(name);
      if (value) preserved[name] = value;
    });
    return preserved;
  }

  function defaultRouteDocId() {
    return currentValue(context.defaultRouteDocId) || "";
  }

  function managementUiEnabled() {
    return Boolean(currentValue(context.managementUiEnabled));
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

  function currentReportRouteParams(docId) {
    var params = new URLSearchParams(window.location.search);
    if ((params.get("doc") || "") !== docId) return {};
    var subdoc = (params.get("subdoc") || "").trim();
    return subdoc ? { subdoc: subdoc } : {};
  }

  function hasDisallowedModeInUrl() {
    return new URLSearchParams(window.location.search).has("mode");
  }

  function viewerUrl(docId, hash, query, reportParams) {
    return buildViewerUrl({
      docId: docId,
      hash: hash,
      origin: window.location.origin,
      preservedQueryParams: preservedQueryParams(),
      query: query,
      reportParams: reportParams,
      viewerBaseUrl: viewerBaseUrl(),
    });
  }

  function viewerUrlForDocument(docId, options) {
    var stage = options && options.stage !== undefined ? options.stage : viewerStage();
    if (stage !== viewerStage() && !(context.workspaceConfig.stageConfigsById.has(stage))) throw new Error("Docs link stage is not configured.");
    return buildViewerUrlForDocument({
      docId: docId,
      origin: window.location.origin,
      viewerBaseUrl: viewerBaseUrl(),
      stage: stage
    });
  }

  function setHistory(docId, hash, query, mode, reportParams) {
    setViewerHistory({
      docId: docId,
      hash: hash,
      history: window.history,
      mode: mode,
      origin: window.location.origin,
      preservedQueryParams: preservedQueryParams(),
      query: query,
      reportParams: reportParams || currentReportRouteParams(docId),
      viewerBaseUrl: viewerBaseUrl(),
    });
  }

  function resolveDocId() {
    return resolveViewerRouteDocId({
      requestedDocId: currentDocId(),
      docsById: state.docsById,
      defaultRouteDocId: defaultRouteDocId(),
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
    return context.collectionProvider.readDocument(doc, {
      docId: docId
    }).finally(stopBusy);
  }

  async function loadDoc(docId, options) {
    if (!await context.confirmDocumentNavigation()) return null;
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
      reportParams: options && options.reportParams ? options.reportParams : currentReportRouteParams(docId),
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
      hasDisallowedModeInUrl: hasDisallowedModeInUrl,
      hash: options && options.hash ? options.hash : "",
      historyMode: options && options.historyMode ? options.historyMode : "push",
      loadDoc: loadDoc,
      managementContextActive: managementUiEnabled,
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
    });
    if (typeof context.updateInfoPanel === "function") {
      context.updateInfoPanel();
    }
    return result;
  }

  function replaceIndex(payload) {
    loadedIndex = JSON.stringify(payload);
    state.managementContext = managementUiEnabled();
    var viewerOptions = payload && payload.viewer_options && typeof payload.viewer_options === "object"
      ? payload.viewer_options
      : {};
    state.nonLoadableDocIds = normalizeDocIdSet(viewerOptions.non_loadable_doc_ids, []);
    state.manageOnlyTreeRootIds = normalizeDocIdSet(viewerOptions.manage_only_tree_root_ids, []);
    state.allDocs = Array.isArray(payload.docs) ? payload.docs.slice() : [];
    context.applyDocVisibility();
    if (typeof context.onIndexReplaced === "function") {
      context.onIndexReplaced({
        docs: state.docs.slice(),
        managementContext: state.managementContext,
        stage: viewerStage()
      });
    }

    context.renderSidebar();
    context.renderBookmarkUi();
  }

  function initializeIndex(payload) {
    replaceIndex(payload);

    if (state.docs.length === 0) {
      setStatus("No docs available.", true);
      return;
    }

    return applyCurrentRoute({ historyMode: "replace", hash: currentHash() });
  }

  function workingPollIsIdle() {
    return managementUiEnabled() && viewerStage() === "working" && !root.ownerDocument.hidden
      && root.dataset.managementBusy !== "true" && root.dataset.documentDisplayMode !== "markdown-source";
  }

  async function refreshDisplayedDocument() {
    var displayed = context.selectedDocument;
    var docId = displayed.displayedDocId;
    var requestId = state.requestId;
    var href = window.location.href;
    var report = context.managedDocumentContext();
    function current() {
      var view = context.activeViewState();
      return workingPollIsIdle() && view.activeModeId === "rendered-document"
        && view.activeViewId === "rendered-document" && state.requestId === requestId
        && displayed.displayedDocId === docId && state.selectedDocId === docId
        && window.location.href === href;
    }
    if (!docId || !current()) return;
    if (report && report.state === "detail" && report.documentTarget) {
      if (typeof report.refreshDisplayedDocument === "function") {
        await report.refreshDisplayedDocument(report.documentTarget, current);
      }
      return;
    }
    var doc = state.docsById.get(docId);
    if (!doc) return;
    var payload = await context.collectionProvider.readDocument(doc, { docId: docId });
    if (!current() || JSON.stringify(payload) === JSON.stringify(displayed.displayedPayload)) return;
    state.payloadCache.set(docId, payload);
    context.refreshRenderedPayload(doc, payload);
    context.updateInfoPanel();
  }

  // Read existing generated outputs. Neither refresh path participates in Source Save.
  async function refreshWorkingIndex() {
    if (indexRefreshRunning || !workingPollIsIdle()) return;
    var stage = viewerStage();
    indexRefreshRunning = true;
    try {
      var results = await Promise.allSettled([
        context.collectionProvider.readIndex(), refreshDisplayedDocument()
      ]);
      if (stage !== viewerStage() || !workingPollIsIdle()) return;
      var index = results[0];
      if (index.status === "fulfilled" && JSON.stringify(index.value) !== loadedIndex) {
        state.payloadCache.clear();
        replaceIndex(index.value);
        var displayed = context.selectedDocument;
        if (displayed.displayedPayload && displayed.displayedDocId === state.selectedDocId) {
          state.payloadCache.set(displayed.displayedDocId, displayed.displayedPayload);
        }
        context.renderManagementUi();
      }
      results.forEach(function (result) {
        if (result.status === "rejected") throw result.reason;
      });
    } catch (error) {
      setStatus(error.message || "Could not refresh Working generated output.", true);
    } finally {
      indexRefreshRunning = false;
    }
  }

  function startIndexRefresh() {
    if (indexRefreshTimer === null && managementUiEnabled()) {
      indexRefreshTimer = window.setInterval(refreshWorkingIndex, 2000);
    }
  }

  window.addEventListener("pagehide", function () {
    window.clearInterval(indexRefreshTimer);
    indexRefreshTimer = null;
  });
  window.addEventListener("pageshow", startIndexRefresh);

  function loadIndex() {
    var stopBusy = startBusy();
    return context.collectionProvider.readIndex()
      .then(function (payload) {
        startIndexRefresh();
        return initializeIndex(payload);
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
      currentHref: window.location.href,
      origin: window.location.origin,
      viewerPathname: viewerPathname(),
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
      if (route.error) { setStatus(route.error, true); return; }
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
        hash: route.hash,
        reportParams: route.reportParams || {}
      });
    });
  }

  function bindPopstate() {
    window.addEventListener("popstate", function () {
      handleViewerPopstate({
        applyCurrentRoute: applyCurrentRoute,
        cancelSearchDebounce: context.cancelSearchDebounce,
        currentHash: currentHash,
        docsAvailable: function () { return state.docs.length > 0; },
        hideContextMenu: context.hideContextMenu,
        reloadWindow: function () { window.location.reload(); },
        routeStageFromUrl: context.routeStageFromUrl,
        viewerStage: viewerStage(),
        setStatus: setStatus,
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
    viewerUrlForDocument: viewerUrlForDocument
  };

  return {
    bindPopstate: bindPopstate,
    bindRouteLinks: bindRouteLinks,
    commands: commands,
    currentDocId: currentDocId,
    currentHash: currentHash,
    currentQuery: currentQuery,
    hasDisallowedModeInUrl: hasDisallowedModeInUrl,
    initializeIndex: initializeIndex,
    managementUiEnabled: managementUiEnabled,
    routeFromAnchor: routeFromAnchor,
    shouldUseNativeNavigation: shouldUseNativeNavigation,
    viewerUrl: viewerUrl,
    viewerUrlForDocument: viewerUrlForDocument
  };
}
