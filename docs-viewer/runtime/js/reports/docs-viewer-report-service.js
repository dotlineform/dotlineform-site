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
    readSeriesGalleries: function () {
      return fetchReportJson("/docs/series-galleries-report", serviceOptions);
    },
    readWorkDocumentCoverage: function () {
      return fetchReportJson("/docs/work-document-coverage", serviceOptions);
    },
    readWorkspaceLinks: function () {
      return fetchReportJson("/docs/workspace-links", serviceOptions);
    },
    refreshWorkspaceLinks: function () {
      return fetchReportJson("/docs/workspace-links", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: {}
      }));
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
    readBrokenLinks: function () {
      return fetchReportJson("/docs/broken-links", Object.assign({}, serviceOptions, { requireOkEnvelope: true }));
    },
    runBrokenLinksAudit: function () {
      return fetchReportJson("/docs/broken-links", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: {},
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
    readMediaMetadata: function () {
      return fetchReportJson("/docs/media-metadata", Object.assign({}, serviceOptions, { requireOkEnvelope: true }));
    },
    refreshMediaMetadata: function () {
      return fetchReportJson("/docs/media-refresh", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: {},
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
    runFoldersWithoutWorks: function () {
      return fetchReportJson("/docs/folders-without-works", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: {},
        requireOkEnvelope: true
      }));
    },
    runWorkDownloads: function () {
      return fetchReportJson("/docs/work-downloads", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: {},
        requireOkEnvelope: true
      }));
    },
    openWorkDownload: function (filename) {
      return fetchReportJson("/docs/open-work-download", Object.assign({}, serviceOptions, {
        method: "POST",
        payload: { filename: filename },
        requireOkEnvelope: true
      }));
    },
    runWorkLinks: function () {
      return fetchReportJson("/docs/work-links", Object.assign({}, serviceOptions, {
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
