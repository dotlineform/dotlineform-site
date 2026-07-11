import {
  readAssetVersion
} from "./docs-viewer-asset-url.js";
import {
  createDocsViewerRouteContext
} from "./docs-viewer-app-context.js";
import {
  resolveDocsViewerRouteConfigAsync
} from "./docs-viewer-route-config.js";
import {
  getDocsViewerAppShellRefs,
  initDocsViewerAppShell
} from "./docs-viewer-app-shell.js";
import {
  startDocsViewerRuntime
} from "./docs-viewer-app-runtime.js";
import {
  docsViewerRouteFeatureEnabled
} from "./docs-viewer-route-features.js";

function defaultWindowRef() {
  return typeof window !== "undefined" ? window : null;
}

function defaultDocumentRef(windowRef) {
  if (typeof document !== "undefined") return document;
  return windowRef && windowRef.document ? windowRef.document : null;
}

function resolveRoot(settings, documentRef) {
  if (settings.root) return settings.root;
  if (!documentRef || typeof documentRef.getElementById !== "function") return null;
  return documentRef.getElementById("docsViewerRoot");
}

function reportBootFailure(root, message, isError) {
  var documentRef = root && root.ownerDocument ? root.ownerDocument : null;
  var status = documentRef && typeof documentRef.getElementById === "function"
    ? documentRef.getElementById("docsViewerStatus")
    : null;
  if (!status) return;
  status.textContent = message || "Failed to initialize Docs Viewer.";
  status.hidden = false;
  status.classList.toggle("is-error", isError !== false);
}

function routeStateDetail(root, ready) {
  return {
    ready: Boolean(ready),
    busy: root && root.dataset ? root.dataset.docsViewerBusy === "true" : false,
    route: root && root.dataset ? root.dataset.docsViewerRoute || root.dataset.routeId || "" : "",
    mode: root && root.dataset ? root.dataset.docsViewerMode || "" : "",
    service: root && root.dataset ? root.dataset.docsViewerService || "" : "",
    recordLoaded: root && root.dataset ? root.dataset.docsViewerRecordLoaded === "true" : false
  };
}

function setDocsViewerRouteBusy(root, busy) {
  if (!root || !root.dataset) return;
  root.dataset.docsViewerBusy = busy ? "true" : "false";
  root.setAttribute("aria-busy", busy ? "true" : "false");
}

function setDocsViewerRouteReady(root, ready) {
  if (!root || !root.dataset) return;
  var nextReady = Boolean(ready);
  root.dataset.docsViewerReady = nextReady ? "true" : "false";
  if (typeof CustomEvent === "function") {
    root.dispatchEvent(new CustomEvent("docs-viewer:ready", {
      bubbles: true,
      detail: routeStateDetail(root, nextReady)
    }));
  }
}

function initializeDocsViewerRouteState(root) {
  if (!root || !root.dataset) return;
  root.dataset.docsViewerReady = "false";
  setDocsViewerRouteBusy(root, true);
}

function setDatasetBoolean(element, key, value) {
  if (!element || !element.dataset) return;
  element.dataset[key] = value ? "true" : "false";
}

function headerControlsMount(root) {
  if (!root || typeof root.querySelector !== "function") return null;
  return root.querySelector("[data-docs-viewer-header-controls-mount]");
}

function applyBodyClass(documentRef, bodyClass) {
  var body = documentRef && documentRef.body ? documentRef.body : null;
  var className = String(bodyClass || "").trim();
  if (!body || !className) return;
  className.split(/\s+/).filter(Boolean).forEach(function (value) {
    body.classList.add(value);
  });
}

function applyResolvedRouteDataset(root, documentRef, routeContext) {
  var routeConfig = routeContext && routeContext.routeConfig ? routeContext.routeConfig : {};
  var ui = routeConfig.ui && typeof routeConfig.ui === "object" ? routeConfig.ui : {};
  var routeShell = ui.routeShell && typeof ui.routeShell === "object" ? ui.routeShell : {};
  var viewerSearch = ui.viewerSearch && typeof ui.viewerSearch === "object" ? ui.viewerSearch : {};
  var headerMount = headerControlsMount(root);

  if (root && root.dataset) {
    var appContext = routeContext && routeContext.appContext ? routeContext.appContext : {};
    var routeAccess = appContext.routeAccess || {};
    var featurePolicy = appContext.featurePolicy || {};
    var serviceAvailability = appContext.serviceAvailability || {};
    root.dataset.routeId = routeConfig.routeId || "";
    root.dataset.docsViewerRoute = routeConfig.routeId || "";
    root.dataset.docsViewerMode = appContext.kind || "";
    root.dataset.docsViewerAppKind = appContext.kind || "";
    root.dataset.docsViewerService = serviceAvailability.management && serviceAvailability.management.available
      ? "available"
      : (serviceAvailability.generatedData && serviceAvailability.generatedData.local ? "read-only" : "static");
    root.dataset.docsViewerFeatures = Array.isArray(featurePolicy.ids) ? featurePolicy.ids.join(" ") : "";
    setDatasetBoolean(root, "managementUi", routeAccess.managementUi && featurePolicy.management);
    setDatasetBoolean(root, "sourceService", featurePolicy.sourceEditing && serviceAvailability.source && serviceAvailability.source.available);
    setDatasetBoolean(root, "includeScopeParam", routeContext && routeContext.includeScopeParam);
    root.dataset.viewerBaseUrl = routeContext && routeContext.viewerBaseUrl ? routeContext.viewerBaseUrl : "";
    root.dataset.viewerScope = routeContext && routeContext.viewerScope ? routeContext.viewerScope : "";
    if (routeShell.pageTitle) root.dataset.pageTitle = routeShell.pageTitle;
    if (routeShell.bodyClass) root.dataset.bodyClass = routeShell.bodyClass;
  }

  if (headerMount && headerMount.dataset && viewerSearch.configured) {
    headerMount.dataset.searchPlaceholder = viewerSearch.placeholder || "search docs";
    headerMount.dataset.searchAriaLabel = viewerSearch.ariaLabel || "Search docs";
  }

  if (routeShell.pageTitle && documentRef) {
    documentRef.title = routeShell.pageTitle;
  }
  applyBodyClass(documentRef, routeShell.bodyClass);
}

export function resolveDocsViewerAppBootContext(options) {
  var settings = options || {};
  var windowRef = settings.window || defaultWindowRef();
  var documentRef = settings.document || defaultDocumentRef(windowRef);
  var root = resolveRoot(settings, documentRef);
  if (!root || !windowRef || !documentRef) return Promise.resolve(null);

  var assetVersion = settings.assetVersion || readAssetVersion(documentRef);
  return resolveDocsViewerRouteConfigAsync({
    root: root,
    document: documentRef,
    window: windowRef,
    assetVersion: assetVersion,
    routeConfig: settings.routeConfig,
    routeConfigSource: settings.routeConfigSource,
    routeConfigUrl: settings.routeConfigUrl,
    routeId: settings.routeId,
    appKind: settings.appKind,
    fetch: settings.fetch
  }).then(function (resolvedRouteConfig) {
    var routeContext = createDocsViewerRouteContext({
      root: root,
      window: windowRef,
      assetVersion: assetVersion,
      appKind: settings.appKind,
      resolvedRouteConfig: resolvedRouteConfig
    });
    applyResolvedRouteDataset(root, documentRef, routeContext);
    var appShellReady = initDocsViewerAppShell({
      root: root,
      document: documentRef,
      managementShellRenderers: settings.managementShellRenderers,
      routeContext: routeContext
    });
    return appShellReady.then(function (appShellResult) {
      return {
        root: root,
        document: documentRef,
        window: windowRef,
        assetVersion: assetVersion,
        createSourceAdapter: settings.createSourceAdapter,
        routeContext: routeContext,
        documentDisplayModes: settings.documentDisplayModes,
        entrypointHostedViews: settings.entrypointHostedViews,
        infoPanelDefaultViewByDocumentMode: settings.infoPanelDefaultViewByDocumentMode,
        mountDocumentExtras: settings.mountDocumentExtras,
        appShellReady: Promise.resolve(appShellResult),
        appShellResult: appShellResult,
        appShellRefs: getDocsViewerAppShellRefs({
          root: root,
          document: documentRef
        })
      };
    });
  });
}

export function initDocsViewerBootThemeToggle(bootContext) {
  var context = bootContext || {};
  var routeContext = context.routeContext || {};
  var appContext = routeContext.appContext || {};
  if (
    !appContext.routeAccess
    || !appContext.routeAccess.managementUi
    || !docsViewerRouteFeatureEnabled(appContext.featurePolicy, "management")
  ) {
    return Promise.resolve(null);
  }
  return (context.appShellReady || Promise.resolve())
    .then(function () {
      return import("../management/docs-viewer-theme.js");
    }).then(function (module) {
      if (module && typeof module.initDocsViewerThemeToggle === "function") {
        return module.initDocsViewerThemeToggle({
          root: context.root,
          document: context.document,
          storage: context.window ? context.window.localStorage : null
        });
      }
      return null;
    })
    .catch(function (error) {
      console.warn("docs_viewer: theme toggle failed to initialize", error);
      return null;
    });
}

export function startDocsViewerApp(options) {
  var settings = options || {};
  var windowRef = settings.window || defaultWindowRef();
  var documentRef = settings.document || defaultDocumentRef(windowRef);
  var root = resolveRoot(settings, documentRef);
  if (!root || !windowRef || !documentRef) return Promise.resolve(null);

  if (root.__docsViewerAppBootPromise) return root.__docsViewerAppBootPromise;
  initializeDocsViewerRouteState(root);
  root.__docsViewerAppBootPromise = resolveDocsViewerAppBootContext(Object.assign({}, settings, {
    root: root,
    document: documentRef,
    window: windowRef
  })).then(function (bootContext) {
    if (!bootContext) return null;
    initDocsViewerBootThemeToggle(bootContext);
    var runtime = startDocsViewerRuntime(bootContext);
    if (runtime && runtime.initialLoadPromise && typeof runtime.initialLoadPromise.then === "function") {
      runtime.initialLoadPromise.then(function () {
        setDocsViewerRouteBusy(root, false);
        setDocsViewerRouteReady(root, true);
      }, function () {
        setDocsViewerRouteBusy(root, false);
        setDocsViewerRouteReady(root, true);
      });
    } else {
      setDocsViewerRouteBusy(root, false);
      setDocsViewerRouteReady(root, true);
    }
    return runtime;
  }).catch(function (error) {
    reportBootFailure(root, error && error.message ? error.message : "Failed to initialize Docs Viewer.", true);
    setDocsViewerRouteBusy(root, false);
    setDocsViewerRouteReady(root, true);
    throw error;
  });
  return root.__docsViewerAppBootPromise;
}

export function startDocsViewerPublicApp(options) {
  return startDocsViewerApp(Object.assign({}, options || {}, {
    appKind: "public"
  }));
}

export function startDocsViewerManageApp(options) {
  return startDocsViewerApp(Object.assign({}, options || {}, {
    appKind: "manage"
  }));
}
