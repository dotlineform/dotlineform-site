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
  renderStudioModalActions,
  renderStudioModalFrame
} from "./studio-modal.js";
import {
  seriesTagsUi
} from "./studio-ui.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
let GROUP_INFO_PAGE_PATH = "/studio/tag-groups/";
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

async function initSeriesTagsPage() {
  const mount = document.getElementById("series-tags");
  if (!mount) return;

  const config = await loadStudioConfig();
  STUDIO_GROUPS = getStudioGroups(config);
  GROUP_INFO_PAGE_PATH = getStudioRoute(config, "tag_groups");

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
    void probeImportAvailability(state);
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
        return;
      }
      const importButton = event.target.closest(UI_SELECTOR.openImportModal);
      if (importButton && !importButton.disabled) {
        state.importModalOpen = true;
        renderChrome(state);
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

  if (state.refs.sessionModalHost) {
    state.refs.sessionModalHost.addEventListener("click", async (event) => {
      if (event.target.closest(`[data-role="${UI.role.closeSessionModal}"]`)) {
        state.sessionModalOpen = false;
        renderChrome(state);
        return;
      }
      const action = event.target.closest("button[data-session-action]");
      if (!action) return;
      const actionName = String(action.getAttribute("data-session-action") || "");
      if (actionName === "copy") {
        await handleCopySession(state);
        return;
      }
      if (actionName === "download") {
        handleDownloadSession(state);
        return;
      }
      if (actionName === "clear") {
        handleClearSession(state);
      }
    });
  }

  if (state.refs.importModalHost) {
    state.refs.importModalHost.addEventListener("click", async (event) => {
      if (event.target.closest(`[data-role="${UI.role.closeImportModal}"]`)) {
        state.importModalOpen = false;
        renderChrome(state);
        return;
      }
      const action = event.target.closest("button[data-import-action]");
      if (!action) return;
      const actionName = String(action.getAttribute("data-import-action") || "");
      if (actionName === "choose-file") {
        const input = state.refs.importModalHost.querySelector('input[type="file"]');
        if (input) input.click();
        return;
      }
      if (actionName === "preview-import") {
        await handlePreviewImport(state);
        return;
      }
      if (actionName === "apply-import") {
        await handleApplyImport(state);
      }
    });

    state.refs.importModalHost.addEventListener("change", (event) => {
      const input = event.target;
      if (input instanceof HTMLInputElement && input.type === "file") {
        const files = input.files;
        state.importFile = files && files.length ? files[0] : null;
        state.importPayload = null;
        state.importPreview = null;
        state.importResolutions = {};
        setResult(state, "", "");
        renderImportModal(state);
        return;
      }
      const select = event.target.closest("select[data-import-resolution]");
      if (!select) return;
      const seriesId = normalize(select.getAttribute("data-import-resolution"));
      if (!seriesId) return;
      state.importResolutions[seriesId] = String(select.value || "skip").trim().toLowerCase();
    });
  }
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

function renderSessionModal(state) {
  if (!state.refs.sessionModalHost) return;
  const exportPayload = buildOfflineAssignmentsExport(state.offlineSession);
  const stagedSeriesIds = Object.keys(exportPayload.series || {}).sort();
  const hasStaged = stagedSeriesIds.length > 0;
  const bodyHtml = `
    <div class="tagStudioToolbar seriesTagsSession">
      <div class="tagStudioToolbar__row seriesTagsSession__row" data-role="${UI.role.sessionSummary}">
        <span class="${UI_CLASS.sessionLabel}">${escapeHtml(seriesTagsText(state.config, "session_summary_label", "Offline session"))}</span>
        <span class="${UI_CLASS.sessionValue}">${escapeHtml(seriesTagsText(
          state.config,
          "session_summary_value",
          "{count} staged series",
          { count: String(stagedSeriesIds.length) }
        ))}</span>
        <span class="${UI_CLASS.sessionValue}">${escapeHtml(seriesTagsText(
          state.config,
          "session_updated_value",
          "Updated: {updated_at}",
          { updated_at: exportPayload.updated_at_utc || seriesTagsText(state.config, "session_updated_empty", "not yet") }
        ))}</span>
      </div>
      <div class="tagStudioToolbar__row seriesTagsSession__row" data-role="${UI.role.sessionActions}">
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-session-action="copy"${hasStaged ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_copy_button", "Copy JSON"))}
        </button>
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-session-action="download"${hasStaged ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_download_button", "Download JSON"))}
        </button>
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-session-action="clear"${hasStaged ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_clear_button", "Clear session"))}
        </button>
      </div>
      <p class="tagStudioToolbar__result" data-role="${UI.role.sessionResult}"${state.resultKind ? ` data-state="${escapeHtml(state.resultKind)}"` : ""}>${escapeHtml(state.resultText || "")}</p>
    </div>
  `;
  state.refs.sessionModalHost.innerHTML = renderStudioModalFrame({
    modalRole: UI.role.sessionModal,
    backdropRole: UI.role.closeSessionModal,
    titleId: "seriesTagsSessionModalTitle",
    title: seriesTagsText(state.config, "session_modal_title", "Offline session"),
    bodyHtml,
    hidden: !state.sessionModalOpen,
    actionsHtml: renderStudioModalActions([{
      label: seriesTagsText(state.config, "modal_close_button", "Close"),
      role: UI.role.closeSessionModal
    }])
  });
}

function renderImportModal(state) {
  if (!state.refs.importModalHost) return;
  const preview = state.importPreview;
  const hasFile = Boolean(state.importFile);
  const canApply = Boolean(preview && (Number(preview.applicable_count) > 0 || Number(preview.conflict_count) > 0));
  const bodyHtml = `
    <div class="tagStudioToolbar seriesTagsSession">
      <div class="tagStudioToolbar__row seriesTagsSession__row" data-role="${UI.role.sessionImport}">
        <input type="file" accept="application/json,.json" hidden>
        <span class="${UI_CLASS.sessionLabel}">${escapeHtml(seriesTagsText(state.config, "session_import_label", "Import assignments"))}</span>
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-import-action="choose-file">
          ${escapeHtml(seriesTagsText(state.config, "session_import_choose_button", "Choose file"))}
        </button>
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-import-action="preview-import"${hasFile ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_import_preview_button", "Preview import"))}
        </button>
        <button type="button" class="tagStudio__button ${UI_CLASS.sessionAction}" data-import-action="apply-import"${canApply ? "" : " disabled"}>
          ${escapeHtml(seriesTagsText(state.config, "session_import_apply_button", "Apply import"))}
        </button>
        <span class="${UI_CLASS.sessionValue}">${escapeHtml(
          state.importFile
            ? seriesTagsText(state.config, "session_import_selected_file", "Selected: {filename}", { filename: state.importFile.name })
            : seriesTagsText(state.config, "session_import_no_file", "No import file selected.")
        )}</span>
      </div>
      <div class="seriesTagsSession__review" data-role="${UI.role.sessionReview}">${renderImportReview(state)}</div>
      <p class="tagStudioToolbar__result" data-role="${UI.role.importResult}"${state.resultKind ? ` data-state="${escapeHtml(state.resultKind)}"` : ""}>${escapeHtml(state.resultText || "")}</p>
    </div>
  `;
  state.refs.importModalHost.innerHTML = renderStudioModalFrame({
    modalRole: UI.role.importModal,
    backdropRole: UI.role.closeImportModal,
    titleId: "seriesTagsImportModalTitle",
    title: seriesTagsText(state.config, "import_modal_title", "Import assignments"),
    bodyHtml,
    hidden: !state.importModalOpen,
    actionsHtml: renderStudioModalActions([{
      label: seriesTagsText(state.config, "modal_close_button", "Close"),
      role: UI.role.closeImportModal
    }])
  });
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
      client_time_utc: new Date().toISOString()
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

function renderImportReview(state) {
  const preview = state.importPreview;
  if (!preview) return "";

  const rows = (preview.series || []).map((row) => renderImportReviewRow(state, row)).join("");
  return `
    <div class="seriesTagsSession__reviewList">
      ${rows}
    </div>
  `;
}

function renderImportReviewRow(state, row) {
  const seriesId = String(row && row.series_id || "").trim();
  const status = String(row && row.status || "").trim();
  const invalidWorkIds = Array.isArray(row && row.invalid_work_ids) ? row.invalid_work_ids : [];
  const resolutionControl = status === "conflict"
    ? `
      <label class="${UI_CLASS.sessionReviewMeta}">
        <span>${escapeHtml(seriesTagsText(state.config, "session_import_resolution_label", "resolution"))}</span>
        <select class="${UI_CLASS.sessionReviewSelect}" data-import-resolution="${escapeHtml(seriesId)}">
          <option value="skip"${String(state.importResolutions[seriesId] || "skip") === "skip" ? " selected" : ""}>${escapeHtml(seriesTagsText(state.config, "session_import_resolution_skip", "skip"))}</option>
          <option value="overwrite"${String(state.importResolutions[seriesId] || "skip") === "overwrite" ? " selected" : ""}>${escapeHtml(seriesTagsText(state.config, "session_import_resolution_overwrite", "overwrite"))}</option>
        </select>
      </label>
    `
    : "";
  const detail = status === "invalid" && invalidWorkIds.length
    ? seriesTagsText(state.config, "session_import_invalid_work_ids", "Invalid works: {work_ids}", { work_ids: invalidWorkIds.join(", ") })
    : seriesTagsText(state.config, `session_import_status_${status}`, status || "unknown");

  return `
    <div class="${UI_CLASS.sessionReviewItem}">
      <div class="${UI_CLASS.sessionReviewMeta}">
        <strong>${escapeHtml(seriesId)}</strong>
        <span>${escapeHtml(detail)}</span>
      </div>
      ${resolutionControl}
    </div>
  `;
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
