import {
  renderDocsViewerHeaderControls
} from "./docs-viewer-header-controls-renderer.js";

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
  var mount = settings.managementActionsMount || settings.mount || managementActionsMount(root);
  if (!mount) return Promise.resolve({ headerControls: headerControls, managementActions: null });

  mount.replaceChildren();
  if (!managementAllowed(root)) {
    return Promise.resolve({ headerControls: headerControls, managementActions: null });
  }

  return import("./docs-viewer-management-actions-renderer.js")
    .then(function (module) {
      var row = module.renderDocsViewerManagementActions({
        document: documentRef,
        mount: mount
      });
      return { headerControls: headerControls, managementActions: row };
    })
    .catch(function (error) {
      console.warn("docs_viewer: management action shell failed to initialize", error);
      return { headerControls: headerControls, managementActions: null };
    });
}
