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
    fetch: settings.fetch
  }).then(function (resolvedRouteConfig) {
    var routeContext = createDocsViewerRouteContext({
      root: root,
      window: windowRef,
      assetVersion: assetVersion,
      managementModeValue: "manage",
      resolvedRouteConfig: resolvedRouteConfig
    });
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
        routeContext: routeContext,
        documentDisplayModes: settings.documentDisplayModes,
        entrypointHostedViews: settings.entrypointHostedViews,
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
  if (!routeContext.access || !routeContext.access.allowManagement) {
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
  root.__docsViewerAppBootPromise = resolveDocsViewerAppBootContext(Object.assign({}, settings, {
    root: root,
    document: documentRef,
    window: windowRef
  })).then(function (bootContext) {
    if (!bootContext) return null;
    initDocsViewerBootThemeToggle(bootContext);
    return startDocsViewerRuntime(bootContext);
  }).catch(function (error) {
    reportBootFailure(root, error && error.message ? error.message : "Failed to initialize Docs Viewer.", true);
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
