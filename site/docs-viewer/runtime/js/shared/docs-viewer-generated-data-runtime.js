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

  function currentViewerScope() {
    return typeof settings.viewerScope === "function" ? settings.viewerScope() : settings.viewerScope;
  }

  function currentViewerStage() {
    return typeof settings.viewerStage === "function" ? settings.viewerStage() : settings.viewerStage || "";
  }

  function requestViewerStage(request) {
    if (Object.prototype.hasOwnProperty.call(request, "viewerStage")) return request.viewerStage || "";
    return !request.viewerScope || request.viewerScope === currentViewerScope() ? currentViewerStage() : "";
  }

  function scopeGeneratedCapability(capabilities, scope, key, stage) {
    var scopeCaps = capabilities && capabilities.scopes ? capabilities.scopes[scope] : null;
    if (scopeCaps && scopeCaps.stages) scopeCaps = scopeCaps.stages[stage === undefined ? requestViewerStage({ viewerScope: scope }) : stage] || null;
    return Boolean(
      capabilities &&
      capabilities.generated_data_reads &&
      scopeCaps &&
      scopeCaps.available &&
      scopeCaps[key]
    );
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

  function checkGeneratedDataReadCapability(scope, stage) {
    var viewerScope = currentViewerScope();
    var targetScope = String(scope || viewerScope || "").trim();
    if (!generatedBaseUrl) {
      generatedData.generatedDataReadChecked = true;
      generatedData.generatedDataReadAvailable = false;
      return Promise.resolve(false);
    }
    if (generatedData.generatedDataReadChecked) {
      if (generatedData.generatedDataCapabilities && targetScope) {
        return Promise.resolve(scopeGeneratedCapability(generatedData.generatedDataCapabilities, targetScope, "generated_data_reads", stage));
      }
      return Promise.resolve(generatedData.generatedDataReadAvailable);
    }
    if (generatedData.generatedDataReadRequestPromise) {
      return generatedData.generatedDataReadRequestPromise;
    }

    generatedData.generatedDataReadRequestPromise = readGeneratedCapabilities()
      .then(function (payload) {
        if (!payload) {
          generatedData.generatedDataReadAvailable = false;
          generatedData.generatedDataReadChecked = true;
          return false;
        }
        generatedData.generatedDataCapabilities = payload.capabilities || null;
        generatedData.generatedDataReadAvailable = scopeGeneratedCapability(generatedData.generatedDataCapabilities, viewerScope, "generated_data_reads");
        generatedData.generatedDataReadChecked = true;
        return scopeGeneratedCapability(generatedData.generatedDataCapabilities, targetScope || viewerScope, "generated_data_reads", stage);
      })
      .catch(function () {
        generatedData.generatedDataReadAvailable = false;
        generatedData.generatedDataReadChecked = true;
        return false;
      })
      .finally(function () {
        generatedData.generatedDataReadRequestPromise = null;
      });

    return generatedData.generatedDataReadRequestPromise;
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
        return checkGeneratedDataReadCapability(requestSettings.viewerScope || currentViewerScope(), requestViewerStage(requestSettings));
      },
      scopeSupportsGeneratedSearchReads: function () {
        return scopeGeneratedCapability(
          generatedData.generatedDataCapabilities || {},
          requestSettings.viewerScope || currentViewerScope(),
          "generated_search_reads",
          requestViewerStage(requestSettings)
        );
      }
    }, requestSettings);
  }

  function readDocsIndexTree(options) {
    var requestSettings = options || {};
    return fetchIndexTreeWithRetry(dataRequestOptions({
      indexTreeUrl: requestSettings.indexTreeUrl,
      viewerStage: requestViewerStage(requestSettings),
      viewerScope: requestSettings.viewerScope || currentViewerScope()
    })).then(normalizeDocsIndexTreePayload);
  }

  function readDocumentPayload(doc, options) {
    var requestSettings = options || {};
    var docId = String(requestSettings.docId || doc && doc.doc_id || "").trim();
    var viewerScope = requestSettings.viewerScope || currentViewerScope();
    var contentUrl = String(requestSettings.contentUrl || doc && doc.content_url || "").trim();
    return fetchPreferredGeneratedJson(
      contentUrl,
      "Failed to load " + contentUrl,
      managementReloadPath("/docs/doc", { scope: viewerScope, stage: requestViewerStage(requestSettings), doc_id: docId }),
      dataRequestOptions(Object.assign({}, requestSettings, {
        useSearchCapability: false,
        viewerScope: viewerScope
      }))
    );
  }

  function readSearchIndex(options) {
    var requestSettings = options || {};
    var viewerScope = requestSettings.viewerScope || currentViewerScope();
    return fetchPreferredGeneratedJson(
      requestSettings.searchIndexUrl,
      "Failed to load search data",
      managementReloadPath("/docs/search", { scope: viewerScope, stage: requestViewerStage(requestSettings) }),
      dataRequestOptions(Object.assign({}, requestSettings, {
        useSearchCapability: true,
        viewerScope: viewerScope
      }))
    );
  }

  /** Use the generated-read service locally or a configured static file publicly.
   * A missing relationship file is unavailable data, distinct from an empty record.
   */
  function readDocumentLinks(target, options) {
    var staticBase = String(options && options.linksByIdUrlBase || "").replace(/\/$/, "");
    var path = managementReloadPath("/docs/links", {
      scope: target.scope, stage: target.stage, sub_scope: target.sub_scope, doc_id: target.doc_id
    });
    return fetchPreferredGeneratedJson(
      staticBase ? staticBase + "/" + encodeURIComponent(target.doc_id) + ".json" : "",
      "Failed to load Links",
      path,
      dataRequestOptions({ viewerScope: target.scope, viewerStage: target.stage || "", useSearchCapability: false,
        reloadNonce: "", reloadRetryAttempts: 1 })
    ).catch(function (error) {
      if (error.status === 404) return null;
      throw error;
    });
  }

  function readRecent(options) {
    var requestSettings = options || {};
    var viewerScope = requestSettings.viewerScope || currentViewerScope();
    return fetchPreferredGeneratedJson(
      requestSettings.recentUrl,
      "Failed to load Recent docs",
      managementReloadPath("/docs/recent", { scope: viewerScope, stage: requestViewerStage(requestSettings) }),
      dataRequestOptions(Object.assign({}, requestSettings, {
        useSearchCapability: false,
        viewerScope: viewerScope
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
    scopeGeneratedCapability: scopeGeneratedCapability
  };
}
