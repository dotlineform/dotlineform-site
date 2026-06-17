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

export function bindSeriesEditorEvents(state, callbacks = {}) {
  invoke(callbacks.bindSelectionControls);
  bindCatalogueEditorActionMessageClearer(state.root, state.messageController, {
    isBusy: () => Boolean(state.isSaving || state.isBuilding || state.isDeleting),
    renderMessages: () => invoke(callbacks.updateEditorState)
  });
  state.newButton.addEventListener("click", () => invoke(callbacks.setNewSeriesMode));
  state.saveButton.addEventListener("click", () => {
    runAsync(callbacks.saveCurrentSeries, "catalogue_series_editor: unexpected save failure");
  });
  state.publicationButton.addEventListener("click", () => {
    runAsync(callbacks.applyPublicationChange, "catalogue_series_editor: unexpected publication failure");
  });
  state.deleteButton.addEventListener("click", () => {
    runAsync(callbacks.deleteCurrentSeries, "catalogue_series_editor: unexpected delete failure");
  });
}
