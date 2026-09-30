import {
  readPublicCatalogueWork, readPublicCatalogueGallery, readPublicCatalogueSeriesGalleries,
  validateCatalogueSeriesGalleriesIndex, catalogueGalleryMediaPresentation
} from "./docs-viewer-catalogue-media.js";
import { readPublicCatalogueMediaConfig, validateCatalogueMediaPolicy } from "./docs-viewer-catalogue-media-policy.js";
import { docsViewerLinksDocumentHref } from "./docs-viewer-links-presentation.js";

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

  function collectionConfig() {
    var config = settings.workspaceConfig && settings.workspaceConfig.activeConfig;
    if (!config) throw new Error("Docs workspace is not configured.");
    return config;
  }

  function readIndex(optionsForRead) {
    var config = collectionConfig(optionsForRead);
    return generatedData.readDocsIndexTree({ indexTreeUrl: config.indexTreeUrl });
  }

  function readDocument(doc, optionsForRead) {
    return generatedData.readDocumentPayload(doc, {
      docId: cleanString(optionsForRead && optionsForRead.docId || doc && doc.doc_id)
    });
  }

  function readSearch(optionsForRead) {
    var config = collectionConfig(optionsForRead);
    return generatedData.readSearchIndex({ searchIndexUrl: config.searchIndexUrl }).then(function (payload) {
      if (!payload || !payload.header || payload.header.schema !== "docs_viewer_search_index_v4") {
        throw new Error("Search data has an unsupported schema.");
      }
      return payload;
    });
  }

  function readRecent(optionsForRead) {
    var config = collectionConfig(optionsForRead);
    return generatedData.readRecent({ recentUrl: config.recentUrl });
  }

  var provider = {
    documentHref: function (target) { return docsViewerLinksDocumentHref(target, collectionConfig()); },
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
  if (source && typeof source.readCatalogueGallery === "function") {
    provider.readCatalogueGallery = function (galleryId) { return source.readCatalogueGallery(galleryId); };
  } else if (routeContext().routeConfig && routeContext().routeConfig.appKind === "public") {
    provider.readCatalogueGallery = function (galleryId) {
      return readPublicCatalogueGallery(routeContext().routeConfig.catalogueGalleryRecordsBaseUrl, galleryId, function (url, optionsForFetch) {
        return settings.window.fetch(url, optionsForFetch);
      });
    };
  }
  if (provider.readCatalogueGallery) {
    provider.readCatalogueGalleryPresentation = async function (galleryId) {
      var [payload, policy] = await Promise.all([provider.readCatalogueGallery(galleryId), provider.readCatalogueMediaConfig()]);
      var config = routeContext().routeConfig || {};
      return catalogueGalleryMediaPresentation(payload, galleryId, policy, config.catalogueWorkThumbnailsBaseUrl);
    };
  }
  if (source && typeof source.readCatalogueSeriesGalleries === "function") {
    provider.readCatalogueSeriesGalleries = function () {
      return source.readCatalogueSeriesGalleries().then(validateCatalogueSeriesGalleriesIndex);
    };
  } else if (routeContext().routeConfig && routeContext().routeConfig.appKind === "public") {
    provider.readCatalogueSeriesGalleries = function () {
      return readPublicCatalogueSeriesGalleries(routeContext().routeConfig.catalogueSeriesGalleriesIndexUrl,
        function (url, optionsForFetch) { return settings.window.fetch(url, optionsForFetch); });
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
      return source.listStagedMedia(mediaKind, requestSettings);
    };
  }
  if (source && typeof source.previewStagedMedia === "function") {
    provider.previewStagedMedia = function (payload, optionsForPreview) {
      var requestSettings = optionsForPreview || {};
      return source.previewStagedMedia(payload, requestSettings);
    };
  }
  if (source && typeof source.applyStagedMedia === "function") {
    provider.applyStagedMedia = function (payload, optionsForApply) {
      var requestSettings = optionsForApply || {};
      return source.applyStagedMedia(payload, requestSettings);
    };
  }

  return provider;
}
