import {
  loadSemanticTokenRegistry
} from "./semantic-token-registry.js";
import {
  collectSemanticTokenTargetMatches,
  loadSemanticTokenTargets
} from "./semantic-token-targets.js";

function conceptTarget(row) {
  if (
    !row
    || row.family !== "concept"
    || row.targetType !== "concept"
    || !row.targetId
    || !row.href
  ) return null;
  return {
    family: "concept",
    targetType: "concept",
    targetId: row.targetId,
    title: row.title,
    href: row.href,
    meta: row.meta.slice()
  };
}

export function createConceptTargetSupport(registry, targets) {
  return {
    registry: registry,
    searchableTargets: (Array.isArray(targets) ? targets : []).filter(function (row) {
      return Boolean(conceptTarget(row));
    })
  };
}

export function collectConceptTargetMatches(support, query, limit) {
  var source = support || {};
  return collectSemanticTokenTargetMatches(
    source.searchableTargets || [],
    query,
    source.registry,
    limit
  ).map(conceptTarget).filter(Boolean);
}

export function findConceptTargetByIdentity(support, identity) {
  var source = support || {};
  var targetIdentity = identity || {};
  if (
    targetIdentity.family !== "concept"
    || targetIdentity.targetType !== "concept"
    || !targetIdentity.targetId
  ) return null;
  return conceptTarget((source.searchableTargets || []).find(function (target) {
    return target.family === "concept"
      && target.targetType === "concept"
      && target.targetId === targetIdentity.targetId;
  }));
}

export function loadConceptTargetSupport(options = {}) {
  return loadSemanticTokenRegistry({ fetch: options.fetch })
    .then(function (registry) {
      return loadSemanticTokenTargets(registry, { fetch: options.fetch })
        .then(function (targets) {
          return createConceptTargetSupport(registry, targets);
        });
    });
}
