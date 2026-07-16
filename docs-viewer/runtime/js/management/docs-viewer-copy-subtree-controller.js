import {
  copySubtreeSupported,
  copySubtreeTargetScopes
} from "./docs-viewer-management-capabilities.js";

var COPY_SUBTREE_UNAVAILABLE = "Copy subtree is unavailable.";

export function createDocsViewerCopySubtreeController(options = {}) {
  var root = options.root || null;
  var management = options.management || {};
  var callbacks = options.callbacks || {};
  var workflowModulePromise = null;
  var flowPromise = null;

  function viewerScope() {
    return typeof callbacks.viewerScope === "function" ? callbacks.viewerScope() : "";
  }

  function targets() {
    return copySubtreeTargetScopes(management.managementCapabilities, viewerScope());
  }

  function project(controlState) {
    if (typeof callbacks.projectControlState === "function") {
      callbacks.projectControlState("copy-subtree", controlState);
    }
  }

  function render() {
    var managementContext = typeof callbacks.managementContext === "function"
      ? callbacks.managementContext()
      : true;
    var available = Boolean(
      managementContext &&
      management.managementAvailable &&
      copySubtreeSupported(management.managementCapabilities)
    );
    var sourceDoc = typeof callbacks.currentActiveDoc === "function"
      ? callbacks.currentActiveDoc()
      : null;
    var targetScopes = available ? targets() : [];
    project({
      hidden: !available,
      disabled: Boolean(
        !available ||
        management.managementBusy ||
        flowPromise ||
        !sourceDoc ||
        !targetScopes.length
      ),
      busy: Boolean(flowPromise),
      label: targetScopes.length
        ? "Copy subtree to scope…"
        : "Copy subtree unavailable: no other writable scope"
    });
  }

  function loadWorkflowModule() {
    if (workflowModulePromise) return workflowModulePromise;
    workflowModulePromise = import("./docs-viewer-copy-subtree-workflow.js")
      .then(function (module) {
        if (!module || typeof module.openCopySubtreeFlow !== "function") {
          throw new Error(COPY_SUBTREE_UNAVAILABLE);
        }
        return module;
      })
      .catch(function (error) {
        workflowModulePromise = null;
        throw error;
      });
    return workflowModulePromise;
  }

  function copy(sourceDoc) {
    if (flowPromise) return flowPromise;
    var activeSource = sourceDoc || (
      typeof callbacks.currentActiveDoc === "function" ? callbacks.currentActiveDoc() : null
    );
    if (!activeSource) return Promise.resolve(null);

    flowPromise = loadWorkflowModule().then(function (module) {
      return module.openCopySubtreeFlow({
        root: root,
        sourceDoc: activeSource,
        targets: targets(),
        clientOptions: typeof callbacks.managementClientOptions === "function"
          ? callbacks.managementClientOptions()
          : {},
        callbacks: {
          onApplied: callbacks.onApplied,
          render: callbacks.render,
          setBusy: callbacks.setBusy,
          setMessage: callbacks.setMessage
        }
      });
    }).catch(function (error) {
      if (typeof callbacks.setMessage === "function") {
        callbacks.setMessage(error && error.message ? error.message : COPY_SUBTREE_UNAVAILABLE, true);
      }
      return null;
    }).finally(function () {
      flowPromise = null;
      render();
    });
    render();
    return flowPromise;
  }

  return {
    copy: copy,
    render: render
  };
}
