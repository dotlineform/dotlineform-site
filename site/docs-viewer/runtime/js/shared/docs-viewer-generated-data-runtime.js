import {
  appendAssetVersion
} from "./docs-viewer-asset-url.js";
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

  function scopeGeneratedCapability(capabilities, scope, key) {
    var scopeCaps = capabilities && capabilities.scopes ? capabilities.scopes[scope] : null;
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

  function checkGeneratedDataReadCapability(scope) {
    var viewerScope = currentViewerScope();
    var targetScope = String(scope || viewerScope || "").trim();
    if (!generatedBaseUrl) {
      generatedData.generatedDataReadChecked = true;
      generatedData.generatedDataReadAvailable = false;
      return Promise.resolve(false);
    }
    if (generatedData.generatedDataReadChecked) {
      if (generatedData.generatedDataCapabilities && targetScope) {
        return Promise.resolve(scopeGeneratedCapability(generatedData.generatedDataCapabilities, targetScope, "generated_data_reads"));
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
        return scopeGeneratedCapability(generatedData.generatedDataCapabilities, targetScope || viewerScope, "generated_data_reads");
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
      managementBaseUrl: generatedBaseUrl,
      fetch: function (url, fetchOptions) {
        return window.fetch(url, fetchOptions);
      },
      setTimeout: function (resolve, delayMs) {
        return window.setTimeout(resolve, delayMs);
      },
      checkGeneratedDataReadCapability: function () {
        return checkGeneratedDataReadCapability(requestSettings.viewerScope || currentViewerScope());
      },
      scopeSupportsGeneratedSearchReads: function () {
        return scopeGeneratedCapability(
          generatedData.generatedDataCapabilities || {},
          requestSettings.viewerScope || currentViewerScope(),
          "generated_search_reads"
        );
      }
    }, requestSettings);
  }

  function readDocsIndexTree(options) {
    var requestSettings = options || {};
    return fetchIndexTreeWithRetry(dataRequestOptions({
      indexTreeUrl: requestSettings.indexTreeUrl,
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
      managementReloadPath("/docs/generated/payload", { scope: viewerScope, doc_id: docId }),
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
      managementReloadPath("/docs/generated/search", { scope: viewerScope }),
      dataRequestOptions(Object.assign({}, requestSettings, {
        useSearchCapability: true,
        viewerScope: viewerScope
      }))
    );
  }

  function readRecent(options) {
    var requestSettings = options || {};
    var viewerScope = requestSettings.viewerScope || currentViewerScope();
    return fetchPreferredGeneratedJson(
      requestSettings.recentUrl,
      "Failed to load Recent docs",
      managementReloadPath("/docs/generated/recent", { scope: viewerScope }),
      dataRequestOptions(Object.assign({}, requestSettings, {
        useSearchCapability: false,
        viewerScope: viewerScope
      }))
    ).then(normalizeRecentPayload);
  }

  function readReferencesIndex(options) {
    var requestSettings = options || {};
    var targetScope = String(requestSettings.viewerScope || currentViewerScope() || "").trim().toLowerCase();
    var baseUrl = String(requestSettings.baseUrl || "").trim();
    if (!baseUrl) {
      return Promise.reject(new Error("Docs scope is not configured: " + targetScope));
    }
    return fetchPreferredGeneratedJson(
      appendAssetVersion(baseUrl + "/references/index.json"),
      "Failed to load docs references",
      managementReloadPath("/docs/generated/references", { scope: targetScope }),
      dataRequestOptions({
        viewerScope: targetScope,
        reloadNonce: "",
        reloadExpectedDocId: ""
      })
    );
  }

  function readReferenceTarget(options) {
    var requestSettings = options || {};
    var targetScope = String(requestSettings.viewerScope || currentViewerScope() || "").trim().toLowerCase();
    var targetKind = String(requestSettings.targetKind || "").trim();
    var targetSlug = String(requestSettings.targetSlug || "").trim();
    return fetchPreferredGeneratedJson(
      appendAssetVersion(requestSettings.staticUrl),
      "Failed to load docs reference target",
      managementReloadPath("/docs/generated/reference-target", {
        scope: targetScope,
        target_kind: targetKind,
        target_slug: targetSlug
      }),
      dataRequestOptions({
        viewerScope: targetScope,
        reloadNonce: "",
        reloadExpectedDocId: ""
      })
    );
  }

  return {
    checkGeneratedDataReadCapability: checkGeneratedDataReadCapability,
    dataRequestOptions: dataRequestOptions,
    readDocsIndexTree: readDocsIndexTree,
    readDocumentPayload: readDocumentPayload,
    readRecent: readRecent,
    readReferenceTarget: readReferenceTarget,
    readReferencesIndex: readReferencesIndex,
    readSearchIndex: readSearchIndex,
    scopeGeneratedCapability: scopeGeneratedCapability
  };
}
