import {
  loadSemanticReferenceRegistry
} from "./semantic-reference-registry.js";
import {
  collectSemanticTargetMatches,
  loadSemanticTargets
} from "./semantic-targets.js";

var CATALOGUE_TARGET_TYPES = new Set(["work", "series", "moment"]);

function catalogueTargetFromPilot(row) {
  if (!row || !CATALOGUE_TARGET_TYPES.has(row.kind) || !row.href) return null;
  return {
    family: "catalogue",
    targetType: row.kind,
    targetId: row.id,
    title: row.title,
    href: row.href,
    meta: row.meta.slice()
  };
}

export function createCatalogueTargetSupport(registry, pilotTargets) {
  var searchableTargets = (Array.isArray(pilotTargets) ? pilotTargets : []).filter(function (row) {
    return Boolean(catalogueTargetFromPilot(row));
  });
  return {
    registry: registry,
    searchableTargets: searchableTargets
  };
}

export function collectCatalogueTargetMatches(support, query, limit) {
  var source = support || {};
  return collectSemanticTargetMatches(
    source.searchableTargets || [],
    query,
    source.registry,
    limit
  ).map(catalogueTargetFromPilot).filter(Boolean);
}

export function loadCatalogueTargetSupport(options = {}) {
  return loadSemanticReferenceRegistry({ fetch: options.fetch })
    .then(function (registry) {
      return loadSemanticTargets(registry, { fetch: options.fetch })
        .then(function (targets) {
          return createCatalogueTargetSupport(registry, targets);
        });
    });
}
