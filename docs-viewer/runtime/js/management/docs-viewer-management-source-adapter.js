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
    readSource: function (target, optionsForRead) {
      return readManagedDocSource(target, clientOptions(optionsForRead));
    },
    writeSource: function (target, payload, optionsForWrite) {
      return rebuildManagedDocSource(target, payload, clientOptions(optionsForWrite));
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
