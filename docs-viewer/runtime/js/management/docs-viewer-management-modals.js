import {
  renderMetadataStatusOptionsMarkup,
  renderSettingsWarningsMarkup
} from "./docs-viewer-management-render.js";
import {
  normalizeText,
  trapDocsViewerModalFocus
} from "./docs-viewer-management-modal-shell.js";
import {
  createDocsViewerMetadataParentPicker
} from "./docs-viewer-management-parent-picker.js";

export {
  openDocsViewerChoiceModal,
  openDocsViewerConfirmModal,
  openDocsViewerManagementModal,
  openDocsViewerNoticeModal,
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
  return lines;
}

export function createDocsViewerManagementModalController(options = {}) {
  var refs = options.refs || {};
  var state = options.state || {};
  var context = options.context || {};
  var nav = options.nav || null;
  var callbacks = options.callbacks || {};
  var metadataModalResolve = null;
  var settingsFieldState = null;
  var importModalCancelButton = null;
  var metadataParentPicker = createDocsViewerMetadataParentPicker({
    refs: refs,
    state: state,
    callbacks: callbacks
  });

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

  function renderMetadataParentOptions(doc) {
    metadataParentPicker.renderOptions(doc);
  }

  function resolveMetadataParentId(doc) {
    return metadataParentPicker.resolveParentId(doc);
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
    metadataParentPicker.dismissSuggestions();
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
    if (!doc || !refs.metadataModal || !refs.metadataForm || !refs.metadataTitleInput || !refs.metadataSummaryInput || !refs.metadataDateInput || !refs.metadataDateDisplayInput || !refs.metadataStatusInput || !refs.metadataNonViewableInput || !refs.metadataParentInput) {
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
    refs.metadataDateInput.value = doc.date || "";
    refs.metadataDateDisplayInput.value = doc.date_display || "";
    renderMetadataStatusOptions(doc);
    refs.metadataNonViewableInput.checked = typeof callbacks.isDocNonViewable === "function" ? callbacks.isDocNonViewable(doc) : doc.viewable === false;
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
    if (!refs.settingsModal || !refs.settingsForm) return false;
    if (typeof callbacks.hideContextMenu === "function") callbacks.hideContextMenu();
    if (typeof callbacks.hideManageActionsMenu === "function") callbacks.hideManageActionsMenu();
    settingsFieldState = null;
    if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = true;
    if (refs.settingsScope) refs.settingsScope.textContent = "scope: " + viewerScope();
    setSettingsStatus(state.managementText.settingsLoading, "");
    renderSettingsWarnings([]);
    refs.settingsModal.hidden = false;
    return true;
  }

  function setSettingsField(field) {
    settingsFieldState = field || null;
    if (!settingsFieldState) {
      if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = true;
      renderSettingsWarnings([]);
      setSettingsStatus(state.managementText.settingsEmpty, "");
      window.requestAnimationFrame(function () {
        focusWithoutScroll(refs.settingsCancelButton || refs.settingsModal);
      });
      return;
    }
    if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = state.managementBusy;
    renderSettingsWarnings(settingsFieldState.warnings || []);
    setSettingsStatus("", "");
  }

  function setSettingsLoadError(message) {
    if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = true;
    renderSettingsWarnings([]);
    setSettingsStatus(message || state.managementText.settingsLoadFailed, "error");
  }

  function setSettingsSaving() {
    setSettingsStatus(state.managementText.settingsSaving, "");
    if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = true;
  }

  function setSettingsSaveError(message) {
    setSettingsStatus(message || state.managementText.settingsSaveFailed, "error");
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
        metadataParentPicker.hidePopup();
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
      metadataParentPicker.hidePopup();
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
        if (doc) metadataParentPicker.renderPopup(doc);
      });
      refs.metadataParentInput.addEventListener("focus", function () {
        var doc = state.metadataEditingDocId ? state.docsById.get(state.metadataEditingDocId) : currentSelectedDoc();
        if (doc) metadataParentPicker.renderPopup(doc);
      });
      refs.metadataParentInput.addEventListener("keydown", function (event) {
        var doc = state.metadataEditingDocId ? state.docsById.get(state.metadataEditingDocId) : currentSelectedDoc();
        metadataParentPicker.handleInputKeydown(event, doc);
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
        metadataParentPicker.selectOption(Number(button.getAttribute("data-parent-index")));
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
