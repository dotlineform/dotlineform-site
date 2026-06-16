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

export function bindWorkDetailEditorEvents(state, callbacks = {}) {
  invoke(callbacks.bindSelectionControls);
  state.saveButton.addEventListener("click", () => {
    runAsync(callbacks.saveCurrentDetail, "catalogue_work_detail_editor: unexpected save failure");
  });
  state.deleteButton.addEventListener("click", () => {
    runAsync(callbacks.deleteCurrentDetail, "catalogue_work_detail_editor: unexpected delete failure");
  });
}
