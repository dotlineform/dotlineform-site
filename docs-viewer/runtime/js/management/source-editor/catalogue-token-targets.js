import {
  loadCatalogueMediaSupport
} from "./catalogue-media-support.js";
import {
  collectSemanticTokenTargetMatches
} from "./semantic-token-targets.js";

var CATALOGUE_TARGET_TYPES = new Set(["work", "series"]);

function allowedTargetTypes(raw) {
  var values = Array.isArray(raw) ? raw : Array.from(CATALOGUE_TARGET_TYPES);
  return new Set(values.map(function (value) {
    return String(value || "").trim();
  }).filter(function (value) {
    return CATALOGUE_TARGET_TYPES.has(value);
  }));
}

function catalogueTarget(row, targetTypes) {
  if (
    !row
    || row.family !== "catalogue"
    || !targetTypes.has(row.targetType)
  ) return null;
  return {
    family: row.family,
    targetType: row.targetType,
    targetId: row.targetId,
    title: row.title,
    meta: row.meta.slice()
  };
}

/** Select Work/Series subject identities; image availability and links do not define a subject. */
export function createCatalogueTargetSupport(registry, targets, options = {}) {
  var targetTypes = allowedTargetTypes(options.allowedTargetTypes);
  var searchableTargets = (Array.isArray(targets) ? targets : []).filter(function (row) {
    return Boolean(catalogueTarget(row, targetTypes));
  });
  return {
    registry: registry,
    searchableTargets: searchableTargets,
    targetTypes: targetTypes
  };
}

export function collectCatalogueTargetMatches(support, query, limit) {
  var source = support || {};
  return collectSemanticTokenTargetMatches(
    source.searchableTargets || [],
    query,
    source.registry,
    limit
  ).map(function (row) {
    return catalogueTarget(
      row,
      source.targetTypes || CATALOGUE_TARGET_TYPES
    );
  }).filter(Boolean);
}

export function findCatalogueTargetByIdentity(support, identity) {
  var source = support || {};
  var targetIdentity = identity || {};
  var family = String(targetIdentity.family || "").trim();
  var targetType = String(targetIdentity.targetType || "").trim();
  var targetId = String(targetIdentity.targetId || "").trim();
  if (family !== "catalogue" || !targetType || !targetId) return null;
  var matched = (source.searchableTargets || []).find(function (target) {
    return (
      target
      && target.family === family
      && target.targetType === targetType
      && target.targetId === targetId
    );
  });
  return catalogueTarget(
    matched,
    source.targetTypes || CATALOGUE_TARGET_TYPES
  );
}

/** Read saved subject choices through the stage-bound Catalogue provider, without a private lookup read. */
export async function loadCatalogueTargetSupport(adapter, options = {}) {
  var support = await loadCatalogueMediaSupport(adapter, { fetch: options.fetch });
  return createCatalogueTargetSupport(support.registry, support.targets, {
    allowedTargetTypes: options.allowedTargetTypes
  });
}
