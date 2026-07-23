import {
  createDocsViewerManagementMetadataWorkflow
} from "./docs-viewer-management-metadata-workflow.js";
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
  var documentIndex = domains.documentIndex || {};
  var management = domains.management || {};
  var routeSession = domains.routeSession || {};
  var scopeConfig = domains.scopeConfig || {};
  var context = options.context || {};
  var callbacks = options.callbacks || {};
  var refs = {
    importModal: shellRef(shellRefs, "importModal", "docsViewerImportModal"),
    importRoot: shellRef(shellRefs, "importRoot", "docsHtmlImportRoot"),
    manageActionsButton: options.manageActionsButton || null,
    manageImportButton: options.manageImportButton || null,
    manageSettingsButton: options.manageSettingsButton || null,
    metadataCancelButton: shellRef(shellRefs, "metadataCancelButton", "docsViewerMetadataCancelButton"),
    metadataDocId: shellRef(shellRefs, "metadataDocId", "docsViewerMetadataDocId"),
    metadataForm: shellRef(shellRefs, "metadataForm", "docsViewerMetadataForm"),
    metadataDateDisplayInput: shellRef(shellRefs, "metadataDateDisplayInput", "docsViewerMetadataDateDisplayInput"),
    metadataDateInput: shellRef(shellRefs, "metadataDateInput", "docsViewerMetadataDateInput"),
    metadataNonViewableInput: shellRef(shellRefs, "metadataNonViewableInput", "docsViewerMetadataNonViewableInput"),
    metadataModal: shellRef(shellRefs, "metadataModal", "docsViewerMetadataModal"),
    metadataParentInput: shellRef(shellRefs, "metadataParentInput", "docsViewerMetadataParentInput"),
    metadataParentPopup: shellRef(shellRefs, "metadataParentPopup", "docsViewerMetadataParentPopup"),
    metadataSaveButton: shellRef(shellRefs, "metadataSaveButton", "docsViewerMetadataSaveButton"),
    metadataStatus: shellRef(shellRefs, "metadataStatus", "docsViewerMetadataStatus"),
    metadataStatusInput: shellRef(shellRefs, "metadataStatusInput", "docsViewerMetadataStatusInput"),
    metadataSummaryInput: shellRef(shellRefs, "metadataSummaryInput", "docsViewerMetadataSummaryInput"),
    metadataTitleInput: shellRef(shellRefs, "metadataTitleInput", "docsViewerMetadataTitleInput"),
    settingsCancelButton: shellRef(shellRefs, "settingsCancelButton", "docsViewerSettingsCancelButton"),
    settingsForm: shellRef(shellRefs, "settingsForm", "docsViewerSettingsForm"),
    settingsModal: shellRef(shellRefs, "settingsModal", "docsViewerSettingsModal"),
    settingsSaveButton: shellRef(shellRefs, "settingsSaveButton", "docsViewerSettingsSaveButton"),
    settingsScope: shellRef(shellRefs, "settingsScope", "docsViewerSettingsScope"),
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
  var metadataWorkflow = createDocsViewerManagementMetadataWorkflow({
    documentIndex: documentIndex,
    management: management,
    routeSession: routeSession,
    refs: {
      dateDisplayInput: refs.metadataDateDisplayInput,
      dateInput: refs.metadataDateInput,
      nonViewableInput: refs.metadataNonViewableInput,
      parentInput: refs.metadataParentInput,
      saveButton: refs.metadataSaveButton,
      statusInput: refs.metadataStatusInput,
      summaryInput: refs.metadataSummaryInput,
      titleInput: refs.metadataTitleInput
    },
    callbacks: {
      currentActiveDoc: callbacks.currentActiveDoc,
      getModalController: function () {
        return modalController;
      },
      onSave: callbacks.onMetadataSave
    }
  });
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
    nav: options.nav || null,
    documentIndex: documentIndex,
    management: management,
    scopeConfig: scopeConfig,
    context: context,
    refs: refs,
    callbacks: {
      currentActiveDoc: callbacks.currentActiveDoc,
      hideContextMenu: callbacks.hideContextMenu,
      hideManageActionsMenu: callbacks.hideManageActionsMenu,
      isDocNonViewable: callbacks.isDocNonViewable,
      metadataParentOptions: metadataWorkflow.parentOptions,
      onImportOpen: callbacks.onImportOpen,
      onMetadataSubmit: metadataWorkflow.confirm,
      onSettingsSubmit: callbacks.onSettingsSubmit,
      viewerScope: callbacks.viewerScope
    }
  });

  return {
    metadataWorkflow: metadataWorkflow,
    modalController: modalController,
    settingsWorkflow: settingsWorkflow
  };
}
