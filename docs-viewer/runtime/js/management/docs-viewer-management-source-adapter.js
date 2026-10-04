import {
  applySourceMedia,
  readSourceMediaOptions,
  openManagedDiagramSource,
  readManagedDiagramSources,
  readManagedDocSource,
  readManagedDocMetadata,
  readManagedDocSourceContext,
  readCatalogueMediaTargets,
  readCatalogueMediaConfig,
  readCatalogueWork,
  readCatalogueGallery,
  readCatalogueSeriesGalleries,
  readDocumentLinkTargets,
  saveManagedDocSource
} from "./docs-viewer-management-client.js";

export function createDocsViewerManagementSourceAdapter(options) {
  var settings = options || {};
  var sourceService = settings.sourceService || null;
  var baseUrl = String(sourceService && sourceService.baseUrl || "").trim().replace(/\/+$/, "");
  if (!baseUrl) return null;

  function clientOptions(overrides) {
    return Object.assign({
      baseUrl: baseUrl,
      fetch: function (url, requestOptions) {
        return settings.window.fetch(url, requestOptions);
      }
    }, overrides || {});
  }

  return {
    readDocumentLinkTargets: function (target) {
      return readDocumentLinkTargets(target, clientOptions());
    },
    readCatalogueMediaTargets: function () {
      return readCatalogueMediaTargets( clientOptions());
    },
    readCatalogueMediaConfig: function () {
      return readCatalogueMediaConfig( clientOptions());
    },
    readCatalogueWork: function (workId) {
      return readCatalogueWork(workId,  clientOptions());
    },
    readCatalogueGallery: function (galleryId) {
      return readCatalogueGallery(galleryId,  clientOptions());
    },
    readCatalogueSeriesGalleries: function () {
      return readCatalogueSeriesGalleries(clientOptions());
    },
    readMetadata: function (target) { return readManagedDocMetadata(target, clientOptions()); },
    readSource: function (target, optionsForRead) {
      return readManagedDocSource(target, clientOptions(optionsForRead));
    },
    readSourceContext: function (target, payload) {
      return readManagedDocSourceContext(target, payload, clientOptions());
    },
    writeSource: function (target, payload, optionsForWrite) {
      return saveManagedDocSource(target, payload, clientOptions(optionsForWrite));
    },
    readDiagramSources: function (target, optionsForRead) {
      return readManagedDiagramSources(target, clientOptions(optionsForRead));
    },
    openDiagramSource: function (target, payload, optionsForOpen) {
      return openManagedDiagramSource(target, payload, clientOptions(optionsForOpen));
    },
    readSourceMediaOptions: function (mediaKind, optionsForRead) {
      return readSourceMediaOptions(mediaKind, clientOptions(optionsForRead));
    },
    applySourceMedia: function (payload, file, optionsForApply) {
      return applySourceMedia(payload, file, clientOptions(optionsForApply));
    }
  };
}
