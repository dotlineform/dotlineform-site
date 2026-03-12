import {
  getStudioGroups,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  loadSiteSeriesIndexJson,
  loadSiteWorksIndexJson,
  loadStudioAliasesJson,
  loadStudioAssignmentsJson,
  loadStudioRegistryJson
} from "./studio-data.js";
import {
  probeStudioHealth
} from "./studio-transport.js";
import {
  buildSeriesWorkOptions,
  cloneWorkStateMap,
  compareEntries,
  compareTagDisplay,
  configureTagStudioDomain,
  createResolvedEntries,
  buildEditorStateDiff,
  getSeriesAssignment,
  getSeriesIndexRow,
  makeResolvedEntry,
  nextWeight,
  normalize,
  normalizeAliasTargets,
  normalizeAssignmentRows,
  normalizeAssignmentTags,
  normalizeManualWeight,
  normalizeWorkId,
  pushMapList,
  sanitizeTag,
  splitWorkInputTokens,
  workStateMapToObject
} from "./tag-studio-domain.js";
import {
  equalOfflineSeriesRows,
  getOfflineAssignmentsSeriesEntry,
  normalizeOfflineSeriesRow,
  readOfflineAssignmentsSession,
  removeOfflineAssignmentsSeriesEntry,
  upsertOfflineAssignmentsSeriesEntry,
  writeOfflineAssignmentsSession
} from "./tag-assignments-offline.js";
import {
  buildPatchSnippet,
  buildSaveModeText as buildTagStudioSaveModeText,
  buildTagSaveSuccessMessage,
  postTags,
  utcTimestamp
} from "./tag-studio-save.js";
import {
  renderStudioModalActions,
  renderStudioModalFrame
} from "./studio-modal.js";
import {
  seriesTagEditorUi
} from "./studio-ui.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const POPUP_TAG_MATCH_CAP = 12;
const POPUP_ALIAS_MATCH_CAP = 12;
const POPUP_WORK_MATCH_CAP = 12;
const WEIGHT_VALUES = [0.3, 0.6, 0.9];
const DEFAULT_WEIGHT = 0.6;
const UI = seriesTagEditorUi;
const { className: UI_CLASS, selector: UI_SELECTOR, state: UI_STATE } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagStudio);
} else {
  initTagStudio();
}

async function initTagStudio() {
  const mount = document.getElementById("tag-studio");
  if (!mount) return;

  const config = await loadStudioConfig();
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
    const offlineSession = readOfflineAssignmentsSession();

    const state = buildState(
      mount,
      seriesId,
      registryJson,
      aliasesJson,
      assignmentsJson,
      seriesIndexJson,
      worksIndexJson,
      config,
      offlineSession
    );
    restoreSelectionFromQuery(state);
    renderShell(state);
    if (!state.refs) return;
    wireEvents(state);
    renderAll(state);
    void probeSaveMode(state);
  } catch (error) {
    renderFatalError(
      mount,
      studioText(
        config,
        "load_failed_error",
        "Failed to load tag data. Check /assets/studio/data/tag_registry.json, /assets/studio/data/tag_aliases.json, /assets/studio/data/tag_assignments.json, /assets/data/series_index.json, and /assets/data/works_index.json."
      )
    );
  }
}

function buildState(mount, seriesId, registryJson, aliasesJson, assignmentsJson, seriesIndexJson, worksIndexJson, config, offlineSession) {
  const tags = Array.isArray(registryJson && registryJson.tags) ? registryJson.tags : [];
  const tagsById = new Map();
  const slugMap = new Map();
  const labelMap = new Map();
  const activeTags = [];

  for (const rawTag of tags) {
    const tag = sanitizeTag(rawTag);
    if (!tag) continue;

    tagsById.set(tag.tag_id, tag);
    pushMapList(slugMap, tag.slug, tag);
    pushMapList(labelMap, normalize(tag.label), tag);

    if (tag.status === "active") {
      activeTags.push(tag);
    }
  }

  activeTags.sort((a, b) => a.tag_id.localeCompare(b.tag_id));
  const activeTagsBySlug = activeTags.slice().sort((a, b) => {
    const bySlug = a.slug.localeCompare(b.slug, undefined, { sensitivity: "base" });
    if (bySlug !== 0) return bySlug;
    return a.tag_id.localeCompare(b.tag_id);
  });

  const aliases = new Map();
  const rawAliases = aliasesJson && typeof aliasesJson.aliases === "object" ? aliasesJson.aliases : {};
  for (const [aliasInput, targetInput] of Object.entries(rawAliases)) {
    const aliasKey = normalize(aliasInput);
    if (!aliasKey) continue;
    const targetTagIds = normalizeAliasTargets(targetInput);
    if (!targetTagIds.length) continue;
    aliases.set(aliasKey, targetTagIds);
  }
  const aliasOptions = buildAliasOptions(aliases, tagsById);

  const seriesIndexMap = seriesIndexJson && typeof seriesIndexJson.series === "object" ? seriesIndexJson.series : {};
  const worksIndexMap = worksIndexJson && typeof worksIndexJson.works === "object" ? worksIndexJson.works : {};
  const seriesRow = getSeriesIndexRow(seriesIndexMap, seriesId);
  const seriesWorkOptions = buildSeriesWorkOptions(seriesId, seriesRow, worksIndexMap);
  const seriesWorkIds = new Set(seriesWorkOptions.map((item) => item.workId));

  const assignmentsSeries = assignmentsJson && typeof assignmentsJson.series === "object" ? assignmentsJson.series : {};
  const repoSeriesAssignment = getSeriesAssignment(assignmentsSeries, seriesId);
  const offlineSeriesEntry = getOfflineAssignmentsSeriesEntry(offlineSession, seriesId);
  const seriesAssignment = offlineSeriesEntry ? offlineSeriesEntry.staged_row : repoSeriesAssignment;
  const seriesEntries = createResolvedEntries(
    normalizeAssignmentTags(seriesAssignment && seriesAssignment.tags),
    tagsById
  ).entries;

  const rawWorkAssignments = seriesAssignment && typeof seriesAssignment.works === "object" ? seriesAssignment.works : {};
  const workEntriesById = new Map();
  const selectedWorkIds = [];
  const baselineWorkStateById = new Map();
  let nextEntryId = 1;

  Object.keys(rawWorkAssignments).forEach((rawWorkId) => {
    const workId = normalizeWorkId(rawWorkId);
    if (!workId) return;
    const workRow = rawWorkAssignments[rawWorkId];
    const tags = workRow && typeof workRow === "object" ? workRow.tags : [];
    const rows = normalizeAssignmentTags(tags);
    const entries = createResolvedEntries(rows, tagsById, nextEntryId);
    workEntriesById.set(workId, entries.entries);
    baselineWorkStateById.set(workId, normalizeAssignmentRows(rows));
    if (seriesWorkIds.has(workId)) {
      selectedWorkIds.push(workId);
    }
    nextEntryId = entries.nextEntryId;
  });

  return {
    mount,
    config,
    seriesId,
    tagsById,
    slugMap,
    labelMap,
    aliases,
    activeTagsBySlug,
    aliasOptions,
    seriesEntries,
    baselineSeriesRows: normalizeAssignmentRows(seriesAssignment && seriesAssignment.tags),
    workEntriesById,
    seriesWorkOptions,
    seriesWorkIds,
    selectedWorkIds,
    baselineWorkStateById,
    selectedWorkId: "",
    lastBroadcastSelectedWorkId: null,
    statusText: "",
    statusKind: "",
    refs: null,
    offlineSession,
    hasOfflineStagedSeries: Boolean(offlineSeriesEntry),
    offlineBaseSeriesRow: offlineSeriesEntry && offlineSeriesEntry.base_row_snapshot
      ? normalizeOfflineSeriesRow(offlineSeriesEntry.base_row_snapshot)
      : normalizeOfflineSeriesRow(repoSeriesAssignment),
    offlineBaseSeriesUpdatedAt: offlineSeriesEntry
      ? String(offlineSeriesEntry.base_series_updated_at_utc || "")
      : String(repoSeriesAssignment && repoSeriesAssignment.updated_at_utc || ""),
    offlineAutosaveTimer: 0,
    modalSnippet: "",
    saveMode: "offline",
    saveModeResolved: false
  };
}

function buildStateDiff(state) {
  return buildEditorStateDiff(state, getOrderedSelectedWorkIds(state));
}

function buildPersistedSeriesRow(diff) {
  const row = {
    tags: normalizeAssignmentRows(diff && diff.nextSeriesRows)
  };
  const works = {};
  const nextWorkStateById = diff && diff.nextWorkStateById instanceof Map ? diff.nextWorkStateById : new Map();

  for (const [workId, tags] of Array.from(nextWorkStateById.entries()).sort((a, b) => a[0].localeCompare(b[0]))) {
    works[workId] = {
      tags: normalizeAssignmentRows(tags)
    };
  }

  if (Object.keys(works).length) row.works = works;
  return row;
}

function applyPersistedBaseline(state, diff) {
  state.baselineSeriesRows = normalizeAssignmentRows(diff.nextSeriesRows);
  state.baselineWorkStateById = cloneWorkStateMap(diff.nextWorkStateById);
}

function restoreSelectionFromQuery(state) {
  const searchParams = new URLSearchParams(window.location.search);
  const worksParam = String(searchParams.get("works") || "").trim();
  if (!worksParam) {
    writeSelectionToQuery(state);
    return;
  }

  const selectedWorkIds = [];
  const seen = new Set();
  for (const rawPart of worksParam.split(",")) {
    const workId = normalizeWorkId(rawPart);
    if (!workId || seen.has(workId) || !state.seriesWorkIds.has(workId)) continue;
    seen.add(workId);
    selectedWorkIds.push(workId);
    if (!state.workEntriesById.has(workId)) {
      state.workEntriesById.set(workId, []);
    }
  }

  state.selectedWorkIds = selectedWorkIds;

  const activeWorkId = normalizeWorkId(searchParams.get("active"));
  if (activeWorkId && selectedWorkIds.includes(activeWorkId)) {
    state.selectedWorkId = activeWorkId;
  } else {
    state.selectedWorkId = selectedWorkIds.length ? selectedWorkIds[0] : "";
  }

  writeSelectionToQuery(state);
}

function writeSelectionToQuery(state) {
  if (!window.history || typeof window.history.replaceState !== "function") return;

  const url = new URL(window.location.href);
  const selectedWorkIds = getOrderedSelectedWorkIds(state);
  if (selectedWorkIds.length) {
    url.searchParams.set("works", selectedWorkIds.join(","));
    if (state.selectedWorkId && selectedWorkIds.includes(state.selectedWorkId)) {
      url.searchParams.set("active", state.selectedWorkId);
    } else {
      url.searchParams.delete("active");
    }
  } else {
    url.searchParams.delete("works");
    url.searchParams.delete("active");
  }

  window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
}

function renderShell(state) {
  const workInputPlaceholder = studioText(state.config, "work_input_placeholder", "work_id(s) in this series");
  const tagInputPlaceholder = studioText(state.config, "tag_input_placeholder", "tag slug or alias");
  const addButtonLabel = studioText(state.config, "add_button", "Add");
  const saveButtonLabel = studioText(state.config, "save_button", "Save Tags");
  const saveModeLabel = buildTagStudioSaveModeText(state.config, "offline", studioText);
  const modalTitle = studioText(state.config, "modal_title", "Tag Assignment Patch Preview");
  const modalResolvedLabel = studioText(state.config, "modal_resolved_label", "Resolved tag assignment payload");
  const modalPatchGuidanceLabel = studioText(state.config, "modal_patch_guidance_label", "Patch guidance for tag_assignments.json");
  const modalCopyButton = studioText(state.config, "modal_copy_button", "Copy");
  const modalCloseButton = studioText(state.config, "modal_close_button", "Close");
  const saveModalHtml = renderStudioModalFrame({
    modalRole: UI.role.modal,
    backdropRole: UI.role.modalClose,
    titleId: "tagStudioModalTitle",
    title: modalTitle,
    bodyHtml: `
      <p class="${UI_CLASS.modalLabel}">${escapeHtml(modalResolvedLabel)}</p>
      <pre class="${UI_CLASS.modalPre}" data-role="${UI.role.modalTags}"></pre>
      <p class="${UI_CLASS.modalLabel}">${escapeHtml(modalPatchGuidanceLabel)}</p>
      <pre class="${UI_CLASS.modalPre}" data-role="${UI.role.modalSnippet}"></pre>
    `,
    actionsHtml: renderStudioModalActions([
      { role: UI.role.copySnippet, label: modalCopyButton, primary: true },
      { role: UI.role.modalClose, label: modalCloseButton }
    ])
  });
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
  refs.modalHost.innerHTML = saveModalHtml;

  state.refs = {
    ...refs,
    modal: state.mount.querySelector(UI_SELECTOR.modal),
    modalTags: state.mount.querySelector(UI_SELECTOR.modalTags),
    modalSnippet: state.mount.querySelector(UI_SELECTOR.modalSnippet),
    copyButton: state.mount.querySelector(UI_SELECTOR.copySnippet)
  };
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
    void handleSave(state);
  });

  state.refs.modal.addEventListener("click", (event) => {
    if (!event.target.closest(UI_SELECTOR.modalClose)) return;
    closeModal(state);
  });

  state.refs.copyButton.addEventListener("click", async () => {
    if (!state.modalSnippet) return;
    try {
      await navigator.clipboard.writeText(state.modalSnippet);
      setStatus(state, "success", studioText(state.config, "save_status_copy", "Patch guidance copied to clipboard."));
    } catch (error) {
      setStatus(state, "error", studioText(state.config, "save_status_copy_failed", "Copy failed. Select and copy the patch guidance manually."));
    }
    renderStatus(state);
  });
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
  renderSaveMode(state);
  renderSaveState(state);
  broadcastSelectedWorkChange(state);
  syncOfflineAutosave(state);
}

function syncOfflineAutosave(state) {
  if (!state.saveModeResolved || state.saveMode !== "offline") {
    clearOfflineAutosave(state);
    return;
  }

  const diff = buildStateDiff(state);
  if (!diff.seriesChanged && !diff.changedWorkIds.length) {
    clearOfflineAutosave(state);
    return;
  }

  if (state.offlineAutosaveTimer) {
    window.clearTimeout(state.offlineAutosaveTimer);
  }

  state.offlineAutosaveTimer = window.setTimeout(() => {
    state.offlineAutosaveTimer = 0;
    stageOfflineState(state, { manual: false });
  }, 700);
}

function clearOfflineAutosave(state) {
  if (!state.offlineAutosaveTimer) return;
  window.clearTimeout(state.offlineAutosaveTimer);
  state.offlineAutosaveTimer = 0;
}

function renderSelectedWork(state) {
  const selected = getOrderedSelectedWorkOptions(state);
  if (!selected.length) {
    state.refs.selectedWork.innerHTML = "";
    return;
  }
  state.refs.selectedWork.innerHTML = selected.map((item) => {
    const titleText = item.title ? ` ${escapeHtml(item.title)}` : "";
    const activeState = item.workId === state.selectedWorkId ? ` data-state="${UI_STATE.active}"` : "";
    return `
      <span class="${UI_CLASS.selectedWorkPill}"${activeState} title="${escapeHtml(item.workId)}${titleText}">
        <button type="button" class="${UI_CLASS.selectedWorkButton}" data-activate-work-id="${escapeHtml(item.workId)}" aria-pressed="${item.workId === state.selectedWorkId ? "true" : "false"}">
          <span class="${UI_CLASS.selectedWorkId}">${escapeHtml(item.workId)}</span>
        </button>
        <button
          type="button"
          class="${UI_CLASS.chipRemove}"
          data-clear-selected-work="${escapeHtml(item.workId)}"
          aria-label="${escapeHtml(studioText(state.config, "remove_selected_work_aria_label", "Remove selected work {work_id}", { work_id: item.workId }))}"
        >x</button>
      </span>
    `;
  }).join("");
}

function renderContextHint(state) {
  if (!state.refs.contextHint) return;
  if (!state.selectedWorkId) {
    state.refs.contextHint.textContent = studioText(
      state.config,
      "context_hint_default",
      "No work selected: edit series tags directly. Select a work to switch to work-only overrides."
    );
    return;
  }
  state.refs.contextHint.textContent = studioText(
    state.config,
    "context_hint_selected",
    "Monochrome pills are inherited from the series. Colored pills are saved as work-only overrides."
  );
}

function renderWorkPopup(state) {
  const queryRaw = String(state.refs.workInput.value || "").trim();
  if (!queryRaw) {
    hideWorkPopup(state);
    return;
  }

  const matches = getMatchingWorkOptions(state, queryRaw).slice(0, POPUP_WORK_MATCH_CAP);
  if (!matches.length) {
    hideWorkPopup(state);
    return;
  }

  state.refs.workPopupList.innerHTML = `
    <div class="${UI_CLASS.suggest}">
      <section class="${UI_CLASS.suggestSection}">
        <p class="${UI_CLASS.suggestHeading}">${escapeHtml(studioText(state.config, "popup_heading_works", "works"))}</p>
        <div class="${UI_CLASS.suggestWorkRows}">
          ${matches.map((item) => `
            <button type="button" class="${UI_CLASS.suggestWorkButton}" data-popup-work-id="${escapeHtml(item.workId)}">
              <span class="${UI_CLASS.suggestWorkId}">${escapeHtml(item.workId)}</span>
              <span class="${UI_CLASS.suggestWorkTitle}">${escapeHtml(item.title || "")}</span>
            </button>
          `).join("")}
        </div>
      </section>
    </div>
  `;
  state.refs.workPopup.hidden = false;
}

function hideWorkPopup(state) {
  state.refs.workPopup.hidden = true;
  state.refs.workPopupList.innerHTML = "";
}

function getMatchingWorkOptions(state, query) {
  const normalizedQuery = normalize(query);
  if (!normalizedQuery) return [];
  return state.seriesWorkOptions.filter((item) => {
    if (item.workId.startsWith(normalizedQuery)) return true;
    if (item.shortWorkId.startsWith(normalizedQuery)) return true;
    return item.titleKey.startsWith(normalizedQuery);
  });
}

function renderPopup(state) {
  const query = normalize(state.refs.input.value);
  if (!query) {
    hidePopup(state);
    return;
  }

  const selectedTagIds = getEditableTagIdSet(state);
  const inheritedTagIds = getSeriesTagIdSet(state);
  const tagMatches = state.activeTagsBySlug
    .filter((tag) => {
      if (!tag.slug.startsWith(query)) return false;
      if (selectedTagIds.has(tag.tag_id)) return false;
      if (state.selectedWorkId && inheritedTagIds.has(tag.tag_id)) return false;
      return true;
    })
    .slice(0, POPUP_TAG_MATCH_CAP);
  const aliasMatches = getPopupAliasMatches(state, query, selectedTagIds, state.selectedWorkId ? inheritedTagIds : new Set()).slice(0, POPUP_ALIAS_MATCH_CAP);

  if (!tagMatches.length && !aliasMatches.length) {
    hidePopup(state);
    return;
  }

  const tagSection = tagMatches.length
    ? `
      <section class="${UI_CLASS.suggestSection}">
        <p class="${UI_CLASS.suggestHeading}">${escapeHtml(studioText(state.config, "popup_heading_tags", "tags"))}</p>
        <div class="${UI_CLASS.suggestTagRows}">
          ${tagMatches.map((tag) => `
            <button
              type="button"
              class="${classNames(UI_CLASS.popupPill, chipGroupClass(tag.group))}"
              data-popup-tag-id="${escapeHtml(tag.tag_id)}"
              title="${escapeHtml(tag.tag_id)}"
            >
              ${escapeHtml(tag.label)}
            </button>
          `).join("")}
        </div>
      </section>
    `
    : "";

  const aliasSection = aliasMatches.length
    ? `
      <section class="${UI_CLASS.suggestSection}">
        <p class="${UI_CLASS.suggestHeading}">${escapeHtml(studioText(state.config, "popup_heading_aliases", "aliases"))}</p>
        <div class="${UI_CLASS.suggestAliasRows}">
          ${aliasMatches.map((entry) => `
            <div class="${UI_CLASS.suggestAliasRow}">
              <span
                class="${classNames(UI_CLASS.popupPill, UI_CLASS.suggestAliasPill)}"
                data-popup-alias="${escapeHtml(entry.alias)}"
                title="${escapeHtml(entry.alias)}"
              >
                ${escapeHtml(entry.alias)}
              </span>
              <div class="${UI_CLASS.suggestAliasTargets}">
                ${entry.targets.map((target) => `
                  <button
                    type="button"
                    class="${classNames(UI_CLASS.popupPill, chipGroupClass(target.group), UI_CLASS.suggestAliasTarget)}"
                    data-popup-alias-target="${escapeHtml(target.tagId)}"
                    data-popup-alias-source="${escapeHtml(entry.alias)}"
                    title="${escapeHtml(target.tagId)}"
                  >
                    ${escapeHtml(target.label)}
                  </button>
                `).join("")}
              </div>
            </div>
          `).join("")}
        </div>
      </section>
    `
    : "";

  state.refs.popupList.innerHTML = `
    <div class="${UI_CLASS.suggest}">
      ${tagSection}
      ${aliasSection}
    </div>
  `;
  state.refs.popup.hidden = false;
}

function hidePopup(state) {
  state.refs.popup.hidden = true;
  state.refs.popupList.innerHTML = "";
}

function getPopupAliasMatches(state, query, selectedTagIds, inheritedTagIds) {
  return state.aliasOptions
    .filter((entry) => entry.alias.startsWith(query))
    .map((entry) => ({
      alias: entry.alias,
      targets: entry.targets.filter((target) => !selectedTagIds.has(target.tagId) && !inheritedTagIds.has(target.tagId))
    }))
    .filter((entry) => entry.targets.length > 0);
}

function getEditableEntries(state) {
  if (!state.selectedWorkId) return state.seriesEntries;
  return getSelectedWorkEntries(state);
}

function getEditableTagIdSet(state) {
  const out = new Set();
  for (const entry of getEditableEntries(state)) {
    out.add(entry.canonicalId);
  }
  return out;
}

function getSeriesTagIdSet(state) {
  const out = new Set();
  for (const entry of state.seriesEntries) {
    out.add(entry.canonicalId);
  }
  return out;
}

function buildAliasOptions(aliases, tagsById) {
  const out = [];
  for (const [alias, targets] of aliases.entries()) {
    const resolved = [];
    const seen = new Set();
    for (const targetTagId of targets) {
      const normalizedTagId = normalize(targetTagId);
      if (!normalizedTagId || seen.has(normalizedTagId)) continue;
      const tag = tagsById.get(normalizedTagId);
      if (!tag) continue;
      seen.add(normalizedTagId);
      resolved.push({
        tagId: normalizedTagId,
        group: tag.group,
        label: tag.label
      });
    }
    if (!resolved.length) continue;
    resolved.sort(compareTagDisplay);
    out.push({ alias, targets: resolved });
  }
  out.sort((a, b) => a.alias.localeCompare(b.alias, undefined, { sensitivity: "base" }));
  return out;
}

function createEmptyMarkerState() {
  return {
    current: new Map(),
    deleted: []
  };
}

function getOfflineBaseWorkRows(state, workId) {
  const normalizedWorkId = normalizeWorkId(workId);
  const works = state.offlineBaseSeriesRow && state.offlineBaseSeriesRow.works && typeof state.offlineBaseSeriesRow.works === "object"
    ? state.offlineBaseSeriesRow.works
    : {};
  const row = normalizedWorkId && works[normalizedWorkId] && typeof works[normalizedWorkId] === "object"
    ? works[normalizedWorkId]
    : null;
  return normalizeAssignmentRows(row && row.tags);
}

function buildEntryRow(entry) {
  if (!entry || !entry.canonicalId) return null;
  const row = {
    tag_id: normalize(entry.canonicalId),
    w_manual: normalizeManualWeight(entry.wManual, DEFAULT_WEIGHT)
  };
  if (entry.alias) row.alias = normalize(entry.alias);
  return row;
}

function equalAssignmentTagRow(left, right) {
  if (!left || !right) return false;
  return left.tag_id === right.tag_id
    && left.w_manual === right.w_manual
    && String(left.alias || "") === String(right.alias || "");
}

function makeHistoricalEntry(state, row, entryId) {
  if (!row || !row.tag_id) return null;
  const tag = state.tagsById.get(normalize(row.tag_id));
  if (!tag) return null;
  return makeResolvedEntry(entryId, row.tag_id, tag, row.w_manual, row.alias);
}

function buildEntryMarkerState(state, entries, baseRows, scopeKey) {
  const current = new Map();
  const deleted = [];
  const normalizedBaseRows = normalizeAssignmentRows(baseRows);
  const baseByTagId = new Map(normalizedBaseRows.map((row) => [row.tag_id, row]));
  const currentTagIds = new Set();

  for (const entry of Array.isArray(entries) ? entries : []) {
    const currentRow = buildEntryRow(entry);
    if (!currentRow) continue;
    currentTagIds.add(currentRow.tag_id);
    const baseRow = baseByTagId.get(currentRow.tag_id) || null;
    if (!baseRow || !equalAssignmentTagRow(baseRow, currentRow)) {
      current.set(currentRow.tag_id, "local");
    }
  }

  for (const row of normalizedBaseRows) {
    if (currentTagIds.has(row.tag_id)) continue;
    const deletedEntry = makeHistoricalEntry(state, row, `${scopeKey}:${row.tag_id}`);
    if (deletedEntry) deleted.push(deletedEntry);
  }
  deleted.sort(compareEntries);

  return { current, deleted };
}

function renderGroups(state) {
  const inheritedByGroup = new Map(STUDIO_GROUPS.map((group) => [group, []]));
  for (const entry of state.seriesEntries) {
    if (!inheritedByGroup.has(entry.group)) continue;
    inheritedByGroup.get(entry.group).push(entry);
  }
  const showOfflineMarkers = state.saveMode !== "post";
  const seriesMarkerState = showOfflineMarkers
    ? buildEntryMarkerState(state, state.seriesEntries, state.offlineBaseSeriesRow && state.offlineBaseSeriesRow.tags, "series")
    : createEmptyMarkerState();
  const inheritedDeletedByGroup = new Map(STUDIO_GROUPS.map((group) => [group, []]));
  for (const entry of seriesMarkerState.deleted) {
    if (!inheritedDeletedByGroup.has(entry.group)) continue;
    inheritedDeletedByGroup.get(entry.group).push(entry);
  }

  const overrideByGroup = new Map(STUDIO_GROUPS.map((group) => [group, []]));
  for (const entry of getSelectedWorkEntries(state)) {
    if (!overrideByGroup.has(entry.group)) continue;
    overrideByGroup.get(entry.group).push(entry);
  }
  const selectedWorkId = state.selectedWorkId;
  const overrideMarkerState = showOfflineMarkers && selectedWorkId
    ? buildEntryMarkerState(state, getSelectedWorkEntries(state), getOfflineBaseWorkRows(state, selectedWorkId), `work:${selectedWorkId}`)
    : createEmptyMarkerState();
  const overrideDeletedByGroup = new Map(STUDIO_GROUPS.map((group) => [group, []]));
  for (const entry of overrideMarkerState.deleted) {
    if (!overrideDeletedByGroup.has(entry.group)) continue;
    overrideDeletedByGroup.get(entry.group).push(entry);
  }

  for (const group of STUDIO_GROUPS) {
    inheritedByGroup.get(group).sort(compareEntries);
    inheritedDeletedByGroup.get(group).sort(compareEntries);
    overrideByGroup.get(group).sort(compareEntries);
    overrideDeletedByGroup.get(group).sort(compareEntries);
  }

  const rowsHtml = STUDIO_GROUPS.map((group) => {
    const inherited = inheritedByGroup.get(group) || [];
    const inheritedDeleted = inheritedDeletedByGroup.get(group) || [];
    const overrides = overrideByGroup.get(group) || [];
    const overrideDeleted = overrideDeletedByGroup.get(group) || [];
    const inheritedHtml = selectedWorkId
      ? inherited.map((entry) => renderInheritedChip(state, entry, false, seriesMarkerState.current.get(entry.canonicalId) || "")).join("")
      : inherited.map((entry) => renderSeriesEditableChip(state, entry, seriesMarkerState.current.get(entry.canonicalId) || "")).join("");
    const inheritedDeletedHtml = selectedWorkId
      ? inheritedDeleted.map((entry) => renderDeletedChip(state, entry, {
        inherited: true,
        scope: "series",
        titleKey: "inherited_tag_title",
        titleFallback: "Inherited from series: {tag_id}"
      })).join("")
      : inheritedDeleted.map((entry) => renderDeletedChip(state, entry, {
        inherited: false,
        scope: "series",
        titleKey: "series_tag_title",
        titleFallback: "Series tag {tag_id}"
      })).join("");
    const overrideHtml = overrides
      .map((entry) => renderOverrideChip(state, entry, overrideMarkerState.current.get(entry.canonicalId) || ""))
      .join("");
    const overrideDeletedHtml = overrideDeleted.map((entry) => renderDeletedChip(state, entry, {
      inherited: false,
      scope: "work",
      titleKey: "work_override_title",
      titleFallback: "Work override {tag_id}"
    })).join("");
    const emptyHtml = (!inheritedHtml && !inheritedDeletedHtml && !overrideHtml && !overrideDeletedHtml)
      ? `<span class="${UI_CLASS.empty}">${escapeHtml(studioText(state.config, "empty_state", "none"))}</span>`
      : "";
    return `
      <div class="${UI_CLASS.groupRow}">
        <span class="${classNames(UI_CLASS.groupRowLabel, UI_CLASS.chip, chipGroupClass(group))}">${escapeHtml(group)}</span>
        <div class="${UI_CLASS.groupRowChips}">
          ${inheritedHtml}
          ${inheritedDeletedHtml}
          ${overrideHtml}
          ${overrideDeletedHtml}
          ${emptyHtml}
        </div>
      </div>
    `;
  }).join("");

  state.refs.groups.innerHTML = `<div class="${UI_CLASS.groups}">${rowsHtml}</div>`;
}

function renderChipCaption(state, marker) {
  if (!marker) return "";
  const key = marker === "delete" ? "chip_caption_delete" : "chip_caption_local";
  const fallback = marker === "delete" ? "delete" : "local";
  const className = marker === "delete" ? UI_CLASS.chipCaptionDelete : UI_CLASS.chipCaptionLocal;
  return `<span class="${classNames(UI_CLASS.chipCaption, className)}">${escapeHtml(studioText(state.config, key, fallback))}</span>`;
}

function renderChipLabel(state, entry, marker) {
  return `
    <span class="${UI_CLASS.chipText}">
      <span class="${classNames(
        UI_CLASS.chipTag,
        marker === "local" ? UI_CLASS.chipTagLocal : "",
        marker === "delete" ? UI_CLASS.chipTagDelete : ""
      )}">${escapeHtml(entry.label)}</span>
      ${renderChipCaption(state, marker)}
    </span>
  `;
}

function renderSeriesEditableChip(state, entry, marker = "") {
  return `
    <span class="${classNames(UI_CLASS.chip, chipGroupClass(entry.group))}" title="${escapeHtml(studioText(state.config, "series_tag_title", "Series tag {tag_id}", { tag_id: entry.canonicalId }))}">
      <button
        type="button"
        class="${classNames(UI_CLASS.weightDot, weightDotClass(entry.wManual))}"
        data-cycle-weight-entry-id="${entry.entryId}"
        title="${escapeHtml(studioText(state.config, "weight_button_title", "w_manual {weight}", { weight: entry.wManual.toFixed(1) }))}"
        aria-label="${escapeHtml(studioText(state.config, "weight_button_aria_label", "w_manual {weight}", { weight: entry.wManual.toFixed(1) }))}"
      ></button>
      ${renderChipLabel(state, entry, marker)}
      <button
        type="button"
        class="${UI_CLASS.chipRemove}"
        data-remove-entry-id="${entry.entryId}"
        aria-label="${escapeHtml(studioText(state.config, "remove_series_tag_aria_label", "Remove {tag_id}", { tag_id: entry.canonicalId }))}"
      >x</button>
    </span>
  `;
}

function renderInheritedChip(state, entry, useColorChip, marker = "") {
  if (useColorChip) {
    return `
      <span class="${classNames(UI_CLASS.chip, chipGroupClass(entry.group))}" title="${escapeHtml(studioText(state.config, "series_tag_title", "Series tag {tag_id}", { tag_id: entry.canonicalId }))}">
        <span class="${classNames(UI_CLASS.weightDot, weightDotClass(entry.wManual))}" aria-hidden="true"></span>
        ${renderChipLabel(state, entry, marker)}
      </span>
    `;
  }
  return `
    <span class="${classNames(UI_CLASS.chip, UI_CLASS.chipInherited)}" title="${escapeHtml(studioText(state.config, "inherited_tag_title", "Inherited from series: {tag_id}", { tag_id: entry.canonicalId }))}">
      <span class="${classNames(UI_CLASS.weightDot, weightDotClass(entry.wManual))}" aria-hidden="true"></span>
      ${renderChipLabel(state, entry, marker)}
    </span>
  `;
}

function renderOverrideChip(state, entry, marker = "") {
  return `
    <span class="${classNames(UI_CLASS.chip, chipGroupClass(entry.group))}" title="${escapeHtml(studioText(state.config, "work_override_title", "Work override {tag_id}", { tag_id: entry.canonicalId }))}">
      <button
        type="button"
        class="${classNames(UI_CLASS.weightDot, weightDotClass(entry.wManual))}"
        data-cycle-weight-entry-id="${entry.entryId}"
        title="${escapeHtml(studioText(state.config, "weight_button_title", "w_manual {weight}", { weight: entry.wManual.toFixed(1) }))}"
        aria-label="${escapeHtml(studioText(state.config, "weight_button_aria_label", "w_manual {weight}", { weight: entry.wManual.toFixed(1) }))}"
      ></button>
      ${renderChipLabel(state, entry, marker)}
      <button
        type="button"
        class="${UI_CLASS.chipRemove}"
        data-remove-entry-id="${entry.entryId}"
        aria-label="${escapeHtml(studioText(state.config, "remove_work_tag_aria_label", "Remove {tag_id}", { tag_id: entry.canonicalId }))}"
      >x</button>
    </span>
  `;
}

function renderDeletedChip(state, entry, options = {}) {
  const inherited = Boolean(options.inherited);
  const titleKey = options.titleKey || "series_tag_title";
  const titleFallback = options.titleFallback || "Series tag {tag_id}";
  const restoreScope = options.scope || "series";
  return `
    <span class="${classNames(UI_CLASS.chip, inherited ? UI_CLASS.chipInherited : chipGroupClass(entry.group))}" title="${escapeHtml(studioText(state.config, titleKey, titleFallback, { tag_id: entry.canonicalId }))}">
      <span class="${classNames(UI_CLASS.weightDot, weightDotClass(entry.wManual))}" aria-hidden="true"></span>
      ${renderChipLabel(state, entry, "delete")}
      <button
        type="button"
        class="${UI_CLASS.chipRemove}"
        data-restore-tag-id="${escapeHtml(entry.canonicalId)}"
        data-restore-scope="${escapeHtml(restoreScope)}"
        aria-label="${escapeHtml(studioText(state.config, "restore_deleted_tag_aria_label", "Restore {tag_id}", { tag_id: entry.canonicalId }))}"
      >⤺</button>
    </span>
  `;
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

function renderSaveMode(state) {
  if (!state.refs.saveMode) return;
  state.refs.saveMode.textContent = buildTagStudioSaveModeText(state.config, state.saveMode, studioText);
}

function computeMetrics(state) {
  return { unresolvedCount: 0 };
}

async function probeSaveMode(state) {
  const ok = await probeStudioHealth(500);
  state.saveMode = ok && !state.hasOfflineStagedSeries ? "post" : "offline";
  state.saveModeResolved = true;
  renderSaveMode(state);
  renderAll(state);
}

function stageOfflineState(state, options = {}) {
  clearOfflineAutosave(state);

  const diff = buildStateDiff(state);
  if (!diff.seriesChanged && !diff.changedWorkIds.length) {
    if (options.manual) {
      setStatus(state, "warn", studioText(state.config, "save_status_no_changes", "No changes to save."));
      renderStatus(state);
    }
    return false;
  }

  const stagedAt = utcTimestamp();
  const stagedRow = buildPersistedSeriesRow(diff);
  const baseRow = normalizeOfflineSeriesRow(state.offlineBaseSeriesRow);
  let session = readOfflineAssignmentsSession();
  let seriesCleared = false;

  if (equalOfflineSeriesRows(stagedRow, baseRow)) {
    session = removeOfflineAssignmentsSeriesEntry(session, state.seriesId, stagedAt);
    seriesCleared = true;
  } else {
    session = upsertOfflineAssignmentsSeriesEntry(session, state.seriesId, {
      base_series_updated_at_utc: state.offlineBaseSeriesUpdatedAt,
      base_row_snapshot: baseRow,
      staged_row: stagedRow,
      staged_at_utc: stagedAt
    }, stagedAt);
  }

  state.offlineSession = writeOfflineAssignmentsSession(session);
  state.hasOfflineStagedSeries = !seriesCleared;
  applyPersistedBaseline(state, diff);

  if (options.manual) {
    const removedCount = diff.changedWorkIds.filter((workId) => !diff.nextWorkStateById.has(workId)).length;
    const savedCount = diff.changedWorkIds.length - removedCount;
    setStatus(
      state,
      "success",
      buildTagSaveSuccessMessage(
        state.config,
        { seriesSaved: diff.seriesChanged, savedCount, removedCount, savedAt: stagedAt },
        studioText
      )
    );
  }

  setSaveResult(
    state,
    "success",
    seriesCleared
      ? studioText(state.config, "save_result_offline_cleared", "Series matches repo data. Offline session entry cleared.")
      : studioText(state.config, "save_result_offline_staged", "Changes are staged in the offline session.")
  );
  renderAll(state);
  return true;
}

async function handleSave(state) {
  const diff = buildStateDiff(state);
  if (!diff.seriesChanged && !diff.changedWorkIds.length) {
    setStatus(state, "warn", studioText(state.config, "save_status_no_changes", "No changes to save."));
    renderStatus(state);
    return;
  }

  if (state.saveMode === "post") {
    try {
      const results = [];
      if (diff.seriesChanged) {
        results.push(await postTags(state.seriesId, null, diff.nextSeriesRows, false, utcTimestamp));
      }
      for (const workId of diff.changedWorkIds) {
        const nextTags = diff.nextWorkStateById.get(workId) || [];
        const keepWork = diff.nextWorkStateById.has(workId);
        results.push(await postTags(state.seriesId, workId, nextTags, keepWork, utcTimestamp));
      }
      const lastResult = results[results.length - 1] || {};
      const savedAt = String(lastResult.updated_at_utc || utcTimestamp());
      const removedCount = results.filter((result) => result && result.deleted).length;
      const savedCount = diff.changedWorkIds.length - removedCount;
      setStatus(
        state,
        "success",
        buildTagSaveSuccessMessage(
          state.config,
          { seriesSaved: diff.seriesChanged, savedCount, removedCount, savedAt },
          studioText
        )
      );
      setSaveResult(state, "", "");
      renderStatus(state);
      applyPersistedBaseline(state, diff);
      renderAll(state);
      return;
    } catch (error) {
      state.saveMode = "offline";
      state.saveModeResolved = true;
      renderSaveMode(state);
      stageOfflineState(state, { manual: false });
      setStatus(state, "error", studioText(state.config, "save_status_local_failed", "Local save failed. Switched to offline mode."));
      setSaveResult(state, "success", studioText(state.config, "save_result_local_failed", "Local server save failed. Changes are now staged in the offline session."));
      renderAll(state);
      return;
    }
  }

  stageOfflineState(state, { manual: true });
}

function openSaveModal(state) {
  const diff = buildStateDiff(state);
  if (!diff.seriesChanged && !diff.changedWorkIds.length) {
    setStatus(state, "warn", studioText(state.config, "save_status_no_changes", "No changes to save."));
    renderStatus(state);
    return;
  }

  const timestamp = utcTimestamp();
  const snippet = buildPatchSnippet(
    state.seriesId,
    diff,
    timestamp
  );
  state.modalSnippet = snippet;

  state.refs.modalTags.textContent = JSON.stringify({
    series_tags: diff.nextSeriesRows,
    work_overrides: workStateMapToObject(diff.nextWorkStateById)
  }, null, 2);
  state.refs.modalSnippet.textContent = snippet;
  state.refs.modal.hidden = false;
}

function closeModal(state) {
  state.refs.modal.hidden = true;
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

function getSelectedWorkEntries(state) {
  if (!state.selectedWorkId) return [];
  return state.workEntriesById.get(state.selectedWorkId) || [];
}

function getSelectedWorkOption(state) {
  if (!state.selectedWorkId) return null;
  return state.seriesWorkOptions.find((item) => item.workId === state.selectedWorkId) || null;
}

function getOrderedSelectedWorkOptions(state) {
  const selected = new Set(state.selectedWorkIds);
  return state.seriesWorkOptions.filter((item) => selected.has(item.workId));
}

function getOrderedSelectedWorkIds(state) {
  return getOrderedSelectedWorkOptions(state).map((item) => item.workId);
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

function weightDotClass(weight) {
  const normalized = normalizeManualWeight(weight, DEFAULT_WEIGHT);
  if (normalized === 0.3) return UI_CLASS.weightDotLow;
  if (normalized === 0.9) return UI_CLASS.weightDotHigh;
  return UI_CLASS.weightDotMid;
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

function classNames(...tokens) {
  return tokens.filter(Boolean).join(" ");
}

function chipGroupClass(group) {
  return `${UI_CLASS.chipGroupPrefix}${group}`;
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
