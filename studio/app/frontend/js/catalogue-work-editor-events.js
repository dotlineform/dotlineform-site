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

  state.detailSearchNode.addEventListener("input", () => {
    invoke(callbacks.updateDetailSections);
  });

  state.newFileLinkNode.addEventListener("click", () => {
    runAsync(callbacks.openEmbeddedEntryModal, "catalogue_work_editor: failed to open download modal", "download");
  });
  state.newLinkLinkNode.addEventListener("click", () => {
    runAsync(callbacks.openEmbeddedEntryModal, "catalogue_work_editor: failed to open link modal", "link");
  });

  state.newButton.addEventListener("click", () => {
    invoke(callbacks.setNewWorkMode);
  });
  state.fieldsNode.addEventListener("click", (event) => {
    const proseButton = event.target && event.target.closest ? event.target.closest('[data-prose-import="work"]') : null;
    if (!proseButton) return;
    runAsync(callbacks.importWorkProse, "catalogue_work_editor: unexpected prose import failure");
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
