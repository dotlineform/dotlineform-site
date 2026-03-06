import {
  buildStudioRagTooltip,
  computeStudioRag,
  computeStudioTagMetrics,
  getSiteDataPath,
  getStudioDataPath,
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
let GROUP_INFO_PAGE_PATH = "/studio/tag-groups/";

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
    mount.innerHTML = `<p class="tagStudio__empty">${escapeHtml(seriesTagsText(config, "empty_state", "none"))}</p>`;
    return;
  }

  try {
    const [assignmentsJson, registryJson] = await Promise.all([
      fetchJson(getStudioDataPath(config, "tag_assignments")),
      fetchJson(getStudioDataPath(config, "tag_registry"))
    ]);

    const assignmentsSeries = assignmentsJson && typeof assignmentsJson.series === "object"
      ? assignmentsJson.series
      : {};
    const registry = buildRegistryLookup(registryJson);
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
      const groupsJson = await fetchJson(getStudioDataPath(config, "tag_groups"));
      state.groupDescriptions = buildGroupDescriptionMap(groupsJson);
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
    mount.innerHTML = `<div class="tagStudioError">${escapeHtml(seriesTagsText(config, "load_failed_error", "Failed to load series tag data."))}</div>`;
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
  const seriesIndexUrl = getSiteDataPath(config, "series_index");
  const payload = await fetchJson(seriesIndexUrl);
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

async function fetchJson(url) {
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function buildRegistryLookup(registryJson) {
  const lookup = new Map();
  const tags = Array.isArray(registryJson && registryJson.tags) ? registryJson.tags : [];
  for (const raw of tags) {
    if (!raw || typeof raw !== "object") continue;
    const tagId = normalize(raw.tag_id);
    const group = normalize(raw.group);
    const label = String(raw.label || "").trim();
    const status = normalize(raw.status || "active");
    if (!tagId || !label) continue;
    lookup.set(tagId, { group, label, status });
  }
  return lookup;
}

function buildGroupDescriptionMap(groupsJson) {
  const out = new Map();
  const groups = Array.isArray(groupsJson && groupsJson.groups) ? groupsJson.groups : [];
  for (const raw of groups) {
    if (!raw || typeof raw !== "object") continue;
    const groupId = normalize(raw.group_id);
    const description = String(raw.description || "").trim();
    if (!STUDIO_GROUPS.includes(groupId) || !description) continue;
    out.set(groupId, description);
  }
  return out;
}

function renderTable(state) {
  const rowsHtml = state.seriesData.map((series) => {
    const assigned = getSeriesTags(state.assignmentsSeries, series.seriesId);
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
        `<li class="tagStudio__chip ${escapeHtml(tag.className)}" title="${escapeHtml(tag.tagId)}">${escapeHtml(tag.label)}</li>`
      )).join("")
      : `<li class="tagStudio__empty">${escapeHtml(seriesTagsText(state.config, "empty_state", "none"))}</li>`;

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
  const allActiveClass = state.filterGroup === "all" ? " is-active" : "";
  const groupButtons = STUDIO_GROUPS.map((group) => {
    const activeClass = state.filterGroup === group ? " is-active" : "";
    const titleAttr = groupTitleAttr(state.groupDescriptions, group);
    return `
      <button
        type="button"
        class="tagStudio__keyPill tagStudio__chip--${escapeHtml(group)} tagRegistry__groupBtn${activeClass}"
        data-group="${escapeHtml(group)}"
        ${titleAttr}
      >
        ${escapeHtml(group)}
      </button>
    `;
  }).join("");

  return `
    <div class="tagStudio__key seriesTags__filters">
      <button type="button" class="tagStudio__button tagRegistry__allBtn${allActiveClass}" data-group="all">${escapeHtml(seriesTagsText(state.config, "filter_all_tags", "All tags"))}</button>
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
      class="tagStudio__keyPill tagStudio__keyInfoBtn"
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

function getSeriesTags(assignmentsSeries, seriesId) {
  const row = assignmentsSeries && assignmentsSeries[seriesId];
  if (!row || !Array.isArray(row.tags)) return [];
  const out = [];
  const seen = new Set();
  for (const value of row.tags) {
    let tagId = "";
    if (typeof value === "string") {
      tagId = String(value || "").trim();
    } else if (value && typeof value === "object") {
      tagId = String(value.tag_id || "").trim();
    }
    tagId = normalize(tagId);
    if (!tagId || seen.has(tagId)) continue;
    seen.add(tagId);
    out.push(tagId);
  }
  return out;
}

function toTagDisplay(rawTagId, registry) {
  const tagId = normalize(rawTagId);
  const known = registry.get(tagId);
  if (known) {
    const className = STUDIO_GROUPS.includes(known.group)
      ? `tagStudio__chip--${known.group}`
      : "tagStudio__chip--warning";
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
    ? `tagStudio__chip--${groupPrefix}`
    : "tagStudio__chip--warning";
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

function normalize(value) {
  return String(value || "").trim().toLowerCase();
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
