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

  state.filesResultsNode.addEventListener("click", (event) => {
    const editButton = closestTarget(event, "[data-download-edit]");
    if (editButton) {
      runAsync(
        callbacks.openEmbeddedEntryModal,
        "catalogue_work_editor: failed to edit download",
        "download",
        Number(editButton.getAttribute("data-download-edit"))
      );
      return;
    }
    const deleteButtonNode = closestTarget(event, "[data-download-delete]");
    if (deleteButtonNode) {
      runAsync(
        callbacks.deleteEmbeddedEntry,
        "catalogue_work_editor: failed to delete download",
        "download",
        Number(deleteButtonNode.getAttribute("data-download-delete"))
      );
    }
  });

  state.linksResultsNode.addEventListener("click", (event) => {
    const editButton = closestTarget(event, "[data-link-edit]");
    if (editButton) {
      runAsync(
        callbacks.openEmbeddedEntryModal,
        "catalogue_work_editor: failed to edit link",
        "link",
        Number(editButton.getAttribute("data-link-edit"))
      );
      return;
    }
    const deleteButtonNode = closestTarget(event, "[data-link-delete]");
    if (deleteButtonNode) {
      runAsync(
        callbacks.deleteEmbeddedEntry,
        "catalogue_work_editor: failed to delete link",
        "link",
        Number(deleteButtonNode.getAttribute("data-link-delete"))
      );
    }
  });

  state.newButton.addEventListener("click", () => {
    invoke(callbacks.setNewWorkMode);
  });
  state.previewNode.addEventListener("click", (event) => {
    const mediaButton = closestTarget(event, '[data-media-refresh="work"]');
    if (!mediaButton) return;
    runAsync(callbacks.refreshWorkMedia, "catalogue_work_editor: unexpected media refresh failure");
  });
  state.readinessNode.addEventListener("click", (event) => {
    const proseButton = closestTarget(event, "[data-prose-import]");
    if (!proseButton) return;
    runAsync(callbacks.importWorkProse, "catalogue_work_editor: unexpected prose import failure");
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
