import {
  applyStagedMedia,
  listStagedMedia,
  previewStagedMedia,
  openManagedDiagramSource,
  readManagedDiagramSources,
  readManagedDocSource,
  readCatalogueMediaTargets,
  readCatalogueMediaConfig,
  readCatalogueWork,
  readCatalogueSeries,
  readCatalogueGallery,
  readDocumentLinkTargets,
  saveManagedDocSource
} from "./docs-viewer-management-client.js";

function currentValue(value) {
  return typeof value === "function" ? value() : value;
}

export function createDocsViewerManagementSourceAdapter(options) {
  var settings = options || {};
  var sourceService = settings.sourceService || null;
  var baseUrl = String(sourceService && sourceService.baseUrl || "").trim().replace(/\/+$/, "");
  if (!baseUrl) return null;

  function clientOptions(overrides) {
    return Object.assign({
      baseUrl: baseUrl,
      stage: String(currentValue(settings.viewerStage) || "").trim(),
      fetch: function (url, requestOptions) {
        return settings.window.fetch(url, requestOptions);
      }
    }, overrides || {});
  }

  return {
    readDocumentLinkTargets: function (target) {
      return readDocumentLinkTargets(target, clientOptions());
    },
    readCatalogueMediaTargets: function (stage) {
      return readCatalogueMediaTargets(stage, clientOptions());
    },
    readCatalogueMediaConfig: function (stage) {
      return readCatalogueMediaConfig(stage, clientOptions());
    },
    readCatalogueWork: function (workId, stage) {
      return readCatalogueWork(workId, stage, clientOptions());
    },
    readCatalogueSeries: function (seriesId, stage) {
      return readCatalogueSeries(seriesId, stage, clientOptions());
    },
    readCatalogueGallery: function (galleryId, stage) {
      return readCatalogueGallery(galleryId, stage, clientOptions());
    },
    readSource: function (target, optionsForRead) {
      return readManagedDocSource(target, clientOptions(optionsForRead));
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
    listStagedMedia: function (mediaKind, optionsForList) {
      return listStagedMedia(mediaKind, clientOptions(optionsForList));
    },
    previewStagedMedia: function (payload, optionsForPreview) {
      return previewStagedMedia(payload, clientOptions(optionsForPreview));
    },
    applyStagedMedia: function (payload, optionsForApply) {
      return applyStagedMedia(payload, clientOptions(optionsForApply));
    }
  };
}
