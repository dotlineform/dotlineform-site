import {
  renderMetadataParentPopupMarkup,
  renderMetadataStatusOptionsMarkup,
  renderSettingsWarningsMarkup
} from "./docs-viewer-management-render.js";
import {
  normalizeText,
  trapDocsViewerModalFocus
} from "./docs-viewer-management-modal-shell.js";

export {
  openDocsViewerChoiceModal,
  openDocsViewerConfirmModal,
  openDocsViewerManagementModal,
  openDocsViewerTextInputModal
} from "./docs-viewer-management-modal-shell.js";

export function buildDocsViewerDeletePreviewBody(preview) {
  var lines = ["Delete " + normalizeText(preview && preview.title) + "?"];
  if (Array.isArray(preview && preview.warnings) && preview.warnings.length) {
    lines.push("Warnings:");
    preview.warnings.forEach(function (item) {
      lines.push("- " + item);
    });
  }
  if (Array.isArray(preview && preview.inbound_refs) && preview.inbound_refs.length) {
    lines.push("Inbound refs:");
    preview.inbound_refs.slice(0, 6).forEach(function (item) {
      lines.push("- " + item.doc_id);
    });
    if (preview.inbound_refs.length > 6) {
      lines.push("- +" + (preview.inbound_refs.length - 6) + " more");
    }
  }
  return lines;
}

export function createDocsViewerManagementModalController(options = {}) {
  var refs = options.refs || {};
  var state = options.state || {};
  var context = options.context || {};
  var nav = options.nav || null;
  var callbacks = options.callbacks || {};
  var metadataModalResolve = null;
  var metadataParentOptionRecords = [];
  var metadataParentActiveIndex = -1;
  var settingsFieldState = null;
  var importModalCancelButton = null;

  function viewerScope() {
    return typeof callbacks.viewerScope === "function" ? callbacks.viewerScope() : "";
  }

  function currentSelectedDoc() {
    return typeof callbacks.currentSelectedDoc === "function" ? callbacks.currentSelectedDoc() : null;
  }

  function metadataModalOpen() {
    return Boolean(refs.metadataModal && !refs.metadataModal.hidden);
  }

  function importModalOpen() {
    return Boolean(refs.importModal && !refs.importModal.hidden);
  }

  function settingsModalOpen() {
    return Boolean(refs.settingsModal && !refs.settingsModal.hidden);
  }

  function metadataParentOptions(doc) {
    return typeof callbacks.metadataParentOptions === "function" ? callbacks.metadataParentOptions(doc) : [];
  }

  function metadataParentOptionTitle(option) {
    if (!option || !option.value) return state.managementText.metadataParentRootOption;
    return String(option.label || "").replace(/^(-\s*)+/, "");
  }

  function metadataParentOptionDisplay(option) {
    return metadataParentOptionTitle(option);
  }

  function metadataParentMatchRank(option, query) {
    var display = metadataParentOptionDisplay(option).toLowerCase();
    var title = metadataParentOptionTitle(option).toLowerCase();
    var value = String(option && option.value || "").toLowerCase();
    if (value === query) return 0;
    if (title === query || display === query) return 1;
    if (value.startsWith(query)) return 2;
    if (title.startsWith(query) || display.startsWith(query)) return 3;
    if (value.includes(query)) return 4;
    if (title.includes(query) || display.includes(query)) return 5;
    return null;
  }

  function hideMetadataParentPopup() {
    metadataParentOptionRecords = [];
    metadataParentActiveIndex = -1;
    if (refs.metadataParentPopup) {
      refs.metadataParentPopup.hidden = true;
      refs.metadataParentPopup.innerHTML = "";
    }
    if (refs.metadataParentInput) {
      refs.metadataParentInput.setAttribute("aria-expanded", "false");
      refs.metadataParentInput.removeAttribute("aria-activedescendant");
    }
  }

  function setMetadataParentActiveIndex(index) {
    if (!refs.metadataParentPopup || !refs.metadataParentInput) return;
    metadataParentActiveIndex = index;
    refs.metadataParentPopup.querySelectorAll("[data-parent-index]").forEach(function (button) {
      var active = Number(button.getAttribute("data-parent-index")) === metadataParentActiveIndex;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", active ? "true" : "false");
      if (active) {
        refs.metadataParentInput.setAttribute("aria-activedescendant", button.id);
      }
    });
    if (metadataParentActiveIndex < 0) {
      refs.metadataParentInput.removeAttribute("aria-activedescendant");
    }
  }

  function metadataParentMatches(doc, query) {
    var normalizedQuery = String(query || "").trim().toLowerCase();
    if (!normalizedQuery) return [];
    return metadataParentOptions(doc).map(function (option, index) {
      return {
        index: index,
        option: option,
        rank: metadataParentMatchRank(option, normalizedQuery)
      };
    }).filter(function (match) {
      return match.rank !== null;
    }).sort(function (left, right) {
      if (left.rank !== right.rank) return left.rank - right.rank;
      return left.index - right.index;
    }).slice(0, 14).map(function (match) {
      return match.option;
    });
  }

  function renderMetadataParentPopup(doc) {
    if (!refs.metadataParentInput || !refs.metadataParentPopup) return;
    var matches = metadataParentMatches(doc, refs.metadataParentInput.value);
    metadataParentOptionRecords = matches;
    if (!String(refs.metadataParentInput.value || "").trim()) {
      hideMetadataParentPopup();
      return;
    }
    if (!matches.length) {
      refs.metadataParentPopup.innerHTML = renderMetadataParentPopupMarkup(matches, {
        emptyText: state.managementText.metadataParentNoMatches
      });
      refs.metadataParentPopup.hidden = false;
      refs.metadataParentInput.setAttribute("aria-expanded", "true");
      metadataParentActiveIndex = -1;
      refs.metadataParentInput.removeAttribute("aria-activedescendant");
      return;
    }
    refs.metadataParentPopup.innerHTML = renderMetadataParentPopupMarkup(matches, {
      optionTitle: metadataParentOptionTitle
    });
    refs.metadataParentPopup.hidden = false;
    refs.metadataParentInput.setAttribute("aria-expanded", "true");
    setMetadataParentActiveIndex(0);
  }

  function selectMetadataParentOption(index) {
    var option = metadataParentOptionRecords[index];
    if (!option || !refs.metadataParentInput) return;
    refs.metadataParentInput.value = metadataParentOptionDisplay(option);
    hideMetadataParentPopup();
    refs.metadataParentInput.focus();
  }

  function renderMetadataParentOptions(doc) {
    if (!refs.metadataParentInput) return;
    var currentParentId = String(doc && doc.parent_id || "").trim();
    var options = metadataParentOptions(doc);
    var currentOption = options.find(function (option) {
      return option.value === currentParentId;
    }) || options[0];
    refs.metadataParentInput.value = metadataParentOptionDisplay(currentOption);
    hideMetadataParentPopup();
  }

  function resolveMetadataParentId(doc) {
    if (!refs.metadataParentInput) return "";
    var inputValue = String(refs.metadataParentInput.value || "").trim();
    var rootLabel = state.managementText.metadataParentRootOption;
    if (!inputValue || inputValue.toLowerCase() === rootLabel.toLowerCase()) return "";
    var options = metadataParentOptions(doc);
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
    var optionRecords = [{
      value: "",
      label: state.managementText.metadataStatusNoneOption
    }];
    (state.uiStatuses || []).forEach(function (status) {
      optionRecords.push({
        value: status.ui_status,
        label: status.emoji + " " + status.label
      });
    });
    return optionRecords;
  }

  function renderMetadataStatusOptions(doc) {
    if (!refs.metadataStatusInput) return;
    var selectedValue = String(doc && doc.ui_status || "").trim();
    renderMetadataStatusSelection(selectedValue);
  }

  function renderMetadataStatusSelection(selectedValue) {
    if (!refs.metadataStatusInput) return;
    refs.metadataStatusInput.innerHTML = renderMetadataStatusOptionsMarkup(
      metadataStatusOptions(),
      selectedValue,
      state.managementText.metadataStatusSelectedSuffix
    );
    refs.metadataStatusInput.size = Math.max(1, refs.metadataStatusInput.options.length);
  }

  function dismissMetadataParentSuggestions() {
    if (!refs.metadataParentInput) return;
    refs.metadataParentInput.blur();
    refs.metadataParentInput.value = "";
    hideMetadataParentPopup();
  }

  function focusWithoutScroll(target) {
    if (!target || typeof target.focus !== "function") return;
    try {
      target.focus({ preventScroll: true });
    } catch (error) {
      var scrollX = window.scrollX;
      var scrollY = window.scrollY;
      target.focus();
      window.scrollTo(scrollX, scrollY);
    }
  }

  function isFocusableNow(target) {
    return Boolean(
      target
      && typeof target.focus === "function"
      && !target.disabled
      && target.getClientRects
      && target.getClientRects().length
    );
  }

  function focusModalReturnTarget(preferredTarget) {
    var target = isFocusableNow(preferredTarget) ? preferredTarget : refs.manageActionsButton;
    window.setTimeout(function () {
      focusWithoutScroll(target);
    }, 0);
  }

  function closeMetadataModal(result) {
    if (!refs.metadataModal) return;
    if (document.activeElement && refs.metadataModal.contains(document.activeElement)) {
      document.activeElement.blur();
    }
    dismissMetadataParentSuggestions();
    refs.metadataModal.hidden = true;
    state.metadataEditingDocId = "";
    var restoreDocId = state.metadataRestoreFocusId;
    state.metadataRestoreFocusId = "";
    if (metadataModalResolve) {
      var resolve = metadataModalResolve;
      metadataModalResolve = null;
      resolve(result || null);
    }
    if (!restoreDocId || !nav) return;
    var escapeCss = typeof context.cssEscape === "function" ? context.cssEscape : function (value) { return String(value || ""); };
    var target = nav.querySelector('[data-doc-row-id="' + escapeCss(restoreDocId) + '"] .docsViewer__navLink');
    focusWithoutScroll(target);
  }

  function openMetadataModal(doc) {
    if (!doc || !refs.metadataModal || !refs.metadataForm || !refs.metadataTitleInput || !refs.metadataSummaryInput || !refs.metadataStatusInput || !refs.metadataHiddenInput || !refs.metadataParentInput || !refs.metadataSortOrderInput) {
      return Promise.resolve(null);
    }
    if (typeof callbacks.hideContextMenu === "function") callbacks.hideContextMenu();
    state.metadataEditingDocId = doc.doc_id;
    state.metadataRestoreFocusId = doc.doc_id;
    if (refs.metadataDocId) {
      refs.metadataDocId.textContent = doc.doc_id;
    }

    refs.metadataTitleInput.value = doc.title || "";
    refs.metadataSummaryInput.value = doc.summary || "";
    renderMetadataStatusOptions(doc);
    refs.metadataHiddenInput.checked = typeof callbacks.isDocHidden === "function" ? callbacks.isDocHidden(doc) : Boolean(doc.hidden);
    refs.metadataSortOrderInput.value = doc.sort_order == null ? "" : String(doc.sort_order);
    refs.metadataSortOrderInput.min = "0";
    renderMetadataParentOptions(doc);

    refs.metadataModal.hidden = false;
    window.requestAnimationFrame(function () {
      refs.metadataTitleInput.focus();
      refs.metadataTitleInput.select();
    });
    return new Promise(function (resolve) {
      metadataModalResolve = resolve;
    });
  }

  function ensureImportModalCancelButton() {
    if (importModalCancelButton) return importModalCancelButton;
    if (!refs.importRoot) return null;
    var actions = refs.importRoot.querySelector(".docsViewerImport__actions");
    var runButton = document.getElementById("docsHtmlImportRun");
    if (!actions || !runButton) return null;
    importModalCancelButton = document.createElement("button");
    importModalCancelButton.type = "button";
    importModalCancelButton.className = "docsViewerImport__button docsViewerImport__button--defaultWidth docsViewerImport__modalCancel";
    importModalCancelButton.id = "docsViewerImportCancelButton";
    importModalCancelButton.textContent = state.managementText.importCancelButton;
    importModalCancelButton.addEventListener("click", closeImportModal);
    actions.insertBefore(importModalCancelButton, runButton);
    return importModalCancelButton;
  }

  function updateImportCancelLabel() {
    if (importModalCancelButton) importModalCancelButton.textContent = state.managementText.importCancelButton;
  }

  function focusImportModalEntry() {
    var cancelButton = ensureImportModalCancelButton();
    if (cancelButton) {
      focusWithoutScroll(cancelButton);
      return;
    }
    if (refs.importRoot) {
      focusWithoutScroll(refs.importRoot);
    }
  }

  function openImportModal() {
    if (!refs.importModal || !refs.importRoot) return;
    var scope = viewerScope();
    refs.importModal.hidden = false;
    var initResult = typeof callbacks.onImportOpen === "function" ? callbacks.onImportOpen(scope) : null;
    if (initResult && typeof initResult.then === "function") {
      initResult.then(focusImportModalEntry).catch(focusImportModalEntry);
    } else {
      focusImportModalEntry();
    }
  }

  function closeImportModal() {
    if (!refs.importModal) return;
    if (document.activeElement && refs.importModal.contains(document.activeElement)) {
      document.activeElement.blur();
    }
    refs.importModal.hidden = true;
    focusModalReturnTarget(refs.manageImportButton);
  }

  function setSettingsStatus(message, stateName) {
    if (!refs.settingsStatus) return;
    refs.settingsStatus.textContent = String(message || "");
    refs.settingsStatus.dataset.state = stateName || "";
    refs.settingsStatus.hidden = !message;
  }

  function renderSettingsWarnings(warnings) {
    if (!refs.settingsWarnings) return;
    var items = Array.isArray(warnings) ? warnings.filter(Boolean) : [];
    refs.settingsWarnings.hidden = items.length === 0;
    refs.settingsWarnings.innerHTML = renderSettingsWarningsMarkup(items);
  }

  function openSettingsModalShell() {
    if (!refs.settingsModal || !refs.settingsForm || !refs.settingsUpdatedInput) return false;
    if (typeof callbacks.hideContextMenu === "function") callbacks.hideContextMenu();
    if (typeof callbacks.hideManageActionsMenu === "function") callbacks.hideManageActionsMenu();
    settingsFieldState = null;
    refs.settingsUpdatedInput.disabled = true;
    if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = true;
    if (refs.settingsScope) refs.settingsScope.textContent = "scope: " + viewerScope();
    setSettingsStatus(state.managementText.settingsLoading, "");
    renderSettingsWarnings([]);
    refs.settingsModal.hidden = false;
    return true;
  }

  function setSettingsField(field) {
    settingsFieldState = field || null;
    if (!refs.settingsUpdatedInput || !settingsFieldState) return;
    refs.settingsUpdatedInput.checked = settingsFieldState.current_value !== false;
    refs.settingsUpdatedInput.disabled = false;
    if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = state.managementBusy;
    renderSettingsWarnings(settingsFieldState.warnings || []);
    setSettingsStatus("", "");
    window.requestAnimationFrame(function () {
      refs.settingsUpdatedInput.focus();
    });
  }

  function setSettingsLoadError(message) {
    if (refs.settingsUpdatedInput) refs.settingsUpdatedInput.disabled = true;
    if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = true;
    renderSettingsWarnings([]);
    setSettingsStatus(message || state.managementText.settingsLoadFailed, "error");
  }

  function setSettingsSaving() {
    setSettingsStatus(state.managementText.settingsSaving, "");
    if (refs.settingsUpdatedInput) refs.settingsUpdatedInput.disabled = true;
    if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = true;
  }

  function setSettingsSaveError(message) {
    setSettingsStatus(message || state.managementText.settingsSaveFailed, "error");
    if (refs.settingsUpdatedInput) refs.settingsUpdatedInput.disabled = false;
    if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = false;
  }

  function closeSettingsModal() {
    if (!refs.settingsModal) return;
    if (document.activeElement && refs.settingsModal.contains(document.activeElement)) {
      document.activeElement.blur();
    }
    refs.settingsModal.hidden = true;
    settingsFieldState = null;
    focusModalReturnTarget(refs.manageSettingsButton);
  }

  function handleRootClick(event) {
    if (metadataModalOpen()) {
      if (refs.metadataParentPopup && !refs.metadataParentPopup.hidden && !event.target.closest(".docsViewer__parentPicker")) {
        hideMetadataParentPopup();
      }
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
    if (event.key === "Tab" && metadataModalOpen()) {
      return trapDocsViewerModalFocus(event, refs.metadataModal);
    }
    if (event.key === "Tab" && importModalOpen()) {
      return trapDocsViewerModalFocus(event, refs.importModal);
    }
    if (event.key === "Tab" && settingsModalOpen()) {
      return trapDocsViewerModalFocus(event, refs.settingsModal);
    }
    if (event.key === "Escape" && refs.metadataParentPopup && !refs.metadataParentPopup.hidden) {
      event.preventDefault();
      hideMetadataParentPopup();
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

  function wireEvents() {
    if (refs.metadataCancelButton) {
      refs.metadataCancelButton.addEventListener("click", function () {
        closeMetadataModal();
      });
    }
    if (refs.settingsCancelButton) {
      refs.settingsCancelButton.addEventListener("click", closeSettingsModal);
    }
    if (refs.metadataForm) {
      refs.metadataForm.addEventListener("submit", function (event) {
        event.preventDefault();
        if (typeof callbacks.onMetadataSubmit === "function") callbacks.onMetadataSubmit();
      });
    }
    if (refs.settingsForm) {
      refs.settingsForm.addEventListener("submit", function (event) {
        if (typeof callbacks.onSettingsSubmit === "function") callbacks.onSettingsSubmit(event);
      });
    }
    if (refs.metadataStatusInput) {
      refs.metadataStatusInput.addEventListener("change", function () {
        renderMetadataStatusSelection(String(refs.metadataStatusInput.value || "").trim());
      });
    }
    if (refs.metadataParentInput) {
      refs.metadataParentInput.addEventListener("input", function () {
        var doc = state.metadataEditingDocId ? state.docsById.get(state.metadataEditingDocId) : currentSelectedDoc();
        if (doc) renderMetadataParentPopup(doc);
      });
      refs.metadataParentInput.addEventListener("focus", function () {
        var doc = state.metadataEditingDocId ? state.docsById.get(state.metadataEditingDocId) : currentSelectedDoc();
        if (doc) renderMetadataParentPopup(doc);
      });
      refs.metadataParentInput.addEventListener("keydown", function (event) {
        if (!refs.metadataParentPopup || refs.metadataParentPopup.hidden) {
          if (event.key === "ArrowDown") {
            var doc = state.metadataEditingDocId ? state.docsById.get(state.metadataEditingDocId) : currentSelectedDoc();
            if (doc) renderMetadataParentPopup(doc);
          }
          return;
        }
        if (event.key === "ArrowDown") {
          event.preventDefault();
          if (metadataParentOptionRecords.length) {
            setMetadataParentActiveIndex(Math.min(metadataParentActiveIndex + 1, metadataParentOptionRecords.length - 1));
          }
          return;
        }
        if (event.key === "ArrowUp") {
          event.preventDefault();
          if (metadataParentOptionRecords.length) {
            setMetadataParentActiveIndex(Math.max(metadataParentActiveIndex - 1, 0));
          }
          return;
        }
        if (event.key === "Enter" && metadataParentActiveIndex >= 0) {
          event.preventDefault();
          selectMetadataParentOption(metadataParentActiveIndex);
          return;
        }
        if (event.key === "Escape") {
          event.preventDefault();
          hideMetadataParentPopup();
        }
      });
    }
    if (refs.metadataParentPopup) {
      refs.metadataParentPopup.addEventListener("mousedown", function (event) {
        if (event.target.closest("[data-parent-index]")) {
          event.preventDefault();
        }
      });
      refs.metadataParentPopup.addEventListener("click", function (event) {
        var button = event.target.closest("[data-parent-index]");
        if (!button) return;
        selectMetadataParentOption(Number(button.getAttribute("data-parent-index")));
      });
    }
  }

  return {
    closeImportModal: closeImportModal,
    closeMetadataModal: closeMetadataModal,
    closeSettingsModal: closeSettingsModal,
    getSettingsFieldState: function () {
      return settingsFieldState;
    },
    handleDocumentKeydown: handleDocumentKeydown,
    handleRootClick: handleRootClick,
    metadataModalOpen: metadataModalOpen,
    openImportModal: openImportModal,
    openMetadataModal: openMetadataModal,
    openSettingsModalShell: openSettingsModalShell,
    renderMetadataParentOptions: renderMetadataParentOptions,
    renderMetadataStatusOptions: renderMetadataStatusOptions,
    renderSettingsWarnings: renderSettingsWarnings,
    resolveMetadataParentId: resolveMetadataParentId,
    setSettingsField: setSettingsField,
    setSettingsLoadError: setSettingsLoadError,
    setSettingsSaveError: setSettingsSaveError,
    setSettingsSaving: setSettingsSaving,
    setSettingsStatus: setSettingsStatus,
    settingsModalOpen: settingsModalOpen,
    updateImportCancelLabel: updateImportCancelLabel,
    wireEvents: wireEvents
  };
}
