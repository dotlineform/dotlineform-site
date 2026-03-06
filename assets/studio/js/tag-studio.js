import {
  getSiteDataPath,
  getStudioDataPath,
  getStudioGroups,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
let GROUP_INDEX = new Map(STUDIO_GROUPS.map((group, index) => [group, index]));
const POST_ENDPOINT = "http://127.0.0.1:8787/save-tags";
const HEALTH_ENDPOINT = "http://127.0.0.1:8787/health";
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
  GROUP_INDEX = new Map(STUDIO_GROUPS.map((group, index) => [group, index]));

  const seriesId = String(mount.dataset.seriesId || "").trim();
  if (!seriesId) {
    renderFatalError(mount, studioText(config, "missing_series_id_error", "Tag Studio error: missing series id."));
    return;
  }

  try {
    const [registryJson, aliasesJson, assignmentsJson, seriesIndexJson, worksIndexJson] = await Promise.all([
      fetchJson(getStudioDataPath(config, "tag_registry")),
      fetchJson(getStudioDataPath(config, "tag_aliases")),
      fetchJson(getStudioDataPath(config, "tag_assignments")),
      fetchJson(getSiteDataPath(config, "series_index")),
      fetchJson(getSiteDataPath(config, "works_index"))
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

async function fetchJson(url) {
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} for ${url}`);
  }
  return response.json();
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

function sanitizeTag(rawTag) {
  if (!rawTag || typeof rawTag !== "object") return null;

  const tagId = normalize(rawTag.tag_id);
  const group = normalize(rawTag.group);
  const label = String(rawTag.label || "").trim();
  const status = normalize(rawTag.status || "active");

  if (!tagId || !group || !label) return null;
  if (!GROUP_INDEX.has(group)) return null;

  const splitIndex = tagId.indexOf(":");
  const slug = splitIndex >= 0 ? tagId.slice(splitIndex + 1) : tagId;

  return {
    tag_id: tagId,
    group,
    label,
    status,
    slug
  };
}

function pushMapList(map, key, value) {
  if (!key) return;
  if (!map.has(key)) map.set(key, []);
  map.get(key).push(value);
}

function getSeriesIndexRow(seriesMap, seriesId) {
  if (seriesMap[seriesId]) return seriesMap[seriesId];

  const normalizedSeriesId = normalize(seriesId);
  for (const [key, value] of Object.entries(seriesMap)) {
    if (normalize(key) === normalizedSeriesId) return value;
  }
  return null;
}

function getSeriesAssignment(seriesAssignments, seriesId) {
  if (seriesAssignments[seriesId]) return seriesAssignments[seriesId];

  const lowerSeriesId = normalize(seriesId);
  for (const [key, value] of Object.entries(seriesAssignments)) {
    if (normalize(key) === lowerSeriesId) return value;
  }
  return null;
}

function buildSeriesWorkOptions(seriesId, seriesRow, worksIndexMap) {
  const works = Array.isArray(seriesRow && seriesRow.works) ? seriesRow.works : [];
  const out = [];
  const seen = new Set();

  for (const rawWorkId of works) {
    const workId = normalizeWorkId(rawWorkId);
    if (!workId || seen.has(workId)) continue;
    seen.add(workId);
    const workMeta = getWorkIndexRow(worksIndexMap, workId);
    const title = String(workMeta && workMeta.title || "").trim();
    const shortWorkId = String(Number(workId));
    out.push({
      workId,
      shortWorkId,
      title,
      seriesId,
      titleKey: normalize(title)
    });
  }

  return out;
}

function getWorkIndexRow(worksMap, workId) {
  if (worksMap[workId]) return worksMap[workId];
  for (const [key, value] of Object.entries(worksMap)) {
    if (normalizeWorkId(key) === workId) return value;
  }
  return null;
}

function createResolvedEntries(rows, tagsById, nextEntryId = 1) {
  const entries = [];
  let cursor = nextEntryId;
  for (const row of rows) {
    const tag = tagsById.get(row.tagId);
    if (!tag) continue;
    entries.push(makeResolvedEntry(cursor++, row.tagId, tag, row.wManual));
  }
  return { entries, nextEntryId: cursor };
}

function renderShell(state) {
  const workInputPlaceholder = studioText(state.config, "work_input_placeholder", "work_id(s) in this series");
  const tagInputPlaceholder = studioText(state.config, "tag_input_placeholder", "tag slug or alias");
  const addButtonLabel = studioText(state.config, "add_button", "Add");
  const saveButtonLabel = studioText(state.config, "save_button", "Save Tags");
  const saveModeLabel = buildSaveModeText(state, "patch");
  const modalTitle = studioText(state.config, "modal_title", "Work Tag Patch Preview");
  const modalResolvedLabel = studioText(state.config, "modal_resolved_label", "Resolved work override tags");
  const modalPatchGuidanceLabel = studioText(state.config, "modal_patch_guidance_label", "Patch guidance for tag_assignments.json");
  const modalCopyButton = studioText(state.config, "modal_copy_button", "Copy");
  const modalCloseButton = studioText(state.config, "modal_close_button", "Close");
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

    <div class="tagStudioModal" data-role="modal" hidden>
      <div class="tagStudioModal__backdrop" data-role="close-modal"></div>
      <div class="tagStudioModal__dialog" role="dialog" aria-modal="true" aria-labelledby="tagStudioModalTitle">
        <h3 id="tagStudioModalTitle">${escapeHtml(modalTitle)}</h3>
        <p class="tagStudioModal__label">${escapeHtml(modalResolvedLabel)}</p>
        <pre class="tagStudioModal__pre" data-role="modal-tags"></pre>
        <p class="tagStudioModal__label">${escapeHtml(modalPatchGuidanceLabel)}</p>
        <pre class="tagStudioModal__pre" data-role="modal-snippet"></pre>
        <div class="tagStudioModal__actions">
          <button type="button" class="tagStudio__button tagStudio__button--primary" data-role="copy-snippet">${escapeHtml(modalCopyButton)}</button>
          <button type="button" class="tagStudio__button" data-role="close-modal">${escapeHtml(modalCloseButton)}</button>
        </div>
      </div>
    </div>
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
      setStatus(state, "success", `Updated ${entry.canonicalId} w_manual to ${entry.wManual.toFixed(1)}.`);
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
      setStatus(state, "error", "Copy failed. Select and copy the patch guidance manually.");
    }
    renderStatus(state);
  });
}

function selectWorkFromInput(state) {
  const rawInput = String(state.refs.workInput.value || "").trim();
  if (!rawInput) {
    setStatus(state, "warn", "Enter a work_id from this series.");
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
    setStatus(state, "error", `Unknown work_id for this series: "${rawInput}".`);
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

  setStatus(state, "warn", `Multiple works match "${rawInput}". Choose one from the popup.`);
  renderStatus(state);
  renderWorkPopup(state);
}

function addWorksFromTokens(state, tokens) {
  if (!tokens.length) {
    setStatus(state, "warn", "Enter at least one work_id from this series.");
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

  const messageParts = [];
  if (added.length) {
    messageParts.push(`Added ${added.length} work${added.length === 1 ? "" : "s"}.`);
  }
  if (unknown.length) {
    messageParts.push(`Not in this series: ${unknown.join(", ")}.`);
  }
  if (invalid.length) {
    messageParts.push(`Invalid work_id: ${invalid.join(", ")}.`);
  }
  const kind = (unknown.length || invalid.length) ? (added.length ? "warn" : "error") : "success";
  setStatus(state, kind, messageParts.join(" "));
  renderAll(state);
}

function addWorkSelection(state, workId, activate = true) {
  if (!state.seriesWorkIds.has(workId)) {
    setStatus(state, "error", `Work ${workId} is not in this series.`);
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
    setStatus(state, "success", `Selected work ${workId}.`);
  }
  state.refs.workInput.value = "";
  hideWorkPopup(state);
  setSaveResult(state, "", "");
  renderAll(state);
  return true;
}

function activateSelectedWork(state, workId, render = true) {
  if (workId && !state.selectedWorkIds.includes(workId)) return;
  state.selectedWorkId = workId;
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
  hideWorkPopup(state);
  hidePopup(state);
  setStatus(state, "", "");
  setSaveResult(state, "", "");
  renderAll(state);
}

function addFromInput(state) {
  if (!state.selectedWorkId) {
    setStatus(state, "warn", "Select a work before adding tags.");
    renderStatus(state);
    return;
  }

  const rawInput = String(state.refs.input.value || "").trim();
  if (!rawInput) {
    setStatus(state, "warn", "Enter a tag slug, tag id, or alias.");
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
    setStatus(state, "warn", `Multiple matches for "${rawInput}": ${candidateIds.join(", ")}${suffix}. Choose one from autocomplete.`);
    renderStatus(state);
    return;
  }

  setStatus(state, "error", `Unknown tag: "${rawInput}".`);
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
    setStatus(state, "warn", `Inherited from series already: ${tagId}.`);
    return;
  }

  const entries = getSelectedWorkEntries(state);
  const alreadyExists = entries.some((entry) => entry.canonicalId === tagId);
  if (alreadyExists) {
    setStatus(state, "warn", `Already added for ${state.selectedWorkId}: ${tagId}.`);
    return;
  }

  entries.push(makeResolvedEntry(nextEntryId(state), rawInput, tag, DEFAULT_WEIGHT));
  setStatus(state, "success", `Added ${tagId} to ${state.selectedWorkId}.`);
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
    setStatus(state, "success", "Work tag removed.");
    setSaveResult(state, "", "");
  }
}

function makeResolvedEntry(entryId, rawInput, tag, wManual) {
  const manual = normalizeManualWeight(wManual, DEFAULT_WEIGHT);
  return {
    entryId,
    rawInput: String(rawInput || "").trim(),
    canonicalId: normalize(tag.tag_id),
    group: normalize(tag.group),
    label: String(tag.label || tag.tag_id).trim(),
    wManual: manual
  };
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
        <button type="button" class="tagStudio__chipRemove" data-clear-selected-work="${escapeHtml(item.workId)}" aria-label="Remove selected work ${escapeHtml(item.workId)}">x</button>
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
        <p class="tagStudioSuggest__heading">works</p>
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
        <p class="tagStudioSuggest__heading">tags</p>
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
        <p class="tagStudioSuggest__heading">aliases</p>
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
    const emptyHtml = (!inheritedHtml && !overrideHtml) ? `<span class="tagStudio__empty">none</span>` : "";
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
      <span class="tagStudio__chip tagStudio__chip--${escapeHtml(entry.group)}" title="Series tag ${escapeHtml(entry.canonicalId)}">
        <span class="tagStudio__weightDot ${weightDotClass(entry.wManual)}" aria-hidden="true"></span>
        <span class="tagStudio__chipTag">${escapeHtml(entry.label)}</span>
      </span>
    `;
  }
  return `
    <span class="tagStudio__chip tagStudio__chip--inherited" title="Inherited from series: ${escapeHtml(entry.canonicalId)}">
      <span class="tagStudio__weightDot ${weightDotClass(entry.wManual)}" aria-hidden="true"></span>
      <span class="tagStudio__chipTag">${escapeHtml(entry.label)}</span>
    </span>
  `;
}

function renderOverrideChip(entry) {
  return `
    <span class="tagStudio__chip tagStudio__chip--${escapeHtml(entry.group)}" title="Work override ${escapeHtml(entry.canonicalId)}">
      <button
        type="button"
        class="tagStudio__weightDot ${weightDotClass(entry.wManual)}"
        data-cycle-weight-entry-id="${entry.entryId}"
        title="w_manual ${entry.wManual.toFixed(1)}"
        aria-label="w_manual ${entry.wManual.toFixed(1)}"
      ></button>
      <span class="tagStudio__chipTag">${escapeHtml(entry.label)}</span>
      <button type="button" class="tagStudio__chipRemove" data-remove-entry-id="${entry.entryId}" aria-label="Remove ${escapeHtml(entry.canonicalId)}">x</button>
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
    state.refs.saveWarning.textContent = "Save to persist the current work-row diff.";
    return;
  }
  state.refs.saveWarning.textContent = metrics.unresolvedCount > 0
    ? studioText(state.config, "save_warning_unresolved", "Resolve unknown tags before saving.")
    : "";
}

function renderSaveMode(state) {
  if (!state.refs.saveMode) return;
  state.refs.saveMode.textContent = buildSaveModeText(state, state.saveMode);
}

function computeMetrics(state) {
  return { unresolvedCount: 0 };
}

async function probeSaveMode(state) {
  const ok = await isLocalSaveAvailable(500);
  state.saveMode = ok ? "post" : "patch";
  renderSaveMode(state);
}

async function isLocalSaveAvailable(timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(HEALTH_ENDPOINT, { signal: controller.signal });
    if (!response.ok) return false;
    const data = await response.json();
    return Boolean(data && data.ok);
  } catch (error) {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

async function handleSave(state) {
  const diff = buildWorkStateDiff(state);
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
        results.push(await postTags(state.seriesId, workId, nextTags, keepWork));
      }
      const lastResult = results[results.length - 1] || {};
      const savedAt = String(lastResult.updated_at_utc || utcTimestamp());
      const removedCount = results.filter((result) => result && result.deleted).length;
      const savedCount = diff.changedWorkIds.length - removedCount;
      setStatus(state, "success", buildSaveSuccessMessage(state, savedCount, removedCount, savedAt));
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

async function postTags(seriesId, workId, tags, keepWork) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 3000);
  try {
    const response = await fetch(POST_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        series_id: seriesId,
        work_id: workId,
        tags,
        keep_work: Boolean(keepWork),
        client_time_utc: utcTimestamp()
      }),
      signal: controller.signal
    });

    let body = null;
    try {
      body = await response.json();
    } catch (error) {
      body = null;
    }

    if (!response.ok || !body || !body.ok) {
      const message = (body && body.error) ? String(body.error) : `HTTP ${response.status}`;
      throw new Error(message);
    }
    return body;
  } finally {
    clearTimeout(timer);
  }
}

function openSaveModal(state) {
  const diff = buildWorkStateDiff(state);
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

function getCanonicalTagAssignments(state) {
  const inheritedTagIds = getSeriesTagIdSet(state);
  const seen = new Set();
  const tags = [];

  for (const entry of getSelectedWorkEntries(state)) {
    if (!entry || !entry.canonicalId) continue;
    if (inheritedTagIds.has(entry.canonicalId) || seen.has(entry.canonicalId)) continue;
    seen.add(entry.canonicalId);
    tags.push({
      tag_id: entry.canonicalId,
      w_manual: entry.wManual
    });
  }

  tags.sort(compareAssignmentRows);
  return tags;
}

function getCanonicalTagAssignmentsForWork(state, workId) {
  const entries = state.workEntriesById.get(workId) || [];
  const inheritedTagIds = getSeriesTagIdSet(state);
  const seen = new Set();
  const tags = [];

  for (const entry of entries) {
    if (!entry || !entry.canonicalId) continue;
    if (inheritedTagIds.has(entry.canonicalId) || seen.has(entry.canonicalId)) continue;
    seen.add(entry.canonicalId);
    tags.push({
      tag_id: entry.canonicalId,
      w_manual: entry.wManual
    });
  }

  return normalizeAssignmentRows(tags);
}

function buildCurrentPersistWorkState(state) {
  const out = new Map();
  const selectedWorkIds = getOrderedSelectedWorkIds(state);
  if (!selectedWorkIds.length) return out;

  if (state.selectedWorkId) {
    const activeAssignments = getCanonicalTagAssignmentsForWork(state, state.selectedWorkId);
    for (const workId of selectedWorkIds) {
      out.set(workId, activeAssignments.map((row) => ({ ...row })));
    }
    return out;
  }

  for (const workId of selectedWorkIds) {
    out.set(workId, getCanonicalTagAssignmentsForWork(state, workId));
  }
  return out;
}

function buildWorkStateDiff(state) {
  const nextWorkStateById = buildCurrentPersistWorkState(state);
  const baseline = state.baselineWorkStateById instanceof Map ? state.baselineWorkStateById : new Map();
  const keys = new Set([...baseline.keys(), ...nextWorkStateById.keys()]);
  const changedWorkIds = [];

  for (const workId of Array.from(keys).sort()) {
    const prevRows = baseline.has(workId) ? baseline.get(workId) : null;
    const nextRows = nextWorkStateById.has(workId) ? nextWorkStateById.get(workId) : null;
    if (!equalAssignmentRows(prevRows, nextRows)) {
      changedWorkIds.push(workId);
    }
  }

  return { changedWorkIds, nextWorkStateById };
}

function cloneWorkStateMap(map) {
  const out = new Map();
  if (!(map instanceof Map)) return out;
  for (const [workId, rows] of map.entries()) {
    out.set(workId, normalizeAssignmentRows(rows));
  }
  return out;
}

function syncWorkEntriesFromPersistedState(state, workStateById) {
  const nextSelectedWorkIds = [];
  const nextWorkEntriesById = new Map();
  let nextId = 1;

  for (const option of state.seriesWorkOptions) {
    if (!(workStateById instanceof Map) || !workStateById.has(option.workId)) continue;
    const rows = workStateById.get(option.workId) || [];
    const resolved = createResolvedEntries(rows, state.tagsById, nextId);
    nextSelectedWorkIds.push(option.workId);
    nextWorkEntriesById.set(option.workId, resolved.entries);
    nextId = resolved.nextEntryId;
  }

  state.selectedWorkIds = nextSelectedWorkIds;
  state.workEntriesById = nextWorkEntriesById;
  if (state.selectedWorkId && !nextWorkEntriesById.has(state.selectedWorkId)) {
    state.selectedWorkId = "";
  }
}

function workStateMapToObject(map) {
  const out = {};
  if (!(map instanceof Map)) return out;
  for (const [workId, rows] of map.entries()) {
    out[workId] = normalizeAssignmentRows(rows);
  }
  return out;
}

function normalizeAssignmentRows(rows) {
  const list = Array.isArray(rows) ? rows : [];
  const seen = new Set();
  const out = [];
  for (const raw of list) {
    if (!raw || typeof raw !== "object") continue;
    const tagId = normalize(raw.tag_id || raw.tagId);
    if (!tagId || seen.has(tagId)) continue;
    seen.add(tagId);
    out.push({
      tag_id: tagId,
      w_manual: normalizeManualWeight(raw.w_manual ?? raw.wManual, DEFAULT_WEIGHT)
    });
  }
  out.sort(compareAssignmentRows);
  return out;
}

function equalAssignmentRows(left, right) {
  const a = normalizeAssignmentRows(left);
  const b = normalizeAssignmentRows(right);
  if (a.length !== b.length) return false;
  for (let index = 0; index < a.length; index += 1) {
    if (a[index].tag_id !== b[index].tag_id) return false;
    if (a[index].w_manual !== b[index].w_manual) return false;
  }
  return true;
}

function buildPatchSnippet(seriesId, diff, timestamp) {
  if (!diff || !diff.changedWorkIds.length) return "";
  const setBlocks = diff.changedWorkIds
    .filter((workId) => diff.nextWorkStateById.has(workId))
    .map((workId) => {
      const tagsText = JSON.stringify(diff.nextWorkStateById.get(workId) || [], null, 2).replace(/\n/g, "\n      ");
      return [
        `${JSON.stringify(workId)}: {`,
        `  "tags": ${tagsText},`,
        `  "updated_at_utc": ${JSON.stringify(timestamp)}`,
        "}"
      ].join("\n");
    });
  const deleteWorkIds = diff.changedWorkIds.filter((workId) => !diff.nextWorkStateById.has(workId));
  return [
    setBlocks.length ? `Under series[${JSON.stringify(seriesId)}].works, set:\n${setBlocks.join("\n")}` : "",
    deleteWorkIds.length ? `Under series[${JSON.stringify(seriesId)}].works, delete: ${deleteWorkIds.map((workId) => JSON.stringify(workId)).join(", ")}` : "",
    "If the works object becomes empty, delete the works object too.",
    `Update series[${JSON.stringify(seriesId)}].updated_at_utc to ${JSON.stringify(timestamp)}.`,
    `Update the top-level updated_at_utc to ${JSON.stringify(timestamp)}.`
  ].filter(Boolean).join("\n\n");
}

function utcTimestamp() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
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
  return buildWorkStateDiff(state).changedWorkIds.length > 0;
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

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function normalizeWorkId(value) {
  const text = String(value || "").trim();
  if (!/^\d{1,5}$/.test(text)) return "";
  return text.padStart(5, "0");
}

function splitWorkInputTokens(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalizeAliasTargets(value) {
  const rawTargets = (value && typeof value === "object" && !Array.isArray(value))
    ? value.tags
    : value;

  if (Array.isArray(rawTargets)) {
    const out = [];
    const seen = new Set();
    for (const item of rawTargets) {
      const normalized = normalize(item);
      if (!normalized || seen.has(normalized)) continue;
      seen.add(normalized);
      out.push(normalized);
    }
    return out;
  }

  const single = normalize(rawTargets);
  return single ? [single] : [];
}

function normalizeAssignmentTags(rawTags) {
  if (!Array.isArray(rawTags)) return [];
  const out = [];
  const seen = new Set();
  for (const raw of rawTags) {
    if (typeof raw === "string") {
      const tagId = normalize(raw);
      if (!tagId || seen.has(tagId)) continue;
      seen.add(tagId);
      out.push({
        tagId,
        wManual: DEFAULT_WEIGHT
      });
      continue;
    }
    if (!raw || typeof raw !== "object") continue;
    const tagId = normalize(raw.tag_id);
    if (!tagId || seen.has(tagId)) continue;
    seen.add(tagId);
    out.push({
      tagId,
      wManual: normalizeManualWeight(raw.w_manual, DEFAULT_WEIGHT)
    });
  }
  return out;
}

function normalizeManualWeight(raw, fallback) {
  const value = typeof raw === "number" ? raw : Number(raw);
  if (!Number.isFinite(value)) return fallback;
  let closest = WEIGHT_VALUES[0];
  let diff = Math.abs(value - closest);
  for (const candidate of WEIGHT_VALUES) {
    const currentDiff = Math.abs(value - candidate);
    if (currentDiff < diff) {
      closest = candidate;
      diff = currentDiff;
    }
  }
  return closest;
}

function nextWeight(value) {
  const normalized = normalizeManualWeight(value, DEFAULT_WEIGHT);
  const index = WEIGHT_VALUES.indexOf(normalized);
  if (index < 0) return DEFAULT_WEIGHT;
  return WEIGHT_VALUES[(index + 1) % WEIGHT_VALUES.length];
}

function weightDotClass(weight) {
  const normalized = normalizeManualWeight(weight, DEFAULT_WEIGHT);
  if (normalized === 0.3) return "tagStudio__weightDot--low";
  if (normalized === 0.9) return "tagStudio__weightDot--high";
  return "tagStudio__weightDot--mid";
}

function groupFromTagId(tagId) {
  const normalized = normalize(tagId);
  const splitIndex = normalized.indexOf(":");
  return splitIndex >= 0 ? normalized.slice(0, splitIndex) : normalized;
}

function slugFromTagId(tagId) {
  const normalized = normalize(tagId);
  const splitIndex = normalized.indexOf(":");
  return splitIndex >= 0 ? normalized.slice(splitIndex + 1) : normalized;
}

function compareEntries(a, b) {
  if (b.wManual !== a.wManual) return b.wManual - a.wManual;
  return slugFromTagId(a.canonicalId).localeCompare(slugFromTagId(b.canonicalId), undefined, { sensitivity: "base" });
}

function compareTagDisplay(a, b) {
  const aIndex = GROUP_INDEX.has(a.group) ? GROUP_INDEX.get(a.group) : Number.MAX_SAFE_INTEGER;
  const bIndex = GROUP_INDEX.has(b.group) ? GROUP_INDEX.get(b.group) : Number.MAX_SAFE_INTEGER;
  if (aIndex !== bIndex) return aIndex - bIndex;
  return a.tagId.localeCompare(b.tagId);
}

function compareAssignmentRows(a, b) {
  const ga = groupFromTagId(a.tag_id);
  const gb = groupFromTagId(b.tag_id);
  const ia = GROUP_INDEX.has(ga) ? GROUP_INDEX.get(ga) : Number.MAX_SAFE_INTEGER;
  const ib = GROUP_INDEX.has(gb) ? GROUP_INDEX.get(gb) : Number.MAX_SAFE_INTEGER;
  if (ia !== ib) return ia - ib;
  if (b.w_manual !== a.w_manual) return b.w_manual - a.w_manual;
  return slugFromTagId(a.tag_id).localeCompare(slugFromTagId(b.tag_id), undefined, { sensitivity: "base" });
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

function studioText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tag_editor.${key}`, fallback, tokens);
}

function buildSaveModeText(state, mode) {
  const label = mode === "post"
    ? studioText(state.config, "save_mode_local_server", "Local server")
    : studioText(state.config, "save_mode_patch", "Patch");
  return studioText(state.config, "save_mode_template", "Save mode: {mode}", { mode: label });
}

function buildSaveSuccessMessage(state, savedCount, removedCount, savedAt) {
  const base = studioText(
    state.config,
    "save_status_success_base",
    "Saved {saved_count} work row{saved_plural}",
    {
      saved_count: savedCount,
      saved_plural: savedCount === 1 ? "" : "s"
    }
  );
  const removed = removedCount > 0
    ? studioText(
        state.config,
        "save_status_success_removed_suffix",
        "; removed {removed_count} row{removed_plural}",
        {
          removed_count: removedCount,
          removed_plural: removedCount === 1 ? "" : "s"
        }
      )
    : "";
  const at = studioText(
    state.config,
    "save_status_success_at_suffix",
    " at {saved_at}.",
    { saved_at: savedAt }
  );
  return `${base}${removed}${at}`;
}
