import {
  bindCatalogueEditorActionMessageClearer
} from "./catalogue-editor-message-controller.js";

function invoke(callback, ...args) {
  if (typeof callback === "function") return callback(...args);
  return undefined;
}

function runAsync(callback, label, ...args) {
  const result = invoke(callback, ...args);
  if (result && typeof result.catch === "function") {
    result.catch((error) => console.warn(label, error));
  }
}

export function bindWorkEditorEvents(state, callbacks = {}) {
  invoke(callbacks.bindSelectionControls);

  bindCatalogueEditorActionMessageClearer(state.root, state.messageController, {
    ignoreEvent: (event) => Boolean(event.target && event.target.closest && event.target.closest('[data-media-refresh="work"]')),
    isBusy: () => Boolean(state.isSaving || state.isBuilding || state.isDeleting),
    preserveWithin: state.statusNode,
    renderMessages: () => invoke(callbacks.renderEditorMessage)
  });

  state.detailBrowserSearchNode.addEventListener("input", () => {
    invoke(callbacks.updateWorkDetailBrowser);
  });
  state.detailBrowserSearchClearNode.addEventListener("click", () => {
    state.detailBrowserSearchNode.value = "";
    state.detailBrowserSearchNode.focus();
    invoke(callbacks.updateWorkDetailBrowser);
  });

  state.newButton.addEventListener("click", () => {
    invoke(callbacks.setNewWorkMode);
  });
  state.saveButton.addEventListener("click", () => {
    runAsync(callbacks.saveCurrentWork, "catalogue_work_editor: unexpected save failure");
  });
  state.deleteButton.addEventListener("click", () => {
    runAsync(callbacks.deleteCurrentWork, "catalogue_work_editor: unexpected delete failure");
  });
}
