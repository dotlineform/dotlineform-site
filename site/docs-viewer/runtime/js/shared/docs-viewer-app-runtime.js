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
  createDocsViewerTreeMoveProjection
} from "./docs-viewer-tree-move-projection.js";
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
import {
  createDocsViewerSharedControlRenderers
} from "./docs-viewer-app-control-renderers.js";
import {
  createDocsViewerControlSurfaceHost
} from "./docs-viewer-control-surface-host.js";

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
  var controlSurfaceRefs = appShellRefs.controlSurfaces || {};
  var mainViewRefs = appShellRefs.mainView;
  var infoPanelRefs = appShellRefs.infoPanel;
  var mainViewToolbar = mainViewRefs.toolbar;
  var pathEl = mainViewRefs.pathEl;
  var bookmarkRow = appShellRefs.bookmarkRow;
  var content = mainViewRefs.content;
  var scopeSelect = null;
  var searchInput = null;
  var resultsStatus = mainViewRefs.resultsStatus;
  var results = mainViewRefs.results;
  var more = mainViewRefs.more;

  var appContext = routeContext.appContext || {};
  var routeAccess = appContext.routeAccess || {};
  var featurePolicy = appContext.featurePolicy || {};
  var bookmarksEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "bookmarks");
  var configuredScopeDiscoveryEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "configured-scope-discovery");
  var managementEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "management");
  var recentEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "recent");
  var searchEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "search");
  var sourceEditingEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "source-editing");
  var allowScopeQuery = routeAccess.allowScopeQuery;
  var docsViewerConfigUrl = routeContext.docsViewerConfigUrl;
  var routeViewerBaseUrl = routeContext.routeViewerBaseUrl;
  var viewerBaseUrl = routeContext.viewerBaseUrl;
  var viewerScope = routeContext.viewerScope;
  var includeScopeParam = routeContext.includeScopeParam;
  var preserveQueryParams = routeContext.preserveQueryParams || [];
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
  var latestIndexProjection = null;
  var composition = createDocsViewerAppComposition({
    root: root,
    window: window,
    routeContext: routeContext,
    appShellRefs: appShellRefs,
    assetVersion: assetVersion,
    createCollectionProvider: settings.createCollectionProvider,
    createSourceAdapter: settings.createSourceAdapter,
    viewRegistry: settings.viewRegistry,
    viewerScope: function () { return viewerScope; },
    indexPanelAvailable: sidebarCollapseAvailable,
    onBeforePanelInteraction: hideContextMenu,
    onIndexProjection: function (projection) {
      latestIndexProjection = projection || null;
      var controller = managementRuntime ? managementRuntime.controller() : null;
      if (controller && typeof controller.handleIndexViewChange === "function") {
        controller.handleIndexViewChange(latestIndexProjection && latestIndexProjection.activeViewId);
      }
      renderAppViewerControls();
      renderIndexViewControls();
    }
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
  var searchController = null;
  var documentController = null;
  var routeWorkflow = null;
  var documentIndex = null;
  var documentViewCoordinator = null;
  var activeSourceEditorContextAdapter = null;
  var recentControlLabel = "Recent";
  var appViewerControlOwners = new Map();
  var appViewerControlHost = null;
  var appManagementControlStates = new Map();
  var appManagementControlHost = null;
  var indexViewControlStates = new Map();
  var indexViewControlHost = null;
  var mainViewControlOwners = new Map();
  var mainViewControlStates = new Map();
  var mainViewControlHost = null;

  var appSession = composition.appSession;
  var state = appSession.state;
  appViewerControlHost = createDocsViewerControlSurfaceHost({
    mount: controlSurfaceRefs.appViewer,
    registry: viewRegistry,
    renderers: Object.assign(
      {},
      createDocsViewerSharedControlRenderers(),
      settings.controlRendererContributions || {}
    ),
    surfaceId: "app-viewer",
    onDispatch: function (detail) {
      var owner = appViewerControlOwners.get(detail.controlId);
      if (typeof owner === "function") owner(detail);
    }
  });
  appViewerControlOwners.set("index-view-switch", function () {
    panelLayout.activateNextIndexView();
  });
  appManagementControlHost = createDocsViewerControlSurfaceHost({
    mount: controlSurfaceRefs.appManagement,
    registry: viewRegistry,
    renderers: settings.controlRendererContributions || {},
    surfaceId: "app-management",
    onDispatch: function (detail) {
      var controller = managementRuntime ? managementRuntime.controller() : null;
      if (controller && typeof controller.handleAppManagementControl === "function") {
        controller.handleAppManagementControl(detail);
      }
    }
  });
  indexViewControlHost = createDocsViewerControlSurfaceHost({
    mount: controlSurfaceRefs.indexView,
    registry: viewRegistry,
    renderers: Object.assign(
      {},
      createDocsViewerSharedControlRenderers(),
      settings.controlRendererContributions || {}
    ),
    surfaceId: "index-view",
    onDispatch: function (detail) {
      var controller = managementRuntime ? managementRuntime.controller() : null;
      if (controller && typeof controller.handleIndexViewControl === "function") {
        controller.handleIndexViewControl(detail);
      }
    }
  });
  mainViewControlHost = createDocsViewerControlSurfaceHost({
    mount: controlSurfaceRefs.mainView,
    registry: viewRegistry,
    renderers: Object.assign(
      {},
      createDocsViewerSharedControlRenderers(),
      settings.controlRendererContributions || {}
    ),
    surfaceId: "main-view",
    onDispatch: function (detail) {
      var owner = mainViewControlOwners.get(detail.controlId);
      if (typeof owner === "function") {
        owner(detail);
        return;
      }
      var controller = managementRuntime ? managementRuntime.controller() : null;
      if (controller && typeof controller.handleMainViewControl === "function") {
        controller.handleMainViewControl(detail);
      }
    }
  });
  mainViewControlOwners.set("bookmark", function () {
    if (bookmarkController) bookmarkController.handleControl();
  });
  mainViewControlOwners.set("info", function () {
    if (documentViewCoordinator) documentViewCoordinator.handleInfoControl();
  });
  renderAppViewerControls();
  renderAppManagementControls();
  renderIndexViewControls();
  renderMainViewControls();
  searchInput = controlSurfaceElement("appViewer", "search", "#docsViewerSearchInput");
  scopeSelect = controlSurfaceElement("appManagement", "manage-scope", "#docsViewerScopeSelect");
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
    renderIndexSelectionGutter: function (doc) {
      var controller = managementRuntime ? managementRuntime.controller() : null;
      return controller && typeof controller.renderIndexSelectionGutter === "function"
        ? controller.renderIndexSelectionGutter(doc)
        : null;
    },
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
    mount: content,
    panelLayout: panelLayout,
    panelView: appSession.domains.panelView,
    projectMainView: panelLayout.projectMainView,
    projectControlStates: function () {
      renderBookmarkControl();
      renderManagementUi();
      renderMainViewControls();
    },
    projectControlState: function (controlId, controlState) {
      projectMainViewControlState("info-panel", controlId, controlState);
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
    diagramDetailAdapter: settings.diagramDetailAdapter,
    hasActiveQuery: hasActiveQuery,
    inlineMermaidAdapter: settings.inlineMermaidAdapter,
    managementService: managementService,
    mountDocumentExtras: settings.mountDocumentExtras,
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
    preserveQueryParams: function () { return preserveQueryParams; },
    more: more,
    onIndexReplaced: function (replacement) {
      var controller = managementRuntime ? managementRuntime.controller() : null;
      if (!controller || typeof controller.reconcileIndexSelectionReload !== "function") return;
      var docs = replacement && Array.isArray(replacement.docs) ? replacement.docs : [];
      controller.reconcileIndexSelectionReload(docs.map(function (doc) {
        return doc && doc.doc_id;
      }));
    },
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
  searchController = searchEnabled || recentEnabled ? initDocsViewerSearchController({
    clearSearchInput: function () {
      if (searchInput) searchInput.value = "";
    },
    collectionProvider: collectionProvider,
    hideContextMenu: hideContextMenu,
    hasActiveQuery: hasActiveQuery,
    documentIndex: appSession.domains.documentIndex,
    more: more,
    paneCommands: searchPaneCommands,
    resultsStatus: resultsStatus,
    results: results,
    routeCommands: searchRouteCommands,
    searchBatchSize: SEARCH_BATCH_SIZE,
    searchDebounceMs: SEARCH_DEBOUNCE_MS,
    searchEnabled: searchEnabled,
    searchRecent: appSession.domains.searchRecent,
    recentEnabled: recentEnabled,
    recentBasis: routeContext.recentBasis,
    selectedDocument: appSession.domains.selectedDocument,
    setRecentModeActive: setRecentModeActive,
    setStatus: statusController.setStatus,
    startBusy: statusController.startBusy
  }) : null;
  appViewerControlOwners.set("recent", function () {
    if (searchController) searchController.handleRecentControl();
  });
  appViewerControlOwners.set("search", function (detail) {
    if (searchController && detail.eventType === "input") {
      searchController.handleSearchInput(detail.event && detail.event.target ? detail.event.target.value : "");
    }
  });
  var configController = initDocsViewerConfigController({
    allowScopeQuery: allowScopeQuery,
    configService: composition.configService,
    featurePolicy: featurePolicy,
    defaultRecentLimit: DEFAULT_RECENT_LIMIT,
    documentIndex: appSession.domains.documentIndex,
    managementController: function () {
      return managementRuntime ? managementRuntime.controller() : null;
    },
    setRecentControlLabel: function (label) {
      recentControlLabel = String(label || "Recent");
      renderAppViewerControls();
    },
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

  var treeMoveProjection = managementEnabled ? createDocsViewerTreeMoveProjection({
    documentIndex: documentIndex,
    documentIndexState: appSession.domains.documentIndex,
    renderMeta: renderMeta,
    selectedDocument: appSession.domains.selectedDocument,
    sidebar: sidebarRenderer,
    updateInfoPanel: documentViewCoordinator.updateInfoPanel
  }) : null;

  managementRuntime = managementEnabled ? createDocsViewerManagementRuntimeAdapter({
    managementUi: managementUiEnabled,
    appShellReady: appShellReady,
    constants: {
      MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS: MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS,
      MANAGEMENT_CAPABILITY_RETRY_DELAY_MS: MANAGEMENT_CAPABILITY_RETRY_DELAY_MS,
      SEARCH_BATCH_SIZE: SEARCH_BATCH_SIZE
    },
    context: {
      activeIndexViewId: function () {
        return latestIndexProjection && latestIndexProjection.activeViewId
          ? latestIndexProjection.activeViewId
          : panelLayout.projectViewState().index.activeViewId;
      },
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
      projectAppManagementControlState: projectAppManagementControlState,
      projectIndexViewControlState: projectIndexViewControlState,
      projectMainViewControlState: function (controlId, controlState) {
        projectMainViewControlState("management", controlId, controlState);
      },
      projectCommittedMove: treeMoveProjection.project,
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
    preserveQueryParams = routeContext.preserveQueryParams || preserveQueryParams;
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

  function getCurrentHash() {
    return routeWorkflow.currentHash();
  }

  function hasActiveQuery(query) {
    if (!searchEnabled) return false;
    var searchRecent = appSession.domains.searchRecent;
    return Boolean(normalizeSearchText(typeof query === "string" ? query : searchRecent.searchQuery));
  }

  function setRecentModeActive(active) {
    var nextActive = Boolean(active);
    if (appSession.domains.searchRecent.recentModeActive === nextActive) return;
    appSession.domains.searchRecent.recentModeActive = nextActive;
    renderAppViewerControls();
  }

  function controlSurfaceElement(surfaceKey, controlId, selector) {
    var mount = controlSurfaceRefs[surfaceKey] || null;
    if (!mount) return null;
    var controlRoot = Array.from(mount.children).find(function (child) {
      return child.dataset && child.dataset.docsViewerControl === controlId;
    }) || null;
    return controlRoot && selector ? controlRoot.querySelector(selector) : controlRoot;
  }

  function renderAppViewerControls() {
    if (!appViewerControlHost) return [];
    return appViewerControlHost.render({
      controlStateById: {
        "recent": {
          label: recentControlLabel,
          pressed: appSession.domains.searchRecent.recentModeActive
        },
        "search": { label: "Search docs" },
        "index-view-switch": panelLayout.indexViewSwitchControlState()
      }
    });
  }

  function projectAppManagementControlState(controlId, controlState) {
    var id = String(controlId || "").trim();
    if (!id) return;
    appManagementControlStates.set(id, controlState || {});
    renderAppManagementControls();
  }

  function renderAppManagementControls() {
    if (!appManagementControlHost) return [];
    var controlStateById = {};
    viewRegistry.listControls({ surfaceId: "app-management" }).forEach(function (control) {
      controlStateById[control.id] = appManagementControlStates.has(control.id)
        ? appManagementControlStates.get(control.id)
        : { hidden: true };
    });
    return appManagementControlHost.render({ controlStateById: controlStateById });
  }

  function projectIndexViewControlState(controlId, controlState) {
    var id = String(controlId || "").trim();
    if (!id) return;
    indexViewControlStates.set(id, controlState || {});
    renderIndexViewControls();
  }

  function renderIndexViewControls() {
    if (!indexViewControlHost) return [];
    var activeViewId = latestIndexProjection && latestIndexProjection.activeViewId
      ? latestIndexProjection.activeViewId
      : panelLayout.projectViewState().index.activeViewId;
    var controlStateById = {};
    viewRegistry.listControls({ surfaceId: "index-view" }).forEach(function (control) {
      controlStateById[control.id] = indexViewControlStates.has(control.id)
        ? indexViewControlStates.get(control.id)
        : { hidden: true };
    });
    return indexViewControlHost.render({
      activeViewId: activeViewId,
      controlStateById: controlStateById
    });
  }

  function projectMainViewControlState(ownerId, controlId, controlState) {
    var owner = String(ownerId || "").trim();
    var id = String(controlId || "").trim();
    if (!owner || !id) return;
    var statesByOwner = mainViewControlStates.get(id) || new Map();
    statesByOwner.set(owner, controlState || {});
    mainViewControlStates.set(id, statesByOwner);
    renderMainViewControls();
  }

  function mergedMainViewControlState(controlId) {
    var statesByOwner = mainViewControlStates.get(controlId);
    if (!statesByOwner || !statesByOwner.size) return { hidden: true };
    var merged = {};
    statesByOwner.forEach(function (state) {
      var current = state || {};
      ["hidden", "disabled", "busy"].forEach(function (key) {
        if (Object.prototype.hasOwnProperty.call(current, key)) {
          merged[key] = Boolean(merged[key]) || Boolean(current[key]);
        }
      });
      ["pressed", "expanded", "label", "count"].forEach(function (key) {
        if (Object.prototype.hasOwnProperty.call(current, key)) merged[key] = current[key];
      });
    });
    return merged;
  }

  function renderMainViewControls() {
    if (!mainViewControlHost) return [];
    var activeState = documentViewCoordinator ? documentViewCoordinator.activeViewState() : {
      activeViewId: "rendered-document",
      activeModeId: "rendered-document"
    };
    var controlStateById = {};
    viewRegistry.listControls({ surfaceId: "main-view" }).forEach(function (control) {
      controlStateById[control.id] = mergedMainViewControlState(control.id);
    });
    return mainViewControlHost.render({
      activeViewId: activeState.activeViewId,
      activeModeId: activeState.activeModeId,
      controlStateById: controlStateById
    });
  }

  function sidebarCollapseAvailable() {
    if (!window.matchMedia) return window.innerWidth > 820;
    return window.matchMedia(SIDEBAR_COLLAPSE_MEDIA).matches;
  }

  function renderIndexPanelState() {
    panelLayout.renderIndexPanelState();
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
      projectMainViewControlState: function (controlId, controlState) {
        projectMainViewControlState("source-editor", controlId, controlState);
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
    projectMainViewControlState("bookmarks", "bookmark", { hidden: true });
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
    panelLayout.bindPanelChrome();

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
      controlActive: documentViewCoordinator.controlActive,
      cssEscape: cssEscape,
      dbName: BOOKMARK_DB_NAME,
      dbVersion: BOOKMARK_DB_VERSION,
      documentIndex: appSession.domains.documentIndex,
      hideContextMenu: hideContextMenu,
      routeCommands: bookmarkRouteCommands,
      projectControlState: function (controlId, controlState) {
        projectMainViewControlState("bookmarks", controlId, controlState);
      },
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
