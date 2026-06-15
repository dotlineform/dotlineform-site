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

export function bindSeriesEditorEvents(state, callbacks = {}) {
  invoke(callbacks.bindSelectionControls);
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
  state.memberSearchNode.addEventListener("input", () => invoke(callbacks.updateMemberList));
  state.memberAddButton.addEventListener("click", () => invoke(callbacks.addMember));
  state.memberAddNode.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    invoke(callbacks.addMember);
  });
  state.membersResultsNode.addEventListener("click", (event) => {
    const primaryButton = closestTarget(event, "[data-member-primary]");
    if (primaryButton) {
      invoke(callbacks.makeMemberPrimary, primaryButton.getAttribute("data-member-primary"));
      return;
    }
    const removeButton = closestTarget(event, "[data-member-remove]");
    if (removeButton) {
      invoke(callbacks.removeMember, removeButton.getAttribute("data-member-remove"));
    }
  });
}
