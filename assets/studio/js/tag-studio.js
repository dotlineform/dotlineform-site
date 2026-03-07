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
  syncWorkEntriesFromPersistedState,
  workStateMapToObject,
  buildWorkStateDiff as buildDomainWorkStateDiff
} from "./tag-studio-domain.js";
import {
  buildPatchSnippet,
  buildSaveModeText as buildTagStudioSaveModeText,
  buildSaveSuccessMessage as buildTagStudioSaveSuccessMessage,
  postTags,
  utcTimestamp
} from "./tag-studio-save.js";
import {
  renderStudioModalActions,
  renderStudioModalFrame
} from "./studio-modal.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const POPUP_TAG_MATCH_CAP = 12;
const POPUP_ALIAS_MATCH_CAP = 12;
const POPUP_WORK_MATCH_CAP = 12;
const WEIGHT_VALUES = [0.3, 0.6, 0.9];
const DEFAULT_WEIGHT = 0.6;

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

    const state = buildState(
      mount,
      seriesId,
      registryJson,
      aliasesJson,
      assignmentsJson,
      seriesIndexJson,
      worksIndexJson,
      config
    );
    restoreSelectionFromQuery(state);
    renderShell(state);
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

function buildState(mount, seriesId, registryJson, aliasesJson, assignmentsJson, seriesIndexJson, worksIndexJson, config) {
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
  const seriesAssignment = getSeriesAssignment(assignmentsSeries, seriesId);
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
    modalSnippet: "",
    saveMode: "patch"
  };
}

function buildStateDiff(state) {
  return buildDomainWorkStateDiff(state, getOrderedSelectedWorkIds(state), getSeriesTagIdSet(state));
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
  const saveModeLabel = buildTagStudioSaveModeText(state.config, "patch", studioText);
  const modalTitle = studioText(state.config, "modal_title", "Work Tag Patch Preview");
  const modalResolvedLabel = studioText(state.config, "modal_resolved_label", "Resolved work override tags");
  const modalPatchGuidanceLabel = studioText(state.config, "modal_patch_guidance_label", "Patch guidance for tag_assignments.json");
  const modalCopyButton = studioText(state.config, "modal_copy_button", "Copy");
  const modalCloseButton = studioText(state.config, "modal_close_button", "Close");
  const saveModalHtml = renderStudioModalFrame({
    modalRole: "modal",
    backdropRole: "close-modal",
    titleId: "tagStudioModalTitle",
    title: modalTitle,
    bodyHtml: `
      <p class="tagStudioModal__label">${escapeHtml(modalResolvedLabel)}</p>
      <pre class="tagStudioModal__pre" data-role="modal-tags"></pre>
      <p class="tagStudioModal__label">${escapeHtml(modalPatchGuidanceLabel)}</p>
      <pre class="tagStudioModal__pre" data-role="modal-snippet"></pre>
    `,
    actionsHtml: renderStudioModalActions([
      { role: "copy-snippet", label: modalCopyButton, primary: true },
      { role: "close-modal", label: modalCloseButton }
    ])
  });
  state.mount.innerHTML = `
    <div class="tagStudio">
      <section class="tagStudio__panel tagStudio__panel--editor">
        <div class="tagStudio__inputRow tagStudio__inputRow--work">
          <input
            id="tagStudioWorkInput"
            class="tagStudio__input"
            type="text"
            autocomplete="off"
            placeholder="${escapeHtml(workInputPlaceholder)}"
          >
          <div class="tagStudio__workSelection" data-role="selected-work"></div>
        </div>
        <div class="tagStudio__popup tagStudio__popup--work" data-role="work-popup" hidden>
          <div class="tagStudio__popupInner tagStudio__popupInner--series" data-role="work-popup-list"></div>
        </div>
        <p class="tagStudio__contextHint" data-role="context-hint"></p>

        <div data-role="groups"></div>
        <div class="tagStudio__inputRow tagStudio__inputRow--editor">
          <input id="tagStudioInput" class="tagStudio__input" type="text" autocomplete="off" placeholder="${escapeHtml(tagInputPlaceholder)}">
          <button type="button" class="tagStudio__button" data-role="add-tag">${escapeHtml(addButtonLabel)}</button>
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="save">${escapeHtml(saveButtonLabel)}</button>
          <span class="tagStudio__saveMode" data-role="save-mode">${escapeHtml(saveModeLabel)}</span>
        </div>
        <div class="tagStudio__popup tagStudio__popup--series" data-role="popup" hidden>
          <div class="tagStudio__popupInner tagStudio__popupInner--series" data-role="popup-list"></div>
        </div>
        <p class="tagStudio__status" data-role="status"></p>
        <p class="tagStudio__saveWarning" data-role="save-warning"></p>
        <p class="tagStudio__saveResult" data-role="save-result"></p>
      </section>
    </div>

    ${saveModalHtml}
  `;

  state.refs = {
    workInput: state.mount.querySelector("#tagStudioWorkInput"),
    selectedWork: state.mount.querySelector('[data-role="selected-work"]'),
    workPopup: state.mount.querySelector('[data-role="work-popup"]'),
    workPopupList: state.mount.querySelector('[data-role="work-popup-list"]'),
    contextHint: state.mount.querySelector('[data-role="context-hint"]'),
    input: state.mount.querySelector("#tagStudioInput"),
    addButton: state.mount.querySelector('[data-role="add-tag"]'),
    popup: state.mount.querySelector('[data-role="popup"]'),
    popupList: state.mount.querySelector('[data-role="popup-list"]'),
    status: state.mount.querySelector('[data-role="status"]'),
    groups: state.mount.querySelector('[data-role="groups"]'),
    saveButton: state.mount.querySelector('[data-role="save"]'),
    saveMode: state.mount.querySelector('[data-role="save-mode"]'),
    saveWarning: state.mount.querySelector('[data-role="save-warning"]'),
    saveResult: state.mount.querySelector('[data-role="save-result"]'),
    modal: state.mount.querySelector('[data-role="modal"]'),
    modalTags: state.mount.querySelector('[data-role="modal-tags"]'),
    modalSnippet: state.mount.querySelector('[data-role="modal-snippet"]'),
    copyButton: state.mount.querySelector('[data-role="copy-snippet"]')
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
      if (!target.closest('[data-role="popup"]') && !target.closest("#tagStudioInput")) {
        hidePopup(state);
      }
    }

    if (state.refs.workPopup && !state.refs.workPopup.hidden) {
      if (!target.closest('[data-role="work-popup"]') && !target.closest("#tagStudioWorkInput")) {
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
      addResolvedTag(state, tag, tag.slug || tag.tag_id);
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
      addResolvedTag(state, tag, aliasSource || tag.tag_id);
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
      const entry = getSelectedWorkEntries(state).find((item) => item.entryId === entryId);
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
    if (!button) return;
    const entryId = Number(button.getAttribute("data-remove-entry-id"));
    removeSelectedWorkEntry(state, entryId);
    renderAll(state);
  });

  state.refs.saveButton.addEventListener("click", () => {
    void handleSave(state);
  });

  state.refs.modal.addEventListener("click", (event) => {
    if (!event.target.closest('[data-role="close-modal"]')) return;
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
  if (!state.selectedWorkId) {
    setStatus(state, "warn", studioText(state.config, "select_work_before_tags", "Select a work before adding tags."));
    renderStatus(state);
    return;
  }

  const rawInput = String(state.refs.input.value || "").trim();
  if (!rawInput) {
    setStatus(state, "warn", studioText(state.config, "tag_input_required", "Enter a tag slug, tag id, or alias."));
    renderStatus(state);
    return;
  }

  const resolved = resolveInput(rawInput, state);
  if (resolved.type === "resolved") {
    addResolvedTag(state, resolved.tag, rawInput);
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

function addResolvedTag(state, tag, rawInput) {
  if (!state.selectedWorkId || !tag || !tag.tag_id) return;

  const tagId = normalize(tag.tag_id);
  if (getSeriesTagIdSet(state).has(tagId)) {
    setStatus(state, "warn", studioText(
      state.config,
      "tag_inherited_warning",
      "Inherited from series already: {tag_id}.",
      { tag_id: tagId }
    ));
    return;
  }

  const entries = getSelectedWorkEntries(state);
  const alreadyExists = entries.some((entry) => entry.canonicalId === tagId);
  if (alreadyExists) {
    setStatus(state, "warn", studioText(
      state.config,
      "tag_already_added_warning",
      "Already added for {work_id}: {tag_id}.",
      {
        work_id: state.selectedWorkId,
        tag_id: tagId
      }
    ));
    return;
  }

  entries.push(makeResolvedEntry(nextEntryId(state), rawInput, tag, DEFAULT_WEIGHT));
  setStatus(state, "success", studioText(
    state.config,
    "tag_added_success",
    "Added {tag_id} to {work_id}.",
    {
      work_id: state.selectedWorkId,
      tag_id: tagId
    }
  ));
  setSaveResult(state, "", "");
}

function nextEntryId(state) {
  let maxId = 0;
  for (const entries of state.workEntriesById.values()) {
    for (const entry of entries) {
      if (entry.entryId > maxId) maxId = entry.entryId;
    }
  }
  return maxId + 1;
}

function removeSelectedWorkEntry(state, entryId) {
  if (!state.selectedWorkId) return;
  const entries = getSelectedWorkEntries(state);
  const sizeBefore = entries.length;
  const nextEntries = entries.filter((entry) => entry.entryId !== entryId);
  state.workEntriesById.set(state.selectedWorkId, nextEntries);
  if (nextEntries.length < sizeBefore) {
    setStatus(state, "success", studioText(state.config, "work_tag_removed", "Work tag removed."));
    setSaveResult(state, "", "");
  }
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
}

function renderSelectedWork(state) {
  const selected = getOrderedSelectedWorkOptions(state);
  if (!selected.length) {
    state.refs.selectedWork.innerHTML = "";
    return;
  }
  state.refs.selectedWork.innerHTML = selected.map((item) => {
    const titleText = item.title ? ` ${escapeHtml(item.title)}` : "";
    const activeClass = item.workId === state.selectedWorkId ? " is-active" : "";
    return `
      <span class="tagStudio__selectedWorkPill${activeClass}" title="${escapeHtml(item.workId)}${titleText}">
        <button type="button" class="tagStudio__selectedWorkBtn" data-activate-work-id="${escapeHtml(item.workId)}" aria-pressed="${item.workId === state.selectedWorkId ? "true" : "false"}">
          <span class="tagStudio__selectedWorkId">${escapeHtml(item.workId)}</span>
        </button>
        <button
          type="button"
          class="tagStudio__chipRemove"
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
      "Select one or more works to add per-work tag overrides. Series tags shown below are context only."
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
    <div class="tagStudioSuggest">
      <section class="tagStudioSuggest__section">
        <p class="tagStudioSuggest__heading">${escapeHtml(studioText(state.config, "popup_heading_works", "works"))}</p>
        <div class="tagStudioSuggest__workRows">
          ${matches.map((item) => `
            <button type="button" class="tagStudioSuggest__workButton" data-popup-work-id="${escapeHtml(item.workId)}">
              <span class="tagStudioSuggest__workId">${escapeHtml(item.workId)}</span>
              <span class="tagStudioSuggest__workTitle">${escapeHtml(item.title || "")}</span>
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
  if (!query || !state.selectedWorkId) {
    hidePopup(state);
    return;
  }

  const selectedTagIds = getSelectedTagIdSet(state);
  const inheritedTagIds = getSeriesTagIdSet(state);
  const tagMatches = state.activeTagsBySlug
    .filter((tag) => tag.slug.startsWith(query) && !selectedTagIds.has(tag.tag_id) && !inheritedTagIds.has(tag.tag_id))
    .slice(0, POPUP_TAG_MATCH_CAP);
  const aliasMatches = getPopupAliasMatches(state, query, selectedTagIds, inheritedTagIds).slice(0, POPUP_ALIAS_MATCH_CAP);

  if (!tagMatches.length && !aliasMatches.length) {
    hidePopup(state);
    return;
  }

  const tagSection = tagMatches.length
    ? `
      <section class="tagStudioSuggest__section">
        <p class="tagStudioSuggest__heading">${escapeHtml(studioText(state.config, "popup_heading_tags", "tags"))}</p>
        <div class="tagStudioSuggest__tagRows">
          ${tagMatches.map((tag) => `
            <button
              type="button"
              class="tagStudio__popupPill tagStudio__chip--${escapeHtml(tag.group)}"
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
      <section class="tagStudioSuggest__section">
        <p class="tagStudioSuggest__heading">${escapeHtml(studioText(state.config, "popup_heading_aliases", "aliases"))}</p>
        <div class="tagStudioSuggest__aliasRows">
          ${aliasMatches.map((entry) => `
            <div class="tagStudioSuggest__aliasRow">
              <span
                class="tagStudio__popupPill tagStudioSuggest__aliasPill"
                data-popup-alias="${escapeHtml(entry.alias)}"
                title="${escapeHtml(entry.alias)}"
              >
                ${escapeHtml(entry.alias)}
              </span>
              <div class="tagStudioSuggest__aliasTargets">
                ${entry.targets.map((target) => `
                  <button
                    type="button"
                    class="tagStudio__popupPill tagStudio__chip--${escapeHtml(target.group)} tagStudioSuggest__aliasTarget"
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
    <div class="tagStudioSuggest">
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

function getSelectedTagIdSet(state) {
  const out = new Set();
  for (const entry of getSelectedWorkEntries(state)) {
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

function renderGroups(state) {
  const inheritedByGroup = new Map(STUDIO_GROUPS.map((group) => [group, []]));
  for (const entry of state.seriesEntries) {
    if (!inheritedByGroup.has(entry.group)) continue;
    inheritedByGroup.get(entry.group).push(entry);
  }

  const overrideByGroup = new Map(STUDIO_GROUPS.map((group) => [group, []]));
  for (const entry of getSelectedWorkEntries(state)) {
    if (!overrideByGroup.has(entry.group)) continue;
    overrideByGroup.get(entry.group).push(entry);
  }

  for (const group of STUDIO_GROUPS) {
    inheritedByGroup.get(group).sort(compareEntries);
    overrideByGroup.get(group).sort(compareEntries);
  }

  const selectedWorkId = state.selectedWorkId;
  const rowsHtml = STUDIO_GROUPS.map((group) => {
    const inherited = inheritedByGroup.get(group) || [];
    const overrides = overrideByGroup.get(group) || [];
    const inheritedHtml = inherited.map((entry) => renderInheritedChip(entry, !selectedWorkId)).join("");
    const overrideHtml = overrides.map((entry) => renderOverrideChip(entry)).join("");
    const emptyHtml = (!inheritedHtml && !overrideHtml)
      ? `<span class="tagStudio__empty">${escapeHtml(studioText(state.config, "empty_state", "none"))}</span>`
      : "";
    return `
      <div class="tagStudioGroupRow">
        <span class="tagStudioGroupRow__label">${escapeHtml(group)}:</span>
        <div class="tagStudioGroupRow__chips">
          ${inheritedHtml}
          ${overrideHtml}
          ${emptyHtml}
        </div>
      </div>
    `;
  }).join("");

  state.refs.groups.innerHTML = `<div class="tagStudioGroups">${rowsHtml}</div>`;
}

function renderInheritedChip(entry, useColorChip) {
  if (useColorChip) {
    return `
      <span class="tagStudio__chip tagStudio__chip--${escapeHtml(entry.group)}" title="${escapeHtml(studioText(null, "series_tag_title", "Series tag {tag_id}", { tag_id: entry.canonicalId }))}">
        <span class="tagStudio__weightDot ${weightDotClass(entry.wManual)}" aria-hidden="true"></span>
        <span class="tagStudio__chipTag">${escapeHtml(entry.label)}</span>
      </span>
    `;
  }
  return `
    <span class="tagStudio__chip tagStudio__chip--inherited" title="${escapeHtml(studioText(null, "inherited_tag_title", "Inherited from series: {tag_id}", { tag_id: entry.canonicalId }))}">
      <span class="tagStudio__weightDot ${weightDotClass(entry.wManual)}" aria-hidden="true"></span>
      <span class="tagStudio__chipTag">${escapeHtml(entry.label)}</span>
    </span>
  `;
}

function renderOverrideChip(entry) {
  return `
    <span class="tagStudio__chip tagStudio__chip--${escapeHtml(entry.group)}" title="${escapeHtml(studioText(null, "work_override_title", "Work override {tag_id}", { tag_id: entry.canonicalId }))}">
      <button
        type="button"
        class="tagStudio__weightDot ${weightDotClass(entry.wManual)}"
        data-cycle-weight-entry-id="${entry.entryId}"
        title="${escapeHtml(studioText(null, "weight_button_title", "w_manual {weight}", { weight: entry.wManual.toFixed(1) }))}"
        aria-label="${escapeHtml(studioText(null, "weight_button_aria_label", "w_manual {weight}", { weight: entry.wManual.toFixed(1) }))}"
      ></button>
      <span class="tagStudio__chipTag">${escapeHtml(entry.label)}</span>
      <button
        type="button"
        class="tagStudio__chipRemove"
        data-remove-entry-id="${entry.entryId}"
        aria-label="${escapeHtml(studioText(null, "remove_work_tag_aria_label", "Remove {tag_id}", { tag_id: entry.canonicalId }))}"
      >x</button>
    </span>
  `;
}

function renderSaveState(state) {
  const metrics = computeMetrics(state);
  const hasSelectedWork = Boolean(state.selectedWorkId);
  const isDirty = hasPendingSaveChanges(state);
  state.refs.input.disabled = !hasSelectedWork;
  state.refs.addButton.disabled = !hasSelectedWork;
  state.refs.saveButton.disabled = !isDirty || metrics.unresolvedCount > 0;

  if (!hasSelectedWork && isDirty) {
    state.refs.saveWarning.textContent = studioText(
      state.config,
      "save_warning_pending_diff",
      "Save to persist the current work-row diff."
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
  state.saveMode = ok ? "post" : "patch";
  renderSaveMode(state);
}

async function handleSave(state) {
  const diff = buildStateDiff(state);
  if (!diff.changedWorkIds.length) {
    setStatus(state, "warn", studioText(state.config, "save_status_no_changes", "No changes to save."));
    renderStatus(state);
    return;
  }

  if (state.saveMode === "post") {
    try {
      const results = [];
      for (const workId of diff.changedWorkIds) {
        const nextTags = diff.nextWorkStateById.get(workId) || [];
        const keepWork = diff.nextWorkStateById.has(workId);
        results.push(await postTags(state.seriesId, workId, nextTags, keepWork, utcTimestamp));
      }
      const lastResult = results[results.length - 1] || {};
      const savedAt = String(lastResult.updated_at_utc || utcTimestamp());
      const removedCount = results.filter((result) => result && result.deleted).length;
      const savedCount = diff.changedWorkIds.length - removedCount;
      setStatus(state, "success", buildTagStudioSaveSuccessMessage(state.config, savedCount, removedCount, savedAt, studioText));
      setSaveResult(state, "", "");
      renderStatus(state);
      state.baselineWorkStateById = cloneWorkStateMap(diff.nextWorkStateById);
      syncWorkEntriesFromPersistedState(state, diff.nextWorkStateById);
      renderAll(state);
      return;
    } catch (error) {
      state.saveMode = "patch";
      renderSaveMode(state);
      setStatus(state, "error", studioText(state.config, "save_status_local_failed", "Local save failed. Switched to Patch mode."));
      setSaveResult(state, "error", studioText(state.config, "save_result_local_failed", "Local server save failed. Showing patch fallback."));
      renderStatus(state);
      openSaveModal(state);
      return;
    }
  }

  openSaveModal(state);
}

function openSaveModal(state) {
  const diff = buildStateDiff(state);
  if (!diff.changedWorkIds.length) {
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

  state.refs.modalTags.textContent = JSON.stringify(workStateMapToObject(diff.nextWorkStateById), null, 2);
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
  state.refs.status.className = "tagStudio__status";
  if (state.statusKind) {
    state.refs.status.classList.add(`is-${state.statusKind}`);
  }
}

function setSaveResult(state, kind, text) {
  if (!state.refs.saveResult) return;
  state.refs.saveResult.textContent = text || "";
  state.refs.saveResult.className = "tagStudio__saveResult";
  if (kind) state.refs.saveResult.classList.add(`is-${kind}`);
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
  return buildStateDiff(state).changedWorkIds.length > 0;
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
  if (normalized === 0.3) return "tagStudio__weightDot--low";
  if (normalized === 0.9) return "tagStudio__weightDot--high";
  return "tagStudio__weightDot--mid";
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
  mount.innerHTML = `<div class="tagStudioError">${escapeHtml(message)}</div>`;
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
