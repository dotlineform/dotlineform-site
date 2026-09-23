import { readPublicCatalogueWork, readPublicCatalogueSeries, catalogueSeriesMediaPresentation } from "./docs-viewer-catalogue-media.js";
import { readPublicCatalogueMediaConfig, validateCatalogueMediaPolicy } from "./docs-viewer-catalogue-media-policy.js";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function currentValue(value) {
  return typeof value === "function" ? value() : value;
}

export function createDocsViewerWorkspaceProvider(options) {
  var settings = options || {};
  var generatedData = settings.generatedData || {};
  var source = settings.source || null;

  function routeContext() {
    var routeSession = settings.routeSession || {};
    return currentValue(settings.routeContext) || routeSession.routeContext || {};
  }

  function activeStage() {
    return cleanString(currentValue(settings.viewerStage) || routeContext().viewerStage);
  }

  function configForStage(stage) {
    var workspace = settings.workspaceConfig || {};
    if (!stage) return workspace.activeConfig && !workspace.activeConfig.stage ? workspace.activeConfig : null;
    return workspace.stageConfigsById instanceof Map ? workspace.stageConfigsById.get(stage) : null;
  }

  function collectionConfig(optionsForRead) {
    var request = optionsForRead || {};
    if (Object.prototype.hasOwnProperty.call(request, "scope")) throw new Error("Scope targets are retired.");
    var stage = Object.prototype.hasOwnProperty.call(request, "stage") ? cleanString(request.stage) : activeStage();
    var config = configForStage(stage);
    if (!config) throw new Error("Docs stage is not configured: " + stage);
    return config;
  }

  function readIndex(optionsForRead) {
    var config = collectionConfig(optionsForRead);
    return generatedData.readDocsIndexTree({ indexTreeUrl: config.indexTreeUrl, viewerStage: config.stage });
  }

  function readDocument(doc, optionsForRead) {
    var config = collectionConfig(optionsForRead);
    return generatedData.readDocumentPayload(doc, {
      docId: cleanString(optionsForRead && optionsForRead.docId || doc && doc.doc_id),
      viewerStage: config.stage
    });
  }

  function readSearch(optionsForRead) {
    var config = collectionConfig(optionsForRead);
    return generatedData.readSearchIndex({ searchIndexUrl: config.searchIndexUrl, viewerStage: config.stage }).then(function (payload) {
      if (!payload || !payload.header || payload.header.schema !== "docs_viewer_search_index_v3"
        || Object.prototype.hasOwnProperty.call(payload.header, "scope")
        || payload.header.stage !== (config.stage || "published")) {
        throw new Error("Search data does not match the selected lifecycle stage.");
      }
      return payload;
    });
  }

  function readRecent(optionsForRead) {
    var config = collectionConfig(optionsForRead);
    return generatedData.readRecent({ recentUrl: config.recentUrl, viewerStage: config.stage });
  }

  var provider = {
    canReadLinks: canReadLinks,
    readLinks: readLinks,
    readDocument: readDocument,
    readIndex: readIndex,
    readRecent: readRecent,
    readSearch: readSearch
  };

  function canReadLinks(target) {
    var config = target && configForStage(cleanString(target.stage));
    return Boolean(config && config.linksEnabled && cleanString(target.stage) === cleanString(config.stage)
      && (cleanString(config.stage) || config.linksByIdUrlBase));
  }

  /** Read the exact staged document's separate relationship record; never infer another collection. */
  function readLinks(target) {
    if (!canReadLinks(target)) return Promise.reject(new Error("Links is not enabled for this stage."));
    var config = configForStage(cleanString(target.stage));
    return generatedData.readDocumentLinks(target, { linksByIdUrlBase: config.linksByIdUrlBase });
  }

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
  var mediaPolicyRead = null;
  if (source && typeof source.readCatalogueMediaConfig === "function"
    || routeContext().routeConfig && routeContext().routeConfig.appKind === "public") {
    provider.readCatalogueMediaConfig = function () {
      // Coalesce concurrent image reads, then revalidate policy on the next activation.
      if (!mediaPolicyRead) {
        mediaPolicyRead = Promise.resolve().then(function () {
          if (source && typeof source.readCatalogueMediaConfig === "function") return source.readCatalogueMediaConfig();
          return readPublicCatalogueMediaConfig(routeContext().routeConfig.catalogueMediaConfigUrl, function (url, optionsForFetch) {
            return settings.window.fetch(url, optionsForFetch);
          });
        }).then(validateCatalogueMediaPolicy).finally(function () { mediaPolicyRead = null; });
      }
      return mediaPolicyRead;
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
  if (source && typeof source.readCatalogueSeries === "function") {
    provider.readCatalogueSeries = function (seriesId) { return source.readCatalogueSeries(seriesId); };
  } else if (routeContext().routeConfig && routeContext().routeConfig.appKind === "public") {
    provider.readCatalogueSeries = function (seriesId) {
      return readPublicCatalogueSeries(routeContext().routeConfig.catalogueSeriesRecordsBaseUrl, seriesId, function (url, optionsForFetch) {
        return settings.window.fetch(url, optionsForFetch);
      });
    };
  }
  if (provider.readCatalogueSeries) {
    provider.readCatalogueSeriesPresentation = async function (seriesId) {
      var [payload, policy] = await Promise.all([provider.readCatalogueSeries(seriesId), provider.readCatalogueMediaConfig()]);
      var config = routeContext().routeConfig || {};
      return catalogueSeriesMediaPresentation(payload, seriesId, policy, config.catalogueWorkThumbnailsBaseUrl);
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
        stage: Object.prototype.hasOwnProperty.call(requestSettings, "stage") ? requestSettings.stage : activeStage()
      }));
    };
  }
  if (source && typeof source.previewStagedMedia === "function") {
    provider.previewStagedMedia = function (payload, optionsForPreview) {
      var requestSettings = optionsForPreview || {};
      return source.previewStagedMedia(payload, Object.assign({}, requestSettings, {
        stage: Object.prototype.hasOwnProperty.call(requestSettings, "stage") ? requestSettings.stage : activeStage()
      }));
    };
  }
  if (source && typeof source.applyStagedMedia === "function") {
    provider.applyStagedMedia = function (payload, optionsForApply) {
      var requestSettings = optionsForApply || {};
      return source.applyStagedMedia(payload, Object.assign({}, requestSettings, {
        stage: Object.prototype.hasOwnProperty.call(requestSettings, "stage") ? requestSettings.stage : activeStage()
      }));
    };
  }

  return provider;
}
