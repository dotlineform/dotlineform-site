function managementAllowed(root) {
  return Boolean(root && root.dataset.allowManagement === "true");
}

function managementActionsMount(root) {
  if (!root) return null;
  return root.querySelector("[data-docs-viewer-management-actions-mount]");
}

export function initDocsViewerAppShell(options) {
  var settings = options || {};
  var root = settings.root;
  var mount = settings.mount || managementActionsMount(root);
  if (!mount) return Promise.resolve({ managementActions: null });

  mount.replaceChildren();
  if (!managementAllowed(root)) {
    return Promise.resolve({ managementActions: null });
  }

  return import("./docs-viewer-management-actions-renderer.js")
    .then(function (module) {
      var row = module.renderDocsViewerManagementActions({
        document: settings.document || document,
        mount: mount
      });
      return { managementActions: row };
    })
    .catch(function (error) {
      console.warn("docs_viewer: management action shell failed to initialize", error);
      return { managementActions: null };
    });
}
