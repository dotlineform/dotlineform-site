import {
  getStudioGroups,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  loadSiteSeriesIndexJson,
  loadSiteWorksIndexJson,
  loadAnalyticsAliasesJson,
  loadAnalyticsAssignmentsJson,
  loadAnalyticsRegistryJson
} from "./studio-tag-data.js";
import {
  configureAnalyticsTagEditorDomain,
  normalize,
  normalizeWorkId
} from "./analytics-tag-editor-domain.js";
import {
  renderContextHint,
  renderGroups,
  renderSelectedWork
} from "./analytics-tag-editor-render.js";
import {
  getMatchingWorkOptions,
  hidePopup,
  hideWorkPopup,
  renderPopup,
  renderWorkPopup
} from "./analytics-tag-editor-suggestions.js";
import {
  buildAnalyticsTagEditorState,
  restoreSelectionFromQuery
} from "./analytics-tag-editor-state.js";
import {
  activateAnalyticsTagEditorSelectedWork,
  addAnalyticsTagEditorResolvedTag,
  addAnalyticsTagEditorTagFromInput,
  addAnalyticsTagEditorWorkSelection,
  applyAnalyticsTagEditorSaveState,
  clearAnalyticsTagEditorSelectedWork,
  cycleAnalyticsTagEditorEntryWeight,
  removeAnalyticsTagEditorEditableEntry,
  selectAnalyticsTagEditorWorkFromInput
} from "./analytics-tag-editor-interactions.js";
import {
  handleAnalyticsTagEditorSave,
  probeAnalyticsTagEditorService
} from "./analytics-tag-editor-save-controller.js";
import {
  buildAnalyticsTagEditorRouteStateDetail,
  markAnalyticsTagEditorRouteReady,
  syncAnalyticsTagEditorRouteBusyState
} from "./analytics-tag-editor-route-state.js";
import {
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  seriesTagEditorUi
} from "./tag-ui.js";

let ANALYTICS_GROUPS = ["subject", "domain", "form", "theme"];
const WEIGHT_VALUES = [0.3, 0.6, 0.9];
const DEFAULT_WEIGHT = 0.6;
const UI = seriesTagEditorUi;
const { className: UI_CLASS, selector: UI_SELECTOR } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initAnalyticsTagEditor);
} else {
  initAnalyticsTagEditor();
}

function syncRouteBusyState(state) {
  syncAnalyticsTagEditorRouteBusyState(state);
}

function markRouteReady(state, ready) {
  markAnalyticsTagEditorRouteReady(state, ready);
}

async function initAnalyticsTagEditor() {
  const mount = document.getElementById("analytics-tag-editor");
  if (!mount) return;
  const routeRoot = document.getElementById("seriesTagEditorRoot");

  let config;
  try {
    config = await loadStudioConfig();
  } catch (error) {
    renderFatalError(mount, "Failed to load tag editor config.");
    setStudioRouteReady(routeRoot, true, {
      ...buildAnalyticsTagEditorRouteStateDetail(null),
      mode: "empty"
    });
    return;
  }
  ANALYTICS_GROUPS = getStudioGroups(config);
  configureAnalyticsTagEditorDomain({
    groups: ANALYTICS_GROUPS,
    weightValues: WEIGHT_VALUES,
    defaultWeight: DEFAULT_WEIGHT
  });

  const seriesId = String(mount.dataset.seriesId || "").trim();
  if (!seriesId) {
    renderFatalError(mount, analyticsTagEditorText(config, "missing_series_id_error", "Tag editor error: missing series id."));
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
    const state = buildAnalyticsTagEditorState({
      mount,
      seriesId,
      registryJson,
      aliasesJson,
      assignmentsJson,
      seriesIndexJson,
      worksIndexJson,
      config,
      studioGroups: ANALYTICS_GROUPS,
      defaultWeight: DEFAULT_WEIGHT
    });
    restoreSelectionFromQuery(state);
    renderShell(state);
    if (!state.refs) return;
    wireEvents(state);
    renderAll(state);
    markRouteReady(state, true);
    void probeAnalyticsTagEditorService(state, saveControllerCallbacks());
  } catch (error) {
    renderFatalError(
      mount,
      analyticsTagEditorText(
        config,
        "load_failed_error",
        "Failed to load tag data. Check /studio/api/tags/tag-registry, /studio/api/tags/tag-aliases, /studio/api/tags/tag-assignments, /assets/data/series_index.json, and /assets/data/works_index.json."
      )
    );
    setStudioRouteReady(routeRoot, true, {
      ...buildAnalyticsTagEditorRouteStateDetail(null),
      mode: "empty"
    });
  }
}

function renderShell(state) {
  const workInputPlaceholder = analyticsTagEditorText(state.config, "work_input_placeholder", "work_id(s) in this series");
  const tagInputPlaceholder = analyticsTagEditorText(state.config, "tag_input_placeholder", "tag slug or alias");
  const addButtonLabel = analyticsTagEditorText(state.config, "add_button", "Add");
  const saveButtonLabel = analyticsTagEditorText(state.config, "save_button", "Save Tags");
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
    saveWarning: state.mount.querySelector(UI_SELECTOR.saveWarning),
    saveResult: state.mount.querySelector(UI_SELECTOR.saveResult)
  };

  const missingRef = Object.entries(refs).find(([, value]) => !value);
  if (missingRef) {
    renderFatalError(
      state.mount,
      analyticsTagEditorText(state.config, "missing_template_shell_error", "Tag editor error: missing template shell markup.")
    );
    return;
  }

  refs.workInput.setAttribute("placeholder", workInputPlaceholder);
  refs.input.setAttribute("placeholder", tagInputPlaceholder);
  refs.addButton.textContent = addButtonLabel;
  refs.saveButton.textContent = saveButtonLabel;
  state.refs = refs;
}

function wireEvents(state) {
  state.refs.workInput.addEventListener("input", () => {
    setStatus(state, "", "");
    renderStatus(state);
    renderWorkPopup(state);
  });

  state.refs.workInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      selectAnalyticsTagEditorWorkFromInput(state, interactionCallbacks(state));
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
      addAnalyticsTagEditorTagFromInput(state, interactionCallbacks(state));
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
    addAnalyticsTagEditorTagFromInput(state, interactionCallbacks(state));
  });

  state.refs.workPopupList.addEventListener("click", (event) => {
    const workButton = event.target.closest("button[data-popup-work-id]");
    if (!workButton) return;
    const workId = normalizeWorkId(workButton.getAttribute("data-popup-work-id"));
    if (!workId) return;
    addAnalyticsTagEditorWorkSelection(state, workId, true, interactionCallbacks(state));
  });

  state.refs.selectedWork.addEventListener("click", (event) => {
    const activateButton = event.target.closest("button[data-activate-work-id]");
    if (activateButton) {
      const workId = normalizeWorkId(activateButton.getAttribute("data-activate-work-id"));
      if (!workId) return;
      if (state.selectedWorkId === workId) {
        activateAnalyticsTagEditorSelectedWork(state, "", interactionCallbacks(state));
        return;
      }
      activateAnalyticsTagEditorSelectedWork(state, workId, interactionCallbacks(state));
      return;
    }
    const clearButton = event.target.closest("button[data-clear-selected-work]");
    if (!clearButton) return;
    const workId = normalizeWorkId(clearButton.getAttribute("data-clear-selected-work"));
    if (!workId) return;
    clearAnalyticsTagEditorSelectedWork(state, workId, interactionCallbacks(state));
  });

  state.refs.popupList.addEventListener("click", (event) => {
    const tagButton = event.target.closest("button[data-popup-tag-id]");
    if (tagButton) {
      const tagId = normalize(tagButton.getAttribute("data-popup-tag-id"));
      const tag = state.tagsById.get(tagId);
      if (!tag) return;
      addAnalyticsTagEditorResolvedTag(state, tag, { rawInput: tag.slug || tag.tag_id }, interactionCallbacks(state));
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
      addAnalyticsTagEditorResolvedTag(state, tag, {
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
      cycleAnalyticsTagEditorEntryWeight(state, entryId, interactionCallbacks(state));
      return;
    }

    const button = event.target.closest("button[data-remove-entry-id]");
    if (button) {
      const entryId = Number(button.getAttribute("data-remove-entry-id"));
      removeAnalyticsTagEditorEditableEntry(state, entryId, interactionCallbacks(state));
      renderAll(state);
    }
  });

  state.refs.saveButton.addEventListener("click", () => {
    void handleAnalyticsTagEditorSave(state, saveControllerCallbacks());
  });
}

function renderAll(state) {
  renderSelectedWork(state);
  renderContextHint(state);
  renderStatus(state);
  renderGroups(state);
  renderWorkPopup(state);
  renderPopup(state);
  applyAnalyticsTagEditorSaveState(state, interactionCallbacks(state));
  broadcastSelectedWorkChange(state);
  syncRouteBusyState(state);
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
    text: (key, fallback, tokens) => analyticsTagEditorText(state.config, key, fallback, tokens)
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

function analyticsTagEditorText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tag_editor.${key}`, fallback, tokens);
}
