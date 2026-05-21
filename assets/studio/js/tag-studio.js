import {
  getStudioGroups,
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import {
  loadSiteSeriesIndexJson,
  loadSiteWorksIndexJson,
  loadStudioAliasesJson,
  loadStudioAssignmentsJson,
  loadStudioRegistryJson
} from "./studio-data.js";
import {
  configureTagStudioDomain,
  makeResolvedEntry,
  nextWeight,
  normalize,
  normalizeAssignmentRows,
  normalizeWorkId,
  splitWorkInputTokens
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
  getOrderedSelectedWorkIds,
  restoreSelectionFromQuery,
  writeSelectionToQuery
} from "./tag-studio-state.js";
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
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  seriesTagEditorUi
} from "./studio-ui.js";

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
    config = await loadStudioConfigWithText("series_tag_editor");
  } catch (error) {
    renderFatalError(mount, "Failed to load tag editor config.");
    setStudioRouteReady(routeRoot, true, {
      ...buildTagStudioRouteStateDetail(null),
      mode: "empty"
    });
    return;
  }
  STUDIO_GROUPS = getStudioGroups(config);
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
      loadStudioRegistryJson(config),
      loadStudioAliasesJson(config),
      loadStudioAssignmentsJson(config),
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
        "Failed to load tag data. Check /assets/studio/data/tag_registry.json, /assets/studio/data/tag_aliases.json, /assets/studio/data/tag_assignments.json, /assets/data/series_index.json, and /assets/data/works_index.json."
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
  const reprobeSaveMode = () => {
    if (document.visibilityState === "hidden") return;
    void probeTagStudioSaveMode(state, saveControllerCallbacks());
  };

  window.addEventListener("focus", reprobeSaveMode);
  window.addEventListener("pageshow", reprobeSaveMode);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState !== "visible") return;
    reprobeSaveMode();
  });

  state.refs.workInput.addEventListener("input", () => {
    setStatus(state, "", "");
    renderStatus(state);
    renderWorkPopup(state);
  });

  state.refs.workInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      selectWorkFromInput(state);
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
      addFromInput(state);
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
    addFromInput(state);
  });

  state.refs.workPopupList.addEventListener("click", (event) => {
    const workButton = event.target.closest("button[data-popup-work-id]");
    if (!workButton) return;
    const workId = normalizeWorkId(workButton.getAttribute("data-popup-work-id"));
    if (!workId) return;
    addWorkSelection(state, workId, true);
  });

  state.refs.selectedWork.addEventListener("click", (event) => {
    const activateButton = event.target.closest("button[data-activate-work-id]");
    if (activateButton) {
      const workId = normalizeWorkId(activateButton.getAttribute("data-activate-work-id"));
      if (!workId) return;
      if (state.selectedWorkId === workId) {
        activateSelectedWork(state, "", true);
        return;
      }
      activateSelectedWork(state, workId);
      return;
    }
    const clearButton = event.target.closest("button[data-clear-selected-work]");
    if (!clearButton) return;
    const workId = normalizeWorkId(clearButton.getAttribute("data-clear-selected-work"));
    if (!workId) return;
    clearSelectedWork(state, workId);
  });

  state.refs.popupList.addEventListener("click", (event) => {
    const tagButton = event.target.closest("button[data-popup-tag-id]");
    if (tagButton) {
      const tagId = normalize(tagButton.getAttribute("data-popup-tag-id"));
      const tag = state.tagsById.get(tagId);
      if (!tag) return;
      addResolvedTag(state, tag, { rawInput: tag.slug || tag.tag_id });
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
      addResolvedTag(state, tag, {
        rawInput: aliasSource || tag.tag_id,
        alias: aliasSource
      });
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
      const entry = getEditableEntries(state).find((item) => item.entryId === entryId);
      if (!entry) return;
      entry.wManual = nextWeight(entry.wManual);
      setStatus(
        state,
        "success",
        studioText(
          state.config,
          "weight_updated",
          "Updated {tag_id} w_manual to {weight}.",
          {
            tag_id: entry.canonicalId,
            weight: entry.wManual.toFixed(1)
          }
        )
      );
      setSaveResult(state, "", "");
      renderAll(state);
      return;
    }

    const button = event.target.closest("button[data-remove-entry-id]");
    if (button) {
      const entryId = Number(button.getAttribute("data-remove-entry-id"));
      removeEditableEntry(state, entryId);
      renderAll(state);
      return;
    }

    const restoreButton = event.target.closest("button[data-restore-tag-id]");
    if (!restoreButton) return;
    restoreDeletedEntry(
      state,
      restoreButton.getAttribute("data-restore-tag-id"),
      restoreButton.getAttribute("data-restore-scope")
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

function selectWorkFromInput(state) {
  const rawInput = String(state.refs.workInput.value || "").trim();
  if (!rawInput) {
    setStatus(state, "warn", studioText(state.config, "work_input_required", "Enter a work_id from this series."));
    renderStatus(state);
    return;
  }

  const tokens = splitWorkInputTokens(rawInput);
  if (tokens.length > 1 || rawInput.includes(",")) {
    addWorksFromTokens(state, tokens);
    return;
  }

  const normalizedWorkId = normalizeWorkId(rawInput);
  const matches = getMatchingWorkOptions(state, rawInput);
  if (!matches.length) {
    setStatus(state, "error", studioText(
      state.config,
      "work_unknown_error",
      "Unknown work_id for this series: \"{input}\".",
      { input: rawInput }
    ));
    renderStatus(state);
    return;
  }

  const exact = normalizedWorkId ? matches.find((item) => item.workId === normalizedWorkId) : null;
  if (exact) {
    addWorkSelection(state, exact.workId, true);
    return;
  }

  if (matches.length === 1) {
    addWorkSelection(state, matches[0].workId, true);
    return;
  }

  setStatus(state, "warn", studioText(
    state.config,
    "work_multiple_matches",
    "Multiple works match \"{input}\". Choose one from the popup.",
    { input: rawInput }
  ));
  renderStatus(state);
  renderWorkPopup(state);
}

function addWorksFromTokens(state, tokens) {
  if (!tokens.length) {
    setStatus(state, "warn", studioText(state.config, "work_input_required_multiple", "Enter at least one work_id from this series."));
    renderStatus(state);
    return;
  }

  const added = [];
  const unknown = [];
  const invalid = [];

  for (const token of tokens) {
    const workId = normalizeWorkId(token);
    if (!workId) {
      invalid.push(token);
      continue;
    }
    if (!state.seriesWorkIds.has(workId)) {
      unknown.push(token);
      continue;
    }
    if (addWorkSelection(state, workId, false)) {
      added.push(workId);
    }
  }

  if (added.length) {
    activateSelectedWork(state, added[added.length - 1], false);
  }
  state.refs.workInput.value = "";
  hideWorkPopup(state);
  setSaveResult(state, "", "");

  const messageParts = buildWorkSelectionSummary(state, added, unknown, invalid);
  const kind = (unknown.length || invalid.length) ? (added.length ? "warn" : "error") : "success";
  setStatus(state, kind, messageParts.join(" "));
  renderAll(state);
}

function addWorkSelection(state, workId, activate = true) {
  if (!state.seriesWorkIds.has(workId)) {
    setStatus(state, "error", studioText(
      state.config,
      "work_not_in_series_error",
      "Work {work_id} is not in this series.",
      { work_id: workId }
    ));
    renderStatus(state);
    return false;
  }

  if (!state.selectedWorkIds.includes(workId)) {
    state.selectedWorkIds.push(workId);
  }
  if (!state.workEntriesById.has(workId)) {
    state.workEntriesById.set(workId, []);
  }
  if (activate) {
    activateSelectedWork(state, workId, false);
    setStatus(state, "success", studioText(
      state.config,
      "work_selected_success",
      "Selected work {work_id}.",
      { work_id: workId }
    ));
  }
  writeSelectionToQuery(state);
  state.refs.workInput.value = "";
  hideWorkPopup(state);
  setSaveResult(state, "", "");
  renderAll(state);
  return true;
}

function activateSelectedWork(state, workId, render = true) {
  if (workId && !state.selectedWorkIds.includes(workId)) return;
  state.selectedWorkId = workId;
  writeSelectionToQuery(state);
  if (render) renderAll(state);
}

function clearSelectedWork(state, workId) {
  state.selectedWorkIds = state.selectedWorkIds.filter((item) => item !== workId);
  state.workEntriesById.delete(workId);
  if (state.selectedWorkId === workId) {
    const remaining = getOrderedSelectedWorkIds(state);
    state.selectedWorkId = remaining.length ? remaining[0] : "";
  }
  if (!state.selectedWorkIds.length) {
    state.refs.workInput.value = "";
  }
  writeSelectionToQuery(state);
  hideWorkPopup(state);
  hidePopup(state);
  setStatus(state, "", "");
  setSaveResult(state, "", "");
  renderAll(state);
}

function addFromInput(state) {
  const rawInput = String(state.refs.input.value || "").trim();
  if (!rawInput) {
    setStatus(state, "warn", studioText(state.config, "tag_input_required", "Enter a tag slug, tag id, or alias."));
    renderStatus(state);
    return;
  }

  const resolved = resolveInput(rawInput, state);
  if (resolved.type === "resolved") {
    addResolvedTag(state, resolved.tag, { rawInput });
    state.refs.input.value = "";
    hidePopup(state);
    renderAll(state);
    return;
  }

  if (resolved.type === "ambiguous") {
    const candidateIds = resolved.candidates.map((tag) => tag.tag_id).slice(0, 6);
    const suffix = resolved.candidates.length > 6 ? ", ..." : "";
    setStatus(state, "warn", studioText(
      state.config,
      "tag_multiple_matches",
      "Multiple matches for \"{input}\": {candidate_ids}{suffix}. Choose one from autocomplete.",
      {
        input: rawInput,
        candidate_ids: candidateIds.join(", "),
        suffix
      }
    ));
    renderStatus(state);
    return;
  }

  setStatus(state, "error", studioText(
    state.config,
    "tag_unknown_error",
    "Unknown tag: \"{input}\".",
    { input: rawInput }
  ));
  renderStatus(state);
}

function resolveInput(rawInput, state) {
  const raw = String(rawInput || "").trim();
  if (!raw) return { type: "empty" };

  const normalized = normalize(raw);
  if (normalized.includes(":")) {
    const canonical = state.tagsById.get(normalized);
    if (canonical) return { type: "resolved", tag: canonical };
    return { type: "unresolved" };
  }

  const aliasTagIds = state.aliases.get(normalized);
  if (Array.isArray(aliasTagIds) && aliasTagIds.length) {
    const aliasCandidates = [];
    const seenAlias = new Set();
    for (const aliasTagId of aliasTagIds) {
      const normalizedAliasTagId = normalize(aliasTagId);
      if (!normalizedAliasTagId || seenAlias.has(normalizedAliasTagId)) continue;
      seenAlias.add(normalizedAliasTagId);
      const aliasTag = state.tagsById.get(normalizedAliasTagId);
      if (aliasTag) aliasCandidates.push(aliasTag);
    }
    if (aliasCandidates.length === 1) return { type: "resolved", tag: aliasCandidates[0] };
    if (aliasCandidates.length > 1) {
      aliasCandidates.sort((a, b) => a.tag_id.localeCompare(b.tag_id));
      return { type: "ambiguous", candidates: aliasCandidates };
    }
  }

  const candidates = [];
  const seen = new Set();

  for (const list of [state.slugMap.get(normalized), state.labelMap.get(normalized)]) {
    if (!Array.isArray(list)) continue;
    for (const tag of list) {
      if (!tag || !tag.tag_id || seen.has(tag.tag_id)) continue;
      seen.add(tag.tag_id);
      candidates.push(tag);
    }
  }

  if (candidates.length === 1) return { type: "resolved", tag: candidates[0] };
  if (candidates.length > 1) {
    candidates.sort((a, b) => a.tag_id.localeCompare(b.tag_id));
    return { type: "ambiguous", candidates };
  }
  return { type: "unresolved" };
}

function addResolvedTag(state, tag, options = {}) {
  if (!tag || !tag.tag_id) return;
  const rawInput = typeof options === "string"
    ? options
    : String(options.rawInput || "").trim();
  const alias = typeof options === "object" && options
    ? normalize(options.alias)
    : "";

  const tagId = normalize(tag.tag_id);
  const isSeriesScope = !state.selectedWorkId;
  const inheritedTagIds = getSeriesTagIdSet(state);
  if (!isSeriesScope && inheritedTagIds.has(tagId)) {
    setStatus(state, "warn", studioText(
      state.config,
      "tag_inherited_warning",
      "Inherited from series already: {tag_id}.",
      { tag_id: tagId }
    ));
    return;
  }

  const entries = getEditableEntries(state);
  const alreadyExists = entries.some((entry) => entry.canonicalId === tagId);
  if (alreadyExists) {
    setStatus(state, "warn", studioText(
      state.config,
      isSeriesScope ? "tag_already_added_warning_series" : "tag_already_added_warning",
      isSeriesScope ? "Already added to series: {tag_id}." : "Already added for {work_id}: {tag_id}.",
      isSeriesScope ? { tag_id: tagId } : {
        work_id: state.selectedWorkId,
        tag_id: tagId
      }
    ));
    return;
  }

  entries.push(makeResolvedEntry(nextEntryId(state), rawInput, tag, DEFAULT_WEIGHT, alias));
  setStatus(state, "success", studioText(
    state.config,
    isSeriesScope ? "series_tag_added_success" : "tag_added_success",
    isSeriesScope ? "Added {tag_id} to series tags." : "Added {tag_id} to {work_id}.",
    isSeriesScope ? { tag_id: tagId } : {
      work_id: state.selectedWorkId,
      tag_id: tagId
    }
  ));
  setSaveResult(state, "", "");
}

function nextEntryId(state) {
  let maxId = 0;
  for (const entry of state.seriesEntries) {
    if (entry.entryId > maxId) maxId = entry.entryId;
  }
  for (const entries of state.workEntriesById.values()) {
    for (const entry of entries) {
      if (entry.entryId > maxId) maxId = entry.entryId;
    }
  }
  return maxId + 1;
}

function removeEditableEntry(state, entryId) {
  const entries = getEditableEntries(state);
  const sizeBefore = entries.length;
  const nextEntries = entries.filter((entry) => entry.entryId !== entryId);
  if (state.selectedWorkId) {
    state.workEntriesById.set(state.selectedWorkId, nextEntries);
  } else {
    state.seriesEntries = nextEntries;
  }
  if (nextEntries.length < sizeBefore) {
    setStatus(
      state,
      "success",
      studioText(
        state.config,
        state.selectedWorkId ? "work_tag_removed" : "series_tag_removed",
        state.selectedWorkId ? "Work tag removed." : "Series tag removed."
      )
    );
    setSaveResult(state, "", "");
  }
}

function restoreDeletedEntry(state, rawTagId, rawScope) {
  const tagId = normalize(rawTagId);
  const scope = String(rawScope || "").trim().toLowerCase();
  if (!tagId) return;

  const tag = state.tagsById.get(tagId);
  if (!tag) return;

  if (scope === "work") {
    if (!state.selectedWorkId) return;
    if (getSeriesTagIdSet(state).has(tagId)) {
      setStatus(
        state,
        "warn",
        studioText(
          state.config,
          "work_tag_restore_inherited_warning",
          "Cannot restore {tag_id} while it is inherited from the series.",
          { tag_id: tagId }
        )
      );
      setSaveResult(state, "", "");
      return;
    }

    const entries = getSelectedWorkEntries(state);
    if (entries.some((entry) => entry.canonicalId === tagId)) return;
    const baseRow = getOfflineBaseWorkRows(state, state.selectedWorkId).find((row) => row.tag_id === tagId);
    if (!baseRow) return;
    entries.push(makeResolvedEntry(nextEntryId(state), tagId, tag, baseRow.w_manual, baseRow.alias));
    setStatus(
      state,
      "success",
      studioText(state.config, "work_tag_restored", "Work tag restored.")
    );
    setSaveResult(state, "", "");
    return;
  }

  if (state.seriesEntries.some((entry) => entry.canonicalId === tagId)) return;
  const baseRow = normalizeAssignmentRows(state.offlineBaseSeriesRow && state.offlineBaseSeriesRow.tags)
    .find((row) => row.tag_id === tagId);
  if (!baseRow) return;
  state.seriesEntries.push(makeResolvedEntry(nextEntryId(state), tagId, tag, baseRow.w_manual, baseRow.alias));
  setStatus(
    state,
    "success",
    studioText(state.config, "series_tag_restored", "Series tag restored.")
  );
  setSaveResult(state, "", "");
}

function renderAll(state) {
  renderSelectedWork(state);
  renderContextHint(state);
  renderStatus(state);
  renderGroups(state);
  renderWorkPopup(state);
  renderPopup(state);
  renderTagStudioSaveMode(state);
  renderSaveState(state);
  broadcastSelectedWorkChange(state);
  syncTagStudioOfflineAutosave(state, saveControllerCallbacks());
  syncRouteBusyState(state);
}

function getEditableEntries(state) {
  if (!state.selectedWorkId) return state.seriesEntries;
  return getSelectedWorkEntries(state);
}

function getSeriesTagIdSet(state) {
  const out = new Set();
  for (const entry of state.seriesEntries) {
    out.add(entry.canonicalId);
  }
  return out;
}

function renderSaveState(state) {
  const metrics = computeMetrics(state);
  const hasSelectedWork = Boolean(state.selectedWorkId);
  const diff = buildStateDiff(state);
  const isDirty = diff.seriesChanged || diff.changedWorkIds.length > 0;
  state.refs.input.disabled = false;
  state.refs.addButton.disabled = false;
  state.refs.saveButton.disabled = !isDirty || metrics.unresolvedCount > 0;

  if (!hasSelectedWork && isDirty) {
    state.refs.saveWarning.textContent = studioText(
      state.config,
      "save_warning_pending_diff",
      "Save to persist the current tag assignment diff."
    );
    return;
  }
  state.refs.saveWarning.textContent = metrics.unresolvedCount > 0
    ? studioText(state.config, "save_warning_unresolved", "Resolve unknown tags before saving.")
    : "";
}

function computeMetrics(state) {
  return { unresolvedCount: 0 };
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

function saveControllerCallbacks() {
  return {
    renderAll,
    renderStatus,
    setSaveResult,
    syncRouteBusyState
  };
}

function getSelectedWorkEntries(state) {
  if (!state.selectedWorkId) return [];
  return state.workEntriesById.get(state.selectedWorkId) || [];
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

function buildWorkSelectionSummary(state, added, unknown, invalid) {
  const parts = [];
  if (added.length) {
    parts.push(studioText(
      state.config,
      "work_summary_added",
      "Added {count} work{plural}.",
      {
        count: added.length,
        plural: added.length === 1 ? "" : "s"
      }
    ));
  }
  if (unknown.length) {
    parts.push(studioText(
      state.config,
      "work_summary_not_in_series",
      "Not in this series: {list}.",
      { list: unknown.join(", ") }
    ));
  }
  if (invalid.length) {
    parts.push(studioText(
      state.config,
      "work_summary_invalid",
      "Invalid work_id: {list}.",
      { list: invalid.join(", ") }
    ));
  }
  return parts;
}

function studioText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tag_editor.${key}`, fallback, tokens);
}
