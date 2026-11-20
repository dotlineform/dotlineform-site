const CATALOGUE_MEDIA_TARGETS_SCHEMA = "docs_catalogue_media_targets_v2";
const TARGET_TYPE_ORDER = { gallery: 0, work: 1 };

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeSearchText(value) {
  return cleanString(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeIdentityToken(value) {
  return /^\d+$/.test(value) ? value.replace(/^0+(?=\d)/, "") : value;
}

function prepareCatalogueMediaTarget({ target_type: targetType, target_id: targetId, title }) {
  var titleNorm = normalizeSearchText(title);
  var targetIdNorm = normalizeIdentityToken(normalizeSearchText(targetId));
  var targetTypeNorm = normalizeSearchText(targetType);
  return {
    targetType: targetType,
    targetId: targetId,
    title: title,
    targetIdNorm: targetIdNorm,
    targetTypeNorm: targetTypeNorm,
    titleNorm: titleNorm,
    titleTokens: titleNorm.split(" ").filter(Boolean)
  };
}

/** Read exact generated Catalogue identities and prepare their search terms once. */
export async function loadCatalogueMediaTargets(readTargets) {
  const payload = await readTargets();
  if (payload?.schema_version !== CATALOGUE_MEDIA_TARGETS_SCHEMA || !Array.isArray(payload.targets)) {
    throw new Error("Generated Catalogue targets are unavailable.");
  }
  return { targets: payload.targets.map(prepareCatalogueMediaTarget), galleryIdsByWork: payload.gallery_ids_by_work };
}

export function collectCatalogueMediaTargetMatches(targets, query, limit) {
  var normalizedQuery = normalizeSearchText(query);
  var tokens = normalizedQuery.split(" ").filter(Boolean);
  if (!normalizedQuery || !tokens.length) return [];
  var identityTokens = tokens.map(normalizeIdentityToken);
  var identityQuery = identityTokens.join(" ");
  var matches = [];
  targets.forEach(function (target) {
    if (!target.titleNorm && target.targetType !== "work") return;
    var qualifiedIdentity = [target.targetTypeNorm, target.targetIdNorm].filter(Boolean).join(" ");
    var allIdentityTokens = identityTokens.every(function (token) {
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
    if (qualifiedIdentity === identityQuery) score = 1300;
    else if (target.targetIdNorm === identityQuery) score = 1200;
    else if (target.titleNorm === normalizedQuery) score = 1000;
    else if (allIdentityTokens && tokens.length > 1) score = 920;
    else if (target.targetIdNorm.indexOf(identityQuery) === 0) score = 880;
    else if (target.targetTypeNorm === normalizedQuery) score = 860;
    else if (target.titleNorm.indexOf(normalizedQuery) === 0) score = 850;
    else if (allTitleTokens) score = 720;
    else if (target.titleNorm.indexOf(normalizedQuery) >= 0) score = 620;
    matches.push({ target: target, score: score });
  });
  matches.sort(function (left, right) {
    if (left.score !== right.score) return right.score - left.score;
    var typeOrder = TARGET_TYPE_ORDER[left.target.targetType] - TARGET_TYPE_ORDER[right.target.targetType];
    if (typeOrder) return typeOrder;
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
