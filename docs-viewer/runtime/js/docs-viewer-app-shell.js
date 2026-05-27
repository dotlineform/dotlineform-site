import {
  renderDocsViewerHeaderControls
} from "./docs-viewer-header-controls-renderer.js";
import {
  applyDocsViewerDocumentShellProjection,
  documentShellMount,
  findDocsViewerDocumentShellRefs,
  renderDocsViewerDocumentShell
} from "./docs-viewer-document-shell-renderer.js";
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

function routeContextFor(settings) {
  return settings.routeContext || createDocsViewerRouteContext({
    root: settings.root,
    routeConfig: settings.routeConfig,
    window: settings.window
  });
}

function managementAllowed(routeContext) {
  return Boolean(routeContext && routeContext.access && routeContext.access.canLoadManagementUi);
}

function headerControlsMount(root) {
  if (!root) return null;
  return root.querySelector("[data-docs-viewer-header-controls-mount]");
}

function managementActionsMount(root) {
  if (!root) return null;
  return root.querySelector("[data-docs-viewer-management-actions-mount]");
}

export function initDocsViewerAppShell(options) {
  var settings = options || {};
  var root = settings.root;
  var documentRef = settings.document || document;
  var routeContext = routeContextFor(settings);
  var headerControls = renderDocsViewerHeaderControls({
    document: documentRef,
    root: root,
    mount: settings.headerControlsMount || headerControlsMount(root)
  });
  var documentShell = renderDocsViewerDocumentShell({
    document: documentRef,
    root: root,
    mount: settings.documentShellMount || documentShellMount(root)
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
  var mount = settings.managementActionsMount || settings.mount || managementActionsMount(root);
  if (!mount) {
    return Promise.resolve({
      headerControls: headerControls,
      documentShell: documentShell,
      infoPanel: infoPanel,
      indexPanel: indexPanel,
      routeContext: routeContext,
      managementActions: null
    });
  }

  mount.replaceChildren();
  if (!managementAllowed(routeContext)) {
    return Promise.resolve({
      headerControls: headerControls,
      documentShell: documentShell,
      infoPanel: infoPanel,
      indexPanel: indexPanel,
      routeContext: routeContext,
      managementActions: null
    });
  }

  return import("./docs-viewer-management-actions-renderer.js")
    .then(function (module) {
      var row = module.renderDocsViewerManagementActions({
        document: documentRef,
        mount: mount
      });
      return {
        headerControls: headerControls,
        documentShell: documentShell,
        infoPanel: infoPanel,
        indexPanel: indexPanel,
        routeContext: routeContext,
        managementActions: row
      };
    })
    .catch(function (error) {
      console.warn("docs_viewer: management action shell failed to initialize", error);
      return {
        headerControls: headerControls,
        documentShell: documentShell,
        infoPanel: infoPanel,
        indexPanel: indexPanel,
        routeContext: routeContext,
        managementActions: null
      };
    });
}

export function getDocsViewerAppShellDocumentRefs(options) {
  var settings = options || {};
  return findDocsViewerDocumentShellRefs({
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

export function getDocsViewerAppShellRefs(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var root = settings.root || null;
  return {
    headerControls: {
      scopeSelect: documentRef.getElementById("docsViewerScopeSelect"),
      recentButton: documentRef.getElementById("docsViewerRecentButton"),
      searchInput: documentRef.getElementById("docsViewerSearchInput")
    },
    indexPanel: getDocsViewerAppShellIndexPanelRefs({ root: root, document: documentRef }),
    documentShell: getDocsViewerAppShellDocumentRefs({ root: root, document: documentRef }),
    infoPanel: getDocsViewerAppShellInfoPanelRefs({ root: root, document: documentRef }),
    status: documentRef.getElementById("docsViewerStatus"),
    bookmarkRow: documentRef.getElementById("docsViewerBookmarkRow"),
    managementActions: {
      mount: documentRef.getElementById("docsViewerManageActionsMount"),
      row: documentRef.getElementById("docsViewerManageRow"),
      actionsButton: documentRef.getElementById("docsViewerManageActionsButton"),
      actionsMenu: documentRef.getElementById("docsViewerManageActionsMenu")
    }
  };
}

export function renderDocsViewerAppShellIndexPanelState(options) {
  applyDocsViewerIndexPanelProjection(options || {});
}

export function renderDocsViewerAppShellDocumentState(options) {
  applyDocsViewerDocumentShellProjection(options || {});
}

export function renderDocsViewerAppShellInfoPanelState(options) {
  applyDocsViewerInfoPanelProjection(options || {});
}
