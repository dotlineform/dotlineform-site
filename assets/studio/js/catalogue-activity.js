import { getStudioDataPath, getStudioText, loadStudioConfig } from "./studio-config.js";

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

function textForStatus(config, status) {
  if (status === "completed") return getStudioText(config, "catalogue_activity.status_completed", "completed");
  if (status === "failed") return getStudioText(config, "catalogue_activity.status_failed", "failed");
  return getStudioText(config, "catalogue_activity.status_other", "status unknown");
}

function summarizeGroup(group, noneLabel) {
  const count = Number(group && group.count) || 0;
  if (!count) return noneLabel;
  const sampleIds = Array.isArray(group && group.sample_ids) ? group.sample_ids : [];
  const sampleText = sampleIds.length ? sampleIds.join(", ") : "";
  const truncated = Number(group && group.truncated) || 0;
  if (!sampleText && !truncated) return String(count);
  if (truncated > 0) return `${count} (${sampleText}, +${truncated} more)`;
  return `${count} (${sampleText})`;
}

function renderAffected(affected, noneLabel) {
  const labels = {
    works: "works",
    series: "series",
    work_details: "work details"
  };
  const items = Object.keys(labels).map((key) => `
    <li class="buildActivityEntry__detailItem">
      <span class="buildActivityEntry__detailLabel">${labels[key]}</span>
      <span class="buildActivityEntry__detailValue">${escapeHtml(summarizeGroup(affected && affected[key], noneLabel))}</span>
    </li>
  `);
  return `<ul class="buildActivityEntry__detailList">${items.join("")}</ul>`;
}

function renderEntry(config, entry) {
  const noneLabel = getStudioText(config, "catalogue_activity.none", "none");
  const timeText = formatTimestamp(entry && entry.time_utc);
  const summary = normalizeText(entry && entry.summary) || noneLabel;
  const status = normalizeText(entry && entry.status);
  const statusText = textForStatus(config, status);
  const operation = normalizeText(entry && entry.operation);
  const kind = normalizeText(entry && entry.kind);
  const logRef = normalizeText(entry && entry.log_ref);

  return `
    <li class="buildActivityEntry catalogueActivityEntry">
      <details class="buildActivityEntry__details">
        <summary class="buildActivityEntry__summary">
          <span class="buildActivityEntry__time">${escapeHtml(timeText)}</span>
          <span class="buildActivityEntry__status" data-status="${escapeHtml(status)}">${escapeHtml(statusText)}</span>
          <span class="buildActivityEntry__headline">${escapeHtml(summary)}</span>
        </summary>
        <div class="buildActivityEntry__body">
          ${operation ? `<p class="buildActivityEntry__meta">operation: ${escapeHtml(operation)}</p>` : ""}
          ${kind ? `<p class="buildActivityEntry__meta">kind: ${escapeHtml(kind)}</p>` : ""}
          <section class="buildActivityEntry__section">
            <h3 class="buildActivityEntry__sectionTitle">${getStudioText(config, "catalogue_activity.detail_affected", "affected")}</h3>
            ${renderAffected(entry && entry.affected, noneLabel)}
          </section>
          ${logRef ? `
            <section class="buildActivityEntry__section">
              <h3 class="buildActivityEntry__sectionTitle">${getStudioText(config, "catalogue_activity.detail_log", "log")}</h3>
              <p class="buildActivityEntry__detailEmpty">${escapeHtml(logRef)}</p>
            </section>
          ` : ""}
        </div>
      </details>
    </li>
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

    listNode.innerHTML = entries.map((entry) => renderEntry(config, entry)).join("");
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
