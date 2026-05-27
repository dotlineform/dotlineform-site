import {
  renderDocsViewerHeaderControls
} from "./docs-viewer-header-controls-renderer.js";
import {
  applyDocsViewerIndexPanelProjection,
  findDocsViewerIndexPanelRefs,
  indexPanelMount,
  renderDocsViewerIndexPanelShell
} from "./docs-viewer-index-panel-renderer.js";

function managementAllowed(root) {
  return Boolean(root && root.dataset.allowManagement === "true");
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
  var headerControls = renderDocsViewerHeaderControls({
    document: documentRef,
    root: root,
    mount: settings.headerControlsMount || headerControlsMount(root)
  });
  var indexPanel = renderDocsViewerIndexPanelShell({
    document: documentRef,
    root: root,
    mount: settings.indexPanelMount || indexPanelMount(root)
  });
  var mount = settings.managementActionsMount || settings.mount || managementActionsMount(root);
  if (!mount) return Promise.resolve({ headerControls: headerControls, indexPanel: indexPanel, managementActions: null });

  mount.replaceChildren();
  if (!managementAllowed(root)) {
    return Promise.resolve({ headerControls: headerControls, indexPanel: indexPanel, managementActions: null });
  }

  return import("./docs-viewer-management-actions-renderer.js")
    .then(function (module) {
      var row = module.renderDocsViewerManagementActions({
        document: documentRef,
        mount: mount
      });
      return { headerControls: headerControls, indexPanel: indexPanel, managementActions: row };
    })
    .catch(function (error) {
      console.warn("docs_viewer: management action shell failed to initialize", error);
      return { headerControls: headerControls, indexPanel: indexPanel, managementActions: null };
    });
}

export function getDocsViewerAppShellIndexPanelRefs(options) {
  var settings = options || {};
  return findDocsViewerIndexPanelRefs({
    document: settings.document || document,
    root: settings.root || null
  });
}

export function renderDocsViewerAppShellIndexPanelState(options) {
  applyDocsViewerIndexPanelProjection(options || {});
}
