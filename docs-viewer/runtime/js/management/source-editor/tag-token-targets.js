import {
  loadSemanticTokenRegistry
} from "./semantic-token-registry.js";
import {
  collectSemanticTokenTargetMatches,
  loadSemanticTokenTargets
} from "./semantic-token-targets.js";

function tagTarget(row) {
  if (
    !row
    || row.family !== "tag"
    || row.targetType !== "tag"
    || !row.targetId
    || !row.href
  ) return null;
  return {
    family: "tag",
    targetType: "tag",
    targetId: row.targetId,
    title: row.title,
    href: row.href,
    meta: row.meta.slice(),
    aliases: row.aliases.slice()
  };
}

export function createTagTargetSupport(registry, targets) {
  return {
    registry: registry,
    searchableTargets: (Array.isArray(targets) ? targets : []).filter(function (row) {
      return Boolean(tagTarget(row));
    })
  };
}

export function collectTagTargetMatches(support, query, limit) {
  var source = support || {};
  return collectSemanticTokenTargetMatches(
    source.searchableTargets || [],
    query,
    source.registry,
    limit
  ).map(tagTarget).filter(Boolean);
}

export function findTagTargetByIdentity(support, identity) {
  var source = support || {};
  var targetIdentity = identity || {};
  if (
    targetIdentity.family !== "tag"
    || targetIdentity.targetType !== "tag"
    || !targetIdentity.targetId
  ) return null;
  return tagTarget((source.searchableTargets || []).find(function (target) {
    return target.family === "tag"
      && target.targetType === "tag"
      && target.targetId === targetIdentity.targetId;
  }));
}

export function loadTagTargetSupport(options = {}) {
  return loadSemanticTokenRegistry({ fetch: options.fetch })
    .then(function (registry) {
      return loadSemanticTokenTargets(registry, { fetch: options.fetch })
        .then(function (targets) {
          return createTagTargetSupport(registry, targets);
        });
    });
}
