import {
  buildChildrenMap,
  isDocHidden
} from "./docs-viewer-tree.js";
import {
  readSourceConfigSettings
} from "./docs-viewer-management-client.js";
import {
  createDocsViewerManagementCapabilityController,
  scopeArchiveAvailable,
  scopeCreateSupported,
  scopeDeleteSupported,
  scopeLifecycleDeleteTargets
} from "./docs-viewer-management-capabilities.js";
import {
  applyDocsViewerManagementConfig
} from "./docs-viewer-management-config.js";
import {
  canDragDoc,
  canDropOnDoc,
  currentDropTargetFromEvent,
  normalizeSortOrderValue,
  rowDropPosition
} from "./docs-viewer-drag-drop.js";
import {
  renderStatusPillsMarkup
} from "./docs-viewer-management-render.js";
import {
  createDocsViewerManagementModalController
} from "./docs-viewer-management-modals.js";
import {
  createDocsViewerManagementActionController
} from "./docs-viewer-management-actions.js";

export function initDocsViewerManagement(context) {
  var root = context.root;
  var nav = context.nav;
  var state = context.state;
  var manageRow = document.getElementById("docsViewerManageRow");
  var manageActions = manageRow ? manageRow.querySelector(".docsViewer__manageActions") : null;
  var manageActionsButton = document.getElementById("docsViewerManageActionsButton");
  var manageActionsMenu = document.getElementById("docsViewerManageActionsMenu");
  var manageRebuildButton = document.getElementById("docsViewerManageRebuildButton");
  var manageSettingsButton = document.getElementById("docsViewerManageSettingsButton");
  var manageNewScopeButton = document.getElementById("docsViewerManageNewScopeButton");
  var manageDeleteScopeButton = document.getElementById("docsViewerManageDeleteScopeButton");
  var manageImportButton = document.getElementById("docsViewerManageImportButton");
  var manageNewButton = document.getElementById("docsViewerManageNewButton");
  var manageEditButton = document.getElementById("docsViewerManageEditButton");
  var manageArchiveButton = document.getElementById("docsViewerManageArchiveButton");
  var manageDeleteButton = document.getElementById("docsViewerManageDeleteButton");
  var manageViewableButton = document.getElementById("docsViewerManageViewableButton");
  var statusPills = document.getElementById("docsViewerStatusPills");
  var draftToggle = document.getElementById("docsViewerDraftToggle");
  var draftLabel = document.querySelector(".docsViewer__draftLabel");
  var indexUndoButton = document.getElementById("docsViewerIndexUndoButton");
  var contextMenu = document.getElementById("docsViewerContextMenu");
  var contextCopyLinkButton = contextMenu ? contextMenu.querySelector('[data-context-action="copy-link"]') : null;
  var metadataModal = document.getElementById("docsViewerMetadataModal");
  var metadataForm = document.getElementById("docsViewerMetadataForm");
  var metadataDocId = document.getElementById("docsViewerMetadataDocId");
  var metadataTitleInput = document.getElementById("docsViewerMetadataTitleInput");
  var metadataSummaryInput = document.getElementById("docsViewerMetadataSummaryInput");
  var metadataStatusLabel = document.getElementById("docsViewerMetadataStatusLabel");
  var metadataStatusInput = document.getElementById("docsViewerMetadataStatusInput");
  var metadataHiddenInput = document.getElementById("docsViewerMetadataHiddenInput");
  var metadataHiddenLabel = document.getElementById("docsViewerMetadataHiddenLabel");
  var metadataParentInput = document.getElementById("docsViewerMetadataParentInput");
  var metadataParentPopup = document.getElementById("docsViewerMetadataParentPopup");
  var metadataSortOrderInput = document.getElementById("docsViewerMetadataSortOrderInput");
  var metadataCancelButton = document.getElementById("docsViewerMetadataCancelButton");
  var metadataSaveButton = document.getElementById("docsViewerMetadataSaveButton");
  var importModal = document.getElementById("docsViewerImportModal");
  var importRoot = document.getElementById("docsHtmlImportRoot");
  var importBootStatus = document.getElementById("docsHtmlImportBootStatus");
  var settingsModal = document.getElementById("docsViewerSettingsModal");
  var settingsForm = document.getElementById("docsViewerSettingsForm");
  var settingsHeading = document.getElementById("docsViewerSettingsHeading");
  var settingsScope = document.getElementById("docsViewerSettingsScope");
  var settingsUpdatedInput = document.getElementById("docsViewerSettingsUpdatedInput");
  var settingsUpdatedLabel = document.getElementById("docsViewerSettingsUpdatedLabel");
  var settingsWarnings = document.getElementById("docsViewerSettingsWarnings");
  var settingsStatus = document.getElementById("docsViewerSettingsStatus");
  var settingsCancelButton = document.getElementById("docsViewerSettingsCancelButton");
  var settingsSaveButton = document.getElementById("docsViewerSettingsSaveButton");
  var docsImportRequestPromise = null;
  var docsImportInitialized = false;
  var scopeLifecycleRequestPromise = null;
  var capabilityController = null;
  var modalController = null;
  var actionController = null;

  function viewerScope() {
    return context.viewerScope();
  }

  function managementClientOptions() {
    return {
      baseUrl: context.managementBaseUrl,
      scope: viewerScope(),
      serverNotConfiguredError: state.managementText.serverNotConfiguredError,
      fetch: function (url, options) {
        return window.fetch(url, options);
      }
    };
  }

  function currentSelectedDoc() {
    return state.docsById.get(state.selectedDocId) || null;
  }

  function currentContextMenuDoc() {
    return state.docsById.get(state.contextMenuDocId) || null;
  }

  function docChildren(docId) {
    return state.childrenByParent.get(docId) || [];
  }

  function docHasChildren(docId) {
    return docChildren(docId).length > 0;
  }

  function managementDragEnabled() {
    return state.managementMode && state.managementAvailable && !state.managementBusy && !state.searchRouteActive;
  }

  function dragDropOptions() {
    return {
      dragDocId: state.dragDocId,
      dragEnabled: managementDragEnabled(),
      docsById: state.docsById,
      hasChildren: docHasChildren
    };
  }

  function canDragCurrentDoc(doc) {
    return canDragDoc(doc, dragDropOptions());
  }

  function currentStatusValue(doc) {
    return String(doc && doc.ui_status || "").trim();
  }

  function statusPillsCanWrite(doc) {
    return Boolean(
      doc &&
      state.managementMode &&
      state.managementAvailable &&
      !state.managementBusy &&
      !state.searchRouteActive
    );
  }

  function statusPillsCanRender(doc) {
    return Boolean(
      doc &&
      state.managementMode &&
      state.managementAvailable &&
      state.uiStatuses.length > 0 &&
      !state.searchRouteActive
    );
  }

  function renderStatusPills() {
    if (!statusPills) return;
    var doc = currentSelectedDoc();
    var canShow = statusPillsCanRender(doc);
    statusPills.hidden = !canShow;
    if (!canShow) {
      statusPills.innerHTML = "";
      state.statusMenuOpen = false;
      return;
    }

    var activeStatus = currentStatusValue(doc);
    var canWrite = statusPillsCanWrite(doc);
    var activeStatusConfig = activeStatus ? state.uiStatusByValue.get(activeStatus) : null;
    statusPills.innerHTML = renderStatusPillsMarkup({
      activeStatus: activeStatus,
      activeStatusConfig: activeStatusConfig,
      canWrite: canWrite,
      doc: doc,
      formatText: context.formatText,
      menuOpen: state.statusMenuOpen,
      statuses: state.uiStatuses,
      text: state.managementText
    });
  }

  function clearDragState() {
    state.dragDocId = "";
    state.dropTargetDocId = "";
    state.dropPosition = "";
    updateNavDragState();
  }

  function contextMenuEnabled() {
    return state.managementMode && state.managementAvailable;
  }

  function settingsModalOpen() {
    return Boolean(modalController && modalController.settingsModalOpen());
  }

  function hideContextMenu() {
    state.contextMenuDocId = "";
    if (contextMenu) {
      contextMenu.hidden = true;
      contextMenu.style.left = "";
      contextMenu.style.top = "";
    }
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

  function showContextMenu(docId, clientX, clientY) {
    if (!contextMenu || !contextMenuEnabled()) return;
    state.contextMenuDocId = docId;
    contextMenu.hidden = false;
    contextMenu.style.left = "0px";
    contextMenu.style.top = "0px";
    var menuRect = contextMenu.getBoundingClientRect();
    var maxLeft = Math.max(8, window.innerWidth - menuRect.width - 8);
    var maxTop = Math.max(8, window.innerHeight - menuRect.height - 8);
    contextMenu.style.left = Math.min(clientX, maxLeft) + "px";
    contextMenu.style.top = Math.min(clientY, maxTop) + "px";
  }

  function collectAllDescendantDocIds(docId, bucket) {
    state.allDocs.forEach(function (candidate) {
      if ((candidate.parent_id || "") !== docId || bucket.has(candidate.doc_id)) return;
      bucket.add(candidate.doc_id);
      collectAllDescendantDocIds(candidate.doc_id, bucket);
    });
    return bucket;
  }

  function metadataParentOptions(doc) {
    var blockedIds = collectAllDescendantDocIds(doc.doc_id, new Set([doc.doc_id]));
    var options = [{ value: "", label: state.managementText.metadataParentRootOption }];
    var docsByParent = buildChildrenMap(state.allDocs, {
      managementMode: state.managementMode,
      showHidden: state.showHidden
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

    docsImportRequestPromise = import("./docs-html-import.js")
      .then(function (module) {
        if (!module || typeof module.initDocsHtmlImport !== "function") {
          throw new Error("Docs Import module did not expose initDocsHtmlImport().");
        }
        return module.initDocsHtmlImport({
          root: importRoot,
          bootStatus: importBootStatus,
          initialScope: scope || viewerScope(),
          docsViewerConfigUrl: root.dataset.docsViewerConfigUrl || "/assets/docs-viewer/data/docs-viewer-config.json",
          uiTextUrl: root.dataset.uiTextUrl || "/assets/docs-viewer/data/ui-text.json",
          managementBaseUrl: context.managementBaseUrl,
          routePath: "/docs/",
          hideIntro: true
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

  function currentSettingsField(payload) {
    var scopes = payload && Array.isArray(payload.scopes) ? payload.scopes : [];
    var scopePayload = scopes.find(function (item) {
      return item && item.scope_id === viewerScope();
    }) || scopes[0] || null;
    var fields = scopePayload && Array.isArray(scopePayload.fields) ? scopePayload.fields : [];
    return fields.find(function (field) {
      return field && field.field === "show_updated_date";
    }) || null;
  }

  function openSettingsModal() {
    if (!modalController || !modalController.openSettingsModalShell()) return;

    readSourceConfigSettings(managementClientOptions())
      .then(function (payload) {
        var field = currentSettingsField(payload);
        if (!field) {
          throw new Error(state.managementText.settingsEmpty);
        }
        modalController.setSettingsField(field);
      })
      .catch(function (error) {
        modalController.setSettingsLoadError(error.message || state.managementText.settingsLoadFailed);
      });
  }

  function openMetadataModal() {
    var doc = currentSelectedDoc();
    return modalController ? modalController.openMetadataModal(doc) : Promise.resolve(null);
  }

  function updateNavDragState() {
    if (!nav) return;
    nav.querySelectorAll(".docsViewer__navRow").forEach(function (row) {
      row.classList.remove("is-dragging", "is-drop-after", "is-drop-inside");
    });
    if (state.dragDocId) {
      var dragRow = nav.querySelector('[data-doc-row-id="' + context.cssEscape(state.dragDocId) + '"]');
      if (dragRow) {
        dragRow.classList.add("is-dragging");
      }
    }
    if (state.dropTargetDocId && state.dropPosition) {
      var dropRow = nav.querySelector('[data-doc-row-id="' + context.cssEscape(state.dropTargetDocId) + '"]');
      if (dropRow) {
        dropRow.classList.add(state.dropPosition === "inside" ? "is-drop-inside" : "is-drop-after");
      }
    }
  }

  function managementArchiveAvailable() {
    return scopeArchiveAvailable(state.managementCapabilities, viewerScope());
  }

  function managementNoteText() {
    if (state.managementMessage) return state.managementMessage;
    if (state.searchRouteActive) {
      return state.managementText.clearSearchNote;
    }
    if (!managementArchiveAvailable()) {
      return state.managementText.archiveUnavailableNote;
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

  function renderManagementUi() {
    if (!manageRow) return;

    state.managementMode = context.getCurrentMode() === context.MANAGEMENT_MODE;
    if (!state.managementMode) {
      syncManagementStatus("", false);
      manageRow.hidden = true;
      hideManageActionsMenu();
      if (indexUndoButton) {
        indexUndoButton.hidden = true;
      }
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
      noteText = state.managementText.checkingNote;
    } else if (!state.managementAvailable) {
      noteText = state.managementText.unavailableNote;
      noteIsError = true;
    } else {
      noteText = managementNoteText();
      noteIsError = state.managementMessageIsError;
    }
    syncManagementStatus(noteText, noteIsError);

    if (indexUndoButton) {
      indexUndoButton.hidden = !state.managementMode;
      indexUndoButton.disabled = (
        state.managementBusy ||
        !state.managementChecked ||
        !state.managementAvailable ||
        !state.moveUndo
      );
      indexUndoButton.setAttribute("aria-label", state.managementText.undoMoveLabel);
      indexUndoButton.title = state.managementText.undoMoveLabel;
    }

    if (!manageRebuildButton || !manageNewButton || !manageEditButton || !manageArchiveButton || !manageDeleteButton || !manageViewableButton) return;

    var doc = currentSelectedDoc();
    var draftDoc = Boolean(doc && isDocHidden(doc));
    var editDisabled = (
      state.managementBusy ||
      !doc ||
      state.searchRouteActive
    );
    var archiveDisabled = (
      state.managementBusy ||
      !doc ||
      state.searchRouteActive ||
      !managementArchiveAvailable() ||
      doc.parent_id === "archive"
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
    if (manageImportButton) {
      manageImportButton.disabled = state.managementBusy || !state.managementAvailable;
    }
    if (manageSettingsButton) {
      manageSettingsButton.disabled = state.managementBusy || !state.managementAvailable;
    }
    manageNewButton.disabled = state.managementBusy || !state.managementAvailable;
    manageEditButton.disabled = !state.managementAvailable || editDisabled;
    manageArchiveButton.disabled = !state.managementAvailable || archiveDisabled;
    manageDeleteButton.disabled = !state.managementAvailable || deleteDisabled;
    manageViewableButton.disabled = !state.managementAvailable || viewableDisabled;
    if (draftToggle) {
      draftToggle.disabled = !state.managementAvailable || state.managementBusy;
      draftToggle.checked = state.showHidden;
    }
    if (metadataSaveButton) {
      metadataSaveButton.disabled = state.managementBusy;
    }
    if (settingsSaveButton && settingsModalOpen()) {
      settingsSaveButton.disabled = state.managementBusy || !modalController.getSettingsFieldState();
    }
    renderStatusPills();
  }

  function initializeManagement() {
    if (capabilityController) capabilityController.initialize();
  }

  function refreshManagementCapabilities() {
    if (capabilityController) capabilityController.refresh();
  }

  function reloadDocsIndex(targetDocId, summaryText) {
    state.payloadCache.clear();
    state.searchEntries = [];
    state.searchLoaded = false;
    state.searchRequestPromise = null;
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
      context.setHistory(targetDocId, "", "", "replace");
    }

    return context.loadIndex().then(function () {
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
    if (!doc || !metadataTitleInput || !metadataSummaryInput || !metadataStatusInput || !metadataHiddenInput || !metadataParentInput || !metadataSortOrderInput) return null;

    var title = String(metadataTitleInput.value || "").trim();
    if (!title) {
      metadataTitleInput.focus();
      return null;
    }

    var parentId = modalController.resolveMetadataParentId(doc);
    if (parentId === null) {
      setManagementMessage(state.managementText.metadataParentInvalid, true);
      metadataParentInput.focus();
      return null;
    }
    var originalParentId = String(doc.parent_id || "").trim();
    var originalSortOrderText = normalizeSortOrderValue(doc.sort_order);
    var sortOrderText = String(metadataSortOrderInput.value || "").trim();
    if (sortOrderText && Number(sortOrderText) < 0) {
      setManagementMessage("sort_order must be zero or greater.", true);
      metadataSortOrderInput.focus();
      return null;
    }
    var payloadSortOrder = sortOrderText;
    if (parentId && parentId !== originalParentId && sortOrderText === originalSortOrderText) {
      payloadSortOrder = "append";
    }
    var selectedStatus = String(metadataStatusInput.value || "").trim();
    return {
      doc_id: doc.doc_id,
      title: title,
      summary: String(metadataSummaryInput.value || "").replace(/\s+/g, " ").trim(),
      ui_status: selectedStatus,
      hidden: metadataHiddenInput.checked,
      parent_id: parentId,
      sort_order: payloadSortOrder
    };
  }

  function confirmMetadataModal() {
    var payload = metadataPayloadFromModal();
    if (!payload) return;
    modalController.closeMetadataModal(payload);
  }

  function scopeLifecycleCallbacks() {
    return {
      onApplied: refreshManagementCapabilities,
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
          typeof module.openDeleteScopeFlow !== "function"
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

  function handleDraftToggleChange() {
    if (!draftToggle) return;
    state.showHidden = Boolean(draftToggle.checked);
    state.managementMode = context.getCurrentMode() === context.MANAGEMENT_MODE;
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
      context.loadDoc(targetDocId, { historyMode: "replace", hash: "" });
    }
  }

  function applyConfig(config) {
    applyDocsViewerManagementConfig({
      config: config,
      context: context,
      state: state,
      refs: {
        contextCopyLinkButton: contextCopyLinkButton,
        draftLabel: draftLabel,
        draftToggle: draftToggle,
        manageDeleteScopeButton: manageDeleteScopeButton,
        manageNewScopeButton: manageNewScopeButton,
        manageSettingsButton: manageSettingsButton,
        manageViewableButton: manageViewableButton,
        metadataHiddenLabel: metadataHiddenLabel,
        metadataStatusInput: metadataStatusInput,
        metadataStatusLabel: metadataStatusLabel,
        settingsHeading: settingsHeading,
        settingsUpdatedLabel: settingsUpdatedLabel
      },
      modalController: modalController
    });
  }

  function handleRootClick(event) {
    if (contextMenu && !event.target.closest("#docsViewerContextMenu")) {
      hideContextMenu();
    }
    if (state.statusMenuOpen && statusPills && !statusPills.contains(event.target)) {
      state.statusMenuOpen = false;
      renderStatusPills();
    }
    if (manageActionsMenu && !event.target.closest(".docsViewer__manageActions")) {
      hideManageActionsMenu();
    }
    return modalController ? modalController.handleRootClick(event) : false;
  }

  function handleDocumentKeydown(event) {
    if (event.key === "Escape" && state.statusMenuOpen) {
      event.preventDefault();
      state.statusMenuOpen = false;
      renderStatusPills();
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
    if (nav) {
      nav.addEventListener("mousedown", function (event) {
        var row = event.target.closest("[data-doc-row-id]");
        if (!row || !contextMenuEnabled() || event.button !== 2) return;
        event.preventDefault();
        if (window.getSelection) {
          var selection = window.getSelection();
          if (selection) selection.removeAllRanges();
        }
      });

      nav.addEventListener("contextmenu", function (event) {
        var row = event.target.closest("[data-doc-row-id]");
        if (!row || !contextMenuEnabled()) return;
        event.preventDefault();
        if (window.getSelection) {
          var selection = window.getSelection();
          if (selection) selection.removeAllRanges();
        }
        showContextMenu(row.dataset.docRowId || "", event.clientX, event.clientY);
      });

      nav.addEventListener("dragstart", function (event) {
        var dragHandle = event.target.closest("[data-drag-doc-id]");
        if (!dragHandle || !managementDragEnabled()) return;
        hideContextMenu();
        state.dragDocId = dragHandle.dataset.dragDocId || "";
        state.dropTargetDocId = "";
        state.dropPosition = "";
        if (event.dataTransfer) {
          event.dataTransfer.effectAllowed = "move";
          event.dataTransfer.setData("text/plain", state.dragDocId);
        }
        updateNavDragState();
      });

      nav.addEventListener("dragover", function (event) {
        var row = event.target.closest("[data-doc-row-id]");
        if (!row) {
          if (state.dropTargetDocId || state.dropPosition) {
            state.dropTargetDocId = "";
            state.dropPosition = "";
            updateNavDragState();
          }
          return;
        }

        var targetDocId = row.dataset.docRowId || "";
        var dropOptions = dragDropOptions();
        var nextPosition = rowDropPosition(row, event, dropOptions);
        if (!canDropOnDoc(targetDocId, nextPosition, dropOptions)) {
          if (state.dropTargetDocId || state.dropPosition) {
            state.dropTargetDocId = "";
            state.dropPosition = "";
            updateNavDragState();
          }
          return;
        }

        event.preventDefault();
        if (event.dataTransfer) {
          event.dataTransfer.dropEffect = "move";
        }
        if (state.dropTargetDocId !== targetDocId || state.dropPosition !== nextPosition) {
          state.dropTargetDocId = targetDocId;
          state.dropPosition = nextPosition;
          updateNavDragState();
        }
      });

      nav.addEventListener("drop", function (event) {
        event.preventDefault();
        var dropOptions = dragDropOptions();
        var dropTarget = currentDropTargetFromEvent(event, {
          targetDocId: state.dropTargetDocId,
          position: state.dropPosition
        }, dropOptions);
        var targetDocId = dropTarget.targetDocId;
        var position = dropTarget.position;
        if ((!targetDocId || !position) && state.dropTargetDocId && state.dropPosition) {
          targetDocId = state.dropTargetDocId;
          position = state.dropPosition;
        }
        if (!canDropOnDoc(targetDocId, position, dropOptions) || !position) {
          clearDragState();
          return;
        }
        var movingDocId = state.dragDocId;
        clearDragState();
        actionController.handleMoveDoc(movingDocId, targetDocId, position);
      });

      nav.addEventListener("dragend", function () {
        clearDragState();
      });
    }

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
      manageSettingsButton.addEventListener("click", openSettingsModal);
    }
    if (manageNewScopeButton) {
      manageNewScopeButton.addEventListener("click", function () {
        handleCreateScope();
      });
    }
    if (manageDeleteScopeButton) {
      manageDeleteScopeButton.addEventListener("click", function () {
        handleDeleteScope();
      });
    }
    if (manageActionsButton) {
      manageActionsButton.addEventListener("click", function () {
        toggleManageActionsMenu();
      });
    }
    if (indexUndoButton) {
      indexUndoButton.addEventListener("click", actionController.handleUndoMove);
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
    if (manageArchiveButton) {
      manageArchiveButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        actionController.handleArchiveDoc();
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
    if (contextMenu) {
      contextMenu.addEventListener("click", function (event) {
        var action = event.target.closest("[data-context-action]");
        if (!action) return;
        if (action.dataset.contextAction === "new-sibling") {
          actionController.handleCreateRelatedDoc("sibling");
          return;
        }
        if (action.dataset.contextAction === "new-child") {
          actionController.handleCreateRelatedDoc("child");
          return;
        }
        if (action.dataset.contextAction === "copy-link") {
          actionController.handleCopyLink();
          return;
        }
        if (action.dataset.contextAction === "open-vscode") {
          actionController.handleOpenSource("vscode");
          return;
        }
        if (action.dataset.contextAction === "open") {
          actionController.handleOpenSource("default");
        }
      });
    }
    if (statusPills) {
      statusPills.addEventListener("click", function (event) {
        var toggle = event.target.closest("[data-ui-status-menu-toggle]");
        if (toggle) {
          event.preventDefault();
          event.stopPropagation();
          if (toggle.disabled) return;
          state.statusMenuOpen = !state.statusMenuOpen;
          renderStatusPills();
          return;
        }
        var button = event.target.closest("[data-ui-status]");
        if (!button) return;
        event.preventDefault();
        event.stopPropagation();
        state.statusMenuOpen = false;
        actionController.handleStatusPillClick(button.dataset.uiStatus);
      });
    }
    document.addEventListener("click", function (event) {
      if (!state.statusMenuOpen || !statusPills || statusPills.contains(event.target)) return;
      state.statusMenuOpen = false;
      renderStatusPills();
    });
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

  actionController = createDocsViewerManagementActionController({
    root: root,
    state: state,
    context: context,
    refs: {
      settingsUpdatedInput: settingsUpdatedInput
    },
    callbacks: {
      clearDragState: clearDragState,
      currentContextMenuDoc: currentContextMenuDoc,
      currentSelectedDoc: currentSelectedDoc,
      currentStatusValue: currentStatusValue,
      getModalController: function () {
        return modalController;
      },
      hideContextMenu: hideContextMenu,
      managementClientOptions: managementClientOptions,
      reloadDocsIndex: reloadDocsIndex,
      renderManagementUi: renderManagementUi,
      renderStatusPills: renderStatusPills,
      setManagementBusy: setManagementBusy,
      setManagementMessage: setManagementMessage,
      statusPillsCanWrite: statusPillsCanWrite
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
      metadataHiddenInput: metadataHiddenInput,
      metadataModal: metadataModal,
      metadataParentInput: metadataParentInput,
      metadataParentPopup: metadataParentPopup,
      metadataSortOrderInput: metadataSortOrderInput,
      metadataStatusInput: metadataStatusInput,
      metadataSummaryInput: metadataSummaryInput,
      metadataTitleInput: metadataTitleInput,
      settingsCancelButton: settingsCancelButton,
      settingsForm: settingsForm,
      settingsModal: settingsModal,
      settingsSaveButton: settingsSaveButton,
      settingsScope: settingsScope,
      settingsStatus: settingsStatus,
      settingsUpdatedInput: settingsUpdatedInput,
      settingsWarnings: settingsWarnings,
      manageSettingsButton: manageSettingsButton
    },
    callbacks: {
      currentSelectedDoc: currentSelectedDoc,
      hideContextMenu: hideContextMenu,
      hideManageActionsMenu: hideManageActionsMenu,
      isDocHidden: isDocHidden,
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
    renderStatusPills: renderStatusPills,
    updateNavDragState: updateNavDragState
  };
}
