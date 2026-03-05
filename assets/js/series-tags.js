const GROUPS = ["subject", "domain", "form", "theme"];
const GROUP_INFO_PAGE_PATH = "/studio/tag-groups/";

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initSeriesTagsPage);
} else {
  initSeriesTagsPage();
}

async function initSeriesTagsPage() {
  const mount = document.getElementById("series-tags");
  if (!mount) return;

  const seriesData = await getSeriesData();
  if (!seriesData.length) {
    mount.innerHTML = `<p class="tagStudio__empty">none</p>`;
    return;
  }

  try {
    const [assignmentsJson, registryJson] = await Promise.all([
      fetchJson("/assets/data/tag_assignments.json"),
      fetchJson("/assets/data/tag_registry.json")
    ]);

    const assignmentsSeries = assignmentsJson && typeof assignmentsJson.series === "object"
      ? assignmentsJson.series
      : {};
    const registry = buildRegistryLookup(registryJson);
    const state = {
      mount,
      seriesData,
      assignmentsSeries,
      registry,
      groupDescriptions: new Map(),
      filterGroup: "all"
    };
    try {
      const groupsJson = await fetchJson("/assets/data/tag_groups.json");
      state.groupDescriptions = buildGroupDescriptionMap(groupsJson);
    } catch (error) {
      state.groupDescriptions = new Map();
    }
    renderTable(state);
    mount.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-group]");
      if (!button) return;
      const next = normalize(button.getAttribute("data-group"));
      state.filterGroup = GROUPS.includes(next) ? next : "all";
      renderTable(state);
    });
  } catch (error) {
    mount.innerHTML = `<div class="tagStudioError">Failed to load series tag data.</div>`;
  }
}

async function getSeriesData() {
  const inline = parseSeriesDataFromInline();
  if (inline.length) return inline;
  return fetchSeriesDataFromIndex();
}

function parseSeriesDataFromInline() {
  const basePath = getBasePath();
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
          url: buildSeriesEditorUrl(seriesId, basePath)
        };
      })
      .filter((entry) => entry.seriesId && entry.title)
      .sort((a, b) => a.title.localeCompare(b.title, undefined, { sensitivity: "base" }));
  } catch (error) {
    return [];
  }
}

async function fetchSeriesDataFromIndex() {
  const basePath = getBasePath();
  const seriesIndexUrl = `${basePath}/assets/data/series_index.json`.replace(/\/{2,}/g, "/");
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
        url: buildSeriesEditorUrl(sid, basePath)
      };
    })
    .filter((entry) => entry.seriesId && entry.title)
    .sort((a, b) => a.title.localeCompare(b.title, undefined, { sensitivity: "base" }));
}

function getBasePath() {
  const baseEl = document.querySelector("base[href]");
  const baseHref = String((baseEl && baseEl.getAttribute("href")) || "/").trim();
  let basePath = "/";
  try {
    basePath = new URL(baseHref, window.location.origin).pathname || "/";
  } catch (error) {
    basePath = "/";
  }
  return basePath.replace(/\/+$/, "");
}

function buildSeriesEditorUrl(seriesId, basePath) {
  const sid = normalize(seriesId);
  return `${basePath}/studio/series-tag-editor/?series=${encodeURIComponent(sid)}`.replace(/\/{2,}/g, "/");
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
    if (!GROUPS.includes(groupId) || !description) continue;
    out.set(groupId, description);
  }
  return out;
}

function renderTable(state) {
  const rowsHtml = state.seriesData.map((series) => {
    const assigned = getSeriesTags(state.assignmentsSeries, series.seriesId);
    const metrics = computeMetrics(assigned, state.registry);
    const rag = computeRag(metrics);
    const tooltip = buildTooltip(metrics);
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
      : `<li class="tagStudio__empty">none</li>`;

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
        <div class="seriesTags__col seriesTags__col--title">series</div>
        <div class="seriesTags__col seriesTags__col--count">status</div>
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
  const groupButtons = GROUPS.map((group) => {
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
      <button type="button" class="tagStudio__button tagRegistry__allBtn${allActiveClass}" data-group="all">All tags</button>
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
      title="Open group descriptions in a new tab"
      aria-label="Open group descriptions in a new tab"
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
    const className = GROUPS.includes(known.group)
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
  const className = GROUPS.includes(groupPrefix)
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

function computeMetrics(assignedTags, registry) {
  const counts = {
    subject: 0,
    domain: 0,
    form: 0,
    theme: 0
  };
  let nUnknown = 0;
  let nDeprecated = 0;
  let nTotal = 0;

  const uniqueTags = Array.from(
    new Set((Array.isArray(assignedTags) ? assignedTags : []).map((tag) => normalize(tag)).filter(Boolean))
  );

  for (const tagId of uniqueTags) {
    nTotal += 1;
    const reg = registry.get(tagId);
    if (!reg) {
      nUnknown += 1;
      continue;
    }
    if (reg.group in counts) counts[reg.group] += 1;
    if (reg.status !== "active") nDeprecated += 1;
  }

  const presentGroups = GROUPS.filter((group) => counts[group] > 0);
  const missingGroups = GROUPS.filter((group) => counts[group] === 0);
  const groupsPresent = presentGroups.length;
  const completenessBase = groupsPresent / 4;
  const tagBonus = (Math.min(nTotal, 6) / 6) * 0.25;
  const completeness = Math.min(1, completenessBase + tagBonus);

  return {
    nTotal,
    nUnknown,
    nDeprecated,
    counts,
    groupsPresent,
    presentGroups,
    missingGroups,
    completeness
  };
}

function computeRag(metrics) {
  if (metrics.nTotal === 0 || metrics.nUnknown > 0) {
    return "red";
  }

  const missingForm = metrics.counts.form === 0;
  const missingTheme = metrics.counts.theme === 0;
  if (
    metrics.groupsPresent === 1 ||
    metrics.nTotal < 3 ||
    metrics.nDeprecated > 0 ||
    (missingForm && missingTheme)
  ) {
    return "amber";
  }

  return "green";
}

function buildTooltip(metrics) {
  const groupsLabel = metrics.presentGroups.length ? metrics.presentGroups.join(", ") : "none";
  const missingLabel = metrics.missingGroups.length ? metrics.missingGroups.join(", ") : "none";
  return (
    `tags: ${metrics.nTotal}; groups: ${groupsLabel}; missing: ${missingLabel}; ` +
    `unknown: ${metrics.nUnknown}; deprecated: ${metrics.nDeprecated}; ` +
    `completeness: ${metrics.completeness.toFixed(2)}`
  );
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
