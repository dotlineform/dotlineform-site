import {
  buildStudioRagTooltip,
  computeStudioRag,
  computeStudioTagMetrics,
  getStudioDataPath,
  loadStudioConfig
} from "./studio-config.js";

initTagStudioIndexRag();

async function initTagStudioIndexRag() {
  const list = document.getElementById("tagStudioList");
  if (!list) return;

  const rows = Array.from(list.querySelectorAll(".worksList__item[data-series-id]"));
  if (!rows.length) return;

  try {
    const config = await loadStudioConfig();
    const [assignmentsData, registryData] = await Promise.all([
      fetchJson(getStudioDataPath(config, "tag_assignments")),
      fetchJson(getStudioDataPath(config, "tag_registry")),
    ]);

    const registry = buildRegistryLookup(registryData);
    const assignmentsSeries = getAssignmentsSeries(assignmentsData);

    for (const row of rows) {
      const seriesId = String(row.getAttribute("data-series-id") || "").trim();
      if (!seriesId) continue;

      const indicator = row.querySelector("[data-rag-indicator]");
      if (!indicator) continue;

      const assignedTags = getSeriesTags(assignmentsSeries, seriesId);
      const metrics = computeStudioTagMetrics(assignedTags, registry, config);
      const rag = computeStudioRag(metrics, config);
      const tooltip = buildStudioRagTooltip(metrics);
      const label = `status ${rag.toUpperCase()}: ${tooltip}`;

      indicator.classList.remove("rag--red", "rag--amber", "rag--green");
      indicator.classList.add(`rag--${rag}`);
      indicator.setAttribute("title", tooltip);
      indicator.setAttribute("aria-label", label);
    }
  } catch (err) {
    for (const row of rows) {
      const indicator = row.querySelector("[data-rag-indicator]");
      if (!indicator) continue;
      indicator.classList.remove("rag--amber", "rag--green");
      indicator.classList.add("rag--red");
      indicator.setAttribute("title", "Tag status unavailable: failed to load tag data.");
      indicator.setAttribute("aria-label", "status RED: failed to load tag data");
    }
  }
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "default" });
  if (!response.ok) throw new Error(`HTTP ${response.status} for ${url}`);
  return response.json();
}

function buildRegistryLookup(registryData) {
  const tags = Array.isArray(registryData && registryData.tags) ? registryData.tags : [];
  const map = new Map();

  for (const rawTag of tags) {
    if (!rawTag || typeof rawTag !== "object") continue;
    const tagId = normalize(rawTag.tag_id);
    const group = normalize(rawTag.group);
    const status = normalize(rawTag.status || "active");
    if (!tagId || !group) continue;
    map.set(tagId, { group, status });
  }

  return map;
}

function getAssignmentsSeries(assignmentsData) {
  if (assignmentsData && typeof assignmentsData.series === "object" && assignmentsData.series !== null) {
    return assignmentsData.series;
  }
  return {};
}

function getSeriesTags(assignmentsSeries, seriesId) {
  if (assignmentsSeries[seriesId] && Array.isArray(assignmentsSeries[seriesId].tags)) {
    return normalizeSeriesTagIds(assignmentsSeries[seriesId].tags);
  }

  const normalizedSeriesId = normalize(seriesId);
  for (const [key, value] of Object.entries(assignmentsSeries)) {
    if (normalize(key) !== normalizedSeriesId) continue;
    return Array.isArray(value && value.tags) ? normalizeSeriesTagIds(value.tags) : [];
  }
  return [];
}

function normalizeSeriesTagIds(rawTags) {
  if (!Array.isArray(rawTags)) return [];
  const out = [];
  const seen = new Set();
  for (const raw of rawTags) {
    const tagId = normalizeAssignmentTagId(raw);
    if (!tagId || seen.has(tagId)) continue;
    seen.add(tagId);
    out.push(tagId);
  }
  return out;
}

function normalizeAssignmentTagId(rawTag) {
  if (typeof rawTag === "string") {
    return normalize(rawTag);
  }
  if (rawTag && typeof rawTag === "object") {
    return normalize(rawTag.tag_id);
  }
  return "";
}

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}
