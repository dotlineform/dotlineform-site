import {
  fetchIndexTreeWithRetry,
  fetchPreferredGeneratedJson,
  managementReloadPath
} from "./docs-viewer-data.js";
import {
  normalizeDocsIndexTreePayload,
  normalizeRecentPayload
} from "./docs-viewer-tree-payload-adapter.js";

export function createDocsViewerGeneratedDataRuntime(options) {
  var settings = options || {};
  var generatedData = settings.generatedData || {};
  var management = settings.management || {};
  var selectedDocument = settings.selectedDocument || {};
  var window = settings.window;
  var assetVersion = settings.assetVersion || "";
  var generatedBaseUrl = settings.generatedBaseUrl || "";
  var reloadRetryAttempts = settings.reloadRetryAttempts || 0;
  var reloadRetryDelayMs = settings.reloadRetryDelayMs || 0;

  function currentViewerStage() {
    return typeof settings.viewerStage === "function" ? settings.viewerStage() : settings.viewerStage || "";
  }

  function requestViewerStage(request) {
    return Object.prototype.hasOwnProperty.call(request, "viewerStage") ? request.viewerStage : currentViewerStage();
  }

  function stageGeneratedCapability(capabilities, stage, key) {
    if (stage === "published") key = key.replace("generated_", "published_");
    var stageCaps = capabilities && capabilities.stages ? capabilities.stages[stage] : null;
    return Boolean(capabilities && capabilities.generated_data_reads && stageCaps && stageCaps.available && stageCaps[key]);
  }

  function readGeneratedCapabilities() {
    if (!generatedBaseUrl) return Promise.resolve(null);
    return window.fetch(generatedBaseUrl + "/capabilities", {
      headers: { Accept: "application/json" },
      cache: "no-store"
    })
      .then(function (response) {
        if (!response.ok) return null;
        return response.json();
      })
      .catch(function () {
        return null;
      });
  }

  function checkGeneratedDataReadCapability(stage) {
    var targetStage = stage === undefined ? currentViewerStage() : stage;
    if (!generatedBaseUrl || !targetStage) return Promise.resolve(false);
    if (!generatedData.generatedDataReadChecked && !generatedData.generatedDataReadRequestPromise) {
      generatedData.generatedDataReadRequestPromise = readGeneratedCapabilities().then(function (payload) {
        generatedData.generatedDataCapabilities = payload && payload.capabilities || null;
        generatedData.generatedDataReadChecked = true;
      }).finally(function () {
        generatedData.generatedDataReadRequestPromise = null;
      });
    }
    return Promise.resolve(generatedData.generatedDataReadRequestPromise).then(function () {
      return stageGeneratedCapability(generatedData.generatedDataCapabilities, targetStage, "generated_data_reads");
    });
  }

  function dataRequestOptions(overrides) {
    var requestSettings = overrides || {};
    return Object.assign({
      assetVersion: assetVersion,
      reloadNonce: selectedDocument.reloadNonce,
      reloadExpectedDocId: selectedDocument.reloadExpectedDocId,
      reloadRetryAttempts: reloadRetryAttempts,
      reloadRetryDelayMs: reloadRetryDelayMs,
      managementAvailable: management.managementAvailable,
      viewerStage: requestViewerStage(requestSettings),
      managementBaseUrl: generatedBaseUrl,
      fetch: function (url, fetchOptions) {
        return window.fetch(url, fetchOptions);
      },
      setTimeout: function (resolve, delayMs) {
        return window.setTimeout(resolve, delayMs);
      },
      checkGeneratedDataReadCapability: function () {
        return checkGeneratedDataReadCapability(requestViewerStage(requestSettings));
      },
      stageSupportsGeneratedSearchReads: function () {
        return stageGeneratedCapability(
          generatedData.generatedDataCapabilities || {},
          requestViewerStage(requestSettings),
          "generated_search_reads"
        );
      }
    }, requestSettings);
  }

  function readDocsIndexTree(options) {
    var requestSettings = options || {};
    return fetchIndexTreeWithRetry(dataRequestOptions({
      indexTreeUrl: requestSettings.indexTreeUrl,
      viewerStage: requestViewerStage(requestSettings)
    })).then(normalizeDocsIndexTreePayload);
  }

  function readDocumentPayload(doc, options) {
    var requestSettings = options || {};
    var docId = String(requestSettings.docId || doc && doc.doc_id || "").trim();
    var contentUrl = String(requestSettings.contentUrl || doc && doc.content_url || "").trim();
    return fetchPreferredGeneratedJson(
      contentUrl,
      "Failed to load " + contentUrl,
      managementReloadPath("/docs/doc", { stage: requestViewerStage(requestSettings), doc_id: docId }),
      dataRequestOptions(Object.assign({}, requestSettings, {
        useSearchCapability: false
      }))
    );
  }

  function readSearchIndex(options) {
    var requestSettings = options || {};
    return fetchPreferredGeneratedJson(
      requestSettings.searchIndexUrl,
      "Failed to load search data",
      managementReloadPath("/docs/search", { stage: requestViewerStage(requestSettings) }),
      dataRequestOptions(Object.assign({}, requestSettings, {
        useSearchCapability: true
      }))
    );
  }

  /** Use the generated-read service locally or a configured static file publicly.
   * A missing relationship file is unavailable data, distinct from an empty record.
   */
  function readDocumentLinks(target, options) {
    var staticBase = String(options && options.linksByIdUrlBase || "").replace(/\/$/, "");
    var path = managementReloadPath("/docs/links", {
      stage: target.stage, collection: target.collection, doc_id: target.doc_id
    });
    return fetchPreferredGeneratedJson(
      staticBase ? staticBase + "/" + encodeURIComponent(target.doc_id) + ".json" : "",
      "Failed to load Links",
      path,
      dataRequestOptions({ viewerStage: target.stage || "", useSearchCapability: false,
        reloadNonce: "", reloadRetryAttempts: 1 })
    ).catch(function (error) {
      if (error.status === 404) return null;
      throw error;
    });
  }

  function readRecent(options) {
    var requestSettings = options || {};
    return fetchPreferredGeneratedJson(
      requestSettings.recentUrl,
      "Failed to load Recent docs",
      managementReloadPath("/docs/recent", { stage: requestViewerStage(requestSettings) }),
      dataRequestOptions(Object.assign({}, requestSettings, {
        useSearchCapability: false
      }))
    ).then(normalizeRecentPayload);
  }

  return {
    checkGeneratedDataReadCapability: checkGeneratedDataReadCapability,
    dataRequestOptions: dataRequestOptions,
    readDocsIndexTree: readDocsIndexTree,
    readDocumentPayload: readDocumentPayload,
    readDocumentLinks: readDocumentLinks,
    readRecent: readRecent,
    readSearchIndex: readSearchIndex,
    stageGeneratedCapability: stageGeneratedCapability
  };
}
