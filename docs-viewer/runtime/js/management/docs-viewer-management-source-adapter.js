import {
  applyStagedMedia,
  listStagedMedia,
  previewStagedMedia,
  openManagedDiagramSource,
  readManagedDiagramSources,
  readManagedDocSource,
  rebuildManagedDocSource
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
      scope: String(currentValue(settings.viewerScope) || "").trim(),
      fetch: function (url, requestOptions) {
        return settings.window.fetch(url, requestOptions);
      }
    }, overrides || {});
  }

  return {
    readSource: function (docId, optionsForRead) {
      return readManagedDocSource(docId, clientOptions(optionsForRead));
    },
    writeSource: function (payload, optionsForWrite) {
      return rebuildManagedDocSource(payload, clientOptions(optionsForWrite));
    },
    readDiagramSources: function (docId, optionsForRead) {
      return readManagedDiagramSources(docId, clientOptions(optionsForRead));
    },
    openDiagramSource: function (payload, optionsForOpen) {
      return openManagedDiagramSource(payload, clientOptions(optionsForOpen));
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
