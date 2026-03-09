function freezeMap(map) {
  return Object.freeze({ ...map });
}

function selectorMap(roleMap) {
  return freezeMap(
    Object.fromEntries(
      Object.entries(roleMap).map(([key, value]) => [key, `[data-role="${value}"]`])
    )
  );
}

export function createUiContract({ role, className = {}, state = {} }) {
  const frozenRole = freezeMap(role);
  return Object.freeze({
    role: frozenRole,
    selector: selectorMap(frozenRole),
    className: freezeMap(className),
    state: freezeMap(state)
  });
}

export const seriesTagEditorUi = createUiContract({
  role: {
    editorRoot: "series-tag-editor",
    editorShell: "editor-shell",
    workSection: "work-section",
    workInput: "work-input",
    workSelection: "selected-work",
    workPopup: "work-popup",
    workPopupList: "work-popup-list",
    messageSection: "message-section",
    contextHint: "context-hint",
    status: "status",
    saveWarning: "save-warning",
    saveResult: "save-result",
    groupsSection: "groups-section",
    groups: "groups",
    searchSection: "search-section",
    tagInput: "tag-input",
    addTag: "add-tag",
    save: "save",
    saveMode: "save-mode",
    popup: "popup",
    popupList: "popup-list",
    modalHost: "modal-host",
    modal: "modal",
    modalClose: "close-modal",
    modalTags: "modal-tags",
    modalSnippet: "modal-snippet",
    copySnippet: "copy-snippet"
  },
  className: {
    modalLabel: "tagStudioModal__label",
    modalPre: "tagStudioModal__pre",
    error: "tagStudioError",
    selectedWorkPill: "tagStudio__selectedWorkPill",
    selectedWorkButton: "tagStudio__selectedWorkBtn",
    selectedWorkId: "tagStudio__selectedWorkId",
    chipRemove: "tagStudio__chipRemove",
    suggest: "tagStudioSuggest",
    suggestSection: "tagStudioSuggest__section",
    suggestHeading: "tagStudioSuggest__heading",
    suggestWorkRows: "tagStudioSuggest__workRows",
    suggestWorkButton: "tagStudioSuggest__workButton",
    suggestWorkId: "tagStudioSuggest__workId",
    suggestWorkTitle: "tagStudioSuggest__workTitle",
    suggestTagRows: "tagStudioSuggest__tagRows",
    suggestAliasRows: "tagStudioSuggest__aliasRows",
    suggestAliasRow: "tagStudioSuggest__aliasRow",
    suggestAliasPill: "tagStudioSuggest__aliasPill",
    suggestAliasTargets: "tagStudioSuggest__aliasTargets",
    suggestAliasTarget: "tagStudioSuggest__aliasTarget",
    popupPill: "tagStudio__popupPill",
    empty: "tagStudio__empty",
    groups: "tagStudioGroups",
    groupRow: "tagStudioGroupRow",
    groupRowLabel: "tagStudioGroupRow__label",
    groupRowChips: "tagStudioGroupRow__chips",
    chip: "tagStudio__chip",
    chipInherited: "tagStudio__chip--inherited",
    chipTag: "tagStudio__chipTag",
    chipGroupPrefix: "tagStudio__chip--",
    weightDot: "tagStudio__weightDot",
    weightDotLow: "tagStudio__weightDot--low",
    weightDotMid: "tagStudio__weightDot--mid",
    weightDotHigh: "tagStudio__weightDot--high"
  },
  state: {
    active: "active",
    success: "success",
    warn: "warn",
    error: "error"
  }
});
