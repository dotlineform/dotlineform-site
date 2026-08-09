const SEMANTIC_TOKEN_TARGET_LOOKUP_SCHEMA_VERSION = "docs_semantic_token_target_lookup_v2";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeTargetImage(value) {
  var row = value && typeof value === "object" && !Array.isArray(value) ? value : {};
  var src = cleanString(row.src);
  if (!src) return null;
  if (src.startsWith("/") && !src.startsWith("//")) return { src: src };
  try {
    var url = new URL(src);
    if (url.protocol !== "https:" || !url.host || url.username || url.password) return null;
  } catch (_error) {
    return null;
  }
  return { src: src };
}

function normalizeSearchText(value) {
  return cleanString(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeTarget(record, registry) {
  var row = record && typeof record === "object" && !Array.isArray(record) ? record : {};
  var family = cleanString(row.family);
  var targetType = cleanString(row.target_type);
  var targetId = cleanString(row.target_id);
  var title = cleanString(row.title);
  var familyDefinition = registry && registry.familiesById
    ? registry.familiesById.get(family)
    : null;
  if (!familyDefinition || !familyDefinition.targetTypesById.has(targetType) || !targetId || !title) return null;
  var titleNorm = normalizeSearchText(title);
  var targetIdNorm = normalizeSearchText(targetId);
  var targetTypeNorm = normalizeSearchText(targetType);
  return {
    family: family,
    targetType: targetType,
    targetId: targetId,
    title: title,
    href: cleanString(row.href),
    meta: Array.isArray(row.meta) ? row.meta.map(cleanString).filter(Boolean) : [],
    image: normalizeTargetImage(row.image),
    targetIdNorm: targetIdNorm,
    targetTypeNorm: targetTypeNorm,
    titleNorm: titleNorm,
    titleTokens: titleNorm.split(" ").filter(Boolean)
  };
}

export function resolveSemanticTokenTargetHref(href, publicPreviewBase) {
  var targetHref = cleanString(href);
  var previewBase = cleanString(publicPreviewBase).replace(/\/+$/, "");
  if (!targetHref || !previewBase) return targetHref;
  try {
    return new URL(targetHref, previewBase + "/").href;
  } catch (_error) {
    return targetHref;
  }
}

export function mountSemanticTokenTargetLinks(root, publicPreviewBase) {
  if (!root || typeof root.querySelectorAll !== "function") return 0;
  var mounted = 0;
  root.querySelectorAll("a[data-semantic-token-family][href]").forEach(function (link) {
    var resolved = resolveSemanticTokenTargetHref(
      link.getAttribute("href"),
      publicPreviewBase
    );
    if (!resolved) return;
    link.setAttribute("href", resolved);
    mounted += 1;
  });
  return mounted;
}

export function normalizeSemanticTokenTargets(payload, registry) {
  var rows = payload
    && typeof payload === "object"
    && payload.schema_version === SEMANTIC_TOKEN_TARGET_LOOKUP_SCHEMA_VERSION
    && Array.isArray(payload.targets)
    ? payload.targets
    : [];
  return rows.map(function (row) {
    return normalizeTarget(row, registry);
  }).filter(Boolean);
}

export function loadSemanticTokenTargets(registry, options = {}) {
  var fetchImpl = typeof options.fetch === "function" ? options.fetch : window.fetch.bind(window);
  var url = cleanString(options.url) || cleanString(registry && registry.targetLookupUrl);
  if (!url) return Promise.reject(new Error("Semantic token target lookup URL is unavailable."));
  return fetchImpl(url, { cache: "no-store" })
    .then(function (response) {
      if (!response || !response.ok) throw new Error("Semantic token target lookup is unavailable.");
      return response.json();
    })
    .then(function (payload) {
      return normalizeSemanticTokenTargets(payload, registry);
    });
}

export function collectSemanticTokenTargetMatches(targets, query, registry, limit) {
  var normalizedQuery = normalizeSearchText(query);
  var tokens = normalizedQuery.split(" ").filter(Boolean);
  if (!normalizedQuery || !tokens.length) return [];
  var matches = [];
  (Array.isArray(targets) ? targets : []).forEach(function (target) {
    if (!target || !target.titleNorm) return;
    var qualifiedIdentity = [target.targetTypeNorm, target.targetIdNorm].filter(Boolean).join(" ");
    var allIdentityTokens = tokens.every(function (token) {
      return (
        target.targetTypeNorm === token
        || target.targetIdNorm === token
        || target.targetIdNorm.indexOf(token) === 0
      );
    });
    var allTitleTokens = tokens.every(function (token) {
      return target.titleTokens.some(function (candidate) {
        return candidate === token || candidate.indexOf(token) === 0;
      });
    });
    var titleContainsAll = tokens.every(function (token) {
      return target.titleNorm.indexOf(token) >= 0;
    });
    if (
      !allIdentityTokens
      && !allTitleTokens
      && !titleContainsAll
      && target.titleNorm.indexOf(normalizedQuery) < 0
    ) return;
    var score = 100;
    if (qualifiedIdentity === normalizedQuery) score = 1300;
    else if (target.targetIdNorm === normalizedQuery) score = 1200;
    else if (target.titleNorm === normalizedQuery) score = 1000;
    else if (allIdentityTokens && tokens.length > 1) score = 920;
    else if (target.targetIdNorm.indexOf(normalizedQuery) === 0) score = 880;
    else if (target.targetTypeNorm === normalizedQuery) score = 860;
    else if (target.titleNorm.indexOf(normalizedQuery) === 0) score = 850;
    else if (allTitleTokens) score = 720;
    else if (target.titleNorm.indexOf(normalizedQuery) >= 0) score = 620;
    matches.push({ target: target, score: score });
  });
  matches.sort(function (left, right) {
    if (left.score !== right.score) return right.score - left.score;
    var familyDefinition = registry && registry.familiesById
      ? registry.familiesById.get(left.target.family)
      : null;
    var leftType = familyDefinition ? familyDefinition.targetTypesById.get(left.target.targetType) : null;
    var rightType = familyDefinition ? familyDefinition.targetTypesById.get(right.target.targetType) : null;
    var leftOrder = leftType ? leftType.order : 999;
    var rightOrder = rightType ? rightType.order : 999;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    var titleCmp = left.target.title.localeCompare(right.target.title, undefined, {
      sensitivity: "base",
      numeric: true
    });
    if (titleCmp !== 0) return titleCmp;
    return left.target.targetId.localeCompare(right.target.targetId, undefined, {
      sensitivity: "base",
      numeric: true
    });
  });
  return matches.slice(0, limit || 25).map(function (match) {
    return match.target;
  });
}
