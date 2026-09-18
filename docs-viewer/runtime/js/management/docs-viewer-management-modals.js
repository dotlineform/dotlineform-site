import {
  renderSettingsWarningsMarkup
} from "./docs-viewer-management-render.js";
import {
  normalizeText,
  openDocsViewerNoticeModal
} from "./docs-viewer-management-modal-shell.js";
import {
  createDocsViewerModalLifecycle
} from "./docs-viewer-modal-lifecycle.js";

export {
  openDocsViewerChoiceModal,
  openDocsViewerConfirmModal,
  openDocsViewerManagementModal,
  openDocsViewerTextInputModal
} from "./docs-viewer-management-modal-shell.js";

export { openDocsViewerNoticeModal };

var MODAL_TEXT = {
  importCancelButton: "Cancel",
  importCloseButton: "Close",
  settingsLoading: "Loading settings...",
  settingsEmpty: "No editable settings are available for this scope.",
  settingsLoadFailed: "Settings unavailable."
};

function publicCleanupCounts(payload) {
  var cleanup = payload && payload.public_cleanup;
  if (!cleanup || cleanup.applicable !== true) {
    return { projected: 0, urls: 0 };
  }
  var projected = new Set(
    (Array.isArray(cleanup.projected_doc_ids) ? cleanup.projected_doc_ids : [])
      .map(normalizeText)
      .filter(Boolean)
  ).size;
  var urls = new Set(
    (Array.isArray(cleanup.removed_urls) ? cleanup.removed_urls : [])
      .map(normalizeText)
      .filter(Boolean)
  ).size;
  return { projected: projected, urls: urls };
}

export function docsViewerDeletePublicCleanupLines(payload) {
  var counts = publicCleanupCounts(payload);
  if (!counts.projected) return [];
  var lines = [
    "Current public projections to remove immediately: " + counts.projected
  ];
  if (counts.urls > counts.projected) {
    lines.push("Public document URLs to remove immediately: " + counts.urls);
  }
  return lines;
}

export function docsViewerDeleteCompletionMessage(payload) {
  var counts = publicCleanupCounts(payload);
  if (!counts.projected) return "";
  var message = normalizeText(payload && payload.summary_text) || "Delete complete.";
  message += " Removed " + counts.projected + " current public projection";
  message += counts.projected === 1 ? " immediately." : "s immediately.";
  if (counts.urls > counts.projected) {
    message += " Removed " + counts.urls + " public document URLs.";
  }
  return message;
}

export function buildDocsViewerDeletePreviewBody(preview) {
  var warnings = (Array.isArray(preview && preview.warnings) ? preview.warnings : [])
    .map(normalizeText)
    .filter(Boolean);
  return warnings.concat(docsViewerDeletePublicCleanupLines(preview));
}

export function createDocsViewerManagementModalController(options = {}) {
  var refs = options.refs || {};
  var management = options.management || {};
  var callbacks = options.callbacks || {};
  var settingsFieldState = null;
  var importModalCancelButton = null;
  var importLifecycle = null;
  var importRestoreFocusTarget = null;
  var importEntryFocusTarget = null;
  var importFolderLifecycle = null;
  var importFolderPicker = null;
  var importFolderRestoreFocusTarget = null;
  var importCollectionLifecycle = null;
  var importCollectionCommand = null;
  var importCollectionPhase = "idle";
  var settingsLifecycle = refs.settingsModal ? createDocsViewerModalLifecycle({
    cancelElements: Array.from(refs.settingsModal.querySelectorAll("[data-settings-close]"))
      .concat(refs.settingsCancelButton || [])
      .filter(Boolean),
    document: document,
    initialFocus: function () { return refs.settingsCancelButton || refs.settingsModal; },
    modal: refs.settingsModal,
    onRequestClose: function () { closeSettingsModal(); }
  }) : null;

  function viewerStage() {
    return typeof callbacks.viewerStage === "function" ? callbacks.viewerStage() : "";
  }

  function settingsModalOpen() {
    return Boolean(refs.settingsModal && !refs.settingsModal.hidden);
  }

  function setModalStatus(node, message, stateName) {
    if (!node) return;
    node.textContent = String(message || "");
    node.hidden = !message;
    if (stateName) {
      node.dataset.state = stateName;
    } else {
      delete node.dataset.state;
    }
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
    importModalCancelButton.textContent = MODAL_TEXT.importCancelButton;
    actions.insertBefore(importModalCancelButton, runButton);
    return importModalCancelButton;
  }

  function importModalBusy() {
    var cancelButton = ensureImportModalCancelButton();
    return Boolean(
      refs.importRoot
      && refs.importRoot.dataset.studioBusy === "true"
    ) || Boolean(cancelButton && cancelButton.disabled);
  }

  function importNestedCancelControl() {
    if (!refs.importModal) return null;
    return Array.from(refs.importModal.querySelectorAll([
      "#docsHtmlImportCancel",
      '[data-collection-command="cancel"]'
    ].join(","))).find(isFocusableNow) || null;
  }

  function consumeImportEscape(event) {
    var nestedCancel = importNestedCancelControl();
    if (nestedCancel) {
      event.preventDefault();
      nestedCancel.click();
      return true;
    }
    if (!importModalBusy()) return false;
    event.preventDefault();
    return true;
  }

  function ensureImportModalLifecycle() {
    if (importLifecycle || !refs.importModal) return importLifecycle;
    var cancelButton = ensureImportModalCancelButton();
    importLifecycle = createDocsViewerModalLifecycle({
      cancelElements: Array.from(refs.importModal.querySelectorAll("[data-import-close]"))
        .concat(cancelButton || [])
        .filter(Boolean),
      consumeEscape: consumeImportEscape,
      document: document,
      initialFocus: function () {
        return isFocusableNow(importEntryFocusTarget)
          ? importEntryFocusTarget
          : cancelButton || refs.importRoot;
      },
      modal: refs.importModal,
      onRequestClose: function () { return closeImportModal(); }
    });
    return importLifecycle;
  }

  function focusImportModalEntry() {
    if (importLifecycle) importLifecycle.focusInitial();
  }

  function ensureImportFolderLifecycle() {
    if (importFolderLifecycle || !refs.importFolderModal) return importFolderLifecycle;
    importFolderLifecycle = createDocsViewerModalLifecycle({
      cancelElements: Array.from(
        refs.importFolderModal.querySelectorAll("[data-import-folder-close]")
      ).concat(refs.importFolderCancelButton || []).filter(Boolean),
      document: document,
      initialFocus: function () { return refs.importFolderModal; },
      modal: refs.importFolderModal,
      onRequestClose: function () {
        if (refs.importFolderConfirmButton && refs.importFolderConfirmButton.disabled) {
          return false;
        }
        return closeImportFolderModal();
      }
    });
    return importFolderLifecycle;
  }

  function restoreImportFromFolder() {
    if (refs.importModal) refs.importModal.hidden = false;
    importEntryFocusTarget = importFolderRestoreFocusTarget;
    var lifecycle = ensureImportModalLifecycle();
    if (lifecycle && !lifecycle.isActive()) {
      lifecycle.open({ restoreFocus: importRestoreFocusTarget });
    } else {
      if (isFocusableNow(importFolderRestoreFocusTarget)) {
        focusWithoutScroll(importFolderRestoreFocusTarget);
      } else {
        focusImportModalEntry();
      }
    }
    window.setTimeout(function () {
      importEntryFocusTarget = null;
    }, 0);
  }

  function closeImportFolderModal() {
    if (!refs.importFolderModal || refs.importFolderModal.hidden) return false;
    if (importFolderLifecycle) {
      importFolderLifecycle.close({ restoreFocus: false });
    }
    refs.importFolderModal.hidden = true;
    if (importFolderPicker && typeof importFolderPicker.destroy === "function") {
      importFolderPicker.destroy();
    }
    importFolderPicker = null;
    if (refs.importFolderConfirmButton) refs.importFolderConfirmButton.disabled = false;
    restoreImportFromFolder();
    return true;
  }

  function showImportFolderError(error) {
    var message = normalizeText(error && error.message) || "Folder could not be loaded.";
    var restoreFocus = importFolderRestoreFocusTarget;
    closeImportFolderModal();
    return openDocsViewerNoticeModal({
      root: refs.importFolderModal && refs.importFolderModal.parentElement,
      title: "Folder unavailable",
      body: message
    }).then(function () {
      if (isFocusableNow(restoreFocus)) focusWithoutScroll(restoreFocus);
      return false;
    });
  }

  function openImportFolderModal(options) {
    var settings = options || {};
    if (
      !refs.importModal
      || !refs.importFolderModal
      || !refs.importFolderPicker
      || typeof settings.createFolderPicker !== "function"
      || typeof settings.loadDirectory !== "function"
      || typeof settings.onSubmit !== "function"
    ) {
      return Promise.reject(new Error("Docs Import folder modal is unavailable."));
    }
    if (importLifecycle && importLifecycle.isActive()) {
      importLifecycle.close({ restoreFocus: false });
    }
    refs.importModal.hidden = true;
    importFolderRestoreFocusTarget = settings.restoreFocus || null;
    refs.importFolderModal.hidden = false;
    if (refs.importFolderConfirmButton) refs.importFolderConfirmButton.disabled = false;
    var lifecycle = ensureImportFolderLifecycle();
    if (lifecycle && !lifecycle.isActive()) {
      lifecycle.open({ restoreFocus: importFolderRestoreFocusTarget });
    }
    try {
      importFolderPicker = settings.createFolderPicker(refs.importFolderPicker, {
        initialDirectory: settings.initialDirectory,
        loadDirectory: settings.loadDirectory,
        onError: showImportFolderError,
        onSubmit: settings.onSubmit
      });
    } catch (error) {
      closeImportFolderModal();
      return Promise.reject(error);
    }
    return Promise.resolve(importFolderPicker.ready).then(function () {
      if (
        importFolderPicker
        && typeof importFolderPicker.focusPreferred === "function"
      ) {
        importFolderPicker.focusPreferred();
      }
      return true;
    }).catch(function (error) {
      return showImportFolderError(error);
    });
  }

  function confirmImportFolder() {
    if (!importFolderPicker || typeof importFolderPicker.submit !== "function") {
      return Promise.resolve(false);
    }
    if (refs.importFolderConfirmButton) refs.importFolderConfirmButton.disabled = true;
    return Promise.resolve(importFolderPicker.submit()).then(function () {
      closeImportFolderModal();
      return true;
    }).catch(function (error) {
      return showImportFolderError(error);
    });
  }

  function projectImportTerminalResult() {
    if (refs.importCollectionModal && !refs.importCollectionModal.hidden) {
      return;
    }
    var cancelButton = ensureImportModalCancelButton();
    var runButton = document.getElementById("docsHtmlImportRun");
    if (runButton) runButton.hidden = true;
    if (!cancelButton) return;
    cancelButton.textContent = MODAL_TEXT.importCloseButton;
    focusImportModalEntry();
  }

  function projectImportBusy(busy) {
    var cancelButton = ensureImportModalCancelButton();
    if (cancelButton) cancelButton.disabled = Boolean(busy);
    if (!busy && cancelButton && cancelButton.textContent === MODAL_TEXT.importCloseButton) {
      focusImportModalEntry();
    }
  }

  function resetImportModalActions() {
    var cancelButton = ensureImportModalCancelButton();
    var runButton = document.getElementById("docsHtmlImportRun");
    if (runButton) runButton.hidden = false;
    if (cancelButton) {
      cancelButton.disabled = false;
      cancelButton.textContent = MODAL_TEXT.importCancelButton;
    }
  }

  function importCollectionInitialFocus() {
    return [
      refs.importCollectionCancelButton,
      refs.importCollectionCloseButton,
      refs.importCollectionRetryButton,
      refs.importCollectionConfirmButton
    ].find(isFocusableNow) || refs.importCollectionModal;
  }

  function invokeImportCollectionCommand(type) {
    if (typeof importCollectionCommand !== "function") return false;
    importCollectionCommand({ type: type });
    return true;
  }

  function closeImportCollectionModal(options) {
    if (!refs.importCollectionModal) return false;
    var settings = options || {};
    if (importCollectionLifecycle) {
      importCollectionLifecycle.close({
        restoreFocus: settings.restoreFocus !== false
      });
    }
    refs.importCollectionModal.hidden = true;
    importCollectionCommand = null;
    importCollectionPhase = "idle";
    return true;
  }

  function requestImportCollectionClose() {
    if (importCollectionPhase === "applying") return false;
    if (importCollectionPhase === "confirmation") {
      return invokeImportCollectionCommand("cancel");
    }
    return invokeImportCollectionCommand("close");
  }

  function ensureImportCollectionLifecycle() {
    if (importCollectionLifecycle || !refs.importCollectionModal) {
      return importCollectionLifecycle;
    }
    importCollectionLifecycle = createDocsViewerModalLifecycle({
      cancelElements: Array.from(
        refs.importCollectionModal.querySelectorAll("[data-import-collection-close]")
      ),
      document: document,
      initialFocus: importCollectionInitialFocus,
      modal: refs.importCollectionModal,
      onRequestClose: requestImportCollectionClose
    });
    return importCollectionLifecycle;
  }

  function transitionToImportCollectionModal() {
    if (!refs.importCollectionModal) return false;
    if (importLifecycle && importLifecycle.isActive()) {
      importLifecycle.close({ restoreFocus: false });
    }
    if (refs.importModal) refs.importModal.hidden = true;
    refs.importCollectionModal.hidden = false;
    var lifecycle = ensureImportCollectionLifecycle();
    if (lifecycle && !lifecycle.isActive()) {
      lifecycle.open({
        restoreFocus: importRestoreFocusTarget
      });
    }
    return true;
  }

  function projectImportCollectionActions(phase) {
    var confirmation = phase === "confirmation";
    var applying = phase === "applying";
    var blocked = phase === "blocked";
    var result = phase === "result";
    var projectionError = phase === "projection_error";
    if (refs.importCollectionCancelButton) {
      refs.importCollectionCancelButton.hidden = !(confirmation || applying);
      refs.importCollectionCancelButton.disabled = applying;
    }
    if (refs.importCollectionConfirmButton) {
      refs.importCollectionConfirmButton.hidden = !(confirmation || applying);
      refs.importCollectionConfirmButton.disabled = applying;
    }
    if (refs.importCollectionRetryButton) {
      refs.importCollectionRetryButton.hidden = !projectionError;
      refs.importCollectionRetryButton.disabled = false;
    }
    if (refs.importCollectionCloseButton) {
      refs.importCollectionCloseButton.hidden = !(blocked || result || projectionError);
      refs.importCollectionCloseButton.disabled = false;
    }
  }

  function projectImportCollectionState(viewState, onCommand) {
    var state = viewState || {};
    var phase = normalizeText(state.phase);
    importCollectionCommand = typeof onCommand === "function" ? onCommand : null;
    importCollectionPhase = phase || "idle";
    projectImportCollectionActions(importCollectionPhase);
    if (["confirmation", "blocked", "applying", "result", "projection_error"].includes(phase)) {
      transitionToImportCollectionModal();
      if (phase !== "applying" && importCollectionLifecycle) {
        importCollectionLifecycle.focusInitial();
      }
      return;
    }
    if (["cancelled", "idle"].includes(phase)) {
      closeImportCollectionModal();
    }
  }

  function openImportModal(options) {
    if (!refs.importModal || !refs.importRoot) return Promise.resolve();
    var settings = options || {};
    var stage = viewerStage();
    importEntryFocusTarget = null;
    var lifecycle = ensureImportModalLifecycle();
    refs.importModal.hidden = false;
    resetImportModalActions();
    if (lifecycle) {
      var requestedRestoreFocus = settings.restoreFocus;
      importRestoreFocusTarget = isFocusableNow(requestedRestoreFocus)
        ? requestedRestoreFocus
        : isFocusableNow(refs.manageImportButton)
          ? refs.manageImportButton
          : refs.manageActionsButton;
      lifecycle.open({
        restoreFocus: importRestoreFocusTarget
      });
    }
    var initResult = typeof callbacks.onImportOpen === "function" ? callbacks.onImportOpen(stage) : null;
    if (initResult && typeof initResult.then === "function") {
      return initResult.then(function () {
        focusImportModalEntry();
      }).catch(function () {
        focusImportModalEntry();
      });
    }
    focusImportModalEntry();
    return Promise.resolve();
  }

  function closeImportModal() {
    if (!refs.importModal || importModalBusy()) return false;
    if (importLifecycle) importLifecycle.close();
    refs.importModal.hidden = true;
    return true;
  }

  function setSettingsStatus(message, stateName) {
    setModalStatus(refs.settingsStatus, message, stateName);
  }

  function settingsFieldLabel(field) {
    return normalizeText(field).replace(/_/g, " ");
  }

  function hideSettingsFields() {
    if (refs.settingsBooleanField) refs.settingsBooleanField.hidden = true;
    if (refs.settingsBooleanInput) {
      refs.settingsBooleanInput.disabled = true;
      refs.settingsBooleanInput.checked = false;
      refs.settingsBooleanInput.name = "";
    }
    if (refs.settingsTextField) refs.settingsTextField.hidden = true;
    if (refs.settingsTextInput) {
      refs.settingsTextInput.disabled = true;
      refs.settingsTextInput.value = "";
      refs.settingsTextInput.name = "";
    }
  }

  function renderSettingsDescription(field) {
    if (!refs.settingsDescription) return;
    refs.settingsDescription.textContent = normalizeText(field && field.description);
    refs.settingsDescription.hidden = !refs.settingsDescription.textContent;
  }

  function renderSettingsField(field) {
    hideSettingsFields();
    if (!field) {
      renderSettingsDescription(null);
      return;
    }
    if (field.type === "string" && refs.settingsTextField && refs.settingsTextInput) {
      refs.settingsTextInput.disabled = false;
      refs.settingsTextInput.name = normalizeText(field.field);
      refs.settingsTextInput.value = normalizeText(field.current_value);
      if (refs.settingsTextLabel) {
        refs.settingsTextLabel.textContent = settingsFieldLabel(field.field);
      }
      refs.settingsTextField.hidden = false;
      renderSettingsDescription(field);
      return;
    }
    if (!refs.settingsBooleanField || !refs.settingsBooleanInput) return;
    refs.settingsBooleanInput.disabled = false;
    refs.settingsBooleanInput.name = normalizeText(field.field);
    refs.settingsBooleanInput.checked = field.current_value === true;
    if (refs.settingsBooleanLabel) {
      refs.settingsBooleanLabel.textContent = settingsFieldLabel(field.field);
    }
    refs.settingsBooleanField.hidden = false;
    renderSettingsDescription(field);
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
    if (refs.settingsStage) refs.settingsStage.textContent = "stage: " + viewerStage();
    renderSettingsField(null);
    setSettingsStatus(MODAL_TEXT.settingsLoading, "busy");
    renderSettingsWarnings([]);
    refs.settingsModal.hidden = false;
    if (settingsLifecycle) {
      settingsLifecycle.open({
        restoreFocus: isFocusableNow(refs.manageSettingsButton)
          ? refs.manageSettingsButton
          : refs.manageActionsButton
      });
    }
    return true;
  }

  function setSettingsField(field) {
    if (!settingsModalOpen()) return;
    settingsFieldState = field || null;
    if (!settingsFieldState) {
      if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = true;
      renderSettingsField(null);
      renderSettingsWarnings([]);
      setSettingsStatus(MODAL_TEXT.settingsEmpty, "");
      window.requestAnimationFrame(function () {
        focusWithoutScroll(refs.settingsCancelButton || refs.settingsModal);
      });
      return;
    }
    renderSettingsField(settingsFieldState);
    if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = management.managementBusy;
    renderSettingsWarnings(settingsFieldState.warnings || []);
    setSettingsStatus("", "");
    var fieldType = settingsFieldState.type;
    window.requestAnimationFrame(function () {
      var primaryInput = fieldType === "string" ? refs.settingsTextInput : refs.settingsBooleanInput;
      focusWithoutScroll(primaryInput || refs.settingsSaveButton || refs.settingsModal);
    });
  }

  function getSettingsChanges() {
    if (!settingsFieldState) return null;
    var fieldName = normalizeText(settingsFieldState.field);
    if (!fieldName) return null;
    if (settingsFieldState.type === "string") {
      if (!refs.settingsTextInput) return null;
      return {
        [fieldName]: normalizeText(refs.settingsTextInput.value)
      };
    }
    if (!refs.settingsBooleanInput) return null;
    return {
      [fieldName]: refs.settingsBooleanInput.checked === true
    };
  }

  function setSettingsLoadError(message) {
    if (!settingsModalOpen()) return;
    if (refs.settingsSaveButton) refs.settingsSaveButton.disabled = true;
    renderSettingsWarnings([]);
    setSettingsStatus(message || MODAL_TEXT.settingsLoadFailed, "error");
  }

  function closeSettingsModal() {
    if (!refs.settingsModal) return;
    if (settingsLifecycle) settingsLifecycle.close();
    refs.settingsModal.hidden = true;
    settingsFieldState = null;
  }

  function wireEvents() {
    if (refs.importFolderConfirmButton) {
      refs.importFolderConfirmButton.addEventListener("click", function () {
        confirmImportFolder();
      });
    }
    [
      refs.importCollectionCancelButton,
      refs.importCollectionConfirmButton,
      refs.importCollectionRetryButton,
      refs.importCollectionCloseButton
    ].filter(Boolean).forEach(function (button) {
      button.addEventListener("click", function () {
        invokeImportCollectionCommand(button.dataset.collectionCommand);
      });
    });
    if (refs.settingsForm) {
      refs.settingsForm.addEventListener("submit", function (event) {
        if (typeof callbacks.onSettingsSubmit === "function") callbacks.onSettingsSubmit(event);
      });
      ["input", "change"].forEach(function (eventName) {
        refs.settingsForm.addEventListener(eventName, function () {
          if (refs.settingsStatus && refs.settingsStatus.dataset.state === "error") {
            setSettingsStatus("", "");
          }
        });
      });
    }
  }

  return {
    closeImportModal: closeImportModal,
    closeImportFolderModal: closeImportFolderModal,
    closeSettingsModal: closeSettingsModal,
    getSettingsFieldState: function () {
      return settingsFieldState;
    },
    getSettingsChanges: getSettingsChanges,
    openImportModal: openImportModal,
    openImportFolderModal: openImportFolderModal,
    openSettingsModalShell: openSettingsModalShell,
    projectImportBusy: projectImportBusy,
    projectImportCollectionState: projectImportCollectionState,
    renderSettingsWarnings: renderSettingsWarnings,
    projectImportTerminalResult: projectImportTerminalResult,
    setSettingsField: setSettingsField,
    setSettingsLoadError: setSettingsLoadError,
    setSettingsStatus: setSettingsStatus,
    settingsModalOpen: settingsModalOpen,
    wireEvents: wireEvents
  };
}
