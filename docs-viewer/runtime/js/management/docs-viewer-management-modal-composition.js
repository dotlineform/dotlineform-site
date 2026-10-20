import {
  createDocsViewerManagementModalController
} from "./docs-viewer-management-modals.js";

function shellRef(shellRefs, name, id) {
  return shellRefs[name] || document.getElementById(id);
}

export function createDocsViewerManagementModalComposition(options = {}) {
  var shellRefs = options.shellRefs || {};
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
    manageActionsButton: options.manageActionsButton || null
  };
  var modalController = createDocsViewerManagementModalController({
    refs: refs,
    callbacks: {
      hideContextMenu: callbacks.hideContextMenu,
      hideManageActionsMenu: callbacks.hideManageActionsMenu,
      onImportOpen: callbacks.onImportOpen
    }
  });

  return {
    modalController: modalController
  };
}
