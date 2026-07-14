import {
  isDocNonViewable
} from "../shared/docs-viewer-tree.js";
import {
  createDocsViewerManagementCapabilityController,
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
  createDocsViewerManagementActionController
} from "./docs-viewer-management-actions.js";

var MANAGEMENT_TEXT = {
  checkingNote: "Checking manage mode...",
  clearSearchNote: "Clear search to manage the current doc.",
  unavailableNote: "Docs management service unavailable."
};

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
  var manageExportButton = document.getElementById("docsViewerManageExportButton");
  var manageImportButton = document.getElementById("docsViewerManageImportButton");
  var manageToolbarImportButton = document.getElementById("docsViewerManageToolbarImportButton");
  var manageImportButtons = [manageImportButton, manageToolbarImportButton].filter(Boolean);
  var manageNewButton = document.getElementById("docsViewerManageNewButton");
  var manageEditButton = document.getElementById("docsViewerManageEditButton");
  var manageSourceButton = document.getElementById("docsViewerManageSourceButton");
  var manageSourceSaveButton = document.getElementById("docsViewerManageSourceSaveButton");
  var manageDeleteButton = document.getElementById("docsViewerManageDeleteButton");
  var manageViewableButton = document.getElementById("docsViewerManageViewableButton");
  var draftToggle = document.getElementById("docsViewerDraftToggle");
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

  function viewerScope() {
    return context.viewerScope();
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

  function currentSelectedDoc() {
    return documentIndex.docsById.get(selectedDocument.selectedDocId) || null;
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
    var activeControlIds = new Set();
    if (context.viewRegistry && typeof context.viewRegistry.projectControls === "function") {
      context.viewRegistry.projectControls(
        typeof context.activeViewState === "function" ? context.activeViewState() : {}
      ).forEach(function (control) { activeControlIds.add(control.id); });
    }
    if (manageEditButton) {
      manageEditButton.hidden = actionsHidden || !activeControlIds.has("edit");
      manageEditButton.disabled = actionsDisabled || !activeControlIds.has("edit");
    }
    if (manageSourceButton) {
      manageSourceButton.hidden = actionsHidden || !activeControlIds.has("markdown-source");
      manageSourceButton.disabled = actionsDisabled || !activeControlIds.has("markdown-source");
      manageSourceButton.setAttribute("aria-pressed", markdownMode ? "true" : "false");
      manageSourceButton.setAttribute("aria-label", markdownMode ? "Show rendered document" : "Show Markdown source");
      manageSourceButton.title = markdownMode ? "Show rendered document" : "Show Markdown source";
      manageSourceButton.textContent = markdownMode ? "📄" : "☰";
    }
    if (manageSourceSaveButton) {
      manageSourceSaveButton.hidden = actionsHidden || !activeControlIds.has("save-markdown-source");
      manageSourceSaveButton.disabled = actionsDisabled || !activeControlIds.has("save-markdown-source");
    }
  }

  function renderManagementUi() {
    if (!manageRow) return;

    routeSession.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    if (!routeSession.managementContext) {
      syncManagementStatus("", false);
      manageRow.hidden = true;
      projectDocumentActionButtons(true, true);
      eventRouter.hideManageActionsMenu();
      return;
    }

    manageRow.hidden = false;
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

    if (!manageRebuildButton || !manageNewButton || !manageDeleteButton || !manageViewableButton) return;

    var doc = currentSelectedDoc();
    var draftDoc = Boolean(doc && isDocNonViewable(doc));
    var editDisabled = (
      management.managementBusy ||
      !doc ||
      searchRecent.searchRouteActive
    );
    var deleteDisabled = (
      management.managementBusy ||
      !doc ||
      searchRecent.searchRouteActive
    );
    var viewableDisabled = (
      management.managementBusy ||
      !doc ||
      searchRecent.searchRouteActive ||
      !draftDoc
    );

    manageRebuildButton.disabled = management.managementBusy || !management.managementAvailable;
    if (manageActionsButton) {
      manageActionsButton.disabled = management.managementBusy || !management.managementAvailable;
      if (manageActionsButton.disabled) {
        eventRouter.hideManageActionsMenu();
      }
    }
    if (scopeLifecycleController) scopeLifecycleController.render();
    var publishAvailable = management.managementAvailable && scopePublishSupported(management.managementCapabilities, viewerScope());
    managePublishButtons.forEach(function (button) {
      button.disabled = management.managementBusy || !publishAvailable;
    });
    if (manageToolbarPublishButton) manageToolbarPublishButton.hidden = !publishAvailable;
    if (manageExportButton) {
      var exportAvailable = management.managementAvailable && scopeStaticHtmlExportSupported(management.managementCapabilities, viewerScope());
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

  function handleDraftToggleChange() {
    if (!draftToggle) return;
    documentIndex.showNonViewable = Boolean(draftToggle.checked);
    routeSession.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    context.applyDocVisibility();
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

  interactionController = createDocsViewerManagementInteractionController({
    nav: nav,
    documentIndex: documentIndex,
    management: management,
    routeSession: routeSession,
    searchRecent: searchRecent,
    selectedDocument: selectedDocument,
    context: context,
    refs: {
      contextMenu: shellRefs.contextMenu
    },
    callbacks: {
      onContextAction: function (actionName) {
        if (!actionController) return;
        if (actionName === "new-sibling") {
          actionController.handleCreateRelatedDoc("sibling");
          return;
        }
        if (actionName === "new-child") {
          actionController.handleCreateRelatedDoc("child");
          return;
        }
        if (actionName === "copy-link") {
          actionController.handleCopyLink();
          return;
        }
        if (actionName === "open-vscode") {
          actionController.handleOpenSource("vscode");
          return;
        }
        if (actionName === "open") {
          actionController.handleOpenSource("default");
        }
      },
      onEditDoc: function (docId) {
        if (!actionController) return;
        eventRouter.hideManageActionsMenu();
        metadataWorkflow.openForDocId(docId);
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
    selectedDocument: selectedDocument,
    context: context,
    refs: {},
    callbacks: {
      clearDragState: clearDragState,
      currentContextMenuDoc: currentContextMenuDoc,
      currentSelectedDoc: currentSelectedDoc,
      getSettingsWorkflow: function () {
        return settingsWorkflow;
      },
      hideContextMenu: hideContextMenu,
      managementClientOptions: managementClientOptions,
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
      deleteButton: manageDeleteButton,
      draftToggle: draftToggle,
      editButton: manageEditButton,
      exportButton: manageExportButton,
      importButtons: manageImportButtons,
      manageActionsButton: manageActionsButton,
      manageActionsMenu: manageActionsMenu,
      newButton: manageNewButton,
      publishButtons: managePublishButtons,
      rebuildButton: manageRebuildButton,
      settingsButton: manageSettingsButton,
      sourceButton: manageSourceButton,
      sourceSaveButton: manageSourceSaveButton,
      viewableButton: manageViewableButton
    },
    commands: {
      createDoc: function () { actionController.handleCreateDoc(); },
      deleteDoc: function () { actionController.handleDeleteDoc(); },
      editCurrent: function () { metadataWorkflow.openCurrent(); },
      exportDocs: function () { actionController.handleExportDocs(); },
      makeViewable: function () { actionController.handleMakeViewable(); },
      openImport: function () { importController.open(); },
      openSettings: function () { settingsWorkflow.open(); },
      publish: function () { actionController.handlePublishDocs(); },
      rebuild: function () { actionController.handleRebuildDocs(); },
      saveMarkdownSource: function () { actionController.handleMarkdownSave(); },
      showMarkdownSource: function () { actionController.handleMarkdownSource(); },
      toggleDraft: handleDraftToggleChange
    },
    controllers: {
      interaction: function () { return interactionController; },
      modal: function () { return modalController; },
      scopeLifecycle: function () { return scopeLifecycleController; }
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
      currentSelectedDoc: currentSelectedDoc,
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
    handleRootClick: eventRouter.handleRootClick,
    hideContextMenu: hideContextMenu,
    initialize: initializeManagement,
    openImportModal: importController.open,
    render: renderManagementUi,
    updateNavDragState: updateNavDragState
  };
}
