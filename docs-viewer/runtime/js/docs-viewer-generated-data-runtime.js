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

  return {
    checkGeneratedDataReadCapability: checkGeneratedDataReadCapability,
    dataRequestOptions: dataRequestOptions,
    scopeGeneratedCapability: scopeGeneratedCapability
  };
}
