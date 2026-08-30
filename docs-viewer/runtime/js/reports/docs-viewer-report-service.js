import {
  normalizeManagedDocumentTarget
} from "../management/docs-viewer-management-document-target.js";

function defaultFetch(url, options) {
  return window.fetch(url, options);
}

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function cleanBaseUrl(value) {
  return cleanString(value).replace(/\/+$/, "");
}

function fetchReportJson(path, options) {
  var settings = options || {};
  var baseUrl = cleanBaseUrl(settings.baseUrl);
  if (!baseUrl) {
    return Promise.reject(new Error("Local docs-management server is not configured."));
  }

  var requestOptions = {
    method: settings.method || "GET",
    headers: {
      Accept: "application/json"
    },
    cache: "no-store"
  };
  if (settings.payload !== undefined) {
    requestOptions.headers["Content-Type"] = "application/json";
    requestOptions.body = JSON.stringify(settings.payload);
  }

  var fetchImpl = settings.fetch || defaultFetch;
  return fetchImpl(baseUrl + path, requestOptions).then(function (response) {
    return response.json().catch(function () {
      throw new Error("HTTP " + response.status);
    }).then(function (payload) {
      if (!response.ok || (settings.requireOkEnvelope && (!payload || !payload.ok))) {
        throw new Error(payload && payload.error ? payload.error : "HTTP " + response.status);
      }
      return payload;
    });
  });
}

export function createDocsViewerReportService(options) {
  var settings = options || {};
  var serviceOptions = {
    baseUrl: cleanBaseUrl(settings.baseUrl),
    fetch: settings.fetch,
    snapshotRole: cleanString(settings.snapshotRole).toLowerCase() === "published"
      ? "published"
      : "generated"
  };

  return {
    baseUrl: serviceOptions.baseUrl,
    readSourceConfig: function () {
      return fetchReportJson("/docs/source-config", Object.assign({}, serviceOptions, {
        requireOkEnvelope: true
      }));
    },
    readSemanticTokens: function (request) {
      var scope = cleanString(request && request.scope).toLowerCase();
      var path = serviceOptions.snapshotRole === "published"
        ? "/docs/published/semantic-tokens"
        : "/docs/semantic-tokens";
      return fetchReportJson(
        path + "?scope=" + encodeURIComponent(scope),
        serviceOptions
      );
    },
    runBrokenLinksAudit: function (request) {
      var payload = {
        scope: cleanString(request && request.scope).toLowerCase()
      };
      return fetchReportJson("/docs/broken-links", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: payload,
        requireOkEnvelope: true
      }));
    },
    runProjectState: function () {
      return fetchReportJson("/docs/project-state", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: {},
        requireOkEnvelope: true
      }));
    },
    runDocsMedia: function (request) {
      return fetchReportJson("/docs/media-report", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: {
          scope: cleanString(request && request.scope).toLowerCase()
        },
        requireOkEnvelope: true
      }));
    },
    runUncatalogedFiles: function () {
      return fetchReportJson("/docs/uncataloged-files", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: {},
        requireOkEnvelope: true
      }));
    },
    runMissingSourceFiles: function () {
      return fetchReportJson("/docs/missing-source-files", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: {},
        requireOkEnvelope: true
      }));
    },
    openLocalTarget: function (target) {
      return fetchReportJson("/docs/open-local-target", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: { target: cleanString(target) },
        requireOkEnvelope: true
      }));
    },
    openSourceDoc: function (request) {
      var target = normalizeManagedDocumentTarget(request && request.target);
      return fetchReportJson("/docs/open-source", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: Object.assign({}, target, {
          editor: cleanString(request && request.editor) === "vscode" ? "vscode" : "default"
        }),
        requireOkEnvelope: true
      }));
    }
  };
}
