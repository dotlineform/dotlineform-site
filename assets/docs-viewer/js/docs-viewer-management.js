import {
  buildChildrenMap,
  isDocHidden,
  isDocViewable
} from "./docs-viewer-tree.js";
import {
  applyManagedDocDelete,
  archiveManagedDoc,
  createManagedDoc,
  moveManagedDoc,
  openManagedDocSource,
  previewManagedDocDelete,
  readManagementCapabilities,
  readSourceConfigSettings,
  rebuildManagedDocs,
  restoreManagedDocMove,
  scopeSupportsGeneratedDataReads,
  updateSourceConfigSettings,
  updateManagedDocMetadata,
  updateManagedDocsViewability
} from "./docs-viewer-management-client.js";
import {
  canDragDoc,
  canDropOnDoc,
  currentDropTargetFromEvent,
  moveUndoPayloadRecords,
  moveUndoRecordChanged,
  normalizeMoveUndoRecords,
  normalizeSortOrderValue,
  rowDropPosition
} from "./docs-viewer-drag-drop.js";

export function initDocsViewerManagement(context) {
  var root = context.root;
  var nav = context.nav;
  var state = context.state;
  var manageRow = document.getElementById("docsViewerManageRow");
  var manageActions = manageRow ? manageRow.querySelector(".docsViewer__manageActions") : null;
  var manageNote = document.getElementById("docsViewerManageNote");
  var manageActionsButton = document.getElementById("docsViewerManageActionsButton");
  var manageActionsMenu = document.getElementById("docsViewerManageActionsMenu");
  var manageRebuildButton = document.getElementById("docsViewerManageRebuildButton");
  var manageSettingsButton = document.getElementById("docsViewerManageSettingsButton");
  var manageImportButton = document.getElementById("docsViewerManageImportButton");
  var manageNewButton = document.getElementById("docsViewerManageNewButton");
  var manageEditButton = document.getElementById("docsViewerManageEditButton");
  var manageArchiveButton = document.getElementById("docsViewerManageArchiveButton");
  var manageDeleteButton = document.getElementById("docsViewerManageDeleteButton");
  var manageViewableButton = document.getElementById("docsViewerManageViewableButton");
  var contextCopyLinkButton = contextMenu ? contextMenu.querySelector('[data-context-action="copy-link"]') : null;
  var draftToggle = document.getElementById("docsViewerDraftToggle");
  var draftLabel = document.querySelector(".docsViewer__draftLabel");
  var indexUndoButton = document.getElementById("docsViewerIndexUndoButton");
  var contextMenu = document.getElementById("docsViewerContextMenu");
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
  var metadataParentList = document.getElementById("docsViewerMetadataParentList");
  var metadataSortOrderInput = document.getElementById("docsViewerMetadataSortOrderInput");
  var metadataCloseButton = document.getElementById("docsViewerMetadataCloseButton");
  var metadataCancelButton = document.getElementById("docsViewerMetadataCancelButton");
  var metadataSaveButton = document.getElementById("docsViewerMetadataSaveButton");
  var importModal = document.getElementById("docsViewerImportModal");
  var importRoot = document.getElementById("docsHtmlImportRoot");
  var importBootStatus = document.getElementById("docsHtmlImportBootStatus");
  var importScope = document.getElementById("docsViewerImportScope");
  var importCloseButton = document.getElementById("docsViewerImportCloseButton");
  var settingsModal = document.getElementById("docsViewerSettingsModal");
  var settingsForm = document.getElementById("docsViewerSettingsForm");
  var settingsHeading = document.getElementById("docsViewerSettingsHeading");
  var settingsScope = document.getElementById("docsViewerSettingsScope");
  var settingsUpdatedInput = document.getElementById("docsViewerSettingsUpdatedInput");
  var settingsUpdatedLabel = document.getElementById("docsViewerSettingsUpdatedLabel");
  var settingsWarnings = document.getElementById("docsViewerSettingsWarnings");
  var settingsStatus = document.getElementById("docsViewerSettingsStatus");
  var settingsCloseButton = document.getElementById("docsViewerSettingsCloseButton");
  var settingsCancelButton = document.getElementById("docsViewerSettingsCancelButton");
  var settingsSaveButton = document.getElementById("docsViewerSettingsSaveButton");
  var docsImportRequestPromise = null;
  var docsImportInitialized = false;
  var metadataModalResolve = null;
  var settingsFieldState = null;

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

  function scopeManagementCapabilities() {
    if (!state.managementCapabilities || !state.managementCapabilities.scopes) return null;
    return state.managementCapabilities.scopes[viewerScope()] || null;
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

  function clearDragState() {
    state.dragDocId = "";
    state.dropTargetDocId = "";
    state.dropPosition = "";
    updateNavDragState();
  }

  function contextMenuEnabled() {
    return state.managementMode && state.managementAvailable;
  }

  function metadataModalOpen() {
    return Boolean(metadataModal && !metadataModal.hidden);
  }

  function importModalOpen() {
    return Boolean(importModal && !importModal.hidden);
  }

  function settingsModalOpen() {
    return Boolean(settingsModal && !settingsModal.hidden);
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

  function nonViewableAncestorDocs(doc) {
    var ancestors = [];
    var current = doc && doc.parent_id ? context.findAllDocById(doc.parent_id) : null;
    while (current) {
      if (!isDocViewable(current)) {
        ancestors.unshift(current);
      }
      current = current.parent_id ? context.findAllDocById(current.parent_id) : null;
    }
    return ancestors;
  }

  function docTitleList(docs) {
    return docs.map(function (item) {
      return item.title || item.doc_id;
    }).join(", ");
  }

  function viewabilityTargetDocIds(doc) {
    var ancestors = nonViewableAncestorDocs(doc);
    if (ancestors.length) {
      var ancestorMessage = context.formatText(state.managementText.viewableAncestorPrompt, {
        titles: docTitleList(ancestors)
      });
      if (!window.confirm(ancestorMessage)) {
        return null;
      }
    }

    var includeDescendants = false;
    var descendantIds = Array.from(collectAllDescendantDocIds(doc.doc_id, new Set()));
    if (descendantIds.length) {
      var descendantChoice = window.prompt(
        state.managementText.viewableDescendantPrompt,
        "selected"
      );
      if (descendantChoice === null) {
        return null;
      }
      var normalizedChoice = descendantChoice.trim().toLowerCase();
      if (normalizedChoice === "all") {
        includeDescendants = true;
      } else if (normalizedChoice !== "selected") {
        setManagementMessage(state.managementText.viewableInvalidChoice, true);
        context.setStatus(state.managementText.viewableInvalidChoice, true);
        return null;
      }
    }

    var targetIds = new Set();
    ancestors.forEach(function (ancestor) {
      targetIds.add(ancestor.doc_id);
    });
    targetIds.add(doc.doc_id);
    if (includeDescendants) {
      descendantIds.forEach(function (docId) {
        targetIds.add(docId);
      });
    }
    return Array.from(targetIds);
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

  function metadataParentOptionDisplay(option) {
    if (!option || !option.value) return state.managementText.metadataParentRootOption;
    return option.label + " [" + option.value + "]";
  }

  function renderMetadataParentOptions(doc) {
    if (!metadataParentInput || !metadataParentList) return;
    metadataParentInput.setAttribute("list", "docsViewerMetadataParentList");
    var currentParentId = String(doc && doc.parent_id || "").trim();
    var options = metadataParentOptions(doc);
    var currentOption = options.find(function (option) {
      return option.value === currentParentId;
    }) || options[0];
    metadataParentInput.value = metadataParentOptionDisplay(currentOption);
    metadataParentList.innerHTML = options.map(function (option) {
      return '<option value="' + context.escapeHtml(metadataParentOptionDisplay(option)) + '"></option>';
    }).join("");
  }

  function resolveMetadataParentId(doc) {
    if (!metadataParentInput) return "";
    var inputValue = String(metadataParentInput.value || "").trim();
    var rootLabel = state.managementText.metadataParentRootOption;
    if (!inputValue || inputValue.toLowerCase() === rootLabel.toLowerCase()) return "";
    var options = metadataParentOptions(doc);
    var exactDisplay = options.find(function (option) {
      return metadataParentOptionDisplay(option) === inputValue;
    });
    if (exactDisplay) return exactDisplay.value;
    var exactDocId = options.find(function (option) {
      return option.value && option.value === inputValue;
    });
    if (exactDocId) return exactDocId.value;
    var exactTitle = options.filter(function (option) {
      return option.value && option.label.replace(/^(-\s*)+/, "") === inputValue;
    });
    if (exactTitle.length === 1) return exactTitle[0].value;
    return null;
  }

  function metadataStatusOptions() {
    var options = [{
      value: "",
      label: state.managementText.metadataStatusNoneOption
    }];
    state.uiStatuses.forEach(function (status) {
      options.push({
        value: status.ui_status,
        label: status.emoji + " " + status.label
      });
    });
    return options;
  }

  function renderMetadataStatusOptions(doc) {
    if (!metadataStatusInput) return;
    var selectedValue = String(doc && doc.ui_status || "").trim();
    renderMetadataStatusSelection(selectedValue);
  }

  function renderMetadataStatusSelection(selectedValue) {
    if (!metadataStatusInput) return;
    metadataStatusInput.innerHTML = metadataStatusOptions().map(function (option) {
      var selected = option.value === selectedValue ? " selected" : "";
      var label = option.label + (selected ? state.managementText.metadataStatusSelectedSuffix : "");
      return '<option value="' + context.escapeHtml(option.value) + '"' + selected + ">" + context.escapeHtml(label) + "</option>";
    }).join("");
    metadataStatusInput.size = Math.max(1, metadataStatusInput.options.length);
  }

  function dismissMetadataParentSuggestions() {
    if (!metadataParentInput) return;
    metadataParentInput.blur();
    metadataParentInput.value = "";
    metadataParentInput.removeAttribute("list");
    if (metadataParentList) {
      metadataParentList.innerHTML = "";
    }
  }

  function closeMetadataModal(result) {
    if (!metadataModal) return;
    if (document.activeElement && metadataModal.contains(document.activeElement)) {
      document.activeElement.blur();
    }
    dismissMetadataParentSuggestions();
    metadataModal.hidden = true;
    state.metadataEditingDocId = "";
    var restoreDocId = state.metadataRestoreFocusId;
    state.metadataRestoreFocusId = "";
    if (metadataModalResolve) {
      var resolve = metadataModalResolve;
      metadataModalResolve = null;
      resolve(result || null);
    }
    if (!restoreDocId || !nav) return;
    var target = nav.querySelector('[data-doc-row-id="' + context.cssEscape(restoreDocId) + '"] .docsViewer__navLink');
    if (target) target.focus();
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
    if (!importModal || !importRoot) return;
    var scope = viewerScope();
    if (importScope) {
      importScope.textContent = "scope: " + scope;
    }
    importModal.hidden = false;
    initializeImportModal(scope);
    if (importCloseButton) {
      importCloseButton.focus();
    }
  }

  function closeImportModal() {
    if (!importModal) return;
    if (document.activeElement && importModal.contains(document.activeElement)) {
      document.activeElement.blur();
    }
    importModal.hidden = true;
    if (manageImportButton) {
      manageImportButton.focus();
    }
  }

  function setSettingsStatus(message, stateName) {
    if (!settingsStatus) return;
    settingsStatus.textContent = String(message || "");
    settingsStatus.dataset.state = stateName || "";
    settingsStatus.hidden = !message;
  }

  function renderSettingsWarnings(warnings) {
    if (!settingsWarnings) return;
    var items = Array.isArray(warnings) ? warnings.filter(Boolean) : [];
    settingsWarnings.hidden = items.length === 0;
    settingsWarnings.innerHTML = items.length
      ? '<ul>' + items.map(function (item) {
        return '<li>' + context.escapeHtml(item) + '</li>';
      }).join("") + '</ul>'
      : "";
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
    if (!settingsModal || !settingsForm || !settingsUpdatedInput) return;
    hideContextMenu();
    hideManageActionsMenu();
    settingsFieldState = null;
    settingsUpdatedInput.disabled = true;
    if (settingsSaveButton) settingsSaveButton.disabled = true;
    if (settingsScope) settingsScope.textContent = "scope: " + viewerScope();
    setSettingsStatus(state.managementText.settingsLoading, "");
    renderSettingsWarnings([]);
    settingsModal.hidden = false;

    readSourceConfigSettings(managementClientOptions())
      .then(function (payload) {
        var field = currentSettingsField(payload);
        if (!field) {
          throw new Error(state.managementText.settingsEmpty);
        }
        settingsFieldState = field;
        settingsUpdatedInput.checked = field.current_value !== false;
        settingsUpdatedInput.disabled = false;
        if (settingsSaveButton) settingsSaveButton.disabled = state.managementBusy;
        renderSettingsWarnings(field.warnings || []);
        setSettingsStatus("", "");
        window.requestAnimationFrame(function () {
          settingsUpdatedInput.focus();
        });
      })
      .catch(function (error) {
        settingsUpdatedInput.disabled = true;
        if (settingsSaveButton) settingsSaveButton.disabled = true;
        renderSettingsWarnings([]);
        setSettingsStatus(error.message || state.managementText.settingsLoadFailed, "error");
      });
  }

  function closeSettingsModal() {
    if (!settingsModal) return;
    if (document.activeElement && settingsModal.contains(document.activeElement)) {
      document.activeElement.blur();
    }
    settingsModal.hidden = true;
    settingsFieldState = null;
    if (manageSettingsButton) {
      manageSettingsButton.focus();
    }
  }

  function openMetadataModal() {
    var doc = currentSelectedDoc();
    if (!doc || !metadataModal || !metadataForm || !metadataTitleInput || !metadataSummaryInput || !metadataStatusInput || !metadataHiddenInput || !metadataParentInput || !metadataSortOrderInput) {
      return Promise.resolve(null);
    }
    hideContextMenu();
    state.metadataEditingDocId = doc.doc_id;
    state.metadataRestoreFocusId = doc.doc_id;
    if (metadataDocId) {
      metadataDocId.textContent = doc.doc_id;
    }

    metadataTitleInput.value = doc.title || "";
    metadataSummaryInput.value = doc.summary || "";
    renderMetadataStatusOptions(doc);
    metadataHiddenInput.checked = isDocHidden(doc);
    metadataSortOrderInput.value = doc.sort_order == null ? "" : String(doc.sort_order);
    metadataSortOrderInput.min = "0";
    renderMetadataParentOptions(doc);

    metadataModal.hidden = false;
    window.requestAnimationFrame(function () {
      metadataTitleInput.focus();
      metadataTitleInput.select();
    });
    return new Promise(function (resolve) {
      metadataModalResolve = resolve;
    });
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
    var scopeCaps = scopeManagementCapabilities();
    return Boolean(scopeCaps && scopeCaps.archive_available);
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

  function renderManagementUi() {
    if (!manageRow) return;

    state.managementMode = context.getCurrentMode() === context.MANAGEMENT_MODE;
    if (!state.managementMode) {
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

    if (manageNote) {
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
      manageNote.textContent = noteText;
      manageNote.hidden = !noteText;
      manageNote.classList.toggle("is-error", noteIsError);
    }

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
      settingsSaveButton.disabled = state.managementBusy || !settingsFieldState;
    }
    context.renderStatusPills();
  }

  function initializeManagement() {
    state.managementMode = context.getCurrentMode() === context.MANAGEMENT_MODE;
    renderManagementUi();
    if (!state.managementMode) return;

    if (!context.managementBaseUrl) {
      state.managementChecked = true;
      state.managementAvailable = false;
      renderManagementUi();
      return;
    }

    state.managementCapabilityCheckId += 1;
    checkManagementCapabilities(0, state.managementCapabilityCheckId);
  }

  function checkManagementCapabilities(attempt, checkId) {
    readManagementCapabilities(managementClientOptions())
      .then(function (payload) {
        if (checkId !== state.managementCapabilityCheckId) return;
        var scopeCaps = payload && payload.capabilities && payload.capabilities.scopes
          ? payload.capabilities.scopes[viewerScope()]
          : null;
        state.managementCapabilities = payload.capabilities || null;
        state.generatedDataReadAvailable = scopeSupportsGeneratedDataReads(state.managementCapabilities, viewerScope());
        state.generatedDataReadChecked = true;
        state.managementChecked = true;
        state.managementAvailable = Boolean(scopeCaps && scopeCaps.available);
        renderManagementUi();
        context.renderSidebar();
      })
      .catch(function () {
        if (checkId !== state.managementCapabilityCheckId) return;
        if (attempt < context.MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS - 1) {
          window.setTimeout(function () {
            checkManagementCapabilities(attempt + 1, checkId);
          }, context.MANAGEMENT_CAPABILITY_RETRY_DELAY_MS);
          return;
        }
        state.managementCapabilities = null;
        state.managementChecked = true;
        state.managementAvailable = false;
        renderManagementUi();
      });
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

  function handleCreateDoc() {
    var titleInput = window.prompt("New doc title", "New Doc");
    if (titleInput == null) return;

    var title = String(titleInput || "").trim() || "New Doc";
    var currentDoc = currentSelectedDoc();

    setManagementBusy(true);
    setManagementMessage("Creating doc...", false);
    context.setStatus("Creating doc...", false);

    createManagedDoc({
      title: title,
      after_doc_id: currentDoc ? currentDoc.doc_id : ""
    }, managementClientOptions())
      .then(function (payload) {
        setManagementMessage("", false);
        return reloadDocsIndex(payload.doc_id, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Create failed.", true);
        context.setStatus(error.message || "Create failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleCreateRelatedDoc(kind) {
    var baseDoc = currentContextMenuDoc();
    if (!baseDoc) return;

    var titleInput = window.prompt(kind === "child" ? "New child title" : "New sibling title", "New Doc");
    if (titleInput == null) return;

    var title = String(titleInput || "").trim() || "New Doc";
    var payload = {
      title: title
    };
    if (kind === "child") {
      payload.parent_id = baseDoc.doc_id;
    } else {
      payload.after_doc_id = baseDoc.doc_id;
    }

    setManagementBusy(true);
    hideContextMenu();
    setManagementMessage("Creating doc...", false);
    context.setStatus("Creating doc...", false);

    createManagedDoc(payload, managementClientOptions())
      .then(function (response) {
        setManagementMessage("", false);
        return reloadDocsIndex(response.doc_id, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Create failed.", true);
        context.setStatus(error.message || "Create failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function metadataPayloadFromModal() {
    var doc = state.metadataEditingDocId ? state.docsById.get(state.metadataEditingDocId) : currentSelectedDoc();
    if (!doc || !metadataTitleInput || !metadataSummaryInput || !metadataStatusInput || !metadataHiddenInput || !metadataParentInput || !metadataSortOrderInput) return null;

    var title = String(metadataTitleInput.value || "").trim();
    if (!title) {
      metadataTitleInput.focus();
      return null;
    }

    var parentId = resolveMetadataParentId(doc);
    if (parentId === null) {
      setManagementMessage(state.managementText.metadataParentInvalid, true);
      context.setStatus(state.managementText.metadataParentInvalid, true);
      metadataParentInput.focus();
      return null;
    }
    var originalParentId = String(doc.parent_id || "").trim();
    var originalSortOrderText = normalizeSortOrderValue(doc.sort_order);
    var sortOrderText = String(metadataSortOrderInput.value || "").trim();
    if (sortOrderText && Number(sortOrderText) < 0) {
      setManagementMessage("sort_order must be zero or greater.", true);
      context.setStatus("sort_order must be zero or greater.", true);
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
    closeMetadataModal(payload);
  }

  function handleEditMetadataSave(payload) {
    if (!payload) return;
    var doc = state.docsById.get(payload.doc_id);
    var title = doc && doc.title ? doc.title : payload.title;

    setManagementBusy(true);
    renderManagementUi();
    setManagementMessage("Saving metadata for " + title + "...", false);
    context.setStatus("Saving metadata for " + title + "...", false);

    updateManagedDocMetadata(payload, managementClientOptions())
      .then(function (response) {
        setManagementMessage("", false);
        return reloadDocsIndex(payload.doc_id, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Metadata update failed.", true);
        context.setStatus(error.message || "Metadata update failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function metadataPayloadForStatus(doc, uiStatus) {
    return {
      doc_id: doc.doc_id,
      title: String(doc.title || "").trim(),
      summary: String(doc.summary || "").replace(/\s+/g, " ").trim(),
      ui_status: String(uiStatus || "").trim(),
      hidden: isDocHidden(doc),
      parent_id: String(doc.parent_id || "").trim(),
      sort_order: normalizeSortOrderValue(doc.sort_order)
    };
  }

  function handleStatusPillClick(statusValue) {
    var doc = currentSelectedDoc();
    if (!context.statusPillsCanWrite(doc)) return;
    var selectedStatus = String(statusValue || "").trim();
    if (!selectedStatus || !state.uiStatusByValue.has(selectedStatus)) return;

    var nextStatus = context.currentStatusValue(doc) === selectedStatus ? "" : selectedStatus;
    var savingText = context.formatText(state.managementText.statusPillSaving, { title: doc.title });

    setManagementBusy(true);
    setManagementMessage(savingText, false);
    context.setStatus(savingText, false);
    context.renderStatusPills();

    updateManagedDocMetadata(metadataPayloadForStatus(doc, nextStatus), managementClientOptions())
      .then(function (response) {
        setManagementMessage("", false);
        return reloadDocsIndex(doc.doc_id, "");
      })
      .catch(function (error) {
        var failedText = error.message || state.managementText.statusPillFailed;
        setManagementMessage(failedText, true);
        context.setStatus(failedText, true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
        context.renderStatusPills();
      });
  }

  function handleRebuildDocs() {
    setManagementBusy(true);
    setManagementMessage("Rebuilding docs...", false);
    context.setStatus("Rebuilding docs...", false);

    rebuildManagedDocs(managementClientOptions())
      .then(function (payload) {
        var targetDocId = state.selectedDocId || context.defaultRouteDocId() || context.defaultDocId();
        setManagementMessage("", false);
        return reloadDocsIndex(targetDocId, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Docs rebuild failed.", true);
        context.setStatus(error.message || "Docs rebuild failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleSettingsSave() {
    if (!settingsUpdatedInput || !settingsFieldState) return;
    var nextValue = Boolean(settingsUpdatedInput.checked);
    var currentValue = settingsFieldState.current_value !== false;
    if (nextValue === currentValue) {
      closeSettingsModal();
      return;
    }

    setManagementBusy(true);
    setSettingsStatus(state.managementText.settingsSaving, "");
    setManagementMessage(state.managementText.settingsSaving, false);
    context.setStatus(state.managementText.settingsSaving, false);
    settingsUpdatedInput.disabled = true;
    if (settingsSaveButton) settingsSaveButton.disabled = true;

    updateSourceConfigSettings({
      show_updated_date: nextValue
    }, managementClientOptions())
      .then(function (payload) {
        renderSettingsWarnings(payload.warnings || []);
        var targetDocId = state.selectedDocId || context.defaultRouteDocId() || context.defaultDocId();
        setManagementMessage("", false);
        return reloadDocsIndex(targetDocId, "").then(function () {
          closeSettingsModal();
        });
      })
      .catch(function (error) {
        var message = error.message || state.managementText.settingsSaveFailed;
        setSettingsStatus(message, "error");
        setManagementMessage(message, true);
        context.setStatus(message, true);
        settingsUpdatedInput.disabled = false;
        if (settingsSaveButton) settingsSaveButton.disabled = false;
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleSettingsSubmit(event) {
    if (event) event.preventDefault();
    handleSettingsSave();
  }

  function handleArchiveDoc() {
    var doc = currentSelectedDoc();
    if (!doc) return;
    if (!window.confirm("Archive " + doc.title + "?")) return;

    setManagementBusy(true);
    setManagementMessage("Archiving " + doc.title + "...", false);
    context.setStatus("Archiving " + doc.title + "...", false);

    archiveManagedDoc(doc.doc_id, managementClientOptions())
      .then(function (payload) {
        setManagementMessage("", false);
        return reloadDocsIndex(payload.doc_id, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Archive failed.", true);
        context.setStatus(error.message || "Archive failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function buildDeleteConfirmation(preview) {
    var lines = ["Delete " + preview.title + "?"];
    if (Array.isArray(preview.warnings) && preview.warnings.length) {
      lines.push("");
      lines.push("Warnings:");
      preview.warnings.forEach(function (item) {
        lines.push("- " + item);
      });
    }
    if (Array.isArray(preview.inbound_refs) && preview.inbound_refs.length) {
      lines.push("");
      lines.push("Inbound refs:");
      preview.inbound_refs.slice(0, 6).forEach(function (item) {
        lines.push("- " + item.doc_id);
      });
      if (preview.inbound_refs.length > 6) {
        lines.push("- +" + (preview.inbound_refs.length - 6) + " more");
      }
    }
    return lines.join("\n");
  }

  function handleDeleteDoc() {
    var doc = currentSelectedDoc();
    if (!doc) return;

    setManagementBusy(true);
    setManagementMessage("Checking delete impact for " + doc.title + "...", false);
    context.setStatus("Checking delete impact for " + doc.title + "...", false);

    previewManagedDocDelete(doc.doc_id, managementClientOptions())
      .then(function (preview) {
        if (!preview.allowed) {
          var blockerText = (preview.blockers || []).join("; ") || "Delete is blocked.";
          setManagementMessage(blockerText, true);
          context.setStatus(blockerText, true);
          return null;
        }
        if (!window.confirm(buildDeleteConfirmation(preview))) {
          setManagementMessage("", false);
          context.setStatus("", false);
          return null;
        }
        setManagementMessage("Deleting " + doc.title + "...", false);
        context.setStatus("Deleting " + doc.title + "...", false);
        return applyManagedDocDelete(doc.doc_id, managementClientOptions());
      })
      .then(function (payload) {
        if (!payload) return;
        var fallbackDocId = doc.parent_id || context.defaultRouteDocId() || context.defaultDocId();
        setManagementMessage("", false);
        return reloadDocsIndex(fallbackDocId, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Delete failed.", true);
        context.setStatus(error.message || "Delete failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleMakeViewable() {
    var doc = currentSelectedDoc();
    if (!doc || isDocViewable(doc)) return;
    var targetDocIds = viewabilityTargetDocIds(doc);
    if (!targetDocIds) return;

    setManagementBusy(true);
    var countText = targetDocIds.length === 1 ? doc.title : targetDocIds.length + " docs";
    setManagementMessage("Showing " + countText + "...", false);
    context.setStatus("Showing " + countText + "...", false);

    updateManagedDocsViewability(targetDocIds, false, managementClientOptions())
      .then(function (payload) {
        setManagementMessage("", false);
        return reloadDocsIndex(doc.doc_id, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Viewability update failed.", true);
        context.setStatus(error.message || "Viewability update failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
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

  function handleMoveDoc(docId, targetDocId, position) {
    if (!docId || !targetDocId || !position) return;
    var movingDoc = state.docsById.get(docId);
    var targetDoc = state.docsById.get(targetDocId);
    if (!movingDoc || !targetDoc) return;

    setManagementBusy(true);
    clearDragState();
    setManagementMessage("Moving " + movingDoc.title + "...", false);
    context.setStatus("Moving " + movingDoc.title + "...", false);

    moveManagedDoc(movingDoc.doc_id, targetDoc.doc_id, position, managementClientOptions())
      .then(function (payload) {
        var undoRecords = normalizeMoveUndoRecords(payload.undo_records);
        if (undoRecords.length) {
          state.moveUndo = {
            doc_id: movingDoc.doc_id,
            title: movingDoc.title || movingDoc.doc_id,
            records: undoRecords
          };
        } else if (moveUndoRecordChanged({
          parent_id: movingDoc.parent_id || "",
          sort_order: normalizeSortOrderValue(movingDoc.sort_order)
        }, payload.record)) {
          state.moveUndo = {
            doc_id: movingDoc.doc_id,
            title: movingDoc.title || movingDoc.doc_id,
            records: [{
              doc_id: movingDoc.doc_id,
              title: movingDoc.title || movingDoc.doc_id,
              parent_id: movingDoc.parent_id || "",
              sort_order: normalizeSortOrderValue(movingDoc.sort_order)
            }]
          };
        }
        setManagementMessage("", false);
        return reloadDocsIndex(movingDoc.doc_id, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Move failed.", true);
        context.setStatus(error.message || "Move failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleUndoMove() {
    var undoRecord = state.moveUndo;
    if (!undoRecord || state.managementBusy) return;

    var undoRecords = normalizeMoveUndoRecords(undoRecord.records || [undoRecord]);
    var focusDocId = String(undoRecord.doc_id || (undoRecords[0] && undoRecords[0].doc_id) || "").trim();
    if (!focusDocId || !context.findAllDocById(focusDocId) || !undoRecords.length) {
      state.moveUndo = null;
      setManagementMessage("Undo unavailable: moved doc is no longer in the current index.", true);
      context.setStatus("Undo unavailable: moved doc is no longer in the current index.", true);
      renderManagementUi();
      return;
    }

    setManagementBusy(true);
    hideContextMenu();
    setManagementMessage(state.managementText.undoMoveStatus, false);
    context.setStatus(state.managementText.undoMoveStatus, false);

    restoreManagedDocMove(focusDocId, moveUndoPayloadRecords(undoRecords), managementClientOptions())
      .then(function (response) {
        state.moveUndo = null;
        setManagementMessage("", false);
        return reloadDocsIndex(response.doc_id || focusDocId, "");
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Undo failed.", true);
        context.setStatus(error.message || "Undo failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function handleOpenSource(editor) {
    var docId = state.contextMenuDocId;
    var doc = state.docsById.get(docId);
    if (!doc) return;

    setManagementBusy(true);
    hideContextMenu();
    setManagementMessage("Opening source for " + doc.title + "...", false);
    context.setStatus("Opening source for " + doc.title + "...", false);

    openManagedDocSource(doc.doc_id, editor, managementClientOptions())
      .then(function () {
        setManagementMessage("", false);
        context.setStatus("", false);
      })
      .catch(function (error) {
        setManagementMessage(error.message || "Open source failed.", true);
        context.setStatus(error.message || "Open source failed.", true);
      })
      .finally(function () {
        setManagementBusy(false);
        renderManagementUi();
      });
  }

  function writeClipboardText(text) {
    if (window.navigator && window.navigator.clipboard && window.isSecureContext) {
      return window.navigator.clipboard.writeText(text);
    }

    return new Promise(function (resolve, reject) {
      var textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.top = "-1000px";
      textarea.style.left = "-1000px";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      try {
        if (!document.execCommand("copy")) {
          throw new Error(state.managementText.copyLinkFailed);
        }
        resolve();
      } catch (error) {
        reject(error);
      } finally {
        document.body.removeChild(textarea);
      }
    });
  }

  function handleCopyLink() {
    var doc = currentContextMenuDoc();
    if (!doc || typeof context.markdownDocLink !== "function") return;
    var markdownLink = context.markdownDocLink(doc);
    if (!markdownLink) return;

    hideContextMenu();
    writeClipboardText(markdownLink)
      .then(function () {
        var message = context.formatText(state.managementText.copyLinkStatus, {
          title: doc.title || doc.doc_id
        });
        setManagementMessage(message, false);
        context.setStatus(message, false);
      })
      .catch(function (error) {
        var message = error && error.message ? error.message : state.managementText.copyLinkFailed;
        setManagementMessage(message, true);
        context.setStatus(message, true);
      });
  }

  function applyConfig(config) {
    if (draftLabel) {
      draftLabel.textContent = context.getConfigText(config, "docs_viewer.hidden_toggle_label", context.getConfigText(config, "docs_viewer.draft_toggle_label", "show hidden"));
    }
    if (draftToggle) {
      draftToggle.setAttribute("aria-label", context.getConfigText(config, "docs_viewer.hidden_toggle_aria_label", context.getConfigText(config, "docs_viewer.draft_toggle_aria_label", "Show hidden docs")));
    }
    if (manageViewableButton) {
      var makeViewableLabel = context.getConfigText(config, "docs_viewer.make_viewable_button", "Show");
      manageViewableButton.textContent = makeViewableLabel;
      manageViewableButton.setAttribute("aria-label", makeViewableLabel);
      manageViewableButton.title = makeViewableLabel;
    }
    if (manageSettingsButton) {
      manageSettingsButton.textContent = context.getConfigText(config, "docs_viewer.settings_button", "Settings");
    }
    if (contextCopyLinkButton) {
      state.managementText.copyLinkLabel = context.getConfigText(config, "docs_viewer.copy_link_label", state.managementText.copyLinkLabel);
      contextCopyLinkButton.textContent = state.managementText.copyLinkLabel;
      contextCopyLinkButton.setAttribute("aria-label", state.managementText.copyLinkLabel);
    }
    if (settingsHeading) {
      settingsHeading.textContent = context.getConfigText(config, "docs_viewer.settings_title", "Settings");
    }
    if (settingsUpdatedLabel) {
      settingsUpdatedLabel.textContent = context.getConfigText(config, "docs_viewer.settings_show_updated_date_label", "show updated dates");
    }
    state.managementText.archiveUnavailableNote = context.getConfigText(config, "docs_viewer.manage_archive_unavailable_note", state.managementText.archiveUnavailableNote);
    state.managementText.checkingNote = context.getConfigText(config, "docs_viewer.manage_checking_note", state.managementText.checkingNote);
    state.managementText.clearSearchNote = context.getConfigText(config, "docs_viewer.manage_clear_search_note", state.managementText.clearSearchNote);
    state.managementText.undoMoveLabel = context.getConfigText(config, "docs_viewer.undo_move_label", state.managementText.undoMoveLabel);
    state.managementText.undoMoveStatus = context.getConfigText(config, "docs_viewer.undo_move_status", state.managementText.undoMoveStatus);
    state.managementText.serverNotConfiguredError = context.getConfigText(config, "docs_viewer.manage_server_not_configured_error", state.managementText.serverNotConfiguredError);
    state.managementText.unavailableNote = context.getConfigText(config, "docs_viewer.manage_unavailable_note", state.managementText.unavailableNote);
    state.managementText.viewableAncestorPrompt = context.getConfigText(config, "docs_viewer.viewable_ancestor_prompt", state.managementText.viewableAncestorPrompt);
    state.managementText.viewableDescendantPrompt = context.getConfigText(config, "docs_viewer.viewable_descendant_prompt", state.managementText.viewableDescendantPrompt);
    state.managementText.viewableInvalidChoice = context.getConfigText(config, "docs_viewer.viewable_invalid_choice", state.managementText.viewableInvalidChoice);
    state.managementText.metadataStatusLabel = context.getConfigText(config, "docs_viewer.metadata_status_label", state.managementText.metadataStatusLabel);
    state.managementText.metadataStatusNoneOption = context.getConfigText(config, "docs_viewer.metadata_status_none_option", state.managementText.metadataStatusNoneOption);
    state.managementText.metadataStatusSelectedSuffix = context.getConfigText(config, "docs_viewer.metadata_status_selected_suffix", state.managementText.metadataStatusSelectedSuffix);
    state.managementText.metadataHiddenLabel = context.getConfigText(config, "docs_viewer.metadata_hidden_label", context.getConfigText(config, "docs_viewer.metadata_viewable_label", state.managementText.metadataHiddenLabel));
    state.managementText.metadataParentRootOption = context.getConfigText(config, "docs_viewer.metadata_parent_root_option", state.managementText.metadataParentRootOption);
    state.managementText.metadataParentInvalid = context.getConfigText(config, "docs_viewer.metadata_parent_invalid", state.managementText.metadataParentInvalid);
    state.managementText.docHiddenEmoji = String(context.getConfigValue(config, "docs_viewer.doc_hidden_emoji") || state.managementText.docHiddenEmoji);
    state.managementText.statusMenuLabel = context.getConfigText(config, "docs_viewer.status_menu_label", state.managementText.statusMenuLabel);
    state.managementText.statusPillSetLabel = context.getConfigText(config, "docs_viewer.status_pill_set_label", state.managementText.statusPillSetLabel);
    state.managementText.statusPillClearLabel = context.getConfigText(config, "docs_viewer.status_pill_clear_label", state.managementText.statusPillClearLabel);
    state.managementText.statusPillReadonlyLabel = context.getConfigText(config, "docs_viewer.status_pill_readonly_label", state.managementText.statusPillReadonlyLabel);
    state.managementText.statusPillSaving = context.getConfigText(config, "docs_viewer.status_pill_saving", state.managementText.statusPillSaving);
    state.managementText.statusPillSaved = context.getConfigText(config, "docs_viewer.status_pill_saved", state.managementText.statusPillSaved);
    state.managementText.statusPillFailed = context.getConfigText(config, "docs_viewer.status_pill_failed", state.managementText.statusPillFailed);
    state.managementText.settingsLoading = context.getConfigText(config, "docs_viewer.settings_loading", state.managementText.settingsLoading);
    state.managementText.settingsEmpty = context.getConfigText(config, "docs_viewer.settings_empty", state.managementText.settingsEmpty);
    state.managementText.settingsSaving = context.getConfigText(config, "docs_viewer.settings_saving", state.managementText.settingsSaving);
    state.managementText.settingsSaved = context.getConfigText(config, "docs_viewer.settings_saved", state.managementText.settingsSaved);
    state.managementText.settingsLoadFailed = context.getConfigText(config, "docs_viewer.settings_load_failed", state.managementText.settingsLoadFailed);
    state.managementText.settingsSaveFailed = context.getConfigText(config, "docs_viewer.settings_save_failed", state.managementText.settingsSaveFailed);
    state.managementText.copyLinkStatus = context.getConfigText(config, "docs_viewer.copy_link_status", state.managementText.copyLinkStatus);
    state.managementText.copyLinkFailed = context.getConfigText(config, "docs_viewer.copy_link_failed", state.managementText.copyLinkFailed);
    if (metadataStatusLabel) {
      metadataStatusLabel.textContent = state.managementText.metadataStatusLabel;
    }
    if (metadataHiddenLabel) {
      metadataHiddenLabel.textContent = state.managementText.metadataHiddenLabel;
    }
    if (state.metadataEditingDocId && metadataStatusInput) {
      var metadataDoc = state.docsById.get(state.metadataEditingDocId);
      renderMetadataStatusOptions(metadataDoc);
      renderMetadataParentOptions(metadataDoc);
    }
  }

  function handleRootClick(event) {
    if (contextMenu && !event.target.closest("#docsViewerContextMenu")) {
      hideContextMenu();
    }
    if (manageActionsMenu && !event.target.closest(".docsViewer__manageActions")) {
      hideManageActionsMenu();
    }
    if (metadataModalOpen()) {
      var closeTrigger = event.target.closest("[data-metadata-close]");
      if (closeTrigger) {
        event.preventDefault();
        closeMetadataModal();
        return true;
      }
    }
    if (importModalOpen()) {
      var importCloseTrigger = event.target.closest("[data-import-close]");
      if (importCloseTrigger) {
        event.preventDefault();
        closeImportModal();
        return true;
      }
    }
    if (settingsModalOpen()) {
      var settingsCloseTrigger = event.target.closest("[data-settings-close]");
      if (settingsCloseTrigger) {
        event.preventDefault();
        closeSettingsModal();
        return true;
      }
    }
    return false;
  }

  function handleDocumentKeydown(event) {
    if (event.key === "Escape" && manageActionsMenu && !manageActionsMenu.hidden) {
      event.preventDefault();
      hideManageActionsMenu();
      return true;
    }
    if (event.key === "Escape" && metadataModalOpen()) {
      event.preventDefault();
      closeMetadataModal();
      return true;
    }
    if (event.key === "Escape" && importModalOpen()) {
      event.preventDefault();
      closeImportModal();
      return true;
    }
    if (event.key === "Escape" && settingsModalOpen()) {
      event.preventDefault();
      closeSettingsModal();
      return true;
    }
    return false;
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
        handleMoveDoc(movingDocId, targetDocId, position);
      });

      nav.addEventListener("dragend", function () {
        clearDragState();
      });
    }

    if (manageRebuildButton) {
      manageRebuildButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        handleRebuildDocs();
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
    if (manageActionsButton) {
      manageActionsButton.addEventListener("click", function () {
        toggleManageActionsMenu();
      });
    }
    if (indexUndoButton) {
      indexUndoButton.addEventListener("click", handleUndoMove);
    }
    if (manageNewButton) {
      manageNewButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        handleCreateDoc();
      });
    }
    if (manageEditButton) {
      manageEditButton.addEventListener("click", function () {
        hideManageActionsMenu();
        openMetadataModal().then(handleEditMetadataSave);
      });
    }
    if (manageArchiveButton) {
      manageArchiveButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        handleArchiveDoc();
      });
    }
    if (manageDeleteButton) {
      manageDeleteButton.addEventListener("click", function () {
        hideContextMenu();
        hideManageActionsMenu();
        handleDeleteDoc();
      });
    }
    if (manageViewableButton) {
      manageViewableButton.addEventListener("click", function () {
        hideContextMenu();
        handleMakeViewable();
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
          handleCreateRelatedDoc("sibling");
          return;
        }
        if (action.dataset.contextAction === "new-child") {
          handleCreateRelatedDoc("child");
          return;
        }
        if (action.dataset.contextAction === "copy-link") {
          handleCopyLink();
          return;
        }
        if (action.dataset.contextAction === "open-vscode") {
          handleOpenSource("vscode");
          return;
        }
        if (action.dataset.contextAction === "open") {
          handleOpenSource("default");
        }
      });
    }
    if (metadataCloseButton) {
      metadataCloseButton.addEventListener("click", closeMetadataModal);
    }
    if (metadataCancelButton) {
      metadataCancelButton.addEventListener("click", closeMetadataModal);
    }
    if (importCloseButton) {
      importCloseButton.addEventListener("click", closeImportModal);
    }
    if (settingsCloseButton) {
      settingsCloseButton.addEventListener("click", closeSettingsModal);
    }
    if (settingsCancelButton) {
      settingsCancelButton.addEventListener("click", closeSettingsModal);
    }
    if (metadataForm) {
      metadataForm.addEventListener("submit", function (event) {
        event.preventDefault();
        confirmMetadataModal();
      });
    }
    if (settingsForm) {
      settingsForm.addEventListener("submit", handleSettingsSubmit);
    }
    if (metadataStatusInput) {
      metadataStatusInput.addEventListener("change", function () {
        renderMetadataStatusSelection(String(metadataStatusInput.value || "").trim());
      });
    }
  }

  bind();
  applyConfig(context.currentViewerConfig());

  return {
    applyConfig: applyConfig,
    canDragCurrentDoc: canDragCurrentDoc,
    handleDocumentKeydown: handleDocumentKeydown,
    handleRootClick: handleRootClick,
    handleStatusPillClick: handleStatusPillClick,
    hideContextMenu: hideContextMenu,
    initialize: initializeManagement,
    openImportModal: openImportModal,
    render: renderManagementUi,
    updateNavDragState: updateNavDragState
  };
}
