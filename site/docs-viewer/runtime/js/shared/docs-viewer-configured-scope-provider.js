function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function currentValue(value) {
  return typeof value === "function" ? value() : value;
}

function scopeId(value) {
  return cleanString(value).toLowerCase();
}

function trimDataFilename(url) {
  return cleanString(url).replace(/\/(?:index|index-tree)\.json(?:[?#].*)?$/, "");
}

function targetSlug(target, origin) {
  var bucketUrl = cleanString(target && target.bucket_url);
  if (bucketUrl) {
    try {
      var url = new URL(bucketUrl, origin || "http://localhost");
      var filename = url.pathname.split("/").pop() || "";
      if (filename.slice(-5) === ".json") return filename.slice(0, -5);
    } catch (error) {
      // Fall through to the target id.
    }
  }
  return encodeURIComponent(cleanString(target && target.target_id));
}

export function createDocsViewerConfiguredScopeProvider(options) {
  var settings = options || {};
  var generatedData = settings.generatedData || {};
  var source = settings.source || null;

  function routeContext() {
    var routeSession = settings.routeSession || {};
    return currentValue(settings.routeContext) || routeSession.routeContext || {};
  }

  function activeScope() {
    return scopeId(currentValue(settings.viewerScope) || routeContext().viewerScope);
  }

  function configForScope(requestedScope) {
    var targetScope = scopeId(requestedScope || activeScope());
    var scopeConfig = settings.scopeConfig || {};
    var configured = scopeConfig.scopeConfigsById && typeof scopeConfig.scopeConfigsById.get === "function"
      ? scopeConfig.scopeConfigsById.get(targetScope)
      : null;
    if (configured) return configured;

    var route = routeContext();
    if (targetScope && targetScope === scopeId(route.viewerScope)) {
      return {
        scopeId: targetScope,
        indexTreeUrl: cleanString(route.indexTreeUrl),
        recentUrl: cleanString(route.recentUrl),
        searchIndexUrl: cleanString(route.searchIndexUrl)
      };
    }
    return null;
  }

  function collectionRequest(optionsForRead) {
    var requestSettings = optionsForRead || {};
    var targetScope = scopeId(requestSettings.scope || activeScope());
    var config = configForScope(targetScope);
    return {
      config: config,
      scope: targetScope
    };
  }

  function readIndex(optionsForRead) {
    var request = collectionRequest(optionsForRead);
    if (!request.config) return Promise.reject(new Error("Docs scope is not configured: " + request.scope));
    return generatedData.readDocsIndexTree({
      indexTreeUrl: cleanString(request.config.indexTreeUrl),
      viewerScope: request.scope
    });
  }

  function readDocument(doc, optionsForRead) {
    var requestSettings = optionsForRead || {};
    return generatedData.readDocumentPayload(doc, {
      docId: cleanString(requestSettings.docId || doc && doc.doc_id),
      viewerScope: scopeId(requestSettings.scope || activeScope())
    });
  }

  function readSearch(optionsForRead) {
    var request = collectionRequest(optionsForRead);
    if (!request.config) return Promise.reject(new Error("Docs scope is not configured: " + request.scope));
    return generatedData.readSearchIndex({
      searchIndexUrl: cleanString(request.config.searchIndexUrl),
      viewerScope: request.scope
    });
  }

  function readRecent(optionsForRead) {
    var request = collectionRequest(optionsForRead);
    if (!request.config) return Promise.reject(new Error("Docs scope is not configured: " + request.scope));
    return generatedData.readRecent({
      recentUrl: cleanString(request.config.recentUrl),
      viewerScope: request.scope
    });
  }

  function readReferences(optionsForRead) {
    var requestSettings = optionsForRead || {};
    var request = collectionRequest(requestSettings);
    if (!request.config) return Promise.reject(new Error("Docs scope is not configured: " + request.scope));
    var target = requestSettings.target || null;
    var baseUrl = trimDataFilename(request.config.indexTreeUrl);
    if (!baseUrl) {
      return Promise.reject(new Error("Docs scope is not configured: " + request.scope));
    }
    if (!target) {
      return generatedData.readReferencesIndex({
        baseUrl: baseUrl,
        viewerScope: request.scope
      });
    }

    var targetKind = cleanString(target.target_kind);
    var slug = targetSlug(target, settings.window && settings.window.location && settings.window.location.origin);
    var staticUrl = cleanString(target.bucket_url);
    if (!staticUrl) {
      staticUrl = baseUrl + "/references/by-target/" + encodeURIComponent(targetKind) + "/" + slug + ".json";
    }
    return generatedData.readReferenceTarget({
      staticUrl: staticUrl,
      targetKind: targetKind,
      targetSlug: slug,
      viewerScope: request.scope
    });
  }

  var provider = {
    readDocument: readDocument,
    readIndex: readIndex,
    readRecent: readRecent,
    readReferences: readReferences,
    readSearch: readSearch
  };

  if (source && typeof source.readSource === "function") {
    provider.readSource = function (docId, optionsForRead) {
      var requestSettings = optionsForRead || {};
      return source.readSource(docId, Object.assign({}, requestSettings, {
        scope: scopeId(requestSettings.scope || activeScope())
      }));
    };
  }
  if (source && typeof source.writeSource === "function") {
    provider.writeSource = function (payload, optionsForWrite) {
      var requestSettings = optionsForWrite || {};
      return source.writeSource(payload, Object.assign({}, requestSettings, {
        scope: scopeId(requestSettings.scope || activeScope())
      }));
    };
  }
  if (source && typeof source.readDiagramSources === "function") {
    provider.readDiagramSources = function (docId, optionsForRead) {
      var requestSettings = optionsForRead || {};
      return source.readDiagramSources(docId, Object.assign({}, requestSettings, {
        scope: scopeId(requestSettings.scope || activeScope())
      }));
    };
  }
  if (source && typeof source.openDiagramSource === "function") {
    provider.openDiagramSource = function (payload, optionsForOpen) {
      var requestSettings = optionsForOpen || {};
      return source.openDiagramSource(payload, Object.assign({}, requestSettings, {
        scope: scopeId(requestSettings.scope || activeScope())
      }));
    };
  }
  if (source && typeof source.listStagedMedia === "function") {
    provider.listStagedMedia = function (mediaKind, optionsForList) {
      var requestSettings = optionsForList || {};
      return source.listStagedMedia(mediaKind, Object.assign({}, requestSettings, {
        scope: scopeId(requestSettings.scope || activeScope())
      }));
    };
  }
  if (source && typeof source.previewStagedMedia === "function") {
    provider.previewStagedMedia = function (payload, optionsForPreview) {
      var requestSettings = optionsForPreview || {};
      return source.previewStagedMedia(payload, Object.assign({}, requestSettings, {
        scope: scopeId(requestSettings.scope || activeScope())
      }));
    };
  }
  if (source && typeof source.applyStagedMedia === "function") {
    provider.applyStagedMedia = function (payload, optionsForApply) {
      var requestSettings = optionsForApply || {};
      return source.applyStagedMedia(payload, Object.assign({}, requestSettings, {
        scope: scopeId(requestSettings.scope || activeScope())
      }));
    };
  }

  return provider;
}
