import {
  subScopeCreateSupported,
  subScopeDeleteSupported,
  subScopeLifecycleDeleteTargets
} from "./docs-viewer-management-capabilities.js";
import {
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

var LIFECYCLE_ERROR = "Sub-scope lifecycle unavailable.";

export function followCreatedSubScopeReport(payload, options = {}) {
  var target;
  try {
    target = normalizeManagedDocumentTarget(payload && payload.report_host_target);
    if (
      !payload
      || payload.action !== "create_sub_scope"
      || payload.committed !== true
      || Object.prototype.hasOwnProperty.call(target, "sub_scope")
      || target.stage !== options.activeStage
    ) {
      throw new Error("Created sub-scope report target is invalid.");
    }
  } catch (error) {
    return Promise.reject(
      new Error("Created sub-scope report target is invalid.", { cause: error })
    );
  }
  if (
    typeof options.reloadViewerConfiguration !== "function"
    || typeof options.reloadDocsIndex !== "function"
  ) {
    return Promise.reject(new Error("Created sub-scope report refresh is unavailable."));
  }
  return Promise.resolve()
    .then(options.reloadViewerConfiguration)
    .then(function () {
      return typeof options.refreshManagementCapabilities === "function"
        ? options.refreshManagementCapabilities()
        : null;
    })
    .then(function () {
      return options.reloadDocsIndex(target.doc_id, "");
    })
    .then(function () {
      return target;
    })
    .catch(function (error) {
      throw new Error(
        "Sub-scope created, but its report could not be opened. " + error.message,
        { cause: error }
      );
    });
}

export function createDocsViewerManagementSubScopeLifecycleController(options = {}) {
  var root = options.root || null;
  var management = options.management || {};
  var callbacks = options.callbacks || {};
  var documentRef = options.document || document;
  var refs = options.refs || {
    createSubScopeButton: documentRef.getElementById("docsViewerManageNewSubScopeButton"),
    deleteSubScopeButton: documentRef.getElementById("docsViewerManageDeleteSubScopeButton")
  };
  var lifecycleRequestPromise = null;

  function viewerStage() {
    return typeof callbacks.viewerStage === "function" ? callbacks.viewerStage() : "";
  }

  function lifecycleCallbacks() {
    return {
      onApplied: function (payload) {
        if (payload && payload.action === "create_sub_scope") return;
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
      followCreatedSubScopeReport: function (payload) {
        return followCreatedSubScopeReport(payload, {
          activeStage: typeof callbacks.managementClientOptions === "function" ? callbacks.managementClientOptions().stage : undefined,
          reloadViewerConfiguration: callbacks.reloadViewerConfiguration,
          refreshManagementCapabilities: callbacks.refreshManagementCapabilities,
          reloadDocsIndex: callbacks.reloadDocsIndex
        });
      },
      render: callbacks.render,
      setBusy: callbacks.setBusy,
      setMessage: callbacks.setMessage,
    };
  }

  function loadLifecycleModule() {
    if (lifecycleRequestPromise) return lifecycleRequestPromise;
    lifecycleRequestPromise = import("./docs-viewer-sub-scope-lifecycle.js")
      .then(function (module) {
        if (
          !module ||
          typeof module.openCreateSubScopeFlow !== "function" ||
          typeof module.openDeleteSubScopeFlow !== "function"
        ) {
          throw new Error("Docs Viewer sub-scope lifecycle module is unavailable.");
        }
        return module;
      })
      .catch(function (error) {
        lifecycleRequestPromise = null;
        throw error;
      });
    return lifecycleRequestPromise;
  }

  function openFlow(flowName) {
    if (typeof callbacks.hideContextMenu === "function") callbacks.hideContextMenu();
    if (typeof callbacks.hideManageActionsMenu === "function") callbacks.hideManageActionsMenu();
    return loadLifecycleModule()
      .then(function (module) {
        var flowOptions = {
          root: root,
          capabilities: management.managementCapabilities,
          clientOptions: typeof callbacks.managementClientOptions === "function" ? callbacks.managementClientOptions() : {},
          callbacks: lifecycleCallbacks()
        };
        return module[flowName](flowOptions);
      })
      .catch(function (error) {
        if (typeof callbacks.setMessage === "function") {
          callbacks.setMessage(error && error.message ? error.message : LIFECYCLE_ERROR, true);
        }
        return null;
      });
  }

  function createSubScope() {
    return openFlow("openCreateSubScopeFlow");
  }

  function deleteSubScope() {
    return openFlow("openDeleteSubScopeFlow");
  }

  function render() {
    if (refs.createSubScopeButton) {
      var createSubScopeAvailable = management.managementAvailable && subScopeCreateSupported(management.managementCapabilities, viewerStage());
      refs.createSubScopeButton.hidden = !createSubScopeAvailable;
      refs.createSubScopeButton.disabled = management.managementBusy || !createSubScopeAvailable;
    }
    if (refs.deleteSubScopeButton) {
      var deleteSubScopeAvailable = management.managementAvailable && subScopeDeleteSupported(management.managementCapabilities, viewerStage());
      var deleteSubScopeTargets = subScopeLifecycleDeleteTargets(management.managementCapabilities, viewerStage());
      refs.deleteSubScopeButton.hidden = !deleteSubScopeAvailable;
      refs.deleteSubScopeButton.disabled = management.managementBusy || !deleteSubScopeAvailable || deleteSubScopeTargets.length === 0;
    }
  }

  return {
    createSubScope: createSubScope,
    deleteSubScope: deleteSubScope,
    render: render
  };
}
