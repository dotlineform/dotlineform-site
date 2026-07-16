import {
  scopeCreateSupported,
  scopeDeleteSupported,
  scopeDeleteNavigationTarget,
  scopeLifecycleDeleteTargets,
  scopeLifecycleRenameTargets,
  scopeRenameSupported,
  subScopeCreateSupported,
  subScopeDeleteSupported,
  subScopeLifecycleDeleteTargets
} from "./docs-viewer-management-capabilities.js";

var LIFECYCLE_ERROR = "Scope lifecycle unavailable.";

export function createDocsViewerManagementScopeLifecycleController(options = {}) {
  var root = options.root || null;
  var management = options.management || {};
  var callbacks = options.callbacks || {};
  var documentRef = options.document || document;
  var refs = options.refs || {
    createScopeButton: documentRef.getElementById("docsViewerManageNewScopeButton"),
    renameScopeButton: documentRef.getElementById("docsViewerManageRenameScopeButton"),
    deleteScopeButton: documentRef.getElementById("docsViewerManageDeleteScopeButton"),
    createSubScopeButton: documentRef.getElementById("docsViewerManageNewSubScopeButton"),
    deleteSubScopeButton: documentRef.getElementById("docsViewerManageDeleteSubScopeButton")
  };
  var lifecycleRequestPromise = null;

  function viewerScope() {
    return typeof callbacks.viewerScope === "function" ? callbacks.viewerScope() : "";
  }

  function lifecycleCallbacks() {
    return {
      onApplied: function (payload) {
        if (payload && payload.action === "rename_scope" && typeof callbacks.navigateToScope === "function") return;
        if (scopeDeleteNavigationTarget(payload, viewerScope()) && typeof callbacks.navigateToScope === "function") return;
        var reloadConfig = typeof callbacks.reloadViewerConfiguration === "function"
          ? callbacks.reloadViewerConfiguration()
          : Promise.resolve(null);
        if (typeof callbacks.refreshManagementCapabilities === "function") {
          callbacks.refreshManagementCapabilities();
          Promise.resolve(reloadConfig)
            .then(callbacks.refreshManagementCapabilities)
            .catch(callbacks.refreshManagementCapabilities);
        }
      },
      render: callbacks.render,
      setBusy: callbacks.setBusy,
      setMessage: callbacks.setMessage,
      navigateToScope: callbacks.navigateToScope
    };
  }

  function loadLifecycleModule() {
    if (lifecycleRequestPromise) return lifecycleRequestPromise;
    lifecycleRequestPromise = import("./docs-viewer-scope-lifecycle.js")
      .then(function (module) {
        if (
          !module ||
          typeof module.openCreateScopeFlow !== "function" ||
          typeof module.openRenameScopeFlow !== "function" ||
          typeof module.openDeleteScopeFlow !== "function" ||
          typeof module.openCreateSubScopeFlow !== "function" ||
          typeof module.openDeleteSubScopeFlow !== "function"
        ) {
          throw new Error("Docs Viewer scope lifecycle module is unavailable.");
        }
        return module;
      })
      .catch(function (error) {
        lifecycleRequestPromise = null;
        throw error;
      });
    return lifecycleRequestPromise;
  }

  function openFlow(flowName, includeParentScope) {
    if (typeof callbacks.hideContextMenu === "function") callbacks.hideContextMenu();
    if (typeof callbacks.hideManageActionsMenu === "function") callbacks.hideManageActionsMenu();
    return loadLifecycleModule()
      .then(function (module) {
        var flowOptions = {
          root: root,
          activeScope: viewerScope(),
          capabilities: management.managementCapabilities,
          clientOptions: typeof callbacks.managementClientOptions === "function" ? callbacks.managementClientOptions() : {},
          callbacks: lifecycleCallbacks()
        };
        if (includeParentScope) flowOptions.parentScope = viewerScope();
        return module[flowName](flowOptions);
      })
      .catch(function (error) {
        if (typeof callbacks.setMessage === "function") {
          callbacks.setMessage(error && error.message ? error.message : LIFECYCLE_ERROR, true);
        }
        return null;
      });
  }

  function createScope() {
    return openFlow("openCreateScopeFlow", false);
  }

  function deleteScope() {
    return openFlow("openDeleteScopeFlow", false);
  }

  function renameScope() {
    return openFlow("openRenameScopeFlow", false);
  }

  function createSubScope() {
    return openFlow("openCreateSubScopeFlow", true);
  }

  function deleteSubScope() {
    return openFlow("openDeleteSubScopeFlow", true);
  }

  function render() {
    if (refs.createScopeButton) {
      var createScopeAvailable = management.managementAvailable && scopeCreateSupported(management.managementCapabilities);
      refs.createScopeButton.hidden = !createScopeAvailable;
      refs.createScopeButton.disabled = management.managementBusy || !createScopeAvailable;
    }
    if (refs.deleteScopeButton) {
      var deleteScopeAvailable = management.managementAvailable && scopeDeleteSupported(management.managementCapabilities);
      var deleteScopeTargets = scopeLifecycleDeleteTargets(management.managementCapabilities);
      refs.deleteScopeButton.hidden = !deleteScopeAvailable;
      refs.deleteScopeButton.disabled = management.managementBusy || !deleteScopeAvailable || deleteScopeTargets.length === 0;
    }
    if (refs.renameScopeButton) {
      var renameScopeAvailable = management.managementAvailable && scopeRenameSupported(management.managementCapabilities);
      var renameScopeTargets = scopeLifecycleRenameTargets(management.managementCapabilities);
      refs.renameScopeButton.hidden = !renameScopeAvailable;
      refs.renameScopeButton.disabled = management.managementBusy || !renameScopeAvailable || renameScopeTargets.length === 0;
    }
    if (refs.createSubScopeButton) {
      var createSubScopeAvailable = management.managementAvailable && subScopeCreateSupported(management.managementCapabilities, viewerScope());
      refs.createSubScopeButton.hidden = !createSubScopeAvailable;
      refs.createSubScopeButton.disabled = management.managementBusy || !createSubScopeAvailable;
    }
    if (refs.deleteSubScopeButton) {
      var deleteSubScopeAvailable = management.managementAvailable && subScopeDeleteSupported(management.managementCapabilities, viewerScope());
      var deleteSubScopeTargets = subScopeLifecycleDeleteTargets(management.managementCapabilities, viewerScope());
      refs.deleteSubScopeButton.hidden = !deleteSubScopeAvailable;
      refs.deleteSubScopeButton.disabled = management.managementBusy || !deleteSubScopeAvailable || deleteSubScopeTargets.length === 0;
    }
  }

  return {
    createScope: createScope,
    createSubScope: createSubScope,
    deleteScope: deleteScope,
    renameScope: renameScope,
    deleteSubScope: deleteSubScope,
    render: render
  };
}
