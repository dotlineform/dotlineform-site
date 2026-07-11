import {
  createDocsViewerPanelLayout
} from "./docs-viewer-panel-layout.js";
import {
  createDocsViewerGeneratedDataRuntime
} from "./docs-viewer-generated-data-runtime.js";
import {
  createDocsViewerConfiguredScopeProvider
} from "./docs-viewer-configured-scope-provider.js";
import {
  createDocsViewerConfigService
} from "./docs-viewer-config-service.js";
import {
  createDocsViewerServiceContext
} from "./docs-viewer-service-context.js";
import {
  createDocsViewerDocumentIndexState
} from "./docs-viewer-document-index-state.js";
import {
  createDocsViewerAppSession
} from "./docs-viewer-app-session.js";
import {
  docsViewerRouteFeatureEnabled
} from "./docs-viewer-route-features.js";

export var DOCS_VIEWER_RUNTIME_DEFAULTS = {
  searchBatchSize: 50,
  searchDebounceMs: 140,
  defaultRecentLimit: 10,
  bookmarkDbName: "dotlineform-docs-viewer",
  bookmarkDbVersion: 1,
  bookmarkStoreName: "favorites",
  managementCapabilityRetryAttempts: 60,
  managementCapabilityRetryDelayMs: 500,
  reloadRetryAttempts: 12,
  reloadRetryDelayMs: 250,
  uiStatusEmojiMaxLength: 8,
  sidebarCollapseMedia: "(min-width: 821px)"
};

var STARTUP_PHASES = [
  {
    id: "bind-events",
    authority: "browser route/config context"
  },
  {
    id: "load-configured-scope-discovery",
    authority: "browser-safe config asset",
    feature: "configured-scope-discovery"
  },
  {
    id: "load-viewer-settings-ui-text",
    authority: "browser-safe config asset"
  },
  {
    id: "initialize-bookmarks",
    authority: "browser storage",
    feature: "bookmarks"
  },
  {
    id: "initialize-management",
    authority: "management backend capability endpoint",
    feature: "management"
  },
  {
    id: "load-initial-index-route",
    authority: "generated static asset or local generated-read service"
  },
  {
    id: "open-import-on-load",
    authority: "management backend write endpoint",
    feature: "management"
  }
];

function cloneRuntimeDefaults(overrides) {
  return Object.assign({}, DOCS_VIEWER_RUNTIME_DEFAULTS, overrides || {});
}

function startupPhaseRecords(appContext, serviceContext) {
  var featurePolicy = appContext && appContext.featurePolicy ? appContext.featurePolicy : {};
  var routeAccess = appContext && appContext.routeAccess ? appContext.routeAccess : {};
  return STARTUP_PHASES.filter(function (phase) {
    if (phase.feature && !docsViewerRouteFeatureEnabled(featurePolicy, phase.feature)) return false;
    if (phase.feature === "management") {
      return Boolean(routeAccess.managementUi && serviceContext && serviceContext.management);
    }
    return true;
  }).map(function (phase) {
    return {
      id: phase.id,
      authority: phase.authority
    };
  });
}

function startupAuthorityRecords(routeContext, serviceContext) {
  var appContext = routeContext.appContext || {};
  var routeAccess = appContext.routeAccess || {};
  var featurePolicy = appContext.featurePolicy || {};
  var output = [
    {
      phase: "root/app-shell input validation",
      authority: "browser route/config context"
    },
    {
      phase: "app session creation",
      authority: "browser route/config context"
    },
    {
      phase: "service-context creation",
      authority: "browser route/config context"
    },
    {
      phase: "viewer settings and UI text load",
      authority: serviceContext.config.authority
    },
    {
      phase: "generated data reads",
      authority: serviceContext.generatedData.authority
    }
  ];

  if (docsViewerRouteFeatureEnabled(featurePolicy, "configured-scope-discovery")) {
    output.splice(3, 0, {
      phase: "configured-scope discovery",
      authority: serviceContext.config.authority
    });
  }
  if (docsViewerRouteFeatureEnabled(featurePolicy, "bookmarks")) {
    output.push({
      phase: "bookmark initialization",
      authority: "browser storage"
    });
  }

  if (docsViewerRouteFeatureEnabled(featurePolicy, "management") && routeAccess.managementUi && serviceContext.management) {
    output.push({
      phase: "management initialization",
      authority: "management backend capability endpoint"
    });
    output.push({
      phase: "import-open-on-load",
      authority: "management backend write endpoint"
    });
  }

  return output;
}

export function createDocsViewerAppComposition(options) {
  var settings = options || {};
  var root = settings.root;
  var window = settings.window || {};
  var routeContext = settings.routeContext || {};
  var routeConfig = routeContext.routeConfig || {};
  var appContext = routeContext.appContext || {};
  var constants = cloneRuntimeDefaults(settings.constants);
  var appShellRefs = settings.appShellRefs || {};
  var routeAccess = appContext.routeAccess || {};
  var featurePolicy = appContext.featurePolicy || {};
  var bookmarkScope = routeContext.bookmarkScope;
  var viewRegistry = settings.viewRegistry;
  if (!viewRegistry) throw new Error("Docs Viewer app composition requires a view registry.");
  var serviceContext = createDocsViewerServiceContext({
    routeContext: routeContext
  });
  var panelLayout = createDocsViewerPanelLayout({
    root: root,
    storage: window.localStorage,
    storageScope: bookmarkScope,
    panels: routeConfig.panels,
    routeId: routeConfig.routeId,
    indexPanelRefs: appShellRefs.indexPanel,
    indexViewToggleRefs: appShellRefs.viewerToolbar,
    mainViewRefs: appShellRefs.mainView,
    infoPanelRefs: appShellRefs.infoPanel,
    viewRegistry: viewRegistry,
    indexPanelAvailable: settings.indexPanelAvailable
  });
  var appSession = createDocsViewerAppSession({
    defaultRecentLimit: constants.defaultRecentLimit,
    panelLayout: panelLayout,
    routeContext: routeContext,
    searchBatchSize: constants.searchBatchSize,
    window: window
  });
  var state = appSession.state;
  viewRegistry.setProjectionInputs(function () {
    return {
      appContext: appContext,
      backendCapabilities: state.managementCapabilities
    };
  });
  var documentIndex = createDocsViewerDocumentIndexState({
    state: state
  });
  var generatedDataRuntime = createDocsViewerGeneratedDataRuntime({
    assetVersion: settings.assetVersion || "",
    generatedBaseUrl: serviceContext.generatedData.baseUrl,
    reloadRetryAttempts: constants.reloadRetryAttempts,
    reloadRetryDelayMs: constants.reloadRetryDelayMs,
    generatedData: appSession.domains.generatedData,
    management: appSession.domains.management,
    selectedDocument: appSession.domains.selectedDocument,
    viewerScope: settings.viewerScope,
    window: window
  });
  var sourceServiceAdapter = (
    docsViewerRouteFeatureEnabled(featurePolicy, "source-editing")
    && serviceContext.source
    && typeof settings.createSourceAdapter === "function"
  )
    ? settings.createSourceAdapter({
        sourceService: serviceContext.source,
        viewerScope: settings.viewerScope,
        window: window
      })
    : null;
  var collectionProvider = createDocsViewerConfiguredScopeProvider({
    generatedData: generatedDataRuntime,
    routeSession: appSession.domains.routeSession,
    scopeConfig: appSession.domains.scopeConfig,
    source: sourceServiceAdapter,
    viewerScope: settings.viewerScope,
    window: window
  });
  var configService = createDocsViewerConfigService({
    dataRequestOptions: generatedDataRuntime.dataRequestOptions,
    docsViewerConfigUrl: serviceContext.config.docsViewerConfigUrl
  });

  function shouldInitializeManagement() {
    return Boolean(
      docsViewerRouteFeatureEnabled(featurePolicy, "management")
      && routeAccess.managementUi
      && serviceContext.management
    );
  }

  function shouldOpenImportOnLoad() {
    return Boolean(routeContext.openImportOnLoad && shouldInitializeManagement());
  }

  return {
    constants: constants,
    serviceContext: serviceContext,
    viewRegistry: viewRegistry,
    panelLayout: panelLayout,
    appSession: appSession,
    documentIndex: documentIndex,
    configService: configService,
    collectionProvider: collectionProvider,
    featurePolicy: featurePolicy,
    generatedDataRuntime: generatedDataRuntime,
    startupPhases: startupPhaseRecords(appContext, serviceContext),
    startupAuthorities: startupAuthorityRecords(routeContext, serviceContext),
    shouldInitializeManagement: shouldInitializeManagement,
    shouldOpenImportOnLoad: shouldOpenImportOnLoad
  };
}

export function startDocsViewerStartupPhases(options) {
  var settings = options || {};
  var composition = settings.composition || {};
  var featurePolicy = composition.featurePolicy || {};
  var stopInitialBusy = function () {};

  function callPhase(name) {
    var handler = settings[name];
    if (typeof handler !== "function") return Promise.resolve(null);
    return Promise.resolve(handler());
  }

  if (typeof settings.bindEvents === "function") {
    settings.bindEvents();
  }
  if (typeof settings.startBusy === "function") {
    stopInitialBusy = settings.startBusy();
  }

  var configuredScopeDiscovery = docsViewerRouteFeatureEnabled(featurePolicy, "configured-scope-discovery")
    ? callPhase("loadConfiguredScopes")
    : Promise.resolve(null);

  return configuredScopeDiscovery
    .then(function () {
      if (typeof settings.renderIndexPanelState === "function") settings.renderIndexPanelState();
      return callPhase("loadViewerSettings");
    })
    .then(function () {
      if (
        docsViewerRouteFeatureEnabled(featurePolicy, "bookmarks")
        && typeof settings.initializeBookmarks === "function"
      ) settings.initializeBookmarks();
      var shouldInitializeManagement = typeof composition.shouldInitializeManagement === "function"
        ? composition.shouldInitializeManagement()
        : true;
      if (shouldInitializeManagement && typeof settings.initializeManagement === "function") settings.initializeManagement();
      return callPhase("loadIndex");
    })
    .then(function () {
      var shouldOpenImport = typeof composition.shouldOpenImportOnLoad === "function"
        ? composition.shouldOpenImportOnLoad()
        : false;
      if (!shouldOpenImport) return null;
      return callPhase("openImportOnLoad");
    })
    .catch(function (error) {
      if (typeof settings.setStatus === "function") {
        settings.setStatus(error.message || "Failed to initialize Docs Viewer.", true);
      }
      if (typeof settings.hideDocPane === "function") settings.hideDocPane();
      if (settings.content) settings.content.textContent = "";
      if (settings.results) settings.results.hidden = true;
      if (settings.more) settings.more.hidden = true;
    })
    .finally(function () {
      stopInitialBusy();
    });
}
