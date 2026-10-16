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
    registerRetainedView: settings.registerRetainedView,
    doc: settings.doc,
    mediaRoot: settings.mediaRoot,
    viewerBaseUrl: settings.viewerBaseUrl,
    collectionProvider: settings.collectionProvider,
    openDocument: settings.openDocument,
    managementContext: false,
    managementService: null,
    payload: payload,
    collectionConfig: payload.report.id === "docs_collection"
      ? settings.workspaceConfigState.activeConfig.collectionsById.get(payload.report.collection) : null,
    selectedUrl: settings.workspaceConfigState.activeConfig.selectedUrl,
    mountRelatedLinks: settings.mountRelatedLinks,
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
