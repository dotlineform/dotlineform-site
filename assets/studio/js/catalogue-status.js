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
  { key: "series", label: "series", pathKey: "catalogue_series", objectKey: "series", idField: "series_id", routeKey: "catalogue_series_editor", paramKey: "series" },
  { key: "work_files", label: "work files", pathKey: "catalogue_work_files", objectKey: "work_files", idField: "file_uid", routeKey: "catalogue_work_file_editor", paramKey: "file" },
  { key: "work_links", label: "work links", pathKey: "catalogue_work_links", objectKey: "work_links", idField: "link_uid", routeKey: "catalogue_work_link_editor", paramKey: "link" }
];

const SORT_KEYS = ["id", "type", "status", "title", "reference"];

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

function recordReference(record) {
  const parts = [];
  if (record.work_id) parts.push(`work ${record.work_id}`);
  if (record.series_id) parts.push(`series ${record.series_id}`);
  if (record.detail_id) parts.push(`detail ${record.detail_id}`);
  return parts.join(" · ");
}

function makeEntry(family, key, record) {
  const id = normalizeText(record[family.idField] || key);
  const status = displayStatus(record.status);
  const title = recordTitle(record);
  const reference = recordReference(record);
  return {
    family: family.key,
    familyLabel: family.label,
    id,
    status,
    title,
    reference,
    editorHref: "",
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

function renderKey(keyNode, counts, activeFamily) {
  const total = Object.values(counts).reduce((sum, value) => sum + Number(value || 0), 0);
  const buttons = [
    `<button type="button" class="tagStudio__keyPill tagStudioFilters__allBtn" data-family="all" data-state="${activeFamily === "all" ? "active" : ""}">all ${total}</button>`
  ];
  FAMILIES.forEach((family) => {
    const count = Number(counts[family.key] || 0);
    buttons.push(`<button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" data-family="${family.key}" data-state="${activeFamily === family.key ? "active" : ""}">${escapeHtml(family.label)} ${count}</button>`);
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
    if (state.activeFamily !== "all" && entry.family !== state.activeFamily) return false;
    if (query && !entry.searchText.includes(query)) return false;
    return true;
  });
  const sorted = filtered.slice().sort((a, b) => compareEntries(a, b, state.sortKey, state.sortDir));

  state.metaNode.textContent = sorted.length === 1
    ? getStudioText(state.config, "catalogue_status.meta_summary_one", "1 non-published source record")
    : getStudioText(state.config, "catalogue_status.meta_summary", "{count} non-published source records", { count: sorted.length });
  renderKey(state.keyNode, state.counts, state.activeFamily);
  renderList(state.listNode, sorted, state);
  state.emptyNode.hidden = sorted.length > 0;
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
      const button = event.target && event.target.closest ? event.target.closest("[data-family]") : null;
      if (!button) return;
      state.activeFamily = normalizeText(button.getAttribute("data-family")) || "all";
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

    emptyNode.textContent = getStudioText(config, "catalogue_status.empty_state", "No non-published catalogue source records.");
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
