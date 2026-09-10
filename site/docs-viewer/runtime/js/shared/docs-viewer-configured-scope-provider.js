import { readPublicCatalogueWork } from "./docs-viewer-catalogue-media.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function currentValue(value) {
  return typeof value === "function" ? value() : value;
}

function scopeId(value) {
  return cleanString(value).toLowerCase();
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
        stage: cleanString(route.viewerStage),
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
      viewerScope: request.scope,
      viewerStage: cleanString(request.config.stage)
    });
  }

  function readDocument(doc, optionsForRead) {
    var requestSettings = optionsForRead || {};
    var request = collectionRequest(requestSettings);
    if (!request.config) return Promise.reject(new Error("Docs scope is not configured: " + request.scope));
    return generatedData.readDocumentPayload(doc, {
      docId: cleanString(requestSettings.docId || doc && doc.doc_id),
      viewerScope: request.scope,
      viewerStage: cleanString(request.config.stage)
    });
  }

  function readSearch(optionsForRead) {
    var request = collectionRequest(optionsForRead);
    if (!request.config) return Promise.reject(new Error("Docs scope is not configured: " + request.scope));
    return generatedData.readSearchIndex({
      searchIndexUrl: cleanString(request.config.searchIndexUrl),
      viewerScope: request.scope,
      viewerStage: cleanString(request.config.stage)
    });
  }

  function readRecent(optionsForRead) {
    var request = collectionRequest(optionsForRead);
    if (!request.config) return Promise.reject(new Error("Docs scope is not configured: " + request.scope));
    return generatedData.readRecent({
      recentUrl: cleanString(request.config.recentUrl),
      viewerScope: request.scope,
      viewerStage: cleanString(request.config.stage)
    });
  }

  var provider = {
    readDocument: readDocument,
    readIndex: readIndex,
    readRecent: readRecent,
    readSearch: readSearch
  };

  if (source && typeof source.readSource === "function") {
    provider.readSource = function (target, optionsForRead) {
      return source.readSource(target, optionsForRead || {});
    };
  }
  if (source && typeof source.readDocumentLinkTargets === "function") {
    provider.readDocumentLinkTargets = function (target) {
      return source.readDocumentLinkTargets(target);
    };
  }
  if (source && typeof source.readCatalogueMediaTargets === "function") {
    provider.readCatalogueMediaTargets = function () {
      return source.readCatalogueMediaTargets();
    };
  }
  if (source && typeof source.readCatalogueWork === "function") {
    provider.readCatalogueWork = function (workId) {
      return source.readCatalogueWork(workId);
    };
  } else if (routeContext().routeConfig && routeContext().routeConfig.appKind === "public") {
    provider.readCatalogueWork = function (workId) {
      return readPublicCatalogueWork(routeContext().routeConfig.catalogueWorkRecordsBaseUrl, workId, function (url, optionsForFetch) {
        return settings.window.fetch(url, optionsForFetch);
      });
    };
  }
  if (source && typeof source.writeSource === "function") {
    provider.writeSource = function (target, payload, optionsForWrite) {
      return source.writeSource(target, payload, optionsForWrite || {});
    };
  }
  if (source && typeof source.readDiagramSources === "function") {
    provider.readDiagramSources = function (target, optionsForRead) {
      return source.readDiagramSources(target, optionsForRead || {});
    };
  }
  if (source && typeof source.openDiagramSource === "function") {
    provider.openDiagramSource = function (target, payload, optionsForOpen) {
      return source.openDiagramSource(target, payload, optionsForOpen || {});
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
