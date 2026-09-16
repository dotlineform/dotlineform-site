import {
  collectionCreateSupported,
  collectionDeleteSupported,
  collectionLifecycleDeleteTargets
} from "./docs-viewer-management-capabilities.js";
import {
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

var LIFECYCLE_ERROR = "Collection lifecycle unavailable.";

export function followCreatedCollectionReport(payload, options = {}) {
  var target;
  try {
    target = normalizeManagedDocumentTarget(payload && payload.report_host_target);
    if (
      !payload
      || payload.action !== "create_collection"
      || payload.committed !== true
      || Object.prototype.hasOwnProperty.call(target, "collection")
      || target.stage !== options.activeStage
    ) {
      throw new Error("Created collection report target is invalid.");
    }
  } catch (error) {
    return Promise.reject(
      new Error("Created collection report target is invalid.", { cause: error })
    );
  }
  if (
    typeof options.reloadViewerConfiguration !== "function"
    || typeof options.reloadDocsIndex !== "function"
  ) {
    return Promise.reject(new Error("Created collection report refresh is unavailable."));
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
        "Collection created, but its report could not be opened. " + error.message,
        { cause: error }
      );
    });
}

export function createDocsViewerManagementCollectionLifecycleController(options = {}) {
  var root = options.root || null;
  var management = options.management || {};
  var callbacks = options.callbacks || {};
  var documentRef = options.document || document;
  var refs = options.refs || {
    createCollectionButton: documentRef.getElementById("docsViewerManageNewCollectionButton"),
    deleteCollectionButton: documentRef.getElementById("docsViewerManageDeleteCollectionButton")
  };
  var lifecycleRequestPromise = null;

  function viewerStage() {
    return typeof callbacks.viewerStage === "function" ? callbacks.viewerStage() : "";
  }

  function lifecycleCallbacks() {
    return {
      onApplied: function (payload) {
        if (payload && payload.action === "create_collection") return;
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
      followCreatedCollectionReport: function (payload) {
        return followCreatedCollectionReport(payload, {
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
    lifecycleRequestPromise = import("./docs-viewer-collection-lifecycle.js")
      .then(function (module) {
        if (
          !module ||
          typeof module.openCreateCollectionFlow !== "function" ||
          typeof module.openDeleteCollectionFlow !== "function"
        ) {
          throw new Error("Docs Viewer collection lifecycle module is unavailable.");
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

  function createCollection() {
    return openFlow("openCreateCollectionFlow");
  }

  function deleteCollection() {
    return openFlow("openDeleteCollectionFlow");
  }

  function render() {
    if (refs.createCollectionButton) {
      var createCollectionAvailable = management.managementAvailable && collectionCreateSupported(management.managementCapabilities, viewerStage());
      refs.createCollectionButton.hidden = !createCollectionAvailable;
      refs.createCollectionButton.disabled = management.managementBusy || !createCollectionAvailable;
    }
    if (refs.deleteCollectionButton) {
      var deleteCollectionAvailable = management.managementAvailable && collectionDeleteSupported(management.managementCapabilities, viewerStage());
      var deleteCollectionTargets = collectionLifecycleDeleteTargets(management.managementCapabilities, viewerStage());
      refs.deleteCollectionButton.hidden = !deleteCollectionAvailable;
      refs.deleteCollectionButton.disabled = management.managementBusy || !deleteCollectionAvailable || deleteCollectionTargets.length === 0;
    }
  }

  return {
    createCollection: createCollection,
    deleteCollection: deleteCollection,
    render: render
  };
}
