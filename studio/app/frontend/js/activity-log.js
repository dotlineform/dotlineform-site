import {
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import { loadStudioServerReadJson } from "./studio-data.js";
import { openActivityDetailsModal } from "./activity-log-modals.js";
import {
  initializeStudioRouteState,
  setStudioRouteReady
} from "./studio-route-state.js";

const SORT_KEYS = ["time", "status", "page", "action", "purpose"];

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatTimestamp(value) {
  const raw = normalizeText(value);
  if (!raw) return "";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;
  try {
    return new Intl.DateTimeFormat(undefined, {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short"
    }).format(date);
  } catch (_error) {
    return raw;
  }
}

function statusMarker(status) {
  return status === "completed" ? "✅" : "❗️";
}

function statusLabel(config, status) {
  if (status === "completed") return getStudioText(config, "activity_log.status_completed", "completed");
  if (status === "warning") return getStudioText(config, "activity_log.status_warning", "warning");
  if (status === "failed") return getStudioText(config, "activity_log.status_failed", "failed");
  return getStudioText(config, "activity_log.status_other", "status unknown");
}

function sortButton(config, labelKey, fallback, sortKey, currentSortKey, sortDir) {
  const active = currentSortKey === sortKey;
  const label = getStudioText(config, `activity_log.${labelKey}`, fallback);
  const suffix = active ? (sortDir === "desc" ? " ↓" : " ↑") : "";
  return `<button type="button" class="tagStudioList__sortBtn" data-sort-key="${escapeHtml(sortKey)}" data-state="${active ? "active" : ""}">${escapeHtml(label + suffix)}</button>`;
}

function recordCountLabel(config, labelKey, fallback, group) {
  const count = Number(group && group.count) || 0;
  if (!count) return "";
  const label = getStudioText(config, `activity_log.${labelKey}`, fallback);
  return `${label} ${count}`;
}

function summarizeRecords(config, recordGroups) {
  const parts = [
    recordCountLabel(config, "record_group_works", "works", recordGroups && recordGroups.works),
    recordCountLabel(config, "record_group_series", "series", recordGroups && recordGroups.series),
    recordCountLabel(config, "record_group_details", "details", recordGroups && recordGroups.work_details),
    recordCountLabel(config, "record_group_moments", "moments", recordGroups && recordGroups.moments),
    recordCountLabel(config, "record_group_docs", "docs", recordGroups && recordGroups.docs),
    recordCountLabel(config, "record_group_files", "files", recordGroups && recordGroups.files),
    recordCountLabel(config, "record_group_tags", "tags", recordGroups && recordGroups.tags),
    recordCountLabel(config, "record_group_aliases", "aliases", recordGroups && recordGroups.aliases),
    recordCountLabel(config, "record_group_search", "search", recordGroups && recordGroups.search)
  ].filter(Boolean);
  return parts.join(" · ");
}

function compareEntries(a, b, sortKey, sortDir) {
  const direction = sortDir === "desc" ? -1 : 1;
  if (sortKey === "time") {
    return normalizeText(a.time_utc || a.timestamp).localeCompare(normalizeText(b.time_utc || b.timestamp)) * direction;
  }
  const fieldMap = {
    status: normalizeText(a.status),
    page: normalizeText(a.page_label),
    action: normalizeText(a.user_action_label),
    purpose: normalizeText(a.script_purpose_label)
  };
  const otherFieldMap = {
    status: normalizeText(b.status),
    page: normalizeText(b.page_label),
    action: normalizeText(b.user_action_label),
    purpose: normalizeText(b.script_purpose_label)
  };
  const compare = fieldMap[sortKey].localeCompare(otherFieldMap[sortKey], undefined, { numeric: true, sensitivity: "base" });
  if (compare !== 0) return compare * direction;
  return normalizeText(b.time_utc || b.timestamp).localeCompare(normalizeText(a.time_utc || a.timestamp));
}

function renderRows(config, entries) {
  return entries.map((entry) => {
    const id = normalizeText(entry.activity_id || entry.id);
    const status = normalizeText(entry.status);
    const recordsText = summarizeRecords(config, entry.record_groups);
    const statusText = statusLabel(config, status);
    return `
      <li class="tagStudioList__row activityReport__row activityReport__row--unified">
        <span class="activityReport__cell activityReport__cell--time">
          <span class="activityReport__title">${escapeHtml(formatTimestamp(entry.time_utc || entry.timestamp))}</span>
          ${recordsText ? `<span class="activityReport__meta">${escapeHtml(recordsText)}</span>` : ""}
        </span>
        <span class="activityReport__cell activityReport__cell--status">
          <button type="button" class="activityReport__statusButton" data-activity-id="${escapeHtml(id)}" aria-label="${escapeHtml(statusText)}" title="${escapeHtml(statusText)}">${escapeHtml(statusMarker(status))}</button>
        </span>
        <span class="activityReport__cell activityReport__cell--page">
          <span class="activityReport__title">${escapeHtml(entry.page_label)}</span>
        </span>
        <span class="activityReport__cell activityReport__cell--action">
          <span class="activityReport__title">${escapeHtml(entry.user_action_label)}</span>
        </span>
        <span class="activityReport__cell activityReport__cell--purpose">
          <span class="activityReport__title">${escapeHtml(entry.script_purpose_label)}</span>
        </span>
      </li>
    `;
  }).join("");
}

function renderList(config, listNode, state, entries) {
  if (!entries.length) {
    listNode.innerHTML = "";
    return;
  }
  listNode.innerHTML = `
    <div class="tagStudioList__head activityReport__head activityReport__head--unified">
      ${sortButton(config, "column_time", "date-time", "time", state.sortKey, state.sortDir)}
      ${sortButton(config, "column_status", "status", "status", state.sortKey, state.sortDir)}
      ${sortButton(config, "column_page", "page", "page", state.sortKey, state.sortDir)}
      ${sortButton(config, "column_user_action", "user action", "action", state.sortKey, state.sortDir)}
      ${sortButton(config, "column_script_purpose", "script purpose", "purpose", state.sortKey, state.sortDir)}
    </div>
    <ol class="tagStudioList__rows activityReport__rows">${renderRows(config, entries)}</ol>
  `;
}

async function loadFeed() {
  return loadStudioServerReadJson("activity_log", { cache: "no-store" });
}

function openActivityDetails(state, activityId) {
  const entry = state.entriesById.get(activityId);
  if (!entry) return;
  openActivityDetailsModal(state, entry);
}

function applySort(state) {
  const entries = state.entries.slice().sort((a, b) => compareEntries(a, b, state.sortKey, state.sortDir));
  renderList(state.config, state.listNode, state, entries);
}

function markRouteReady(root, ready, detail = {}) {
  setStudioRouteReady(root, ready, {
    route: "studio-activity",
    mode: detail.mode || "empty",
    service: detail.service || "available",
    recordLoaded: Boolean(detail.recordLoaded)
  });
}

async function init() {
  const root = document.getElementById("studioActivityRoot");
  const statusNode = document.getElementById("studioActivityStatus");
  const metaNode = document.getElementById("studioActivityMeta");
  const listNode = document.getElementById("studioActivityList");
  const emptyNode = document.getElementById("studioActivityEmpty");
  if (!root || !statusNode || !metaNode || !listNode || !emptyNode) return;
  initializeStudioRouteState(root, { route: "studio-activity" });

  try {
    const config = await loadStudioConfigWithText("activity_log");
    const payload = await loadFeed();
    const entries = Array.isArray(payload && payload.entries) ? payload.entries : [];
    metaNode.textContent = entries.length === 1
      ? getStudioText(config, "activity_log.meta_summary_one", "1 recent activity row")
      : getStudioText(config, "activity_log.meta_summary", "{count} recent activity rows", { count: entries.length });

    if (!entries.length) {
      emptyNode.textContent = getStudioText(config, "activity_log.empty_state", "No Studio activity yet.");
      emptyNode.hidden = false;
      root.hidden = false;
      statusNode.hidden = true;
      markRouteReady(root, true, { mode: "empty", recordLoaded: false });
      return;
    }

    const entriesById = new Map(entries.map((entry) => [normalizeText(entry.activity_id || entry.id), entry]));
    const state = {
      config,
      entries,
      entriesById,
      root,
      sortKey: "time",
      sortDir: "desc",
      listNode
    };
    listNode.addEventListener("click", (event) => {
      const sortButtonNode = event.target && event.target.closest ? event.target.closest("[data-sort-key]") : null;
      if (sortButtonNode) {
        const sortKey = normalizeText(sortButtonNode.getAttribute("data-sort-key"));
        if (!SORT_KEYS.includes(sortKey)) return;
        if (state.sortKey === sortKey) {
          state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
        } else {
          state.sortKey = sortKey;
          state.sortDir = sortKey === "time" ? "desc" : "asc";
        }
        applySort(state);
        return;
      }
      const statusButton = event.target && event.target.closest ? event.target.closest("[data-activity-id]") : null;
      if (!statusButton) return;
      openActivityDetails(state, normalizeText(statusButton.getAttribute("data-activity-id")));
    });
    applySort(state);
    root.hidden = false;
    statusNode.hidden = true;
    markRouteReady(root, true, { mode: "list", recordLoaded: true });
  } catch (error) {
    console.warn("activity_log: load failed", error);
    try {
      const config = await loadStudioConfigWithText("activity_log");
      statusNode.textContent = getStudioText(config, "activity_log.load_failed_error", "Failed to load Studio activity.");
    } catch (_configError) {
      statusNode.textContent = "Failed to load Studio activity.";
    }
    root.hidden = false;
    markRouteReady(root, true, { mode: "empty", service: "unavailable", recordLoaded: false });
  }
}

init();
