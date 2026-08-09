import {
  loadSemanticTokenRegistry
} from "./semantic-token-registry.js";
import {
  collectSemanticTokenTargetMatches,
  loadSemanticTokenTargets
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
    || !row.href
  ) return null;
  return {
    family: row.family,
    targetType: row.targetType,
    targetId: row.targetId,
    title: row.title,
    href: row.href,
    meta: row.meta.slice()
  };
}

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
    return catalogueTarget(row, source.targetTypes || CATALOGUE_TARGET_TYPES);
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
  return catalogueTarget(matched, source.targetTypes || CATALOGUE_TARGET_TYPES);
}

export function loadCatalogueTargetSupport(options = {}) {
  return loadSemanticTokenRegistry({ fetch: options.fetch })
    .then(function (registry) {
      return loadSemanticTokenTargets(registry, { fetch: options.fetch })
        .then(function (targets) {
          return createCatalogueTargetSupport(registry, targets, {
            allowedTargetTypes: options.allowedTargetTypes
          });
        });
    });
}
