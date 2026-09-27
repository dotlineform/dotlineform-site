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
    cache: (settings.method || "GET") === "GET" ? "no-cache" : "no-store"
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
    readWorkspaceLinks: function () {
      return fetchReportJson("/docs/workspace-links", serviceOptions);
    },
    readUnpublishable: function () {
      return fetchReportJson("/docs/unpublishable-report", Object.assign({}, serviceOptions, { requireOkEnvelope: true }));
    },
    openPublicationIgnore: function () {
      return fetchReportJson("/docs/open-publication-ignore", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: {  },
        requireOkEnvelope: true
      }));
    },
    readSeriesWorkMedia: function (request) {
      var target = normalizeManagedDocumentTarget(request && request.target);
      var query = new URLSearchParams(Object.assign({}, target, { work_id: request.workId })).toString();
      return fetchReportJson("/docs/series-work-media?" + query, Object.assign({}, serviceOptions, {
        requireOkEnvelope: true
      }));
    },
    readSeriesWorks: function (request) {
      var target = normalizeManagedDocumentTarget(request && request.target);
      var query = new URLSearchParams(target).toString();
      return fetchReportJson("/docs/series-works-report?" + query, Object.assign({}, serviceOptions, {
        requireOkEnvelope: true
      }));
    },
    readSemanticTokens: function () {
      return fetchReportJson("/docs/semantic-tokens", serviceOptions);
    },
    runBrokenLinksAudit: function (request) {
      var payload = {
        report_context: request && request.report_context
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
    readMediaFiles: function (request) {
      return fetchReportJson("/docs/media-files?" + new URLSearchParams({
        ...(request.collection ? { collection: request.collection } : {})
      }).toString(), Object.assign({}, serviceOptions, { requireOkEnvelope: true }));
    },
    readMediaReferences: function (request) {
      return fetchReportJson("/docs/media-references?" + new URLSearchParams({
        ...(request.collection ? { collection: request.collection } : {})
      }).toString(), Object.assign({}, serviceOptions, { requireOkEnvelope: true }));
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
    openDocsMediaSource: function (target) {
      return fetchReportJson("/docs/open-media-source", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: target,
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
