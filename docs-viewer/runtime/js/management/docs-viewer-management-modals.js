import {
  renderMetadataStatusOptionsMarkup,
  renderSettingsWarningsMarkup
} from "./docs-viewer-management-render.js";
import {
  normalizeText
} from "./docs-viewer-management-modal-shell.js";
import {
  createDocsViewerModalLifecycle
} from "./docs-viewer-modal-lifecycle.js";
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

var MODAL_TEXT = {
  importCancelButton: "Cancel",
  importCloseButton: "Close",
  settingsLoading: "Loading settings...",
  settingsEmpty: "No editable settings are available for this scope.",
  settingsLoadFailed: "Settings unavailable."
};

export function buildDocsViewerDeletePreviewBody(preview) {
  return (Array.isArray(preview && preview.warnings) ? preview.warnings : [])
    .map(normalizeText)
    .filter(Boolean);
}

export function createDocsViewerManagementModalController(options = {}) {
  var refs = options.refs || {};
  var management = options.management || {};
  var scopeConfig = options.scopeConfig || {};
  var context = options.context || {};
  var nav = options.nav || null;
  var callbacks = options.callbacks || {};
  var metadataModalResolve = null;
  var metadataStatusPointerValue = null;
  var metadataEditingDoc = null;
  var metadataEditingChoices = null;
  var settingsFieldState = null;
  var importModalCancelButton = null;
  var importLifecycle = null;
  var metadataParentPicker = createDocsViewerMetadataParentPicker({
    refs: refs,
    callbacks: callbacks
  });
  var metadataLifecycle = refs.metadataModal ? createDocsViewerModalLifecycle({
    cancelElements: Array.from(refs.metadataModal.querySelectorAll("[data-metadata-close]"))
      .concat(refs.metadataCancelButton || [])
      .filter(Boolean),
    document: document,
    initialFocus: function () { return refs.metadataTitleInput; },
    modal: refs.metadataModal,
    onRequestClose: function () { closeMetadataModal(); },
    consumeEscape: function (event) {
      if (event.defaultPrevented) return true;
      if (!refs.metadataParentPopup || refs.metadataParentPopup.hidden) return false;
      event.preventDefault();
      metadataParentPicker.hidePopup();
      return true;
    },
    selectInitialFocus: true
  }) : null;
  var settingsLifecycle = refs.settingsModal ? createDocsViewerModalLifecycle({
    cancelElements: Array.from(refs.settingsModal.querySelectorAll("[data-settings-close]"))
      .concat(refs.settingsCancelButton || [])
      .filter(Boolean),
    document: document,
    initialFocus: function () { return refs.settingsCancelButton || refs.settingsModal; },
    modal: refs.settingsModal,
    onRequestClose: function () { closeSettingsModal(); }
  }) : null;

  function viewerScope() {
    return typeof callbacks.viewerScope === "function" ? callbacks.viewerScope() : "";
  }

  function metadataModalOpen() {
    return Boolean(refs.metadataModal && !refs.metadataModal.hidden);
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

  function metadataStatusOptions(choices) {
    var allowedValues = Array.isArray(choices && choices.ui_status)
      ? new Set(choices.ui_status)
      : null;
    var optionRecords = [];
    (scopeConfig.uiStatuses || []).forEach(function (status) {
      if (allowedValues && !allowedValues.has(status.ui_status)) return;
      optionRecords.push({
        value: status.ui_status,
        label: status.emoji + " " + status.label
      });
    });
    if (allowedValues) {
      allowedValues.forEach(function (value) {
        if (optionRecords.some(function (option) { return option.value === value; })) return;
        optionRecords.push({ value: value, label: value });
      });
    }
    return optionRecords;
  }

  function renderMetadataStatusOptions(doc, choices) {
    if (!refs.metadataStatusInput) return;
    var selectedValue = String(doc && doc.ui_status || "").trim();
    renderMetadataStatusSelection(selectedValue, choices);
  }

  function renderMetadataStatusSelection(selectedValue, choices) {
    if (!refs.metadataStatusInput) return;
    refs.metadataStatusInput.innerHTML = renderMetadataStatusOptionsMarkup(
      metadataStatusOptions(choices),
      selectedValue
    );
    var selectedOption = Array.from(refs.metadataStatusInput.options).find(function (option) {
      return option.value === selectedValue;
    });
    refs.metadataStatusInput.selectedIndex = selectedOption ? selectedOption.index : -1;
    refs.metadataStatusInput.size = Math.max(1, refs.metadataStatusInput.options.length);
  }

  function renderMetadataGroupOptions(doc, choices) {
    if (!refs.metadataGroupField || !refs.metadataGroupInput) return;
    var values = Array.isArray(choices && choices.group) ? choices.group : [];
    var showGroup = values.length > 0;
    refs.metadataGroupField.hidden = !showGroup;
    refs.metadataGroupInput.disabled = !showGroup;
    refs.metadataGroupInput.replaceChildren();
    if (!showGroup) return;

    var emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = "No group";
    refs.metadataGroupInput.appendChild(emptyOption);
    values.forEach(function (value) {
      var option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      refs.metadataGroupInput.appendChild(option);
    });
    refs.metadataGroupInput.value = String(doc && doc.group || "").trim();
  }

  function clearMetadataStatusSelection() {
    if (!refs.metadataStatusInput || refs.metadataStatusInput.selectedIndex < 0) return false;
    refs.metadataStatusInput.selectedIndex = -1;
    ["input", "change"].forEach(function (eventName) {
      refs.metadataStatusInput.dispatchEvent(new window.Event(eventName, { bubbles: true }));
    });
    return true;
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

  function setMetadataStatus(message, stateName) {
    setModalStatus(refs.metadataStatus, message, stateName);
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

  function metadataReturnTarget(docId) {
    if (!docId || !nav) return null;
    var escapeCss = typeof context.cssEscape === "function"
      ? context.cssEscape
      : function (value) { return String(value || ""); };
    return nav.querySelector(
      '[data-doc-row-id="' + escapeCss(docId) + '"] .docsViewer__navLink'
    );
  }

  function closeMetadataModal(result) {
    if (!refs.metadataModal) return;
    dismissMetadataParentSuggestions();
    if (metadataLifecycle) metadataLifecycle.close();
    refs.metadataModal.hidden = true;
    management.metadataEditingDocId = "";
    metadataEditingDoc = null;
    metadataEditingChoices = null;
    if (metadataModalResolve) {
      var resolve = metadataModalResolve;
      metadataModalResolve = null;
      resolve(result || null);
    }
  }

  function openMetadataModal(doc, options) {
    var settings = options || {};
    var target = settings.target || null;
    if (!doc || !target || !refs.metadataModal || !refs.metadataForm || !refs.metadataTitleInput || !refs.metadataSummaryInput || !refs.metadataDateInput || !refs.metadataDateDisplayInput || !refs.metadataStatusInput || !refs.metadataGroupField || !refs.metadataGroupInput || !refs.metadataNonViewableInput || !refs.metadataParentField || !refs.metadataParentInput) {
      return Promise.resolve(null);
    }
    if (typeof callbacks.hideContextMenu === "function") callbacks.hideContextMenu();
    metadataEditingDoc = doc;
    metadataEditingChoices = settings.choices || null;
    management.metadataEditingDocId = doc.doc_id;
    if (refs.metadataDocId) {
      refs.metadataDocId.textContent = doc.doc_id;
    }

    refs.metadataTitleInput.value = doc.title || "";
    refs.metadataSummaryInput.value = doc.summary || "";
    refs.metadataDateInput.value = doc.date || "";
    refs.metadataDateDisplayInput.value = doc.date_display || "";
    renderMetadataStatusOptions(doc, metadataEditingChoices);
    renderMetadataGroupOptions(doc, metadataEditingChoices);
    refs.metadataNonViewableInput.checked = typeof callbacks.isDocNonViewable === "function" ? callbacks.isDocNonViewable(doc) : doc.viewable === false;
    var showParent = settings.showParent === true;
    refs.metadataParentField.hidden = !showParent;
    refs.metadataParentInput.disabled = !showParent;
    if (showParent) {
      renderMetadataParentOptions(doc);
    } else {
      refs.metadataParentInput.value = "";
      metadataParentPicker.hidePopup();
    }
    setMetadataStatus("", "");

    refs.metadataModal.hidden = false;
    if (metadataLifecycle) {
      metadataLifecycle.open({
        restoreFocus: metadataReturnTarget(doc.doc_id)
      });
    }
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
      initialFocus: function () { return cancelButton || refs.importRoot; },
      modal: refs.importModal,
      onRequestClose: function () { return closeImportModal(); }
    });
    return importLifecycle;
  }

  function focusImportModalEntry() {
    if (importLifecycle) importLifecycle.focusInitial();
  }

  function projectImportTerminalResult() {
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

  function openImportModal(options) {
    if (!refs.importModal || !refs.importRoot) return Promise.resolve();
    var settings = options || {};
    var scope = viewerScope();
    var lifecycle = ensureImportModalLifecycle();
    refs.importModal.hidden = false;
    resetImportModalActions();
    if (lifecycle) {
      var requestedRestoreFocus = settings.restoreFocus;
      lifecycle.open({
        restoreFocus: isFocusableNow(requestedRestoreFocus)
          ? requestedRestoreFocus
          : isFocusableNow(refs.manageImportButton)
            ? refs.manageImportButton
            : refs.manageActionsButton
      });
    }
    var initResult = typeof callbacks.onImportOpen === "function" ? callbacks.onImportOpen(scope) : null;
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
    if (refs.settingsScope) refs.settingsScope.textContent = "scope: " + viewerScope();
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

  function handleRootClick(event) {
    if (metadataModalOpen()) {
      if (refs.metadataParentPopup && !refs.metadataParentPopup.hidden && !event.target.closest(".docsViewer__parentPicker")) {
        metadataParentPicker.hidePopup();
      }
    }
    return false;
  }

  function wireEvents() {
    if (refs.metadataForm) {
      refs.metadataForm.addEventListener("submit", function (event) {
        event.preventDefault();
        if (typeof callbacks.onMetadataSubmit === "function") callbacks.onMetadataSubmit();
      });
      ["input", "change"].forEach(function (eventName) {
        refs.metadataForm.addEventListener(eventName, function () {
          if (refs.metadataStatus && refs.metadataStatus.dataset.state === "error") {
            setMetadataStatus("", "");
          }
        });
      });
    }
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
    if (refs.metadataStatusInput) {
      refs.metadataStatusInput.addEventListener("pointerdown", function (event) {
        var option = event.target && event.target.closest
          ? event.target.closest("option")
          : null;
        metadataStatusPointerValue = option
          ? String(refs.metadataStatusInput.value || "").trim()
          : null;
      });
      refs.metadataStatusInput.addEventListener("click", function (event) {
        var option = event.target && event.target.closest
          ? event.target.closest("option")
          : null;
        var repeatedValue = option
          && metadataStatusPointerValue !== null
          && option.value === metadataStatusPointerValue;
        metadataStatusPointerValue = null;
        if (repeatedValue) clearMetadataStatusSelection();
      });
      refs.metadataStatusInput.addEventListener("keydown", function (event) {
        if (event.key !== "Backspace" && event.key !== "Delete") return;
        if (refs.metadataStatusInput.selectedIndex < 0) return;
        event.preventDefault();
        clearMetadataStatusSelection();
      });
    }
    if (refs.metadataParentInput) {
      refs.metadataParentInput.addEventListener("input", function () {
        if (metadataEditingDoc) metadataParentPicker.handleInput(metadataEditingDoc);
      });
      refs.metadataParentInput.addEventListener("blur", function () {
        metadataParentPicker.hidePopup();
      });
      refs.metadataParentInput.addEventListener("keydown", function (event) {
        metadataParentPicker.handleInputKeydown(event, metadataEditingDoc);
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
    getSettingsChanges: getSettingsChanges,
    handleRootClick: handleRootClick,
    metadataModalOpen: metadataModalOpen,
    openImportModal: openImportModal,
    openMetadataModal: openMetadataModal,
    openSettingsModalShell: openSettingsModalShell,
    projectImportBusy: projectImportBusy,
    renderMetadataParentOptions: renderMetadataParentOptions,
    renderMetadataStatusOptions: renderMetadataStatusOptions,
    renderSettingsWarnings: renderSettingsWarnings,
    resolveMetadataParentId: resolveMetadataParentId,
    projectImportTerminalResult: projectImportTerminalResult,
    setSettingsField: setSettingsField,
    setSettingsLoadError: setSettingsLoadError,
    setMetadataStatus: setMetadataStatus,
    setSettingsStatus: setSettingsStatus,
    settingsModalOpen: settingsModalOpen,
    wireEvents: wireEvents
  };
}
