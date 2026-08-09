import {
  buildStudioRouteUrl,
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  buildAnalyticsGroupDescriptionMap,
  buildAnalyticsRegistryLookup,
  getAnalyticsAssignmentsSeries,
  loadAnalyticsAssignmentsJson,
  loadAnalyticsGroupsJson,
  loadAnalyticsRegistryJson,
  loadStudioSeriesSearchJson,
  normalizeAnalyticsValue as normalize
} from "./studio-tag-data.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  seriesTagsUi
} from "./tag-ui.js";
import {
  renderSeriesTagsReport
} from "./series-tags-render.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
let GROUP_INFO_PAGE_PATH = "/studio/tag-groups/";
const SORTABLE_KEYS = new Set(["series", "status", "tags"]);
const UI = seriesTagsUi;
const { className: UI_CLASS } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initSeriesTagsPage);
} else {
  initSeriesTagsPage();
}

function routeStateDetail(state) {
  return {
    route: "series-tags",
    mode: "list",
    service: state.dataAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.seriesData && state.seriesData.length)
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(state.refs && state.refs.mount, Boolean(state.isBusy), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.refs && state.refs.mount, ready, routeStateDetail(state));
}

async function initSeriesTagsPage() {
  const mount = document.getElementById("series-tags");
  if (!mount) return;
  initializeStudioRouteState(mount, { route: "series-tags" });

  let config;
  try {
    config = await loadStudioConfig();
    STUDIO_GROUPS = getStudioGroups(config);
    GROUP_INFO_PAGE_PATH = getStudioRoute(config, "tag_groups");
  } catch (error) {
    mount.innerHTML = `<div class="${UI_CLASS.error}">Failed to load series tag config.</div>`;
    markRouteReady({
      refs: { mount },
      dataAvailable: false,
      seriesData: []
    }, true);
    return;
  }

  let seriesData;
  try {
    seriesData = await getSeriesData(config);
  } catch (error) {
    mount.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(seriesTagsText(config, "load_failed_error", "Failed to load series tag data."))}</div>`;
    markRouteReady({
      refs: { mount },
      dataAvailable: false,
      seriesData: []
    }, true);
    return;
  }
  if (!seriesData.length) {
    mount.innerHTML = `<p class="${UI_CLASS.empty}">${escapeHtml(seriesTagsText(config, "empty_state", "none"))}</p>`;
    markRouteReady({
      refs: { mount },
      dataAvailable: true,
      seriesData
    }, true);
    return;
  }

  try {
    const [assignmentsJson, registryJson] = await Promise.all([
      loadAnalyticsAssignmentsJson(config),
      loadAnalyticsRegistryJson(config)
    ]);

    const state = {
      refs: { mount },
      config,
      studioGroups: STUDIO_GROUPS,
      groupInfoPagePath: GROUP_INFO_PAGE_PATH,
      seriesData,
      assignmentsSeries: getAnalyticsAssignmentsSeries(assignmentsJson),
      registry: buildAnalyticsRegistryLookup(registryJson, STUDIO_GROUPS),
      groupDescriptions: new Map(),
      dataAvailable: true,
      isBusy: false,
      filterGroup: "all",
      sortKey: "series",
      sortDir: "asc"
    };
    try {
      const groupsJson = await loadAnalyticsGroupsJson(config);
      state.groupDescriptions = buildAnalyticsGroupDescriptionMap(groupsJson, STUDIO_GROUPS);
    } catch (error) {
      state.groupDescriptions = new Map();
    }
    wireEvents(state);
    renderTable(state);
    markRouteReady(state, true);
  } catch (error) {
    mount.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(seriesTagsText(config, "load_failed_error", "Failed to load series tag data."))}</div>`;
    markRouteReady({
      refs: { mount },
      dataAvailable: false,
      seriesData: []
    }, true);
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
      .filter((entry) => isPrimarySeriesEntry(entry))
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
  const payload = await loadStudioSeriesSearchJson(config, { cache: "no-store" });
  const items = Array.isArray(payload && payload.items) ? payload.items : [];
  return items
    .filter((row) => isPrimarySeriesEntry(row) && normalize(row && row.status) === "published")
    .map((row) => {
      const sid = normalize(row && row.series_id);
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

function isPrimarySeriesEntry(entry) {
  return normalize(entry && entry.series_type) === "primary";
}

function buildSeriesEditorUrl(config, seriesId) {
  const sid = normalize(seriesId);
  return sid ? buildStudioRouteUrl(config, "series_tag_editor", { series: sid }) : "";
}

function wireEvents(state) {
  state.refs.mount.addEventListener("click", (event) => {
    const groupButton = event.target.closest("button[data-group]");
    if (groupButton) {
      const next = normalize(groupButton.getAttribute("data-group"));
      state.filterGroup = state.studioGroups.includes(next) ? next : "all";
      renderTable(state);
      return;
    }
    const sortButton = event.target.closest("button[data-sort-key]");
    if (!sortButton) return;
    const nextSortKey = normalize(sortButton.getAttribute("data-sort-key"));
    if (!SORTABLE_KEYS.has(nextSortKey)) return;
    if (state.sortKey === nextSortKey) {
      state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    } else {
      state.sortKey = nextSortKey;
      state.sortDir = "asc";
    }
    renderTable(state);
  });
}

function renderTable(state) {
  renderSeriesTagsReport({
    mount: state.refs.mount,
    config: state.config,
    studioGroups: state.studioGroups,
    groupInfoPagePath: state.groupInfoPagePath,
    groupDescriptions: state.groupDescriptions,
    seriesData: state.seriesData,
    assignmentsSeries: state.assignmentsSeries,
    registry: state.registry,
    filterGroup: state.filterGroup,
    sortKey: state.sortKey,
    sortDir: state.sortDir
  });
  syncRouteBusyState(state);
}

function escapeHtml(value) {
  return String(value == null ? "" : value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function seriesTagsText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tags.${key}`, fallback, tokens);
}
