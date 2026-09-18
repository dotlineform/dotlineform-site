import {
  createDocsViewerManagementModalController
} from "./docs-viewer-management-modals.js";
import {
  createDocsViewerManagementSettingsWorkflow
} from "./docs-viewer-management-settings-workflow.js";

function shellRef(shellRefs, name, id) {
  return shellRefs[name] || document.getElementById(id);
}

export function createDocsViewerManagementModalComposition(options = {}) {
  var shellRefs = options.shellRefs || {};
  var domains = options.domains || {};
  var management = domains.management || {};
  var callbacks = options.callbacks || {};
  var refs = {
    importModal: shellRef(shellRefs, "importModal", "docsViewerImportModal"),
    importRoot: shellRef(shellRefs, "importRoot", "docsHtmlImportRoot"),
    importFolderModal: shellRef(shellRefs, "importFolderModal", "docsViewerImportFolderModal"),
    importFolderPicker: shellRef(shellRefs, "importFolderPicker", "docsViewerImportFolderPicker"),
    importFolderCancelButton: shellRef(shellRefs, "importFolderCancelButton", "docsViewerImportFolderCancel"),
    importFolderConfirmButton: shellRef(shellRefs, "importFolderConfirmButton", "docsViewerImportFolderConfirm"),
    importCollectionModal: shellRef(shellRefs, "importCollectionModal", "docsViewerImportCollectionModal"),
    importCollectionCancelButton: shellRef(shellRefs, "importCollectionCancelButton", "docsImportCollectionCancel"),
    importCollectionConfirmButton: shellRef(shellRefs, "importCollectionConfirmButton", "docsImportCollectionConfirm"),
    importCollectionRetryButton: shellRef(shellRefs, "importCollectionRetryButton", "docsImportCollectionRetry"),
    importCollectionCloseButton: shellRef(shellRefs, "importCollectionCloseButton", "docsImportCollectionClose"),
    manageActionsButton: options.manageActionsButton || null,
    manageImportButton: options.manageImportButton || null,
    manageSettingsButton: options.manageSettingsButton || null,
    settingsCancelButton: shellRef(shellRefs, "settingsCancelButton", "docsViewerSettingsCancelButton"),
    settingsForm: shellRef(shellRefs, "settingsForm", "docsViewerSettingsForm"),
    settingsModal: shellRef(shellRefs, "settingsModal", "docsViewerSettingsModal"),
    settingsSaveButton: shellRef(shellRefs, "settingsSaveButton", "docsViewerSettingsSaveButton"),
    settingsStage: shellRef(shellRefs, "settingsStage", "docsViewerSettingsStage"),
    settingsBooleanField: shellRef(shellRefs, "settingsBooleanField", "docsViewerSettingsBooleanField"),
    settingsBooleanInput: shellRef(shellRefs, "settingsBooleanInput", "docsViewerSettingsBooleanInput"),
    settingsBooleanLabel: shellRef(shellRefs, "settingsBooleanLabel", "docsViewerSettingsBooleanLabel"),
    settingsTextField: shellRef(shellRefs, "settingsTextField", "docsViewerSettingsTextField"),
    settingsTextInput: shellRef(shellRefs, "settingsTextInput", "docsViewerSettingsTextInput"),
    settingsTextLabel: shellRef(shellRefs, "settingsTextLabel", "docsViewerSettingsTextLabel"),
    settingsDescription: shellRef(shellRefs, "settingsDescription", "docsViewerSettingsDescription"),
    settingsStatus: shellRef(shellRefs, "settingsStatus", "docsViewerSettingsStatus"),
    settingsWarnings: shellRef(shellRefs, "settingsWarnings", "docsViewerSettingsWarnings")
  };
  var modalController = null;
  var settingsWorkflow = createDocsViewerManagementSettingsWorkflow({
    management: management,
    refs: {
      saveButton: refs.settingsSaveButton
    },
    callbacks: {
      getModalController: function () {
        return modalController;
      },
      hideContextMenu: callbacks.hideContextMenu,
      hideManageActionsMenu: callbacks.hideManageActionsMenu,
      managementClientOptions: callbacks.managementClientOptions
    }
  });

  modalController = createDocsViewerManagementModalController({
    management: management,
    refs: refs,
    callbacks: {
      hideContextMenu: callbacks.hideContextMenu,
      hideManageActionsMenu: callbacks.hideManageActionsMenu,
      onImportOpen: callbacks.onImportOpen,
      onSettingsSubmit: callbacks.onSettingsSubmit,
      viewerStage: callbacks.viewerStage
    }
  });

  return {
    modalController: modalController,
    settingsWorkflow: settingsWorkflow
  };
}
