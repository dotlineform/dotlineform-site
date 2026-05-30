import {
  getAnalyticsGroups,
  getAnalyticsText,
  loadAnalyticsConfigWithText
} from "./analytics-config.js";
import {
  loadSiteSeriesIndexJson,
  loadSiteWorksIndexJson,
  loadAnalyticsAliasesJson,
  loadAnalyticsAssignmentsJson,
  loadAnalyticsRegistryJson
} from "./analytics-data.js";
import {
  configureTagStudioDomain,
  normalize,
  normalizeWorkId
} from "./tag-studio-domain.js";
import {
  buildSaveModeText as buildTagStudioSaveModeText
} from "./tag-studio-save.js";
import {
  collectTagStudioSaveModalRefs,
  openTagStudioSaveModal,
  renderTagStudioSaveModal,
  wireTagStudioSaveModalEvents
} from "./tag-studio-modals.js";
import {
  renderContextHint,
  renderGroups,
  renderSelectedWork
} from "./tag-studio-render.js";
import {
  getMatchingWorkOptions,
  hidePopup,
  hideWorkPopup,
  renderPopup,
  renderWorkPopup
} from "./tag-studio-suggestions.js";
import {
  buildStateDiff,
  buildTagStudioState,
  restoreSelectionFromQuery
} from "./tag-studio-state.js";
import {
  activateTagStudioSelectedWork,
  addTagStudioResolvedTag,
  addTagStudioTagFromInput,
  addTagStudioWorkSelection,
  applyTagStudioSaveState,
  clearTagStudioSelectedWork,
  cycleTagStudioEntryWeight,
  removeTagStudioEditableEntry,
  restoreTagStudioDeletedEntry,
  selectTagStudioWorkFromInput
} from "./tag-studio-interactions.js";
import {
  handleTagStudioSave,
  probeTagStudioSaveMode,
  renderTagStudioSaveMode,
  syncTagStudioOfflineAutosave
} from "./tag-studio-save-controller.js";
import {
  buildTagStudioRouteStateDetail,
  markTagStudioRouteReady,
  syncTagStudioRouteBusyState
} from "./tag-studio-route-state.js";
import {
  bindTagSaveModeReprobe
} from "./tag-route-save-session.js";
import {
  setStudioRouteReady
} from "./analytics-route-state.js";
import {
  seriesTagEditorUi
} from "./analytics-ui.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const WEIGHT_VALUES = [0.3, 0.6, 0.9];
const DEFAULT_WEIGHT = 0.6;
const UI = seriesTagEditorUi;
const { className: UI_CLASS, selector: UI_SELECTOR } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagStudio);
} else {
  initTagStudio();
}

function syncRouteBusyState(state) {
  syncTagStudioRouteBusyState(state);
}

function markRouteReady(state, ready) {
  markTagStudioRouteReady(state, ready);
}

async function initTagStudio() {
  const mount = document.getElementById("tag-studio");
  if (!mount) return;
  const routeRoot = document.getElementById("seriesTagEditorRoot");

  let config = null;
  try {
    config = await loadAnalyticsConfigWithText("series_tag_editor");
  } catch (error) {
    renderFatalError(mount, "Failed to load tag editor config.");
    setStudioRouteReady(routeRoot, true, {
      ...buildTagStudioRouteStateDetail(null),
      mode: "empty"
    });
    return;
  }
  STUDIO_GROUPS = getAnalyticsGroups(config);
  configureTagStudioDomain({
    groups: STUDIO_GROUPS,
    weightValues: WEIGHT_VALUES,
    defaultWeight: DEFAULT_WEIGHT
  });

  const seriesId = String(mount.dataset.seriesId || "").trim();
  if (!seriesId) {
    renderFatalError(mount, studioText(config, "missing_series_id_error", "Tag Studio error: missing series id."));
    return;
  }

  try {
    const [registryJson, aliasesJson, assignmentsJson, seriesIndexJson, worksIndexJson] = await Promise.all([
      loadAnalyticsRegistryJson(config),
      loadAnalyticsAliasesJson(config),
      loadAnalyticsAssignmentsJson(config),
      loadSiteSeriesIndexJson(config),
      loadSiteWorksIndexJson(config)
    ]);
    const state = buildTagStudioState({
      mount,
      seriesId,
      registryJson,
      aliasesJson,
      assignmentsJson,
      seriesIndexJson,
      worksIndexJson,
      config,
      offlineSession: null,
      studioGroups: STUDIO_GROUPS,
      defaultWeight: DEFAULT_WEIGHT
    });
    restoreSelectionFromQuery(state);
    renderShell(state);
    if (!state.refs) return;
    wireEvents(state);
    renderAll(state);
    markRouteReady(state, true);
    void probeTagStudioSaveMode(state, saveControllerCallbacks());
  } catch (error) {
    renderFatalError(
      mount,
      studioText(
        config,
        "load_failed_error",
        "Failed to load tag data. Check /analytics/data/canonical/tag-registry.json, /analytics/data/canonical/tag-aliases.json, /analytics/data/canonical/tag-assignments.json, /assets/data/series_index.json, and /assets/data/works_index.json."
      )
    );
    setStudioRouteReady(routeRoot, true, {
      ...buildTagStudioRouteStateDetail(null),
      mode: "empty"
    });
  }
}

function renderShell(state) {
  const workInputPlaceholder = studioText(state.config, "work_input_placeholder", "work_id(s) in this series");
  const tagInputPlaceholder = studioText(state.config, "tag_input_placeholder", "tag slug or alias");
  const addButtonLabel = studioText(state.config, "add_button", "Add");
  const saveButtonLabel = studioText(state.config, "save_button", "Save Tags");
  const saveModeLabel = buildTagStudioSaveModeText(state.config, "offline", studioText);
  const refs = {
    workInput: state.mount.querySelector(UI_SELECTOR.workInput),
    selectedWork: state.mount.querySelector(UI_SELECTOR.workSelection),
    workPopup: state.mount.querySelector(UI_SELECTOR.workPopup),
    workPopupList: state.mount.querySelector(UI_SELECTOR.workPopupList),
    contextHint: state.mount.querySelector(UI_SELECTOR.contextHint),
    input: state.mount.querySelector(UI_SELECTOR.tagInput),
    addButton: state.mount.querySelector(UI_SELECTOR.addTag),
    popup: state.mount.querySelector(UI_SELECTOR.popup),
    popupList: state.mount.querySelector(UI_SELECTOR.popupList),
    status: state.mount.querySelector(UI_SELECTOR.status),
    groups: state.mount.querySelector(UI_SELECTOR.groups),
    saveButton: state.mount.querySelector(UI_SELECTOR.save),
    saveMode: state.mount.querySelector(UI_SELECTOR.saveMode),
    saveWarning: state.mount.querySelector(UI_SELECTOR.saveWarning),
    saveResult: state.mount.querySelector(UI_SELECTOR.saveResult),
    modalHost: state.mount.querySelector(UI_SELECTOR.modalHost)
  };

  const missingRef = Object.entries(refs).find(([, value]) => !value);
  if (missingRef) {
    renderFatalError(
      state.mount,
      studioText(state.config, "missing_template_shell_error", "Tag Studio error: missing template shell markup.")
    );
    return;
  }

  refs.workInput.setAttribute("placeholder", workInputPlaceholder);
  refs.input.setAttribute("placeholder", tagInputPlaceholder);
  refs.addButton.textContent = addButtonLabel;
  refs.saveButton.textContent = saveButtonLabel;
  refs.saveMode.textContent = saveModeLabel;
  refs.modalHost.innerHTML = renderTagStudioSaveModal(state);

  state.refs = {
    ...refs,
    ...collectTagStudioSaveModalRefs(state.mount)
  };
}

function wireEvents(state) {
  bindTagSaveModeReprobe(() => {
    void probeTagStudioSaveMode(state, saveControllerCallbacks());
  });

  state.refs.workInput.addEventListener("input", () => {
    setStatus(state, "", "");
    renderStatus(state);
    renderWorkPopup(state);
  });

  state.refs.workInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      selectTagStudioWorkFromInput(state, interactionCallbacks(state));
    } else if (event.key === "Escape") {
      hideWorkPopup(state);
    }
  });

  state.refs.input.addEventListener("input", () => {
    setStatus(state, "", "");
    renderStatus(state);
    renderPopup(state);
  });

  state.refs.input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addTagStudioTagFromInput(state, interactionCallbacks(state));
    } else if (event.key === "Escape") {
      hidePopup(state);
    }
  });

  document.addEventListener("pointerdown", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;

    if (state.refs.popup && !state.refs.popup.hidden) {
      if (!target.closest(UI_SELECTOR.popup) && !target.closest(UI_SELECTOR.tagInput)) {
        hidePopup(state);
      }
    }

    if (state.refs.workPopup && !state.refs.workPopup.hidden) {
      if (!target.closest(UI_SELECTOR.workPopup) && !target.closest(UI_SELECTOR.workInput)) {
        hideWorkPopup(state);
      }
    }
  });

  state.refs.addButton.addEventListener("click", () => {
    addTagStudioTagFromInput(state, interactionCallbacks(state));
  });

  state.refs.workPopupList.addEventListener("click", (event) => {
    const workButton = event.target.closest("button[data-popup-work-id]");
    if (!workButton) return;
    const workId = normalizeWorkId(workButton.getAttribute("data-popup-work-id"));
    if (!workId) return;
    addTagStudioWorkSelection(state, workId, true, interactionCallbacks(state));
  });

  state.refs.selectedWork.addEventListener("click", (event) => {
    const activateButton = event.target.closest("button[data-activate-work-id]");
    if (activateButton) {
      const workId = normalizeWorkId(activateButton.getAttribute("data-activate-work-id"));
      if (!workId) return;
      if (state.selectedWorkId === workId) {
        activateTagStudioSelectedWork(state, "", interactionCallbacks(state));
        return;
      }
      activateTagStudioSelectedWork(state, workId, interactionCallbacks(state));
      return;
    }
    const clearButton = event.target.closest("button[data-clear-selected-work]");
    if (!clearButton) return;
    const workId = normalizeWorkId(clearButton.getAttribute("data-clear-selected-work"));
    if (!workId) return;
    clearTagStudioSelectedWork(state, workId, interactionCallbacks(state));
  });

  state.refs.popupList.addEventListener("click", (event) => {
    const tagButton = event.target.closest("button[data-popup-tag-id]");
    if (tagButton) {
      const tagId = normalize(tagButton.getAttribute("data-popup-tag-id"));
      const tag = state.tagsById.get(tagId);
      if (!tag) return;
      addTagStudioResolvedTag(state, tag, { rawInput: tag.slug || tag.tag_id }, interactionCallbacks(state));
      state.refs.input.value = "";
      hidePopup(state);
      renderAll(state);
      return;
    }

    const aliasTargetButton = event.target.closest("button[data-popup-alias-target]");
    if (aliasTargetButton) {
      const tagId = normalize(aliasTargetButton.getAttribute("data-popup-alias-target"));
      const tag = state.tagsById.get(tagId);
      if (!tag) return;
      const aliasSource = normalize(aliasTargetButton.getAttribute("data-popup-alias-source"));
      addTagStudioResolvedTag(state, tag, {
        rawInput: aliasSource || tag.tag_id,
        alias: aliasSource
      }, interactionCallbacks(state));
      state.refs.input.value = "";
      hidePopup(state);
      renderAll(state);
    }
  });

  state.refs.groups.addEventListener("click", (event) => {
    const weightButton = event.target.closest("button[data-cycle-weight-entry-id]");
    if (weightButton) {
      const entryId = Number(weightButton.getAttribute("data-cycle-weight-entry-id"));
      if (!Number.isFinite(entryId)) return;
      cycleTagStudioEntryWeight(state, entryId, interactionCallbacks(state));
      return;
    }

    const button = event.target.closest("button[data-remove-entry-id]");
    if (button) {
      const entryId = Number(button.getAttribute("data-remove-entry-id"));
      removeTagStudioEditableEntry(state, entryId, interactionCallbacks(state));
      renderAll(state);
      return;
    }

    const restoreButton = event.target.closest("button[data-restore-tag-id]");
    if (!restoreButton) return;
    restoreTagStudioDeletedEntry(
      state,
      restoreButton.getAttribute("data-restore-tag-id"),
      restoreButton.getAttribute("data-restore-scope"),
      interactionCallbacks(state)
    );
    renderAll(state);
  });

  state.refs.saveButton.addEventListener("click", () => {
    void handleTagStudioSave(state, saveControllerCallbacks());
  });

  wireTagStudioSaveModalEvents(state, {
    onCopySnippet: () => {
      void copySaveModalSnippet(state);
    }
  });
}

async function copySaveModalSnippet(state) {
  if (!state.modalSnippet) return;
  try {
    await navigator.clipboard.writeText(state.modalSnippet);
    setStatus(state, "success", studioText(state.config, "save_status_copy", "Patch guidance copied to clipboard."));
  } catch (error) {
    setStatus(state, "error", studioText(state.config, "save_status_copy_failed", "Copy failed. Select and copy the patch guidance manually."));
  }
  renderStatus(state);
}

function renderAll(state) {
  renderSelectedWork(state);
  renderContextHint(state);
  renderStatus(state);
  renderGroups(state);
  renderWorkPopup(state);
  renderPopup(state);
  renderTagStudioSaveMode(state);
  applyTagStudioSaveState(state, interactionCallbacks(state));
  broadcastSelectedWorkChange(state);
  syncTagStudioOfflineAutosave(state, saveControllerCallbacks());
  syncRouteBusyState(state);
}

function openSaveModal(state) {
  const diff = buildStateDiff(state);
  if (!diff.seriesChanged && !diff.changedWorkIds.length) {
    setStatus(state, "warn", studioText(state.config, "save_status_no_changes", "No changes to save."));
    renderStatus(state);
    return;
  }

  openTagStudioSaveModal(state, diff);
}

function setStatus(state, kind, text) {
  state.statusKind = kind || "";
  state.statusText = text || "";
}

function renderStatus(state) {
  state.refs.status.textContent = state.statusText || "";
  if (state.statusKind) {
    state.refs.status.dataset.state = state.statusKind;
    return;
  }
  delete state.refs.status.dataset.state;
}

function setSaveResult(state, kind, text) {
  if (!state.refs.saveResult) return;
  state.refs.saveResult.textContent = text || "";
  if (kind) {
    state.refs.saveResult.dataset.state = kind;
    return;
  }
  delete state.refs.saveResult.dataset.state;
}

function interactionCallbacks(state) {
  return {
    getMatchingWorkOptions,
    hidePopup,
    hideWorkPopup,
    renderAll,
    renderStatus,
    renderWorkPopup,
    setSaveResult,
    setStatus,
    text: (key, fallback, tokens) => studioText(state.config, key, fallback, tokens)
  };
}

function saveControllerCallbacks() {
  return {
    renderAll,
    renderStatus,
    setSaveResult,
    syncRouteBusyState
  };
}

function hasPendingSaveChanges(state) {
  const diff = buildStateDiff(state);
  return diff.seriesChanged || diff.changedWorkIds.length > 0;
}

function broadcastSelectedWorkChange(state) {
  const nextWorkId = state.selectedWorkId || "";
  if (state.lastBroadcastSelectedWorkId === nextWorkId) return;
  state.lastBroadcastSelectedWorkId = nextWorkId;
  window.dispatchEvent(new CustomEvent("series-tag-editor:selected-work-change", {
    detail: {
      seriesId: state.seriesId,
      workId: nextWorkId
    }
  }));
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderFatalError(mount, message) {
  mount.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(message)}</div>`;
}

function studioText(config, key, fallback, tokens) {
  return getAnalyticsText(config, `series_tag_editor.${key}`, fallback, tokens);
}
