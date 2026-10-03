import {
  normalizeSearchText
} from "./docs-viewer-search.js";
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
import {
  createDocsViewerSharedControlRenderers
} from "./docs-viewer-app-control-renderers.js";
import {
  createDocsViewerControlSurfaceHost
} from "./docs-viewer-control-surface-host.js";
import {
  initDocsViewerFocusMode
} from "./docs-viewer-focus-mode.js";

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

  initDocsViewerFocusMode(root, document);

  var indexPanelRefs = appShellRefs.indexPanel;
  var nav = indexPanelRefs.nav;
  var controlSurfaceRefs = appShellRefs.controlSurfaces || {};
  var mainViewRefs = appShellRefs.mainView;
  var infoPanelRefs = appShellRefs.infoPanel;
  var mainViewToolbar = mainViewRefs.toolbar;
  var content = mainViewRefs.content;
  var searchInput = null;
  var resultsStatus = indexPanelRefs.resultsStatus;
  var results = indexPanelRefs.results;
  var more = indexPanelRefs.more;

  var appContext = routeContext.appContext || {};
  var routeAccess = appContext.routeAccess || {};
  var featurePolicy = appContext.featurePolicy || {};
  var managementEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "management");
  var recentEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "recent");
  var searchEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "search");
  var sourceEditingEnabled = docsViewerRouteFeatureEnabled(featurePolicy, "source-editing");
  var docsViewerConfigUrl = routeContext.docsViewerConfigUrl;
  var routeViewerBaseUrl = routeContext.routeViewerBaseUrl;
  var viewerBaseUrl = routeContext.viewerBaseUrl;

  var preserveQueryParams = routeContext.preserveQueryParams || [];
  var defaultRouteDocId = routeContext.defaultRouteDocId;
  var viewerPathname = routeContext.viewerPathname;
  var runtimeDefaults = DOCS_VIEWER_RUNTIME_DEFAULTS;
  var SEARCH_BATCH_SIZE = runtimeDefaults.searchBatchSize;
  var SEARCH_DEBOUNCE_MS = runtimeDefaults.searchDebounceMs;
  var DEFAULT_RECENT_LIMIT = runtimeDefaults.defaultRecentLimit;
  var MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS = runtimeDefaults.managementCapabilityRetryAttempts;
  var MANAGEMENT_CAPABILITY_RETRY_DELAY_MS = runtimeDefaults.managementCapabilityRetryDelayMs;
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
    onIndexProjection: function (projection) {
      latestIndexProjection = projection || null;
      var controller = managementRuntime ? managementRuntime.controller() : null;
      if (controller && typeof controller.handleIndexViewChange === "function") {
        controller.handleIndexViewChange(latestIndexProjection && latestIndexProjection.activeViewId);
      }
      renderIndexListControls();
      renderIndexViewControls();
    },
    onTreeVisible: function () {
      if (sidebarRenderer) sidebarRenderer.scrollSelectionIntoView();
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
  var searchController = null;
  var documentController = null;
  var routeWorkflow = null;
  var documentIndex = null;
  var documentViewCoordinator = null;
  var activeSourceEditorContextAdapter = null;
  var recentControlLabel = "Recent";
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
  var appViewerControlHost;
  var indexListControlHost = null;
  var appManagementControlStates = new Map();
  var appManagementControlHost = null;
  var indexViewControlStates = new Map();
  var indexViewControlHost = null;
  var mainViewControlOwners = new Map();
  var mainViewControlStates = new Map();
  var mainViewControlHost = null;

  function publishCollectionReportState(value) {
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
    renderMainViewControls();
    if (searchController) searchController.syncSelection();
  }

  function documentActionContext() { return documentController ? documentController.actionContext() : {}; }

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
    surfaceId: "app-viewer"
  });
  indexListControlHost = createDocsViewerControlSurfaceHost({
    mount: controlSurfaceRefs.indexLists,
    registry: viewRegistry,
    renderers: createDocsViewerSharedControlRenderers(),
    surfaceId: "index-lists",
    onDispatch: function (detail) {
      if (!searchController) return;
      if (detail.controlId === "recent" && detail.eventType === "click") searchController.handleRecentControl();
      if (detail.controlId === "search" && detail.eventType === "input") {
        searchController.handleSearchInput(detail.event.target.value);
      }
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
  if (contentDetailBackControlId) {
    mainViewControlOwners.set(contentDetailBackControlId, function () {
      if (!documentViewCoordinator) return;
      routeWorkflowCommands.returnToDocument().catch(function (error) { statusController.setStatus(error.message, true); });
    });
  }
  if (mainViewRefs.collectionBack) {
    mainViewRefs.collectionBack.addEventListener("click", function () {
      if (mainViewRefs.collectionBack.hidden || mainViewRefs.collectionBack.disabled) return;
      routeWorkflowCommands.back();
    });
  }
  appViewerControlHost.render();
  renderIndexListControls();
  renderAppManagementControls();
  renderIndexViewControls();
  renderMainViewControls();
  searchInput = controlSurfaceElement("indexLists", "search", "#docsViewerSearchInput");
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
    documentIndex: appSession.domains.documentIndex,
    toolbar: mainViewToolbar,
    nav: nav,
    workspaceConfig: appSession.domains.workspaceConfig,
    selectedDocument: appSession.domains.selectedDocument,
    statusForIndexDoc: documentIndex.statusForIndexDoc,
    viewerTargetDocId: documentIndex.viewerTargetDocId,
    viewerUrl: viewerUrl
  });
  documentViewCoordinator = createDocsViewerDocumentViewCoordinator({
    appContext: function () { return appContext; },
    buildTrail: buildTrail,
    collectionProvider: collectionProvider,
    documentIndex: appSession.domains.documentIndex,
    infoPanelRefs: infoPanelRefs,
    managedDocumentContext: documentActionContext,
    mount: function () { return documentController ? documentController.activeMount() : content; },
    panelLayout: panelLayout,
    panelView: appSession.domains.panelView,
    projectMainView: panelLayout.projectMainView,
    projectMainViewControlState: function (controlId, controlState) {
      projectMainViewControlState("content-detail", controlId, controlState);
    },
    projectControlStates: function () {
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
    viewerTargetDocId: documentIndex.viewerTargetDocId,
    viewerUrl: viewerUrl
  });
  documentController = initDocsViewerDocumentController({
    appContext: appContext,
    checkGeneratedDataReadCapability: checkGeneratedDataReadCapability,
    content: content,
    collectionProvider: collectionProvider,
    diagramDetailAdapter: settings.diagramDetailAdapter,
    inlineMermaidAdapter: settings.inlineMermaidAdapter,
    mediaDetailAdapter: settings.mediaDetailAdapter,
    managementService: managementService,
    managementDocumentActions: {
      regenerateCatalogue: function (collection, options) {
        return loadManagementController().then(function (controller) {
          if (!controller || typeof controller.regenerateCatalogue !== "function") {
            throw new Error("Catalogue regeneration is unavailable.");
          }
          return controller.regenerateCatalogue(collection, options);
        });
      }
    },
    mountDocumentExtras: settings.mountDocumentExtras,
    openDocument: function (target, response) {
      if (response && response.record) collectionProvider.commitDocumentChange({ target: target, record: response.record });
      return routeWorkflowCommands.loadDoc(target);
    },
    commitDeletedDocument: function (target) { return routeWorkflowCommands.commitDeletedDocument(target); },
    mountRelatedLinks: documentViewCoordinator.mountRelatedLinks,
    reportPresentationAdapter: settings.reportPresentationAdapter,
    projectDocumentShell: panelLayout.projectMainView,
    renderManagementUi: renderManagementUi,
    renderMeta: renderMeta,
    publishCollectionReportState: publishCollectionReportState,
    requestContentDetail: function (targetContext) {
      if (!routeWorkflow) return false;
      routeWorkflowCommands.openPresentation(targetContext).catch(function (error) { statusController.setStatus(error.message, true); });
      return true;
    },
    routeContext: function () { return routeContext; },
    routeSession: appSession.domains.routeSession,
    workspaceConfig: appSession.domains.workspaceConfig,
    selectedDocument: appSession.domains.selectedDocument,
    statusCommands: {
      setStatus: statusController.setStatus
    },
    tableDetailAdapter: settings.tableDetailAdapter,
    themedDiagramAdapter: settings.themedDiagramAdapter,
    toolbar: mainViewToolbar,
    viewerUrlForDocument: viewerUrlForDocument
  });
  routeWorkflow = initDocsViewerRouteWorkflow({
    activeMount: documentController.activeMount,
    captureDocument: documentController.capture,
    restoreDocument: documentController.restore,
    restoreRetainedDocument: documentController.restoreRetained,
    retainDocuments: documentController.retainDocuments,
    scrollToHash: documentController.scrollToHash,
    prepareDocumentNavigation: documentViewCoordinator.prepareDocumentNavigation,
    returnToDocument: documentViewCoordinator.returnToDocument,
    openPresentation: documentViewCoordinator.openPresentation,
    projectBack: renderMainViewControls,
    activeIndexViewId: function () { return panelLayout.projectViewState().index.activeViewId; },
    syncIndexRoute: function (query, viewId) {
      if (searchController) searchController.applyRoute(query, viewId);
    },
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
    handleManagementRootClick: function (event) {
      var controller = managementRuntime ? managementRuntime.controller() : null;
      return Boolean(controller && controller.handleRootClick(event));
    },
    handleMissingDoc: handleMissingDoc,
    handlePayloadError: handlePayloadError,
    hideContextMenu: hideContextMenu,
    hideDocPane: hideDocPane,
    collectionProvider: collectionProvider,
    preserveQueryParams: function () { return preserveQueryParams; },
    renderDocLoadingState: renderDocLoadingState,
    renderManagementUi: renderManagementUi,
    renderPayload: renderPayload,
    renderSidebar: renderSidebar,
    trackSidebarSelection: trackSidebarSelection,
    toggleSidebarBranch: sidebarRenderer.toggleBranch,
    resolveLoadableDocId: documentIndex.resolveLoadableDocId,
    root: root,
    routeSession: appSession.domains.routeSession,
    documentIndex: appSession.domains.documentIndex,
    selectedDocument: appSession.domains.selectedDocument,
    searchRecent: appSession.domains.searchRecent,
    statusCommands: {
      setStatus: statusController.setStatus,
      startBusy: statusController.startBusy
    },
    viewerBaseUrl: function () { return viewerBaseUrl; },
    viewerPathname: function () { return viewerPathname; },
    window: window
  });
  var routeWorkflowCommands = routeWorkflow.commands;
  var searchRouteCommands = createDocsViewerSearchRouteCommands({
    routeCommands: routeWorkflowCommands,
    viewerTargetDocId: documentIndex.viewerTargetDocId
  });
  searchController = searchEnabled || recentEnabled ? initDocsViewerSearchController({
    setSearchInput: function (query) {
      if (searchInput) searchInput.value = query;
    },
    collectionProvider: collectionProvider,
    hideContextMenu: hideContextMenu,
    hasActiveQuery: hasActiveQuery,
    currentDocumentTarget: currentDocumentTarget,
    workspaceConfig: appSession.domains.workspaceConfig,
    more: more,
    setIndexView: panelLayout.setActiveIndexView,
    resultsView: indexPanelRefs.resultsView,
    resultsStatus: resultsStatus,
    results: results,
    routeCommands: searchRouteCommands,
    searchBatchSize: SEARCH_BATCH_SIZE,
    searchDebounceMs: SEARCH_DEBOUNCE_MS,
    searchEnabled: searchEnabled,
    searchRecent: appSession.domains.searchRecent,
    recentEnabled: recentEnabled,
    activeIndexViewId: function () { return panelLayout.projectViewState().index.activeViewId; },
    startBusy: statusController.startBusy
  }) : null;
  if (collectionProvider.subscribeDocumentChanges) collectionProvider.subscribeDocumentChanges(function (change) {
    if (change.target.collection) return;
    var index = appSession.domains.documentIndex;
    if (change.deleted) index.allDocs = index.allDocs.filter(function (doc) { return doc.doc_id !== change.target.doc_id; });
    else index.allDocs = index.allDocs.map(function (doc) { return doc.doc_id === change.target.doc_id ? Object.assign({}, doc, change.record) : doc; });
    documentIndex.applyDocVisibility();
    renderSidebar();
  });
  var configController = initDocsViewerConfigController({
    activeIndexViewId: function () { return panelLayout.projectViewState().index.activeViewId; },
    configService: composition.configService,
    featurePolicy: featurePolicy,
    defaultRecentLimit: DEFAULT_RECENT_LIMIT,
    documentIndex: appSession.domains.documentIndex,
    managementController: function () {
      return managementRuntime ? managementRuntime.controller() : null;
    },
    setRecentControlLabel: function (label) {
      recentControlLabel = String(label || "Recent");
      renderIndexListControls();
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
      commitDocumentChange: collectionProvider.commitDocumentChange,
      commitDeletedDocument: function (target) { return routeWorkflowCommands.commitDeletedDocument(target); },
      viewRegistry: viewRegistry,
      activeViewState: documentViewCoordinator.activeViewState,
      projectAppManagementControlState: projectAppManagementControlState,
      projectIndexViewControlState: projectIndexViewControlState,
      projectMainViewControlState: function (controlId, controlState) {
        projectMainViewControlState("management", controlId, controlState);
      },
      nav: nav,
      renderRecentMode: renderRecentMode,
      renderSearchMode: renderSearchMode,
      renderSidebar: renderSidebar,
      root: root,
      routeReload: {
        reloadViewerConfiguration: function () { return configController.reloadViewerConfiguration(); },
        routeCommands: routeWorkflowCommands
      },
      searchInput: searchInput,
      resetIndexLists: function () { if (searchController) searchController.resetForReload(); },
      setStatus: statusController.setStatus,
      requestMainView: documentViewCoordinator.requestMainView,
      requestDocumentMode: documentViewCoordinator.requestDocumentMode,
      markdownDocLink: markdownDocLink,
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

  function applyRouteGlobals(values) {
    routeContext = updateDocsViewerRouteContext(routeContext, values, { window: window });
    appSession.domains.routeSession.updateRouteContext(routeContext);

    defaultRouteDocId = routeContext.defaultRouteDocId;
    viewerBaseUrl = routeContext.viewerBaseUrl;
    preserveQueryParams = routeContext.preserveQueryParams || preserveQueryParams;
    viewerPathname = routeContext.viewerPathname;
  }

  function loadWorkspaceConfiguration() {
    return configController.loadWorkspaceConfiguration();
  }

  function hasActiveQuery(query) {
    if (!searchEnabled) return false;
    var searchRecent = appSession.domains.searchRecent;
    return Boolean(normalizeSearchText(typeof query === "string" ? query : searchRecent.searchQuery));
  }

  function controlSurfaceElement(surfaceKey, controlId, selector) {
    var mount = controlSurfaceRefs[surfaceKey] || null;
    if (!mount) return null;
    var controlRoot = Array.from(mount.children).find(function (child) {
      return child.dataset && child.dataset.docsViewerControl === controlId;
    }) || null;
    return controlRoot && selector ? controlRoot.querySelector(selector) : controlRoot;
  }

  function renderIndexListControls() {
    if (!indexListControlHost) return [];
    return indexListControlHost.render({
      controlStateById: {
        "recent": {
          label: recentControlLabel,
          pressed: latestIndexProjection && latestIndexProjection.activeViewId === "recent-results"
        },
        "search": { label: "Search" }
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
      mainViewRefs.collectionBack.hidden = !rendered || !routeWorkflow || !routeWorkflow.commands.hasCaller();
      mainViewRefs.collectionBack.disabled = root.dataset.managementBusy === "true";
      var label = "Back";
      mainViewRefs.collectionBack.title = label;
      mainViewRefs.collectionBack.setAttribute("aria-label", label);
    }
    var mount = mainViewRefs.collectionActions;
    if (mount) {
      // Manage detail actions use Edit while rendered; retain them here in other modes.
      var host = appContext.kind === "manage" && report.state === "detail" && rendered ? null : report.actionHost || null;
      if (mount.firstChild !== host) mount.replaceChildren(...(host ? [host] : []));
      mount.hidden = !rendered;
    }
    return mainViewControlHost.render({
      activeViewId: activeState.activeViewId,
      activeModeId: activeState.activeModeId,
      controlStateById: controlStateById
    });
  }

  function renderIndexPanelState() {
    panelLayout.renderIndexPanelState();
  }

  function loadViewerSettings() {
    return configController.loadViewerSettings();
  }

  function sourceEditorServices() {
    return {
      commitDocumentChange: collectionProvider.commitDocumentChange,
      localFolderLinksCapability: function () {
        var capabilities = appSession.domains.management.managementCapabilities;
        return capabilities ? capabilities.local_folder_links || null : null;
      },
      clearActiveSourceEditorContextAdapter: function (adapter) {
        if (adapter && activeSourceEditorContextAdapter !== adapter) return;
        activeSourceEditorContextAdapter = null;
      },
      getActiveSourceEditorContextAdapter: function () {
        return activeSourceEditorContextAdapter;
      },
      projectMainViewControlState: function (controlId, controlState) {
        projectMainViewControlState("source-editor", controlId, controlState);
      },
      publicPreviewBase: routeContext.publicPreviewBase || "",
      studioBaseUrl: routeContext.studioBaseUrl || "",
      sourceEditorActionControlIds: Array.isArray(settings.sourceEditorActionControlIds)
        ? settings.sourceEditorActionControlIds.slice()
        : [],
      setActiveSourceEditorContextAdapter: function (adapter) {
        activeSourceEditorContextAdapter = adapter || null;
        if (documentViewCoordinator) documentViewCoordinator.closeInfoIfOpen();
      },
      setStatus: statusController.setStatus,
      startBusy: statusController.startBusy
    };
  }

  function viewerUrl(docId, hash, query, options) {
    return routeWorkflowCommands.viewerUrl(docId, hash, query, options);
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

  function renderSidebar() {
    sidebarRenderer.renderSidebar();
  }

  function trackSidebarSelection() {
    sidebarRenderer.trackSelection();
    if (searchController) searchController.syncSelection();
  }

  function currentDocumentTarget() { return appSession.domains.selectedDocument.documentTarget; }

  function renderMeta() {
    sidebarRenderer.renderMeta();
  }

  function hideContextMenu() {
    var controller = managementRuntime ? managementRuntime.controller() : null;
    if (controller) {
      controller.hideContextMenu();
    }
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
  }

  function renderPayload(doc, payload, hash) { return documentController.renderPayload(doc, payload, hash); }

  function cancelSearchDebounce() {
    var searchRecent = appSession.domains.searchRecent;
    if (searchRecent.searchDebounceId == null) return;
    window.clearTimeout(searchRecent.searchDebounceId);
    searchRecent.searchDebounceId = null;
  }

  function handleMissingDoc() { return documentController.handleMissingDoc(); }

  function renderDocLoadingState(doc) { return documentController.renderDocLoadingState(doc); }

  function handlePayloadError(error) { return documentController.handlePayloadError(error); }

  function bindLinkInterception() {
    routeWorkflow.bindRouteLinks();

    documentViewCoordinator.bind();

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
  window.addEventListener("resize", hideContextMenu);
  window.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      hideContextMenu();
    }
  });

  var initialLoadPromise = startDocsViewerStartupPhases({
    composition: composition,
    bindEvents: bindLinkInterception,
    startBusy: statusController.startBusy,
    loadWorkspaceConfiguration: loadWorkspaceConfiguration,
    renderIndexPanelState: renderIndexPanelState,
    loadViewerSettings: loadViewerSettings,
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
