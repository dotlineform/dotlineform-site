import {
  getStudioDataPath,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";

const SORT_KEYS = ["time", "run", "status", "scope", "result"];

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

function statusText(config, status) {
  if (status === "completed") return getStudioText(config, "build_activity.status_completed", "completed");
  if (status === "failed") return getStudioText(config, "build_activity.status_failed", "failed");
  return getStudioText(config, "build_activity.status_other", "status unknown");
}

function countText(label, group) {
  const count = Number(group && group.count) || 0;
  if (!count) return "";
  return `${label} ${count}`;
}

function summarizeBuildChanges(entry) {
  const source = entry && entry.changes && entry.changes.source;
  const workbook = entry && entry.changes && entry.changes.workbook;
  const media = entry && entry.changes && entry.changes.media;
  const parts = [
    countText("works", source && source.works),
    countText("series", source && source.series),
    countText("details", source && source.work_details),
    countText("moments", source && source.moments),
    countText("workbook", { count: (Number(workbook && workbook.works && workbook.works.count) || 0) + (Number(workbook && workbook.series && workbook.series.count) || 0) + (Number(workbook && workbook.work_details && workbook.work_details.count) || 0) + (Number(workbook && workbook.moments && workbook.moments.count) || 0) }),
    countText("media", { count: (Number(media && media.work && media.work.count) || 0) + (Number(media && media.work_details && media.work_details.count) || 0) + (Number(media && media.moment && media.moment.count) || 0) })
  ].filter(Boolean);
  if (entry && entry.search_rebuilt) parts.push("search rebuilt");
  return parts.join(" · ");
}

function scopeLink(config, entry) {
  const scopeKind = normalizeText(entry && entry.scope_kind);
  const scopeId = normalizeText(entry && entry.scope_id);
  const scopeLabel = normalizeText(entry && entry.scope_label) || "catalogue scope";
  let href = "";
  if (scopeKind === "work" && scopeId) href = `${getStudioRoute(config, "catalogue_work_editor")}?work=${encodeURIComponent(scopeId)}`;
  if (scopeKind === "series" && scopeId) href = `${getStudioRoute(config, "catalogue_series_editor")}?series=${encodeURIComponent(scopeId)}`;
  if (scopeKind === "moment") href = getStudioRoute(config, "catalogue_moment_import");
  if (scopeKind === "catalogue") href = getStudioRoute(config, "catalogue_status");
  return { href, label: scopeLabel };
}

function nextLink(config, entry) {
  const scope = scopeLink(config, entry);
  if (scope.href) {
    return {
      href: scope.href,
      label: normalizeText(entry && entry.scope_kind) === "catalogue" ? "Review status" : "Open scope"
    };
  }
  return { href: getStudioRoute(config, "catalogue_status"), label: "Review status" };
}

function sortButton(label, sortKey, sortDir) {
  const active = sortKey === label;
  const suffix = active ? (sortDir === "desc" ? " ↓" : " ↑") : "";
  return `<button type="button" class="tagStudioList__sortBtn" data-sort-key="${escapeHtml(label)}" data-state="${active ? "active" : ""}">${escapeHtml(label + suffix)}</button>`;
}

function compareEntries(a, b, sortKey, sortDir) {
  const direction = sortDir === "desc" ? -1 : 1;
  if (sortKey === "time") {
    return normalizeText(a.time_utc).localeCompare(normalizeText(b.time_utc)) * direction;
  }
  const fieldMap = {
    run: normalizeText(a.run_label),
    status: normalizeText(a.status),
    scope: normalizeText(a.scope_label),
    result: normalizeText(a.result_label)
  };
  const otherFieldMap = {
    run: normalizeText(b.run_label),
    status: normalizeText(b.status),
    scope: normalizeText(b.scope_label),
    result: normalizeText(b.result_label)
  };
  const compare = fieldMap[sortKey].localeCompare(otherFieldMap[sortKey], undefined, { numeric: true, sensitivity: "base" });
  if (compare !== 0) return compare * direction;
  return normalizeText(b.time_utc).localeCompare(normalizeText(a.time_utc));
}

function renderRows(config, entries) {
  return entries.map((entry) => {
    const timeText = formatTimestamp(entry.time_utc);
    const status = normalizeText(entry.status);
    const scope = scopeLink(config, entry);
    const next = nextLink(config, entry);
    const changeSummary = summarizeBuildChanges(entry);
    return `
      <li class="tagStudioList__row activityReport__row activityReport__row--build">
        <span class="activityReport__cell activityReport__cell--time">
          <span class="activityReport__title">${escapeHtml(timeText)}</span>
        </span>
        <span class="activityReport__cell">
          <span class="activityReport__title">${escapeHtml(normalizeText(entry.run_label) || "Catalogue build")}</span>
          <span class="activityReport__meta">${escapeHtml(normalizeText(entry.summary) || "—")}</span>
        </span>
        <span class="activityReport__cell">
          <span class="activityReport__pill" data-status="${escapeHtml(status)}">${escapeHtml(statusText(config, status))}</span>
        </span>
        <span class="activityReport__cell">
          ${scope.href ? `<a class="activityReport__link" href="${escapeHtml(scope.href)}">${escapeHtml(scope.label)}</a>` : `<span class="activityReport__title">${escapeHtml(scope.label)}</span>`}
          ${changeSummary ? `<span class="activityReport__meta">${escapeHtml(changeSummary)}</span>` : ""}
        </span>
        <span class="activityReport__cell">
          <span class="activityReport__title">${escapeHtml(normalizeText(entry.result_label) || "completed")}</span>
        </span>
        <span class="activityReport__cell">
          ${next.href ? `<a class="activityReport__link" href="${escapeHtml(next.href)}">${escapeHtml(next.label)}</a>` : `<span class="activityReport__meta">—</span>`}
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
    <div class="tagStudioList__head activityReport__head activityReport__head--build">
      ${sortButton("time", state.sortKey, state.sortDir)}
      ${sortButton("run", state.sortKey, state.sortDir)}
      ${sortButton("status", state.sortKey, state.sortDir)}
      ${sortButton("scope", state.sortKey, state.sortDir)}
      ${sortButton("result", state.sortKey, state.sortDir)}
      <span class="tagStudioList__headLabel">next</span>
    </div>
    <ol class="tagStudioList__rows activityReport__rows">${renderRows(config, entries)}</ol>
  `;
}

async function loadFeed(config) {
  const url = getStudioDataPath(config, "build_activity");
  if (!url) return { entries: [] };
  const response = await fetch(url, { cache: "default" });
  if (response.status === 404) return { entries: [] };
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function applySort(state) {
  const entries = state.entries.slice().sort((a, b) => compareEntries(a, b, state.sortKey, state.sortDir));
  renderList(state.config, state.listNode, state, entries);
}

async function init() {
  const root = document.getElementById("buildActivityRoot");
  const statusNode = document.getElementById("buildActivityStatus");
  const metaNode = document.getElementById("buildActivityMeta");
  const listNode = document.getElementById("buildActivityList");
  const emptyNode = document.getElementById("buildActivityEmpty");
  if (!root || !statusNode || !metaNode || !listNode || !emptyNode) return;

  try {
    const config = await loadStudioConfig();
    const payload = await loadFeed(config);
    const entries = Array.isArray(payload && payload.entries) ? payload.entries : [];
    metaNode.textContent = entries.length === 1
      ? getStudioText(config, "build_activity.meta_summary_one", "1 recent build entry")
      : getStudioText(config, "build_activity.meta_summary", "{count} recent build entries", { count: entries.length });

    if (!entries.length) {
      emptyNode.textContent = getStudioText(config, "build_activity.empty_state", "No build activity yet.");
      emptyNode.hidden = false;
      root.hidden = false;
      statusNode.hidden = true;
      return;
    }

    const state = {
      config,
      entries,
      sortKey: "time",
      sortDir: "desc",
      listNode
    };
    listNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-sort-key]") : null;
      if (!button) return;
      const sortKey = normalizeText(button.getAttribute("data-sort-key"));
      if (!SORT_KEYS.includes(sortKey)) return;
      if (state.sortKey === sortKey) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = sortKey;
        state.sortDir = sortKey === "time" ? "desc" : "asc";
      }
      applySort(state);
    });
    applySort(state);
    root.hidden = false;
    statusNode.hidden = true;
  } catch (error) {
    console.warn("build_activity: load failed", error);
    try {
      const config = await loadStudioConfig();
      statusNode.textContent = getStudioText(config, "build_activity.load_failed_error", "Failed to load build activity.");
    } catch (_configError) {
      statusNode.textContent = "Failed to load build activity.";
    }
  }
}

init();
