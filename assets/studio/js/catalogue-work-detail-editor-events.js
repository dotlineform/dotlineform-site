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

export function bindWorkDetailEditorEvents(state, callbacks = {}) {
  invoke(callbacks.bindSelectionControls);
  state.readinessNode.addEventListener("click", (event) => {
    const button = closestTarget(event, "[data-media-refresh]");
    if (!button) return;
    runAsync(callbacks.refreshWorkDetailMedia, "catalogue_work_detail_editor: unexpected media refresh failure");
  });
  state.saveButton.addEventListener("click", () => {
    runAsync(callbacks.saveCurrentDetail, "catalogue_work_detail_editor: unexpected save failure");
  });
  state.publicationButton.addEventListener("click", () => {
    runAsync(callbacks.applyPublicationChange, "catalogue_work_detail_editor: unexpected publication failure");
  });
  state.deleteButton.addEventListener("click", () => {
    runAsync(callbacks.deleteCurrentDetail, "catalogue_work_detail_editor: unexpected delete failure");
  });
}
