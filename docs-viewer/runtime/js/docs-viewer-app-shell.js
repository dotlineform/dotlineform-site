import {
  renderDocsViewerTopBar
} from "./docs-viewer-top-bar-renderer.js";
import {
  applyDocsViewerViewerToolbarProjection
} from "./docs-viewer-viewer-toolbar-renderer.js";
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

function routeContextFor(settings) {
  if (settings.routeContext) return settings.routeContext;
  if (!settings.routeConfig) return null;
  return createDocsViewerRouteContext({
    root: settings.root,
    document: settings.document,
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

function managementShellMount(root) {
  if (!root) return null;
  return root.querySelector("[data-docs-viewer-management-shell-mount]");
}

function nodeById(documentRef, id) {
  return documentRef.getElementById(id);
}

function findDocsViewerManagementShellRefs(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  return {
    contextMenu: nodeById(documentRef, "docsViewerContextMenu"),
    metadataModal: nodeById(documentRef, "docsViewerMetadataModal"),
    metadataForm: nodeById(documentRef, "docsViewerMetadataForm"),
    metadataDocId: nodeById(documentRef, "docsViewerMetadataDocId"),
    metadataTitleInput: nodeById(documentRef, "docsViewerMetadataTitleInput"),
    metadataSummaryInput: nodeById(documentRef, "docsViewerMetadataSummaryInput"),
    metadataStatusLabel: nodeById(documentRef, "docsViewerMetadataStatusLabel"),
    metadataStatusInput: nodeById(documentRef, "docsViewerMetadataStatusInput"),
    metadataNonViewableInput: nodeById(documentRef, "docsViewerMetadataNonViewableInput"),
    metadataNonViewableLabel: nodeById(documentRef, "docsViewerMetadataNonViewableLabel"),
    metadataParentInput: nodeById(documentRef, "docsViewerMetadataParentInput"),
    metadataParentPopup: nodeById(documentRef, "docsViewerMetadataParentPopup"),
    metadataCancelButton: nodeById(documentRef, "docsViewerMetadataCancelButton"),
    metadataSaveButton: nodeById(documentRef, "docsViewerMetadataSaveButton"),
    importModal: nodeById(documentRef, "docsViewerImportModal"),
    importRoot: nodeById(documentRef, "docsHtmlImportRoot"),
    importBootStatus: nodeById(documentRef, "docsHtmlImportBootStatus"),
    settingsModal: nodeById(documentRef, "docsViewerSettingsModal"),
    settingsForm: nodeById(documentRef, "docsViewerSettingsForm"),
    settingsHeading: nodeById(documentRef, "docsViewerSettingsHeading"),
    settingsScope: nodeById(documentRef, "docsViewerSettingsScope"),
    settingsUpdatedInput: nodeById(documentRef, "docsViewerSettingsUpdatedInput"),
    settingsUpdatedLabel: nodeById(documentRef, "docsViewerSettingsUpdatedLabel"),
    settingsWarnings: nodeById(documentRef, "docsViewerSettingsWarnings"),
    settingsStatus: nodeById(documentRef, "docsViewerSettingsStatus"),
    settingsCancelButton: nodeById(documentRef, "docsViewerSettingsCancelButton"),
    settingsSaveButton: nodeById(documentRef, "docsViewerSettingsSaveButton")
  };
}

function emptyManagementShell(documentRef) {
  return findDocsViewerManagementShellRefs({
    document: documentRef
  });
}

function appShellResult(parts) {
  return {
    topBar: parts.topBar,
    viewerToolbar: parts.viewerToolbar,
    headerControls: parts.headerControls,
    mainView: parts.mainView,
    infoPanel: parts.infoPanel,
    indexPanel: parts.indexPanel,
    routeContext: parts.routeContext,
    managementActions: parts.managementActions || null,
    managementShell: parts.managementShell || null
  };
}

export function initDocsViewerAppShell(options) {
  var settings = options || {};
  var root = settings.root;
  var documentRef = settings.document || document;
  var routeContext = routeContextFor(settings);
  var topBar = renderDocsViewerTopBar({
    document: documentRef,
    root: root,
    mount: settings.headerControlsMount || headerControlsMount(root),
    routeContext: routeContext
  });
  var headerControls = topBar && topBar.viewerToolbar;
  var mainView = renderDocsViewerMainView({
    document: documentRef,
    root: root,
    mount: settings.mainViewMount || mainViewMount(root)
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
  var actionMount = settings.managementActionsMount || settings.mount || (topBar && topBar.manageToolbarMount) || managementActionsMount(root);
  var shellMount = settings.managementShellMount || managementShellMount(root);
  if (actionMount) {
    actionMount.replaceChildren();
  }
  if (shellMount) {
    shellMount.replaceChildren();
  }
  if (!managementAllowed(routeContext)) {
    return Promise.resolve(appShellResult({
      headerControls: headerControls,
      topBar: topBar && topBar.topBar,
      viewerToolbar: topBar && topBar.viewerToolbar,
      mainView: mainView,
      infoPanel: infoPanel,
      indexPanel: indexPanel,
      routeContext: routeContext,
      managementActions: null,
      managementShell: null
    }));
  }

  return Promise.all([
    actionMount ? import("./docs-viewer-management-actions-renderer.js") : Promise.resolve(null),
    shellMount ? import("./docs-viewer-management-shell-renderer.js") : Promise.resolve(null),
    import("./docs-viewer-management-document-actions-renderer.js")
  ])
    .then(function (modules) {
      var actionsModule = modules[0];
      var shellModule = modules[1];
      var documentActionsModule = modules[2];
      var row = actionsModule ? actionsModule.renderDocsViewerManagementActions({
        document: documentRef,
        mount: actionMount
      }) : null;
      var managementShell = shellModule ? shellModule.renderDocsViewerManagementShell({
        document: documentRef,
        root: root,
        mount: shellMount
      }) : emptyManagementShell(documentRef);
      if (documentActionsModule && typeof documentActionsModule.renderDocsViewerManagementDocumentActions === "function") {
        documentActionsModule.renderDocsViewerManagementDocumentActions({
          document: documentRef,
          root: root
        });
        mainView = findDocsViewerMainViewRefs({
          document: documentRef,
          root: root
        });
      }
      return appShellResult({
        headerControls: headerControls,
        topBar: topBar && topBar.topBar,
        viewerToolbar: topBar && topBar.viewerToolbar,
        mainView: mainView,
        infoPanel: infoPanel,
        indexPanel: indexPanel,
        routeContext: routeContext,
        managementActions: row,
        managementShell: managementShell
      });
    })
    .catch(function (error) {
      console.warn("docs_viewer: management shell failed to initialize", error);
      return appShellResult({
        headerControls: headerControls,
        topBar: topBar && topBar.topBar,
        viewerToolbar: topBar && topBar.viewerToolbar,
        mainView: mainView,
        infoPanel: infoPanel,
        indexPanel: indexPanel,
        routeContext: routeContext,
        managementActions: null,
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
  return findDocsViewerManagementShellRefs({
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
    topBar: {
      root: documentRef.getElementById("docsViewerTopBar")
    },
    viewerToolbar: {
      root: documentRef.getElementById("docsViewerViewerToolbar"),
      indexViewToggle: documentRef.getElementById("docsViewerIndexViewToggle"),
      infoToggle: documentRef.getElementById("docsViewerInfoToggle")
    },
    indexPanel: getDocsViewerAppShellIndexPanelRefs({ root: root, document: documentRef }),
    mainView: getDocsViewerAppShellMainViewRefs({ root: root, document: documentRef }),
    infoPanel: getDocsViewerAppShellInfoPanelRefs({ root: root, document: documentRef }),
    managementShell: getDocsViewerAppShellManagementShellRefs({ root: root, document: documentRef }),
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

export function renderDocsViewerAppShellMainViewState(options) {
  applyDocsViewerMainViewProjection(options || {});
}

export function renderDocsViewerAppShellViewerToolbarState(options) {
  applyDocsViewerViewerToolbarProjection(options || {});
}

export function renderDocsViewerAppShellInfoPanelState(options) {
  applyDocsViewerInfoPanelProjection(options || {});
}

export function renderDocsViewerAppShellIndexViewToggleState(options) {
  var settings = options || {};
  var refs = settings.refs || {};
  var projection = settings.projection || {};
  var button = refs.indexViewToggle || null;
  if (!button) return;
  var activeViewId = projection.activeViewId || "";
  var targetViewId = projection.nextViewId || "";
  var activeLabel = projection.activeViewLabel || activeViewId || "Index view";
  if (activeViewId === "index-tree") activeLabel = "Tree index view";
  if (activeViewId === "index-graph") activeLabel = "Graph index view";
  button.hidden = Boolean(projection.toggleHidden);
  button.dataset.indexPanelView = targetViewId;
  button.dataset.activeIndexPanelView = activeViewId;
  button.textContent = activeViewId === "index-graph" ? "🕸️" : "📁";
  button.setAttribute("aria-label", activeLabel);
  button.title = activeLabel;
}
