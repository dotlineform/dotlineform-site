import {
  requestUrl
} from "./docs-viewer-asset-url.js";

function defaultFetch(url, options) {
  return window.fetch(url, options);
}

function defaultSetTimeout(resolve, delayMs) {
  return window.setTimeout(resolve, delayMs);
}

export function requestOptions(options) {
  var settings = options || {};
  return {
    headers: { Accept: "application/json" },
    cache: settings.reloadNonce ? "no-store" : "default"
  };
}

export function generatedRequestOptions() {
  return {
    headers: { Accept: "application/json" },
    cache: "no-store"
  };
}

export function waitForReloadRetry(options) {
  var settings = options || {};
  var delayMs = typeof settings.reloadRetryDelayMs === "number" ? settings.reloadRetryDelayMs : 250;
  var setTimeoutFn = settings.setTimeout || defaultSetTimeout;
  return new Promise(function (resolve) {
    setTimeoutFn(resolve, delayMs);
  });
}

export function shouldRetryReload(error, attempt, options) {
  var settings = options || {};
  var attempts = typeof settings.reloadRetryAttempts === "number" ? settings.reloadRetryAttempts : 1;
  if (!settings.reloadNonce) return false;
  if (attempt >= attempts - 1) return false;
  if (error && (error.status === 404 || error.status === 500 || error.status === 503)) {
    return true;
  }
  return Boolean(error && /failed to fetch/i.test(String(error.message || "")));
}

export function fetchJsonOnce(url, failureLabel, reloadPath, options) {
  var settings = options || {};
  var fetchImpl = settings.fetch || defaultFetch;
  var fetchUrl = requestUrl(url, settings);
  var fetchOptions = requestOptions(settings);
  if (settings.reloadNonce && reloadPath && settings.managementAvailable && settings.managementBaseUrl) {
    fetchUrl = settings.managementBaseUrl + reloadPath;
    fetchOptions = {
      headers: { Accept: "application/json" }
    };
  }
  return fetchImpl(fetchUrl, fetchOptions)
    .then(function (response) {
      if (!response.ok) {
        var httpError = new Error(failureLabel + " (" + response.status + ")");
        httpError.status = response.status;
        throw httpError;
      }
      return response.json();
    });
}

export function fetchGeneratedJsonOnce(path, failureLabel, options) {
  var settings = options || {};
  var fetchImpl = settings.fetch || defaultFetch;
  return fetchImpl(settings.managementBaseUrl + path, generatedRequestOptions())
    .then(function (response) {
      if (!response.ok) {
        var httpError = new Error(failureLabel + " (" + response.status + ")");
        httpError.status = response.status;
        throw httpError;
      }
      return response.json();
    });
}

export function fetchJsonWithRetry(url, failureLabel, reloadPath, options) {
  var settings = options || {};
  var currentAttempt = typeof settings.attempt === "number" ? settings.attempt : 0;
  return fetchJsonOnce(url, failureLabel, reloadPath, settings).catch(function (error) {
    if (!shouldRetryReload(error, currentAttempt, settings)) {
      throw error;
    }
    return waitForReloadRetry(settings).then(function () {
      var nextSettings = Object.assign({}, settings, { attempt: currentAttempt + 1 });
      return fetchJsonWithRetry(url, failureLabel, reloadPath, nextSettings);
    });
  });
}

export function fetchGeneratedJsonWithRetry(path, failureLabel, options) {
  var settings = options || {};
  var currentAttempt = typeof settings.attempt === "number" ? settings.attempt : 0;
  return fetchGeneratedJsonOnce(path, failureLabel, settings).catch(function (error) {
    if (!shouldRetryReload(error, currentAttempt, settings)) {
      throw error;
    }
    return waitForReloadRetry(settings).then(function () {
      var nextSettings = Object.assign({}, settings, { attempt: currentAttempt + 1 });
      return fetchGeneratedJsonWithRetry(path, failureLabel, nextSettings);
    });
  });
}

export function fetchPreferredGeneratedJson(staticUrl, failureLabel, generatedPath, options) {
  var settings = options || {};
  var checkGeneratedDataReadCapability = settings.checkGeneratedDataReadCapability || function () {
    return Promise.resolve(false);
  };
  return checkGeneratedDataReadCapability().then(function (available) {
    var generatedAvailable = settings.useSearchCapability
      ? Boolean(settings.scopeSupportsGeneratedSearchReads && settings.scopeSupportsGeneratedSearchReads())
      : available;
    if (generatedAvailable) {
      return fetchGeneratedJsonWithRetry(generatedPath, failureLabel, settings);
    }
    return fetchJsonWithRetry(staticUrl, failureLabel, "", settings);
  });
}

export function indexIncludesExpectedDoc(payload, expectedDocId) {
  if (!expectedDocId) return true;
  var docs = payload && Array.isArray(payload.docs) ? payload.docs : [];
  return docs.some(function (doc) {
    return doc && doc.doc_id === expectedDocId;
  });
}

export function fetchIndexWithRetry(options) {
  var settings = options || {};
  var currentAttempt = typeof settings.attempt === "number" ? settings.attempt : 0;
  var attempts = typeof settings.reloadRetryAttempts === "number" ? settings.reloadRetryAttempts : 1;
  return fetchPreferredGeneratedJson(
    settings.indexUrl,
    "Failed to load docs index",
    managementReloadPath("/docs/generated/index", { scope: settings.viewerScope }),
    Object.assign({}, settings, { attempt: currentAttempt, useSearchCapability: false })
  )
    .then(function (payload) {
      if (indexIncludesExpectedDoc(payload, settings.reloadExpectedDocId)) {
        return payload;
      }
      if (!settings.reloadNonce || currentAttempt >= attempts - 1) {
        var missingError = new Error("Updated docs index is missing " + settings.reloadExpectedDocId + ".");
        missingError.status = 404;
        throw missingError;
      }
      return waitForReloadRetry(settings).then(function () {
        var nextSettings = Object.assign({}, settings, { attempt: currentAttempt + 1 });
        return fetchIndexWithRetry(nextSettings);
      });
    });
}

export function managementReloadPath(path, params) {
  if (!path || !params) return "";
  var query = [];
  Object.keys(params).forEach(function (key) {
    var value = String(params[key] || "").trim();
    if (!value) return;
    query.push(encodeURIComponent(key) + "=" + encodeURIComponent(value));
  });
  return query.length ? path + "?" + query.join("&") : path;
}
