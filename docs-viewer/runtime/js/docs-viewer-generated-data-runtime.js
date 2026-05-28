import {
  appendAssetVersion,
  fetchIndexWithRetry,
  fetchPreferredGeneratedJson,
  managementReloadPath
} from "./docs-viewer-data.js";

export function createDocsViewerGeneratedDataRuntime(options) {
  var settings = options || {};
  var state = settings.state;
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
      state.generatedDataReadChecked = true;
      state.generatedDataReadAvailable = false;
      return Promise.resolve(false);
    }
    if (state.generatedDataReadChecked) {
      if (state.managementCapabilities && targetScope) {
        return Promise.resolve(scopeGeneratedCapability(state.managementCapabilities, targetScope, "generated_data_reads"));
      }
      return Promise.resolve(state.generatedDataReadAvailable);
    }
    if (state.generatedDataReadRequestPromise) {
      return state.generatedDataReadRequestPromise;
    }

    state.generatedDataReadRequestPromise = readGeneratedCapabilities()
      .then(function (payload) {
        if (!payload) {
          state.generatedDataReadAvailable = false;
          state.generatedDataReadChecked = true;
          return false;
        }
        state.managementCapabilities = payload.capabilities || null;
        state.generatedDataReadAvailable = scopeGeneratedCapability(state.managementCapabilities, viewerScope, "generated_data_reads");
        state.generatedDataReadChecked = true;
        return scopeGeneratedCapability(state.managementCapabilities, targetScope || viewerScope, "generated_data_reads");
      })
      .catch(function () {
        state.generatedDataReadAvailable = false;
        state.generatedDataReadChecked = true;
        return false;
      })
      .finally(function () {
        state.generatedDataReadRequestPromise = null;
      });

    return state.generatedDataReadRequestPromise;
  }

  function dataRequestOptions(overrides) {
    var requestSettings = overrides || {};
    return Object.assign({
      assetVersion: assetVersion,
      reloadNonce: state.reloadNonce,
      reloadExpectedDocId: state.reloadExpectedDocId,
      reloadRetryAttempts: reloadRetryAttempts,
      reloadRetryDelayMs: reloadRetryDelayMs,
      managementAvailable: state.managementAvailable,
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
          state.managementCapabilities || {},
          requestSettings.viewerScope || currentViewerScope(),
          "generated_search_reads"
        );
      }
    }, requestSettings);
  }

  function readDocsIndex(options) {
    var requestSettings = options || {};
    return fetchIndexWithRetry(dataRequestOptions({
      indexUrl: requestSettings.indexUrl,
      viewerScope: requestSettings.viewerScope || currentViewerScope()
    }));
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

  function readScopeIndex(options) {
    var requestSettings = options || {};
    var targetScope = String(requestSettings.viewerScope || currentViewerScope() || "").trim().toLowerCase();
    var targetConfig = requestSettings.scopeConfig || null;
    if (!targetConfig || !targetConfig.indexUrl) {
      return Promise.reject(new Error("Docs scope is not configured: " + targetScope));
    }
    return fetchIndexWithRetry(dataRequestOptions({
      indexUrl: appendAssetVersion(targetConfig.indexUrl),
      viewerScope: targetScope,
      reloadNonce: "",
      reloadExpectedDocId: ""
    }));
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
    readDocsIndex: readDocsIndex,
    readDocumentPayload: readDocumentPayload,
    readReferenceTarget: readReferenceTarget,
    readReferencesIndex: readReferencesIndex,
    readScopeIndex: readScopeIndex,
    readSearchIndex: readSearchIndex,
    scopeGeneratedCapability: scopeGeneratedCapability
  };
}
