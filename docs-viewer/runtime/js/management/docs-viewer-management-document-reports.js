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

function fetchDocsIndexTreeForScope(context, scope) {
  var targetScope = cleanString(scope || currentViewerScope(context)).toLowerCase();
  return context.collectionProvider.readIndex({
    scope: targetScope
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

  var managementService = settings.managementService || null;
  var reportManagementBaseUrl = cleanString(managementService && managementService.baseUrl);
  return mountDocsViewerReport({
    appContext: settings.appContext,
    checkGeneratedDataReadCapability: settings.checkGeneratedDataReadCapability,
    content: settings.content,
    doc: settings.doc,
    fetchDocsIndexTree: function (scope) {
      return fetchDocsIndexTreeForScope(settings, scope);
    },
    managementContext: Boolean(settings.managementContext),
    managementService: managementService,
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
