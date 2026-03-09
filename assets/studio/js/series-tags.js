import {
  buildStudioRagTooltip,
  computeStudioRag,
  computeStudioTagMetrics,
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  buildStudioGroupDescriptionMap,
  buildStudioRegistryLookup,
  getSeriesAssignmentTagIds,
  getStudioAssignmentsSeries,
  loadSiteSeriesIndexJson,
  loadStudioAssignmentsJson,
  loadStudioGroupsJson,
  loadStudioRegistryJson,
  normalizeStudioValue as normalize
} from "./studio-data.js";
import {
  seriesTagsUi
} from "./studio-ui.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
let GROUP_INFO_PAGE_PATH = "/studio/tag-groups/";
const UI = seriesTagsUi;
const { className: UI_CLASS, state: UI_STATE } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initSeriesTagsPage);
} else {
  initSeriesTagsPage();
}

async function initSeriesTagsPage() {
  const mount = document.getElementById("series-tags");
  if (!mount) return;

  const config = await loadStudioConfig();
  STUDIO_GROUPS = getStudioGroups(config);
  GROUP_INFO_PAGE_PATH = getStudioRoute(config, "tag_groups");

  const seriesData = await getSeriesData(config);
  if (!seriesData.length) {
    mount.innerHTML = `<p class="${UI_CLASS.empty}">${escapeHtml(seriesTagsText(config, "empty_state", "none"))}</p>`;
    return;
  }

  try {
    const [assignmentsJson, registryJson] = await Promise.all([
      loadStudioAssignmentsJson(config),
      loadStudioRegistryJson(config)
    ]);

    const assignmentsSeries = getStudioAssignmentsSeries(assignmentsJson);
    const registry = buildStudioRegistryLookup(registryJson, STUDIO_GROUPS, { requireLabel: true });
    const state = {
      mount,
      config,
      seriesData,
      assignmentsSeries,
      registry,
      groupDescriptions: new Map(),
      filterGroup: "all"
    };
    try {
      const groupsJson = await loadStudioGroupsJson(config);
      state.groupDescriptions = buildStudioGroupDescriptionMap(groupsJson, STUDIO_GROUPS);
    } catch (error) {
      state.groupDescriptions = new Map();
    }
    renderTable(state);
    mount.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-group]");
      if (!button) return;
      const next = normalize(button.getAttribute("data-group"));
      state.filterGroup = STUDIO_GROUPS.includes(next) ? next : "all";
      renderTable(state);
    });
  } catch (error) {
    mount.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(seriesTagsText(config, "load_failed_error", "Failed to load series tag data."))}</div>`;
  }
}

async function getSeriesData(config) {
  const inline = parseSeriesDataFromInline(config);
  if (inline.length) return inline;
  return fetchSeriesDataFromIndex(config);
}

function parseSeriesDataFromInline(config) {
  const node = document.getElementById("series-tags-series-data");
  if (!node) return [];
  try {
    const parsed = JSON.parse(node.textContent || "[]");
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((entry) => {
        const seriesId = normalize(entry && entry.series_id);
        const title = String((entry && entry.title) || "").trim();
        return {
          seriesId,
          title,
          url: buildSeriesEditorUrl(config, seriesId)
        };
      })
      .filter((entry) => entry.seriesId && entry.title)
      .sort((a, b) => a.title.localeCompare(b.title, undefined, { sensitivity: "base" }));
  } catch (error) {
    return [];
  }
}

async function fetchSeriesDataFromIndex(config) {
  const payload = await loadSiteSeriesIndexJson(config);
  const seriesMap = payload && typeof payload.series === "object" && payload.series !== null
    ? payload.series
    : {};
  return Object.keys(seriesMap)
    .map((seriesId) => {
      const row = seriesMap[seriesId];
      const sid = normalize(seriesId);
      const title = String((row && row.title) || sid).trim();
      return {
        seriesId: sid,
        title,
        url: buildSeriesEditorUrl(config, sid)
      };
    })
    .filter((entry) => entry.seriesId && entry.title)
    .sort((a, b) => a.title.localeCompare(b.title, undefined, { sensitivity: "base" }));
}

function buildSeriesEditorUrl(config, seriesId) {
  const sid = normalize(seriesId);
  const base = getStudioRoute(config, "series_tag_editor");
  if (!base) return "";
  return `${base}?series=${encodeURIComponent(sid)}`;
}

function renderTable(state) {
  const rowsHtml = state.seriesData.map((series) => {
    const assigned = getSeriesAssignmentTagIds(state.assignmentsSeries, series.seriesId, { exactMatchOnly: true });
    const metrics = computeStudioTagMetrics(assigned, state.registry, state.config);
    const rag = computeStudioRag(metrics, state.config);
    const tooltip = buildStudioRagTooltip(metrics);
    const ragLabel = `status ${rag.toUpperCase()}: ${tooltip}`;
    const tags = assigned
      .map((tagId) => toTagDisplay(tagId, state.registry))
      .sort((a, b) => a.sortLabel.localeCompare(b.sortLabel, undefined, { sensitivity: "base" }));
    const visibleTags = state.filterGroup === "all"
      ? tags
      : tags.filter((tag) => tag.group === state.filterGroup);

    const chips = visibleTags.length
      ? visibleTags.map((tag) => (
        `<li class="${classNames(UI_CLASS.chip, tag.className)}" title="${escapeHtml(tag.tagId)}">${escapeHtml(tag.label)}</li>`
      )).join("")
      : `<li class="${UI_CLASS.empty}">${escapeHtml(seriesTagsText(state.config, "empty_state", "none"))}</li>`;

    return `
      <li class="seriesTags__row">
        <div class="seriesTags__col seriesTags__col--title">
          <a href="${escapeHtml(series.url)}">${escapeHtml(series.title)}</a>
        </div>
        <div class="seriesTags__col seriesTags__col--count">
          <span class="tagStudioIndex__statusWrap">
            <span class="rag rag--${escapeHtml(rag)}" title="${escapeHtml(tooltip)}" aria-label="${escapeHtml(ragLabel)}"></span>
          </span>
        </div>
        <div class="seriesTags__col seriesTags__col--tags">
          <ul class="seriesTags__chipList">${chips}</ul>
        </div>
      </li>
    `;
  }).join("");

  state.mount.innerHTML = `
    <div class="seriesTags">
      <div class="seriesTags__head">
        <div class="seriesTags__col seriesTags__col--title">${escapeHtml(seriesTagsText(state.config, "table_heading_series", "series"))}</div>
        <div class="seriesTags__col seriesTags__col--count">${escapeHtml(seriesTagsText(state.config, "table_heading_status", "status"))}</div>
        <div class="seriesTags__col seriesTags__col--tags">
          ${renderFilters(state)}
        </div>
      </div>
      <ul class="seriesTags__rows">${rowsHtml}</ul>
    </div>
  `;
}

function renderFilters(state) {
  const groupButtons = STUDIO_GROUPS.map((group) => {
    const titleAttr = groupTitleAttr(state.groupDescriptions, group);
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

function groupTitleAttr(groupDescriptions, group) {
  const description = String(groupDescriptions.get(group) || "").trim();
  if (!description) return "";
  return `title="${escapeHtml(description)}"`;
}

function renderGroupInfoControl(state) {
  return `
    <a
      class="${classNames(UI_CLASS.keyPill, UI_CLASS.keyInfoButton)}"
      href="${GROUP_INFO_PAGE_PATH}"
      target="_blank"
      rel="noopener noreferrer"
      title="${escapeHtml(seriesTagsText(state.config, "group_info_title", "Open group descriptions in a new tab"))}"
      aria-label="${escapeHtml(seriesTagsText(state.config, "group_info_aria_label", "Open group descriptions in a new tab"))}"
    >
      <em>i</em>
    </a>
  `;
}

function toTagDisplay(rawTagId, registry) {
  const tagId = normalize(rawTagId);
  const known = registry.get(tagId);
  if (known) {
    const className = STUDIO_GROUPS.includes(known.group)
      ? chipGroupClass(known.group)
      : UI_CLASS.chipWarning;
    return {
      tagId,
      group: known.group,
      label: known.label,
      sortLabel: known.label,
      className
    };
  }

  const groupPrefix = groupFromTagId(tagId);
  const className = STUDIO_GROUPS.includes(groupPrefix)
    ? chipGroupClass(groupPrefix)
    : UI_CLASS.chipWarning;
  return {
    tagId,
    group: groupPrefix,
    label: tagId,
    sortLabel: tagId,
    className
  };
}

function groupFromTagId(tagId) {
  const idx = tagId.indexOf(":");
  if (idx < 0) return "";
  return tagId.slice(0, idx);
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function seriesTagsText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tags.${key}`, fallback, tokens);
}

function classNames(...tokens) {
  return tokens.filter(Boolean).join(" ");
}

function chipGroupClass(group) {
  return `${UI_CLASS.chipGroupPrefix}${group}`;
}

function stateAttr(stateValue) {
  return stateValue ? ` data-state="${escapeHtml(stateValue)}"` : "";
}
