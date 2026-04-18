import { getStudioDataPath, getStudioText, loadStudioConfig } from "./studio-config.js";

function formatTimestamp(value) {
  const raw = String(value || "").trim();
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
  if (status === "completed") return getStudioText(config, "build_activity.status_completed", "completed");
  if (status === "failed") return getStudioText(config, "build_activity.status_failed", "failed");
  return getStudioText(config, "build_activity.status_other", "status unknown");
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

function renderDetailList(groups, labels, noneLabel) {
  const items = [];
  Object.keys(labels).forEach((key) => {
    const label = labels[key];
    items.push(`
      <li class="buildActivityEntry__detailItem">
        <span class="buildActivityEntry__detailLabel">${label}</span>
        <span class="buildActivityEntry__detailValue">${summarizeGroup(groups && groups[key], noneLabel)}</span>
      </li>
    `);
  });
  return `<ul class="buildActivityEntry__detailList">${items.join("")}</ul>`;
}

function renderActions(actions, noneLabel) {
  const entries = Object.entries(actions || {}).filter(([, value]) => {
    if (typeof value === "boolean") return value;
    if (typeof value === "number") return value > 0;
    return Boolean(value);
  });
  if (!entries.length) return `<p class="buildActivityEntry__detailEmpty">${noneLabel}</p>`;
  const items = entries.map(([key, value]) => `
    <li class="buildActivityEntry__detailItem">
      <span class="buildActivityEntry__detailLabel">${String(key).replace(/_/g, " ")}</span>
      <span class="buildActivityEntry__detailValue">${String(value)}</span>
    </li>
  `);
  return `<ul class="buildActivityEntry__detailList">${items.join("")}</ul>`;
}

function renderEntry(config, entry) {
  const sourceLabels = {
    works: "works",
    series: "series",
    work_details: "work details",
    moments: "moments"
  };
  const workbookLabels = {
    works: "works",
    series: "series",
    work_details: "work details",
    moments: "moments"
  };
  const mediaLabels = {
    work: "works",
    work_details: "work details",
    moment: "moments"
  };
  const noneLabel = getStudioText(config, "build_activity.none", "none");
  const timeText = formatTimestamp(entry && entry.time_utc);
  const summary = String((entry && entry.summary) || "").trim() || noneLabel;
  const statusText = textForStatus(config, entry && entry.status);
  const plannerMode = String((entry && entry.planner_mode) || "").trim();
  const sourceSection = renderDetailList(entry && entry.changes && entry.changes.source, sourceLabels, noneLabel);

  return `
    <li class="buildActivityEntry">
      <details class="buildActivityEntry__details">
        <summary class="buildActivityEntry__summary">
          <span class="buildActivityEntry__time">${timeText}</span>
          <span class="buildActivityEntry__status" data-status="${String((entry && entry.status) || "").trim()}">${statusText}</span>
          <span class="buildActivityEntry__headline">${summary}</span>
        </summary>
        <div class="buildActivityEntry__body">
          ${plannerMode ? `<p class="buildActivityEntry__meta">planner: ${plannerMode}</p>` : ""}
          <section class="buildActivityEntry__section">
            <h3 class="buildActivityEntry__sectionTitle">${getStudioText(config, "build_activity.detail_source", "source")}</h3>
            ${sourceSection}
          </section>
          <section class="buildActivityEntry__section">
            <h3 class="buildActivityEntry__sectionTitle">${getStudioText(config, "build_activity.detail_workbook", "workbook")}</h3>
            ${renderDetailList(entry && entry.changes && entry.changes.workbook, workbookLabels, noneLabel)}
          </section>
          <section class="buildActivityEntry__section">
            <h3 class="buildActivityEntry__sectionTitle">${getStudioText(config, "build_activity.detail_media", "media")}</h3>
            ${renderDetailList(entry && entry.changes && entry.changes.media, mediaLabels, noneLabel)}
          </section>
          <section class="buildActivityEntry__section">
            <h3 class="buildActivityEntry__sectionTitle">${getStudioText(config, "build_activity.detail_actions", "actions")}</h3>
            ${renderActions(entry && entry.actions, noneLabel)}
          </section>
          <section class="buildActivityEntry__section">
            <h3 class="buildActivityEntry__sectionTitle">${getStudioText(config, "build_activity.detail_results", "results")}</h3>
            ${renderActions(entry && entry.results, noneLabel)}
          </section>
        </div>
      </details>
    </li>
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
    const count = entries.length;
    metaNode.textContent = count === 1
      ? getStudioText(config, "build_activity.meta_summary_one", "1 recent build entry")
      : getStudioText(config, "build_activity.meta_summary", "{count} recent build entries", { count });

    if (!count) {
      emptyNode.textContent = getStudioText(config, "build_activity.empty_state", "No build activity yet.");
      emptyNode.hidden = false;
      root.hidden = false;
      statusNode.hidden = true;
      return;
    }

    listNode.innerHTML = entries.map((entry) => renderEntry(config, entry)).join("");
    root.hidden = false;
    statusNode.hidden = true;
  } catch (_error) {
    statusNode.textContent = "Failed to load build activity.";
    try {
      const config = await loadStudioConfig();
      statusNode.textContent = getStudioText(config, "build_activity.load_failed_error", "Failed to load build activity.");
    } catch (_configError) {
    }
  }
}

init();
