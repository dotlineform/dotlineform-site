import {
  createDocsViewerPanelLayout
} from "./docs-viewer-panel-layout.js";
import {
  createDocsViewerDefaultHostedViews,
  createDocsViewerHostedViewRegistry,
  createDocsViewerRouteHostedViews,
  registerDocsViewerHostedViews
} from "./docs-viewer-hosted-views.js";
import {
  createDocsViewerGeneratedDataRuntime
} from "./docs-viewer-generated-data-runtime.js";
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
    authority: "browser route/config context",
    contexts: ["public", "manage"]
  },
  {
    id: "load-docs-viewer-config",
    authority: "browser-safe config asset",
    contexts: ["public", "manage"]
  },
  {
    id: "load-viewer-config-ui-text",
    authority: "browser-safe config asset",
    contexts: ["public", "manage"]
  },
  {
    id: "initialize-bookmarks",
    authority: "browser storage",
    contexts: ["public", "manage"]
  },
  {
    id: "initialize-management",
    authority: "management backend capability endpoint",
    contexts: ["manage"]
  },
  {
    id: "load-initial-index-route",
    authority: "generated static asset or local generated-read service",
    contexts: ["public", "manage"]
  },
  {
    id: "open-import-on-load",
    authority: "management backend write endpoint",
    contexts: ["manage"]
  }
];

function cloneRuntimeDefaults(overrides) {
  return Object.assign({}, DOCS_VIEWER_RUNTIME_DEFAULTS, overrides || {});
}

function startupContextName(access) {
  return access && access.allowManagement ? "manage" : "public";
}

function startupPhaseRecords(access) {
  var contextName = startupContextName(access);
  return STARTUP_PHASES.filter(function (phase) {
    return phase.contexts.indexOf(contextName) !== -1;
  }).map(function (phase) {
    return {
      id: phase.id,
      authority: phase.authority
    };
  });
}

function startupAuthorityRecords(routeContext, serviceContext) {
  var access = routeContext.access || {};
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
      phase: "config and UI text load",
      authority: serviceContext.config.authority
    },
    {
      phase: "generated data reads",
      authority: serviceContext.generatedRead.authority
    },
    {
      phase: "bookmark initialization",
      authority: "browser storage"
    }
  ];

  if (access.allowManagement) {
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
  var constants = cloneRuntimeDefaults(settings.constants);
  var appShellRefs = settings.appShellRefs || {};
  var access = routeContext.access || {};
  var bookmarkScope = routeContext.bookmarkScope;
  var routeHostedViews = routeConfig.hostedViews && Array.isArray(routeConfig.hostedViews.records)
    ? routeConfig.hostedViews.records
    : [];
  var entrypointHostedViews = Array.isArray(settings.entrypointHostedViews)
    ? settings.entrypointHostedViews
    : [];
  var defaultHostedViews = createDocsViewerDefaultHostedViews().concat(entrypointHostedViews);

  var hostedViewRegistry = registerDocsViewerHostedViews(
    createDocsViewerHostedViewRegistry({ accessProjection: access }),
    defaultHostedViews.concat(createDocsViewerRouteHostedViews(routeHostedViews, {
      reservedRecords: defaultHostedViews
    }))
  );
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
    hostedViewRegistry: hostedViewRegistry,
    indexPanelAvailable: settings.indexPanelAvailable
  });
  var appSession = createDocsViewerAppSession({
    defaultRecentLimit: constants.defaultRecentLimit,
    hostedViewRegistry: hostedViewRegistry,
    panelLayout: panelLayout,
    routeContext: routeContext,
    searchBatchSize: constants.searchBatchSize,
    window: window
  });
  var state = appSession.state;
  var documentIndex = createDocsViewerDocumentIndexState({
    state: state
  });
  var generatedDataRuntime = createDocsViewerGeneratedDataRuntime({
    assetVersion: settings.assetVersion || "",
    generatedBaseUrl: serviceContext.generatedRead.baseUrl,
    reloadRetryAttempts: constants.reloadRetryAttempts,
    reloadRetryDelayMs: constants.reloadRetryDelayMs,
    state: state,
    viewerScope: settings.viewerScope,
    window: window
  });
  var configService = createDocsViewerConfigService({
    dataRequestOptions: generatedDataRuntime.dataRequestOptions,
    docsViewerConfigUrl: serviceContext.config.docsViewerConfigUrl
  });

  function shouldInitializeManagement() {
    return Boolean(access.allowManagement);
  }

  function shouldOpenImportOnLoad() {
    return Boolean(routeContext.openImportOnLoad && shouldInitializeManagement());
  }

  return {
    constants: constants,
    serviceContext: serviceContext,
    hostedViewRegistry: hostedViewRegistry,
    panelLayout: panelLayout,
    appSession: appSession,
    documentIndex: documentIndex,
    configService: configService,
    generatedDataRuntime: generatedDataRuntime,
    managementBaseUrl: serviceContext.management ? serviceContext.management.baseUrl : "",
    generatedBaseUrl: serviceContext.generatedRead.baseUrl,
    startupPhases: startupPhaseRecords(access),
    startupAuthorities: startupAuthorityRecords(routeContext, serviceContext),
    shouldInitializeManagement: shouldInitializeManagement,
    shouldOpenImportOnLoad: shouldOpenImportOnLoad
  };
}

export function startDocsViewerStartupPhases(options) {
  var settings = options || {};
  var composition = settings.composition || {};
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

  return callPhase("loadDocsViewerConfig")
    .then(function () {
      if (typeof settings.renderIndexPanelState === "function") settings.renderIndexPanelState();
      return callPhase("loadViewerConfig");
    })
    .then(function () {
      if (typeof settings.initializeBookmarks === "function") settings.initializeBookmarks();
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
