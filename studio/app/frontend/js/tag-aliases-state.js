import {
  buildRegistryOptions,
  normalize,
  normalizeTimestamp
} from "./tag-aliases-domain.js";

export function applyTagAliasesDeleteProjection(state, options = {}) {
  const aliasKey = normalize(options.aliasKey);
  state.aliasesUpdatedAt = aliasesUpdatedAtFromResponse(options.response, state.aliasesUpdatedAt) || state.aliasesUpdatedAt;
  state.aliases = state.aliases.filter((entry) => entry && entry.alias !== aliasKey);
}

export function applyTagAliasesEditProjection(state, options = {}) {
  const validation = options.validation || {};
  const originalAlias = normalize(options.originalAlias);
  const updatedAtUtc = aliasesUpdatedAtFromResponse(options.response, state.aliasesUpdatedAt);
  state.aliasesUpdatedAt = updatedAtUtc || state.aliasesUpdatedAt;
  replaceTagAliasEntry(
    state,
    makeTagAliasEntry(state, validation.alias, validation.description, validation.tags, state.aliasesUpdatedAt),
    originalAlias
  );
}

export function applyTagAliasesPromoteProjection(state, options = {}) {
  const aliasKey = normalize(options.aliasKey);
  const group = normalize(options.group);
  state.aliasesUpdatedAt = aliasesUpdatedAtFromResponse(options.response, state.aliasesUpdatedAt) || state.aliasesUpdatedAt;
  state.aliases = state.aliases.filter((entry) => entry && entry.alias !== aliasKey);
  if (group && aliasKey) {
    state.registryById.set(`${group}:${aliasKey}`, { group, label: aliasKey });
  }
  syncTagAliasesDerivedState(state);
}

export function applyTagAliasesDemoteProjection(state, options = {}) {
  const canonicalTagId = normalize(options.canonicalTagId);
  const aliasTargets = Array.isArray(options.aliasTargets)
    ? options.aliasTargets.map((tagId) => normalize(tagId)).filter(Boolean)
    : [];
  const updatedAtUtc = aliasesUpdatedAtFromResponse(options.response, state.aliasesUpdatedAt);
  state.aliasesUpdatedAt = updatedAtUtc || state.aliasesUpdatedAt;
  if (canonicalTagId) {
    state.registryById.delete(canonicalTagId);
    replaceTagAliasEntry(
      state,
      makeTagAliasEntry(state, canonicalTagId.split(":")[1] || canonicalTagId, "", aliasTargets, updatedAtUtc)
    );
  }
  syncTagAliasesDerivedState(state);
}

export function makeTagAliasEntry(state, alias, description, targets, updatedAtUtc) {
  const normalizedAlias = normalize(alias);
  const normalizedDescription = String(description || "").trim();
  const normalizedTargets = Array.isArray(targets) ? targets.map((tagId) => normalize(tagId)).filter(Boolean) : [];
  const resolvedTargets = normalizedTargets.map((tagId) => {
    const info = state.registryById.get(tagId);
    return {
      tagId,
      group: info ? info.group : "",
      label: info ? info.label : tagId,
      known: Boolean(info)
    };
  });
  const groups = Array.from(new Set(resolvedTargets.filter((item) => item.known).map((item) => item.group)));
  const hasUnknown = resolvedTargets.some((item) => !item.known);
  const normalizedUpdatedAt = normalizeTimestamp(updatedAtUtc) || state.aliasesUpdatedAt;
  const updatedAtMs = normalizedUpdatedAt ? Date.parse(normalizedUpdatedAt) : null;
  return {
    alias: normalizedAlias,
    value: {
      description: normalizedDescription,
      tags: normalizedTargets.slice()
    },
    description: normalizedDescription,
    targets: normalizedTargets.slice(),
    resolvedTargets,
    groups,
    hasUnknown,
    updatedAtUtc: normalizedUpdatedAt,
    updatedAtMs: Number.isFinite(updatedAtMs) ? updatedAtMs : null
  };
}

export function replaceTagAliasEntry(state, entry, originalAlias = "") {
  const normalizedOriginal = normalize(originalAlias);
  state.aliases = state.aliases
    .filter((item) => item && item.alias !== entry.alias && item.alias !== normalizedOriginal)
    .concat([entry]);
}

export function syncTagAliasesDerivedState(state) {
  state.registryOptions = buildRegistryOptions(state.registryById);
}

function aliasesUpdatedAtFromResponse(response, fallback) {
  return normalizeTimestamp(response && response.updated_at_utc) || fallback || "";
}
