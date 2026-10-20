import {
  readPublicCatalogueGallery,
  catalogueGalleryMediaPresentation
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
    return generatedData.readDocumentPayload(target, { contentUrl: url, collection: target.collection || "", docId: target.doc_id });
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

  if (source) {
    provider.commitDocumentChange = source.commitDocumentChange;
    provider.subscribeDocumentChanges = source.subscribeDocumentChanges;
  }
  if (source && typeof source.readMetadata === "function") provider.readMetadata = source.readMetadata;
  if (source && typeof source.readSource === "function") {
    provider.readSource = function (target, optionsForRead) {
      return source.readSource(target, optionsForRead || {});
    };
  }
  if (source && typeof source.readDocumentLinkTargets === "function") {
    provider.readDocumentLinkTargets = function () {
      return source.readDocumentLinkTargets();
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
  if (source && typeof source.createCataloguePresentationOperation === "function") {
    provider.createCataloguePresentationOperation = source.createCataloguePresentationOperation;
  } else if (routeContext().routeConfig && routeContext().routeConfig.appKind === "public") {
    provider.createCataloguePresentationOperation = function (payload) {
      var embedded = payload && payload.catalogue && payload.catalogue.presentations || {};
      return { live: false, readWork: async function (workId, optionsForRead) {
        var key = "catalogue-work:" + workId;
        if (!optionsForRead || !optionsForRead.navigation) {
          if (!embedded[key]) throw new Error("Embedded Work presentation is unavailable: " + workId);
          return embedded[key];
        }
        var selected = await readDocument({ collection: "catalogue", doc_id: workId });
        var presentation = selected.catalogue && selected.catalogue.presentations && selected.catalogue.presentations[key];
        if (!presentation) throw new Error("Prepared Catalogue Work presentation is unavailable: " + workId);
        return presentation;
      } };
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
  if (source && typeof source.writeSource === "function") {
    provider.writeSource = function (target, payload, optionsForWrite) {
      return source.writeSource(target, payload, optionsForWrite || {});
    };
  }
  if (source && typeof source.prepareSourceMedia === "function") {
    provider.prepareSourceMedia = function (payload, optionsForPrepare) {
      return source.prepareSourceMedia(payload, optionsForPrepare || {});
    };
  }
  return provider;
}
