import {
  documentPackagePrepareCapability,
  staticHtmlExportCapability
} from "./docs-viewer-management-capabilities.js";
import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import {
  openStaticHtmlSnapshotExportWorkflow
} from "./docs-viewer-static-html-export-workflow.js";
import { openRecentExclusions } from "./docs-viewer-management-client.js";

export function docsViewerPreparePackageActionControlState(options = {}) {
  var resolution = options.resolution || null;
  var disabledReason = "";
  if (!options.managementChecked) {
    disabledReason = "Checking Prepare package availability.";
  } else if (!options.managementAvailable) {
    disabledReason = "Prepare package is unavailable.";
  } else if (options.managementBusy) {
    disabledReason = "Docs management is busy.";
  } else {
    var capability = documentPackagePrepareCapability(options.capabilities);
    if (!capability.available) disabledReason = capability.reason;
    else if (!resolution || !resolution.enabled) {
      disabledReason = resolution && resolution.disabledReason
        ? resolution.disabledReason
        : "No Index target document.";
    }
  }
  return {
    disabled: Boolean(disabledReason),
    disabledReason: disabledReason
  };
}

export function docsViewerStaticHtmlExportActionControlState(options = {}) {
  var resolution = options.resolution || null;
  var disabledReason = "";
  if (!options.managementChecked) {
    disabledReason = "Checking Export availability.";
  } else if (options.managementBusy || options.workflowActive) {
    disabledReason = "Docs management is busy.";
  } else {
    var capability = staticHtmlExportCapability(options.capabilities);
    if (!capability.available) disabledReason = capability.reason;
    else if (!resolution || !resolution.enabled) {
      disabledReason = resolution && resolution.disabledReason
        ? resolution.disabledReason
        : "No Index target document.";
    }
  }
  return {
    disabled: Boolean(disabledReason),
    disabledReason: disabledReason
  };
}

export function createDocsViewerManagementIndexController(options = {}) {
  var root = options.root || null;
  var management = options.management || {};
  var callbacks = options.callbacks || {};
  var openSnapshotExportWorkflow = options.openSnapshotExportWorkflow || openStaticHtmlSnapshotExportWorkflow;
  var preparePackageWorkflowRequest = null;
  var snapshotExportWorkflowActive = false;

  function activeIndexViewId() {
    return typeof callbacks.activeIndexViewId === "function"
      ? String(callbacks.activeIndexViewId() || "").trim()
      : "index-tree";
  }

  function resolveAction(actionId, targetDocId) {
    return typeof callbacks.resolveAction === "function"
      ? callbacks.resolveAction(actionId, targetDocId)
      : null;
  }

  function managementClientOptions() {
    return typeof callbacks.managementClientOptions === "function"
      ? callbacks.managementClientOptions()
      : {};
  }

  function renderManagementUi() {
    if (typeof callbacks.renderManagementUi === "function") callbacks.renderManagementUi();
  }

  function setManagementBusy(busy) {
    if (typeof callbacks.setManagementBusy === "function") callbacks.setManagementBusy(busy);
  }

  function setManagementMessage(message, isError) {
    if (typeof callbacks.setManagementMessage === "function") {
      callbacks.setManagementMessage(message, isError);
    }
  }

  function preparePackageActionControlState(targetDocId) {
    return docsViewerPreparePackageActionControlState({
      capabilities: management.managementCapabilities,
      managementAvailable: management.managementAvailable,
      managementBusy: management.managementBusy,
      managementChecked: management.managementChecked,
      resolution: resolveAction(DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE, targetDocId)
    });
  }

  function mutationActionControlState(actionId, targetDocId) {
    var resolution = resolveAction(actionId, targetDocId);
    var label = actionId === DOCS_VIEWER_ACTION_IDS.DELETE ? "Delete" : "Position";
    var disabledReason = "";
    if (!management.managementChecked) {
      disabledReason = "Checking " + label + " availability.";
    } else if (!management.managementAvailable) {
      disabledReason = label + " is unavailable.";
    } else if (management.managementBusy) {
      disabledReason = "Docs management is busy.";
    } else if (activeIndexViewId() !== "index-tree") {
      disabledReason = "Return to the Index tree.";
    } else if (callbacks.sourceEditingActive()) {
      disabledReason = "Finish source editing before changing the Index.";
    } else if (!resolution || !resolution.enabled) {
      disabledReason = resolution ? resolution.disabledReason : "No Index target document.";
    }
    return {
      hidden: Boolean(resolution && resolution.hidden),
      disabled: Boolean(disabledReason),
      disabledReason: disabledReason
    };
  }

  function snapshotExportActionControlState(targetDocId) {
    return docsViewerStaticHtmlExportActionControlState({
      capabilities: management.managementCapabilities,
      managementBusy: management.managementBusy,
      managementChecked: management.managementChecked,
      resolution: resolveAction(DOCS_VIEWER_ACTION_IDS.EXPORT_DOCS, targetDocId),
      workflowActive: snapshotExportWorkflowActive
    });
  }

  function actionControlState(actionId, targetDocId) {
    if (actionId === DOCS_VIEWER_ACTION_IDS.EXPORT_DOCS) return snapshotExportActionControlState(targetDocId);
    if (actionId === DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE) return preparePackageActionControlState(targetDocId);
    if (actionId === DOCS_VIEWER_ACTION_IDS.DELETE || actionId === DOCS_VIEWER_ACTION_IDS.POSITION) {
      return mutationActionControlState(actionId, targetDocId);
    }
    return null;
  }

  function actionStates(targetDocId) {
    var states = {
      [DOCS_VIEWER_ACTION_IDS.EXPORT_DOCS]: snapshotExportActionControlState(targetDocId),
      [DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE]: preparePackageActionControlState(targetDocId),
      [DOCS_VIEWER_ACTION_IDS.DELETE]: mutationActionControlState(DOCS_VIEWER_ACTION_IDS.DELETE, targetDocId),
      [DOCS_VIEWER_ACTION_IDS.POSITION]: mutationActionControlState(DOCS_VIEWER_ACTION_IDS.POSITION, targetDocId)
    };
    Object.values(DOCS_VIEWER_ACTION_IDS).forEach(function (actionId) {
      var policy = callbacks.documentActionState(actionId, { doc_id: targetDocId });
      var state = states[actionId] || {};
      states[actionId] = {
        hidden: policy.hidden || Boolean(state.hidden),
        disabled: policy.disabled || Boolean(state.disabled),
        disabledReason: policy.reason || state.disabledReason || ""
      };
    });
    return states;
  }

  function loadPreparePackageWorkflow() {
    if (preparePackageWorkflowRequest) return preparePackageWorkflowRequest;
    preparePackageWorkflowRequest = import("../packages/document-package-prepare-workflow.js")
      .then(function (module) {
        if (!module || typeof module.openDocumentPackagePrepareWorkflow !== "function") {
          throw new Error("Prepare package workflow is unavailable.");
        }
        return module;
      })
      .catch(function (error) {
        preparePackageWorkflowRequest = null;
        throw error;
      });
    return preparePackageWorkflowRequest;
  }

  function handlePreparePackage(resolution, targetDocument, restoreFocus) {
    var docIds = resolution.targetDocIds.slice(0, 1);
    setManagementBusy(true);
    renderManagementUi();
    return loadPreparePackageWorkflow()
      .then(function (module) {
        return module.openDocumentPackagePrepareWorkflow({
          root: root,
          docIds: docIds,
          targetDocument: targetDocument,
          restoreFocus: restoreFocus,
          callbacks: {
            setBusy: function (busy) {
              setManagementBusy(busy);
              renderManagementUi();
            },
            setMessage: setManagementMessage
          }
        });
      })
      .catch(function (error) {
        setManagementBusy(false);
        setManagementMessage(
          error && error.message ? error.message : "Prepare package workflow is unavailable.",
          true
        );
        return null;
      });
  }

  function handleSnapshotExport(resolution, targetDocument, restoreFocus) {
    var docIds = resolution.targetDocIds.slice();
    snapshotExportWorkflowActive = true;
    renderManagementUi();
    return openSnapshotExportWorkflow({
      root: root,
      restoreFocus: restoreFocus,
      docIds: docIds,
      targetDocument: targetDocument,
      clientOptions: managementClientOptions(),
      callbacks: {
        setBusy: setManagementBusy,
        setMessage: setManagementMessage,
        render: renderManagementUi,
        onApplied: function () {
          if (typeof callbacks.refreshManagementCapabilities === "function") {
            return callbacks.refreshManagementCapabilities();
          }
          return null;
        }
      }
    }).catch(function (error) {
      setManagementBusy(false);
      setManagementMessage(
        error && error.message ? error.message : "Snapshot Export failed.",
        true
      );
      return null;
    }).finally(function () {
      snapshotExportWorkflowActive = false;
      renderManagementUi();
    });
  }

  async function handleOpenRecentExclusions() {
    setManagementBusy(true);
    setManagementMessage("", false);
    renderManagementUi();
    try {
      await openRecentExclusions(managementClientOptions());
    } catch (error) {
      setManagementMessage(error.message || "Could not open Recent exclusions in VS Code.", true);
    } finally {
      setManagementBusy(false);
      renderManagementUi();
    }
  }

  function handleIndexViewControl(detail) {
    if (!detail || detail.controlId !== "open-recent-exclusions" || activeIndexViewId() !== "recent-results") return false;
    if (!management.managementChecked || !management.managementAvailable || management.managementBusy) return false;
    handleOpenRecentExclusions();
    return true;
  }

  function handleAction(actionId, targetDocId, restoreFocus) {
    if (activeIndexViewId() !== "index-tree") return false;
    if (management.managementBusy) return false;
    var itemState = actionControlState(actionId, targetDocId);
    if (!itemState || itemState.disabled) return false;
    var resolution = resolveAction(actionId, targetDocId);
    var targetDocument = callbacks.indexDocument(targetDocId);
    if (!targetDocument || !resolution || !resolution.enabled) return false;
    if (actionId === DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE) {
      handlePreparePackage(resolution, targetDocument, restoreFocus);
    } else if (actionId === DOCS_VIEWER_ACTION_IDS.EXPORT_DOCS) {
      handleSnapshotExport(resolution, targetDocument, restoreFocus);
    } else if (actionId === DOCS_VIEWER_ACTION_IDS.DELETE) {
      callbacks.handleDeleteDoc(targetDocId, restoreFocus);
    } else if (actionId === DOCS_VIEWER_ACTION_IDS.POSITION) {
      callbacks.handlePositionDoc(targetDocId, restoreFocus);
    } else {
      return false;
    }
    return true;
  }

  return {
    actionControlState: actionControlState,
    actionStates: actionStates,
    handleAction: handleAction,
    handleIndexViewControl: handleIndexViewControl
  };
}
