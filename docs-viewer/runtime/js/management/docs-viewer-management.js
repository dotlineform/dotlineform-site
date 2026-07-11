import {
  buildChildrenMap,
  isDocNonViewable
} from "../shared/docs-viewer-tree.js";
import {
  createDocsViewerManagementCapabilityController,
  scopeCreateSupported,
  scopeDeleteSupported,
  scopePublishSupported,
  scopeStaticHtmlExportSupported,
  scopeLifecycleDeleteTargets,
  subScopeCreateSupported,
  subScopeDeleteSupported,
  subScopeLifecycleDeleteTargets
} from "./docs-viewer-management-capabilities.js";
import {
  applyDocsViewerManagementConfig
} from "./docs-viewer-management-config.js";
import {
  createDocsViewerManagementInteractionController
} from "./docs-viewer-management-interactions.js";
import {
  createDocsViewerManagementModalController
} from "./docs-viewer-management-modals.js";
import {
  createDocsViewerManagementActionController
} from "./docs-viewer-management-actions.js";
import {
  collectDescendantDocIds
} from "./docs-viewer-management-action-workflow.js";
import {
  readSourceConfigSettings
} from "./docs-viewer-management-client.js";

var MANAGEMENT_TEXT = {
  checkingNote: "Checking manage mode...",
  clearSearchNote: "Clear search to manage the current doc.",
  unavailableNote: "Docs management service unavailable.",
  metadataParentRootOption: "Root",
  metadataParentInvalid: "Select a parent from the search field suggestions or enter Root.",
  settingsLoadFailed: "Settings unavailable."
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
  var manageNewScopeButton = document.getElementById("docsViewerManageNewScopeButton");
  var manageDeleteScopeButton = document.getElementById("docsViewerManageDeleteScopeButton");
  var manageNewSubScopeButton = document.getElementById("docsViewerManageNewSubScopeButton");
  var manageDeleteSubScopeButton = document.getElementById("docsViewerManageDeleteSubScopeButton");
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
  var metadataModal = shellRef("metadataModal", "docsViewerMetadataModal");
  var metadataForm = shellRef("metadataForm", "docsViewerMetadataForm");
  var metadataDocId = shellRef("metadataDocId", "docsViewerMetadataDocId");
  var metadataTitleInput = shellRef("metadataTitleInput", "docsViewerMetadataTitleInput");
  var metadataSummaryInput = shellRef("metadataSummaryInput", "docsViewerMetadataSummaryInput");
  var metadataDateInput = shellRef("metadataDateInput", "docsViewerMetadataDateInput");
  var metadataDateDisplayInput = shellRef("metadataDateDisplayInput", "docsViewerMetadataDateDisplayInput");
  var metadataStatusInput = shellRef("metadataStatusInput", "docsViewerMetadataStatusInput");
  var metadataNonViewableInput = shellRef("metadataNonViewableInput", "docsViewerMetadataNonViewableInput");
  var metadataParentInput = shellRef("metadataParentInput", "docsViewerMetadataParentInput");
  var metadataParentPopup = shellRef("metadataParentPopup", "docsViewerMetadataParentPopup");
  var metadataCancelButton = shellRef("metadataCancelButton", "docsViewerMetadataCancelButton");
  var metadataSaveButton = shellRef("metadataSaveButton", "docsViewerMetadataSaveButton");
  var importModal = shellRef("importModal", "docsViewerImportModal");
  var importRoot = shellRef("importRoot", "docsHtmlImportRoot");
  var importBootStatus = shellRef("importBootStatus", "docsHtmlImportBootStatus");
  var settingsModal = shellRef("settingsModal", "docsViewerSettingsModal");
  var settingsForm = shellRef("settingsForm", "docsViewerSettingsForm");
  var settingsScope = shellRef("settingsScope", "docsViewerSettingsScope");
  var settingsBooleanField = shellRef("settingsBooleanField", "docsViewerSettingsBooleanField");
  var settingsBooleanInput = shellRef("settingsBooleanInput", "docsViewerSettingsBooleanInput");
  var settingsBooleanLabel = shellRef("settingsBooleanLabel", "docsViewerSettingsBooleanLabel");
  var settingsTextField = shellRef("settingsTextField", "docsViewerSettingsTextField");
  var settingsTextInput = shellRef("settingsTextInput", "docsViewerSettingsTextInput");
  var settingsTextLabel = shellRef("settingsTextLabel", "docsViewerSettingsTextLabel");
  var settingsDescription = shellRef("settingsDescription", "docsViewerSettingsDescription");
  var settingsWarnings = shellRef("settingsWarnings", "docsViewerSettingsWarnings");
  var settingsStatus = shellRef("settingsStatus", "docsViewerSettingsStatus");
  var settingsCancelButton = shellRef("settingsCancelButton", "docsViewerSettingsCancelButton");
  var settingsSaveButton = shellRef("settingsSaveButton", "docsViewerSettingsSaveButton");
  var docsImportRequestPromise = null;
  var docsImportInitialized = false;
  var scopeLifecycleRequestPromise = null;
  var capabilityController = null;
  var interactionController = null;
  var modalController = null;
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

  function settingsModalOpen() {
    return Boolean(modalController && modalController.settingsModalOpen());
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

  function metadataParentOptions(doc) {
    var blockedIds = collectDescendantDocIds(state.allDocs, doc.doc_id, new Set([doc.doc_id]));
    var options = [{ value: "", label: MANAGEMENT_TEXT.metadataParentRootOption }];
    var docsByParent = buildChildrenMap(state.allDocs, {
      managementContext: state.managementContext,
      showNonViewable: state.showNonViewable
    });
    function pushChildren(parentId, depth) {
      (docsByParent.get(parentId) || []).forEach(function (candidate) {
        if (!blockedIds.has(candidate.doc_id)) {
          options.push({
            value: candidate.doc_id,
            label: (depth > 0 ? new Array(depth + 1).join("- ") : "") + candidate.title
          });
        }
        pushChildren(candidate.doc_id, depth + 1);
      });
    }
    pushChildren("", 0);
    return options;
  }

  function initializeImportModal(scope) {
    if (!importRoot || !importBootStatus || docsImportInitialized) return Promise.resolve();
    if (docsImportRequestPromise) return docsImportRequestPromise;

    docsImportRequestPromise = import("../import/docs-html-import.js")
      .then(function (module) {
        if (!module || typeof module.initDocsHtmlImport !== "function") {
          throw new Error("Docs Import module did not expose initDocsHtmlImport().");
        }
        return module.initDocsHtmlImport({
          root: importRoot,
          bootStatus: importBootStatus,
          initialScope: scope || viewerScope(),
          docsViewerConfigUrl: serviceClient.docsViewerConfigUrl || context.docsViewerConfigUrl || root.dataset.docsViewerConfigUrl || "/docs-viewer/config/defaults/docs-viewer-config.json",
          managementBaseUrl: serviceClient.managementBaseUrl || context.managementBaseUrl,
          routePath: "/docs/"
        });
      })
      .then(function () {
        docsImportInitialized = true;
      })
      .catch(function (error) {
        console.warn("docs_viewer: docs import modal failed to initialize", error);
        if (importBootStatus) {
          importBootStatus.hidden = false;
          importBootStatus.textContent = error && error.message ? error.message : "Failed to initialize docs import.";
          importBootStatus.dataset.state = "error";
        }
      })
      .finally(function () {
        docsImportRequestPromise = null;
      });

    return docsImportRequestPromise;
  }

  function openImportModal() {
    if (modalController) modalController.openImportModal();
  }

  function closeImportModal() {
    if (modalController) modalController.closeImportModal();
  }

  function openSettingsModal() {
    if (!modalController || !modalController.openSettingsModalShell()) return;
    readSourceConfigSettings(managementClientOptions())
      .then(function (payload) {
        var scopes = Array.isArray(payload && payload.scopes) ? payload.scopes : [];
        var fields = scopes[0] && Array.isArray(scopes[0].fields) ? scopes[0].fields : [];
        modalController.setSettingsField(fields.find(function (field) {
          return field && field.editable !== false;
        }) || null);
      })
      .catch(function (error) {
        modalController.setSettingsLoadError(error && error.message ? error.message : MANAGEMENT_TEXT.settingsLoadFailed);
      });
  }

  function openMetadataModalForDoc(doc) {
    return modalController ? modalController.openMetadataModal(doc) : Promise.resolve(null);
  }

  function openMetadataModal() {
    return openMetadataModalForDoc(currentSelectedDoc());
  }

  function openMetadataModalForDocId(docId) {
    return openMetadataModalForDoc(state.docsById.get(docId) || null);
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
    if (manageNewScopeButton) {
      var newScopeAvailable = state.managementAvailable && scopeCreateSupported(state.managementCapabilities);
      manageNewScopeButton.hidden = !newScopeAvailable;
      manageNewScopeButton.disabled = state.managementBusy || !newScopeAvailable;
    }
    if (manageDeleteScopeButton) {
      var deleteScopeAvailable = state.managementAvailable && scopeDeleteSupported(state.managementCapabilities);
      var deleteScopeTargets = scopeLifecycleDeleteTargets(state.managementCapabilities);
      manageDeleteScopeButton.hidden = !deleteScopeAvailable;
      manageDeleteScopeButton.disabled = state.managementBusy || !deleteScopeAvailable || deleteScopeTargets.length === 0;
    }
    if (manageNewSubScopeButton) {
      var newSubScopeAvailable = state.managementAvailable && subScopeCreateSupported(state.managementCapabilities, viewerScope());
      manageNewSubScopeButton.hidden = !newSubScopeAvailable;
      manageNewSubScopeButton.disabled = state.managementBusy || !newSubScopeAvailable;
    }
    if (manageDeleteSubScopeButton) {
      var deleteSubScopeAvailable = state.managementAvailable && subScopeDeleteSupported(state.managementCapabilities, viewerScope());
      var deleteSubScopeTargets = subScopeLifecycleDeleteTargets(state.managementCapabilities, viewerScope());
      manageDeleteSubScopeButton.hidden = !deleteSubScopeAvailable;
      manageDeleteSubScopeButton.disabled = state.managementBusy || !deleteSubScopeAvailable || deleteSubScopeTargets.length === 0;
    }
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
    if (metadataSaveButton) {
      metadataSaveButton.disabled = state.managementBusy;
    }
    if (settingsSaveButton && settingsModalOpen()) {
      settingsSaveButton.disabled = state.managementBusy || !modalController.getSettingsFieldState();
    }
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

  function metadataPayloadFromModal() {
    var doc = state.metadataEditingDocId ? state.docsById.get(state.metadataEditingDocId) : currentSelectedDoc();
    if (!doc || !metadataTitleInput || !metadataSummaryInput || !metadataDateInput || !metadataDateDisplayInput || !metadataStatusInput || !metadataNonViewableInput || !metadataParentInput) return null;

    var title = String(metadataTitleInput.value || "").trim();
    if (!title) {
      metadataTitleInput.focus();
      return null;
    }

    var parentId = modalController.resolveMetadataParentId(doc);
    if (parentId === null) {
      setManagementMessage(MANAGEMENT_TEXT.metadataParentInvalid, true);
      metadataParentInput.focus();
      return null;
    }
    var selectedStatus = String(metadataStatusInput.value || "").trim();
    return {
      doc_id: doc.doc_id,
      title: title,
      summary: String(metadataSummaryInput.value || "").replace(/\s+/g, " ").trim(),
      date: String(metadataDateInput.value || "").trim(),
      date_display: String(metadataDateDisplayInput.value || "").trim(),
      ui_status: selectedStatus,
      viewable: !metadataNonViewableInput.checked,
      parent_id: parentId
    };
  }

  function confirmMetadataModal() {
    var payload = metadataPayloadFromModal();
    if (!payload) return;
    modalController.closeMetadataModal(payload);
  }

  function scopeLifecycleCallbacks() {
    return {
      onApplied: function () {
        var reloadConfig = reloadViewerConfiguration();
        refreshManagementCapabilities();
        Promise.resolve(reloadConfig)
          .then(refreshManagementCapabilities)
          .catch(function () {
            refreshManagementCapabilities();
          });
      },
      render: renderManagementUi,
      setBusy: setManagementBusy,
      setMessage: setManagementMessage
    };
  }

  function loadScopeLifecycleModule() {
    if (scopeLifecycleRequestPromise) return scopeLifecycleRequestPromise;
    scopeLifecycleRequestPromise = import("./docs-viewer-scope-lifecycle.js")
      .then(function (module) {
        if (
          !module ||
          typeof module.openCreateScopeFlow !== "function" ||
          typeof module.openDeleteScopeFlow !== "function" ||
          typeof module.openCreateSubScopeFlow !== "function" ||
          typeof module.openDeleteSubScopeFlow !== "function"
        ) {
          throw new Error("Docs Viewer scope lifecycle module is unavailable.");
        }
        return module;
      })
      .catch(function (error) {
        scopeLifecycleRequestPromise = null;
        throw error;
      });
    return scopeLifecycleRequestPromise;
  }

  function handleCreateScope() {
    hideContextMenu();
    hideManageActionsMenu();
    return loadScopeLifecycleModule()
      .then(function (module) {
        return module.openCreateScopeFlow({
          root: root,
          state: state,
          capabilities: state.managementCapabilities,
          clientOptions: managementClientOptions(),
          callbacks: scopeLifecycleCallbacks()
        });
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Scope lifecycle unavailable.", true);
        return null;
      });
  }

  function handleDeleteScope() {
    hideContextMenu();
    hideManageActionsMenu();
    return loadScopeLifecycleModule()
      .then(function (module) {
        return module.openDeleteScopeFlow({
          root: root,
          state: state,
          capabilities: state.managementCapabilities,
          clientOptions: managementClientOptions(),
          callbacks: scopeLifecycleCallbacks()
        });
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Scope lifecycle unavailable.", true);
        return null;
      });
  }

  function handleCreateSubScope() {
    hideContextMenu();
    hideManageActionsMenu();
    return loadScopeLifecycleModule()
      .then(function (module) {
        return module.openCreateSubScopeFlow({
          root: root,
          state: state,
          parentScope: viewerScope(),
          capabilities: state.managementCapabilities,
          clientOptions: managementClientOptions(),
          callbacks: scopeLifecycleCallbacks()
        });
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Scope lifecycle unavailable.", true);
        return null;
      });
  }

  function handleDeleteSubScope() {
    hideContextMenu();
    hideManageActionsMenu();
    return loadScopeLifecycleModule()
      .then(function (module) {
        return module.openDeleteSubScopeFlow({
          root: root,
          state: state,
          parentScope: viewerScope(),
          capabilities: state.managementCapabilities,
          clientOptions: managementClientOptions(),
          callbacks: scopeLifecycleCallbacks()
        });
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Scope lifecycle unavailable.", true);
        return null;
      });
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
      refs: {
        metadataStatusInput: metadataStatusInput
      },
      modalController: modalController
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
        hideContextMenu();
        hideManageActionsMenu();
        openImportModal();
      });
    }
    if (manageSettingsButton) {
      manageSettingsButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        openSettingsModal();
      });
    }
    if (manageNewScopeButton) {
      manageNewScopeButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        handleCreateScope();
      });
    }
    if (manageDeleteScopeButton) {
      manageDeleteScopeButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        handleDeleteScope();
      });
    }
    if (manageNewSubScopeButton) {
      manageNewSubScopeButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        handleCreateSubScope();
      });
    }
    if (manageDeleteSubScopeButton) {
      manageDeleteSubScopeButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        handleDeleteSubScope();
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
        openMetadataModal().then(actionController.handleEditMetadataSave);
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
        openMetadataModalForDocId(docId).then(actionController.handleEditMetadataSave);
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
      getModalController: function () {
        return modalController;
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

  modalController = createDocsViewerManagementModalController({
    nav: nav,
    state: state,
    context: context,
    refs: {
      importModal: importModal,
      importRoot: importRoot,
      manageActionsButton: manageActionsButton,
      manageImportButton: manageImportButton,
      metadataCancelButton: metadataCancelButton,
      metadataDocId: metadataDocId,
      metadataForm: metadataForm,
      metadataDateDisplayInput: metadataDateDisplayInput,
      metadataDateInput: metadataDateInput,
      metadataNonViewableInput: metadataNonViewableInput,
      metadataModal: metadataModal,
      metadataParentInput: metadataParentInput,
      metadataParentPopup: metadataParentPopup,
      metadataStatusInput: metadataStatusInput,
      metadataSummaryInput: metadataSummaryInput,
      metadataTitleInput: metadataTitleInput,
      settingsCancelButton: settingsCancelButton,
      settingsForm: settingsForm,
      settingsModal: settingsModal,
      settingsSaveButton: settingsSaveButton,
      settingsScope: settingsScope,
      settingsBooleanField: settingsBooleanField,
      settingsBooleanInput: settingsBooleanInput,
      settingsBooleanLabel: settingsBooleanLabel,
      settingsTextField: settingsTextField,
      settingsTextInput: settingsTextInput,
      settingsTextLabel: settingsTextLabel,
      settingsDescription: settingsDescription,
      settingsStatus: settingsStatus,
      settingsWarnings: settingsWarnings,
      manageSettingsButton: manageSettingsButton
    },
    callbacks: {
      currentSelectedDoc: currentSelectedDoc,
      hideContextMenu: hideContextMenu,
      hideManageActionsMenu: hideManageActionsMenu,
      isDocNonViewable: isDocNonViewable,
      metadataParentOptions: metadataParentOptions,
      onImportOpen: initializeImportModal,
      onMetadataSubmit: confirmMetadataModal,
      onSettingsSubmit: actionController.handleSettingsSubmit,
      viewerScope: viewerScope
    }
  });

  bind();
  applyConfig(context.currentViewerConfig());

  return {
    applyConfig: applyConfig,
    canDragCurrentDoc: canDragCurrentDoc,
    handleDocumentKeydown: handleDocumentKeydown,
    handleRootClick: handleRootClick,
    hideContextMenu: hideContextMenu,
    initialize: initializeManagement,
    openImportModal: openImportModal,
    render: renderManagementUi,
    updateNavDragState: updateNavDragState
  };
}
