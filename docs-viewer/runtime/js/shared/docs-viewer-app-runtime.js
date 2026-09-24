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
  var contentDetailBackControlId = String(settings.contentDetailBackControlId || "").trim();
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
  var bookmarkRow = appShellRefs.bookmarkRow;
  var content = mainViewRefs.content;
  var searchInput = null;
  var resultsStatus = mainViewRefs.resultsStatus;
  var results = mainViewRefs.results;
  var more = mainViewRefs.more;

  var appContext = routeContext.appContext || {};
  var routeAccess = appContext.routeAccess || {};
  var featurePolicy = appContext.featurePolicy || {};
  var bookmarksEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "bookmarks");
  var workspaceConfigurationEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "workspace-configuration");
  var managementEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "management");
  var recentEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "recent");
  var searchEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "search");
  var sourceEditingEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "source-editing");
  var docsViewerConfigUrl = routeContext.docsViewerConfigUrl;
  var routeViewerBaseUrl = routeContext.routeViewerBaseUrl;
  var viewerBaseUrl = routeContext.viewerBaseUrl;
  var viewerStage = routeContext.viewerStage || "";
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
  var SIDEBAR_COLLAPSE_MEDIA = runtimeDefaults.sidebarCollapseMedia;
  var bookmarkOwner = routeContext.bookmarkOwner;
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
    viewerStage: function () { return viewerStage; },
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
  var activeSourceEditorInfoUnsubscribe = null;
  var sourceEditorInfoRequest = 0;
  var sourceEditorInfoViewId = "metadata-info";
  var recentControlLabel = "Recent";
  var latestCollectionReportGeneration = 0;
  var latestCollectionReportState = {
    state: "inactive",
    reason: "startup",
    parentTarget: null,
    collectionTarget: null,
    collectionLabel: "",
    documentTarget: null,
    documentRecord: null,
    documentInfo: null,
    refreshDocument: null,
    refreshCollection: null
  };
  var appViewerControlOwners = new Map();
  var appViewerControlHost = null;
  var appManagementControlStates = new Map();
  var appManagementControlHost = null;
  var indexViewControlStates = new Map();
  var indexViewControlHost = null;
  var mainViewControlOwners = new Map();
  var mainViewControlStates = new Map();
  var mainViewControlHost = null;

  function publishCollectionReportState(value) {
    var generation = Number(value && value.documentMountGeneration);
    if (Number.isInteger(generation) && generation > 0) {
      if (generation < latestCollectionReportGeneration) return;
      latestCollectionReportGeneration = generation;
    }
    latestCollectionReportState = value && typeof value === "object"
      ? Object.assign({}, value)
      : {
          state: "inactive",
          reason: "invalid-report-state",
          parentTarget: null,
          collectionTarget: null,
          collectionLabel: "",
          documentTarget: null,
          documentRecord: null,
          documentInfo: null,
          refreshDocument: null,
          refreshCollection: null
        };
    var controller = managementRuntime ? managementRuntime.controller() : null;
    if (controller && typeof controller.publishCollectionReportState === "function") {
      controller.publishCollectionReportState(latestCollectionReportState);
    }
    if (documentViewCoordinator) documentViewCoordinator.updateInfoPanel();
    renderMainViewControls();
  }

  function documentActionContext() {
    if (latestCollectionReportState.parentTarget) return latestCollectionReportState;
    var displayed = appSession.domains.selectedDocument;
    var doc = displayed.selectedDocId === displayed.displayedDocId && displayed.displayedPayload
      && displayed.displayedPayload.doc_id === displayed.displayedDocId
      ? appSession.domains.documentIndex.docsById.get(displayed.displayedDocId) : null;
    return {
      documentTarget: doc ? { ...(viewerStage ? { stage: viewerStage } : {}), doc_id: doc.doc_id } : null,
      documentRecord: doc || null
    };
  }

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
  mainViewControlOwners.set("document-links", function (detail) {
    if (documentController) documentController.openLinks(detail);
  });
  mainViewControlOwners.set("info", function () {
    if (!documentViewCoordinator) return;
    if (
      activeSourceEditorContextAdapter
      && !documentViewCoordinator.isInfoOpen()
      && sourceEditorInfoViewId
    ) {
      documentViewCoordinator.openInfoView(sourceEditorInfoViewId);
      return;
    }
    documentViewCoordinator.handleInfoControl();
  });
  if (contentDetailBackControlId) {
    mainViewControlOwners.set(contentDetailBackControlId, function () {
      if (!documentViewCoordinator) return;
      documentViewCoordinator.requestMainView("rendered-document", {
        reason: "back",
        warn: false
      });
    });
  }
  if (mainViewRefs.collectionBack) {
    mainViewRefs.collectionBack.addEventListener("click", function () {
      if (mainViewRefs.collectionBack.hidden || mainViewRefs.collectionBack.disabled) return;
      if (typeof latestCollectionReportState.returnToList === "function") latestCollectionReportState.returnToList();
    });
  }
  renderAppViewerControls();
  renderAppManagementControls();
  renderIndexViewControls();
  renderMainViewControls();
  searchInput = controlSurfaceElement("appViewer", "search", "#docsViewerSearchInput");
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
    renderBookmarkToggle: renderBookmarkToggle,
    renderIndexSelectionGutter: function (doc) {
      var controller = managementRuntime ? managementRuntime.controller() : null;
      return controller && typeof controller.renderIndexSelectionGutter === "function"
        ? controller.renderIndexSelectionGutter(doc)
        : null;
    },
    workspaceConfig: appSession.domains.workspaceConfig,
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
    infoPanelAutoOpenDocumentModes: settings.infoPanelAutoOpenDocumentModes,
    infoPanelDefaultViewByDocumentMode: settings.infoPanelDefaultViewByDocumentMode,
    infoPanelRefs: infoPanelRefs,
    managedDocumentContext: function () { return latestCollectionReportState; },
    mount: content,
    panelLayout: panelLayout,
    panelView: appSession.domains.panelView,
    projectMainView: panelLayout.projectMainView,
    projectMainViewControlState: function (controlId, controlState) {
      projectMainViewControlState("content-detail", controlId, controlState);
    },
    projectControlStates: function () {
      renderBookmarkControl();
      renderManagementUi();
      renderMainViewControls();
    },
    projectControlState: function (controlId, controlState) {
      projectMainViewControlState("info-panel", controlId, controlState);
    },
    root: root,
    workspaceConfig: appSession.domains.workspaceConfig,
    selectedDocument: appSession.domains.selectedDocument,
    sourceEditorServices: function () {
      return sourceEditingEnabled && sourceService ? sourceEditorServices() : null;
    },
    showWarning: statusController.setStatus,
    viewRegistry: viewRegistry,
    viewerStage: function () { return viewerStage; },
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
    mediaDetailAdapter: settings.mediaDetailAdapter,
    linksDetailAdapter: settings.linksDetailAdapter,
    projectLinksControlState: function (controlState) {
      projectMainViewControlState("links", "document-links", controlState);
    },
    managementService: managementService,
    managementDocumentActions: {
      regenerateCatalogue: function (collection, options) {
        return loadManagementController().then(function (controller) {
          if (!controller || typeof controller.regenerateCatalogue !== "function") {
            throw new Error("Catalogue regeneration is unavailable.");
          }
          return controller.regenerateCatalogue(collection, options);
        });
      },
      toggleCollectionDocumentDraft: function (target, draft) {
        return loadManagementController().then(function (controller) {
          if (!controller || typeof controller.toggleCollectionDocumentDraft !== "function") {
            throw new Error("Collection draft readiness is unavailable.");
          }
          return controller.toggleCollectionDocumentDraft(target, draft);
        });
      },
      createCollectionDocument: function (collection, options) {
        return loadManagementController().then(function (controller) {
          if (!controller || typeof controller.createCollectionDocument !== "function") {
            throw new Error("Collection document creation is unavailable.");
          }
          return controller.createCollectionDocument(collection, options);
        });
      }
    },
    mountDocumentExtras: settings.mountDocumentExtras,
    reportPresentationAdapter: settings.reportPresentationAdapter,
    more: more,
    projectDocumentShell: panelLayout.projectMainView,
    renderBookmarkToggle: renderBookmarkToggle,
    renderBookmarkUi: renderBookmarkUi,
    renderManagementUi: renderManagementUi,
    renderMeta: renderMeta,
    renderSearchMode: renderSearchMode,
    renderSidebar: renderSidebar,
    results: results,
    publishCollectionReportState: publishCollectionReportState,
    requestContentDetail: function (targetContext) {
      if (!documentViewCoordinator) return false;
      return documentViewCoordinator.requestMainView("content-detail", {
        reason: "content-detail-open",
        targetContext: targetContext,
        warn: true
      });
    },
    routeContext: function () { return routeContext; },
    routeSession: appSession.domains.routeSession,
    workspaceConfig: appSession.domains.workspaceConfig,
    selectedDocument: appSession.domains.selectedDocument,
    setRecentModeActive: setRecentModeActive,
    statusCommands: {
      setStatus: statusController.setStatus
    },
    tableDetailAdapter: settings.tableDetailAdapter,
    themedDiagramAdapter: settings.themedDiagramAdapter,
    toolbar: mainViewToolbar,
    viewerStage: function () { return viewerStage; },
    viewerUrlForDocument: viewerUrlForDocument
  });
  routeWorkflow = initDocsViewerRouteWorkflow({
    confirmDocumentNavigation: documentViewCoordinator.confirmDocumentNavigation,
    activeViewState: documentViewCoordinator.activeViewState,
    managedDocumentContext: function () { return latestCollectionReportState; },
    refreshRenderedPayload: function (doc, payload) {
      documentController.renderPayload(doc, payload, "", { preservePosition: true });
    },
    managementUiEnabled: function () { return managementUiEnabled; },
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
    routeStageFromUrl: routeStageFromUrl,
    routeViewerBaseUrl: function () { return routeViewerBaseUrl; },
    searchBatchSize: SEARCH_BATCH_SIZE,
    searchInput: searchInput,
    setRecentModeActive: setRecentModeActive,
    routeSession: appSession.domains.routeSession,
    workspaceConfig: appSession.domains.workspaceConfig,
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
    viewerStage: function () { return viewerStage; },
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
    workspaceConfig: appSession.domains.workspaceConfig,
    searchRecent: appSession.domains.searchRecent,
    viewerBaseUrl: function () { return viewerBaseUrl; },
    viewerStage: function () { return viewerStage; },
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
      currentViewerConfig: function () { return appSession.domains.workspaceConfig.viewerConfig || {}; },
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
          workspaceConfig: appSession.domains.workspaceConfig,
          searchRecent: appSession.domains.searchRecent,
          selectedDocument: appSession.domains.selectedDocument
        }
      },
      managementShellRefs: appShellRefs.managementShell || {},
      mainViewControlHandlerContributions: settings.mainViewControlHandlerContributions || {},
      documentActionContext: documentActionContext,
      sourceEditorServices: sourceEditorServices,
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
      viewerStage: function () { return viewerStage; },
    },
    logger: window.console || console,
    onLoaded: function () {
      var controller = managementRuntime ? managementRuntime.controller() : null;
      if (controller && typeof controller.publishCollectionReportState === "function") {
        controller.publishCollectionReportState(latestCollectionReportState);
      }
      renderSidebar();
    }
  }) : null;

  function loadManagementController() {
    return managementRuntime ? managementRuntime.load() : Promise.resolve(null);
  }

  function routeStageFromUrl() {
    if (!workspaceConfigurationEnabled) return viewerStage;
    return configController.routeStageFromUrl();
  }

  function applyRouteGlobals(values) {
    routeContext = updateDocsViewerRouteContext(routeContext, values, { window: window });
    appSession.domains.routeSession.updateRouteContext(routeContext);
    viewerStage = routeContext.viewerStage || "";
    defaultRouteDocId = routeContext.defaultRouteDocId;
    viewerBaseUrl = routeContext.viewerBaseUrl;
    preserveQueryParams = routeContext.preserveQueryParams || preserveQueryParams;
    viewerPathname = routeContext.viewerPathname;
    bookmarkOwner = routeContext.bookmarkOwner;
    state.indexPanelState = panelLayout.setStorageOwner(bookmarkOwner);
  }

  function loadWorkspaceConfiguration() {
    return configController.loadWorkspaceConfiguration();
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
        "search": { label: "Search docs" }
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
      ["pressed", "expanded", "label", "href", "count"].forEach(function (key) {
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
    var rendered = activeState.activeViewId === "rendered-document"
      && activeState.activeModeId === "rendered-document";
    var report = latestCollectionReportState;
    if (mainViewRefs.collectionBack) {
      mainViewRefs.collectionBack.hidden = !rendered || typeof report.returnToList !== "function";
      mainViewRefs.collectionBack.disabled = root.dataset.managementBusy === "true";
      var label = "Back to all " + String(report.collectionLabel || "").toLowerCase();
      mainViewRefs.collectionBack.title = label;
      mainViewRefs.collectionBack.setAttribute("aria-label", label);
    }
    var mount = mainViewRefs.collectionActions;
    if (mount) {
      var host = report.actionHost || null;
      if (mount.firstChild !== host) mount.replaceChildren(...(host ? [host] : []));
      mount.hidden = !rendered;
    }
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

  function sourceEditorServices() {
    function clearInfoSubscription() {
      sourceEditorInfoRequest += 1;
      if (typeof activeSourceEditorInfoUnsubscribe === "function") {
        activeSourceEditorInfoUnsubscribe();
      }
      activeSourceEditorInfoUnsubscribe = null;
      sourceEditorInfoViewId = settings.infoPanelDefaultViewByDocumentMode["markdown-source"];
    }

    function routeInfoView(adapter) {
      var resolver = settings.sourceEditorInfoViewResolver;
      if (typeof resolver !== "function" || !adapter) return;
      var requestId = ++sourceEditorInfoRequest;
      Promise.resolve(resolver(adapter)).then(function (viewId) {
        var resolvedViewId = String(viewId || "").trim() || settings.infoPanelDefaultViewByDocumentMode["markdown-source"];
        if (requestId !== sourceEditorInfoRequest || adapter !== activeSourceEditorContextAdapter) return;
        sourceEditorInfoViewId = resolvedViewId;
        if (!documentViewCoordinator) return;
        documentViewCoordinator.renderInfoToggle();
        if (!documentViewCoordinator.isInfoOpen()) return;
        if (documentViewCoordinator.activeInfoViewId() === resolvedViewId) {
          documentViewCoordinator.updateInfoPanel();
        } else {
          documentViewCoordinator.openInfoView(resolvedViewId);
        }
      });
    }

    return {
      openMetadataPanel: function () {
        if (!activeSourceEditorContextAdapter) return;
        activeSourceEditorContextAdapter.selectMetadataContext();
        documentViewCoordinator.openInfoView(settings.infoPanelDefaultViewByDocumentMode["markdown-source"]);
      },
      localFolderLinksCapability: function () {
        var capabilities = appSession.domains.management.managementCapabilities;
        return capabilities ? capabilities.local_folder_links || null : null;
      },
      clearActiveSourceEditorContextAdapter: function (adapter) {
        if (adapter && activeSourceEditorContextAdapter !== adapter) return;
        clearInfoSubscription();
        activeSourceEditorContextAdapter = null;
        if (documentViewCoordinator && documentViewCoordinator.isInfoOpen()) {
          documentViewCoordinator.openInfoView("metadata-info");
        } else if (documentViewCoordinator) {
          documentViewCoordinator.renderInfoToggle();
        }
      },
      getActiveSourceEditorContextAdapter: function () {
        return activeSourceEditorContextAdapter;
      },
      getInfoViewId: function () { return sourceEditorInfoViewId; },
      projectMainViewControlState: function (controlId, controlState) {
        projectMainViewControlState("source-editor", controlId, controlState);
      },
      publicPreviewBase: routeContext.publicPreviewBase || "",
      studioBaseUrl: routeContext.studioBaseUrl || "",
      sourceEditorActionControlIds: Array.isArray(settings.sourceEditorActionControlIds)
        ? settings.sourceEditorActionControlIds.slice()
        : [],
      setActiveSourceEditorContextAdapter: function (adapter) {
        clearInfoSubscription();
        activeSourceEditorContextAdapter = adapter || null;
        if (
          activeSourceEditorContextAdapter
          && typeof activeSourceEditorContextAdapter.onSelectionChange === "function"
        ) {
          activeSourceEditorInfoUnsubscribe = activeSourceEditorContextAdapter.onSelectionChange(
            function () {
              routeInfoView(activeSourceEditorContextAdapter);
            }
          );
        }
        routeInfoView(activeSourceEditorContextAdapter);
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

  function viewerUrlForDocument(docId, options) {
    return routeWorkflowCommands.viewerUrlForDocument(docId, options);
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
    var url = viewerUrlForDocument(documentIndex.viewerTargetDocId(doc.doc_id), { manage: false });
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

  function renderMeta() {
    sidebarRenderer.renderMeta();
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
    documentViewCoordinator.showRenderedDocument(documentController.hideDocPane, {
      reason: "document-navigation"
    });
    documentViewCoordinator.updateInfoPanel();
  }

  function showSearchPane() {
    documentViewCoordinator.showView("search-results", documentController.showSearchPane, {
      reason: "document-navigation"
    });
    documentViewCoordinator.updateInfoPanel();
  }

  function showRecentPane() {
    documentViewCoordinator.showView("recent-results", documentController.showRecentPane, {
      reason: "document-navigation"
    });
    documentViewCoordinator.updateInfoPanel();
  }

  function renderPayload(doc, payload, hash) {
    documentViewCoordinator.showRenderedDocument(function () {
      documentController.renderPayload(doc, payload, hash);
      documentViewCoordinator.updateInfoPanel();
    }, { reason: "document-navigation" });
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
    }, { reason: "document-navigation" });
  }

  function renderDocLoadingState(doc) {
    documentViewCoordinator.showRenderedDocument(function () {
      documentController.renderDocLoadingState(doc);
      documentViewCoordinator.updateInfoPanel();
    }, { reason: "document-navigation" });
  }

  function handlePayloadError(error) {
    documentViewCoordinator.showRenderedDocument(function () {
      documentController.handlePayloadError(error);
      documentViewCoordinator.updateInfoPanel();
    }, { reason: "document-navigation" });
  }

  function bindLinkInterception() {
    routeWorkflow.bindRouteLinks();
    panelLayout.bindPanelChrome();

    documentViewCoordinator.bind();


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
      bookmarkOwner: function () { return bookmarkOwner; },
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
    loadWorkspaceConfiguration: loadWorkspaceConfiguration,
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
