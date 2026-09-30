import {
  mountDocsViewerPublicReport
} from "../reports/docs-viewer-public-reports.js";

function cleanString(value) {
  return String(value || "").trim();
}

function payloadHasReport(payload) {
  return Boolean(payload && payload.report && cleanString(payload.report.id));
}

export function mountDocsViewerPublicDocumentExtras(context) {
  var settings = context || {};
  var payload = settings.payload || {};
  if (!payloadHasReport(payload)) return Promise.resolve(false);

  return mountDocsViewerPublicReport({
    appContext: settings.appContext,
    content: settings.content,
    doc: settings.doc,
    mediaRoot: settings.mediaRoot,
    viewerBaseUrl: settings.viewerBaseUrl,
    collectionProvider: settings.collectionProvider,
    managementContext: false,
    managementService: null,
    payload: payload,
    selectedUrl: settings.workspaceConfigState.activeConfig.selectedUrl,
    mountThemedDiagrams: settings.mountThemedDiagrams,
    openMediaPresentation: settings.openMediaPresentation,
    openMediaTarget: settings.openMediaTarget,
    loadMediaTarget: settings.loadMediaTarget,
    onCollectionDocumentState: settings.onCollectionDocumentState,
    reportRegistryUrl: cleanString(settings.routeContext && settings.routeContext.reportRegistryUrl),
    routeContext: settings.routeContext,
    setStatus: settings.setStatus,
    viewerUrlForDocument: settings.viewerUrlForDocument
  });
}
