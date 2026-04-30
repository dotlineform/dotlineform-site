import {
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  loadStudioLookupJson
} from "./studio-data.js";
import { probeCatalogueHealth } from "./studio-transport.js";

const FAMILIES = [
  { key: "series", label: "series", singular: "series", pathKey: "catalogue_series", objectKey: "series", idField: "series_id", routeKey: "catalogue_series_editor", paramKey: "series" },
  { key: "works", label: "works", singular: "work", pathKey: "catalogue_works", objectKey: "works", idField: "work_id", routeKey: "catalogue_work_editor", paramKey: "work" },
  { key: "work_details", label: "work details", singular: "work detail", pathKey: "catalogue_work_details", objectKey: "work_details", idField: "detail_uid", routeKey: "catalogue_work_detail_editor", paramKey: "detail" },
  { key: "moments", label: "moments", singular: "moment", pathKey: "catalogue_moments", objectKey: "moments", idField: "moment_id", routeKey: "catalogue_moment_editor", paramKey: "moment" }
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
  } else if (family.key === "moments") {
    const date = normalizeText(record.date || record.date_display);
    if (date) parts.push(date);
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
    searchText: normalizeSearch(`${family.label} ${id} ${status} ${title} ${reference}`)
  };
}

async function loadFamily(config, family, serverAvailable) {
  const payload = await loadStudioLookupJson(config, family.pathKey, {
    cache: "no-store",
    catalogueServerAvailable: serverAvailable
  });
  const records = payload && payload[family.objectKey] && typeof payload[family.objectKey] === "object"
    ? payload[family.objectKey]
    : {};
  return Object.keys(records).map((key) => {
    const record = records[key] && typeof records[key] === "object" ? records[key] : {};
    return makeEntry(family, key, record);
  }).filter((entry) => entry.normalizedStatus === "draft");
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
  keyNode.innerHTML = FAMILIES.map((family) => {
    const count = Number(counts[family.key] || 0);
    return `<button type="button" class="tagStudio__keyPill tagStudioFilters__groupBtn" data-family="${family.key}" data-state="${activeFamily === family.key ? "active" : ""}">${escapeHtml(family.label)} ${count}</button>`;
  }).join("");
}

function renderList(listNode, entries, state) {
  if (!entries.length) {
    listNode.innerHTML = "";
    return;
  }
  const rows = entries.map((entry) => `
    <li class="tagStudioList__row catalogueStatusRow">
      <span class="catalogueStatusRow__id">${entry.editorHref ? `<a href="${escapeHtml(entry.editorHref)}" target="_blank" rel="noopener">${escapeHtml(entry.id)}</a>` : escapeHtml(entry.id)}</span>
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
    if (entry.family !== state.activeFamily) return false;
    if (query && !entry.searchText.includes(query)) return false;
    return true;
  });
  const sorted = filtered.slice().sort((a, b) => compareEntries(a, b, state.sortKey, state.sortDir));
  const activeFamily = FAMILIES.find((family) => family.key === state.activeFamily) || FAMILIES[0];
  const familyLabel = sorted.length === 1 ? activeFamily.singular : activeFamily.label;

  state.metaNode.textContent = sorted.length === 1
    ? getStudioText(state.config, "catalogue_status.meta_summary_one", "1 draft {family} record", { family: familyLabel })
    : getStudioText(state.config, "catalogue_status.meta_summary", "{count} draft {family} records", { count: sorted.length, family: familyLabel });
  renderKey(state.keyNode, state.counts, state.activeFamily);
  renderList(state.listNode, sorted, state);
  state.emptyNode.textContent = getStudioText(state.config, "catalogue_status.empty_state", "No draft {family} records.", { family: activeFamily.label });
  state.emptyNode.hidden = sorted.length > 0;
}

function normalizeFamilyKey(value) {
  const key = normalizeText(value).replace(/-/g, "_");
  if (key === "draft_works") return "works";
  if (key === "draft_series") return "series";
  if (key === "draft_work_details") return "work_details";
  if (key === "draft_moments") return "moments";
  return FAMILIES.some((family) => family.key === key) ? key : "";
}

function initialFamilyFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return normalizeFamilyKey(params.get("family")) || normalizeFamilyKey(params.get("view")) || FAMILIES[0].key;
}

function syncStatusUrl(state) {
  const url = new URL(window.location.href);
  url.searchParams.delete("view");
  if (state.activeFamily && state.activeFamily !== FAMILIES[0].key) {
    url.searchParams.set("family", state.activeFamily);
  } else {
    url.searchParams.delete("family");
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
    const serverAvailable = await probeCatalogueHealth();
    if (!serverAvailable) {
      loadingNode.textContent = getStudioText(config, "catalogue_status.server_unavailable_hint", "Local catalogue server unavailable. Catalogue drafts are disabled.");
      root.hidden = false;
      return;
    }
    const groups = await Promise.all(FAMILIES.map((family) => loadFamily(config, family, serverAvailable)));
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
      activeFamily: initialFamilyFromUrl(),
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
      state.activeFamily = normalizeFamilyKey(button.getAttribute("data-family")) || FAMILIES[0].key;
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
      loadingNode.textContent = getStudioText(config, "catalogue_status.load_failed_error", "Failed to load catalogue drafts.");
    } catch (_configError) {
      loadingNode.textContent = "Failed to load catalogue drafts.";
    }
  }
}

init();
