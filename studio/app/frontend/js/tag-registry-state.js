import {
  buildRegistryOptions,
  normalize,
  normalizeTimestamp
} from "./tag-registry-domain.js";
import {
  getSeriesAssignmentTagIds
} from "./studio-tag-data.js";
import {
  buildStudioRouteUrl
} from "./studio-config.js";
import {
  attachTagRegistryDocuments
} from "./tag-registry-documents.js";

export function applyTagRegistryEditProjection(state, options = {}) {
  const tagId = normalize(options.tagId);
  const group = normalize(options.group);
  const docUrl = Array.isArray(options.response && options.response.doc_url)
    ? options.response.doc_url.slice()
    : (Array.isArray(options.docUrl) ? options.docUrl.slice() : []);
  const updatedAtUtc = registryUpdatedAtFromResponse(options.response, state.registryUpdatedAt);
  const updatedAtMs = timestampMs(updatedAtUtc);

  state.registryUpdatedAt = updatedAtUtc || state.registryUpdatedAt;
  state.tags = state.tags.map((tag) => {
    if (!tag || tag.tagId !== tagId) return tag;
    return {
      ...tag,
      group,
      docUrl,
      updatedAtUtc,
      updatedAtMs: Number.isFinite(updatedAtMs) ? updatedAtMs : tag.updatedAtMs
    };
  });
  state.tags = attachTagRegistryDocuments(state.tags, state.documentLocationsByUrl);
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
      docUrl: Array.isArray(options.response && options.response.doc_url)
        ? options.response.doc_url.slice()
        : [],
      documents: [],
      updatedAtUtc,
      updatedAtMs: Number.isFinite(updatedAtMs) ? updatedAtMs : null
    }]);
  state.tags = attachTagRegistryDocuments(state.tags, state.documentLocationsByUrl);
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
  const items = Array.isArray(payload && payload.items) ? payload.items : [];
  const out = new Map();
  items.forEach((row) => {
    if (normalize(row && row.status) !== "published") return;
    const seriesId = normalize(row && row.series_id);
    if (!seriesId) return;
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
  const normalizedSeriesId = normalize(seriesId);
  return normalizedSeriesId ? buildStudioRouteUrl(config, "series_tag_editor", { series: normalizedSeriesId }) : "";
}
