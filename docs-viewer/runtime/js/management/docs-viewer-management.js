import {
  isDocNonViewable
} from "../shared/docs-viewer-tree.js";
import {
  createDocsViewerManagementCapabilityController,
  documentPackagePrepareCapability,
  scopePublishSupported,
  scopeStaticHtmlExportSupported
} from "./docs-viewer-management-capabilities.js";
import {
  applyDocsViewerManagementConfig
} from "./docs-viewer-management-config.js";
import {
  createDocsViewerManagementEventRouter
} from "./docs-viewer-management-event-router.js";
import {
  createDocsViewerManagementInteractionController
} from "./docs-viewer-management-interactions.js";
import {
  createDocsViewerManagementImportController
} from "./docs-viewer-management-import-controller.js";
import {
  createDocsViewerManagementModalComposition
} from "./docs-viewer-management-modal-composition.js";
import {
  createDocsViewerManagementScopeLifecycleController
} from "./docs-viewer-management-scope-lifecycle-controller.js";
import {
  createDocsViewerCopySubtreeController
} from "./docs-viewer-copy-subtree-controller.js";
import {
  createDocsViewerManagementActionController
} from "./docs-viewer-management-actions.js";
import {
  DOCS_VIEWER_ACTION_IDS,
  createDocsViewerActionContext,
  resolveDocsViewerAction
} from "./docs-viewer-action-definitions.js";
import {
  createDocsViewerIndexSelectionGutter,
  createDocsViewerIndexSelectionOwner,
  projectDocsViewerIndexSelectionRows
} from "./docs-viewer-index-selection.js";

var MANAGEMENT_TEXT = {
  checkingNote: "Checking manage mode...",
  clearSearchNote: "Clear search to manage the current doc.",
  unavailableNote: "Docs management service unavailable."
};

export function createDocsViewerManagementActionContext(options = {}) {
  var selectedDocument = options.selectedDocument || {};
  var indexSelection = options.indexSelection || createDocsViewerIndexSelectionOwner();
  var contextOptions = {
    activeDocId: selectedDocument.selectedDocId,
    selectedDocIds: indexSelection.selectedDocIds()
  };
  if (Object.prototype.hasOwnProperty.call(options, "invocationDocId")) {
    contextOptions.invocationDocId = options.invocationDocId;
  }
  return createDocsViewerActionContext(contextOptions);
}

export function createDocsViewerManagementActionResolver(options = {}) {
  var selectedDocument = options.selectedDocument || {};
  var indexSelection = options.indexSelection || createDocsViewerIndexSelectionOwner();

  return function resolveAction(actionId, targetDocId) {
    var contextOptions = {
      indexSelection: indexSelection,
      selectedDocument: selectedDocument
    };
    if (arguments.length > 1) contextOptions.invocationDocId = targetDocId;
    return resolveDocsViewerAction(
      actionId,
      createDocsViewerManagementActionContext(contextOptions)
    );
  };
}

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

export function projectDocsViewerPreparePackageActionControl(button, state) {
  if (!button) return null;
  var controlState = state || { disabled: true, disabledReason: "Prepare package is unavailable." };
  var label = "Prepare package";
  var accessibleLabel = controlState.disabledReason ? label + ". " + controlState.disabledReason : label;
  button.disabled = Boolean(controlState.disabled);
  button.title = accessibleLabel;
  button.setAttribute("aria-label", accessibleLabel);
  if (controlState.disabledReason) {
    button.dataset.docsViewerDisabledReason = controlState.disabledReason;
  } else {
    delete button.dataset.docsViewerDisabledReason;
  }
  return controlState;
}

export function initDocsViewerManagement(context) {
  var root = context.root;
  var nav = context.nav;
  var managementState = context.managementState || {};
  var domains = managementState.domains || {};
  var documentIndex = domains.documentIndex || {};
  var management = domains.management || {};
  var routeSession = domains.routeSession || {};
  var scopeConfig = domains.scopeConfig || {};
  var searchRecent = domains.searchRecent || {};
  var selectedDocument = domains.selectedDocument || {};
  var serviceClient = context.serviceClient || {};
  var routeReload = context.routeReload || {};
  context = Object.assign({}, context, {
    docsViewerConfigUrl: serviceClient.docsViewerConfigUrl || context.docsViewerConfigUrl,
    managementBaseUrl: serviceClient.managementBaseUrl || context.managementBaseUrl,
    reloadViewerConfiguration: routeReload.reloadViewerConfiguration || context.reloadViewerConfiguration,
    routeCommands: routeReload.routeCommands || context.routeCommands
  });
  var shellRefs = context.managementShellRefs || {};
  function shellRef(name, id) {
    return shellRefs[name] || document.getElementById(id);
  }
  var manageRow = document.getElementById("docsViewerManageRow");
  var manageActions = manageRow ? manageRow.querySelector(".docsViewer__manageActions") : null;
  var manageActionsButton = document.getElementById("docsViewerManageActionsButton");
  var manageActionsMenu = document.getElementById("docsViewerManageActionsMenu");
  var manageScopeLinks = manageActionsMenu
    ? Array.from(manageActionsMenu.querySelectorAll("[data-docs-viewer-scope-href]"))
    : [];
  var manageRebuildButton = document.getElementById("docsViewerManageRebuildButton");
  var manageSettingsButton = document.getElementById("docsViewerManageSettingsButton");
  var managePublishButton = document.getElementById("docsViewerManagePublishButton");
  var manageToolbarPublishButton = document.getElementById("docsViewerManageToolbarPublishButton");
  var managePublishButtons = [managePublishButton, manageToolbarPublishButton].filter(Boolean);
  var manageExportButton = document.getElementById("docsViewerManageExportButton");
  var manageImportButton = document.getElementById("docsViewerManageImportButton");
  var manageToolbarImportButton = document.getElementById("docsViewerManageToolbarImportButton");
  var manageImportButtons = [manageImportButton, manageToolbarImportButton].filter(Boolean);
  var managePreparePackageButton = document.getElementById("docsViewerManagePreparePackageButton");
  var manageNewButton = document.getElementById("docsViewerManageNewButton");
  var manageDeleteButton = document.getElementById("docsViewerManageDeleteButton");
  var manageViewableButton = document.getElementById("docsViewerManageViewableButton");
  var draftToggle = document.getElementById("docsViewerDraftToggle");
  var importRoot = shellRef("importRoot", "docsHtmlImportRoot");
  var importBootStatus = shellRef("importBootStatus", "docsHtmlImportBootStatus");
  var capabilityController = null;
  var copySubtreeController = null;
  var eventRouter = null;
  var importController = null;
  var interactionController = null;
  var metadataWorkflow = null;
  var modalController = null;
  var preparePackageWorkflowRequest = null;
  var scopeLifecycleController = null;
  var settingsWorkflow = null;
  var actionController = null;
  var indexSelection = createDocsViewerIndexSelectionOwner({
    initialScopeId: viewerScope()
  });

  function viewerScope() {
    return context.viewerScope();
  }

  function activeIndexViewId() {
    return typeof context.activeIndexViewId === "function"
      ? String(context.activeIndexViewId() || "").trim()
      : "index-tree";
  }

  function indexSelectionLifecycleContext(indexViewId) {
    return {
      scopeId: viewerScope(),
      managementContext: routeSession.managementContext,
      indexViewId: arguments.length ? String(indexViewId || "").trim() : activeIndexViewId()
    };
  }

  function syncManageScopeLinks() {
    var scope = String(viewerScope() || "").trim();
    manageScopeLinks.forEach(function (link) {
      var baseHref = String(link.dataset.docsViewerScopeHref || "").trim();
      if (!baseHref) return;
      link.href = scope ? baseHref + "?scope=" + encodeURIComponent(scope) : baseHref;
    });
  }

  function managementClientOptions() {
    return {
      baseUrl: serviceClient.managementBaseUrl || context.managementBaseUrl,
      scope: viewerScope(),
      fetch: function (url, options) {
        return window.fetch(url, options);
      }
    };
  }

  function currentActiveDoc() {
    return documentIndex.docsById.get(selectedDocument.selectedDocId) || null;
  }

  var resolveAction = createDocsViewerManagementActionResolver({
    indexSelection: indexSelection,
    selectedDocument: selectedDocument
  });

  function actionTargetDoc(resolution) {
    if (!resolution || !resolution.enabled || resolution.targetDocIds.length !== 1) return null;
    return documentIndex.docsById.get(resolution.targetDocIds[0]) || null;
  }

  function currentContextMenuDoc() {
    return interactionController ? interactionController.currentContextMenuDoc() : null;
  }

  function canDragCurrentDoc(doc) {
    return Boolean(interactionController && interactionController.canDragCurrentDoc(doc));
  }

  function clearDragState() {
    if (interactionController) interactionController.clearDragState();
  }

  function hideContextMenu() {
    if (interactionController) interactionController.hideContextMenu();
  }

  function setManagementBusy(busy) {
    management.managementBusy = Boolean(busy);
    if (root) {
      root.dataset.managementBusy = management.managementBusy ? "true" : "false";
    }
  }

  function updateNavDragState() {
    if (interactionController) interactionController.updateNavDragState();
  }

  function managementNoteText() {
    if (management.managementMessage) return management.managementMessage;
    if (searchRecent.searchRouteActive) {
      return MANAGEMENT_TEXT.clearSearchNote;
    }
    return "";
  }

  function syncManagementStatus(noteText, isError) {
    var text = String(noteText || "");
    var hasManagementStatus = Boolean(text);
    if (hasManagementStatus || management.managementStatusOwnsViewerStatus) {
      context.setStatus(text, Boolean(isError));
    }
    management.managementStatusOwnsViewerStatus = hasManagementStatus;
  }

  function projectDocumentActionButtons(hidden, disabled) {
    var actionsHidden = Boolean(hidden);
    var actionsDisabled = Boolean(disabled);
    var documentMode = root && root.dataset ? String(root.dataset.documentDisplayMode || "") : "";
    var markdownMode = documentMode === "markdown-source";
    if (typeof context.projectMainViewControlState === "function") {
      context.projectMainViewControlState("edit", {
        hidden: actionsHidden,
        disabled: actionsDisabled
      });
      context.projectMainViewControlState("open-vscode", {
        hidden: actionsHidden,
        disabled: actionsDisabled
      });
      context.projectMainViewControlState("markdown-source", {
        hidden: actionsHidden,
        disabled: actionsDisabled,
        pressed: markdownMode,
        label: markdownMode ? "Show rendered document" : "Show Markdown source"
      });
      context.projectMainViewControlState("save-markdown-source", {
        hidden: actionsHidden,
        disabled: actionsDisabled
      });
      context.projectMainViewControlState("source-add-image", {
        hidden: actionsHidden || !markdownMode,
        disabled: actionsDisabled
      });
      context.projectMainViewControlState("source-add-file", {
        hidden: actionsHidden || !markdownMode,
        disabled: actionsDisabled
      });
    }
  }

  function projectAppControl(controlId, controlState) {
    if (typeof context.projectAppManagementControlState === "function") {
      context.projectAppManagementControlState(controlId, controlState);
    }
  }

  function hideAppManagementControls() {
    [
      "manage-import",
      "manage-actions",
      "manage-publish",
      "manage-show",
      "manage-show-non-viewable",
      "manage-scope",
      "manage-theme"
    ].forEach(function (controlId) {
      projectAppControl(controlId, { hidden: true, disabled: true });
    });
  }

  function indexSelectionAvailable() {
    return Boolean(
      routeSession.managementContext
      && activeIndexViewId() === "index-tree"
      && management.managementChecked
      && management.managementAvailable
    );
  }

  function renderIndexSelectionGutter(doc) {
    return createDocsViewerIndexSelectionGutter({
      document: document,
      doc: doc,
      state: indexSelection.snapshot(),
      disabled: !indexSelectionAvailable() || management.managementBusy
    });
  }

  function projectIndexSelection() {
    var snapshot = indexSelection.snapshot();
    var available = indexSelectionAvailable();
    if (typeof context.projectIndexViewControlState === "function") {
      context.projectIndexViewControlState("index-selection", {
        hidden: !available,
        disabled: !available || management.managementBusy,
        active: snapshot.selectionModeActive,
        count: snapshot.selectedDocIds.length,
        label: snapshot.selectionModeActive ? "Done selecting documents" : "Select documents"
      });
    }
    projectDocsViewerIndexSelectionRows({
      nav: nav,
      state: snapshot,
      disabled: !available || management.managementBusy
    });
    projectPreparePackageAction();
    return snapshot;
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

  function projectPreparePackageAction() {
    return projectDocsViewerPreparePackageActionControl(
      managePreparePackageButton,
      preparePackageActionControlState()
    );
  }

  function reconcileIndexSelectionReload(eligibleDocIds) {
    routeSession.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    var snapshot = indexSelection.reconcileReload(
      eligibleDocIds,
      indexSelectionLifecycleContext()
    );
    projectIndexSelection();
    return snapshot;
  }

  function handleIndexViewChange(indexViewId) {
    var snapshot = indexSelection.syncContext(indexSelectionLifecycleContext(indexViewId));
    projectIndexSelection();
    return snapshot;
  }

  function handleMainViewControl(detail) {
    var controlId = String(detail && detail.controlId || "").trim();
    var actionId = String(detail && detail.actionId || "").trim();
    var resolution = actionId ? resolveAction(actionId) : null;
    if (actionId && (!resolution || !resolution.enabled)) return false;
    var owners = new Map([
      ["edit", function () {
        var doc = actionTargetDoc(resolution);
        if (doc) metadataWorkflow.openForDocId(doc.doc_id);
      }],
      ["open-vscode", function () { actionController.handleOpenSource("vscode"); }],
      ["markdown-source", function () { actionController.handleMarkdownSource(); }],
      ["save-markdown-source", function () { actionController.handleMarkdownSave(); }],
      ["source-add-image", function () {
        if (root && typeof root.dispatchEvent === "function") {
          root.dispatchEvent(new CustomEvent("docs-viewer-source-editor-add-image", { bubbles: true }));
        }
      }],
      ["source-add-file", function () {
        if (root && typeof root.dispatchEvent === "function") {
          root.dispatchEvent(new CustomEvent("docs-viewer-source-editor-add-file", { bubbles: true }));
        }
      }]
    ]);
    var owner = owners.get(controlId);
    if (!owner) return false;
    owner();
    return true;
  }

  function handleIndexViewControl(detail) {
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
      if (command === "enter") {
        indexSelection.enter();
        if (typeof context.renderSidebar === "function") context.renderSidebar();
      } else if (command === "clear") {
        indexSelection.clear();
      } else if (command === "done") {
        indexSelection.exit();
      } else {
        return false;
      }
      projectIndexSelection();
      return true;
    }
    if (controlId !== "copy-subtree" || actionId !== DOCS_VIEWER_ACTION_IDS.COPY_SUBTREE) return false;
    var resolution = resolveAction(actionId);
    var sourceDoc = actionTargetDoc(resolution);
    if (!sourceDoc || !copySubtreeController) return false;
    copySubtreeController.copy(sourceDoc);
    return true;
  }

  function handleAppManagementControl(detail) {
    var actionId = String(detail && detail.actionId || "").trim();
    if (actionId && !resolveAction(actionId).enabled) return false;
    if (
      actionId === DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE
      && preparePackageActionControlState().disabled
    ) return false;
    return eventRouter.handleAppManagementControl(detail);
  }

  function renderManagementUi() {
    if (!manageRow) return;

    routeSession.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    indexSelection.syncContext(indexSelectionLifecycleContext());
    syncManageScopeLinks();
    projectIndexSelection();
    if (!routeSession.managementContext) {
      syncManagementStatus("", false);
      hideAppManagementControls();
      projectDocumentActionButtons(true, true);
      if (copySubtreeController) copySubtreeController.render();
      eventRouter.hideManageActionsMenu();
      return;
    }

    manageRow.hidden = false;
    var managementActionsHidden = !management.managementChecked || !management.managementAvailable;
    if (manageActions) {
      manageActions.hidden = !management.managementChecked || !management.managementAvailable;
      if (manageActions.hidden) {
        eventRouter.hideManageActionsMenu();
      }
    }

    var noteText = "";
    var noteIsError = false;
    if (!management.managementChecked) {
      noteText = MANAGEMENT_TEXT.checkingNote;
    } else if (!management.managementAvailable) {
      noteText = management.managementCapabilityError || MANAGEMENT_TEXT.unavailableNote;
      noteIsError = true;
    } else {
      noteText = managementNoteText();
      noteIsError = management.managementMessageIsError;
    }
    syncManagementStatus(noteText, noteIsError);
    if (copySubtreeController) copySubtreeController.render();

    if (!manageRebuildButton || !manageNewButton || !manageDeleteButton || !manageViewableButton) return;

    var editAction = resolveAction(DOCS_VIEWER_ACTION_IDS.EDIT_METADATA);
    var deleteAction = resolveAction(DOCS_VIEWER_ACTION_IDS.DELETE);
    var showAction = resolveAction(DOCS_VIEWER_ACTION_IDS.SHOW);
    var showDoc = actionTargetDoc(showAction);
    var draftDoc = Boolean(showDoc && isDocNonViewable(showDoc));
    var editDisabled = (
      management.managementBusy ||
      !editAction.enabled ||
      searchRecent.searchRouteActive
    );
    var deleteDisabled = (
      management.managementBusy ||
      !deleteAction.enabled ||
      searchRecent.searchRouteActive
    );
    var viewableDisabled = (
      management.managementBusy ||
      !showAction.enabled ||
      searchRecent.searchRouteActive ||
      !draftDoc
    );
    var publishAvailable = management.managementAvailable && scopePublishSupported(management.managementCapabilities, viewerScope());
    var exportAvailable = management.managementAvailable && scopeStaticHtmlExportSupported(management.managementCapabilities, viewerScope());
    var themeIsDark = document.documentElement && document.documentElement.getAttribute("data-theme") === "dark";

    projectAppControl("manage-import", {
      hidden: managementActionsHidden,
      disabled: management.managementBusy || !management.managementAvailable
    });
    projectAppControl("manage-actions", {
      hidden: managementActionsHidden,
      disabled: management.managementBusy || !management.managementAvailable
    });
    projectAppControl("manage-publish", {
      hidden: managementActionsHidden || !publishAvailable,
      disabled: management.managementBusy || !publishAvailable
    });
    projectAppControl("manage-show", {
      hidden: managementActionsHidden,
      disabled: !management.managementAvailable || viewableDisabled
    });
    projectAppControl("manage-show-non-viewable", {
      hidden: managementActionsHidden,
      disabled: !management.managementAvailable || management.managementBusy,
      pressed: documentIndex.showNonViewable
    });
    projectAppControl("manage-scope", { hidden: managementActionsHidden });
    projectAppControl("manage-theme", {
      hidden: false,
      pressed: themeIsDark,
      label: themeIsDark ? "Switch to light mode" : "Switch to dark mode"
    });

    manageRebuildButton.disabled = management.managementBusy || !management.managementAvailable;
    if (manageActionsButton) {
      manageActionsButton.disabled = management.managementBusy || !management.managementAvailable;
      if (manageActionsButton.disabled) {
        eventRouter.hideManageActionsMenu();
      }
    }
    if (scopeLifecycleController) scopeLifecycleController.render();
    managePublishButtons.forEach(function (button) {
      button.disabled = management.managementBusy || !publishAvailable;
    });
    if (manageToolbarPublishButton) manageToolbarPublishButton.hidden = !publishAvailable;
    if (manageExportButton) {
      manageExportButton.hidden = !exportAvailable;
      manageExportButton.disabled = management.managementBusy || !exportAvailable;
    }
    manageImportButtons.forEach(function (button) {
      button.disabled = management.managementBusy || !management.managementAvailable;
    });
    if (manageSettingsButton) {
      manageSettingsButton.disabled = management.managementBusy || !management.managementAvailable;
    }
    manageNewButton.disabled = management.managementBusy || !management.managementAvailable;
    projectDocumentActionButtons(!management.managementChecked || !management.managementAvailable, !management.managementAvailable || editDisabled);
    manageDeleteButton.disabled = !management.managementAvailable || deleteDisabled;
    manageViewableButton.disabled = !management.managementAvailable || viewableDisabled;
    if (draftToggle) {
      draftToggle.disabled = !management.managementAvailable || management.managementBusy;
      draftToggle.checked = documentIndex.showNonViewable;
    }
    if (metadataWorkflow) metadataWorkflow.render();
    if (settingsWorkflow) settingsWorkflow.render();
  }

  function initializeManagement() {
    if (capabilityController) capabilityController.initialize();
  }

  function refreshManagementCapabilities() {
    if (capabilityController) capabilityController.refresh();
  }

  function reloadViewerConfiguration() {
    if (typeof routeReload.reloadViewerConfiguration === "function") {
      return routeReload.reloadViewerConfiguration();
    }
    if (typeof context.reloadViewerConfiguration === "function") {
      return context.reloadViewerConfiguration();
    }
    return Promise.resolve(null);
  }

  function routeCommand(name) {
    var routeCommands = routeReload.routeCommands || context.routeCommands || {};
    return typeof routeCommands[name] === "function" ? routeCommands[name] : null;
  }

  function setRouteHistory(docId, hash, query, mode) {
    var command = routeCommand("setHistory");
    if (command) command(docId, hash, query, mode);
  }

  function loadRouteIndex() {
    var command = routeCommand("loadIndex");
    return command ? command() : Promise.resolve(null);
  }

  function loadRouteDoc(docId, options) {
    var command = routeCommand("loadDoc");
    return command ? command(docId, options) : Promise.resolve(null);
  }

  function reloadDocsIndex(targetDocId, summaryText) {
    selectedDocument.payloadCache.clear();
    searchRecent.searchEntries = [];
    searchRecent.searchLoaded = false;
    searchRecent.searchRequestPromise = null;
    searchRecent.recentEntries = [];
    searchRecent.recentLoaded = false;
    searchRecent.recentRequestPromise = null;
    selectedDocument.reloadNonce = String(Date.now());
    selectedDocument.reloadExpectedDocId = String(targetDocId || "").trim();
    searchRecent.searchQuery = "";
    searchRecent.searchVisibleCount = context.SEARCH_BATCH_SIZE;
    searchRecent.searchRouteActive = false;
    context.cancelSearchDebounce();
    if (context.searchInput) {
      context.searchInput.value = "";
    }

    if (targetDocId) {
      setRouteHistory(targetDocId, "", "", "replace");
    }

    return loadRouteIndex().then(function () {
      context.setStatus("", false);
      renderManagementUi();
    });
  }

  function displayImportedDocument(detail) {
    var importedScope = String(detail && detail.scope || "").trim().toLowerCase();
    var importedDocId = String(detail && detail.docId || "").trim();
    if (!importedDocId) return Promise.resolve();

    if (importedScope && importedScope !== viewerScope()) {
      var url = new URL(window.location.href);
      url.searchParams.set("scope", importedScope);
      url.searchParams.set("doc", importedDocId);
      url.searchParams.delete("import");
      url.searchParams.delete("review_package");
      url.searchParams.delete("q");
      url.hash = "";
      window.location.assign(url.toString());
      return Promise.resolve();
    }

    return reloadDocsIndex(importedDocId, "");
  }

  function setManagementMessage(message, isError) {
    management.managementMessage = String(message || "");
    management.managementMessageIsError = Boolean(isError);
    renderManagementUi();
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
    if (!resolution.enabled || preparePackageActionControlState().disabled) return Promise.resolve(null);
    var checkedDocIds = resolution.targetDocIds.slice();
    return loadPreparePackageWorkflow()
      .then(function (module) {
        return module.openDocumentPackagePrepareWorkflow({
          root: root,
          scope: viewerScope(),
          checkedDocIds: checkedDocIds,
          restoreFocus: managePreparePackageButton,
          callbacks: {
            hideManageActionsMenu: eventRouter.hideManageActionsMenu,
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

  function handleDraftToggleChange() {
    if (!draftToggle) return;
    documentIndex.showNonViewable = Boolean(draftToggle.checked);
    routeSession.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    context.applyDocVisibility();
    reconcileIndexSelectionReload(documentIndex.docs.map(function (doc) { return doc.doc_id; }));
    context.renderSidebar();
    context.renderBookmarkUi();
    renderManagementUi();

    var currentDocId = selectedDocument.selectedDocId;
    var targetDocId = currentDocId && documentIndex.docsById.has(currentDocId) ? currentDocId : context.defaultDocId();
    if (searchRecent.recentModeActive) {
      context.renderRecentMode();
      return;
    }
    if (searchRecent.searchRouteActive) {
      context.renderSearchMode();
      return;
    }
    if (targetDocId) {
      loadRouteDoc(targetDocId, { historyMode: "replace", hash: "" });
    }
  }

  function applyConfig(config) {
    applyDocsViewerManagementConfig({
      config: config,
      context: context,
      scopeConfig: scopeConfig,
      metadataWorkflow: metadataWorkflow
    });
  }

  capabilityController = createDocsViewerManagementCapabilityController({
    management: management,
    routeSession: routeSession,
    context: context,
    callbacks: {
      managementClientOptions: managementClientOptions,
      renderManagementUi: renderManagementUi,
      renderSidebar: context.renderSidebar,
      viewerScope: viewerScope
    }
  });

  copySubtreeController = createDocsViewerCopySubtreeController({
    root: root,
    management: management,
    callbacks: {
      currentActiveDoc: currentActiveDoc,
      managementClientOptions: managementClientOptions,
      managementContext: function () { return routeSession.managementContext; },
      onApplied: function (payload) {
        var targetUrl = String(payload && payload.target_viewer_url || "").trim();
        if (!targetUrl) throw new Error("Copy subtree result did not include a target URL.");
        window.location.assign(new URL(targetUrl, window.location.href).toString());
      },
      projectControlState: context.projectIndexViewControlState,
      render: renderManagementUi,
      setBusy: setManagementBusy,
      setMessage: setManagementMessage,
      viewerScope: viewerScope
    }
  });

  interactionController = createDocsViewerManagementInteractionController({
    nav: nav,
    documentIndex: documentIndex,
    management: management,
    routeSession: routeSession,
    searchRecent: searchRecent,
    selectedDocument: selectedDocument,
    indexSelection: indexSelection,
    context: context,
    refs: {
      contextMenu: shellRefs.contextMenu
    },
    callbacks: {
      onContextAction: function (actionId) {
        if (!actionController) return;
        if (actionId === DOCS_VIEWER_ACTION_IDS.NEW_SIBLING) {
          actionController.handleCreateRelatedDoc("sibling");
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.NEW_CHILD) {
          actionController.handleCreateRelatedDoc("child");
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.COPY_LINK) {
          actionController.handleCopyLink();
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.OPEN_VSCODE) {
          var vscodeDoc = currentContextMenuDoc();
          if (vscodeDoc) actionController.handleOpenSource("vscode", vscodeDoc.doc_id);
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.OPEN) {
          var defaultDoc = currentContextMenuDoc();
          if (defaultDoc) actionController.handleOpenSource("default", defaultDoc.doc_id);
        }
      },
      onEditDoc: function (docId) {
        if (!actionController) return;
        eventRouter.hideManageActionsMenu();
        metadataWorkflow.openForDocId(docId);
      },
      onIndexSelectionChange: function () {
        projectIndexSelection();
      },
      onMoveDoc: function (movingDocId, parentId) {
        if (actionController) actionController.handleMoveDoc(movingDocId, parentId);
      }
    }
  });

  actionController = createDocsViewerManagementActionController({
    root: root,
    documentIndex: documentIndex,
    management: management,
    searchRecent: searchRecent,
    selectedDocument: selectedDocument,
    context: context,
    refs: {},
    resolveAction: resolveAction,
    callbacks: {
      clearDragState: clearDragState,
      currentActiveDoc: currentActiveDoc,
      currentContextMenuDoc: currentContextMenuDoc,
      getSettingsWorkflow: function () {
        return settingsWorkflow;
      },
      hideContextMenu: hideContextMenu,
      managementClientOptions: managementClientOptions,
      projectCommittedMove: function (record) {
        if (typeof context.projectCommittedMove !== "function") {
          throw new Error("Docs Viewer local move projection is unavailable.");
        }
        return context.projectCommittedMove(record);
      },
      reloadDocsIndex: reloadDocsIndex,
      reloadViewerConfiguration: reloadViewerConfiguration,
      refreshManagementCapabilities: refreshManagementCapabilities,
      renderManagementUi: renderManagementUi,
      setManagementBusy: setManagementBusy,
      setManagementMessage: setManagementMessage,
      viewerScope: viewerScope
    }
  });

  eventRouter = createDocsViewerManagementEventRouter({
    refs: {
      manageActionsButton: manageActionsButton,
      manageActionsMenu: manageActionsMenu
    },
    commands: {
      createDoc: function () { actionController.handleCreateDoc(); },
      createScope: function () { scopeLifecycleController.createScope(); },
      createSubScope: function () { scopeLifecycleController.createSubScope(); },
      deleteDoc: function () { actionController.handleDeleteDoc(); },
      deleteScope: function () { scopeLifecycleController.deleteScope(); },
      deleteSubScope: function () { scopeLifecycleController.deleteSubScope(); },
      exportDocs: function () { actionController.handleExportDocs(); },
      makeViewable: function () { actionController.handleMakeViewable(); },
      openImport: function () { importController.open(); },
      preparePackage: handlePreparePackage,
      openSettings: function () { settingsWorkflow.open(); },
      publish: function () { actionController.handlePublishDocs(); },
      renameScope: function () { scopeLifecycleController.renameScope(); },
      rebuild: function () { actionController.handleRebuildDocs(); },
      toggleDraft: handleDraftToggleChange
    },
    controllers: {
      interaction: function () { return interactionController; },
      modal: function () { return modalController; }
    }
  });

  importController = createDocsViewerManagementImportController({
    refs: {
      root: importRoot,
      bootStatus: importBootStatus
    },
    context: {
      root: root,
      docsViewerConfigUrl: serviceClient.docsViewerConfigUrl || context.docsViewerConfigUrl,
      managementBaseUrl: serviceClient.managementBaseUrl || context.managementBaseUrl
    },
    callbacks: {
      getModalController: function () {
        return modalController;
      },
      hideContextMenu: hideContextMenu,
      hideManageActionsMenu: eventRouter.hideManageActionsMenu,
      onImportComplete: displayImportedDocument,
      viewerScope: viewerScope
    }
  });

  scopeLifecycleController = createDocsViewerManagementScopeLifecycleController({
    root: root,
    management: management,
    callbacks: {
      hideContextMenu: hideContextMenu,
      hideManageActionsMenu: eventRouter.hideManageActionsMenu,
      managementClientOptions: managementClientOptions,
      navigateToScope: function (scopeId) {
        var url = new URL(window.location.href);
        url.searchParams.set("scope", scopeId);
        url.searchParams.delete("doc");
        url.searchParams.delete("q");
        window.location.assign(url.toString());
      },
      refreshManagementCapabilities: refreshManagementCapabilities,
      reloadViewerConfiguration: reloadViewerConfiguration,
      render: renderManagementUi,
      setBusy: setManagementBusy,
      setMessage: setManagementMessage,
      viewerScope: viewerScope
    }
  });

  var modalComposition = createDocsViewerManagementModalComposition({
    nav: nav,
    domains: {
      documentIndex: documentIndex,
      management: management,
      routeSession: routeSession,
      scopeConfig: scopeConfig
    },
    context: context,
    shellRefs: shellRefs,
    manageActionsButton: manageActionsButton,
    manageImportButton: manageToolbarImportButton || manageImportButton,
    manageSettingsButton: manageSettingsButton,
    callbacks: {
      currentActiveDoc: currentActiveDoc,
      hideContextMenu: hideContextMenu,
      hideManageActionsMenu: eventRouter.hideManageActionsMenu,
      isDocNonViewable: isDocNonViewable,
      onImportOpen: importController.initialize,
      onMetadataSave: actionController.handleEditMetadataSave,
      onSettingsSubmit: actionController.handleSettingsSubmit,
      managementClientOptions: managementClientOptions,
      setManagementMessage: setManagementMessage,
      viewerScope: viewerScope
    }
  });
  metadataWorkflow = modalComposition.metadataWorkflow;
  modalController = modalComposition.modalController;
  settingsWorkflow = modalComposition.settingsWorkflow;

  eventRouter.wireEvents();
  applyConfig(context.currentViewerConfig());

  return {
    applyConfig: applyConfig,
    canDragCurrentDoc: canDragCurrentDoc,
    handleDocumentKeydown: eventRouter.handleDocumentKeydown,
    handleAppManagementControl: handleAppManagementControl,
    handleIndexViewChange: handleIndexViewChange,
    handleIndexViewControl: handleIndexViewControl,
    handleMainViewControl: handleMainViewControl,
    handleRootClick: eventRouter.handleRootClick,
    hideContextMenu: hideContextMenu,
    indexSelection: indexSelection,
    initialize: initializeManagement,
    openImportModal: importController.open,
    reconcileIndexSelectionReload: reconcileIndexSelectionReload,
    render: renderManagementUi,
    renderIndexSelectionGutter: renderIndexSelectionGutter,
    updateNavDragState: updateNavDragState
  };
}
