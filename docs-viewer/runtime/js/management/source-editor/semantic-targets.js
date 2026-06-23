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

function searchTokens(value) {
  return normalizeSearchText(value).split(" ").filter(Boolean);
}

function normalizeTarget(record, registry) {
  var row = record && typeof record === "object" && !Array.isArray(record) ? record : {};
  var kind = cleanString(row.kind);
  var id = cleanString(row.id);
  var title = cleanString(row.title);
  if (!kind || !id || !title || !registry.kindsById.has(kind)) return null;
  var titleNorm = normalizeSearchText(title);
  return {
    kind: kind,
    id: id,
    title: title,
    meta: Array.isArray(row.meta) ? row.meta.map(cleanString).filter(Boolean) : [],
    titleNorm: titleNorm,
    titleTokens: titleNorm.split(" ").filter(Boolean)
  };
}

export function normalizeSemanticTargets(payload, registry) {
  var rows = payload && typeof payload === "object" && Array.isArray(payload.targets) ? payload.targets : [];
  return rows.map(function (row) {
    return normalizeTarget(row, registry);
  }).filter(Boolean);
}

export function loadSemanticTargets(registry, options = {}) {
  var fetchImpl = typeof options.fetch === "function" ? options.fetch : window.fetch.bind(window);
  var url = cleanString(options.url) || cleanString(registry && registry.targetLookupUrl);
  if (!url) return Promise.reject(new Error("Semantic target lookup URL is unavailable."));
  return fetchImpl(url, { cache: "no-store" })
    .then(function (response) {
      if (!response || !response.ok) throw new Error("Semantic target lookup is unavailable.");
      return response.json();
    })
    .then(function (payload) {
      return normalizeSemanticTargets(payload, registry);
    });
}

export function collectSemanticTargetMatches(targets, query, registry, limit) {
  var normalizedQuery = normalizeSearchText(query);
  var tokens = searchTokens(query);
  if (!normalizedQuery || !tokens.length) return [];
  var kindsById = registry && registry.kindsById ? registry.kindsById : new Map();
  var matches = [];
  targets.forEach(function (target) {
    if (!target || !target.titleNorm) return;
    var allTitleTokens = tokens.every(function (token) {
      return target.titleTokens.some(function (candidate) {
        return candidate === token || candidate.indexOf(token) === 0;
      });
    });
    var titleContainsAll = tokens.every(function (token) {
      return target.titleNorm.indexOf(token) >= 0;
    });
    if (!allTitleTokens && !titleContainsAll && target.titleNorm.indexOf(normalizedQuery) < 0) return;
    var score = 100;
    if (target.titleNorm === normalizedQuery) score = 1000;
    else if (target.titleNorm.indexOf(normalizedQuery) === 0) score = 850;
    else if (allTitleTokens) score = 720;
    else if (target.titleNorm.indexOf(normalizedQuery) >= 0) score = 620;
    matches.push({ target: target, score: score });
  });
  matches.sort(function (left, right) {
    if (left.score !== right.score) return right.score - left.score;
    var leftKind = kindsById.get(left.target.kind);
    var rightKind = kindsById.get(right.target.kind);
    var leftOrder = leftKind ? leftKind.order : 999;
    var rightOrder = rightKind ? rightKind.order : 999;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    var titleCmp = left.target.title.localeCompare(right.target.title, undefined, { sensitivity: "base", numeric: true });
    if (titleCmp !== 0) return titleCmp;
    return left.target.id.localeCompare(right.target.id, undefined, { sensitivity: "base", numeric: true });
  });
  return matches.slice(0, limit || 25).map(function (match) {
    return match.target;
  });
}
