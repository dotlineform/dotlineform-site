import {
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import {
  buildStudioRagTooltip,
  computeStudioRag,
  computeStudioTagMetrics
} from "./analysis-tag-scoring.js";
import {
  buildStudioGroupDescriptionMap,
  buildStudioRegistryLookup,
  getStudioAssignmentsSeries,
  loadSiteSeriesIndexJson,
  loadStudioAssignmentsJson,
  loadStudioGroupsJson,
  loadStudioRegistryJson,
  normalizeStudioValue as normalize
} from "./studio-data.js";
import {
  buildOfflineAssignmentsExport,
  clearOfflineAssignmentsSession,
  equalOfflineSeriesRows,
  getOfflineAssignmentsSeriesEntry,
  normalizeOfflineSeriesRow,
  readOfflineAssignmentsSession,
  removeOfflineAssignmentsSeriesEntry,
  writeOfflineAssignmentsSession
} from "./tag-assignments-offline.js";
import {
  probeStudioHealth,
  postJson,
  STUDIO_WRITE_ENDPOINTS
} from "./studio-transport.js";
import {
  renderImportModal,
  renderSessionModal,
  wireSeriesTagsModalEvents
} from "./series-tags-modals.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import { buildStudioActivityContext } from "./studio-activity-context.js";
import {
  seriesTagsUi
} from "./studio-ui.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
let GROUP_INFO_PAGE_PATH = "/studio/analytics/tag-groups/";
const SORTABLE_KEYS = new Set(["series", "status", "tags"]);
const RAG_ORDER = {
  red: 0,
  amber: 1,
  green: 2
};
const UI = seriesTagsUi;
const { className: UI_CLASS, selector: UI_SELECTOR, state: UI_STATE } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initSeriesTagsPage);
} else {
  initSeriesTagsPage();
}

function routeStateDetail(state) {
  return {
    route: "series-tags",
    mode: state.importModalOpen ? "import" : state.sessionModalOpen ? "session" : "list",
    service: state.importAvailable ? "available" : "unavailable",
    recordLoaded: Boolean(state.seriesData && state.seriesData.length)
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(state.refs && state.refs.mount, Boolean(state.isBusy), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.refs && state.refs.mount, ready, routeStateDetail(state));
}

async function withRouteBusy(state, task) {
  state.isBusy = true;
  syncRouteBusyState(state);
  try {
    return await task();
  } finally {
    state.isBusy = false;
    syncRouteBusyState(state);
  }
}

async function initSeriesTagsPage() {
  const mount = document.getElementById("series-tags");
  if (!mount) return;
  initializeStudioRouteState(mount, { route: "series-tags" });

  let config = null;
  try {
    config = await loadStudioConfigWithText("series_tags");
    STUDIO_GROUPS = getStudioGroups(config);
    GROUP_INFO_PAGE_PATH = getStudioRoute(config, "tag_groups");
  } catch (error) {
    mount.innerHTML = `<div class="${UI_CLASS.error}">Failed to load series tag config.</div>`;
    markRouteReady({
      refs: { mount },
      importAvailable: false,
      seriesData: [],
      importModalOpen: false,
      sessionModalOpen: false
    }, true);
    return;
  }

  const actions = document.querySelector(UI_SELECTOR.actions);
  const openSessionModal = document.querySelector(UI_SELECTOR.openSessionModal);
  const openImportModal = document.querySelector(UI_SELECTOR.openImportModal);
  const sessionModalHost = document.querySelector(UI_SELECTOR.sessionModalHost);
  const importModalHost = document.querySelector(UI_SELECTOR.importModalHost);

  const refs = {
    mount,
    actions,
    openSessionModal,
    openImportModal,
    sessionModalHost,
    importModalHost
  };

  let seriesData = [];
  try {
    seriesData = await getSeriesData(config);
  } catch (error) {
    mount.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(seriesTagsText(config, "load_failed_error", "Failed to load series tag data."))}</div>`;
    markRouteReady({
      refs,
      importAvailable: false,
      seriesData: [],
      importModalOpen: false,
      sessionModalOpen: false
    }, true);
    return;
  }
  if (!seriesData.length) {
    mount.innerHTML = `<p class="${UI_CLASS.empty}">${escapeHtml(seriesTagsText(config, "empty_state", "none"))}</p>`;
    markRouteReady({
      refs,
      importAvailable: false,
      seriesData,
      importModalOpen: false,
      sessionModalOpen: false
    }, true);
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
      refs,
      config,
      seriesData,
      assignmentsSeries,
      registry,
      groupDescriptions: new Map(),
      offlineSession: readOfflineAssignmentsSession(),
      importAvailable: false,
      importFile: null,
      importPayload: null,
      importPreview: null,
      importResolutions: {},
      sessionModalOpen: false,
      importModalOpen: false,
      isBusy: false,
      filterGroup: "all",
      sortKey: "series",
      sortDir: "asc",
      resultKind: "",
      resultText: ""
    };
    try {
      const groupsJson = await loadStudioGroupsJson(config);
      state.groupDescriptions = buildStudioGroupDescriptionMap(groupsJson, STUDIO_GROUPS);
    } catch (error) {
      state.groupDescriptions = new Map();
    }
    wireEvents(state);
    renderPage(state);
    markRouteReady(state, true);
    void probeImportAvailability(state);
  } catch (error) {
    mount.innerHTML = `<div class="${UI_CLASS.error}">${escapeHtml(seriesTagsText(config, "load_failed_error", "Failed to load series tag data."))}</div>`;
    markRouteReady({
      refs,
      importAvailable: false,
      seriesData: [],
      importModalOpen: false,
      sessionModalOpen: false
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
  const payload = await loadSiteSeriesIndexJson(config);
  const seriesMap = payload && typeof payload.series === "object" && payload.series !== null
    ? payload.series
    : {};
  return Object.keys(seriesMap)
    .filter((seriesId) => isPrimarySeriesEntry(seriesMap[seriesId]))
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

function isPrimarySeriesEntry(entry) {
  return normalize(entry && entry.series_type) === "primary";
}

function buildSeriesEditorUrl(config, seriesId) {
  const sid = normalize(seriesId);
  const base = getStudioRoute(config, "series_tag_editor");
  if (!base) return "";
  return `${base}?series=${encodeURIComponent(sid)}`;
}

function wireEvents(state) {
  window.addEventListener("pageshow", () => {
    state.offlineSession = readOfflineAssignmentsSession();
    renderPage(state);
  });

  if (state.refs.actions) {
    state.refs.actions.addEventListener("click", (event) => {
      const sessionButton = event.target.closest(UI_SELECTOR.openSessionModal);
      if (sessionButton && !sessionButton.disabled) {
        state.sessionModalOpen = true;
        renderChrome(state);
        syncRouteBusyState(state);
        return;
      }
      const importButton = event.target.closest(UI_SELECTOR.openImportModal);
      if (importButton && !importButton.disabled) {
        state.importModalOpen = true;
        renderChrome(state);
        syncRouteBusyState(state);
      }
    });
  }

  state.refs.mount.addEventListener("click", (event) => {
    const groupButton = event.target.closest("button[data-group]");
    if (groupButton) {
      const next = normalize(groupButton.getAttribute("data-group"));
      state.filterGroup = STUDIO_GROUPS.includes(next) ? next : "all";
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

  wireSeriesTagsModalEvents(state, {
    onModalStateChange: () => {
      renderChrome(state);
      syncRouteBusyState(state);
    },
    onSessionAction: (actionName) => {
      if (actionName === "copy") {
        void handleCopySession(state);
        return;
      }
      if (actionName === "download") {
        handleDownloadSession(state);
        return;
      }
      if (actionName === "clear") {
        handleClearSession(state);
      }
    },
    onImportAction: (actionName) => {
      if (actionName === "preview-import") {
        void withRouteBusy(state, () => handlePreviewImport(state));
        return;
      }
      if (actionName === "apply-import") {
        void withRouteBusy(state, () => handleApplyImport(state));
      }
    },
    onImportFileChange: (file) => {
      state.importFile = file;
      state.importPayload = null;
      state.importPreview = null;
      state.importResolutions = {};
      setResult(state, "", "");
      renderImportModal(state);
    },
    onImportResolutionChange: (seriesId, value) => {
      state.importResolutions[seriesId] = value;
    }
  });
}

function renderPage(state) {
  renderChrome(state);
  renderTable(state);
}

function renderChrome(state) {
  renderActionButtons(state);
  renderSessionModal(state);
  renderImportModal(state);
}

function renderActionButtons(state) {
  const exportPayload = buildOfflineAssignmentsExport(state.offlineSession);
  const stagedSeriesIds = Object.keys(exportPayload.series || {}).sort();
  const hasStaged = stagedSeriesIds.length > 0;
  if (!state.refs.actions || !state.refs.openSessionModal || !state.refs.openImportModal) return;
  state.refs.openSessionModal.textContent = seriesTagsText(state.config, "session_open_button", "Session");
  state.refs.openSessionModal.disabled = !hasStaged;
  state.refs.openImportModal.textContent = seriesTagsText(state.config, "import_open_button", "Import");
  state.refs.openImportModal.disabled = !state.importAvailable;
}

function renderTable(state) {
  const rowsHtml = buildSeriesRows(state).map((row) => {
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

function buildSeriesRows(state) {
  return state.seriesData
    .map((series) => {
      const repoRow = normalizeRepoSeriesRow(state.assignmentsSeries, series.seriesId);
      const offlineEntry = state.offlineSession.series && state.offlineSession.series[series.seriesId]
        ? state.offlineSession.series[series.seriesId]
        : null;
      const effectiveRow = offlineEntry ? normalizeOfflineSeriesRow(offlineEntry.staged_row) : repoRow;
      const assigned = effectiveRow.tags.map((row) => row.tag_id);
      const metrics = computeStudioTagMetrics(assigned, state.registry, state.config);
      const rag = computeStudioRag(metrics, state.config);
      const tooltip = buildStudioRagTooltip(metrics);
      const ragLabel = `status ${rag.toUpperCase()}: ${tooltip}`;
      const tags = buildSeriesDisplayTags(state, repoRow, effectiveRow)
        .sort((a, b) => compareText(a.sortLabel, b.sortLabel));
      const visibleTags = state.filterGroup === "all"
        ? tags
        : tags.filter((tag) => tag.group === state.filterGroup);
      return {
        ...series,
        rag,
        ragRank: Number.isInteger(RAG_ORDER[rag]) ? RAG_ORDER[rag] : Number.MAX_SAFE_INTEGER,
        tooltip,
        ragLabel,
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

async function handleCopySession(state) {
  try {
    const exportPayload = buildOfflineAssignmentsExport(state.offlineSession);
    await navigator.clipboard.writeText(JSON.stringify(exportPayload, null, 2));
    setResult(state, "success", seriesTagsText(state.config, "session_copy_success", "Offline session JSON copied."));
  } catch (error) {
    setResult(state, "error", seriesTagsText(state.config, "session_copy_failed", "Copy failed. Select and copy manually."));
  }
  renderSessionModal(state);
}

function handleDownloadSession(state) {
  const exportPayload = buildOfflineAssignmentsExport(state.offlineSession);
  const blob = new Blob([`${JSON.stringify(exportPayload, null, 2)}\n`], { type: "application/json" });
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = `tag-assignments-offline-${timestampForFilename(exportPayload.updated_at_utc)}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(href), 0);
  setResult(state, "success", seriesTagsText(state.config, "session_download_success", "Offline session JSON download started."));
  renderSessionModal(state);
}

function handleClearSession(state) {
  state.offlineSession = clearOfflineAssignmentsSession();
  setResult(state, "success", seriesTagsText(state.config, "session_clear_success", "Offline session cleared."));
  renderPage(state);
}

async function probeImportAvailability(state) {
  state.importAvailable = await probeStudioHealth(500);
  renderChrome(state);
  syncRouteBusyState(state);
}

async function handlePreviewImport(state) {
  if (!state.importFile) {
    setResult(state, "error", seriesTagsText(state.config, "session_import_no_file", "No import file selected."));
    renderImportModal(state);
    return;
  }

  try {
    state.importPayload = JSON.parse(await state.importFile.text());
  } catch (error) {
    setResult(state, "error", seriesTagsText(state.config, "session_import_invalid_json", "Import file is not valid JSON."));
    renderImportModal(state);
    return;
  }

  try {
    const response = await postJson(STUDIO_WRITE_ENDPOINTS.importTagAssignmentsPreview, {
      import_assignments: state.importPayload,
      import_filename: state.importFile.name || "",
      client_time_utc: new Date().toISOString()
    });
    state.importPreview = response;
    state.importResolutions = {};
    for (const row of response.series || []) {
      if (String(row && row.status || "") === "conflict") {
        state.importResolutions[String(row.series_id || "").trim().toLowerCase()] = "skip";
      }
    }
    setResult(state, "success", String(response.summary_text || seriesTagsText(state.config, "session_import_preview_success", "Import preview ready.")));
  } catch (error) {
    setResult(state, "error", String(error && error.message ? error.message : seriesTagsText(state.config, "session_import_preview_failed", "Import preview failed.")));
  }
  renderImportModal(state);
}

async function handleApplyImport(state) {
  if (!state.importPayload || !state.importPreview) {
    setResult(state, "error", seriesTagsText(state.config, "session_import_apply_without_preview", "Preview the import before applying it."));
    renderImportModal(state);
    return;
  }

  try {
    const response = await postJson(STUDIO_WRITE_ENDPOINTS.importTagAssignments, {
      import_assignments: state.importPayload,
      import_filename: state.importFile && state.importFile.name ? state.importFile.name : "",
      resolutions: state.importResolutions,
      client_time_utc: new Date().toISOString(),
      activity_context: buildStudioActivityContext({
        pageId: "series-tags",
        actionId: "import-series-tag-assignments",
        route: "/studio/analytics/series-tags/",
        controlId: "apply-import",
        controlSelector: "[data-import-action=\"apply-import\"]",
        recordIdField: "import_filename",
        recordId: state.importFile && state.importFile.name ? state.importFile.name : "series-tags-import"
      })
    });
    clearAppliedLocalSessionEntries(state);
    state.importPreview = null;
    state.importPayload = null;
    state.importResolutions = {};
    state.importFile = null;
    state.assignmentsSeries = getStudioAssignmentsSeries(await loadStudioAssignmentsJson(state.config, { cache: "no-store" }));
    setResult(state, "success", String(response.summary_text || seriesTagsText(state.config, "session_import_apply_success", "Import applied.")));
    renderPage(state);
  } catch (error) {
    setResult(state, "error", String(error && error.message ? error.message : seriesTagsText(state.config, "session_import_apply_failed", "Import failed.")));
    renderImportModal(state);
  }
}

function clearAppliedLocalSessionEntries(state) {
  if (!state.importPreview || !state.importPayload || !state.importPayload.series) return;
  let session = state.offlineSession;
  let changed = false;

  for (const row of state.importPreview.series || []) {
    const seriesId = normalize(row && row.series_id);
    if (!seriesId) continue;
    const status = String(row && row.status || "");
    if (status === "invalid" || status === "missing") continue;
    if (status === "conflict" && String(state.importResolutions[seriesId] || "skip") !== "overwrite") continue;

    const importedEntry = state.importPayload.series[seriesId];
    const localEntry = getOfflineAssignmentsSeriesEntry(session, seriesId);
    if (!importedEntry || !localEntry) continue;
    if (!equalOfflineSeriesRows(importedEntry.staged_row, localEntry.staged_row)) continue;
    session = removeOfflineAssignmentsSeriesEntry(session, seriesId, new Date().toISOString());
    changed = true;
  }

  if (!changed) return;
  state.offlineSession = writeOfflineAssignmentsSession(session);
}

function setResult(state, kind, text) {
  state.resultKind = kind || "";
  state.resultText = text || "";
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
  return description ? `title="${escapeHtml(description)}"` : "";
}

function renderGroupInfoControl(state) {
  const href = GROUP_INFO_PAGE_PATH || "";
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

function timestampForFilename(value) {
  const text = String(value || "").trim();
  if (!text) return "session";
  return text.replace(/[^0-9A-Za-z]+/g, "-").replace(/^-+|-+$/g, "") || "session";
}

function seriesTagsText(config, key, fallback, tokens) {
  return getStudioText(config, `series_tags.${key}`, fallback, tokens);
}
