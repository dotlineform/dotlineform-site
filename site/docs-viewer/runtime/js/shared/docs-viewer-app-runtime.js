import {
  normalizeSearchText
} from "./docs-viewer-search.js";
import {
  createDocsViewerBookmarkRouteCommands,
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
  createDocsViewerSearchRouteCommands,
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
  createDocsViewerDocumentViewCoordinator
} from "./docs-viewer-document-view-coordinator.js";
import {
  createDocsViewerManagementRuntimeAdapter
} from "./docs-viewer-runtime-lazy-controller.js";
import {
  DOCS_VIEWER_RUNTIME_DEFAULTS,
  createDocsViewerAppComposition,
  startDocsViewerStartupPhases
} from "./docs-viewer-app-composition.js";
import {
  docsViewerRouteFeatureEnabled
} from "./docs-viewer-route-features.js";
import {
  createDocsViewerStatusController
} from "./docs-viewer-status-controller.js";

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
  var viewerToolbarRefs = appShellRefs.viewerToolbar || {};
  var indexViewToggle = viewerToolbarRefs.indexViewToggle;
  var sidebarToggle = indexPanelRefs.sidebarToggle;
  var sidebarExpand = indexPanelRefs.sidebarExpand;
  var mainViewRefs = appShellRefs.mainView;
  var infoPanelRefs = appShellRefs.infoPanel;
  var mainViewToolbar = mainViewRefs.toolbar;
  var pathEl = mainViewRefs.pathEl;
  var bookmarkRow = appShellRefs.bookmarkRow;
  var infoToggle = mainViewRefs.infoToggle;
  var bookmarkToggle = mainViewRefs.bookmarkToggle;
  var content = mainViewRefs.content;
  var scopeSelect = appShellRefs.headerControls.scopeSelect;
  var recentButton = appShellRefs.headerControls.recentButton;
  var searchInput = appShellRefs.headerControls.searchInput;
  var resultsStatus = mainViewRefs.resultsStatus;
  var results = mainViewRefs.results;
  var more = mainViewRefs.more;

  var appContext = routeContext.appContext || {};
  var routeAccess = appContext.routeAccess || {};
  var featurePolicy = appContext.featurePolicy || {};
  var bookmarksEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "bookmarks");
  var configuredScopeDiscoveryEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "configured-scope-discovery");
  var managementEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "management");
  var recentlyAddedEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "recently-added");
  var reportsEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "reports");
  var searchEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "search");
  var sourceEditingEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "source-editing");
  var allowScopeQuery = routeAccess.allowScopeQuery;
  var docsViewerConfigUrl = routeContext.docsViewerConfigUrl;
  var routeViewerBaseUrl = routeContext.routeViewerBaseUrl;
  var viewerBaseUrl = routeContext.viewerBaseUrl;
  var viewerScope = routeContext.viewerScope;
  var includeScopeParam = routeContext.includeScopeParam;
  var defaultRouteDocId = routeContext.defaultRouteDocId;
  var viewerPathname = routeContext.viewerPathname;
  var runtimeDefaults = DOCS_VIEWER_RUNTIME_DEFAULTS;
  var SEARCH_BATCH_SIZE = runtimeDefaults.searchBatchSize;
  var SEARCH_DEBOUNCE_MS = runtimeDefaults.searchDebounceMs;
  var DEFAULT_RECENT_LIMIT = runtimeDefaults.defaultRecentLimit;
  var BOOKMARK_DB_NAME = runtimeDefaults.bookmarkDbName;
  var BOOKMARK_DB_VERSION = runtimeDefaults.bookmarkDbVersion;
  var BOOKMARK_STORE_NAME = runtimeDefaults.bookmarkStoreName;
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
    createSourceAdapter: settings.createSourceAdapter,
    viewRegistry: settings.viewRegistry,
    viewerScope: function () { return viewerScope; },
    indexPanelAvailable: sidebarCollapseAvailable
  });
  var viewRegistry = composition.viewRegistry;
  var serviceContext = composition.serviceContext;
  var managementService = serviceContext.management;
  var sourceService = serviceContext.source;
  var managementUiEnabled = Boolean(managementEnabled && routeAccess.managementUi && managementService);
  var managementBaseUrl = managementService ? managementService.baseUrl : "";
  var panelLayout = composition.panelLayout;
  var managementRuntime = null;
  var bookmarkController = null;
  var documentController = null;
  var routeWorkflow = null;
  var documentIndex = null;
  var documentViewCoordinator = null;
  var activeSourceEditorContextAdapter = null;

  var appSession = composition.appSession;
  var state = appSession.state;
  documentIndex = composition.documentIndex;
  var generatedDataRuntime = composition.generatedDataRuntime;
  var collectionProvider = composition.collectionProvider;
  var checkGeneratedDataReadCapability = generatedDataRuntime.checkGeneratedDataReadCapability;
  var statusController = createDocsViewerStatusController({
    root: root,
    state: appSession.domains.busyStatus,
    status: appShellRefs.status
  });
  var sidebarRenderer = initDocsViewerSidebarRenderer({
    canDragCurrentDoc: canDragCurrentDoc,
    documentIndex: appSession.domains.documentIndex,
    toolbar: mainViewToolbar,
    nav: nav,
    pathEl: pathEl,
    renderBookmarkToggle: renderBookmarkToggle,
    scopeConfig: appSession.domains.scopeConfig,
    selectedDocument: appSession.domains.selectedDocument,
    statusForIndexDoc: documentIndex.statusForIndexDoc,
    updateNavDragState: updateNavDragState,
    viewerTargetDocId: documentIndex.viewerTargetDocId,
    viewerUrl: viewerUrl
  });
  documentViewCoordinator = createDocsViewerDocumentViewCoordinator({
    appContext: function () { return appContext; },
    buildTrail: buildTrail,
    collectionProvider: collectionProvider,
    documentIndex: appSession.domains.documentIndex,
    infoPanelDefaultViewByDocumentMode: settings.infoPanelDefaultViewByDocumentMode,
    infoPanelRefs: infoPanelRefs,
    infoToggle: infoToggle,
    mount: content,
    panelLayout: panelLayout,
    panelView: appSession.domains.panelView,
    projectMainView: panelLayout.projectMainView,
    renderDocumentControls: function () {
      renderBookmarkControl();
      renderManagementUi();
    },
    root: root,
    scopeConfig: appSession.domains.scopeConfig,
    selectedDocument: appSession.domains.selectedDocument,
    sourceEditorServices: function () {
      return sourceEditingEnabled && sourceService ? sourceEditorServices() : null;
    },
    showWarning: statusController.setStatus,
    viewRegistry: viewRegistry,
    viewerScope: function () { return viewerScope; },
    viewerTargetDocId: documentIndex.viewerTargetDocId,
    viewerUrl: viewerUrl
  });
  documentController = initDocsViewerDocumentController({
    appContext: appContext,
    checkGeneratedDataReadCapability: checkGeneratedDataReadCapability,
    clearResultsStatus: clearResultsStatus,
    content: content,
    collectionProvider: collectionProvider,
    hasActiveQuery: hasActiveQuery,
    managementService: managementService,
    mountDocumentExtras: reportsEnabled ? settings.mountDocumentExtras : null,
    more: more,
    projectDocumentShell: panelLayout.projectMainView,
    renderBookmarkToggle: renderBookmarkToggle,
    renderBookmarkUi: renderBookmarkUi,
    renderManagementUi: renderManagementUi,
    renderMeta: renderMeta,
    renderSearchMode: renderSearchMode,
    renderSidebar: renderSidebar,
    results: results,
    routeContext: function () { return routeContext; },
    routeSession: appSession.domains.routeSession,
    scopeConfig: appSession.domains.scopeConfig,
    selectedDocument: appSession.domains.selectedDocument,
    setRecentModeActive: setRecentModeActive,
    statusCommands: {
      setStatus: statusController.setStatus
    },
    toolbar: mainViewToolbar,
    viewerScope: function () { return viewerScope; },
    viewerUrlForScope: viewerUrlForScope
  });
  routeWorkflow = initDocsViewerRouteWorkflow({
    managementUiEnabled: function () { return managementUiEnabled; },
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
    collectionProvider: collectionProvider,
    includeScopeParam: function () { return includeScopeParam; },
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
    searchBatchSize: SEARCH_BATCH_SIZE,
    searchInput: searchInput,
    setRecentModeActive: setRecentModeActive,
    routeSession: appSession.domains.routeSession,
    scopeConfig: appSession.domains.scopeConfig,
    documentIndex: appSession.domains.documentIndex,
    selectedDocument: appSession.domains.selectedDocument,
    searchRecent: appSession.domains.searchRecent,
    statusCommands: {
      setStatus: statusController.setStatus,
      startBusy: statusController.startBusy
    },
    syncNonViewableVisibilityForRequestedDoc: function () {
      documentIndex.syncNonViewableVisibilityForRequestedDoc(getCurrentDocId);
    },
    updateInfoPanel: documentViewCoordinator.updateInfoPanel,
    viewerBaseUrl: function () { return viewerBaseUrl; },
    viewerPathname: function () { return viewerPathname; },
    viewerScope: function () { return viewerScope; },
    window: window
  });
  var routeWorkflowCommands = routeWorkflow.commands;
  var searchRouteCommands = createDocsViewerSearchRouteCommands({
    defaultDocId: documentIndex.defaultDocId,
    routeCommands: routeWorkflowCommands,
    viewerTargetDocId: documentIndex.viewerTargetDocId
  });
  var searchPaneCommands = {
    hideDocPane: hideDocPane,
    showRecentPane: showRecentPane,
    showSearchPane: showSearchPane
  };
  var searchController = searchEnabled || recentlyAddedEnabled ? initDocsViewerSearchController({
    collectionProvider: collectionProvider,
    hideContextMenu: hideContextMenu,
    hasActiveQuery: hasActiveQuery,
    documentIndex: appSession.domains.documentIndex,
    more: more,
    paneCommands: searchPaneCommands,
    recentButton: recentButton,
    resultsStatus: resultsStatus,
    results: results,
    routeCommands: searchRouteCommands,
    searchBatchSize: SEARCH_BATCH_SIZE,
    searchDebounceMs: SEARCH_DEBOUNCE_MS,
    searchEnabled: searchEnabled,
    searchRecent: appSession.domains.searchRecent,
    recentlyAddedEnabled: recentlyAddedEnabled,
    searchInput: searchInput,
    selectedDocument: appSession.domains.selectedDocument,
    setRecentModeActive: setRecentModeActive,
    setStatus: statusController.setStatus,
    startBusy: statusController.startBusy
  }) : null;
  var configController = initDocsViewerConfigController({
    allowScopeQuery: allowScopeQuery,
    configService: composition.configService,
    featurePolicy: featurePolicy,
    defaultRecentLimit: DEFAULT_RECENT_LIMIT,
    documentIndex: appSession.domains.documentIndex,
    managementController: function () {
      return managementRuntime ? managementRuntime.controller() : null;
    },
    recentButton: recentButton,
    renderRecentMode: renderRecentMode,
    renderSidebar: renderSidebar,
    root: root,
    routeCommands: {
      applyRouteGlobals: applyRouteGlobals
    },
    routeViewerBaseUrl: routeViewerBaseUrl,
    routeSession: appSession.domains.routeSession,
    scopeSelect: scopeSelect,
    scopeConfig: appSession.domains.scopeConfig,
    searchRecent: appSession.domains.searchRecent,
    uiStatusEmojiMaxLength: UI_STATUS_EMOJI_MAX_LENGTH,
    viewerBaseUrl: function () { return viewerBaseUrl; },
    viewerScope: function () { return viewerScope; }
  });

  managementRuntime = managementEnabled ? createDocsViewerManagementRuntimeAdapter({
    managementUi: managementUiEnabled,
    appShellReady: appShellReady,
    constants: {
      MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS: MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS,
      MANAGEMENT_CAPABILITY_RETRY_DELAY_MS: MANAGEMENT_CAPABILITY_RETRY_DELAY_MS,
      SEARCH_BATCH_SIZE: SEARCH_BATCH_SIZE
    },
    context: {
      applyDocVisibility: documentIndex.applyDocVisibility,
      cancelSearchDebounce: cancelSearchDebounce,
      cssEscape: cssEscape,
      currentViewerConfig: function () { return appSession.domains.scopeConfig.viewerConfig || {}; },
      defaultDocId: documentIndex.defaultDocId,
      defaultRouteDocId: function () { return defaultRouteDocId; },
      docsViewerConfigUrl: docsViewerConfigUrl,
      escapeHtml: escapeHtml,
      findAllDocById: documentIndex.findAllDocById,
      formatText: formatText,
      getConfigText: getConfigText,
      getConfigValue: getConfigValue,
      isManagementContext: function () { return routeWorkflow.managementUiEnabled(); },
      serviceClient: {
        docsViewerConfigUrl: docsViewerConfigUrl,
        managementBaseUrl: managementBaseUrl
      },
      managementState: {
        domains: {
          documentIndex: appSession.domains.documentIndex,
          management: appSession.domains.management,
          routeSession: appSession.domains.routeSession,
          scopeConfig: appSession.domains.scopeConfig,
          searchRecent: appSession.domains.searchRecent,
          selectedDocument: appSession.domains.selectedDocument
        }
      },
      managementShellRefs: appShellRefs.managementShell || {},
      viewRegistry: viewRegistry,
      activeViewState: documentViewCoordinator.activeViewState,
      nav: nav,
      renderBookmarkUi: renderBookmarkUi,
      renderRecentMode: renderRecentMode,
      renderSearchMode: renderSearchMode,
      renderSidebar: renderSidebar,
      root: root,
      routeReload: {
        reloadViewerConfiguration: function () { return configController.reloadViewerConfiguration(); },
        routeCommands: routeWorkflowCommands
      },
      searchInput: searchInput,
      setStatus: statusController.setStatus,
      requestMainView: documentViewCoordinator.requestMainView,
      requestDocumentMode: documentViewCoordinator.requestDocumentMode,
      markdownDocLink: markdownDocLink,
      viewerScope: function () { return viewerScope; }
    },
    logger: window.console || console,
    onLoaded: function () {
      renderSidebar();
    }
  }) : null;

  function loadManagementController() {
    return managementRuntime ? managementRuntime.load() : Promise.resolve(null);
  }

  function routeScopeFromUrl() {
    if (!configuredScopeDiscoveryEnabled) return viewerScope;
    return configController.routeScopeFromUrl();
  }

  function applyRouteGlobals(values) {
    routeContext = updateDocsViewerRouteContext(routeContext, values, { window: window });
    appSession.domains.routeSession.updateRouteContext(routeContext);
    viewerScope = routeContext.viewerScope;
    defaultRouteDocId = routeContext.defaultRouteDocId;
    viewerBaseUrl = routeContext.viewerBaseUrl;
    includeScopeParam = routeContext.includeScopeParam;
    viewerPathname = routeContext.viewerPathname;
    bookmarkScope = routeContext.bookmarkScope;
    state.indexPanelState = panelLayout.setStorageScope(bookmarkScope);
  }

  function loadConfiguredScopes() {
    return configController.loadConfiguredScopes();
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

  function hasActiveQuery(query) {
    if (!searchEnabled) return false;
    var searchRecent = appSession.domains.searchRecent;
    return Boolean(normalizeSearchText(typeof query === "string" ? query : searchRecent.searchQuery));
  }

  function setRecentModeActive(active) {
    appSession.domains.searchRecent.recentModeActive = Boolean(active);
    renderRecentButtonState();
  }

  function renderRecentButtonState() {
    if (!recentButton) return;
    recentButton.setAttribute("aria-pressed", appSession.domains.searchRecent.recentModeActive ? "true" : "false");
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

  function setActiveIndexView(viewId) {
    hideContextMenu();
    panelLayout.setActiveIndexView(viewId);
    state.indexPanelState = panelLayout.indexPanelState();
    state.viewState = panelLayout.projectViewState();
  }

  function loadViewerSettings() {
    return configController.loadViewerSettings();
  }

  function reloadGeneratedDoc(targetDocId) {
    var selectedDocument = appSession.domains.selectedDocument;
    var searchRecent = appSession.domains.searchRecent;
    selectedDocument.payloadCache.clear();
    searchRecent.searchEntries = [];
    searchRecent.searchLoaded = false;
    searchRecent.searchRequestPromise = null;
    selectedDocument.reloadNonce = String(Date.now());
    selectedDocument.reloadExpectedDocId = String(targetDocId || "").trim();
    searchRecent.searchQuery = "";
    searchRecent.searchVisibleCount = SEARCH_BATCH_SIZE;
    searchRecent.searchRouteActive = false;
    cancelSearchDebounce();
    if (searchInput) searchInput.value = "";
    if (routeWorkflowCommands && typeof routeWorkflowCommands.setHistory === "function" && targetDocId) {
      routeWorkflowCommands.setHistory(targetDocId, "", "", "replace");
    }
    if (routeWorkflowCommands && typeof routeWorkflowCommands.loadIndex === "function") {
      return routeWorkflowCommands.loadIndex();
    }
    return Promise.resolve(null);
  }

  function sourceEditorServices() {
    return {
      reloadRenderedDoc: function (docId) {
        return reloadGeneratedDoc(docId);
      },
      clearActiveSourceEditorContextAdapter: function (adapter) {
        if (!adapter || activeSourceEditorContextAdapter === adapter) {
          activeSourceEditorContextAdapter = null;
        }
        var activeViewId = documentViewCoordinator ? documentViewCoordinator.activeInfoViewId() : "";
        if (documentViewCoordinator && documentViewCoordinator.isConfiguredInfoView(activeViewId)) {
          documentViewCoordinator.openInfoView("metadata-info");
        } else if (documentViewCoordinator) {
          documentViewCoordinator.renderInfoToggle();
        }
      },
      getActiveSourceEditorContextAdapter: function () {
        return activeSourceEditorContextAdapter;
      },
      setActiveSourceEditorContextAdapter: function (adapter) {
        activeSourceEditorContextAdapter = adapter || null;
        if (documentViewCoordinator) documentViewCoordinator.renderInfoToggle();
      },
      setStatus: statusController.setStatus,
      startBusy: statusController.startBusy
    };
  }

  function renderBookmarkUi() {
    if (bookmarkController) {
      bookmarkController.renderUi();
      return;
    }
  }

  function renderBookmarkToggle() {
    renderBookmarkControl();
    if (documentViewCoordinator) documentViewCoordinator.renderInfoToggle();
  }

  function renderBookmarkControl() {
    if (bookmarkController) {
      bookmarkController.renderToggle();
      return;
    }
    if (bookmarkToggle) bookmarkToggle.hidden = true;
  }

  function initializeBookmarks() {
    if (bookmarkController) bookmarkController.initialize();
  }

  function viewerUrl(docId, hash, query) {
    return routeWorkflowCommands.viewerUrl(docId, hash, query);
  }

  function viewerUrlForScope(scope, docId, options) {
    return routeWorkflowCommands.viewerUrlForScope(scope, docId, options);
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

  function clearResultsStatus() {
    panelLayout.projectMainView({
      resultsStatusText: "",
      resultsStatusHidden: true,
      resultsStatusError: false
    });
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
    if (!managementUiEnabled) return;
    state.managementContext = routeWorkflow.managementUiEnabled();
    if (!state.managementContext) return;
    loadManagementController().then(function (controller) {
      if (controller) controller.initialize();
    });
  }

  function hideDocPane() {
    documentViewCoordinator.showRenderedDocument(documentController.hideDocPane);
    documentViewCoordinator.updateInfoPanel();
  }

  function showDocPane() {
    documentViewCoordinator.showRenderedDocument(documentController.showDocPane);
  }

  function showSearchPane() {
    documentViewCoordinator.showView("search-results", documentController.showSearchPane);
    documentViewCoordinator.updateInfoPanel();
  }

  function showRecentPane() {
    documentViewCoordinator.showView("recent-results", documentController.showRecentPane);
    documentViewCoordinator.updateInfoPanel();
  }

  function renderPayload(doc, payload, hash) {
    documentViewCoordinator.showRenderedDocument(function () {
      documentController.renderPayload(doc, payload, hash);
      documentViewCoordinator.updateInfoPanel();
    });
  }

  function cancelSearchDebounce() {
    var searchRecent = appSession.domains.searchRecent;
    if (searchRecent.searchDebounceId == null) return;
    window.clearTimeout(searchRecent.searchDebounceId);
    searchRecent.searchDebounceId = null;
  }

  function handleMissingDoc() {
    documentViewCoordinator.showRenderedDocument(function () {
      documentController.handleMissingDoc();
      documentViewCoordinator.updateInfoPanel();
    });
  }

  function renderDocLoadingState(doc) {
    documentViewCoordinator.showRenderedDocument(function () {
      documentController.renderDocLoadingState(doc);
      documentViewCoordinator.updateInfoPanel();
    });
  }

  function handlePayloadError(error) {
    documentViewCoordinator.showRenderedDocument(function () {
      documentController.handlePayloadError(error);
      documentViewCoordinator.updateInfoPanel();
    });
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

    if (indexViewToggle) {
      indexViewToggle.addEventListener("click", function () {
        setActiveIndexView(indexViewToggle.dataset.indexPanelView);
      });
    }

    documentViewCoordinator.bind();

    if (featurePolicy.scopeSelection && scopeSelect) {
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
        documentViewCoordinator.closeInfoIfOpen();
      }
    });

    if (searchController) searchController.bind();
  }

  function renderRecentMode() {
    if (searchController) searchController.renderRecentMode();
  }

  function renderSearchPendingState() {
    if (searchController) searchController.renderSearchPendingState();
  }

  function renderSearchMode() {
    if (searchController) searchController.renderSearchMode();
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

  if (bookmarksEnabled) {
    var bookmarkRouteCommands = createDocsViewerBookmarkRouteCommands({
      routeCommands: routeWorkflowCommands
    });
    var bookmarkSearchResetCommand = {
      resetForBookmarkOpen: function () {
        cancelSearchDebounce();
        appSession.domains.searchRecent.searchQuery = "";
        appSession.domains.searchRecent.searchVisibleCount = SEARCH_BATCH_SIZE;
        if (searchInput) searchInput.value = "";
      }
    };
    bookmarkController = initDocsViewerBookmarks({
      bookmarks: appSession.domains.bookmarks,
      bookmarkRow: bookmarkRow,
      bookmarkScope: function () { return bookmarkScope; },
      bookmarkToggle: bookmarkToggle,
      controlActive: documentViewCoordinator.controlActive,
      cssEscape: cssEscape,
      dbName: BOOKMARK_DB_NAME,
      dbVersion: BOOKMARK_DB_VERSION,
      documentIndex: appSession.domains.documentIndex,
      hideContextMenu: hideContextMenu,
      routeCommands: bookmarkRouteCommands,
      searchRecent: appSession.domains.searchRecent,
      searchResetCommand: bookmarkSearchResetCommand,
      selectedDocument: appSession.domains.selectedDocument,
      setStatus: statusController.setStatus,
      storeName: BOOKMARK_STORE_NAME
    });
  }
  var initialLoadPromise = startDocsViewerStartupPhases({
    composition: composition,
    bindEvents: bindLinkInterception,
    startBusy: statusController.startBusy,
    loadConfiguredScopes: loadConfiguredScopes,
    renderIndexPanelState: renderIndexPanelState,
    loadViewerSettings: loadViewerSettings,
    initializeBookmarks: initializeBookmarks,
    initializeManagement: initializeManagement,
    loadIndex: routeWorkflowCommands.loadIndex,
    openImportOnLoad: function () {
      loadManagementController().then(function (controller) {
        if (controller) controller.openImportModal();
      });
    },
    setStatus: statusController.setStatus,
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
