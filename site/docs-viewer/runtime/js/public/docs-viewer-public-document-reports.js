import {
  mountDocsViewerPublicReport
} from "../reports/docs-viewer-public-reports.js";

function cleanString(value) {
  return String(value || "").trim();
}

function payloadHasReport(payload) {
  return Boolean(payload && cleanString(payload.viewer_report));
}

export function mountDocsViewerPublicDocumentExtras(context) {
  var settings = context || {};
  var payload = settings.payload || {};
  if (!payloadHasReport(payload)) return Promise.resolve(false);

  return mountDocsViewerPublicReport({
    allowManagement: false,
    content: settings.content,
    doc: settings.doc,
    generatedData: settings.generatedData,
    managementContext: false,
    payload: payload,
    reportRegistryUrl: cleanString(settings.routeContext && settings.routeContext.reportRegistryUrl),
    routeContext: settings.routeContext,
    scopeConfigs: settings.scopeConfigState && Array.isArray(settings.scopeConfigState.scopeConfigs)
      ? settings.scopeConfigState.scopeConfigs.slice()
      : [],
    setStatus: settings.setStatus,
    viewerScope: cleanString(settings.viewerScope),
    viewerUrlForScope: settings.viewerUrlForScope
  });
}
