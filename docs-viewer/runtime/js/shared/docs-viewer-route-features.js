export const DOCS_VIEWER_ROUTE_FEATURE_IDS = [
  "configured-scope-discovery",
  "scope-selection",
  "search",
  "recent",
  "bookmarks",
  "reports",
  "source-editing",
  "management"
];

var FEATURE_KEYS = {
  "configured-scope-discovery": "configuredScopeDiscovery",
  "scope-selection": "scopeSelection",
  "search": "search",
  "recent": "recent",
  "bookmarks": "bookmarks",
  "reports": "reports",
  "source-editing": "sourceEditing",
  "management": "management"
};

function cleanFeatureId(value) {
  return String(value == null ? "" : value).trim().toLowerCase();
}

function requireKnownFeatureId(value) {
  var featureId = cleanFeatureId(value);
  if (!Object.prototype.hasOwnProperty.call(FEATURE_KEYS, featureId)) {
    throw new Error("Unknown Docs Viewer route feature: " + (featureId || "(empty)"));
  }
  return featureId;
}

export function normalizeDocsViewerRouteFeatures(rawFeatures) {
  if (!Array.isArray(rawFeatures)) {
    throw new Error("Docs Viewer route config requires a features array.");
  }
  var ids = [];
  var seen = new Set();
  rawFeatures.forEach(function (value) {
    var featureId = requireKnownFeatureId(value);
    if (seen.has(featureId)) return;
    seen.add(featureId);
    ids.push(featureId);
  });
  if (seen.has("scope-selection") && !seen.has("configured-scope-discovery")) {
    throw new Error("Docs Viewer route feature scope-selection requires configured-scope-discovery.");
  }

  var projection = { ids: ids };
  DOCS_VIEWER_ROUTE_FEATURE_IDS.forEach(function (featureId) {
    projection[FEATURE_KEYS[featureId]] = seen.has(featureId);
  });
  return projection;
}

export function docsViewerRouteFeatureEnabled(featurePolicy, featureId) {
  var id = requireKnownFeatureId(featureId);
  var policy = featurePolicy || {};
  return policy[FEATURE_KEYS[id]] === true;
}

export function projectDocsViewerFeatureRecords(records, featurePolicy) {
  return (records || []).filter(function (record) {
    var requiredFeature = cleanFeatureId(record && record.feature);
    return !requiredFeature || docsViewerRouteFeatureEnabled(featurePolicy, requiredFeature);
  });
}
