import {
  scopeCreateSupported,
  scopeDeleteSupported,
  scopeLifecycleDeleteTargets,
  subScopeCreateSupported,
  subScopeDeleteSupported,
  subScopeLifecycleDeleteTargets
} from "./docs-viewer-management-capabilities.js";

var LIFECYCLE_ERROR = "Scope lifecycle unavailable.";

export function createDocsViewerManagementScopeLifecycleController(options = {}) {
  var root = options.root || null;
  var state = options.state || {};
  var callbacks = options.callbacks || {};
  var documentRef = options.document || document;
  var refs = options.refs || {
    createScopeButton: documentRef.getElementById("docsViewerManageNewScopeButton"),
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
      onApplied: function () {
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
      setMessage: callbacks.setMessage
    };
  }

  function loadLifecycleModule() {
    if (lifecycleRequestPromise) return lifecycleRequestPromise;
    lifecycleRequestPromise = import("./docs-viewer-scope-lifecycle.js")
      .then(function (module) {
        if (
          !module ||
          typeof module.openCreateScopeFlow !== "function" ||
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
          capabilities: state.managementCapabilities,
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

  function createSubScope() {
    return openFlow("openCreateSubScopeFlow", true);
  }

  function deleteSubScope() {
    return openFlow("openDeleteSubScopeFlow", true);
  }

  function render() {
    if (refs.createScopeButton) {
      var createScopeAvailable = state.managementAvailable && scopeCreateSupported(state.managementCapabilities);
      refs.createScopeButton.hidden = !createScopeAvailable;
      refs.createScopeButton.disabled = state.managementBusy || !createScopeAvailable;
    }
    if (refs.deleteScopeButton) {
      var deleteScopeAvailable = state.managementAvailable && scopeDeleteSupported(state.managementCapabilities);
      var deleteScopeTargets = scopeLifecycleDeleteTargets(state.managementCapabilities);
      refs.deleteScopeButton.hidden = !deleteScopeAvailable;
      refs.deleteScopeButton.disabled = state.managementBusy || !deleteScopeAvailable || deleteScopeTargets.length === 0;
    }
    if (refs.createSubScopeButton) {
      var createSubScopeAvailable = state.managementAvailable && subScopeCreateSupported(state.managementCapabilities, viewerScope());
      refs.createSubScopeButton.hidden = !createSubScopeAvailable;
      refs.createSubScopeButton.disabled = state.managementBusy || !createSubScopeAvailable;
    }
    if (refs.deleteSubScopeButton) {
      var deleteSubScopeAvailable = state.managementAvailable && subScopeDeleteSupported(state.managementCapabilities, viewerScope());
      var deleteSubScopeTargets = subScopeLifecycleDeleteTargets(state.managementCapabilities, viewerScope());
      refs.deleteSubScopeButton.hidden = !deleteSubScopeAvailable;
      refs.deleteSubScopeButton.disabled = state.managementBusy || !deleteSubScopeAvailable || deleteSubScopeTargets.length === 0;
    }
  }

  function wireEvents() {
    if (refs.createScopeButton) refs.createScopeButton.addEventListener("click", createScope);
    if (refs.deleteScopeButton) refs.deleteScopeButton.addEventListener("click", deleteScope);
    if (refs.createSubScopeButton) refs.createSubScopeButton.addEventListener("click", createSubScope);
    if (refs.deleteSubScopeButton) refs.deleteSubScopeButton.addEventListener("click", deleteSubScope);
  }

  return {
    createScope: createScope,
    createSubScope: createSubScope,
    deleteScope: deleteScope,
    deleteSubScope: deleteSubScope,
    render: render,
    wireEvents: wireEvents
  };
}
