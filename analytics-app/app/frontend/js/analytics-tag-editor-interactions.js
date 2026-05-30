import {
  makeResolvedEntry,
  nextWeight,
  normalize,
  normalizeAssignmentRows,
  normalizeWorkId,
  splitWorkInputTokens
} from "./analytics-tag-editor-domain.js";
import {
  buildStateDiff,
  getOrderedSelectedWorkIds,
  writeSelectionToQuery
} from "./analytics-tag-editor-state.js";

const DEFAULT_WEIGHT = 0.6;

export function selectAnalyticsTagEditorWorkFromInput(state, options = {}) {
  const rawInput = String(state.refs.workInput.value || "").trim();
  if (!rawInput) {
    setInteractionStatus(state, options, "warn", text(options, "work_input_required", "Enter a work_id from this series."));
    renderStatus(options, state);
    return;
  }

  const tokens = splitWorkInputTokens(rawInput);
  if (tokens.length > 1 || rawInput.includes(",")) {
    addAnalyticsTagEditorWorksFromTokens(state, tokens, options);
    return;
  }

  const normalizedWorkId = normalizeWorkId(rawInput);
  const matches = getMatchingWorkOptions(state, rawInput, options);
  if (!matches.length) {
    setInteractionStatus(state, options, "error", text(
      options,
      "work_unknown_error",
      "Unknown work_id for this series: \"{input}\".",
      { input: rawInput }
    ));
    renderStatus(options, state);
    return;
  }

  const exact = normalizedWorkId ? matches.find((item) => item.workId === normalizedWorkId) : null;
  if (exact) {
    addAnalyticsTagEditorWorkSelection(state, exact.workId, true, options);
    return;
  }

  if (matches.length === 1) {
    addAnalyticsTagEditorWorkSelection(state, matches[0].workId, true, options);
    return;
  }

  setInteractionStatus(state, options, "warn", text(
    options,
    "work_multiple_matches",
    "Multiple works match \"{input}\". Choose one from the popup.",
    { input: rawInput }
  ));
  renderStatus(options, state);
  renderWorkPopup(options, state);
}

export function addAnalyticsTagEditorWorksFromTokens(state, tokens, options = {}) {
  if (!tokens.length) {
    setInteractionStatus(state, options, "warn", text(options, "work_input_required_multiple", "Enter at least one work_id from this series."));
    renderStatus(options, state);
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
    if (addAnalyticsTagEditorWorkSelection(state, workId, false, options)) {
      added.push(workId);
    }
  }

  if (added.length) {
    activateAnalyticsTagEditorSelectedWork(state, added[added.length - 1], { ...options, render: false });
  }
  state.refs.workInput.value = "";
  hideWorkPopup(options, state);
  setSaveResult(options, state, "", "");

  const messageParts = buildWorkSelectionSummary(state, added, unknown, invalid, options);
  const kind = (unknown.length || invalid.length) ? (added.length ? "warn" : "error") : "success";
  setInteractionStatus(state, options, kind, messageParts.join(" "));
  renderAll(options, state);
}

export function addAnalyticsTagEditorWorkSelection(state, workId, activate = true, options = {}) {
  if (!state.seriesWorkIds.has(workId)) {
    setInteractionStatus(state, options, "error", text(
      options,
      "work_not_in_series_error",
      "Work {work_id} is not in this series.",
      { work_id: workId }
    ));
    renderStatus(options, state);
    return false;
  }

  if (!state.selectedWorkIds.includes(workId)) {
    state.selectedWorkIds.push(workId);
  }
  if (!state.workEntriesById.has(workId)) {
    state.workEntriesById.set(workId, []);
  }
  if (activate) {
    activateAnalyticsTagEditorSelectedWork(state, workId, { ...options, render: false });
    setInteractionStatus(state, options, "success", text(
      options,
      "work_selected_success",
      "Selected work {work_id}.",
      { work_id: workId }
    ));
  }
  writeSelectionToQuery(state);
  state.refs.workInput.value = "";
  hideWorkPopup(options, state);
  setSaveResult(options, state, "", "");
  renderAll(options, state);
  return true;
}

export function activateAnalyticsTagEditorSelectedWork(state, workId, options = {}) {
  if (workId && !state.selectedWorkIds.includes(workId)) return;
  state.selectedWorkId = workId;
  writeSelectionToQuery(state);
  if (options.render !== false) renderAll(options, state);
}

export function clearAnalyticsTagEditorSelectedWork(state, workId, options = {}) {
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
  hideWorkPopup(options, state);
  hidePopup(options, state);
  setInteractionStatus(state, options, "", "");
  setSaveResult(options, state, "", "");
  renderAll(options, state);
}

export function addAnalyticsTagEditorTagFromInput(state, options = {}) {
  const rawInput = String(state.refs.input.value || "").trim();
  if (!rawInput) {
    setInteractionStatus(state, options, "warn", text(options, "tag_input_required", "Enter a tag slug, tag id, or alias."));
    renderStatus(options, state);
    return;
  }

  const resolved = resolveAnalyticsTagEditorInput(rawInput, state);
  if (resolved.type === "resolved") {
    addAnalyticsTagEditorResolvedTag(state, resolved.tag, { rawInput }, options);
    state.refs.input.value = "";
    hidePopup(options, state);
    renderAll(options, state);
    return;
  }

  if (resolved.type === "ambiguous") {
    const candidateIds = resolved.candidates.map((tag) => tag.tag_id).slice(0, 6);
    const suffix = resolved.candidates.length > 6 ? ", ..." : "";
    setInteractionStatus(state, options, "warn", text(
      options,
      "tag_multiple_matches",
      "Multiple matches for \"{input}\": {candidate_ids}{suffix}. Choose one from autocomplete.",
      {
        input: rawInput,
        candidate_ids: candidateIds.join(", "),
        suffix
      }
    ));
    renderStatus(options, state);
    return;
  }

  setInteractionStatus(state, options, "error", text(
    options,
    "tag_unknown_error",
    "Unknown tag: \"{input}\".",
    { input: rawInput }
  ));
  renderStatus(options, state);
}

export function resolveAnalyticsTagEditorInput(rawInput, state) {
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

export function addAnalyticsTagEditorResolvedTag(state, tag, inputOptions = {}, interactionOptions = {}) {
  if (!tag || !tag.tag_id) return;
  const rawInput = typeof inputOptions === "string"
    ? inputOptions
    : String(inputOptions.rawInput || "").trim();
  const alias = typeof inputOptions === "object" && inputOptions
    ? normalize(inputOptions.alias)
    : "";

  const tagId = normalize(tag.tag_id);
  const isSeriesScope = !state.selectedWorkId;
  const inheritedTagIds = getAnalyticsTagEditorSeriesTagIdSet(state);
  if (!isSeriesScope && inheritedTagIds.has(tagId)) {
    setInteractionStatus(state, interactionOptions, "warn", text(
      interactionOptions,
      "tag_inherited_warning",
      "Inherited from series already: {tag_id}.",
      { tag_id: tagId }
    ));
    return;
  }

  const entries = getAnalyticsTagEditorEditableEntries(state);
  const alreadyExists = entries.some((entry) => entry.canonicalId === tagId);
  if (alreadyExists) {
    setInteractionStatus(state, interactionOptions, "warn", text(
      interactionOptions,
      isSeriesScope ? "tag_already_added_warning_series" : "tag_already_added_warning",
      isSeriesScope ? "Already added to series: {tag_id}." : "Already added for {work_id}: {tag_id}.",
      isSeriesScope ? { tag_id: tagId } : {
        work_id: state.selectedWorkId,
        tag_id: tagId
      }
    ));
    return;
  }

  entries.push(makeResolvedEntry(nextAnalyticsTagEditorEntryId(state), rawInput, tag, stateDefaultWeight(state), alias));
  setInteractionStatus(state, interactionOptions, "success", text(
    interactionOptions,
    isSeriesScope ? "series_tag_added_success" : "tag_added_success",
    isSeriesScope ? "Added {tag_id} to series tags." : "Added {tag_id} to {work_id}.",
    isSeriesScope ? { tag_id: tagId } : {
      work_id: state.selectedWorkId,
      tag_id: tagId
    }
  ));
  setSaveResult(interactionOptions, state, "", "");
}

export function cycleAnalyticsTagEditorEntryWeight(state, entryId, options = {}) {
  const entry = getAnalyticsTagEditorEditableEntries(state).find((item) => item.entryId === entryId);
  if (!entry) return false;
  entry.wManual = nextWeight(entry.wManual);
  setInteractionStatus(
    state,
    options,
    "success",
    text(
      options,
      "weight_updated",
      "Updated {tag_id} w_manual to {weight}.",
      {
        tag_id: entry.canonicalId,
        weight: entry.wManual.toFixed(1)
      }
    )
  );
  setSaveResult(options, state, "", "");
  renderAll(options, state);
  return true;
}

export function removeAnalyticsTagEditorEditableEntry(state, entryId, options = {}) {
  const entries = getAnalyticsTagEditorEditableEntries(state);
  const sizeBefore = entries.length;
  const nextEntries = entries.filter((entry) => entry.entryId !== entryId);
  if (state.selectedWorkId) {
    state.workEntriesById.set(state.selectedWorkId, nextEntries);
  } else {
    state.seriesEntries = nextEntries;
  }
  if (nextEntries.length < sizeBefore) {
    setInteractionStatus(
      state,
      options,
      "success",
      text(
        options,
        state.selectedWorkId ? "work_tag_removed" : "series_tag_removed",
        state.selectedWorkId ? "Work tag removed." : "Series tag removed."
      )
    );
    setSaveResult(options, state, "", "");
  }
}

export function restoreAnalyticsTagEditorDeletedEntry(state, rawTagId, rawScope, options = {}) {
  const tagId = normalize(rawTagId);
  const scope = String(rawScope || "").trim().toLowerCase();
  if (!tagId) return;

  const tag = state.tagsById.get(tagId);
  if (!tag) return;

  if (scope === "work") {
    if (!state.selectedWorkId) return;
    if (getAnalyticsTagEditorSeriesTagIdSet(state).has(tagId)) {
      setInteractionStatus(
        state,
        options,
        "warn",
        text(
          options,
          "work_tag_restore_inherited_warning",
          "Cannot restore {tag_id} while it is inherited from the series.",
          { tag_id: tagId }
        )
      );
      setSaveResult(options, state, "", "");
      return;
    }

    const entries = getSelectedAnalyticsTagEditorWorkEntries(state);
    if (entries.some((entry) => entry.canonicalId === tagId)) return;
    const baseRow = getOfflineBaseWorkRows(state, state.selectedWorkId).find((row) => row.tag_id === tagId);
    if (!baseRow) return;
    entries.push(makeResolvedEntry(nextAnalyticsTagEditorEntryId(state), tagId, tag, baseRow.w_manual, baseRow.alias));
    setInteractionStatus(
      state,
      options,
      "success",
      text(options, "work_tag_restored", "Work tag restored.")
    );
    setSaveResult(options, state, "", "");
    return;
  }

  if (state.seriesEntries.some((entry) => entry.canonicalId === tagId)) return;
  const baseRow = normalizeAssignmentRows(state.offlineBaseSeriesRow && state.offlineBaseSeriesRow.tags)
    .find((row) => row.tag_id === tagId);
  if (!baseRow) return;
  state.seriesEntries.push(makeResolvedEntry(nextAnalyticsTagEditorEntryId(state), tagId, tag, baseRow.w_manual, baseRow.alias));
  setInteractionStatus(
    state,
    options,
    "success",
    text(options, "series_tag_restored", "Series tag restored.")
  );
  setSaveResult(options, state, "", "");
}

export function applyAnalyticsTagEditorSaveState(state, options = {}) {
  const projection = projectAnalyticsTagEditorSaveState(state, options);
  state.refs.input.disabled = projection.inputDisabled;
  state.refs.addButton.disabled = projection.addButtonDisabled;
  state.refs.saveButton.disabled = projection.saveButtonDisabled;
  state.refs.saveWarning.textContent = projection.warningText;
  return projection;
}

export function projectAnalyticsTagEditorSaveState(state, options = {}) {
  const metrics = computeAnalyticsTagEditorMetrics(state);
  const hasSelectedWork = Boolean(state.selectedWorkId);
  const diff = buildStateDiff(state);
  const isDirty = diff.seriesChanged || diff.changedWorkIds.length > 0;
  const warningText = projectSaveWarningText(state, {
    hasSelectedWork,
    isDirty,
    unresolvedCount: metrics.unresolvedCount
  }, options);

  return {
    metrics,
    diff,
    hasSelectedWork,
    isDirty,
    inputDisabled: false,
    addButtonDisabled: false,
    saveButtonDisabled: !isDirty || metrics.unresolvedCount > 0,
    warningText
  };
}

export function computeAnalyticsTagEditorMetrics(_state) {
  return { unresolvedCount: 0 };
}

export function getAnalyticsTagEditorEditableEntries(state) {
  if (!state.selectedWorkId) return state.seriesEntries;
  return getSelectedAnalyticsTagEditorWorkEntries(state);
}

export function getSelectedAnalyticsTagEditorWorkEntries(state) {
  if (!state.selectedWorkId) return [];
  return state.workEntriesById.get(state.selectedWorkId) || [];
}

export function getAnalyticsTagEditorSeriesTagIdSet(state) {
  const out = new Set();
  for (const entry of state.seriesEntries) {
    out.add(entry.canonicalId);
  }
  return out;
}

export function nextAnalyticsTagEditorEntryId(state) {
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

function projectSaveWarningText(state, projection, options) {
  if (!projection.hasSelectedWork && projection.isDirty) {
    return text(
      options,
      "save_warning_pending_diff",
      "Save to persist the current tag assignment diff."
    );
  }
  return projection.unresolvedCount > 0
    ? text(options, "save_warning_unresolved", "Resolve unknown tags before saving.")
    : "";
}

function stateDefaultWeight(state) {
  const value = Number(state && state.defaultWeight);
  return Number.isFinite(value) ? value : DEFAULT_WEIGHT;
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

function buildWorkSelectionSummary(state, added, unknown, invalid, options) {
  const parts = [];
  if (added.length) {
    parts.push(text(
      options,
      "work_summary_added",
      "Added {count} work{plural}.",
      {
        count: added.length,
        plural: added.length === 1 ? "" : "s"
      }
    ));
  }
  if (unknown.length) {
    parts.push(text(
      options,
      "work_summary_not_in_series",
      "Not in this series: {list}.",
      { list: unknown.join(", ") }
    ));
  }
  if (invalid.length) {
    parts.push(text(
      options,
      "work_summary_invalid",
      "Invalid work_id: {list}.",
      { list: invalid.join(", ") }
    ));
  }
  return parts;
}

function setInteractionStatus(state, options, kind, message) {
  if (typeof options.setStatus === "function") {
    options.setStatus(state, kind, message);
    return;
  }
  state.statusKind = kind || "";
  state.statusText = message || "";
}

function text(options, key, fallback, tokens) {
  return typeof options.text === "function"
    ? options.text(key, fallback, tokens)
    : fallback;
}

function getMatchingWorkOptions(state, rawInput, options) {
  return typeof options.getMatchingWorkOptions === "function"
    ? options.getMatchingWorkOptions(state, rawInput)
    : [];
}

function renderStatus(options, state) {
  if (typeof options.renderStatus === "function") options.renderStatus(state);
}

function renderAll(options, state) {
  if (typeof options.renderAll === "function") options.renderAll(state);
}

function renderWorkPopup(options, state) {
  if (typeof options.renderWorkPopup === "function") options.renderWorkPopup(state);
}

function hidePopup(options, state) {
  if (typeof options.hidePopup === "function") options.hidePopup(state);
}

function hideWorkPopup(options, state) {
  if (typeof options.hideWorkPopup === "function") options.hideWorkPopup(state);
}

function setSaveResult(options, state, kind, message) {
  if (typeof options.setSaveResult === "function") options.setSaveResult(state, kind, message);
}
