import {
  documentPackagePrepareCapability,
  stageStaticHtmlExportCapability
} from "./docs-viewer-management-capabilities.js";
import {
  DOCS_VIEWER_ACTION_IDS
} from "./docs-viewer-action-definitions.js";
import {
  createDocsViewerIndexSelectionGutter,
  createDocsViewerIndexSelectionOwner,
  projectDocsViewerIndexSelectionRows
} from "./docs-viewer-index-selection.js";
import {
  openStaticHtmlSnapshotExportWorkflow
} from "./docs-viewer-static-html-export-workflow.js";

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
        : "Select one or more documents.";
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
    var capability = stageStaticHtmlExportCapability(options.capabilities, options.stage);
    if (!capability.available) disabledReason = capability.reason;
    else if (!resolution || !resolution.enabled) {
      disabledReason = resolution && resolution.disabledReason
        ? resolution.disabledReason
        : "Select one or more documents.";
    }
  }
  return {
    disabled: Boolean(disabledReason),
    disabledReason: disabledReason
  };
}

export function createDocsViewerManagementIndexController(options = {}) {
  var root = options.root || null;
  var nav = options.nav || null;
  var documentIndex = options.documentIndex || {};
  var management = options.management || {};
  var routeSession = options.routeSession || {};
  var searchRecent = options.searchRecent || {};
  var callbacks = options.callbacks || {};
  var documentRef = options.document || document;
  var openSnapshotExportWorkflow = options.openSnapshotExportWorkflow || openStaticHtmlSnapshotExportWorkflow;
  var indexSelection = options.indexSelection || createDocsViewerIndexSelectionOwner({
    initialStage: viewerStage()
  });
  var preparePackageWorkflowRequest = null;
  var snapshotExportWorkflowActive = false;

  function viewerStage() {
    return typeof callbacks.viewerStage === "function" ? callbacks.viewerStage() : "";
  }

  function activeDocId() {
    return typeof callbacks.activeDocId === "function"
      ? String(callbacks.activeDocId() || "").trim()
      : "";
  }

  function activeIndexViewId() {
    return typeof callbacks.activeIndexViewId === "function"
      ? String(callbacks.activeIndexViewId() || "").trim()
      : "index-tree";
  }

  function resolveAction(actionId) {
    return typeof callbacks.resolveAction === "function"
      ? callbacks.resolveAction(actionId)
      : null;
  }

  function indexActionsButton() {
    return documentRef.getElementById("docsViewerIndexActionsButton");
  }

  function indexActionsMenu() {
    return documentRef.getElementById("docsViewerIndexActionsMenu");
  }

  function lifecycleContext(indexViewId) {
    return {
      stage: viewerStage(),
      managementContext: routeSession.managementContext,
      indexViewId: arguments.length ? String(indexViewId || "").trim() : activeIndexViewId()
    };
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

  function hideIndexActionsMenu(options) {
    if (typeof callbacks.hideIndexActionsMenu === "function") {
      callbacks.hideIndexActionsMenu(options);
    }
  }

  function toggleIndexActionsMenu() {
    if (typeof callbacks.toggleIndexActionsMenu === "function") {
      callbacks.toggleIndexActionsMenu();
    }
  }

  function indexSelectionAvailable() {
    var snapshotCapability = stageStaticHtmlExportCapability(
      management.managementCapabilities,
      viewerStage()
    );
    return Boolean(
      routeSession.managementContext
      && activeIndexViewId() === "index-tree"
      && management.managementChecked
      && (management.managementAvailable || snapshotCapability.available)
    );
  }

  function eligibleIndexSelectionDocIds() {
    return documentIndex.docs.map(function (doc) {
      return String(doc && doc.doc_id || "").trim();
    }).filter(Boolean);
  }

  function renderIndexSelectionGutter(doc) {
    return createDocsViewerIndexSelectionGutter({
      document: documentRef,
      doc: doc,
      state: indexSelection.snapshot(),
      disabled: !indexSelectionAvailable() || management.managementBusy
    });
  }

  function preparePackageActionControlState() {
    return docsViewerPreparePackageActionControlState({
      capabilities: management.managementCapabilities,
      managementAvailable: management.managementAvailable,
      managementBusy: management.managementBusy,
      managementChecked: management.managementChecked,
      resolution: resolveAction(DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE)
    });
  }

  function deleteActionControlState() {
    var resolution = resolveAction(DOCS_VIEWER_ACTION_IDS.DELETE);
    var disabledReason = "";
    if (!management.managementChecked) {
      disabledReason = "Checking Delete availability.";
    } else if (!management.managementAvailable) {
      disabledReason = "Delete is unavailable.";
    } else if (management.managementBusy) {
      disabledReason = "Docs management is busy.";
    } else if (searchRecent.searchRouteActive) {
      disabledReason = "Clear search to delete documents.";
    } else if (!resolution || !resolution.enabled) {
      disabledReason = resolution ? resolution.disabledReason : "Select one or more documents.";
    }
    return {
      hidden: Boolean(resolution && resolution.hidden),
      disabled: Boolean(disabledReason),
      disabledReason: disabledReason
    };
  }

  function snapshotExportActionControlState() {
    return docsViewerStaticHtmlExportActionControlState({
      capabilities: management.managementCapabilities,
      stage: viewerStage(),
      managementBusy: management.managementBusy,
      managementChecked: management.managementChecked,
      resolution: resolveAction(DOCS_VIEWER_ACTION_IDS.EXPORT_DOCS),
      workflowActive: snapshotExportWorkflowActive
    });
  }

  function projectActions() {
    if (typeof callbacks.projectIndexViewControlState !== "function") return null;
    var visible = Boolean(
      routeSession.managementContext
      && activeIndexViewId() === "index-tree"
    );
    var state = {
      hidden: !visible,
      disabled: false,
      items: {
        [DOCS_VIEWER_ACTION_IDS.EXPORT_DOCS]: snapshotExportActionControlState(),
        [DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE]: preparePackageActionControlState(),
        [DOCS_VIEWER_ACTION_IDS.DELETE]: deleteActionControlState()
      }
    };
    callbacks.projectIndexViewControlState("index-actions", state);
    if (!visible) hideIndexActionsMenu();
    return state;
  }

  function projectSelection() {
    var snapshot = indexSelection.snapshot();
    var available = indexSelectionAvailable();
    var eligibleDocIds = eligibleIndexSelectionDocIds();
    var selectedCount = snapshot.selectedDocIds.length;
    if (typeof callbacks.projectIndexViewControlState === "function") {
      callbacks.projectIndexViewControlState("index-selection", {
        hidden: !available || !snapshot.selectionModeActive,
        disabled: !available || management.managementBusy,
        active: snapshot.selectionModeActive,
        hasSelection: selectedCount > 0,
        allSelected: eligibleDocIds.length > 0 && selectedCount === eligibleDocIds.length,
        total: eligibleDocIds.length,
        label: "Done selecting documents"
      });
    }
    projectDocsViewerIndexSelectionRows({
      nav: nav,
      state: snapshot,
      disabled: !available || management.managementBusy
    });
    projectActions();
    return snapshot;
  }

  function render() {
    indexSelection.syncContext(lifecycleContext());
    return projectSelection();
  }

  function reconcileReload(eligibleDocIds) {
    if (typeof callbacks.isManagementContext === "function") {
      routeSession.managementContext = callbacks.isManagementContext();
    }
    var snapshot = indexSelection.reconcileReload(
      eligibleDocIds,
      lifecycleContext()
    );
    projectSelection();
    return snapshot;
  }

  function handleViewChange(indexViewId) {
    var snapshot = indexSelection.syncContext(lifecycleContext(indexViewId));
    projectSelection();
    return snapshot;
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

  function handlePreparePackage() {
    var resolution = resolveAction(DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE);
    if (!resolution || !resolution.enabled || preparePackageActionControlState().disabled) {
      return Promise.resolve(null);
    }
    var checkedDocIds = resolution.targetDocIds.slice();
    var restoreFocus = indexActionsButton();
    return loadPreparePackageWorkflow()
      .then(function (module) {
        return module.openDocumentPackagePrepareWorkflow({
          root: root,
          stage: viewerStage(),
          checkedDocIds: checkedDocIds,
          restoreFocus: restoreFocus,
          callbacks: {
            hideManageActionsMenu: hideIndexActionsMenu,
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

  function handleSnapshotExport() {
    var resolution = resolveAction(DOCS_VIEWER_ACTION_IDS.EXPORT_DOCS);
    var controlState = snapshotExportActionControlState();
    if (
      !resolution
      || !resolution.enabled
      || controlState.disabled
      || snapshotExportWorkflowActive
    ) {
      return Promise.resolve(null);
    }
    var checkedDocIds = resolution.targetDocIds.slice();
    snapshotExportWorkflowActive = true;
    renderManagementUi();
    return openSnapshotExportWorkflow({
      root: root,
      restoreFocus: indexActionsButton(),
      checkedDocIds: checkedDocIds,
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

  function handleControl(detail) {
    var controlId = String(detail && detail.controlId || "").trim();
    var actionId = String(detail && detail.actionId || "").trim();
    if (controlId === "index-selection") {
      if (String(detail && detail.eventType || "") !== "click") return false;
      var eventTarget = detail && detail.event && detail.event.target;
      var commandTarget = eventTarget && typeof eventTarget.closest === "function"
        ? eventTarget.closest("[data-docs-viewer-selection-command]")
        : null;
      var command = commandTarget ? String(commandTarget.dataset.docsViewerSelectionCommand || "") : "";
      if (!command || !indexSelectionAvailable() || management.managementBusy) return false;
      if (command === "select-all") {
        indexSelection.selectAll(eligibleIndexSelectionDocIds());
      } else if (command === "clear") {
        indexSelection.clear();
      } else if (command === "done") {
        indexSelection.exit();
      } else {
        return false;
      }
      projectSelection();
      return true;
    }
    if (controlId !== "index-actions" || String(detail && detail.eventType || "") !== "click") {
      return false;
    }
    if (!actionId) {
      var menu = indexActionsMenu();
      if (!menu || menu.hidden) {
        var snapshot = indexSelection.snapshot();
        var enteredSelection = !snapshot.selectionModeActive;
        if (enteredSelection) indexSelection.enter();
        var displayedDocId = activeDocId();
        if (
          displayedDocId
          && eligibleIndexSelectionDocIds().indexOf(displayedDocId) !== -1
          && indexSelection.selectedDocIds().indexOf(displayedDocId) === -1
        ) {
          indexSelection.toggle(displayedDocId, true);
        }
        if (enteredSelection && typeof callbacks.renderSidebar === "function") {
          callbacks.renderSidebar();
        }
        projectSelection();
      }
      toggleIndexActionsMenu();
      return true;
    }
    var controlState = projectActions();
    var itemState = controlState && controlState.items[actionId];
    if (!itemState || itemState.disabled) return false;
    hideIndexActionsMenu({ focusButton: true });
    if (actionId === DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE) {
      handlePreparePackage();
    } else if (actionId === DOCS_VIEWER_ACTION_IDS.EXPORT_DOCS) {
      handleSnapshotExport();

    } else if (actionId === DOCS_VIEWER_ACTION_IDS.DELETE) {
      if (typeof callbacks.handleDeleteDoc === "function") callbacks.handleDeleteDoc();
    } else {
      return false;
    }
    return true;
  }

  return {
    actionsButton: indexActionsButton,
    actionsMenu: indexActionsMenu,
    handleControl: handleControl,
    handleViewChange: handleViewChange,
    indexSelection: indexSelection,
    projectSelection: projectSelection,
    reconcileReload: reconcileReload,
    render: render,
    renderSelectionGutter: renderIndexSelectionGutter
  };
}
