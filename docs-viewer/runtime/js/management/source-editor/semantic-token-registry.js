function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function objectRecord(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

function normalizeTargetType(record, order) {
  var source = objectRecord(record) || {};
  var idPolicy = objectRecord(source.id_policy) || {};
  var key = cleanString(source.key);
  if (!key) return null;
  return {
    key: key,
    label: cleanString(source.label),
    idPolicy: {
      canonicalPattern: cleanString(idPolicy.canonical_pattern),
      inputPattern: cleanString(idPolicy.input_pattern),
      normalizer: cleanString(idPolicy.normalizer),
      width: Number(idPolicy.width || 0)
    },
    lookupAdapter: cleanString(source.lookup_adapter),
    lookupFields: Array.isArray(source.lookup_fields)
      ? source.lookup_fields.map(cleanString).filter(Boolean)
      : [],
    order: order
  };
}

function normalizeFamily(record, order) {
  var source = objectRecord(record) || {};
  var key = cleanString(source.key);
  var targetTypes = Array.isArray(source.target_types)
    ? source.target_types.map(normalizeTargetType).filter(Boolean)
    : [];
  if (!key) return null;
  return {
    key: key,
    labels: Object.assign({}, objectRecord(source.labels) || {}),
    occurrenceFields: Array.isArray(source.occurrence_fields)
      ? source.occurrence_fields.filter(objectRecord).map(function (field) { return Object.assign({}, field); })
      : [],
    order: order,
    targetTypes: targetTypes,
    targetTypesById: new Map(targetTypes.map(function (targetType) {
      return [targetType.key, targetType];
    })),
    uiContributions: Object.assign({}, objectRecord(source.ui_contributions) || {})
  };
}

export function normalizeSemanticTokenRegistry(payload) {
  var source = objectRecord(payload) || {};
  var families = Array.isArray(source.families)
    ? source.families.map(normalizeFamily).filter(Boolean)
    : [];
  return {
    schemaVersion: cleanString(source.schema_version),
    targetLookupUrl: cleanString(source.target_lookup_url),
    families: families,
    familiesById: new Map(families.map(function (family) { return [family.key, family]; }))
  };
}

export function loadSemanticTokenRegistry(options = {}) {
  var fetchImpl = typeof options.fetch === "function" ? options.fetch : window.fetch.bind(window);
  var url = cleanString(options.url) || "/docs-viewer/config/semantic-tokens/registry.json";
  return fetchImpl(url, { cache: "no-store" })
    .then(function (response) {
      if (!response || !response.ok) throw new Error("Semantic token registry is unavailable.");
      return response.json();
    })
    .then(normalizeSemanticTokenRegistry);
}
