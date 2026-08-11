import { loadStudioServerReadJson } from "./studio-data.js";

export async function fetchJson(url, options = {}) {
  const cache = String(options.cache || "default");
  const response = await fetch(url, { cache });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}${url ? ` for ${url}` : ""}`);
  }
  return response.json();
}

export async function loadAnalyticsRegistryJson(config, options) {
  return fetchJson(requiredStudioTagServicePath(config, "tags", "tag_registry"), options);
}

export async function loadTagDocumentAssociationsJson(config, options) {
  return fetchJson(
    requiredStudioTagServicePath(config, "tags", "tag_associations"),
    { cache: "no-store", ...(options || {}) }
  );
}

export async function loadAnalyticsAliasesJson(config, options) {
  return fetchJson(requiredStudioTagServicePath(config, "tags", "tag_aliases"), options);
}

export async function loadAnalyticsAssignmentsJson(config, options) {
  return fetchJson(
    requiredStudioTagServicePath(config, "tags", "tag_assignments"),
    { cache: "no-store", ...(options || {}) }
  );
}

export async function loadAnalyticsGroupsJson(config, options) {
  return fetchJson(requiredStudioTagServicePath(config, "tags", "tag_groups"), options);
}

export async function loadStudioSeriesSearchJson(_config, options) {
  return loadStudioServerReadJson("catalogue_lookup_series_search", "", options);
}

export async function loadStudioSeriesRecordJson(_config, seriesId, options) {
  return loadStudioServerReadJson("catalogue_lookup_series_base", seriesId, options);
}

export async function loadStudioWorkRecordJson(_config, workId, options) {
  return loadStudioServerReadJson("catalogue_work_record", workId, options);
}

function studioTagServicePath(config, serviceName, key) {
  const runtime = config && config.app && config.app.runtime;
  const services = runtime && runtime.services;
  const service = services && services[serviceName];
  const value = service && service[key];
  return typeof value === "string" && value.trim() ? value : "";
}

function requiredStudioTagServicePath(config, serviceName, key) {
  const path = studioTagServicePath(config, serviceName, key);
  if (!path) {
    throw new Error(`Missing Studio ${serviceName} service endpoint: ${key}`);
  }
  return path;
}

export function buildAnalyticsRegistryLookup(registryJson, studioGroups = []) {
  const tags = Array.isArray(registryJson && registryJson.tags) ? registryJson.tags : [];
  const allowedGroups = sanitizeGroupSet(studioGroups);
  const map = new Map();

  for (const rawTag of tags) {
    if (!rawTag || typeof rawTag !== "object") continue;
    const tagId = normalizeAnalyticsValue(rawTag.tag_id);
    const group = normalizeAnalyticsValue(rawTag.group);
    if (!tagId || !group) continue;
    if (allowedGroups && !allowedGroups.has(group)) continue;
    map.set(tagId, {
      group,
      label: tagId
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
