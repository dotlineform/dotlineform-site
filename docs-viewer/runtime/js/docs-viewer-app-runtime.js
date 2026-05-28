import {
  normalizeSearchText
} from "./docs-viewer-search.js";
import {
  createDocsViewerBookmarkRouteCallbacks,
  initDocsViewerBookmarks
} from "./docs-viewer-bookmarks.js";
import {
  formatText,
  getConfigText,
  getConfigValue,
  initDocsViewerConfigController
} from "./docs-viewer-config-controller.js";
import {
  initDocsViewerDocumentController
} from "./docs-viewer-document-controller.js";
import {
  createDocsViewerSearchRouteCallbacks,
  initDocsViewerSearchController
} from "./docs-viewer-search-controller.js";
import {
  initDocsViewerRouteWorkflow
} from "./docs-viewer-route-workflow.js";
import {
  escapeHtml
} from "./docs-viewer-render.js";
import {
  initDocsViewerSidebarRenderer
} from "./docs-viewer-sidebar.js";
import {
  updateDocsViewerRouteContext
} from "./docs-viewer-app-context.js";
import {
  createDocsViewerInfoPanelController
} from "./docs-viewer-info-panel-controller.js";
import {
  createDocsViewerManagementRuntimeAdapter
} from "./docs-viewer-runtime-lazy-controller.js";
import {
  DOCS_VIEWER_RUNTIME_DEFAULTS,
  createDocsViewerAppComposition,
  startDocsViewerStartupPhases
} from "./docs-viewer-app-composition.js";
export function startDocsViewerRuntime(options) {
  var settings = options || {};
  var root = settings.root;
  var document = settings.document;
  var window = settings.window;
  var assetVersion = settings.assetVersion || "";
  var routeContext = settings.routeContext;
  var appShellReady = settings.appShellReady || Promise.resolve(null);
  var appShellRefs = settings.appShellRefs || {};
  if (!root || !document || !window || !routeContext) return null;

  var indexPanelRefs = appShellRefs.indexPanel;
  var nav = indexPanelRefs.nav;
  var sidebarToggle = indexPanelRefs.sidebarToggle;
  var sidebarExpand = indexPanelRefs.sidebarExpand;
  var documentShellRefs = appShellRefs.documentShell;
  var infoPanelRefs = appShellRefs.infoPanel;
  var status = appShellRefs.status;
  var meta = documentShellRefs.meta;
  var pathEl = documentShellRefs.pathEl;
  var updatedEl = documentShellRefs.updatedEl;
  var summaryEl = documentShellRefs.summaryEl;
  var bookmarkRow = appShellRefs.bookmarkRow;
  var infoToggle = documentShellRefs.infoToggle;
  var bookmarkToggle = documentShellRefs.bookmarkToggle;
  var statusPills = documentShellRefs.statusPills;
  var content = documentShellRefs.content;
  var scopeSelect = appShellRefs.headerControls.scopeSelect;
  var recentButton = appShellRefs.headerControls.recentButton;
  var searchInput = appShellRefs.headerControls.searchInput;
  var resultsStatus = documentShellRefs.resultsStatus;
  var results = documentShellRefs.results;
  var more = documentShellRefs.more;

  var allowManagement = routeContext.access.allowManagement;
  var allowScopeQuery = routeContext.access.allowScopeQuery;
  var docsViewerConfigUrl = routeContext.docsViewerConfigUrl;
  var routeViewerBaseUrl = routeContext.routeViewerBaseUrl;
  var indexUrl = routeContext.indexUrl;
  var viewerBaseUrl = routeContext.viewerBaseUrl;
  var viewerScope = routeContext.viewerScope;
  var includeScopeParam = routeContext.includeScopeParam;
  var defaultRouteDocId = routeContext.defaultRouteDocId;
  var viewerPathname = routeContext.viewerPathname;
  var searchIndexUrl = routeContext.searchIndexUrl;
  var uiTextUrl = routeContext.uiTextUrl;
  var reportRegistryUrl = routeContext.reportRegistryUrl;
  var managementBaseUrl = routeContext.managementBaseUrl;
  var runtimeDefaults = DOCS_VIEWER_RUNTIME_DEFAULTS;
  var SEARCH_BATCH_SIZE = runtimeDefaults.searchBatchSize;
  var SEARCH_DEBOUNCE_MS = runtimeDefaults.searchDebounceMs;
  var DEFAULT_RECENT_LIMIT = runtimeDefaults.defaultRecentLimit;
  var BOOKMARK_DB_NAME = runtimeDefaults.bookmarkDbName;
  var BOOKMARK_DB_VERSION = runtimeDefaults.bookmarkDbVersion;
  var BOOKMARK_STORE_NAME = runtimeDefaults.bookmarkStoreName;
  var MANAGEMENT_MODE = runtimeDefaults.managementMode;
  var MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS = runtimeDefaults.managementCapabilityRetryAttempts;
  var MANAGEMENT_CAPABILITY_RETRY_DELAY_MS = runtimeDefaults.managementCapabilityRetryDelayMs;
  var UI_STATUS_EMOJI_MAX_LENGTH = runtimeDefaults.uiStatusEmojiMaxLength;
  var SIDEBAR_COLLAPSE_MEDIA = runtimeDefaults.sidebarCollapseMedia;
  var bookmarkScope = routeContext.bookmarkScope;
  var composition = createDocsViewerAppComposition({
    root: root,
    window: window,
    routeContext: routeContext,
    appShellRefs: appShellRefs,
    assetVersion: assetVersion,
    viewerScope: function () { return viewerScope; },
    indexPanelAvailable: sidebarCollapseAvailable
  });
  var hostedViewRegistry = composition.hostedViewRegistry;
  managementBaseUrl = composition.managementBaseUrl;
  var panelLayout = composition.panelLayout;
  var managementRuntime = null;
  var bookmarkController = null;
  var documentController = null;
  var routeWorkflow = null;
  var documentIndex = null;
  var infoPanelController = null;

  var appSession = composition.appSession;
  var state = appSession.state;
  documentIndex = composition.documentIndex;
  var generatedDataRuntime = composition.generatedDataRuntime;
  var dataRequestOptions = generatedDataRuntime.dataRequestOptions;
  var checkGeneratedDataReadCapability = generatedDataRuntime.checkGeneratedDataReadCapability;
  var sidebarRenderer = initDocsViewerSidebarRenderer({
    canDragCurrentDoc: canDragCurrentDoc,
    meta: meta,
    nav: nav,
    pathEl: pathEl,
    renderBookmarkToggle: renderBookmarkToggle,
    renderStatusPills: renderStatusPills,
    state: state,
    statusForIndexDoc: documentIndex.statusForIndexDoc,
    summaryEl: summaryEl,
    updateNavDragState: updateNavDragState,
    updatedEl: updatedEl,
    viewerTargetDocId: documentIndex.viewerTargetDocId,
    viewerUrl: viewerUrl
  });
  infoPanelController = createDocsViewerInfoPanelController({
    buildTrail: buildTrail,
    infoToggle: infoToggle,
    projectDocumentShell: projectDocumentShell,
    projectInfoPanel: function (projection) { panelLayout.projectInfoPanel(projection || {}); },
    projectViewState: function () { return panelLayout.projectViewState(); },
    refs: infoPanelRefs,
    registry: hostedViewRegistry,
    routeAccess: function () { return routeContext.access; },
    state: state,
    viewerScope: function () { return viewerScope; },
    viewerTargetDocId: documentIndex.viewerTargetDocId,
    viewerUrl: viewerUrl
  });
  documentController = initDocsViewerDocumentController({
    allowManagement: allowManagement,
    checkGeneratedDataReadCapability: checkGeneratedDataReadCapability,
    clearResultsStatus: clearResultsStatus,
    content: content,
    generatedData: generatedDataRuntime,
    hasActiveQuery: hasActiveQuery,
    managementBaseUrl: function () { return managementBaseUrl; },
    meta: meta,
    more: more,
    projectDocumentShell: projectDocumentShell,
    renderBookmarkToggle: renderBookmarkToggle,
    renderBookmarkUi: renderBookmarkUi,
    renderManagementUi: renderManagementUi,
    renderMeta: renderMeta,
    renderSearchMode: renderSearchMode,
    renderSidebar: renderSidebar,
    renderStatusPills: renderStatusPills,
    reportRegistryUrl: function () { return reportRegistryUrl; },
    results: results,
    scopeConfigs: function () { return state.scopeConfigs; },
    setRecentModeActive: setRecentModeActive,
    setStatus: setStatus,
    state: state,
    viewerScope: function () { return viewerScope; },
    viewerUrlForScope: viewerUrlForScope
  });
  routeWorkflow = initDocsViewerRouteWorkflow({
    allowManagement: function () { return allowManagement; },
    allowScopeQuery: function () { return allowScopeQuery; },
    applyDocVisibility: documentIndex.applyDocVisibility,
    cancelSearchDebounce: cancelSearchDebounce,
    clearManagementMessageForDocChange: clearManagementMessageForDocChange,
    content: content,
    defaultDocId: documentIndex.defaultDocId,
    defaultRouteDocId: function () { return defaultRouteDocId; },
    expandTrail: expandTrail,
    handleManagementRootClick: function (event) {
      var controller = managementRuntime ? managementRuntime.controller() : null;
      return Boolean(controller && controller.handleRootClick(event));
    },
    handleMissingDoc: handleMissingDoc,
    handlePayloadError: handlePayloadError,
    hasActiveQuery: hasActiveQuery,
    hideContextMenu: hideContextMenu,
    hideDocPane: hideDocPane,
    generatedData: generatedDataRuntime,
    includeScopeParam: function () { return includeScopeParam; },
    indexUrl: function () { return indexUrl; },
    managementModeValue: MANAGEMENT_MODE,
    more: more,
    renderBookmarkUi: renderBookmarkUi,
    renderDocLoadingState: renderDocLoadingState,
    renderManagementUi: renderManagementUi,
    renderPayload: renderPayload,
    renderSearchMode: renderSearchMode,
    renderSidebar: renderSidebar,
    resolveLoadableDocId: documentIndex.resolveLoadableDocId,
    results: results,
    root: root,
    routeScopeFromUrl: routeScopeFromUrl,
    routeViewerBaseUrl: function () { return routeViewerBaseUrl; },
    scopeConfigsById: function () { return state.scopeConfigsById; },
    searchBatchSize: SEARCH_BATCH_SIZE,
    searchInput: searchInput,
    setRecentModeActive: setRecentModeActive,
    setStatus: setStatus,
    startBusy: startBusy,
    state: state,
    syncHiddenVisibilityForRequestedDoc: function () {
      documentIndex.syncHiddenVisibilityForRequestedDoc(getCurrentDocId);
    },
    updateInfoPanel: updateInfoPanel,
    viewerBaseUrl: function () { return viewerBaseUrl; },
    viewerPathname: function () { return viewerPathname; },
    viewerScope: function () { return viewerScope; },
    window: window
  });
  var searchRouteCallbacks = createDocsViewerSearchRouteCallbacks({
    defaultDocId: documentIndex.defaultDocId,
    routeWorkflow: routeWorkflow,
    viewerTargetDocId: documentIndex.viewerTargetDocId
  });
  var searchPaneCallbacks = {
    hideDocPane: hideDocPane,
    showRecentPane: showRecentPane,
    showSearchPane: showSearchPane
  };
  var searchController = initDocsViewerSearchController({
    cancelSearchDebounce: cancelSearchDebounce,
    generatedData: generatedDataRuntime,
    hideContextMenu: hideContextMenu,
    hasActiveQuery: hasActiveQuery,
    more: more,
    paneCallbacks: searchPaneCallbacks,
    recentButton: recentButton,
    resultsStatus: resultsStatus,
    results: results,
    routeCallbacks: searchRouteCallbacks,
    searchBatchSize: SEARCH_BATCH_SIZE,
    searchDebounceMs: SEARCH_DEBOUNCE_MS,
    searchIndexUrl: function () { return searchIndexUrl; },
    searchInput: searchInput,
    setRecentModeActive: setRecentModeActive,
    setStatus: setStatus,
    startBusy: startBusy,
    state: state,
    viewerScope: function () { return viewerScope; }
  });
  var configController = initDocsViewerConfigController({
    allowScopeQuery: allowScopeQuery,
    applyRouteGlobals: applyRouteGlobals,
    dataRequestOptions: dataRequestOptions,
    defaultRecentLimit: DEFAULT_RECENT_LIMIT,
    docsViewerConfigUrl: docsViewerConfigUrl,
    getCurrentMode: getCurrentMode,
    managementController: function () {
      return managementRuntime ? managementRuntime.controller() : null;
    },
    managementMode: MANAGEMENT_MODE,
    recentButton: recentButton,
    renderRecentMode: renderRecentMode,
    renderSidebar: renderSidebar,
    renderStatusPills: renderStatusPills,
    root: root,
    routeViewerBaseUrl: routeViewerBaseUrl,
    scopeSelect: scopeSelect,
    state: state,
    uiStatusEmojiMaxLength: UI_STATUS_EMOJI_MAX_LENGTH,
    uiTextUrl: uiTextUrl,
    viewerBaseUrl: function () { return viewerBaseUrl; },
    viewerScope: function () { return viewerScope; }
  });

  managementRuntime = createDocsViewerManagementRuntimeAdapter({
    allowManagement: allowManagement,
    appShellReady: appShellReady,
    constants: {
      MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS: MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS,
      MANAGEMENT_CAPABILITY_RETRY_DELAY_MS: MANAGEMENT_CAPABILITY_RETRY_DELAY_MS,
      MANAGEMENT_MODE: MANAGEMENT_MODE,
      SEARCH_BATCH_SIZE: SEARCH_BATCH_SIZE
    },
    context: {
      applyDocVisibility: documentIndex.applyDocVisibility,
      cancelSearchDebounce: cancelSearchDebounce,
      cssEscape: cssEscape,
      currentViewerConfig: function () { return state.viewerConfig || {}; },
      defaultDocId: documentIndex.defaultDocId,
      defaultRouteDocId: function () { return defaultRouteDocId; },
      docsViewerConfigUrl: docsViewerConfigUrl,
      escapeHtml: escapeHtml,
      findAllDocById: documentIndex.findAllDocById,
      formatText: formatText,
      getConfigText: getConfigText,
      getConfigValue: getConfigValue,
      getCurrentMode: getCurrentMode,
      loadDoc: loadDoc,
      loadIndex: loadIndex,
      managementBaseUrl: managementBaseUrl,
      managementShellRefs: appShellRefs.managementShell || {},
      nav: nav,
      renderBookmarkUi: renderBookmarkUi,
      renderRecentMode: renderRecentMode,
      renderSearchMode: renderSearchMode,
      renderSidebar: renderSidebar,
      root: root,
      searchInput: searchInput,
      setHistory: setHistory,
      setStatus: setStatus,
      state: state,
      uiTextUrl: uiTextUrl,
      markdownDocLink: markdownDocLink,
      reloadDocsViewerConfig: function () { return configController.reloadDocsViewerConfig(); },
      viewerScope: function () { return viewerScope; }
    },
    logger: window.console || console,
    onLoaded: function () {
      renderSidebar();
    }
  });

  function loadManagementController() {
    return managementRuntime.load();
  }

  function routeScopeFromUrl() {
    return configController.routeScopeFromUrl();
  }

  function applyRouteGlobals(values) {
    routeContext = updateDocsViewerRouteContext(routeContext, values, { window: window });
    appSession.domains.routeSession.updateRouteContext(routeContext);
    viewerScope = routeContext.viewerScope;
    indexUrl = routeContext.indexUrl;
    searchIndexUrl = routeContext.searchIndexUrl;
    defaultRouteDocId = routeContext.defaultRouteDocId;
    viewerBaseUrl = routeContext.viewerBaseUrl;
    includeScopeParam = routeContext.includeScopeParam;
    viewerPathname = routeContext.viewerPathname;
    bookmarkScope = routeContext.bookmarkScope;
    state.indexPanelState = panelLayout.setStorageScope(bookmarkScope);
  }

  function loadDocsViewerConfig() {
    return configController.loadDocsViewerConfig();
  }

  function handleScopeChange() {
    configController.handleScopeChange();
  }

  function getCurrentDocId() {
    return routeWorkflow.currentDocId();
  }

  function getCurrentHash() {
    return routeWorkflow.currentHash();
  }

  function getCurrentMode() {
    return routeWorkflow.currentMode();
  }

  function hasActiveQuery(query) {
    return Boolean(normalizeSearchText(typeof query === "string" ? query : state.searchQuery));
  }

  function setRecentModeActive(active) {
    state.recentModeActive = Boolean(active);
    renderRecentButtonState();
  }

  function renderRecentButtonState() {
    if (!recentButton) return;
    recentButton.setAttribute("aria-pressed", state.recentModeActive ? "true" : "false");
  }

  function sidebarCollapseAvailable() {
    if (!window.matchMedia) return window.innerWidth > 820;
    return window.matchMedia(SIDEBAR_COLLAPSE_MEDIA).matches;
  }

  function renderIndexPanelState() {
    panelLayout.renderIndexPanelState();
  }

  function toggleIndexPanelState() {
    hideContextMenu();
    state.indexPanelState = panelLayout.toggleIndexPanelState();
  }

  function expandIndexPanelState() {
    hideContextMenu();
    state.indexPanelState = panelLayout.expandIndexPanelState();
  }

  function loadViewerConfig() {
    return configController.loadViewerConfig();
  }

  function renderBookmarkUi() {
    if (bookmarkController) {
      bookmarkController.renderUi();
      return;
    }
    renderStatusPills();
  }

  function renderBookmarkToggle() {
    if (bookmarkController) {
      bookmarkController.renderToggle();
      infoPanelController.renderToggleState();
      return;
    }
    if (bookmarkToggle) bookmarkToggle.hidden = true;
    infoPanelController.renderToggleState();
  }

  function updateInfoPanel() {
    infoPanelController.update();
  }

  function renderStatusPills() {
    if (!statusPills) return;
    var controller = managementRuntime ? managementRuntime.controller() : null;
    if (controller && typeof controller.renderStatusPills === "function") {
      controller.renderStatusPills();
      return;
    }
    statusPills.hidden = true;
    statusPills.innerHTML = "";
    state.statusMenuOpen = false;
  }

  function initializeBookmarks() {
    if (bookmarkController) bookmarkController.initialize();
  }

  function viewerUrl(docId, hash, query) {
    return routeWorkflow.viewerUrl(docId, hash, query);
  }

  function viewerUrlForScope(scope, docId, options) {
    return routeWorkflow.viewerUrlForScope(scope, docId, options);
  }

  function escapeMarkdownLinkText(value) {
    return String(value || "")
      .replace(/\\/g, "\\\\")
      .replace(/\[/g, "\\[")
      .replace(/\]/g, "\\]");
  }

  function markdownDocLink(doc) {
    if (!doc || !doc.doc_id) return "";
    var title = escapeMarkdownLinkText(doc.title || doc.doc_id);
    var url = viewerUrlForScope(viewerScope, documentIndex.viewerTargetDocId(doc.doc_id), { manage: false });
    return "[" + title + "](" + url + ")";
  }

  function buildTrail(docId) {
    return sidebarRenderer.buildTrail(docId);
  }

  function expandTrail(docId) {
    sidebarRenderer.expandTrail(docId);
  }

  function renderSidebar() {
    sidebarRenderer.renderSidebar();
  }

  function renderMeta(doc) {
    sidebarRenderer.renderMeta(doc);
  }

  function setStatus(message, isError) {
    status.textContent = message;
    status.hidden = !message;
    status.classList.toggle("is-error", Boolean(isError));
  }

  function clearResultsStatus() {
    projectDocumentShell({
      resultsStatusText: "",
      resultsStatusHidden: true,
      resultsStatusError: false
    });
  }

  function projectDocumentShell(projection) {
    panelLayout.projectDocumentShell(projection || {});
  }

  function syncBusyState() {
    var isBusy = state.pendingBusyCount > 0;
    root.classList.toggle("is-busy", isBusy);
    root.setAttribute("aria-busy", isBusy ? "true" : "false");
  }

  function startBusy() {
    state.pendingBusyCount += 1;
    syncBusyState();
    var stopped = false;
    return function stopBusy() {
      if (stopped) return;
      stopped = true;
      state.pendingBusyCount = Math.max(0, state.pendingBusyCount - 1);
      syncBusyState();
    };
  }

  function hideContextMenu() {
    var controller = managementRuntime ? managementRuntime.controller() : null;
    if (controller) {
      controller.hideContextMenu();
    }
  }

  function updateNavDragState() {
    var controller = managementRuntime ? managementRuntime.controller() : null;
    if (controller) {
      controller.updateNavDragState();
    }
  }

  function canDragCurrentDoc(doc) {
    var controller = managementRuntime ? managementRuntime.controller() : null;
    return Boolean(controller && controller.canDragCurrentDoc(doc));
  }

  function renderManagementUi() {
    var controller = managementRuntime ? managementRuntime.controller() : null;
    if (controller) {
      controller.render();
    }
  }

  function clearManagementMessageForDocChange(docId) {
    var targetDocId = String(docId || "").trim();
    if (!targetDocId || targetDocId === state.selectedDocId || !state.managementMessage) return;
    state.managementMessage = "";
    state.managementMessageIsError = false;
  }

  function initializeManagement() {
    if (!allowManagement) return;
    state.managementMode = getCurrentMode() === MANAGEMENT_MODE;
    if (!state.managementMode) return;
    loadManagementController().then(function (controller) {
      if (controller) controller.initialize();
    });
  }

  function hideDocPane() {
    documentController.hideDocPane();
    updateInfoPanel();
  }

  function showDocPane() {
    documentController.showDocPane();
  }

  function showSearchPane() {
    documentController.showSearchPane();
    updateInfoPanel();
  }

  function showRecentPane() {
    documentController.showRecentPane();
    updateInfoPanel();
  }

  function renderPayload(doc, payload, hash) {
    documentController.renderPayload(doc, payload, hash);
    updateInfoPanel();
  }

  function setHistory(docId, hash, query, mode) {
    routeWorkflow.setHistory(docId, hash, query, mode);
  }

  function cancelSearchDebounce() {
    if (state.searchDebounceId == null) return;
    window.clearTimeout(state.searchDebounceId);
    state.searchDebounceId = null;
  }

  function handleMissingDoc() {
    documentController.handleMissingDoc();
    updateInfoPanel();
  }

  function renderDocLoadingState(doc) {
    documentController.renderDocLoadingState(doc);
    updateInfoPanel();
  }

  function handlePayloadError(error) {
    documentController.handlePayloadError(error);
    updateInfoPanel();
  }

  function loadDoc(docId, options) {
    return routeWorkflow.loadDoc(docId, options);
  }

  function bindLinkInterception() {
    routeWorkflow.bindRouteLinks();

    if (sidebarToggle) {
      sidebarToggle.addEventListener("click", function () {
        toggleIndexPanelState();
      });
    }

    if (sidebarExpand) {
      sidebarExpand.addEventListener("click", function () {
        expandIndexPanelState();
      });
    }

    infoPanelController.bind();

    if (scopeSelect) {
      scopeSelect.addEventListener("change", function () {
        handleScopeChange();
      });
    }

    if (bookmarkController) {
      bookmarkController.bind();
    }

    document.addEventListener("keydown", function (event) {
      var controller = managementRuntime ? managementRuntime.controller() : null;
      if (controller && controller.handleDocumentKeydown(event)) {
        return;
      }
      if (event.key === "Escape") {
        infoPanelController.closeIfOpen();
      }
    });

    searchController.bind();
  }

  function resolveDocId() {
    return routeWorkflow.resolveDocId();
  }

  function applyCurrentRoute(options) {
    return routeWorkflow.applyCurrentRoute(options);
  }

  function loadIndex() {
    return routeWorkflow.loadIndex();
  }

  function renderRecentMode() {
    searchController.renderRecentMode();
  }

  function renderSearchPendingState() {
    searchController.renderSearchPendingState();
  }

  function renderSearchMode() {
    searchController.renderSearchMode();
  }

  routeWorkflow.bindPopstate();

  window.addEventListener("scroll", hideContextMenu, { passive: true });
  window.addEventListener("resize", function () {
    hideContextMenu();
    renderIndexPanelState();
  });
  window.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      hideContextMenu();
    }
  });

  var bookmarkRouteCallbacks = createDocsViewerBookmarkRouteCallbacks({
    cancelSearchDebounce: cancelSearchDebounce,
    routeWorkflow: routeWorkflow
  });
  bookmarkController = initDocsViewerBookmarks({
    bookmarkRow: bookmarkRow,
    bookmarkScope: function () { return bookmarkScope; },
    bookmarkToggle: bookmarkToggle,
    cssEscape: cssEscape,
    dbName: BOOKMARK_DB_NAME,
    dbVersion: BOOKMARK_DB_VERSION,
    hideContextMenu: hideContextMenu,
    renderStatusPills: renderStatusPills,
    routeCallbacks: bookmarkRouteCallbacks,
    searchBatchSize: SEARCH_BATCH_SIZE,
    searchInput: searchInput,
    setStatus: setStatus,
    state: state,
    storeName: BOOKMARK_STORE_NAME
  });
  var initialLoadPromise = startDocsViewerStartupPhases({
    composition: composition,
    bindEvents: bindLinkInterception,
    startBusy: startBusy,
    loadDocsViewerConfig: loadDocsViewerConfig,
    renderIndexPanelState: renderIndexPanelState,
    loadViewerConfig: loadViewerConfig,
    initializeBookmarks: initializeBookmarks,
    initializeManagement: initializeManagement,
    loadIndex: loadIndex,
    openImportOnLoad: function () {
      loadManagementController().then(function (controller) {
        if (controller) controller.openImportModal();
      });
    },
    getCurrentMode: getCurrentMode,
    setStatus: setStatus,
    hideDocPane: hideDocPane,
    content: content,
    results: results,
    more: more
  });

  function cssEscape(value) {
    if (window.CSS && typeof window.CSS.escape === "function") {
      return window.CSS.escape(String(value || ""));
    }
    return String(value || "").replace(/["\\]/g, "\\$&");
  }

  return {
    root: root,
    routeContext: function () { return routeContext; },
    appShellRefs: appShellRefs,
    initialLoadPromise: initialLoadPromise
  };
}
