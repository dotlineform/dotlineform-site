import {
  readPublicCatalogueGallery,
  catalogueGalleryMediaPresentation,
  catalogueAssetUrl,
  catalogueDocumentImage,
  catalogueDocumentWorkPresentation
} from "./docs-viewer-catalogue-media.js";
import { readPublicCatalogueMediaConfig, validateCatalogueMediaPolicy } from "./docs-viewer-catalogue-media-policy.js";
import { fetchDocsCollectionManifest } from "./docs-viewer-data.js";
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

  var publicContextManifestRead = null;
  provider.readContextManifest = async function () {
    if (publicContextManifestRead) return publicContextManifestRead;
    var url = collectionConfig().collectionsById.get("works")?.manifestUrl;
    if (!url) throw new Error("Context manifest is not configured.");
    var manifestRead = fetchDocsCollectionManifest(url, function (target, optionsForFetch) {
      return settings.window.fetch(target, optionsForFetch);
    });
    if (routeContext().routeConfig?.appKind !== "public") return manifestRead;
    publicContextManifestRead = manifestRead.catch(function (error) {
      publicContextManifestRead = null;
      throw error;
    });
    return publicContextManifestRead;
  };

  if (source) {
    provider.commitDocumentChange = source.commitDocumentChange;
    provider.subscribeDocumentChanges = source.subscribeDocumentChanges;
    provider.commitDocumentStar = source.commitDocumentStar;
    provider.subscribeDocumentStars = source.subscribeDocumentStars;
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
  provider.catalogueImage = function (image) {
    return catalogueDocumentImage(image, routeContext().routeConfig.catalogueWorkPrimaryBaseUrl);
  };
  provider.catalogueDownloadUrl = function (identity) {
    return catalogueAssetUrl(routeContext().routeConfig.catalogueWorkFilesBaseUrl, identity);
  };
  provider.readCatalogueWorkPresentation = async function (workId, loadedPayload) {
    var payload = loadedPayload || await readDocument({ collection: "catalogue", doc_id: workId });
    return catalogueDocumentWorkPresentation(payload, workId, routeContext().routeConfig.catalogueWorkPrimaryBaseUrl);
  };
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
      var [payload, policy, manifest] = await Promise.all([
        provider.readCatalogueGallery(galleryId),
        provider.readCatalogueMediaConfig(),
        provider.readContextManifest().catch(function () { return null; })
      ]);
      var config = routeContext().routeConfig || {};
      var presentation = catalogueGalleryMediaPresentation(payload, galleryId, policy, config.catalogueWorkThumbnailsBaseUrl, manifest?.docs);
      presentation.gallery.context_unavailable = manifest === null;
      return presentation;
    };
  }
  if (source && typeof source.readCatalogueGalleryReportSearch === "function") {
    provider.readCatalogueGalleryReportSearch = function () { return source.readCatalogueGalleryReportSearch(); };
  } else if (routeContext().routeConfig?.appKind === "public") {
    provider.readCatalogueGalleryReportSearch = async function () {
      var url = routeContext().routeConfig.catalogueGalleryReportSearchUrl;
      if (!url) throw new Error("Catalogue Gallery search is not configured.");
      var response = await settings.window.fetch(url, { cache: "no-cache", headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("Catalogue Gallery search is unavailable (" + response.status + ").");
      return response.json();
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
