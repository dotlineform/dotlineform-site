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

function catalogueTarget(row, targetTypes, requireImage) {
  var image = row && row.image && typeof row.image === "object" && row.image.src
    ? { src: String(row.image.src).trim() }
    : null;
  if (
    !row
    || row.family !== "catalogue"
    || !targetTypes.has(row.targetType)
    || !row.href
    || (requireImage && !image)
  ) return null;
  var target = {
    family: row.family,
    targetType: row.targetType,
    targetId: row.targetId,
    title: row.title,
    href: row.href,
    meta: row.meta.slice()
  };
  if (image) target.image = image;
  return target;
}

export function createCatalogueTargetSupport(registry, targets, options = {}) {
  var targetTypes = allowedTargetTypes(options.allowedTargetTypes);
  var requireImage = options.requireImage === true;
  var searchableTargets = (Array.isArray(targets) ? targets : []).filter(function (row) {
    return Boolean(catalogueTarget(row, targetTypes, requireImage));
  });
  return {
    registry: registry,
    searchableTargets: searchableTargets,
    targetTypes: targetTypes,
    requireImage: requireImage
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
      source.targetTypes || CATALOGUE_TARGET_TYPES,
      source.requireImage === true
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
    source.targetTypes || CATALOGUE_TARGET_TYPES,
    source.requireImage === true
  );
}

export function loadCatalogueTargetSupport(options = {}) {
  return loadSemanticTokenRegistry({ fetch: options.fetch })
    .then(function (registry) {
      return loadSemanticTokenTargets(registry, { fetch: options.fetch })
        .then(function (targets) {
          return createCatalogueTargetSupport(registry, targets, {
            allowedTargetTypes: options.allowedTargetTypes,
            requireImage: options.requireImage
          });
        });
    });
}
