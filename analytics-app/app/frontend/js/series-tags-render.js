import {
  getAnalyticsText
} from "./analytics-config.js";
import {
  buildStudioTagScore
} from "./analysis-tag-scoring.js";
import {
  normalizeAssignmentRows
} from "./analytics-tag-editor-domain.js";
import {
  seriesTagsUi
} from "./analytics-ui.js";

const DEFAULT_STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const UI = seriesTagsUi;
const { className: UI_CLASS, state: UI_STATE } = UI;

export function renderSeriesTagsReport(input) {
  const rowsHtml = buildSeriesTagsRows(input).map((row) => {
    const chips = row.visibleTags.length
      ? row.visibleTags.map((tag) => renderTagChip(input, tag)).join("")
      : "";

    return `
      <li class="analyticsList__row seriesTags__row">
        <div class="seriesTags__col seriesTags__col--title">
          <a href="${escapeHtml(row.url)}">${escapeHtml(row.title)}</a>
        </div>
        <div class="seriesTags__col seriesTags__col--count">
          <span class="analyticsTagIndex__statusWrap">
            <span class="rag rag--${escapeHtml(row.rag)}" title="${escapeHtml(row.tooltip)}" aria-label="${escapeHtml(row.ragLabel)}"></span>
          </span>
        </div>
        <div class="seriesTags__col seriesTags__col--tags">
          <ul class="seriesTags__chipList">${chips}</ul>
        </div>
      </li>
    `;
  }).join("");

  input.mount.innerHTML = `
    <div class="seriesTags">
      ${renderFilters(input)}
      <div class="analyticsList__head seriesTags__head">
        <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="series"${stateAttr(input.sortKey === "series" ? UI_STATE.active : "")}>
          ${escapeHtml(seriesTagsText(input.config, "table_heading_series", "series"))}${sortIndicator(input, "series")}
        </button>
        <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="status"${stateAttr(input.sortKey === "status" ? UI_STATE.active : "")}>
          ${escapeHtml(seriesTagsText(input.config, "table_heading_status", "status"))}${sortIndicator(input, "status")}
        </button>
        <button type="button" class="${UI_CLASS.sortButton}" data-sort-key="tags"${stateAttr(input.sortKey === "tags" ? UI_STATE.active : "")}>
          ${escapeHtml(seriesTagsText(input.config, "table_heading_tags", "tags"))}${sortIndicator(input, "tags")}
        </button>
      </div>
      <ul class="analyticsList__rows seriesTags__rows">${rowsHtml}</ul>
    </div>
  `;
}

export function buildSeriesTagsRows(input) {
  return input.seriesData
    .map((series) => {
      const repoRow = normalizeRepoSeriesRow(input.assignmentsSeries, series.seriesId);
      const offlineSession = input.offlineSession && typeof input.offlineSession === "object"
        ? input.offlineSession
        : {};
      const offlineSeries = offlineSession.series && typeof offlineSession.series === "object"
        ? offlineSession.series
        : {};
      const offlineEntry = offlineSeries[series.seriesId]
        ? offlineSeries[series.seriesId]
        : null;
      const effectiveRow = offlineEntry ? normalizeSeriesAssignmentRow(offlineEntry.staged_row) : repoRow;
      const assigned = effectiveRow.tags.map((row) => row.tag_id);
      const score = buildStudioTagScore(assigned, input.registry, input.config);
      const tags = buildSeriesDisplayTags(input, repoRow, effectiveRow)
        .sort((a, b) => compareText(a.sortLabel, b.sortLabel));
      const visibleTags = input.filterGroup === "all"
        ? tags
        : tags.filter((tag) => tag.group === input.filterGroup);
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
    .sort((left, right) => compareSeriesRows(input, left, right));
}

function buildSeriesDisplayTags(input, repoRow, effectiveRow) {
  const repoTags = new Map(repoRow.tags.map((row) => [row.tag_id, row]));
  const effectiveTags = new Map(effectiveRow.tags.map((row) => [row.tag_id, row]));
  const tagIds = Array.from(new Set([...repoTags.keys(), ...effectiveTags.keys()]));
  const display = [];

  for (const tagId of tagIds) {
    const repoTag = repoTags.get(tagId) || null;
    const effectiveTag = effectiveTags.get(tagId) || null;
    if (!repoTag && effectiveTag) {
      display.push(toTagDisplay(tagId, input.registry, "local"));
      continue;
    }
    if (repoTag && !effectiveTag) {
      display.push(toTagDisplay(tagId, input.registry, "delete"));
      continue;
    }
    if (repoTag && effectiveTag) {
      const marker = equalNormalizedAssignmentTag(repoTag, effectiveTag) ? "" : "local";
      display.push(toTagDisplay(tagId, input.registry, marker));
    }
  }

  return display;
}

function renderTagChip(input, tag) {
  const caption = tag.marker
    ? `<span class="${classNames(UI_CLASS.chipCaption, tag.marker === "delete" ? UI_CLASS.chipCaptionDelete : UI_CLASS.chipCaptionLocal)}">${escapeHtml(seriesTagsText(
      input.config,
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

function renderFilters(input) {
  const groupButtons = getAnalyticsGroups(input).map((group) => {
    const titleAttr = groupTitleAttr(input, group);
    return `
      <button
        type="button"
        class="${classNames(UI_CLASS.keyPill, chipGroupClass(group), UI_CLASS.groupFilterButton)}"
        data-group="${escapeHtml(group)}"
        ${stateAttr(input.filterGroup === group ? UI_STATE.active : "")}
        ${titleAttr}
      >
        ${escapeHtml(group)}
      </button>
    `;
  }).join("");

  return `
    <div class="${UI_CLASS.filters}">
      <button type="button" class="analytics__button ${UI_CLASS.allFilterButton}" data-group="all"${stateAttr(input.filterGroup === "all" ? UI_STATE.active : "")}>${escapeHtml(seriesTagsText(input.config, "filter_all_tags", "All tags"))}</button>
      ${groupButtons}
    </div>
  `;
}

function getAnalyticsGroups(input) {
  return Array.isArray(input && input.studioGroups) && input.studioGroups.length
    ? input.studioGroups
    : DEFAULT_STUDIO_GROUPS;
}

function groupTitleAttr(input, group) {
  const descriptions = input.groupDescriptions instanceof Map ? input.groupDescriptions : new Map();
  const description = String(descriptions.get(group) || "").trim();
  return description ? `title="${escapeHtml(description)}"` : "";
}

function compareSeriesRows(input, left, right) {
  if (input.sortKey === "status") {
    if (left.ragRank !== right.ragRank) {
      return compareDir(left.ragRank, right.ragRank, input.sortDir);
    }
    return compareDir(left.title, right.title, input.sortDir, compareText);
  }
  if (input.sortKey === "tags") {
    const byTags = compareDir(left.tagsSortKey, right.tagsSortKey, input.sortDir, compareText);
    if (byTags !== 0) return byTags;
    return compareText(left.title, right.title);
  }
  return compareDir(left.title, right.title, input.sortDir, compareText);
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
  return normalizeSeriesAssignmentRow(row);
}

function normalizeSeriesAssignmentRow(row) {
  const raw = row && typeof row === "object" ? row : {};
  return {
    tags: normalizeAssignmentRows(raw.tags)
  };
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
  return getAnalyticsText(config, `series_tags.${key}`, fallback, tokens);
}
