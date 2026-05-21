import {
  getStudioText
} from "./studio-config.js";
import {
  buildStudioTagScore
} from "./analysis-tag-scoring.js";
import {
  normalizeOfflineSeriesRow
} from "./tag-assignments-offline.js";
import {
  seriesTagsUi
} from "./studio-ui.js";

const DEFAULT_STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const UI = seriesTagsUi;
const { className: UI_CLASS, state: UI_STATE } = UI;

export function renderSeriesTagsReport(state) {
  const rowsHtml = buildSeriesTagsRows(state).map((row) => {
    const chips = row.visibleTags.length
      ? row.visibleTags.map((tag) => renderTagChip(state, tag)).join("")
      : "";

    return `
      <li class="tagStudioList__row seriesTags__row">
        <div class="seriesTags__col seriesTags__col--title">
          <a href="${escapeHtml(row.url)}">${escapeHtml(row.title)}</a>
        </div>
        <div class="seriesTags__col seriesTags__col--count">
          <span class="tagStudioIndex__statusWrap">
            <span class="rag rag--${escapeHtml(row.rag)}" title="${escapeHtml(row.tooltip)}" aria-label="${escapeHtml(row.ragLabel)}"></span>
          </span>
        </div>
        <div class="seriesTags__col seriesTags__col--tags">
          <ul class="seriesTags__chipList">${chips}</ul>
        </div>
      </li>
    `;
  }).join("");

  state.refs.mount.innerHTML = `
    <div class="seriesTags">
      ${renderFilters(state)}
      <div class="tagStudioList__head seriesTags__head">
        <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="series"${stateAttr(state.sortKey === "series" ? UI_STATE.active : "")}>
          ${escapeHtml(seriesTagsText(state.config, "table_heading_series", "series"))}${sortIndicator(state, "series")}
        </button>
        <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="status"${stateAttr(state.sortKey === "status" ? UI_STATE.active : "")}>
          ${escapeHtml(seriesTagsText(state.config, "table_heading_status", "status"))}${sortIndicator(state, "status")}
        </button>
        <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="tags"${stateAttr(state.sortKey === "tags" ? UI_STATE.active : "")}>
          ${escapeHtml(seriesTagsText(state.config, "table_heading_tags", "tags"))}${sortIndicator(state, "tags")}
        </button>
      </div>
      <ul class="tagStudioList__rows seriesTags__rows">${rowsHtml}</ul>
    </div>
  `;
}

export function buildSeriesTagsRows(state) {
  return state.seriesData
    .map((series) => {
      const repoRow = normalizeRepoSeriesRow(state.assignmentsSeries, series.seriesId);
      const offlineEntry = state.offlineSession.series && state.offlineSession.series[series.seriesId]
        ? state.offlineSession.series[series.seriesId]
        : null;
      const effectiveRow = offlineEntry ? normalizeOfflineSeriesRow(offlineEntry.staged_row) : repoRow;
      const assigned = effectiveRow.tags.map((row) => row.tag_id);
      const score = buildStudioTagScore(assigned, state.registry, state.config);
      const tags = buildSeriesDisplayTags(state, repoRow, effectiveRow)
        .sort((a, b) => compareText(a.sortLabel, b.sortLabel));
      const visibleTags = state.filterGroup === "all"
        ? tags
        : tags.filter((tag) => tag.group === state.filterGroup);
      return {
        ...series,
        rag: score.rag,
        ragRank: score.ragRank,
        tooltip: score.tooltip,
        ragLabel: score.ragLabel,
        visibleTags,
        tagsSortKey: visibleTags.map((tag) => `${tag.sortLabel}:${tag.marker || ""}`).join(" | ")
      };
    })
    .sort((left, right) => compareSeriesRows(state, left, right));
}

function buildSeriesDisplayTags(state, repoRow, effectiveRow) {
  const repoTags = new Map(repoRow.tags.map((row) => [row.tag_id, row]));
  const effectiveTags = new Map(effectiveRow.tags.map((row) => [row.tag_id, row]));
  const tagIds = Array.from(new Set([...repoTags.keys(), ...effectiveTags.keys()]));
  const display = [];

  for (const tagId of tagIds) {
    const repoTag = repoTags.get(tagId) || null;
    const effectiveTag = effectiveTags.get(tagId) || null;
    if (!repoTag && effectiveTag) {
      display.push(toTagDisplay(tagId, state.registry, "local"));
      continue;
    }
    if (repoTag && !effectiveTag) {
      display.push(toTagDisplay(tagId, state.registry, "delete"));
      continue;
    }
    if (repoTag && effectiveTag) {
      const marker = equalNormalizedAssignmentTag(repoTag, effectiveTag) ? "" : "local";
      display.push(toTagDisplay(tagId, state.registry, marker));
    }
  }

  return display;
}

function renderTagChip(state, tag) {
  const caption = tag.marker
    ? `<span class="${classNames(UI_CLASS.chipCaption, tag.marker === "delete" ? UI_CLASS.chipCaptionDelete : UI_CLASS.chipCaptionLocal)}">${escapeHtml(seriesTagsText(
      state.config,
      tag.marker === "delete" ? "chip_caption_delete" : "chip_caption_local",
      tag.marker
    ))}</span>`
    : "";
  return `
    <li class="${classNames(UI_CLASS.chip, tag.className)}" title="${escapeHtml(tag.tagId)}">
      <span class="${UI_CLASS.chipText}">
        <span class="${classNames(
          UI_CLASS.chipTag,
          tag.marker === "local" ? UI_CLASS.chipTagLocal : "",
          tag.marker === "delete" ? UI_CLASS.chipTagDelete : ""
        )}">${escapeHtml(tag.label)}</span>
        ${caption}
      </span>
    </li>
  `;
}

function renderFilters(state) {
  const groupButtons = getStudioGroups(state).map((group) => {
    const titleAttr = groupTitleAttr(state, group);
    return `
      <button
        type="button"
        class="${classNames(UI_CLASS.keyPill, chipGroupClass(group), UI_CLASS.groupFilterButton)}"
        data-group="${escapeHtml(group)}"
        ${stateAttr(state.filterGroup === group ? UI_STATE.active : "")}
        ${titleAttr}
      >
        ${escapeHtml(group)}
      </button>
    `;
  }).join("");

  return `
    <div class="${UI_CLASS.filters}">
      <button type="button" class="tagStudio__button ${UI_CLASS.allFilterButton}" data-group="all"${stateAttr(state.filterGroup === "all" ? UI_STATE.active : "")}>${escapeHtml(seriesTagsText(state.config, "filter_all_tags", "All tags"))}</button>
      ${groupButtons}
      ${renderGroupInfoControl(state)}
    </div>
  `;
}

function getStudioGroups(state) {
  return Array.isArray(state && state.studioGroups) && state.studioGroups.length
    ? state.studioGroups
    : DEFAULT_STUDIO_GROUPS;
}

function groupTitleAttr(state, group) {
  const descriptions = state.groupDescriptions instanceof Map ? state.groupDescriptions : new Map();
  const description = String(descriptions.get(group) || "").trim();
  return description ? `title="${escapeHtml(description)}"` : "";
}

function renderGroupInfoControl(state) {
  const href = state.groupInfoPagePath || "";
  if (!href) return "";
  return `
    <a
      class="${UI_CLASS.keyInfoButton}"
      href="${escapeHtml(href)}"
      target="_blank"
      rel="noopener"
      title="${escapeHtml(seriesTagsText(state.config, "group_info_title", "Open group descriptions in a new tab"))}"
      aria-label="${escapeHtml(seriesTagsText(state.config, "group_info_aria_label", "Open group descriptions in a new tab"))}"
    >i</a>
  `;
}

function compareSeriesRows(state, left, right) {
  if (state.sortKey === "status") {
    if (left.ragRank !== right.ragRank) {
      return compareDir(left.ragRank, right.ragRank, state.sortDir);
    }
    return compareDir(left.title, right.title, state.sortDir, compareText);
  }
  if (state.sortKey === "tags") {
    const byTags = compareDir(left.tagsSortKey, right.tagsSortKey, state.sortDir, compareText);
    if (byTags !== 0) return byTags;
    return compareText(left.title, right.title);
  }
  return compareDir(left.title, right.title, state.sortDir, compareText);
}

function compareDir(left, right, dir, compareFn = compareBasic) {
  const value = compareFn(left, right);
  return dir === "desc" ? value * -1 : value;
}

function compareBasic(left, right) {
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

function compareText(left, right) {
  return String(left || "").localeCompare(String(right || ""), undefined, { sensitivity: "base" });
}

function toTagDisplay(tagId, registry, marker = "") {
  const record = registry.get(tagId);
  const group = record && record.group ? record.group : tagId.split(":", 1)[0];
  const label = record && record.label ? record.label : tagId;
  return {
    tagId,
    group,
    label,
    marker,
    className: chipGroupClass(group),
    sortLabel: `${label} ${tagId}`
  };
}

function normalizeRepoSeriesRow(assignmentsSeries, seriesId) {
  const row = assignmentsSeries && assignmentsSeries[seriesId] ? assignmentsSeries[seriesId] : null;
  return normalizeOfflineSeriesRow(row);
}

function equalNormalizedAssignmentTag(left, right) {
  if (!left || !right) return false;
  return (
    left.tag_id === right.tag_id &&
    left.w_manual === right.w_manual &&
    String(left.alias || "") === String(right.alias || "")
  );
}

function chipGroupClass(group) {
  const normalized = normalize(group);
  return normalized ? `${UI_CLASS.chipGroupPrefix}${normalized}` : "";
}

function sortIndicator(state, key) {
  if (state.sortKey !== key) return "";
  return state.sortDir === "desc" ? " ↓" : " ↑";
}

function stateAttr(value) {
  return value ? ` data-state="${escapeHtml(value)}"` : "";
}

function classNames(...values) {
  return values.filter(Boolean).join(" ");
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function seriesTagsText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tags.${key}`, fallback, tokens);
}
