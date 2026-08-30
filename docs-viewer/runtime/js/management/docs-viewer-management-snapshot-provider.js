import {
  createDocsViewerConfiguredScopeProvider
} from "../shared/docs-viewer-configured-scope-provider.js";
import {
  fetchGeneratedJsonWithRetry,
  managementReloadPath
} from "../shared/docs-viewer-data.js";
import {
  normalizeDocsIndexTreePayload,
  normalizeRecentPayload
} from "../shared/docs-viewer-tree-payload-adapter.js";

function cleanScope(value) {
  return String(value || "").trim().toLowerCase();
}

function requestedSnapshotRole(windowRef) {
  try {
    return new URL(windowRef.location.href).searchParams.get("snapshot") === "published"
      ? "published"
      : "generated";
  } catch (_error) {
    return "generated";
  }
}

function publishedPath(path, scope, extra) {
  return managementReloadPath("/docs/published/" + path, Object.assign({
    scope: scope
  }, extra || {}));
}

function projectPublishedScopeConfigs(scopeConfig) {
  var configs = Array.isArray(scopeConfig.scopeConfigs) ? scopeConfig.scopeConfigs : [];
  configs.forEach(function (config) {
    var scope = cleanScope(config.scopeId);
    if (!scope) return;
    config.indexTreeUrl = publishedPath("index-tree", scope);
    config.recentUrl = publishedPath("recent", scope);
    config.backlinksUrl = publishedPath("backlinks", scope);
    config.searchIndexUrl = publishedPath("search", scope);
    var subScopes = Array.isArray(config.subScopes) ? config.subScopes : [];
    subScopes.forEach(function (subScope) {
      var subScopeId = cleanScope(subScope.subScope);
      if (!subScopeId) return;
      var base = "/docs/published/external/" + encodeURIComponent(scope) + "/" + encodeURIComponent(subScopeId);
      subScope.manifestUrl = base + "/manifest.json";
      subScope.byIdUrlBase = base + "/by-id";
    });
  });
}

export function createDocsViewerManagementSnapshotProvider(options) {
  var settings = options || {};
  var scopeConfig = settings.scopeConfig || {};
  var generatedData = settings.generatedData || {};
  var source = settings.source || null;
  var windowRef = settings.window || window;
  var role = requestedSnapshotRole(windowRef);

  var generatedProvider = createDocsViewerConfiguredScopeProvider(settings);
  if (role !== "published") return generatedProvider;

  function activeScope(optionsForRead) {
    var request = optionsForRead || {};
    var configured = typeof settings.viewerScope === "function"
      ? settings.viewerScope()
      : settings.viewerScope;
    return cleanScope(request.scope || configured);
  }

  function read(path, scope, extra, label, optionsForRead) {
    if (!scope) return Promise.reject(new Error("Published snapshot scope is required."));
    if (typeof generatedData.dataRequestOptions !== "function") {
      return Promise.reject(new Error("Published snapshot reads are unavailable."));
    }
    projectPublishedScopeConfigs(scopeConfig);
    return fetchGeneratedJsonWithRetry(
      publishedPath(path, scope, extra),
      label,
      generatedData.dataRequestOptions(Object.assign({}, optionsForRead || {}, {
        viewerScope: scope,
        useSearchCapability: path === "search"
      }))
    );
  }

  var provider = Object.assign({}, generatedProvider, {
    readIndex: function (optionsForRead) {
      var scope = activeScope(optionsForRead);
      return read(
        "index-tree",
        scope,
        null,
        "Failed to load published docs index tree",
        optionsForRead
      ).then(normalizeDocsIndexTreePayload);
    },
    readDocument: function (doc, optionsForRead) {
      var request = optionsForRead || {};
      var scope = activeScope(request);
      var docId = String(request.docId || doc && doc.doc_id || "").trim();
      return read(
        "doc",
        scope,
        { doc_id: docId },
        "Failed to load published document " + docId,
        request
      );
    },
    readRecent: function (optionsForRead) {
      var scope = activeScope(optionsForRead);
      return read(
        "recent",
        scope,
        null,
        "Failed to load published Recent docs",
        optionsForRead
      ).then(normalizeRecentPayload);
    },
    readSearch: function (optionsForRead) {
      var scope = activeScope(optionsForRead);
      return read(
        "search",
        scope,
        null,
        "Failed to load published Search index",
        optionsForRead
      );
    }
  });

  if (source && typeof source.readSource === "function") {
    provider.readSource = generatedProvider.readSource;
  }
  return provider;
}
