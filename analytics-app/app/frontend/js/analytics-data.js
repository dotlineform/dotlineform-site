let analyticsConfigModulePromise = null;

export async function fetchJson(url, options = {}) {
  const cache = String(options.cache || "default");
  const response = await fetch(url, { cache });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}${url ? ` for ${url}` : ""}`);
  }
  return response.json();
}

export async function loadAnalyticsRegistryJson(config, options) {
  return fetchJson(requiredAnalyticsServicePath(config, "analytics", "tag_registry"), options);
}

export async function loadAnalyticsAliasesJson(config, options) {
  return fetchJson(requiredAnalyticsServicePath(config, "analytics", "tag_aliases"), options);
}

export async function loadAnalyticsAssignmentsJson(config, options) {
  return fetchJson(
    requiredAnalyticsServicePath(config, "analytics", "tag_assignments"),
    { cache: "no-store", ...(options || {}) }
  );
}

export async function loadAnalyticsGroupsJson(config, options) {
  return fetchJson(requiredAnalyticsServicePath(config, "analytics", "tag_groups"), options);
}

export async function loadSiteSeriesIndexJson(config, options) {
  const { getSiteDataPath } = await loadAnalyticsConfigModule();
  return fetchJson(getSiteDataPath(config, "series_index"), options);
}

export async function loadSiteWorksIndexJson(config, options) {
  const { getSiteDataPath } = await loadAnalyticsConfigModule();
  return fetchJson(getSiteDataPath(config, "works_index"), options);
}

function analyticsServicePath(config, serviceName, key) {
  const runtime = config && config.app && config.app.runtime;
  const services = runtime && runtime.services;
  const service = services && services[serviceName];
  const value = service && service[key];
  return typeof value === "string" && value.trim() ? value : "";
}

function requiredAnalyticsServicePath(config, serviceName, key) {
  const path = analyticsServicePath(config, serviceName, key);
  if (!path) {
    throw new Error(`Missing Analytics ${serviceName} service endpoint: ${key}`);
  }
  return path;
}

export function buildAnalyticsRegistryLookup(registryJson, studioGroups = [], options = {}) {
  const tags = Array.isArray(registryJson && registryJson.tags) ? registryJson.tags : [];
  const allowedGroups = sanitizeGroupSet(studioGroups);
  const requireLabel = Boolean(options && options.requireLabel);
  const map = new Map();

  for (const rawTag of tags) {
    if (!rawTag || typeof rawTag !== "object") continue;
    const tagId = normalizeAnalyticsValue(rawTag.tag_id);
    const group = normalizeAnalyticsValue(rawTag.group);
    const label = String(rawTag.label || "").trim();
    const status = normalizeAnalyticsValue(rawTag.status || "active");
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

export function buildAnalyticsGroupDescriptionMap(groupsJson, studioGroups = []) {
  const rows = Array.isArray(groupsJson && groupsJson.groups) ? groupsJson.groups : [];
  const allowedGroups = sanitizeGroupSet(studioGroups);
  const out = new Map();

  for (const raw of rows) {
    if (!raw || typeof raw !== "object") continue;
    const groupId = normalizeAnalyticsValue(raw.group_id);
    const description = String(raw.description || "").trim();
    if (!groupId || !description) continue;
    if (allowedGroups && !allowedGroups.has(groupId)) continue;
    out.set(groupId, description);
  }

  return out;
}

export function normalizeAnalyticsGroups(groupsJson, studioGroups = []) {
  const rows = Array.isArray(groupsJson && groupsJson.groups) ? groupsJson.groups : [];
  const orderedGroups = Array.isArray(studioGroups) ? studioGroups.map((group) => normalizeAnalyticsValue(group)).filter(Boolean) : [];
  const allowedGroups = sanitizeGroupSet(orderedGroups);
  const byId = new Map();

  for (const raw of rows) {
    if (!raw || typeof raw !== "object") continue;
    const groupId = normalizeAnalyticsValue(raw.group_id);
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

export function getAnalyticsAssignmentsSeries(assignmentsJson) {
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
    return normalizeAnalyticsValue(rawTag);
  }
  if (rawTag && typeof rawTag === "object") {
    return normalizeAnalyticsValue(rawTag.tag_id);
  }
  return "";
}

export function normalizeAnalyticsValue(value) {
  return String(value || "").trim().toLowerCase();
}

function getAssignmentsSeriesRow(assignmentsSeries, seriesId, exactMatchOnly) {
  if (!assignmentsSeries || typeof assignmentsSeries !== "object") return null;
  if (assignmentsSeries[seriesId]) return assignmentsSeries[seriesId];
  if (exactMatchOnly) return null;

  const normalizedSeriesId = normalizeAnalyticsValue(seriesId);
  for (const [key, value] of Object.entries(assignmentsSeries)) {
    if (normalizeAnalyticsValue(key) === normalizedSeriesId) return value;
  }
  return null;
}

function sanitizeGroupSet(studioGroups) {
  const groups = Array.isArray(studioGroups)
    ? studioGroups.map((group) => normalizeAnalyticsValue(group)).filter(Boolean)
    : [];
  return groups.length ? new Set(groups) : null;
}

async function loadAnalyticsConfigModule() {
  if (!analyticsConfigModulePromise) {
    const url = new URL("./analytics-config.js", import.meta.url);
    const assetVersion = readAssetVersion(import.meta.url);
    if (assetVersion) {
      url.searchParams.set("v", assetVersion);
    }
    analyticsConfigModulePromise = import(url.href);
  }
  return analyticsConfigModulePromise;
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
