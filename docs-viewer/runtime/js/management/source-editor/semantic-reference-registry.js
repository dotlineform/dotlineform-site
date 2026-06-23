function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function objectRecord(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

function normalizeKind(record, order) {
  var source = objectRecord(record) || {};
  var kind = cleanString(source.kind);
  var id = objectRecord(source.id) || {};
  var route = objectRecord(source.route) || {};
  var sourceEditor = objectRecord(source.source_editor) || {};
  if (!kind) return null;
  return {
    kind: kind,
    id: {
      normalizer: cleanString(id.normalizer),
      width: Number(id.width || 0),
      example: cleanString(id.example)
    },
    order: order,
    picker: sourceEditor.picker !== false,
    route: {
      path: cleanString(route.path),
      param: cleanString(route.param),
      type: cleanString(route.type)
    },
    selectionSearch: sourceEditor.selection_search !== false
  };
}

export function normalizeSemanticReferenceRegistry(payload) {
  var source = objectRecord(payload) || {};
  var kinds = Array.isArray(source.kinds)
    ? source.kinds.map(normalizeKind).filter(Boolean)
    : [];
  return {
    schemaVersion: cleanString(source.schema_version),
    targetLookupUrl: cleanString(source.target_lookup_url),
    kinds: kinds,
    kindsById: new Map(kinds.map(function (kind) { return [kind.kind, kind]; }))
  };
}

export function loadSemanticReferenceRegistry(options = {}) {
  var fetchImpl = typeof options.fetch === "function" ? options.fetch : window.fetch.bind(window);
  var url = cleanString(options.url) || "/docs-viewer/config/semantic-references/registry.json";
  return fetchImpl(url, { cache: "no-store" })
    .then(function (response) {
      if (!response || !response.ok) throw new Error("Semantic reference registry is unavailable.");
      return response.json();
    })
    .then(normalizeSemanticReferenceRegistry);
}
