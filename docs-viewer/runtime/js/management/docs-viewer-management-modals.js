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

export function createDocsViewerManagementModalController(options = {}) {
  var refs = options.refs || {};
  var callbacks = options.callbacks || {};
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
    importModalCancelButton.textContent = "Cancel";
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
    cancelButton.textContent = "Close";
    focusImportModalEntry();
  }

  function projectImportBusy(busy) {
    var cancelButton = ensureImportModalCancelButton();
    if (cancelButton) cancelButton.disabled = Boolean(busy);
    if (!busy && cancelButton && cancelButton.textContent === "Close") {
      focusImportModalEntry();
    }
  }

  function resetImportModalActions() {
    var cancelButton = ensureImportModalCancelButton();
    var runButton = document.getElementById("docsHtmlImportRun");
    if (runButton) runButton.hidden = false;
    if (cancelButton) {
      cancelButton.disabled = false;
      cancelButton.textContent = "Cancel";
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
    var initResult = typeof callbacks.onImportOpen === "function" ? callbacks.onImportOpen() : null;
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
  }

  return {
    closeImportModal: closeImportModal,
    closeImportFolderModal: closeImportFolderModal,
    openImportModal: openImportModal,
    openImportFolderModal: openImportFolderModal,
    projectImportBusy: projectImportBusy,
    projectImportCollectionState: projectImportCollectionState,
    projectImportTerminalResult: projectImportTerminalResult,
    wireEvents: wireEvents
  };
}
