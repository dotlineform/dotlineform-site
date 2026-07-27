import {
  getStudioText
} from "./studio-config.js";
import {
  compareEntries,
  normalizeManualWeight
} from "./analytics-tag-editor-domain.js";
import {
  seriesTagEditorUi
} from "./tag-ui.js";

const DEFAULT_ANALYTICS_GROUPS = ["subject", "domain", "form", "theme"];
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
          aria-label="${escapeHtml(analyticsTagEditorText(state.config, "remove_selected_work_aria_label", "Remove selected work {work_id}", { work_id: item.workId }))}"
        >x</button>
      </span>
    `;
  }).join("");
}

export function renderContextHint(state) {
  if (!state.refs.contextHint) return;
  if (!state.selectedWorkId) {
    state.refs.contextHint.textContent = analyticsTagEditorText(
      state.config,
      "context_hint_default",
      "No work selected: edit series tags directly. Select a work to switch to work-only overrides."
    );
    return;
  }
  state.refs.contextHint.textContent = analyticsTagEditorText(
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

  const overrideByGroup = new Map(studioGroups.map((group) => [group, []]));
  for (const entry of getSelectedWorkEntries(state)) {
    if (!overrideByGroup.has(entry.group)) continue;
    overrideByGroup.get(entry.group).push(entry);
  }
  const selectedWorkId = state.selectedWorkId;

  for (const group of studioGroups) {
    inheritedByGroup.get(group).sort(compareEntries);
    overrideByGroup.get(group).sort(compareEntries);
  }

  const rowsHtml = studioGroups.map((group) => {
    const inherited = inheritedByGroup.get(group) || [];
    const overrides = overrideByGroup.get(group) || [];
    const inheritedHtml = selectedWorkId
      ? inherited.map((entry) => renderInheritedChip(state, entry)).join("")
      : inherited.map((entry) => renderSeriesEditableChip(state, entry)).join("");
    const overrideHtml = overrides
      .map((entry) => renderOverrideChip(state, entry))
      .join("");
    const emptyHtml = (!inheritedHtml && !overrideHtml)
      ? `<span class="${UI_CLASS.empty}">${escapeHtml(analyticsTagEditorText(state.config, "empty_state", "none"))}</span>`
      : "";
    return `
      <div class="${UI_CLASS.groupRow}">
        <span class="${classNames(UI_CLASS.groupRowLabel, UI_CLASS.chip, chipGroupClass(group))}">${escapeHtml(group)}</span>
        <div class="${UI_CLASS.groupRowChips}">
          ${inheritedHtml}
          ${overrideHtml}
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
    : DEFAULT_ANALYTICS_GROUPS;
}

function renderChipLabel(entry) {
  return `
    <span class="${UI_CLASS.chipText}">
      <span class="${UI_CLASS.chipTag}">${escapeHtml(entry.label)}</span>
    </span>
  `;
}

function renderSeriesEditableChip(state, entry) {
  return `
    <span class="${classNames(UI_CLASS.chip, chipGroupClass(entry.group))}" title="${escapeHtml(analyticsTagEditorText(state.config, "series_tag_title", "Series tag {tag_id}", { tag_id: entry.canonicalId }))}">
      <button
        type="button"
        class="${classNames(UI_CLASS.weightDot, weightDotClass(state, entry.wManual))}"
        data-cycle-weight-entry-id="${entry.entryId}"
        title="${escapeHtml(analyticsTagEditorText(state.config, "weight_button_title", "w_manual {weight}", { weight: entry.wManual.toFixed(1) }))}"
        aria-label="${escapeHtml(analyticsTagEditorText(state.config, "weight_button_aria_label", "w_manual {weight}", { weight: entry.wManual.toFixed(1) }))}"
      ></button>
      ${renderChipLabel(entry)}
      <button
        type="button"
        class="${UI_CLASS.chipRemove}"
        data-remove-entry-id="${entry.entryId}"
        aria-label="${escapeHtml(analyticsTagEditorText(state.config, "remove_series_tag_aria_label", "Remove {tag_id}", { tag_id: entry.canonicalId }))}"
      >x</button>
    </span>
  `;
}

function renderInheritedChip(state, entry) {
  return `
    <span class="${classNames(UI_CLASS.chip, UI_CLASS.chipInherited)}" title="${escapeHtml(analyticsTagEditorText(state.config, "inherited_tag_title", "Inherited from series: {tag_id}", { tag_id: entry.canonicalId }))}">
      <span class="${classNames(UI_CLASS.weightDot, weightDotClass(state, entry.wManual))}" aria-hidden="true"></span>
      ${renderChipLabel(entry)}
    </span>
  `;
}

function renderOverrideChip(state, entry) {
  return `
    <span class="${classNames(UI_CLASS.chip, chipGroupClass(entry.group))}" title="${escapeHtml(analyticsTagEditorText(state.config, "work_override_title", "Work override {tag_id}", { tag_id: entry.canonicalId }))}">
      <button
        type="button"
        class="${classNames(UI_CLASS.weightDot, weightDotClass(state, entry.wManual))}"
        data-cycle-weight-entry-id="${entry.entryId}"
        title="${escapeHtml(analyticsTagEditorText(state.config, "weight_button_title", "w_manual {weight}", { weight: entry.wManual.toFixed(1) }))}"
        aria-label="${escapeHtml(analyticsTagEditorText(state.config, "weight_button_aria_label", "w_manual {weight}", { weight: entry.wManual.toFixed(1) }))}"
      ></button>
      ${renderChipLabel(entry)}
      <button
        type="button"
        class="${UI_CLASS.chipRemove}"
        data-remove-entry-id="${entry.entryId}"
        aria-label="${escapeHtml(analyticsTagEditorText(state.config, "remove_work_tag_aria_label", "Remove {tag_id}", { tag_id: entry.canonicalId }))}"
      >x</button>
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

function analyticsTagEditorText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tag_editor.${key}`, fallback, tokens);
}
