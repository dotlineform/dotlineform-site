import {
  createDocsViewerManagementCapabilityController,
  scopePublishSupported
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
  createDocsViewerManagementIndexController
} from "./docs-viewer-management-index-controller.js";
import {
  createDocsViewerManagementModalComposition
} from "./docs-viewer-management-modal-composition.js";
import {
  createDocsViewerManagementScopeLifecycleController
} from "./docs-viewer-management-scope-lifecycle-controller.js";
import {
  createDocsViewerManagementActionController,
  requestCommittedDocumentSource
} from "./docs-viewer-management-actions.js";
import {
  normalizeManagedDocumentCollectionTarget,
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";
import {
  docsImportResultDestination
} from "./docs-viewer-management-import-result.js";
import {
  projectDocsViewerReportControlState
} from "./docs-viewer-management-report-controls.js";
import {
  readManagedDocMetadata
} from "./docs-viewer-management-client.js";
import {
  DOCS_VIEWER_ACTION_IDS,
  createDocsViewerActionContext,
  resolveDocsViewerAction
} from "./docs-viewer-action-definitions.js";
import {
  createDocsViewerIndexSelectionOwner
} from "./docs-viewer-index-selection.js";

var MANAGEMENT_TEXT = {
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

export function refreshDocsImportTerminalDestination(detail, options = {}) {
  var result = detail && detail.result;
  var isCollection = Boolean(result && result.collection === true);
  var destination = docsImportResultDestination(
    result,
    { collection: isCollection }
  );
  if (String(detail && detail.destinationUrl || "").trim() !== destination.href) {
    throw new Error("Docs Import terminal destination URL does not match its result.");
  }
  var target = destination.target;
  var targetCollection = normalizeManagedDocumentCollectionTarget({
    scope: target.scope,
    ...(target.sub_scope ? { sub_scope: target.sub_scope } : {})
  });
  var displayedCollection = normalizeManagedDocumentCollectionTarget(
    options.currentCollection
  );
  var destinationIsDisplayed = (
    displayedCollection.scope === targetCollection.scope
    && String(displayedCollection.sub_scope || "")
      === String(targetCollection.sub_scope || "")
  );
  if (!destinationIsDisplayed) {
    return Promise.resolve({
      refreshed: false,
      target: target
    });
  }

  if (targetCollection.sub_scope) {
    var reportState = options.reportState || {};
    var refresh = isCollection
      ? reportState.refreshCollection
      : reportState.refreshDocument;
    if (typeof refresh !== "function") {
      return Promise.reject(new Error(
        "The exact imported sub-scope destination is no longer mounted."
      ));
    }
    return Promise.resolve(refresh(target)).then(function () {
      return { refreshed: true, target: target };
    });
  }

  if (typeof options.reloadParent !== "function") {
    return Promise.reject(new Error(
      "The exact imported parent-scope destination cannot be refreshed."
    ));
  }
  return Promise.resolve(
    options.reloadParent(isCollection ? "" : target.doc_id)
  ).then(function () {
    return { refreshed: true, target: target };
  });
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
  var manageRebuildButton = document.getElementById("docsViewerManageRebuildButton");
  var manageSettingsButton = document.getElementById("docsViewerManageSettingsButton");
  var managePublishButton = document.getElementById("docsViewerManagePublishButton");
  var manageToolbarPublishButton = document.getElementById("docsViewerManageToolbarPublishButton");
  var managePublishButtons = [managePublishButton, manageToolbarPublishButton].filter(Boolean);
  var manageImportButton = document.getElementById("docsViewerManageImportButton");
  var manageToolbarImportButton = document.getElementById("docsViewerManageToolbarImportButton");
  var manageImportButtons = [manageImportButton, manageToolbarImportButton].filter(Boolean);
  var manageNewButton = document.getElementById("docsViewerManageNewButton");
  var importRoot = shellRef("importRoot", "docsHtmlImportRoot");
  var importBootStatus = shellRef("importBootStatus", "docsHtmlImportBootStatus");
  var capabilityController = null;
  var eventRouter = null;
  var importController = null;
  var interactionController = null;
  var metadataWorkflow = null;
  var modalController = null;
  var scopeLifecycleController = null;
  var settingsWorkflow = null;
  var actionController = null;
  var resolveAction = null;
  var projectedReportControls = null;
  var sourceSessionReportActive = false;
  var subscopeReportState = null;
  var indexController = createDocsViewerManagementIndexController({
    root: root,
    nav: nav,
    documentIndex: documentIndex,
    management: management,
    routeSession: routeSession,
    searchRecent: searchRecent,
    callbacks: {
      activeDocId: function () {
        return selectedDocument.selectedDocId;
      },
      activeIndexViewId: function () {
        return typeof context.activeIndexViewId === "function"
          ? context.activeIndexViewId()
          : "index-tree";
      },
      handleDeleteDoc: function () {
        if (actionController) actionController.handleDeleteDoc();
      },
      hideIndexActionsMenu: function (options) {
        if (eventRouter) eventRouter.hideIndexActionsMenu(options);
      },
      isManagementContext: function () {
        return typeof context.isManagementContext === "function" && context.isManagementContext();
      },
      managementClientOptions: managementClientOptions,
      projectIndexViewControlState: function (controlId, controlState) {
        if (typeof context.projectIndexViewControlState === "function") {
          return context.projectIndexViewControlState(controlId, controlState);
        }
        return null;
      },
      refreshManagementCapabilities: refreshManagementCapabilities,
      reloadDocsIndex: reloadDocsIndex,
      renderManagementUi: renderManagementUi,
      renderSidebar: function () {
        if (typeof context.renderSidebar === "function") context.renderSidebar();
      },
      resolveAction: function (actionId) {
        return resolveAction ? resolveAction(actionId) : null;
      },
      setManagementBusy: setManagementBusy,
      setManagementMessage: setManagementMessage,
      toggleIndexActionsMenu: function () {
        if (eventRouter) eventRouter.toggleIndexActionsMenu();
      },
      viewerScope: viewerScope
    }
  });
  var indexSelection = indexController.indexSelection;
  resolveAction = createDocsViewerManagementActionResolver({
    indexSelection: indexSelection,
    selectedDocument: selectedDocument
  });

  function viewerScope() {
    return context.viewerScope();
  }

  function currentImportDisplayContext() {
    if (subscopeReportState && subscopeReportState.collectionTarget) {
      return normalizeManagedDocumentCollectionTarget(
        subscopeReportState.collectionTarget
      );
    }
    return normalizeManagedDocumentCollectionTarget({
      scope: viewerScope()
    });
  }

  function currentImportDisplayContextLabel() {
    if (subscopeReportState && subscopeReportState.collectionTarget) {
      return String(subscopeReportState.collectionLabel || "").trim();
    }
    return viewerScope();
  }

  function openAppImport(detail) {
    var eventDetail = detail && typeof detail === "object" ? detail : {};
    return importController.open({
      destination: currentImportDisplayContext(),
      destinationLabel: currentImportDisplayContextLabel(),
      restoreFocus: eventDetail.actionTarget || eventDetail.target || null
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

  function actionTargetDoc(resolution) {
    if (!resolution || !resolution.enabled || resolution.targetDocIds.length !== 1) return null;
    return documentIndex.docsById.get(resolution.targetDocIds[0]) || null;
  }

  function sourceTargetForDoc(doc) {
    if (!doc || !doc.doc_id) return null;
    return normalizeManagedDocumentTarget({
      scope: viewerScope(),
      doc_id: doc.doc_id
    });
  }

  function publishSubscopeReportState(value) {
    var state = value && typeof value === "object" ? value : {};
    var stateName = String(state.state || "").trim().toLowerCase();
    var activeStateNames = ["list", "loading", "detail", "invalid", "error"];
    var parentTarget = null;
    var collectionTarget = null;
    var subdocTarget = null;
    var subdocRecord = null;
    var subdocInfo = null;
    try {
      if (activeStateNames.indexOf(stateName) !== -1) {
        parentTarget = normalizeManagedDocumentTarget(state.parentTarget);
        collectionTarget = normalizeManagedDocumentCollectionTarget(
          state.collectionTarget
        );
        if (
          !collectionTarget.sub_scope
          || collectionTarget.scope !== parentTarget.scope
        ) {
          throw new Error(
            "Validated sub-scope report collection does not match its parent."
          );
        }
        if (stateName === "detail") {
          subdocTarget = normalizeManagedDocumentTarget(state.subdocTarget);
          if (
            !subdocTarget.sub_scope
            || subdocTarget.scope !== parentTarget.scope
            || subdocTarget.sub_scope !== collectionTarget.sub_scope
          ) {
            throw new Error("Validated sub-scope report target does not match its parent report.");
          }
          if (
            !state.subdocRecord
            || typeof state.subdocRecord !== "object"
            || Array.isArray(state.subdocRecord)
            || String(state.subdocRecord.doc_id || "").trim() !== subdocTarget.doc_id
          ) {
            throw new Error("Validated sub-scope report record does not match its target.");
          }
          subdocRecord = Object.freeze(Object.assign({}, state.subdocRecord));
          subdocInfo = state.subdocInfo && typeof state.subdocInfo === "object"
            ? Object.freeze(Object.assign({}, state.subdocInfo))
            : null;
        }
      }
    } catch (_error) {
      stateName = "inactive";
      parentTarget = null;
      subdocTarget = null;
      subdocRecord = null;
      subdocInfo = null;
    }
    subscopeReportState = parentTarget
      ? {
          state: stateName,
          parentTarget: parentTarget,
          collectionTarget: collectionTarget,
          collectionLabel: String(state.collectionLabel || "").trim(),
          subdocTarget: subdocTarget,
          subdocRecord: subdocRecord,
          subdocInfo: subdocInfo,
          refreshDocument: typeof state.refreshDocument === "function"
            ? state.refreshDocument
            : null,
          refreshCollection: typeof state.refreshCollection === "function"
            ? state.refreshCollection
            : null
        }
      : null;
    var documentMode = root && root.dataset
      ? String(root.dataset.documentDisplayMode || "")
      : "";
    if (documentMode !== "markdown-source") {
      sourceSessionReportActive = false;
    }
    renderManagementUi();
  }

  function activeSourceTarget() {
    var services = typeof context.sourceEditorServices === "function"
      ? context.sourceEditorServices()
      : context.sourceEditorServices;
    var adapter = services && typeof services.getActiveSourceEditorContextAdapter === "function"
      ? services.getActiveSourceEditorContextAdapter()
      : null;
    return adapter && typeof adapter.getDocumentTarget === "function"
      ? adapter.getDocumentTarget()
      : null;
  }

  function openCreatedDocumentSource(target) {
    sourceSessionReportActive = Boolean(subscopeReportState);
    return requestCommittedDocumentSource(target, function (modeId, options) {
      return context.requestDocumentMode(modeId, options);
    });
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
    var reportActive = Boolean(subscopeReportState) || (markdownMode && sourceSessionReportActive);
    projectedReportControls = projectDocsViewerReportControlState({
      disabled: actionsDisabled,
      documentMode: documentMode,
      hidden: actionsHidden,
      ordinaryTarget: sourceTargetForDoc(currentActiveDoc()),
      parentTarget: subscopeReportState ? subscopeReportState.parentTarget : null,
      reportActive: reportActive,
      reportState: subscopeReportState ? subscopeReportState.state : "",
      subdocTarget: subscopeReportState ? subscopeReportState.subdocTarget : null
    });
    if (typeof context.projectMainViewControlState === "function") {
      context.projectMainViewControlState("edit", projectedReportControls.editMetadata.state);
      context.projectMainViewControlState("open-vscode", projectedReportControls.openVsCode.state);
      context.projectMainViewControlState("markdown-source", projectedReportControls.parentSource.state);
      context.projectMainViewControlState("subdoc-source", projectedReportControls.subdocSource.state);
      context.projectMainViewControlState("return-to-doc", projectedReportControls.returnToDoc.state);
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
      "manage-scope",
      "manage-theme"
    ].forEach(function (controlId) {
      projectAppControl(controlId, { hidden: true, disabled: true });
    });
  }

  function handleMainViewControl(detail) {
    var controlId = String(detail && detail.controlId || "").trim();
    var actionId = String(detail && detail.actionId || "").trim();
    var reportControlOwners = new Map([
      ["edit", {
        projection: "editMetadata",
        run: function (target) {
          metadataWorkflow.openForTarget(target);
        }
      }],
      ["markdown-source", {
        projection: "parentSource",
        run: function (target) {
          sourceSessionReportActive = Boolean(subscopeReportState);
          actionController.handleMarkdownSource(target);
        }
      }],
      ["subdoc-source", {
        projection: "subdocSource",
        run: function (target) {
          sourceSessionReportActive = Boolean(subscopeReportState);
          actionController.handleMarkdownSource(target);
        }
      }],
      ["return-to-doc", {
        projection: "returnToDoc",
        run: function () {
          actionController.handleReturnToDoc();
        }
      }]
    ]);
    var reportOwner = reportControlOwners.get(controlId);
    if (reportOwner) {
      var projected = projectedReportControls
        ? projectedReportControls[reportOwner.projection]
        : null;
      if (
        !projected
        || projected.state.hidden
        || projected.state.disabled
        || (
          reportOwner.projection !== "returnToDoc"
          && !projected.target
        )
      ) {
        return false;
      }
      reportOwner.run(projected.target);
      return true;
    }

    var resolution = actionId ? resolveAction(actionId) : null;
    if (actionId && (!resolution || !resolution.enabled)) return false;
    var owners = new Map([
      ["open-vscode", function () {
        var doc = actionTargetDoc(resolution);
        var mountedTarget = activeSourceTarget();
        var projectedOpen = projectedReportControls
          ? projectedReportControls.openVsCode
          : null;
        var projectedTarget = (
          projectedOpen
          && !projectedOpen.state.hidden
          && !projectedOpen.state.disabled
        ) ? projectedOpen.target : null;
        var target = mountedTarget || projectedTarget;
        if (target) {
          actionController.handleOpenSource(
            "vscode",
            target,
            doc && target.doc_id === doc.doc_id ? doc.title : target.doc_id
          );
        }
      }],
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
    if (owner) {
      owner();
      return true;
    }
    var contributions = context.mainViewControlHandlerContributions || {};
    var contribution = typeof contributions[controlId] === "function"
      ? contributions[controlId]
      : null;
    if (!contribution) return false;
    contribution({
      detail: detail,
      resolution: resolution,
      root: root,
      setStatus: context.setStatus,
      sourceEditorServices: typeof context.sourceEditorServices === "function"
        ? context.sourceEditorServices()
        : context.sourceEditorServices
    });
    return true;
  }

  function handleAppManagementControl(detail) {
    var actionId = String(detail && detail.actionId || "").trim();
    if (actionId && !resolveAction(actionId).enabled) return false;
    return eventRouter.handleAppManagementControl(detail);
  }

  function renderManagementUi() {
    if (!manageRow) return;

    routeSession.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    indexController.render();
    if (!routeSession.managementContext) {
      syncManagementStatus("", false);
      hideAppManagementControls();
      projectDocumentActionButtons(true, true);
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

    var noteText;
    var noteIsError = false;
    if (!management.managementChecked) {
      noteText = "";
    } else if (!management.managementAvailable) {
      noteText = management.managementCapabilityError || MANAGEMENT_TEXT.unavailableNote;
      noteIsError = true;
    } else {
      noteText = managementNoteText();
      noteIsError = management.managementMessageIsError;
    }
    syncManagementStatus(noteText, noteIsError);

    if (!manageRebuildButton || !manageNewButton) return;

    var editAction = resolveAction(DOCS_VIEWER_ACTION_IDS.EDIT_METADATA);
    var editDisabled = (
      management.managementBusy ||
      !editAction.enabled ||
      searchRecent.searchRouteActive
    );
    var publishAvailable = management.managementAvailable && scopePublishSupported(management.managementCapabilities, viewerScope());
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
    manageImportButtons.forEach(function (button) {
      button.disabled = management.managementBusy || !management.managementAvailable;
    });
    if (manageSettingsButton) {
      manageSettingsButton.disabled = management.managementBusy || !management.managementAvailable;
    }
    manageNewButton.disabled = management.managementBusy || !management.managementAvailable;
    projectDocumentActionButtons(!management.managementChecked || !management.managementAvailable, !management.managementAvailable || editDisabled);
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

  function reloadDocsIndex(targetDocId, _summaryText) {
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
    return refreshDocsImportTerminalDestination(detail, {
      currentCollection: currentImportDisplayContext(),
      reportState: subscopeReportState,
      reloadParent: function (targetDocId) {
        return reloadDocsIndex(targetDocId, "");
      }
    });
  }

  function setManagementMessage(message, isError) {
    management.managementMessage = String(message || "");
    management.managementMessageIsError = Boolean(isError);
    renderManagementUi();
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
          if (vscodeDoc) {
            actionController.handleOpenSource(
              "vscode",
              sourceTargetForDoc(vscodeDoc),
              vscodeDoc.title
            );
          }
          return;
        }
        if (actionId === DOCS_VIEWER_ACTION_IDS.OPEN) {
          var defaultDoc = currentContextMenuDoc();
          if (defaultDoc) {
            actionController.handleOpenSource(
              "default",
              sourceTargetForDoc(defaultDoc),
              defaultDoc.title
            );
          }
        }
      },
      onEditDoc: function (docId) {
        if (!actionController) return;
        eventRouter.hideManageActionsMenu();
        var doc = documentIndex.docsById.get(docId) || null;
        var target = sourceTargetForDoc(doc);
        if (target) metadataWorkflow.openForTarget(target);
      },
      onIndexSelectionChange: function () {
        indexController.projectSelection();
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
      openCreatedDocumentSource: openCreatedDocumentSource,
      reloadDocsIndex: reloadDocsIndex,
      reloadMetadataTarget: function (target, response) {
        return typeof context.reloadMetadataTarget === "function"
          ? context.reloadMetadataTarget(target, response)
          : response;
      },
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
      indexActionsButton: indexController.actionsButton,
      indexActionsMenu: indexController.actionsMenu,
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
      openImport: openAppImport,
      openSettings: function () { settingsWorkflow.open(); },
      publish: function () { actionController.handlePublishDocs(); },
      renameScope: function () { scopeLifecycleController.renameScope(); },
      rebuild: function () { actionController.handleRebuildDocs(); }
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
      reloadDocsIndex: reloadDocsIndex,
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
      hideContextMenu: hideContextMenu,
      hideManageActionsMenu: eventRouter.hideManageActionsMenu,
      onImportOpen: importController.initialize,
      loadMetadataDoc: function (target) {
        return readManagedDocMetadata(target, managementClientOptions());
      },
      onMetadataLoadError: function (error) {
        setManagementMessage(
          error && error.message ? error.message : "Document metadata could not be loaded.",
          true
        );
        renderManagementUi();
      },
      onMetadataSave: actionController.handleEditMetadataSave,
      onSettingsSubmit: actionController.handleSettingsSubmit,
      managementClientOptions: managementClientOptions,
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
    copySubscopeDocuments: indexController.copySubscopeDocuments,
    createSubscopeDocument: actionController.handleCreateSubscopeDocument,
    handleDocumentKeydown: eventRouter.handleDocumentKeydown,
    handleAppManagementControl: handleAppManagementControl,
    handleIndexViewChange: indexController.handleViewChange,
    handleIndexViewControl: indexController.handleControl,
    handleMainViewControl: handleMainViewControl,
    handleRootClick: eventRouter.handleRootClick,
    hideContextMenu: hideContextMenu,
    indexSelection: indexSelection,
    initialize: initializeManagement,
    openImportModal: importController.open,
    publishSubscopeReportState: publishSubscopeReportState,
    reconcileIndexSelectionReload: indexController.reconcileReload,
    render: renderManagementUi,
    renderIndexSelectionGutter: indexController.renderSelectionGutter,
    setSubscopePublishable: indexController.setSubscopePublishable,
    updateNavDragState: updateNavDragState
  };
}
