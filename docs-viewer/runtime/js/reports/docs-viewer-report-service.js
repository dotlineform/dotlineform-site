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
    fetch: settings.fetch
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
      return fetchReportJson(
        "/docs/semantic-tokens?scope=" + encodeURIComponent(scope),
        serviceOptions
      );
    },
    runBrokenLinksAudit: function (request) {
      var payload = {
        scope: cleanString(request && request.scope).toLowerCase()
      };
      if (request && request.activityContext) {
        payload.activity_context = request.activityContext;
      }
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
