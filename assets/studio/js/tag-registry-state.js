import {
  buildRegistryOptions,
  normalize,
  normalizeTimestamp
} from "./tag-registry-domain.js";
import {
  getSeriesAssignmentTagIds
} from "./studio-data.js";
import {
  getStudioRoute
} from "./studio-config.js";

export function applyTagRegistryEditProjection(state, options = {}) {
  const tagId = normalize(options.tagId);
  const description = String(options.description || "").trim();
  const updatedAtUtc = registryUpdatedAtFromResponse(options.response, state.registryUpdatedAt);
  const updatedAtMs = timestampMs(updatedAtUtc);

  state.registryUpdatedAt = updatedAtUtc || state.registryUpdatedAt;
  state.tags = state.tags.map((tag) => {
    if (!tag || tag.tagId !== tagId) return tag;
    return {
      ...tag,
      description,
      updatedAtUtc,
      updatedAtMs: Number.isFinite(updatedAtMs) ? updatedAtMs : tag.updatedAtMs
    };
  });
  syncTagRegistryOptions(state);
}

export function applyTagRegistryCreateProjection(state, options = {}) {
  const validation = options.validation || {};
  const updatedAtUtc = registryUpdatedAtFromResponse(options.response, state.registryUpdatedAt);
  const updatedAtMs = timestampMs(updatedAtUtc);

  state.registryUpdatedAt = updatedAtUtc || state.registryUpdatedAt;
  state.tags = state.tags
    .filter((tag) => tag && tag.tagId !== validation.tagId)
    .concat([{
      group: validation.group,
      tagId: validation.tagId,
      label: validation.slug,
      description: validation.description,
      status: "active",
      updatedAtUtc,
      updatedAtMs: Number.isFinite(updatedAtMs) ? updatedAtMs : null
    }]);
  syncTagRegistryOptions(state);
}

export function applyTagRegistryDeleteProjection(state, options = {}) {
  const tagId = normalize(options.tagId);
  state.registryUpdatedAt = registryUpdatedAtFromResponse(options.response, state.registryUpdatedAt) || state.registryUpdatedAt;
  state.tags = state.tags.filter((tag) => tag && tag.tagId !== tagId);
  syncTagRegistryOptions(state);
}

export function applyTagRegistryDemoteProjection(state, options = {}) {
  const tagId = normalize(options.tagId);
  const aliasKey = normalize(options.aliasKey);
  state.registryUpdatedAt = registryUpdatedAtFromResponse(options.response, state.registryUpdatedAt) || state.registryUpdatedAt;
  state.tags = state.tags.filter((tag) => tag && tag.tagId !== tagId);
  if (aliasKey) state.aliasKeys.add(aliasKey);
  syncTagRegistryOptions(state);
}

export function getTagRegistryDeleteImpactSeries(state, tagId) {
  const targetTagId = normalize(tagId);
  if (!targetTagId) return [];
  return Object.keys(state.assignmentsSeries || {})
    .map((rawSeriesId) => ({
      rawSeriesId,
      seriesId: normalize(rawSeriesId)
    }))
    .filter(({ rawSeriesId, seriesId }) => seriesId && getSeriesAssignmentTagIds(state.assignmentsSeries, rawSeriesId).includes(targetTagId))
    .map(({ seriesId }) => {
      const meta = state.seriesMetaById.get(seriesId);
      return {
        seriesId,
        title: meta && meta.title ? meta.title : seriesId,
        url: buildSeriesEditorUrl(state.config, seriesId)
      };
    })
    .sort((left, right) => left.title.localeCompare(right.title, undefined, { sensitivity: "base" }));
}

export function buildTagRegistrySeriesMetaById(config, payload) {
  const seriesMap = payload && payload.series && typeof payload.series === "object" ? payload.series : {};
  const out = new Map();
  Object.keys(seriesMap).forEach((rawSeriesId) => {
    const seriesId = normalize(rawSeriesId);
    if (!seriesId) return;
    const row = seriesMap[rawSeriesId];
    const title = String((row && row.title) || seriesId).trim();
    out.set(seriesId, {
      title,
      url: buildSeriesEditorUrl(config, seriesId)
    });
  });
  return out;
}

function syncTagRegistryOptions(state) {
  state.registryOptions = buildRegistryOptions(state.tags);
}

function registryUpdatedAtFromResponse(response, fallback) {
  return normalizeTimestamp(response && response.updated_at_utc) || fallback || "";
}

function timestampMs(value) {
  return value ? Date.parse(value) : null;
}

function buildSeriesEditorUrl(config, seriesId) {
  const base = getStudioRoute(config, "series_tag_editor");
  const normalizedSeriesId = normalize(seriesId);
  if (!base || !normalizedSeriesId) return "";
  return `${base}?series=${encodeURIComponent(normalizedSeriesId)}`;
}
