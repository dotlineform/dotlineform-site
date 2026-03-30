let studioConfigModulePromise = null;

export async function fetchJson(url, options = {}) {
  const cache = String(options.cache || "default");
  const response = await fetch(url, { cache });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}${url ? ` for ${url}` : ""}`);
  }
  return response.json();
}

export async function loadStudioRegistryJson(config, options) {
  const { getStudioDataPath } = await loadStudioConfigModule();
  return fetchJson(getStudioDataPath(config, "tag_registry"), options);
}

export async function loadStudioAliasesJson(config, options) {
  const { getStudioDataPath } = await loadStudioConfigModule();
  return fetchJson(getStudioDataPath(config, "tag_aliases"), options);
}

export async function loadStudioAssignmentsJson(config, options) {
  const { getStudioDataPath } = await loadStudioConfigModule();
  return fetchJson(getStudioDataPath(config, "tag_assignments"), { cache: "no-store", ...(options || {}) });
}

export async function loadStudioGroupsJson(config, options) {
  const { getStudioDataPath } = await loadStudioConfigModule();
  return fetchJson(getStudioDataPath(config, "tag_groups"), options);
}

export async function loadSiteSeriesIndexJson(config, options) {
  const { getSiteDataPath } = await loadStudioConfigModule();
  return fetchJson(getSiteDataPath(config, "series_index"), options);
}

export async function loadSiteWorksIndexJson(config, options) {
  const { getSiteDataPath } = await loadStudioConfigModule();
  return fetchJson(getSiteDataPath(config, "works_index"), options);
}

export async function loadSearchIndexJson(config, scope, options) {
  const { getSearchScopeDataPath } = await loadStudioConfigModule();
  return fetchJson(getSearchScopeDataPath(config, scope, "index"), options);
}

export function buildStudioRegistryLookup(registryJson, studioGroups = [], options = {}) {
  const tags = Array.isArray(registryJson && registryJson.tags) ? registryJson.tags : [];
  const allowedGroups = sanitizeGroupSet(studioGroups);
  const requireLabel = Boolean(options && options.requireLabel);
  const map = new Map();

  for (const rawTag of tags) {
    if (!rawTag || typeof rawTag !== "object") continue;
    const tagId = normalizeStudioValue(rawTag.tag_id);
    const group = normalizeStudioValue(rawTag.group);
    const label = String(rawTag.label || "").trim();
    const status = normalizeStudioValue(rawTag.status || "active");
    if (!tagId || !group) continue;
    if (allowedGroups && !allowedGroups.has(group)) continue;
    if (requireLabel && !label) continue;
    map.set(tagId, {
      group,
      label,
      status
    });
  }

  return map;
}

export function buildStudioGroupDescriptionMap(groupsJson, studioGroups = []) {
  const rows = Array.isArray(groupsJson && groupsJson.groups) ? groupsJson.groups : [];
  const allowedGroups = sanitizeGroupSet(studioGroups);
  const out = new Map();

  for (const raw of rows) {
    if (!raw || typeof raw !== "object") continue;
    const groupId = normalizeStudioValue(raw.group_id);
    const description = String(raw.description || "").trim();
    if (!groupId || !description) continue;
    if (allowedGroups && !allowedGroups.has(groupId)) continue;
    out.set(groupId, description);
  }

  return out;
}

export function normalizeStudioGroups(groupsJson, studioGroups = []) {
  const rows = Array.isArray(groupsJson && groupsJson.groups) ? groupsJson.groups : [];
  const orderedGroups = Array.isArray(studioGroups) ? studioGroups.map((group) => normalizeStudioValue(group)).filter(Boolean) : [];
  const allowedGroups = sanitizeGroupSet(orderedGroups);
  const byId = new Map();

  for (const raw of rows) {
    if (!raw || typeof raw !== "object") continue;
    const groupId = normalizeStudioValue(raw.group_id);
    if (!groupId) continue;
    if (allowedGroups && !allowedGroups.has(groupId)) continue;
    byId.set(groupId, {
      groupId,
      description: String(raw.description || "").trim(),
      descriptionLong: String(raw.description_long || "").trim()
    });
  }

  if (!orderedGroups.length) {
    return Array.from(byId.values());
  }
  return orderedGroups.map((groupId) => byId.get(groupId)).filter(Boolean);
}

export function getStudioAssignmentsSeries(assignmentsJson) {
  if (assignmentsJson && typeof assignmentsJson.series === "object" && assignmentsJson.series !== null) {
    return assignmentsJson.series;
  }
  return {};
}

export function getSeriesAssignmentTagIds(assignmentsSeries, seriesId, options = {}) {
  const exactMatchOnly = Boolean(options && options.exactMatchOnly);
  const row = getAssignmentsSeriesRow(assignmentsSeries, seriesId, exactMatchOnly);
  if (!row || !Array.isArray(row.tags)) return [];

  const out = [];
  const seen = new Set();
  for (const rawTag of row.tags) {
    const tagId = normalizeAssignmentTagId(rawTag);
    if (!tagId || seen.has(tagId)) continue;
    seen.add(tagId);
    out.push(tagId);
  }
  return out;
}

export function normalizeAssignmentTagId(rawTag) {
  if (typeof rawTag === "string") {
    return normalizeStudioValue(rawTag);
  }
  if (rawTag && typeof rawTag === "object") {
    return normalizeStudioValue(rawTag.tag_id);
  }
  return "";
}

export function normalizeStudioValue(value) {
  return String(value || "").trim().toLowerCase();
}

function getAssignmentsSeriesRow(assignmentsSeries, seriesId, exactMatchOnly) {
  if (!assignmentsSeries || typeof assignmentsSeries !== "object") return null;
  if (assignmentsSeries[seriesId]) return assignmentsSeries[seriesId];
  if (exactMatchOnly) return null;

  const normalizedSeriesId = normalizeStudioValue(seriesId);
  for (const [key, value] of Object.entries(assignmentsSeries)) {
    if (normalizeStudioValue(key) === normalizedSeriesId) return value;
  }
  return null;
}

function sanitizeGroupSet(studioGroups) {
  const groups = Array.isArray(studioGroups)
    ? studioGroups.map((group) => normalizeStudioValue(group)).filter(Boolean)
    : [];
  return groups.length ? new Set(groups) : null;
}

async function loadStudioConfigModule() {
  if (!studioConfigModulePromise) {
    const url = new URL("./studio-config.js", import.meta.url);
    const assetVersion = readAssetVersion(import.meta.url);
    if (assetVersion) {
      url.searchParams.set("v", assetVersion);
    }
    studioConfigModulePromise = import(url.href);
  }
  return studioConfigModulePromise;
}

function readAssetVersion(importUrl = "") {
  try {
    const importVersion = new URL(importUrl).searchParams.get("v");
    if (importVersion) return importVersion;
  } catch (_error) {
    // Ignore malformed import URLs and continue to DOM-based lookup.
  }

  if (typeof document !== "undefined") {
    const meta = document.querySelector('meta[name="dlf-asset-version"]');
    const value = meta ? String(meta.getAttribute("content") || "").trim() : "";
    if (value) return value;
  }

  return "";
}
