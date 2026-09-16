import {
  createDocsViewerManagementMetadataWorkflow
} from "./docs-viewer-management-metadata-workflow.js";
import {
  createDocsViewerManagementModalController
} from "./docs-viewer-management-modals.js";
import {
  createDocsViewerManagementSettingsWorkflow
} from "./docs-viewer-management-settings-workflow.js";
import {
  resolveManagementDocsCollectionCustomisation
} from "./docs-viewer-management-collection-customisation-registry.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function metadataCustomisationDescriptor(workspaceConfig, target) {
  if (!target || !target.collection) return null;
  var configs = Array.isArray(workspaceConfig && workspaceConfig.stageConfigs)
    ? workspaceConfig.stageConfigs
    : [];
  var stage = cleanString(target.stage);
  var collection = cleanString(target.collection).toLowerCase();
  var parent = configs.find(function (config) {
    return cleanString(config && config.stage) === stage;
  });
  var children = parent && Array.isArray(parent.collections) ? parent.collections : [];
  var child = children.find(function (record) {
    return cleanString(record && record.collection).toLowerCase() === collection;
  });
  if (!child) {
    throw new Error("Edit Metadata target collection is not configured.");
  }
  return child.collectionCustomisation || null;
}

function shellRef(shellRefs, name, id) {
  return shellRefs[name] || document.getElementById(id);
}

export function createDocsViewerManagementModalComposition(options = {}) {
  var shellRefs = options.shellRefs || {};
  var domains = options.domains || {};
  var documentIndex = domains.documentIndex || {};
  var management = domains.management || {};
  var routeSession = domains.routeSession || {};
  var workspaceConfig = domains.workspaceConfig || {};
  var context = options.context || {};
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
    metadataCancelButton: shellRef(shellRefs, "metadataCancelButton", "docsViewerMetadataCancelButton"),
    metadataDocId: shellRef(shellRefs, "metadataDocId", "docsViewerMetadataDocId"),
    metadataForm: shellRef(shellRefs, "metadataForm", "docsViewerMetadataForm"),
    metadataCustomisationHost: shellRef(shellRefs, "metadataCustomisationHost", "docsViewerMetadataCustomisationHost"),
    metadataDateDisplayInput: shellRef(shellRefs, "metadataDateDisplayInput", "docsViewerMetadataDateDisplayInput"),
    metadataDateInput: shellRef(shellRefs, "metadataDateInput", "docsViewerMetadataDateInput"),
    metadataModal: shellRef(shellRefs, "metadataModal", "docsViewerMetadataModal"),
    metadataParentField: shellRef(shellRefs, "metadataParentField", "docsViewerMetadataParentField"),
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
  var metadataWorkflow = createDocsViewerManagementMetadataWorkflow({
    documentIndex: documentIndex,
    management: management,
    routeSession: routeSession,
    refs: {
      dateDisplayInput: refs.metadataDateDisplayInput,
      dateInput: refs.metadataDateInput,
      parentInput: refs.metadataParentInput,
      saveButton: refs.metadataSaveButton,
      statusInput: refs.metadataStatusInput,
      summaryInput: refs.metadataSummaryInput,
      titleInput: refs.metadataTitleInput
    },
    callbacks: {
      getModalController: function () {
        return modalController;
      },
      loadMetadataDoc: callbacks.loadMetadataDoc,
      onLoadError: callbacks.onMetadataLoadError,
      onSave: callbacks.onMetadataSave,
      resolveMetadataContribution: function (target) {
        var descriptor = metadataCustomisationDescriptor(workspaceConfig, target);
        return resolveManagementDocsCollectionCustomisation(descriptor, {
          collection: {
            stage: cleanString(target && target.stage),
            collection: cleanString(target && target.collection).toLowerCase()
          }
        });
      }
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
    workspaceConfig: workspaceConfig,
    context: context,
    refs: refs,
    callbacks: {
      hideContextMenu: callbacks.hideContextMenu,
      hideManageActionsMenu: callbacks.hideManageActionsMenu,
      metadataParentOptions: metadataWorkflow.parentOptions,
      onImportOpen: callbacks.onImportOpen,
      onMetadataSubmit: metadataWorkflow.confirm,
      onSettingsSubmit: callbacks.onSettingsSubmit,
      viewerStage: callbacks.viewerStage
    }
  });

  return {
    metadataWorkflow: metadataWorkflow,
    modalController: modalController,
    settingsWorkflow: settingsWorkflow
  };
}
