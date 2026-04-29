import {
  getStudioDataPath,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  fetchJson
} from "./studio-data.js";

const FAMILIES = [
  { key: "works", label: "works", pathKey: "catalogue_works", objectKey: "works", idField: "work_id", routeKey: "catalogue_work_editor", paramKey: "work" },
  { key: "work_details", label: "work details", pathKey: "catalogue_work_details", objectKey: "work_details", idField: "detail_uid", routeKey: "catalogue_work_detail_editor", paramKey: "detail" },
  { key: "series", label: "series", pathKey: "catalogue_series", objectKey: "series", idField: "series_id", routeKey: "catalogue_series_editor", paramKey: "series" }
];

const SORT_KEYS = ["id", "type", "status", "title", "reference"];
const DRAFT_WORKS_VIEW = "draft-works";
const DRAFT_SERIES_VIEW = "draft-series";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeSearch(value) {
  return normalizeText(value).toLowerCase();
}

function escapeHtml(value) {
  return normalizeText(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function displayStatus(value) {
  return normalizeText(value) || "(blank)";
}

function recordTitle(record) {
  return normalizeText(record.title || record.label || record.filename || record.url || record.project_filename) || "(untitled)";
}

function recordReference(record, family) {
  const parts = [];
  if (family.key === "works" && Array.isArray(record.series_ids) && record.series_ids.length) {
    parts.push(`series ${record.series_ids.map((item) => normalizeText(item)).filter(Boolean).join(", ")}`);
  } else if (family.key === "series") {
    const primaryWorkId = normalizeText(record.primary_work_id);
    if (primaryWorkId) parts.push(`primary work ${primaryWorkId}`);
  } else if (family.key === "work_details") {
    if (record.work_id) parts.push(`work ${record.work_id}`);
    if (record.detail_id) parts.push(`detail ${record.detail_id}`);
  }
  return parts.join(" · ");
}

function makeEntry(family, key, record) {
  const id = normalizeText(record[family.idField] || key);
  const normalizedStatus = normalizeSearch(record.status);
  const status = displayStatus(record.status);
  const title = recordTitle(record);
  const reference = recordReference(record, family);
  return {
    family: family.key,
    familyLabel: family.label,
    id,
    normalizedStatus,
    status,
    title,
    reference,
    editorHref: "",
    isDraftWork: family.key === "works" && normalizedStatus === "draft",
    isDraftSeries: family.key === "series" && normalizedStatus === "draft",
    searchText: normalizeSearch(`${family.label} ${id} ${status} ${title} ${reference}`)
  };
}

async function loadFamily(config, family) {
  const url = getStudioDataPath(config, family.pathKey);
  if (!url) return [];
  const payload = await fetchJson(url);
  const records = payload && payload[family.objectKey] && typeof payload[family.objectKey] === "object"
    ? payload[family.objectKey]
    : {};
  return Object.keys(records).map((key) => {
    const record = records[key] && typeof records[key] === "object" ? records[key] : {};
    return makeEntry(family, key, record);
  }).filter((entry) => normalizeSearch(entry.status) !== "published");
}

function buildFamilyCounts(entries) {
  const counts = {};
  FAMILIES.forEach((family) => {
    counts[family.key] = 0;
  });
  entries.forEach((entry) => {
    counts[entry.family] = (counts[entry.family] || 0) + 1;
  });
  return counts;
}

function renderKey(keyNode, counts, activeFamily, activeView, draftWorkCount, draftSeriesCount, config) {
  const total = Object.values(counts).reduce((sum, value) => sum + Number(value || 0), 0);
  const draftWorksLabel = getStudioText(config, "catalogue_status.draft_works_filter_label", "draft works");
  const draftSeriesLabel = getStudioText(config, "catalogue_status.draft_series_filter_label", "draft series");
  const allLabel = getStudioText(config, "catalogue_status.all_filter_label", "all");
  const buttons = [
    `<button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" data-view="${DRAFT_WORKS_VIEW}" data-state="${activeView === DRAFT_WORKS_VIEW ? "active" : ""}">${escapeHtml(draftWorksLabel)} ${draftWorkCount}</button>`,
    `<button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" data-view="${DRAFT_SERIES_VIEW}" data-state="${activeView === DRAFT_SERIES_VIEW ? "active" : ""}">${escapeHtml(draftSeriesLabel)} ${draftSeriesCount}</button>`,
    `<button type="button" class="tagStudio__keyPill tagStudioFilters__allBtn" data-family="all" data-state="${activeView === "all" && activeFamily === "all" ? "active" : ""}">${escapeHtml(allLabel)} ${total}</button>`
  ];
  FAMILIES.forEach((family) => {
    const count = Number(counts[family.key] || 0);
    buttons.push(`<button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" data-family="${family.key}" data-state="${activeView === "all" && activeFamily === family.key ? "active" : ""}">${escapeHtml(family.label)} ${count}</button>`);
  });
  keyNode.innerHTML = buttons.join("");
}

function renderList(listNode, entries, state) {
  if (!entries.length) {
    listNode.innerHTML = "";
    return;
  }
  const rows = entries.map((entry) => `
    <li class="tagStudioList__row catalogueStatusRow">
      <span class="catalogueStatusRow__id">${entry.editorHref ? `<a href="${escapeHtml(entry.editorHref)}">${escapeHtml(entry.id)}</a>` : escapeHtml(entry.id)}</span>
      <span class="catalogueStatusRow__family">${escapeHtml(entry.familyLabel)}</span>
      <span class="catalogueStatusRow__status">${escapeHtml(entry.status)}</span>
      <span class="catalogueStatusRow__title">${escapeHtml(entry.title)}</span>
      <span class="catalogueStatusRow__reference">${escapeHtml(entry.reference)}</span>
    </li>
  `);
  listNode.innerHTML = `
    <div class="tagStudioList__head catalogueStatusPage__head">
      ${renderSortButton("id", state.sortKey, state.sortDir)}
      ${renderSortButton("type", state.sortKey, state.sortDir)}
      ${renderSortButton("status", state.sortKey, state.sortDir)}
      ${renderSortButton("title", state.sortKey, state.sortDir)}
      ${renderSortButton("reference", state.sortKey, state.sortDir)}
    </div>
    <ul class="tagStudioList__rows catalogueStatusPage__rows">${rows.join("")}</ul>
  `;
}

function renderSortButton(label, activeKey, activeDir) {
  const buttonState = activeKey === label ? "active" : "";
  const suffix = activeKey === label ? (activeDir === "desc" ? " ↓" : " ↑") : "";
  return `<button type="button" class="tagStudioList__sortBtn" data-sort-key="${escapeHtml(label)}" data-state="${buttonState}">${escapeHtml(`${label}${suffix}`)}</button>`;
}

function compareEntries(a, b, sortKey, sortDir) {
  const direction = sortDir === "desc" ? -1 : 1;
  const fieldA = normalizeText(sortKey === "type" ? a.familyLabel : a[sortKey]);
  const fieldB = normalizeText(sortKey === "type" ? b.familyLabel : b[sortKey]);
  const compare = fieldA.localeCompare(fieldB, undefined, { numeric: true, sensitivity: "base" });
  if (compare !== 0) return compare * direction;
  if (a.family !== b.family) {
    return a.family.localeCompare(b.family, undefined, { numeric: true, sensitivity: "base" });
  }
  return a.id.localeCompare(b.id, undefined, { numeric: true, sensitivity: "base" });
}

function applyFilters(state) {
  const query = normalizeSearch(state.searchNode.value);
  const filtered = state.entries.filter((entry) => {
    if (state.activeView === DRAFT_WORKS_VIEW && !entry.isDraftWork) return false;
    if (state.activeView === DRAFT_SERIES_VIEW && !entry.isDraftSeries) return false;
    if (state.activeFamily !== "all" && entry.family !== state.activeFamily) return false;
    if (query && !entry.searchText.includes(query)) return false;
    return true;
  });
  const sorted = filtered.slice().sort((a, b) => compareEntries(a, b, state.sortKey, state.sortDir));

  if (state.activeView === DRAFT_WORKS_VIEW) {
    state.metaNode.textContent = sorted.length === 1
      ? getStudioText(state.config, "catalogue_status.draft_works_summary_one", "1 draft work record")
      : getStudioText(state.config, "catalogue_status.draft_works_summary", "{count} draft work records", { count: sorted.length });
  } else if (state.activeView === DRAFT_SERIES_VIEW) {
    state.metaNode.textContent = sorted.length === 1
      ? getStudioText(state.config, "catalogue_status.draft_series_summary_one", "1 draft series record")
      : getStudioText(state.config, "catalogue_status.draft_series_summary", "{count} draft series records", { count: sorted.length });
  } else {
    state.metaNode.textContent = sorted.length === 1
      ? getStudioText(state.config, "catalogue_status.meta_summary_one", "1 non-published source record")
      : getStudioText(state.config, "catalogue_status.meta_summary", "{count} non-published source records", { count: sorted.length });
  }
  renderKey(state.keyNode, state.counts, state.activeFamily, state.activeView, state.draftWorkCount, state.draftSeriesCount, state.config);
  renderList(state.listNode, sorted, state);
  if (state.activeView === DRAFT_WORKS_VIEW) {
    state.emptyNode.textContent = getStudioText(state.config, "catalogue_status.draft_works_empty_state", "No draft work records.");
  } else if (state.activeView === DRAFT_SERIES_VIEW) {
    state.emptyNode.textContent = getStudioText(state.config, "catalogue_status.draft_series_empty_state", "No draft series records.");
  } else {
    state.emptyNode.textContent = getStudioText(state.config, "catalogue_status.empty_state", "No non-published catalogue source records.");
  }
  state.emptyNode.hidden = sorted.length > 0;
}

function initialViewFromUrl() {
  const view = normalizeText(new URLSearchParams(window.location.search).get("view"));
  return view === DRAFT_WORKS_VIEW || view === DRAFT_SERIES_VIEW ? view : "all";
}

function syncStatusUrl(state) {
  const url = new URL(window.location.href);
  if (state.activeView === DRAFT_WORKS_VIEW || state.activeView === DRAFT_SERIES_VIEW) {
    url.searchParams.set("view", state.activeView);
  } else {
    url.searchParams.delete("view");
  }
  window.history.replaceState({}, "", url.toString());
}

async function init() {
  const root = document.getElementById("catalogueStatusRoot");
  const loadingNode = document.getElementById("catalogueStatusLoading");
  const emptyNode = document.getElementById("catalogueStatusEmpty");
  const keyNode = document.getElementById("catalogueStatusKey");
  const searchNode = document.getElementById("catalogueStatusSearch");
  const metaNode = document.getElementById("catalogueStatusMeta");
  const listNode = document.getElementById("catalogueStatusList");
  if (!root || !loadingNode || !emptyNode || !keyNode || !searchNode || !metaNode || !listNode) return;

  try {
    const config = await loadStudioConfig();
    const groups = await Promise.all(FAMILIES.map((family) => loadFamily(config, family)));
    const entries = groups.flat().sort((a, b) => {
      if (a.family !== b.family) return a.family.localeCompare(b.family);
      return a.id.localeCompare(b.id, undefined, { numeric: true, sensitivity: "base" });
    });
    entries.forEach((entry) => {
      const family = FAMILIES.find((item) => item.key === entry.family);
      if (!family) return;
      const route = getStudioRoute(config, family.routeKey);
      if (!route) return;
      entry.editorHref = `${route}?${family.paramKey}=${encodeURIComponent(entry.id)}`;
    });
    const state = {
      config,
      entries,
      counts: buildFamilyCounts(entries),
      draftWorkCount: entries.filter((entry) => entry.isDraftWork).length,
      draftSeriesCount: entries.filter((entry) => entry.isDraftSeries).length,
      activeView: initialViewFromUrl(),
      activeFamily: "all",
      sortKey: "type",
      sortDir: "asc",
      keyNode,
      searchNode,
      metaNode,
      listNode,
      emptyNode
    };

    keyNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-family],[data-view]") : null;
      if (!button) return;
      const view = normalizeText(button.getAttribute("data-view"));
      if (view === DRAFT_WORKS_VIEW || view === DRAFT_SERIES_VIEW) {
        state.activeView = view;
        state.activeFamily = "all";
      } else {
        state.activeView = "all";
        state.activeFamily = normalizeText(button.getAttribute("data-family")) || "all";
      }
      syncStatusUrl(state);
      applyFilters(state);
    });
    listNode.addEventListener("click", (event) => {
      const button = event.target && event.target.closest ? event.target.closest("[data-sort-key]") : null;
      if (!button) return;
      const sortKey = normalizeText(button.getAttribute("data-sort-key"));
      if (!SORT_KEYS.includes(sortKey)) return;
      if (state.sortKey === sortKey) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = sortKey;
        state.sortDir = sortKey === "status" ? "desc" : "asc";
      }
      applyFilters(state);
    });
    searchNode.addEventListener("input", () => applyFilters(state));

    applyFilters(state);
    root.hidden = false;
    loadingNode.hidden = true;
  } catch (error) {
    console.warn("catalogue_status: load failed", error);
    try {
      const config = await loadStudioConfig();
      loadingNode.textContent = getStudioText(config, "catalogue_status.load_failed_error", "Failed to load catalogue status.");
    } catch (_configError) {
      loadingNode.textContent = "Failed to load catalogue status.";
    }
  }
}

init();
