import {
  fetchJsonWithRetry
} from "./docs-viewer-data.js";

export function createDocsViewerConfigService(options) {
  var settings = options || {};
  var docsViewerConfigUrl = String(settings.docsViewerConfigUrl || "").trim();
  var dataRequestOptions = typeof settings.dataRequestOptions === "function"
    ? settings.dataRequestOptions
    : function () { return {}; };

  function fetchDocsViewerConfig(options) {
    var requestSettings = options || {};
    if (!docsViewerConfigUrl) {
      return Promise.reject(new Error("Docs Viewer config URL is not configured."));
    }
    return fetchJsonWithRetry(
      docsViewerConfigUrl,
      "Failed to load Docs Viewer config",
      "",
      dataRequestOptions(requestSettings.reloadNonce ? { reloadNonce: requestSettings.reloadNonce } : {})
    );
  }

  return {
    docsViewerConfigUrl: docsViewerConfigUrl,
    fetchDocsViewerConfig: fetchDocsViewerConfig
  };
}
