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
    metadataHiddenInput: nodeById(documentRef, "docsViewerMetadataHiddenInput"),
    metadataHiddenLabel: nodeById(documentRef, "docsViewerMetadataHiddenLabel"),
    metadataParentInput: nodeById(documentRef, "docsViewerMetadataParentInput"),
    metadataParentPopup: nodeById(documentRef, "docsViewerMetadataParentPopup"),
    metadataSortOrderInput: nodeById(documentRef, "docsViewerMetadataSortOrderInput"),
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
    headerControls: parts.headerControls,
    documentShell: parts.documentShell,
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
  var headerControls = renderDocsViewerHeaderControls({
    document: documentRef,
    root: root,
    mount: settings.headerControlsMount || headerControlsMount(root),
    routeContext: routeContext
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
  var actionMount = settings.managementActionsMount || settings.mount || managementActionsMount(root);
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
      documentShell: documentShell,
      infoPanel: infoPanel,
      indexPanel: indexPanel,
      routeContext: routeContext,
      managementActions: null,
      managementShell: null
    }));
  }

  return Promise.all([
    actionMount ? import("./docs-viewer-management-actions-renderer.js") : Promise.resolve(null),
    shellMount ? import("./docs-viewer-management-shell-renderer.js") : Promise.resolve(null)
  ])
    .then(function (modules) {
      var actionsModule = modules[0];
      var shellModule = modules[1];
      var row = actionsModule ? actionsModule.renderDocsViewerManagementActions({
        document: documentRef,
        mount: actionMount
      }) : null;
      var managementShell = shellModule ? shellModule.renderDocsViewerManagementShell({
        document: documentRef,
        root: root,
        mount: shellMount
      }) : emptyManagementShell(documentRef);
      return appShellResult({
        headerControls: headerControls,
        documentShell: documentShell,
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
        documentShell: documentShell,
        infoPanel: infoPanel,
        indexPanel: indexPanel,
        routeContext: routeContext,
        managementActions: null,
        managementShell: null
      });
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
    indexPanel: getDocsViewerAppShellIndexPanelRefs({ root: root, document: documentRef }),
    documentShell: getDocsViewerAppShellDocumentRefs({ root: root, document: documentRef }),
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

export function renderDocsViewerAppShellDocumentState(options) {
  applyDocsViewerDocumentShellProjection(options || {});
}

export function renderDocsViewerAppShellInfoPanelState(options) {
  applyDocsViewerInfoPanelProjection(options || {});
}
