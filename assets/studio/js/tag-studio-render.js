import {
  getStudioText
} from "./studio-config.js";
import {
  compareEntries,
  makeResolvedEntry,
  normalize,
  normalizeAssignmentRows,
  normalizeManualWeight,
  normalizeWorkId
} from "./tag-studio-domain.js";
import {
  seriesTagEditorUi
} from "./studio-ui.js";

const DEFAULT_STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const DEFAULT_WEIGHT = 0.6;
const UI = seriesTagEditorUi;
const { className: UI_CLASS, state: UI_STATE } = UI;

export function renderSelectedWork(state) {
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

export function renderContextHint(state) {
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

export function renderGroups(state) {
  const studioGroups = getStudioGroups(state);
  const inheritedByGroup = new Map(studioGroups.map((group) => [group, []]));
  for (const entry of state.seriesEntries) {
    if (!inheritedByGroup.has(entry.group)) continue;
    inheritedByGroup.get(entry.group).push(entry);
  }
  const showOfflineMarkers = state.saveMode !== "post";
  const seriesMarkerState = showOfflineMarkers
    ? buildEntryMarkerState(state, state.seriesEntries, state.offlineBaseSeriesRow && state.offlineBaseSeriesRow.tags, "series")
    : createEmptyMarkerState();
  const inheritedDeletedByGroup = new Map(studioGroups.map((group) => [group, []]));
  for (const entry of seriesMarkerState.deleted) {
    if (!inheritedDeletedByGroup.has(entry.group)) continue;
    inheritedDeletedByGroup.get(entry.group).push(entry);
  }

  const overrideByGroup = new Map(studioGroups.map((group) => [group, []]));
  for (const entry of getSelectedWorkEntries(state)) {
    if (!overrideByGroup.has(entry.group)) continue;
    overrideByGroup.get(entry.group).push(entry);
  }
  const selectedWorkId = state.selectedWorkId;
  const overrideMarkerState = showOfflineMarkers && selectedWorkId
    ? buildEntryMarkerState(state, getSelectedWorkEntries(state), getOfflineBaseWorkRows(state, selectedWorkId), `work:${selectedWorkId}`)
    : createEmptyMarkerState();
  const overrideDeletedByGroup = new Map(studioGroups.map((group) => [group, []]));
  for (const entry of overrideMarkerState.deleted) {
    if (!overrideDeletedByGroup.has(entry.group)) continue;
    overrideDeletedByGroup.get(entry.group).push(entry);
  }

  for (const group of studioGroups) {
    inheritedByGroup.get(group).sort(compareEntries);
    inheritedDeletedByGroup.get(group).sort(compareEntries);
    overrideByGroup.get(group).sort(compareEntries);
    overrideDeletedByGroup.get(group).sort(compareEntries);
  }

  const rowsHtml = studioGroups.map((group) => {
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

function getStudioGroups(state) {
  return Array.isArray(state && state.studioGroups) && state.studioGroups.length
    ? state.studioGroups
    : DEFAULT_STUDIO_GROUPS;
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

function buildEntryRow(state, entry) {
  if (!entry || !entry.canonicalId) return null;
  const row = {
    tag_id: normalize(entry.canonicalId),
    w_manual: normalizeManualWeight(entry.wManual, stateDefaultWeight(state))
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
    const currentRow = buildEntryRow(state, entry);
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
        class="${classNames(UI_CLASS.weightDot, weightDotClass(state, entry.wManual))}"
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
        <span class="${classNames(UI_CLASS.weightDot, weightDotClass(state, entry.wManual))}" aria-hidden="true"></span>
        ${renderChipLabel(state, entry, marker)}
      </span>
    `;
  }
  return `
    <span class="${classNames(UI_CLASS.chip, UI_CLASS.chipInherited)}" title="${escapeHtml(studioText(state.config, "inherited_tag_title", "Inherited from series: {tag_id}", { tag_id: entry.canonicalId }))}">
      <span class="${classNames(UI_CLASS.weightDot, weightDotClass(state, entry.wManual))}" aria-hidden="true"></span>
      ${renderChipLabel(state, entry, marker)}
    </span>
  `;
}

function renderOverrideChip(state, entry, marker = "") {
  return `
    <span class="${classNames(UI_CLASS.chip, chipGroupClass(entry.group))}" title="${escapeHtml(studioText(state.config, "work_override_title", "Work override {tag_id}", { tag_id: entry.canonicalId }))}">
      <button
        type="button"
        class="${classNames(UI_CLASS.weightDot, weightDotClass(state, entry.wManual))}"
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
      <span class="${classNames(UI_CLASS.weightDot, weightDotClass(state, entry.wManual))}" aria-hidden="true"></span>
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

function getSelectedWorkEntries(state) {
  if (!state.selectedWorkId) return [];
  return state.workEntriesById.get(state.selectedWorkId) || [];
}

function getOrderedSelectedWorkOptions(state) {
  const selected = new Set(state.selectedWorkIds);
  return state.seriesWorkOptions.filter((item) => selected.has(item.workId));
}

function stateDefaultWeight(state) {
  return Number.isFinite(state && state.defaultWeight) ? state.defaultWeight : DEFAULT_WEIGHT;
}

function weightDotClass(state, weight) {
  const normalized = normalizeManualWeight(weight, stateDefaultWeight(state));
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

function classNames(...tokens) {
  return tokens.filter(Boolean).join(" ");
}

function chipGroupClass(group) {
  return `${UI_CLASS.chipGroupPrefix}${group}`;
}

function studioText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tag_editor.${key}`, fallback, tokens);
}
