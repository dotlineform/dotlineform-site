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

function closestTarget(event, selector) {
  return event.target && event.target.closest ? event.target.closest(selector) : null;
}

export function bindMomentEditorEvents(state, callbacks = {}) {
  invoke(callbacks.bindSelectionControls);
  bindCatalogueEditorActionMessageClearer(state.root, state.messageController, {
    ignoreEvent: (event) => Boolean(event.target && event.target.closest && event.target.closest("[data-media-refresh], [data-prose-import]")),
    isBusy: () => Boolean(state.isSaving || state.isBuilding || state.isDeleting || state.importIsBusy),
    renderMessages: () => invoke(callbacks.updateEditorState)
  });
  state.newButton.addEventListener("click", () => invoke(callbacks.enterImportMode));
  state.saveButton.addEventListener("click", () => {
    runAsync(callbacks.saveCurrentMoment, "catalogue_moment_editor: save failed");
  });
  state.publicationButton.addEventListener("click", () => {
    runAsync(callbacks.applyPublicationChange, "catalogue_moment_editor: publication failed");
  });
  state.deleteButton.addEventListener("click", () => {
    runAsync(callbacks.deleteCurrentMoment, "catalogue_moment_editor: delete failed");
  });
  state.importFileNode.addEventListener("input", () => {
    invoke(callbacks.updateImportFile, state.importFileNode.value);
  });
  state.importPreviewButton.addEventListener("click", () => {
    runAsync(callbacks.previewMomentImport, "catalogue_moment_editor: import preview failed");
  });
  state.importApplyButton.addEventListener("click", () => {
    runAsync(callbacks.applyMomentImport, "catalogue_moment_editor: import apply failed");
  });
  state.readinessNode.addEventListener("click", (event) => {
    const mediaButton = closestTarget(event, "[data-media-refresh]");
    if (mediaButton) {
      runAsync(callbacks.refreshMomentMedia, "catalogue_moment_editor: media refresh failed");
      return;
    }
    const button = closestTarget(event, "[data-prose-import]");
    if (!button) return;
    runAsync(callbacks.importMomentProse, "catalogue_moment_editor: prose import failed");
  });
}
