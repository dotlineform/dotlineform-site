import {
  readPublicCatalogueWork, readPublicCatalogueGallery, readPublicCatalogueSeriesGalleries,
  validateCatalogueSeriesGalleriesIndex, catalogueGalleryMediaPresentation
} from "./docs-viewer-catalogue-media.js";
import { readPublicCatalogueMediaConfig, validateCatalogueMediaPolicy } from "./docs-viewer-catalogue-media-policy.js";
import { documentTarget } from "./docs-viewer-document-target.js";
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
  var changeListeners = new Set();
  function commitDocumentChange(change) {
    var target = documentTarget(change.target);
    if (!change.deleted && (!change.record || change.record.doc_id !== target.doc_id)) throw new Error("Committed record did not match its target.");
    var failures = [];
    changeListeners.forEach(function (listener) {
      try { listener(Object.assign({}, change, { target: target })); } catch (error) { failures.push(error); }
    });
    if (failures.length) console.warn("Document saved; a retained list projection failed.", failures);
    return failures;
  }

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
    var target = documentTarget({ doc_id: cleanString(optionsForRead && optionsForRead.docId || doc && doc.doc_id), collection: doc && doc.collection || "" });
    var config = collectionConfig();
    var owner = target.collection ? config.collectionsById.get(target.collection) : null;
    if (target.collection && !owner) throw new Error("Unknown document collection: " + target.collection);
    var url = owner ? owner.byIdUrlBase + "/" + encodeURIComponent(target.doc_id) + ".json"
      : config.documentUrlTemplate.replace("{doc_id}", encodeURIComponent(target.doc_id));
    if (!url) throw new Error("Document payload URL is not configured.");
    return generatedData.readDocumentPayload({ doc_id: target.doc_id, content_url: url }, { collection: target.collection || "", docId: target.doc_id });
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
    commitDocumentChange: commitDocumentChange,
    subscribeDocumentChanges: function (listener) { changeListeners.add(listener); return function () { changeListeners.delete(listener); }; },
    documentHref: function (target) { return docsViewerLinksDocumentHref(target, collectionConfig()); },
    readDocument: readDocument,
    readIndex: readIndex,
    readRecent: readRecent,
    readSearch: readSearch
  };

  if (source && typeof source.readMetadata === "function") provider.readMetadata = source.readMetadata;
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
    function projectSavedSource(response) {
      if (response && response.source_saved && response.committed_document) {
        try { response.projection_errors = commitDocumentChange(response.committed_document).map(function (error) { return error.message; }); }
        catch (error) { response.projection_errors = [error.message]; }
      }
      return response;
    }
    provider.writeSource = function (target, payload, optionsForWrite) {
      return source.writeSource(target, payload, optionsForWrite || {}).then(projectSavedSource).catch(function (error) {
        projectSavedSource(error.payload);
        throw error;
      });
    };
  }
  if (source && typeof source.readSourceContext === "function") {
    provider.readSourceContext = function (target, payload) { return source.readSourceContext(target, payload); };
  }
  if (source && typeof source.openLocalTarget === "function") {
    provider.openLocalTarget = function (target) { return source.openLocalTarget(target); };
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
  if (source && typeof source.readSourceMediaOptions === "function") {
    provider.readSourceMediaOptions = function (mediaKind, optionsForRead) {
      return source.readSourceMediaOptions(mediaKind, optionsForRead || {});
    };
  }
  if (source && typeof source.applySourceMedia === "function") {
    provider.applySourceMedia = function (payload, file, optionsForApply) {
      return source.applySourceMedia(payload, file, optionsForApply || {});
    };
  }

  return provider;
}
