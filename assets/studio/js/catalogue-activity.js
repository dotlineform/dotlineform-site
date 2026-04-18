import {
  getStudioDataPath,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";

const SORT_KEYS = ["time", "event", "status", "scope", "attention"];

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
  if (status === "completed") return getStudioText(config, "catalogue_activity.status_completed", "completed");
  if (status === "failed") return getStudioText(config, "catalogue_activity.status_failed", "failed");
  return getStudioText(config, "catalogue_activity.status_other", "status unknown");
}

function countText(label, group) {
  const count = Number(group && group.count) || 0;
  if (!count) return "";
  return `${label} ${count}`;
}

function summarizeAffected(affected) {
  const parts = [
    countText("works", affected && affected.works),
    countText("series", affected && affected.series),
    countText("details", affected && affected.work_details),
    countText("files", affected && affected.work_files),
    countText("links", affected && affected.work_links),
    countText("moments", affected && affected.moments)
  ].filter(Boolean);
  return parts.join(" · ");
}

function scopeLink(config, entry) {
  const scopeKind = normalizeText(entry && entry.scope_kind);
  const scopeId = normalizeText(entry && entry.scope_id);
  const scopeLabel = normalizeText(entry && entry.scope_label) || "general catalogue";
  let href = "";
  if (scopeKind === "work" && scopeId) href = `${getStudioRoute(config, "catalogue_work_editor")}?work=${encodeURIComponent(scopeId)}`;
  if (scopeKind === "series" && scopeId) href = `${getStudioRoute(config, "catalogue_series_editor")}?series=${encodeURIComponent(scopeId)}`;
  if (scopeKind === "work_detail" && scopeId) href = `${getStudioRoute(config, "catalogue_work_detail_editor")}?detail=${encodeURIComponent(scopeId)}`;
  if (scopeKind === "work_file" && scopeId) href = `${getStudioRoute(config, "catalogue_work_file_editor")}?file=${encodeURIComponent(scopeId)}`;
  if (scopeKind === "work_link" && scopeId) href = `${getStudioRoute(config, "catalogue_work_link_editor")}?link=${encodeURIComponent(scopeId)}`;
  if (scopeKind === "bulk_works" || scopeKind === "bulk_work_details") href = getStudioRoute(config, "bulk_add_work");
  if (scopeKind === "moment") href = getStudioRoute(config, "catalogue_moment_import");
  return { href, label: scopeLabel };
}

function nextLink(config, entry) {
  const status = normalizeText(entry && entry.status);
  const operation = normalizeText(entry && entry.operation);
  const attentionLabel = normalizeText(entry && entry.attention_label);
  const scope = scopeLink(config, entry);
  if (status === "failed") {
    if (operation.startsWith("catalogue/import-")) {
      return { href: getStudioRoute(config, "bulk_add_work"), label: "Open import" };
    }
    if (scope.href) return { href: scope.href, label: "Open record" };
    return { href: getStudioRoute(config, "catalogue_status"), label: "Review status" };
  }
  if (attentionLabel === "rebuild pending") {
    if (scope.href) return { href: scope.href, label: "Open record" };
    return { href: getStudioRoute(config, "catalogue_status"), label: "Review status" };
  }
  if (operation === "moment.import") {
    return { href: getStudioRoute(config, "build_activity"), label: "Review build" };
  }
  if (operation.startsWith("catalogue/import-")) {
    return { href: getStudioRoute(config, "build_activity"), label: "Review build" };
  }
  if (scope.href) return { href: scope.href, label: "Open record" };
  return { href: "", label: "" };
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
    event: normalizeText(a.event_label),
    status: normalizeText(a.status),
    scope: normalizeText(a.scope_label),
    attention: normalizeText(a.attention_label)
  };
  const otherFieldMap = {
    event: normalizeText(b.event_label),
    status: normalizeText(b.status),
    scope: normalizeText(b.scope_label),
    attention: normalizeText(b.attention_label)
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
    const affectedText = summarizeAffected(entry.affected);
    return `
      <li class="tagStudioList__row activityReport__row activityReport__row--catalogue">
        <span class="activityReport__cell activityReport__cell--time">
          <span class="activityReport__title">${escapeHtml(timeText)}</span>
        </span>
        <span class="activityReport__cell">
          <span class="activityReport__title">${escapeHtml(normalizeText(entry.event_label) || "Updated")}</span>
          <span class="activityReport__meta">${escapeHtml(normalizeText(entry.summary) || "—")}</span>
        </span>
        <span class="activityReport__cell">
          <span class="activityReport__pill" data-status="${escapeHtml(status)}">${escapeHtml(statusText(config, status))}</span>
        </span>
        <span class="activityReport__cell">
          ${scope.href ? `<a class="activityReport__link" href="${escapeHtml(scope.href)}">${escapeHtml(scope.label)}</a>` : `<span class="activityReport__title">${escapeHtml(scope.label)}</span>`}
          ${affectedText ? `<span class="activityReport__meta">${escapeHtml(affectedText)}</span>` : ""}
        </span>
        <span class="activityReport__cell">
          <span class="activityReport__title">${escapeHtml(normalizeText(entry.attention_label) || "review")}</span>
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
    <div class="tagStudioList__head activityReport__head activityReport__head--catalogue">
      ${sortButton("time", state.sortKey, state.sortDir)}
      ${sortButton("event", state.sortKey, state.sortDir)}
      ${sortButton("status", state.sortKey, state.sortDir)}
      ${sortButton("scope", state.sortKey, state.sortDir)}
      ${sortButton("attention", state.sortKey, state.sortDir)}
      <span class="tagStudioList__headLabel">next</span>
    </div>
    <ol class="tagStudioList__rows activityReport__rows">${renderRows(config, entries)}</ol>
  `;
}

async function loadFeed(config) {
  const url = getStudioDataPath(config, "catalogue_activity");
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
  const root = document.getElementById("catalogueActivityRoot");
  const statusNode = document.getElementById("catalogueActivityStatus");
  const metaNode = document.getElementById("catalogueActivityMeta");
  const listNode = document.getElementById("catalogueActivityList");
  const emptyNode = document.getElementById("catalogueActivityEmpty");
  if (!root || !statusNode || !metaNode || !listNode || !emptyNode) return;

  try {
    const config = await loadStudioConfig();
    const payload = await loadFeed(config);
    const entries = Array.isArray(payload && payload.entries) ? payload.entries : [];
    metaNode.textContent = entries.length === 1
      ? getStudioText(config, "catalogue_activity.meta_summary_one", "1 recent catalogue entry")
      : getStudioText(config, "catalogue_activity.meta_summary", "{count} recent catalogue entries", { count: entries.length });

    if (!entries.length) {
      emptyNode.textContent = getStudioText(config, "catalogue_activity.empty_state", "No catalogue activity yet.");
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
    console.warn("catalogue_activity: load failed", error);
    try {
      const config = await loadStudioConfig();
      statusNode.textContent = getStudioText(config, "catalogue_activity.load_failed_error", "Failed to load catalogue activity.");
    } catch (_configError) {
      statusNode.textContent = "Failed to load catalogue activity.";
    }
  }
}

init();
