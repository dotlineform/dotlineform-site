import {
  renderDocsViewerTopBar
} from "./docs-viewer-top-bar-renderer.js";
import {
  applyDocsViewerMainViewProjection,
  findDocsViewerMainViewRefs,
  mainViewMount,
  renderDocsViewerMainView
} from "./docs-viewer-main-view-renderer.js";
import {
  applyDocsViewerIndexPanelProjection,
  findDocsViewerIndexPanelRefs,
  indexPanelMount,
  renderDocsViewerIndexPanelShell
} from "./docs-viewer-index-panel-renderer.js";
import {
  applyDocsViewerInfoPanelProjection,
  findDocsViewerInfoPanelRefs,
  infoPanelMount,
  renderDocsViewerInfoPanelShell
} from "./docs-viewer-info-panel-renderer.js";
import {
  createDocsViewerRouteContext
} from "./docs-viewer-app-context.js";
import {
  docsViewerRouteFeatureEnabled
} from "./docs-viewer-route-features.js";

function routeFeatureEnabled(routeContext, featureId) {
  var appContext = routeContext && routeContext.appContext ? routeContext.appContext : {};
  return docsViewerRouteFeatureEnabled(appContext.featurePolicy, featureId);
}

function routeContextFor(settings) {
  if (settings.routeContext) return settings.routeContext;
  if (!settings.routeConfig) return null;
  return createDocsViewerRouteContext({
    appKind: settings.appKind,
    root: settings.root,
    document: settings.document,
    routeConfig: settings.routeConfig,
    window: settings.window
  });
}

function managementAllowed(routeContext) {
  return Boolean(
    routeContext
    && routeContext.appContext
    && routeContext.appContext.routeAccess
    && routeContext.appContext.routeAccess.managementUi
    && routeFeatureEnabled(routeContext, "management")
  );
}

function headerControlsMount(root) {
  if (!root) return null;
  return root.querySelector("[data-docs-viewer-header-controls-mount]");
}

function mainViewToolbarMount(root) {
  if (!root) return null;
  return root.querySelector("[data-docs-viewer-main-view-toolbar-mount]");
}

function managementShellMount(root) {
  if (!root) return null;
  return root.querySelector("[data-docs-viewer-management-shell-mount]");
}

function emptyManagementShell(documentRef) {
  return {};
}

function managementShellRenderers(settings) {
  return settings.managementShellRenderers || {};
}

function canRenderManagementShell(renderers) {
  return Boolean(
    renderers
    && (
      typeof renderers.renderShell === "function"
    )
  );
}

function appShellResult(parts) {
  if (parts.root) {
    parts.root.__docsViewerAppShellManagementShellRefs = parts.managementShell || {};
  }
  return {
    topBar: parts.topBar,
    viewerToolbar: parts.viewerToolbar,
    mainView: parts.mainView,
    infoPanel: parts.infoPanel,
    indexPanel: parts.indexPanel,
    routeContext: parts.routeContext,
    managementShell: parts.managementShell || null
  };
}

export function initDocsViewerAppShell(options) {
  var settings = options || {};
  var root = settings.root;
  var documentRef = settings.document || document;
  var routeContext = routeContextFor(settings);
  var renderers = managementShellRenderers(settings);
  var topBar = renderDocsViewerTopBar({
    document: documentRef,
    root: root,
    mount: settings.headerControlsMount || headerControlsMount(root),
    routeContext: routeContext
  });
  var mainView = renderDocsViewerMainView({
    document: documentRef,
    root: root,
    mount: settings.mainViewMount || mainViewMount(root),
    toolbarMount: settings.mainViewToolbarMount || (topBar && topBar.mainViewToolbarMount) || mainViewToolbarMount(root),
    viewRegistry: settings.viewRegistry
  });
  var indexPanel = renderDocsViewerIndexPanelShell({
    document: documentRef,
    root: root,
    mount: settings.indexPanelMount || indexPanelMount(root)
  });
  var infoPanel = renderDocsViewerInfoPanelShell({
    document: documentRef,
    root: root,
    mount: settings.infoPanelMount || infoPanelMount(root)
  });
  var shellMount = settings.managementShellMount || managementShellMount(root);
  if (shellMount) {
    shellMount.replaceChildren();
  }
  if (!managementAllowed(routeContext) || !canRenderManagementShell(renderers)) {
    return Promise.resolve(appShellResult({
      topBar: topBar && topBar.topBar,
      viewerToolbar: topBar && topBar.viewerToolbar,
      mainView: mainView,
      infoPanel: infoPanel,
      indexPanel: indexPanel,
      routeContext: routeContext,
      root: root,
      managementShell: null
    }));
  }

  return Promise.resolve()
    .then(function () {
      var managementShell = shellMount && typeof renderers.renderShell === "function"
        ? renderers.renderShell({
        document: documentRef,
        root: root,
        mount: shellMount
        })
        : emptyManagementShell(documentRef);
      return appShellResult({
        topBar: topBar && topBar.topBar,
        viewerToolbar: topBar && topBar.viewerToolbar,
        mainView: mainView,
        infoPanel: infoPanel,
        indexPanel: indexPanel,
        routeContext: routeContext,
        root: root,
        managementShell: managementShell
      });
    })
    .catch(function (error) {
      console.warn("docs_viewer: management shell failed to initialize", error);
      return appShellResult({
        topBar: topBar && topBar.topBar,
        viewerToolbar: topBar && topBar.viewerToolbar,
        mainView: mainView,
        infoPanel: infoPanel,
        indexPanel: indexPanel,
        routeContext: routeContext,
        root: root,
        managementShell: null
      });
    });
}

export function getDocsViewerAppShellMainViewRefs(options) {
  var settings = options || {};
  return findDocsViewerMainViewRefs({
    document: settings.document || document,
    root: settings.root || null
  });
}

export function getDocsViewerAppShellIndexPanelRefs(options) {
  var settings = options || {};
  return findDocsViewerIndexPanelRefs({
    document: settings.document || document,
    root: settings.root || null
  });
}

export function getDocsViewerAppShellInfoPanelRefs(options) {
  var settings = options || {};
  return findDocsViewerInfoPanelRefs({
    document: settings.document || document,
    root: settings.root || null
  });
}

export function getDocsViewerAppShellManagementShellRefs(options) {
  var settings = options || {};
  var root = settings.root || null;
  return root && root.__docsViewerAppShellManagementShellRefs
    ? root.__docsViewerAppShellManagementShellRefs
    : {};
}

export function getDocsViewerAppShellRefs(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var root = settings.root || null;
  return {
    controlSurfaces: {
      appViewer: root ? root.querySelector('[data-docs-viewer-control-surface-mount="app-viewer"]') : null,
      appManagement: root ? root.querySelector('[data-docs-viewer-control-surface-mount="app-management"]') : null,
      indexView: root ? root.querySelector('[data-docs-viewer-control-surface-mount="index-view"]') : null,
      mainView: root ? root.querySelector('[data-docs-viewer-control-surface-mount="main-view"]') : null
    },
    topBar: {
      root: documentRef.getElementById("docsViewerTopBar")
    },
    viewerToolbar: {
      root: documentRef.getElementById("docsViewerViewerToolbar")
    },
    indexPanel: getDocsViewerAppShellIndexPanelRefs({ root: root, document: documentRef }),
    mainView: getDocsViewerAppShellMainViewRefs({ root: root, document: documentRef }),
    infoPanel: getDocsViewerAppShellInfoPanelRefs({ root: root, document: documentRef }),
    managementShell: getDocsViewerAppShellManagementShellRefs({ root: root, document: documentRef }),
    status: documentRef.getElementById("docsViewerStatus"),
    bookmarkRow: documentRef.getElementById("docsViewerBookmarkRow")
  };
}

export function renderDocsViewerAppShellIndexPanelState(options) {
  applyDocsViewerIndexPanelProjection(options || {});
}

export function renderDocsViewerAppShellMainViewState(options) {
  applyDocsViewerMainViewProjection(options || {});
}

export function renderDocsViewerAppShellInfoPanelState(options) {
  applyDocsViewerInfoPanelProjection(options || {});
}
