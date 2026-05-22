import {
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
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
  probeStudioHealth
} from "./studio-transport.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  seriesTagsUi
} from "./studio-ui.js";
import {
  renderSeriesTagsReport
} from "./series-tags-render.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
let GROUP_INFO_PAGE_PATH = "/studio/analytics/tag-groups/";
const SORTABLE_KEYS = new Set(["series", "status", "tags"]);
const UI = seriesTagsUi;
const { className: UI_CLASS, selector: UI_SELECTOR } = UI;
const EMPTY_OFFLINE_SESSION = {
  version: "tag_assignments_offline_v1",
  updated_at_utc: "",
  series: {}
};

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
      studioGroups: STUDIO_GROUPS,
      groupInfoPagePath: GROUP_INFO_PAGE_PATH,
      seriesData,
      assignmentsSeries,
      registry,
      groupDescriptions: new Map(),
      offlineSession: null,
      offlineSessionActivated: false,
      offlineSessionWorkflow: null,
      modalModule: null,
      importWorkflowModule: null,
      modalEventsWired: false,
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
    if (!state.offlineSessionActivated) return;
    void refreshActivatedOfflineSession(state);
  });

  if (state.refs.actions) {
    state.refs.actions.addEventListener("click", (event) => {
      const sessionButton = event.target.closest(UI_SELECTOR.openSessionModal);
      if (sessionButton && !sessionButton.disabled) {
        void withRouteBusy(state, () => openSeriesTagsSessionModal(state));
        return;
      }
      const importButton = event.target.closest(UI_SELECTOR.openImportModal);
      if (importButton && !importButton.disabled) {
        void withRouteBusy(state, () => openSeriesTagsImportModal(state));
      }
    });
  }

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

async function openSeriesTagsSessionModal(state) {
  await activateOfflineSession(state);
  await ensureSeriesTagsModalEvents(state);
  state.sessionModalRestoreFocus = document.activeElement;
  state.sessionModalFocusReady = false;
  state.sessionModalOpen = true;
  state.importModalOpen = false;
  renderPage(state);
  syncRouteBusyState(state);
}

async function openSeriesTagsImportModal(state) {
  await ensureSeriesTagsModalEvents(state);
  state.importModalRestoreFocus = document.activeElement;
  state.importModalFocusReady = false;
  state.importModalOpen = true;
  state.sessionModalOpen = false;
  renderChrome(state);
  syncRouteBusyState(state);
}

async function refreshActivatedOfflineSession(state) {
  await activateOfflineSession(state);
  renderPage(state);
}

async function activateOfflineSession(state) {
  const workflow = await ensureOfflineSessionWorkflow(state);
  state.offlineSession = workflow.readTagAssignmentsOfflineSession();
  state.offlineSessionActivated = true;
  return state.offlineSession;
}

async function ensureOfflineSessionWorkflow(state) {
  if (!state.offlineSessionWorkflow) {
    state.offlineSessionWorkflow = await import("./tag-assignments-offline-session.js");
  }
  return state.offlineSessionWorkflow;
}

async function ensureSeriesTagsModalEvents(state) {
  const modalModule = await ensureSeriesTagsModalModule(state);
  if (state.modalEventsWired) return modalModule;
  modalModule.wireSeriesTagsModalEvents(state, {
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
        void handleDownloadSession(state);
        return;
      }
      if (actionName === "clear") {
        void handleClearSession(state);
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
  state.modalEventsWired = true;
  return modalModule;
}

async function ensureSeriesTagsModalModule(state) {
  if (!state.modalModule) {
    state.modalModule = await import("./series-tags-modals.js");
  }
  return state.modalModule;
}

async function ensureSeriesTagsImportWorkflow(state) {
  if (!state.importWorkflowModule) {
    state.importWorkflowModule = await import("./series-tags-import-workflow.js");
  }
  return state.importWorkflowModule;
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

function renderSessionModal(state) {
  if (!state.modalModule || !state.offlineSessionActivated) return;
  state.modalModule.renderSessionModal(state);
}

function renderImportModal(state) {
  if (!state.modalModule) return;
  state.modalModule.renderImportModal(state);
}

function renderActionButtons(state) {
  if (!state.refs.actions || !state.refs.openSessionModal || !state.refs.openImportModal) return;
  state.refs.openSessionModal.textContent = seriesTagsText(state.config, "session_open_button", "Session");
  state.refs.openSessionModal.disabled = false;
  state.refs.openImportModal.textContent = seriesTagsText(state.config, "import_open_button", "Import");
  state.refs.openImportModal.disabled = !state.importAvailable;
}

function renderTable(state) {
  renderSeriesTagsReport(buildSeriesTagsReportInput(state));
}

function buildSeriesTagsReportInput(state) {
  return {
    mount: state.refs.mount,
    config: state.config,
    studioGroups: state.studioGroups,
    groupInfoPagePath: state.groupInfoPagePath,
    groupDescriptions: state.groupDescriptions,
    seriesData: state.seriesData,
    assignmentsSeries: state.assignmentsSeries,
    offlineSession: state.offlineSessionActivated ? state.offlineSession : EMPTY_OFFLINE_SESSION,
    registry: state.registry,
    filterGroup: state.filterGroup,
    sortKey: state.sortKey,
    sortDir: state.sortDir
  };
}

async function handleCopySession(state) {
  try {
    const workflow = await ensureOfflineSessionWorkflow(state);
    await workflow.copyTagAssignmentsOfflineSession(state.offlineSession || EMPTY_OFFLINE_SESSION);
    setResult(state, "success", seriesTagsText(state.config, "session_copy_success", "Offline session JSON copied."));
  } catch (error) {
    setResult(state, "error", seriesTagsText(state.config, "session_copy_failed", "Copy failed. Select and copy manually."));
  }
  renderSessionModal(state);
}

async function handleDownloadSession(state) {
  const workflow = await ensureOfflineSessionWorkflow(state);
  workflow.downloadTagAssignmentsOfflineSession(state.offlineSession || EMPTY_OFFLINE_SESSION);
  setResult(state, "success", seriesTagsText(state.config, "session_download_success", "Offline session JSON download started."));
  renderSessionModal(state);
}

async function handleClearSession(state) {
  const workflow = await ensureOfflineSessionWorkflow(state);
  state.offlineSession = workflow.clearTagAssignmentsOfflineSession();
  setResult(state, "success", seriesTagsText(state.config, "session_clear_success", "Offline session cleared."));
  renderPage(state);
}

async function probeImportAvailability(state) {
  state.importAvailable = await probeStudioHealth(500, { config: state.config });
  renderChrome(state);
  syncRouteBusyState(state);
}

async function handlePreviewImport(state) {
  const workflow = await ensureSeriesTagsImportWorkflow(state);
  const result = await workflow.previewSeriesTagsImport({
    file: state.importFile,
    config: state.config
  });
  if (Object.prototype.hasOwnProperty.call(result, "importPayload")) {
    state.importPayload = result.importPayload;
  }
  if (result.ok) {
    state.importPreview = result.importPreview;
    state.importResolutions = result.importResolutions;
  }
  setResult(state, result.resultKind, result.resultText);
  renderImportModal(state);
}

async function handleApplyImport(state) {
  const workflow = await ensureSeriesTagsImportWorkflow(state);
  const result = await workflow.applySeriesTagsImport({
    config: state.config,
    file: state.importFile,
    importPayload: state.importPayload,
    importPreview: state.importPreview,
    importResolutions: state.importResolutions
  });
  setResult(state, result.resultKind, result.resultText);
  if (result.ok) {
    await clearAppliedLocalSessionEntries(state);
    state.importPreview = null;
    state.importPayload = null;
    state.importResolutions = {};
    state.importFile = null;
    state.assignmentsSeries = result.assignmentsSeries;
    renderPage(state);
    return;
  }
  renderImportModal(state);
}

async function clearAppliedLocalSessionEntries(state) {
  const workflow = await ensureOfflineSessionWorkflow(state);
  state.offlineSession = workflow.clearImportedOfflineAssignmentsEntries({
    importPreview: state.importPreview,
    importPayload: state.importPayload,
    importResolutions: state.importResolutions
  });
  state.offlineSessionActivated = true;
}

function setResult(state, kind, text) {
  state.resultKind = kind || "";
  state.resultText = text || "";
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
