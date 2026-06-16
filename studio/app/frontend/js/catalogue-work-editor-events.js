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

  state.root.addEventListener("click", (event) => {
    const refreshButton = event.target && event.target.closest ? event.target.closest('[data-media-refresh="work"]') : null;
    if (refreshButton) return;
    invoke(callbacks.clearMediaRefreshStatus);
  }, { capture: true });

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
  state.previewNode.addEventListener("click", (event) => {
    const mediaButton = event.target && event.target.closest ? event.target.closest('[data-media-refresh="work"]') : null;
    if (!mediaButton) return;
    runAsync(callbacks.refreshWorkMedia, "catalogue_work_editor: unexpected media refresh failure");
  });
  state.saveButton.addEventListener("click", () => {
    runAsync(callbacks.saveCurrentWork, "catalogue_work_editor: unexpected save failure");
  });
  state.publicationButton.addEventListener("click", () => {
    runAsync(callbacks.applyPublicationChange, "catalogue_work_editor: unexpected publication failure");
  });
  state.deleteButton.addEventListener("click", () => {
    runAsync(callbacks.deleteCurrentWork, "catalogue_work_editor: unexpected delete failure");
  });
}
