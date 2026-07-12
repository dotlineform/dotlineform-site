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

function createDocsViewerManagementStateFacade(domains) {
  var sources = domains || {};
  var fieldSources = {
    allDocs: sources.documentIndex,
    childrenByParent: sources.documentIndex,
    docNonViewableEmoji: sources.scopeConfig,
    docsById: sources.documentIndex,
    generatedDataReadAvailable: sources.generatedData,
    generatedDataReadChecked: sources.generatedData,
    managementAvailable: sources.management,
    managementBusy: sources.management,
    managementCapabilities: sources.management,
    managementCapabilityCheckId: sources.management,
    managementCapabilityError: sources.management,
    managementChecked: sources.management,
    managementMessage: sources.management,
    managementMessageIsError: sources.management,
    managementContext: sources.routeSession,
    managementStatusOwnsViewerStatus: sources.management,
    metadataEditingDocId: sources.management,
    metadataRestoreFocusId: sources.management,
    payloadCache: sources.selectedDocument,
    recentEntries: sources.searchRecent,
    recentLoaded: sources.searchRecent,
    recentRequestPromise: sources.searchRecent,
    recentModeActive: sources.searchRecent,
    reloadExpectedDocId: sources.selectedDocument,
    reloadNonce: sources.selectedDocument,
    searchEntries: sources.searchRecent,
    searchLoaded: sources.searchRecent,
    searchQuery: sources.searchRecent,
    searchRequestPromise: sources.searchRecent,
    searchRouteActive: sources.searchRecent,
    searchVisibleCount: sources.searchRecent,
    selectedDocId: sources.selectedDocument,
    showNonViewable: sources.documentIndex,
    uiStatusByValue: sources.scopeConfig,
    uiStatuses: sources.scopeConfig
  };
  var facade = {};
  Object.keys(fieldSources).forEach(function (fieldName) {
    Object.defineProperty(facade, fieldName, {
      enumerable: true,
      get: function () {
        var source = fieldSources[fieldName] || {};
        return source[fieldName];
      },
      set: function (value) {
        var source = fieldSources[fieldName] || {};
        source[fieldName] = value;
      }
    });
  });
  return facade;
}

export function initDocsViewerManagement(context) {
  var root = context.root;
  var nav = context.nav;
  var managementState = context.managementState || {};
  var state = createDocsViewerManagementStateFacade(managementState.domains || {});
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
  var manageExportButton = document.getElementById("docsViewerManageExportButton");
  var manageImportButton = document.getElementById("docsViewerManageImportButton");
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
    return state.docsById.get(state.selectedDocId) || null;
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

  function hideManageActionsMenu() {
    if (!manageActionsMenu || !manageActionsButton) return;
    manageActionsMenu.hidden = true;
    manageActionsButton.setAttribute("aria-expanded", "false");
  }

  function toggleManageActionsMenu() {
    if (!manageActionsMenu || !manageActionsButton || manageActionsButton.disabled) return;
    if (manageActionsMenu.hidden) {
      manageActionsMenu.hidden = false;
      manageActionsButton.setAttribute("aria-expanded", "true");
    } else {
      hideManageActionsMenu();
    }
  }

  function setManagementBusy(busy) {
    state.managementBusy = Boolean(busy);
    if (root) {
      root.dataset.managementBusy = state.managementBusy ? "true" : "false";
    }
  }

  function updateNavDragState() {
    if (interactionController) interactionController.updateNavDragState();
  }

  function managementNoteText() {
    if (state.managementMessage) return state.managementMessage;
    if (state.searchRouteActive) {
      return MANAGEMENT_TEXT.clearSearchNote;
    }
    return "";
  }

  function syncManagementStatus(noteText, isError) {
    var text = String(noteText || "");
    var hasManagementStatus = Boolean(text);
    if (hasManagementStatus || state.managementStatusOwnsViewerStatus) {
      context.setStatus(text, Boolean(isError));
    }
    state.managementStatusOwnsViewerStatus = hasManagementStatus;
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

    state.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    if (!state.managementContext) {
      syncManagementStatus("", false);
      manageRow.hidden = true;
      projectDocumentActionButtons(true, true);
      hideManageActionsMenu();
      return;
    }

    manageRow.hidden = false;
    if (manageActions) {
      manageActions.hidden = !state.managementChecked || !state.managementAvailable;
      if (manageActions.hidden) {
        hideManageActionsMenu();
      }
    }

    var noteText = "";
    var noteIsError = false;
    if (!state.managementChecked) {
      noteText = MANAGEMENT_TEXT.checkingNote;
    } else if (!state.managementAvailable) {
      noteText = state.managementCapabilityError || MANAGEMENT_TEXT.unavailableNote;
      noteIsError = true;
    } else {
      noteText = managementNoteText();
      noteIsError = state.managementMessageIsError;
    }
    syncManagementStatus(noteText, noteIsError);

    if (!manageRebuildButton || !manageNewButton || !manageDeleteButton || !manageViewableButton) return;

    var doc = currentSelectedDoc();
    var draftDoc = Boolean(doc && isDocNonViewable(doc));
    var editDisabled = (
      state.managementBusy ||
      !doc ||
      state.searchRouteActive
    );
    var deleteDisabled = (
      state.managementBusy ||
      !doc ||
      state.searchRouteActive
    );
    var viewableDisabled = (
      state.managementBusy ||
      !doc ||
      state.searchRouteActive ||
      !draftDoc
    );

    manageRebuildButton.disabled = state.managementBusy || !state.managementAvailable;
    if (manageActionsButton) {
      manageActionsButton.disabled = state.managementBusy || !state.managementAvailable;
      if (manageActionsButton.disabled) {
        hideManageActionsMenu();
      }
    }
    if (scopeLifecycleController) scopeLifecycleController.render();
    if (managePublishButton) {
      var publishAvailable = state.managementAvailable && scopePublishSupported(state.managementCapabilities, viewerScope());
      managePublishButton.disabled = state.managementBusy || !publishAvailable;
    }
    if (manageExportButton) {
      var exportAvailable = state.managementAvailable && scopeStaticHtmlExportSupported(state.managementCapabilities, viewerScope());
      manageExportButton.hidden = !exportAvailable;
      manageExportButton.disabled = state.managementBusy || !exportAvailable;
    }
    if (manageImportButton) {
      manageImportButton.disabled = state.managementBusy || !state.managementAvailable;
    }
    if (manageSettingsButton) {
      manageSettingsButton.disabled = state.managementBusy || !state.managementAvailable;
    }
    manageNewButton.disabled = state.managementBusy || !state.managementAvailable;
    projectDocumentActionButtons(!state.managementChecked || !state.managementAvailable, !state.managementAvailable || editDisabled);
    manageDeleteButton.disabled = !state.managementAvailable || deleteDisabled;
    manageViewableButton.disabled = !state.managementAvailable || viewableDisabled;
    if (draftToggle) {
      draftToggle.disabled = !state.managementAvailable || state.managementBusy;
      draftToggle.checked = state.showNonViewable;
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
    state.payloadCache.clear();
    state.searchEntries = [];
    state.searchLoaded = false;
    state.searchRequestPromise = null;
    state.recentEntries = [];
    state.recentLoaded = false;
    state.recentRequestPromise = null;
    state.reloadNonce = String(Date.now());
    state.reloadExpectedDocId = String(targetDocId || "").trim();
    state.searchQuery = "";
    state.searchVisibleCount = context.SEARCH_BATCH_SIZE;
    state.searchRouteActive = false;
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

  function setManagementMessage(message, isError) {
    state.managementMessage = String(message || "");
    state.managementMessageIsError = Boolean(isError);
    renderManagementUi();
  }

  function handleDraftToggleChange() {
    if (!draftToggle) return;
    state.showNonViewable = Boolean(draftToggle.checked);
    state.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    context.applyDocVisibility();
    context.renderSidebar();
    context.renderBookmarkUi();
    renderManagementUi();

    var currentDocId = state.selectedDocId;
    var targetDocId = currentDocId && state.docsById.has(currentDocId) ? currentDocId : context.defaultDocId();
    if (state.recentModeActive) {
      context.renderRecentMode();
      return;
    }
    if (state.searchRouteActive) {
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
      state: state,
      metadataWorkflow: metadataWorkflow
    });
  }

  function handleRootClick(event) {
    if (interactionController) interactionController.handleRootClick(event);
    if (manageActionsMenu && !event.target.closest(".docsViewer__manageActions")) {
      hideManageActionsMenu();
    }
    return modalController ? modalController.handleRootClick(event) : false;
  }

  function handleDocumentKeydown(event) {
    if (interactionController && interactionController.handleDocumentKeydown(event)) {
      return true;
    }
    if (event.key === "Escape" && manageActionsMenu && !manageActionsMenu.hidden) {
      event.preventDefault();
      hideManageActionsMenu();
      return true;
    }
    return modalController ? modalController.handleDocumentKeydown(event) : false;
  }

  function bind() {
    if (interactionController) interactionController.wireEvents();

    if (manageRebuildButton) {
      manageRebuildButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        actionController.handleRebuildDocs();
      });
    }
    if (manageImportButton) {
      manageImportButton.addEventListener("click", function () {
        importController.open();
      });
    }
    if (manageSettingsButton) {
      manageSettingsButton.addEventListener("click", function () {
        settingsWorkflow.open();
      });
    }
    if (managePublishButton) {
      managePublishButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        actionController.handlePublishDocs();
      });
    }
    if (manageExportButton) {
      manageExportButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        actionController.handleExportDocs();
      });
    }
    if (manageActionsButton) {
      manageActionsButton.addEventListener("click", function () {
        toggleManageActionsMenu();
      });
    }
    if (manageNewButton) {
      manageNewButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        actionController.handleCreateDoc();
      });
    }
    if (manageEditButton) {
      manageEditButton.addEventListener("click", function () {
        hideManageActionsMenu();
        metadataWorkflow.openCurrent();
      });
    }
    if (manageSourceButton) {
      manageSourceButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        actionController.handleMarkdownSource();
      });
    }
    if (manageSourceSaveButton) {
      manageSourceSaveButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        actionController.handleMarkdownSave();
      });
    }
    if (manageDeleteButton) {
      manageDeleteButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        actionController.handleDeleteDoc();
      });
    }
    if (manageViewableButton) {
      manageViewableButton.addEventListener("click", function () {
        hideContextMenu();
        actionController.handleMakeViewable();
      });
    }
    if (draftToggle) {
      draftToggle.addEventListener("change", function () {
        hideContextMenu();
        handleDraftToggleChange();
      });
    }
    if (modalController) modalController.wireEvents();
    if (scopeLifecycleController) scopeLifecycleController.wireEvents();
  }

  capabilityController = createDocsViewerManagementCapabilityController({
    state: state,
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
    state: state,
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
        hideManageActionsMenu();
        metadataWorkflow.openForDocId(docId);
      },
      onMoveDoc: function (movingDocId, parentId) {
        if (actionController) actionController.handleMoveDoc(movingDocId, parentId);
      }
    }
  });

  actionController = createDocsViewerManagementActionController({
    root: root,
    state: state,
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
      hideManageActionsMenu: hideManageActionsMenu,
      viewerScope: viewerScope
    }
  });

  scopeLifecycleController = createDocsViewerManagementScopeLifecycleController({
    root: root,
    state: state,
    callbacks: {
      hideContextMenu: hideContextMenu,
      hideManageActionsMenu: hideManageActionsMenu,
      managementClientOptions: managementClientOptions,
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
    state: state,
    context: context,
    shellRefs: shellRefs,
    manageActionsButton: manageActionsButton,
    manageImportButton: manageImportButton,
    manageSettingsButton: manageSettingsButton,
    callbacks: {
      currentSelectedDoc: currentSelectedDoc,
      hideContextMenu: hideContextMenu,
      hideManageActionsMenu: hideManageActionsMenu,
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

  bind();
  applyConfig(context.currentViewerConfig());

  return {
    applyConfig: applyConfig,
    canDragCurrentDoc: canDragCurrentDoc,
    handleDocumentKeydown: handleDocumentKeydown,
    handleRootClick: handleRootClick,
    hideContextMenu: hideContextMenu,
    initialize: initializeManagement,
    openImportModal: importController.open,
    render: renderManagementUi,
    updateNavDragState: updateNavDragState
  };
}
