import {
  documentPackagePrepareCapability,
  documentTransferSourceSupported,
  documentTransferSupported,
  documentTransferTargets,
  scopePublishSupported,
  scopeStaticHtmlExportCapability
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
import {
  openDocsViewerSetPublishableWorkflow
} from "./docs-viewer-management-publishable-workflow.js";
import {
  normalizeManagedDocumentCollectionTarget
} from "./docs-viewer-management-document-target.js";

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

export function docsViewerDocumentTransferActionControlState(options = {}) {
  var mode = String(options.mode || "").trim().toLowerCase();
  var label = mode === "move" ? "Move" : "Copy";
  var resolution = options.resolution || null;
  var targets = Array.isArray(options.targets) ? options.targets : [];
  var disabledReason = "";
  if (!options.managementChecked) {
    disabledReason = "Checking " + label + " availability.";
  } else if (!options.managementAvailable) {
    disabledReason = label + " is unavailable.";
  } else if (options.managementBusy || options.workflowActive) {
    disabledReason = "Docs management is busy.";
  } else if (!resolution || !resolution.enabled) {
    disabledReason = resolution && resolution.disabledReason
      ? resolution.disabledReason
      : "Select one or more documents.";
  } else if (!documentTransferSupported(options.capabilities)) {
    disabledReason = label + " is unavailable.";
  } else if (!documentTransferSourceSupported(options.capabilities, options.source, mode)) {
    disabledReason = label + " is not supported from this collection.";
  } else if (!targets.length) {
    disabledReason = "No other writable Docs Viewer collection is available.";
  }
  return {
    disabled: Boolean(disabledReason),
    disabledReason: disabledReason,
    targets: targets
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
    var capability = scopeStaticHtmlExportCapability(options.capabilities, options.scope);
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

export function docsViewerSetPublishableActionControlState(options = {}) {
  var resolution = options.resolution || null;
  var hidden = !options.managementChecked || !scopePublishSupported(
    options.capabilities,
    options.source && options.source.scope
  );
  var disabledReason = "";
  if (!hidden && !options.managementAvailable) {
    disabledReason = "Set Publishable is unavailable.";
  } else if (!hidden && (options.managementBusy || options.workflowActive)) {
    disabledReason = "Docs management is busy.";
  } else if (!hidden && (!resolution || !resolution.enabled)) {
    disabledReason = resolution && resolution.disabledReason
      ? resolution.disabledReason
      : "Select one or more documents.";
  }
  return {
    hidden: hidden,
    disabled: hidden || Boolean(disabledReason),
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
  var windowRef = options.window || window;
  var openSnapshotExportWorkflow = options.openSnapshotExportWorkflow || openStaticHtmlSnapshotExportWorkflow;
  var openSetPublishableWorkflow = options.openSetPublishableWorkflow || openDocsViewerSetPublishableWorkflow;
  var indexSelection = options.indexSelection || createDocsViewerIndexSelectionOwner({
    initialScopeId: viewerScope()
  });
  var documentTransferWorkflowActive = false;
  var documentTransferWorkflowRequest = null;
  var preparePackageWorkflowRequest = null;
  var snapshotExportWorkflowActive = false;
  var setPublishableWorkflowActive = false;

  function viewerScope() {
    return typeof callbacks.viewerScope === "function" ? callbacks.viewerScope() : "";
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
      scopeId: viewerScope(),
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
    var snapshotCapability = scopeStaticHtmlExportCapability(
      management.managementCapabilities,
      viewerScope()
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
      disabled: Boolean(disabledReason),
      disabledReason: disabledReason
    };
  }

  function documentTransferActionControlState(mode) {
    var actionId = mode === "move" ? DOCS_VIEWER_ACTION_IDS.MOVE : DOCS_VIEWER_ACTION_IDS.COPY;
    var source = { scope: viewerScope() };
    var targets = documentTransferTargets(
      management.managementCapabilities,
      source,
      mode
    );
    return docsViewerDocumentTransferActionControlState({
      capabilities: management.managementCapabilities,
      managementAvailable: management.managementAvailable,
      managementBusy: management.managementBusy,
      managementChecked: management.managementChecked,
      mode: mode,
      resolution: resolveAction(actionId),
      source: source,
      targets: targets,
      workflowActive: documentTransferWorkflowActive
    });
  }

  function snapshotExportActionControlState() {
    return docsViewerStaticHtmlExportActionControlState({
      capabilities: management.managementCapabilities,
      managementBusy: management.managementBusy,
      managementChecked: management.managementChecked,
      resolution: resolveAction(DOCS_VIEWER_ACTION_IDS.EXPORT_DOCS),
      scope: viewerScope(),
      workflowActive: snapshotExportWorkflowActive
    });
  }

  function setPublishableActionControlState(source, resolution) {
    return docsViewerSetPublishableActionControlState({
      capabilities: management.managementCapabilities,
      managementAvailable: management.managementAvailable,
      managementBusy: management.managementBusy,
      managementChecked: management.managementChecked,
      resolution: resolution || resolveAction(DOCS_VIEWER_ACTION_IDS.SET_PUBLISHABLE),
      source: source,
      workflowActive: setPublishableWorkflowActive
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
        [DOCS_VIEWER_ACTION_IDS.SET_PUBLISHABLE]: setPublishableActionControlState({ scope: viewerScope() }),
        [DOCS_VIEWER_ACTION_IDS.COPY]: documentTransferActionControlState("copy"),
        [DOCS_VIEWER_ACTION_IDS.MOVE]: documentTransferActionControlState("move"),
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

  function checkedSelectionHasDescendants(checkedDocIds) {
    var selected = new Set(checkedDocIds || []);
    return documentIndex.docs.some(function (doc) {
      var parentId = String(doc && doc.parent_id || "").trim();
      var seen = new Set();
      while (parentId && !seen.has(parentId)) {
        if (selected.has(parentId)) return true;
        seen.add(parentId);
        var parent = documentIndex.docsById.get(parentId);
        parentId = String(parent && parent.parent_id || "").trim();
      }
      return false;
    });
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
          scope: viewerScope(),
          checkedDocIds: checkedDocIds,
          restoreFocus: restoreFocus,
          activityContext: {
            page_id: "docs-manage",
            action_id: "prepare-document-package",
            route: "/docs/",
            control_id: "docsViewerIndexPreparePackageButton",
            control_selector: "#docsViewerIndexPreparePackageButton",
            correlation_id: "prepare-document-package:" + String(Date.now())
          },
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

  function loadDocumentTransferWorkflow() {
    if (documentTransferWorkflowRequest) return documentTransferWorkflowRequest;
    documentTransferWorkflowRequest = import("./docs-viewer-document-transfer-workflow.js")
      .then(function (module) {
        if (!module || typeof module.openDocumentTransferWorkflow !== "function") {
          throw new Error("Document transfer workflow is unavailable.");
        }
        return module;
      })
      .catch(function (error) {
        documentTransferWorkflowRequest = null;
        throw error;
      });
    return documentTransferWorkflowRequest;
  }

  function openDocumentTransfer(options) {
    var settings = options || {};
    var checkedDocIds = settings.checkedDocIds.slice();
    documentTransferWorkflowActive = true;
    renderManagementUi();
    return loadDocumentTransferWorkflow()
      .then(function (module) {
        return module.openDocumentTransferWorkflow({
          root: root,
          restoreFocus: settings.restoreFocus,
          source: settings.source,
          mode: settings.mode,
          checkedDocIds: checkedDocIds,
          targets: settings.targets,
          copyDescendantsAvailable: settings.copyDescendantsAvailable === true,
          clientOptions: managementClientOptions(),
          callbacks: {
            setBusy: setManagementBusy,
            setMessage: setManagementMessage,
            render: renderManagementUi,
            onApplied: function (payload) {
              var effectiveRoots = Array.isArray(payload && payload.effective_roots)
                ? payload.effective_roots
                : [];
              var targetUrl = String(
                effectiveRoots[0] && effectiveRoots[0].target_viewer_url || ""
              ).trim();
              if (!targetUrl) {
                throw new Error("Document transfer result did not include a target URL.");
              }
              windowRef.location.assign(new URL(targetUrl, windowRef.location.href).toString());
            }
          }
        });
      })
      .catch(function (error) {
        setManagementBusy(false);
        setManagementMessage(
          error && error.message ? error.message : "Document transfer workflow is unavailable.",
          true
        );
        return null;
      })
      .finally(function () {
        documentTransferWorkflowActive = false;
        renderManagementUi();
      });
  }

  function handleDocumentTransfer(mode) {
    var normalizedMode = mode === "move" ? "move" : "copy";
    var actionId = normalizedMode === "move"
      ? DOCS_VIEWER_ACTION_IDS.MOVE
      : DOCS_VIEWER_ACTION_IDS.COPY;
    var resolution = resolveAction(actionId);
    var controlState = documentTransferActionControlState(normalizedMode);
    if (
      !resolution
      || !resolution.enabled
      || controlState.disabled
      || documentTransferWorkflowActive
    ) {
      return Promise.resolve(null);
    }
    var checkedDocIds = resolution.targetDocIds.slice();
    return openDocumentTransfer({
      source: { scope: viewerScope() },
      mode: normalizedMode,
      checkedDocIds: checkedDocIds,
      targets: controlState.targets,
      copyDescendantsAvailable: checkedSelectionHasDescendants(checkedDocIds),
      restoreFocus: indexActionsButton()
    });
  }

  function normalizeSubscopeCopyRequest(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error("Sub-scope Copy request must be an object.");
    }
    var keys = Object.keys(value).sort();
    if (keys.join("\u0000") !== ["doc_ids", "scope", "sub_scope"].join("\u0000")) {
      throw new Error(
        "Sub-scope Copy request must contain exactly scope, sub_scope, and doc_ids."
      );
    }
    var source = normalizeManagedDocumentCollectionTarget({
      scope: value.scope,
      sub_scope: value.sub_scope
    });
    if (!Array.isArray(value.doc_ids) || !value.doc_ids.length) {
      throw new Error("Select one or more documents.");
    }
    var seen = new Set();
    var docIds = value.doc_ids.map(function (docId) {
      if (typeof docId !== "string" || !docId || docId !== docId.trim()) {
        throw new Error("Every checked document id must be exact and non-blank.");
      }
      if (seen.has(docId)) {
        throw new Error("Checked document ids must not contain duplicates.");
      }
      seen.add(docId);
      return docId;
    });
    return { source: source, docIds: docIds };
  }

  function copySubscopeDocuments(request, options) {
    var normalized;
    try {
      normalized = normalizeSubscopeCopyRequest(request);
    } catch (error) {
      return Promise.reject(error);
    }
    var targets = documentTransferTargets(
      management.managementCapabilities,
      normalized.source,
      "copy"
    );
    var controlState = docsViewerDocumentTransferActionControlState({
      capabilities: management.managementCapabilities,
      managementAvailable: management.managementAvailable,
      managementBusy: management.managementBusy,
      managementChecked: management.managementChecked,
      mode: "copy",
      resolution: { enabled: true },
      source: normalized.source,
      targets: targets,
      workflowActive: documentTransferWorkflowActive
    });
    if (controlState.disabled) {
      return Promise.reject(new Error(controlState.disabledReason));
    }
    return openDocumentTransfer({
      source: normalized.source,
      mode: "copy",
      checkedDocIds: normalized.docIds,
      targets: targets,
      copyDescendantsAvailable: false,
      restoreFocus: options && options.restoreFocus
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
      scope: viewerScope(),
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

  function openSetPublishable(source, checkedDocIds, options) {
    var settings = options || {};
    setPublishableWorkflowActive = true;
    renderManagementUi();
    return openSetPublishableWorkflow({
      root: root,
      source: source,
      checkedDocIds: checkedDocIds,
      restoreFocus: settings.restoreFocus,
      clientOptions: managementClientOptions(),
      callbacks: {
        setBusy: setManagementBusy,
        setMessage: setManagementMessage,
        render: renderManagementUi,
        onApplied: settings.onApplied
      }
    }).finally(function () {
      setPublishableWorkflowActive = false;
      renderManagementUi();
    });
  }

  function handleSetPublishable() {
    var resolution = resolveAction(DOCS_VIEWER_ACTION_IDS.SET_PUBLISHABLE);
    var source = { scope: viewerScope() };
    var controlState = setPublishableActionControlState(source);
    if (!resolution || !resolution.enabled || controlState.disabled) {
      return Promise.resolve(null);
    }
    return openSetPublishable(source, resolution.targetDocIds.slice(), {
      restoreFocus: indexActionsButton(),
      onApplied: function () {
        return typeof callbacks.reloadDocsIndex === "function"
          ? callbacks.reloadDocsIndex(activeDocId(), "")
          : null;
      }
    });
  }

  function normalizeSubscopePublishableRequest(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error("Sub-scope Set Publishable request must be an object.");
    }
    var keys = Object.keys(value).sort();
    if (keys.join("\u0000") !== ["doc_ids", "scope", "sub_scope"].join("\u0000")) {
      throw new Error(
        "Sub-scope Set Publishable request must contain exactly scope, sub_scope, and doc_ids."
      );
    }
    var source = normalizeManagedDocumentCollectionTarget({
      scope: value.scope,
      sub_scope: value.sub_scope
    });
    var seen = new Set();
    var docIds = Array.isArray(value.doc_ids)
      ? value.doc_ids.map(function (docId) {
          return String(docId || "").trim();
        }).filter(function (docId) {
          if (!docId || seen.has(docId)) return false;
          seen.add(docId);
          return true;
        })
      : [];
    if (!docIds.length) throw new Error("Select one or more documents.");
    return { source: source, docIds: docIds };
  }

  function setSubscopePublishable(request, options) {
    var normalized;
    try {
      normalized = normalizeSubscopePublishableRequest(request);
    } catch (error) {
      return Promise.reject(error);
    }
    var controlState = setPublishableActionControlState(
      normalized.source,
      { enabled: true, disabledReason: "", targetDocIds: normalized.docIds }
    );
    if (controlState.hidden || controlState.disabled) {
      return Promise.reject(new Error(
        controlState.disabledReason || "Set Publishable is unavailable for this collection."
      ));
    }
    var refreshCollection = options && options.refreshCollection;
    if (typeof refreshCollection !== "function") {
      return Promise.reject(new Error(
        "The exact Set Publishable sub-scope collection cannot be refreshed."
      ));
    }
    return openSetPublishable(normalized.source, normalized.docIds, {
      restoreFocus: options && options.restoreFocus,
      onApplied: function () {
        return refreshCollection(normalized.source);
      }
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
    } else if (actionId === DOCS_VIEWER_ACTION_IDS.SET_PUBLISHABLE) {
      handleSetPublishable();
    } else if (actionId === DOCS_VIEWER_ACTION_IDS.COPY) {
      handleDocumentTransfer("copy");
    } else if (actionId === DOCS_VIEWER_ACTION_IDS.MOVE) {
      handleDocumentTransfer("move");
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
    copySubscopeDocuments: copySubscopeDocuments,
    handleControl: handleControl,
    handleViewChange: handleViewChange,
    indexSelection: indexSelection,
    projectSelection: projectSelection,
    reconcileReload: reconcileReload,
    render: render,
    renderSelectionGutter: renderIndexSelectionGutter,
    setSubscopePublishable: setSubscopePublishable
  };
}
