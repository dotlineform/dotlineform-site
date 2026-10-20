import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import { openRecentExclusions } from "./docs-viewer-management-client.js";

export function createDocsViewerManagementIndexController(options = {}) {
  var management = options.management || {};
  var callbacks = options.callbacks || {};

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

  function mutationActionControlState(actionId, targetDocId) {
    var resolution = resolveAction(actionId, targetDocId);
    var label = actionId === DOCS_VIEWER_ACTION_IDS.DELETE ? "Delete"
      : actionId === DOCS_VIEWER_ACTION_IDS.SORT_CHILDREN ? "Sort Children A–Z" : "Position";
    var disabledReason = "";
    var pending = !management.managementChecked || management.managementBusy;
    if (management.managementChecked && !management.managementAvailable) {
      disabledReason = label + " is unavailable.";
    } else if (!pending && activeIndexViewId() !== "index-tree") {
      disabledReason = "Return to the Index tree.";
    } else if (!pending && callbacks.sourceEditingActive()) {
      disabledReason = "Finish source editing before changing the Index.";
    } else if (!pending && (!resolution || !resolution.enabled)) {
      disabledReason = resolution ? resolution.disabledReason : "No Index target document.";
    } else if (!pending && actionId === DOCS_VIEWER_ACTION_IDS.SORT_CHILDREN && callbacks.indexChildren(targetDocId).length < 2) {
      disabledReason = "This document has fewer than two children.";
    }
    return {
      hidden: Boolean(resolution && resolution.hidden),
      disabled: pending || Boolean(disabledReason),
      disabledReason: disabledReason
    };
  }

  function actionControlState(actionId, targetDocId) {
    if ([DOCS_VIEWER_ACTION_IDS.DELETE, DOCS_VIEWER_ACTION_IDS.POSITION, DOCS_VIEWER_ACTION_IDS.SORT_CHILDREN].includes(actionId)) {
      return mutationActionControlState(actionId, targetDocId);
    }
    return null;
  }

  function actionStates(targetDocId) {
    var states = {
      [DOCS_VIEWER_ACTION_IDS.DELETE]: mutationActionControlState(DOCS_VIEWER_ACTION_IDS.DELETE, targetDocId),
      [DOCS_VIEWER_ACTION_IDS.POSITION]: mutationActionControlState(DOCS_VIEWER_ACTION_IDS.POSITION, targetDocId),
      [DOCS_VIEWER_ACTION_IDS.SORT_CHILDREN]: mutationActionControlState(DOCS_VIEWER_ACTION_IDS.SORT_CHILDREN, targetDocId)
    };
    Object.values(DOCS_VIEWER_ACTION_IDS).forEach(function (actionId) {
      if (states[actionId]) return;
      var resolution = resolveAction(actionId, targetDocId);
      states[actionId] = {
        hidden: resolution.hidden,
        disabled: resolution.disabled,
        disabledReason: resolution.disabledReason
      };
    });
    return states;
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
    if (actionId === DOCS_VIEWER_ACTION_IDS.DELETE) {
      callbacks.handleDeleteDoc(targetDocId, restoreFocus);
    } else if (actionId === DOCS_VIEWER_ACTION_IDS.POSITION) {
      callbacks.handlePositionDoc(targetDocId, restoreFocus);
    } else if (actionId === DOCS_VIEWER_ACTION_IDS.SORT_CHILDREN) {
      callbacks.handleSortChildren(targetDocId, restoreFocus);
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
