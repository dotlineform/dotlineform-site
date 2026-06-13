import {
  createDocsViewerReportService
} from "../reports/docs-viewer-report-service.js";
import {
  mountDocsViewerReport
} from "../reports/docs-viewer-reports.js";

function cleanString(value) {
  return String(value || "").trim();
}

function currentViewerScope(context) {
  return cleanString(context && context.viewerScope);
}

function scopeConfigs(context) {
  var scopeConfig = context && context.scopeConfigState ? context.scopeConfigState : {};
  return Array.isArray(scopeConfig.scopeConfigs) ? scopeConfig.scopeConfigs : [];
}

function scopeConfigFor(context, scope) {
  var targetScope = cleanString(scope || currentViewerScope(context)).toLowerCase();
  var scopeConfig = context && context.scopeConfigState ? context.scopeConfigState : {};
  return scopeConfig.scopeConfigsById ? scopeConfig.scopeConfigsById.get(targetScope) : null;
}

function docsScopeDataBaseUrl(context, scope) {
  var targetConfig = scopeConfigFor(context, scope);
  var indexUrl = targetConfig ? cleanString(targetConfig.indexTreeUrl) : "";
  return indexUrl.replace(/\/(?:index|index-tree)\.json(?:[?#].*)?$/, "");
}

function referenceTargetSlug(target) {
  var bucketUrl = cleanString(target && target.bucket_url);
  if (bucketUrl) {
    try {
      var url = new URL(bucketUrl, window.location.origin);
      var filename = url.pathname.split("/").pop() || "";
      if (filename.slice(-5) === ".json") return filename.slice(0, -5);
    } catch (error) {
      // Fall through to target id encoding.
    }
  }
  return encodeURIComponent(cleanString(target && target.target_id));
}

function fetchDocsIndexTreeForScope(context, scope) {
  var targetScope = cleanString(scope || currentViewerScope(context)).toLowerCase();
  var targetConfig = scopeConfigFor(context, targetScope);
  if (!targetConfig || !targetConfig.indexTreeUrl) {
    return Promise.reject(new Error("Docs scope is not configured: " + targetScope));
  }
  return context.generatedData.readDocsIndexTree({
    indexTreeUrl: targetConfig.indexTreeUrl,
    viewerScope: targetScope,
    reloadNonce: "",
    reloadExpectedDocId: ""
  });
}

function fetchDocsReferencesIndexForScope(context, scope) {
  var targetScope = cleanString(scope || currentViewerScope(context)).toLowerCase();
  var baseUrl = docsScopeDataBaseUrl(context, targetScope);
  if (!baseUrl) {
    return Promise.reject(new Error("Docs scope is not configured: " + targetScope));
  }
  return context.generatedData.readReferencesIndex({
    baseUrl: baseUrl,
    viewerScope: targetScope
  });
}

function fetchDocsReferenceTargetForScope(context, scope, target) {
  var targetScope = cleanString(scope || currentViewerScope(context)).toLowerCase();
  var targetKind = cleanString(target && target.target_kind);
  var targetSlug = referenceTargetSlug(target);
  var staticUrl = cleanString(target && target.bucket_url);
  if (!staticUrl) {
    var baseUrl = docsScopeDataBaseUrl(context, targetScope);
    staticUrl = baseUrl + "/references/by-target/" + encodeURIComponent(targetKind) + "/" + targetSlug + ".json";
  }
  return context.generatedData.readReferenceTarget({
    staticUrl: staticUrl,
    targetKind: targetKind,
    targetSlug: targetSlug,
    viewerScope: targetScope
  });
}

function payloadHasReport(payload) {
  return Boolean(payload && cleanString(payload.viewer_report));
}

export function mountDocsViewerManageDocumentExtras(context) {
  var settings = context || {};
  var payload = settings.payload || {};
  var routeContext = settings.routeContext || {};
  if (!payloadHasReport(payload)) return Promise.resolve(false);

  var reportManagementBaseUrl = cleanString(settings.managementBaseUrl);
  return mountDocsViewerReport({
    allowManagement: settings.allowManagement,
    checkGeneratedDataReadCapability: settings.checkGeneratedDataReadCapability,
    content: settings.content,
    doc: settings.doc,
    fetchDocsReferenceTarget: function (scope, target) {
      return fetchDocsReferenceTargetForScope(settings, scope, target);
    },
    fetchDocsReferencesIndex: function (scope) {
      return fetchDocsReferencesIndexForScope(settings, scope);
    },
    fetchDocsIndexTree: function (scope) {
      return fetchDocsIndexTreeForScope(settings, scope);
    },
    managementMode: Boolean(settings.managementMode),
    payload: payload,
    reportRegistryUrl: cleanString(routeContext.reportRegistryUrl),
    reportService: reportManagementBaseUrl
      ? createDocsViewerReportService({ baseUrl: reportManagementBaseUrl })
      : null,
    setStatus: settings.setStatus,
    scopeConfigs: scopeConfigs(settings).slice(),
    viewerScope: currentViewerScope(settings),
    viewerUrlForScope: settings.viewerUrlForScope
  });
}
