import {
  createDocsViewerReportService
} from "../reports/docs-viewer-report-service.js";
import {
  mountDocsViewerReport
} from "../reports/docs-viewer-reports.js";
import {
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";
import { DOCS_VIEWER_ACTION_IDS } from "./docs-viewer-action-definitions.js";
import { openCollectionExportWorkflow } from "./docs-viewer-collection-export-workflow.js";

function cleanString(value) {
  return String(value || "").trim();
}

function reportServiceOptions(baseUrl) {
  return {
    baseUrl: baseUrl
  };
}

function payloadHasReport(payload) {
  return Boolean(payload && payload.report && cleanString(payload.report.id));
}

function reportCollection(payload) {
  var report = payload && payload.report;
  if (cleanString(report && report.id) !== "docs_collection") return "";
  return cleanString(report && report.collection).toLowerCase();
}

function parentTarget(settings) {
  return normalizeManagedDocumentTarget({
    doc_id: cleanString(settings && settings.doc && settings.doc.doc_id)
  });
}

function managementClientOptions(settings) {
  var managementService = settings.managementService || null;
  return {
    baseUrl: cleanString(managementService && managementService.baseUrl)
  };
}

function managementModalRoot(settings) {
  var content = settings && settings.content;
  return content && typeof content.closest === "function"
    ? content.closest(".docsViewer")
    : null;
}

function configuredCollection(settings,  collection) {
  return settings.workspaceConfigState.activeConfig.collectionsById.get(collection);
}

function escapeMarkdownLinkText(value) {
  return String(value == null ? "" : value)
    .replace(/\\/g, "\\\\")
    .replace(/\[/g, "\\[")
    .replace(/\]/g, "\\]");
}

function markdownLinkForCollectionDocument(settings, parent, collection, target, documentRecord) {
  var normalized = normalizeManagedDocumentTarget(target);
  if (
    normalized.collection !== collection
    || typeof settings.viewerUrlForDocument !== "function"
  ) {
    throw new Error("Copy Link target did not match the mounted collection report.");
  }
  var base = settings.viewerUrlForDocument(normalized.doc_id, { collection: normalized.collection });
  if (!cleanString(base)) throw new Error("Copy Link viewer URL is unavailable.");
  var url = new URL(base, "http://docs.local");
  var title = escapeMarkdownLinkText(
    cleanString(documentRecord && documentRecord.title) || normalized.doc_id
  );
  return "[" + title + "](" + url.pathname + url.search + url.hash + ")";
}

export function loadDocsViewerCollectionContribution(settings, parent, collectionConfig, options) {
  var contributionOptions = options || {};
  var clientOptions = managementClientOptions(settings);
  if (!collectionConfig) {
    return Promise.reject(new Error("Docs collection is not configured."));
  }
  var collection = collectionConfig.collection;
  return Promise.all([
    import("./docs-viewer-management-collection-default-contribution.js"),
    import("./docs-viewer-management-collection-composition.js")
  ]).then(function (modules) {
    var defaultContribution = modules[0].createDocsViewerManagementCollectionDefaultContribution({
      clientOptions: clientOptions,
      managementContext: Boolean(settings.managementContext),
      paginationToggle: collectionConfig.collectionType === "book-collection",
      markdownLinkForDocument: function (target, documentRecord) {
        return markdownLinkForCollectionDocument(
          settings,
          parent,
          collection,
          target,
          documentRecord
        );
      },
      resolveAction: settings.managementDocumentActions.resolveAction,
      startBusyOperation: settings.managementDocumentActions.startBusyOperation,
      commitDocumentChange: settings.collectionProvider.commitDocumentChange,
      onRegenerateCatalogue: settings.managementContext
        && collection === "catalogue" && cleanString(clientOptions.baseUrl)
        ? settings.managementDocumentActions?.regenerateCatalogue
        : null,
      onPreparePackage: contributionOptions.onPreparePackage,
      onExport: settings.managementContext && clientOptions.baseUrl
        ? function (target, context) {
            return openCollectionExportWorkflow({
              target: target, root: managementModalRoot(settings), restoreFocus: context.restoreFocus,
              clientOptions: clientOptions,
              startBusyOperation: settings.managementDocumentActions.startBusyOperation,
              setStatus: settings.setStatus
            });
          }
        : null,
      root: managementModalRoot(settings),
      setStatus: settings.setStatus
    });
    return modules[1].createDocsViewerManagementCollectionContribution({
      defaultContribution: defaultContribution
    });
  });
}

var preparePackageWorkflowRequest = null;

function loadPreparePackageWorkflow() {
  if (preparePackageWorkflowRequest) return preparePackageWorkflowRequest;
  preparePackageWorkflowRequest = import("../packages/document-package-prepare-workflow.js")
    .then(function (module) {
      if (!module || typeof module.openDocumentPackagePrepareWorkflow !== "function") {
        throw new Error("Prepare package workflow is unavailable.");
      }
      return module;
    })
    .catch(function (error) {
      preparePackageWorkflowRequest = null;
      throw error;
    });
  return preparePackageWorkflowRequest;
}

function openCollectionPreparePackage(settings, request, context) {
  var actionContext = context || {};
  var resolution = settings.managementDocumentActions.resolveAction(DOCS_VIEWER_ACTION_IDS.PREPARE_DOCUMENT_PACKAGE, request);
  if (resolution.disabled) return Promise.reject(new Error(resolution.disabledReason));
  return loadPreparePackageWorkflow().then(function (module) {
    return module.openDocumentPackagePrepareWorkflow({
      root: managementModalRoot(settings),
      collection: cleanString(request && request.collection).toLowerCase(),
      docIds: Array.isArray(request && request.doc_ids)
        ? request.doc_ids.slice()
        : [],
      restoreFocus: actionContext.restoreFocus,
      callbacks: {
        setMessage: settings.setStatus
      }
    });
  });
}

/** Collection documents use the shared reader mount and exact action target. */
function mountCollectionDocumentActions(settings) {
  var target = normalizeManagedDocumentTarget(settings.documentTarget);
  var parent = { doc_id: target.doc_id };
  return loadDocsViewerCollectionContribution(settings, parent, configuredCollection(settings, target.collection)).then(async function (contribution) {
    var metadata = settings.collectionProvider.readMetadata
      ? await settings.collectionProvider.readMetadata(target) : null;
    var record = metadata && metadata.record ? metadata.record : settings.doc;
    var host = settings.content.ownerDocument.createElement("div");
    host.className = "docsViewer__collectionActions";
    function project() {
      var actionContext = Object.assign({}, settings.documentActionContext, { documentRecord: record, actionHost: host });
      settings.onDocumentActionState(actionContext);
      host.replaceChildren();
      if (contribution.renderDetailToolbar) contribution.renderDetailToolbar({
        actionContext: actionContext, collection: { collection: target.collection }, target: target,
        document: record, data: {}, host: host, commitDeletedDocument: settings.commitDeletedDocument,
        refreshAndOpenDocument: settings.openDocument, refreshCollection: actionContext.refreshCollection
      });
    }
    project();
    settings.collectionProvider.subscribeDocumentChanges(function (change) {
      if (!change.deleted && change.target.collection === target.collection && change.target.doc_id === target.doc_id && settings.content.isConnected) {
        record = change.record;
        project();
      }
    });
    return true;
  });
}

export function mountDocsViewerManageDocumentExtras(context) {
  var settings = context || {};
  var payload = settings.payload || {};
  var routeContext = settings.routeContext || {};
  if (settings.documentTarget && settings.documentTarget.collection) {
    return mountCollectionDocumentActions(settings).then(function () {
      if (!payloadHasReport(payload)) return true;
      return mountDocsViewerReport(Object.assign({}, settings, { workspaceConfig: settings.workspaceConfigState.activeConfig, reportRegistryUrl: settings.routeContext.reportRegistryUrl }));
    });
  }
  if (!payloadHasReport(payload)) return Promise.resolve(false);

  var managementService = settings.managementService || null;
  var reportManagementBaseUrl = cleanString(managementService && managementService.baseUrl);
  var collection = reportCollection(payload);
  if (!collection) {
    return mountDocsViewerReport({
      appContext: settings.appContext,
      workspaceConfig: settings.workspaceConfigState.activeConfig,
      checkGeneratedDataReadCapability: settings.checkGeneratedDataReadCapability,
      content: settings.content,
      registerRetainedView: settings.registerRetainedView,
      doc: settings.doc,
      mediaRoot: settings.mediaRoot,
      viewerBaseUrl: settings.viewerBaseUrl,
      documentMountGeneration: settings.documentMountGeneration,
      managementContext: Boolean(settings.managementContext),
      managementService: managementService,
      payload: payload,
      collectionProvider: settings.collectionProvider,
      openDocument: settings.openDocument,
      mountRelatedLinks: settings.mountRelatedLinks,
      reportPresentationAdapter: settings.reportPresentationAdapter,
      openMediaPresentation: settings.openMediaPresentation,
      openMediaTarget: settings.openMediaTarget,
      loadMediaTarget: settings.loadMediaTarget,
      onCollectionDocumentState: settings.onCollectionDocumentState,
      routeContext: routeContext,
      publicPreviewBase: cleanString(routeContext.publicPreviewBase),
      selectedUrl: settings.workspaceConfigState.activeConfig.selectedUrl,
      studioBaseUrl: cleanString(routeContext.studioBaseUrl),
      reportRegistryUrl: cleanString(routeContext.reportRegistryUrl),
      reportService: reportManagementBaseUrl
        ? createDocsViewerReportService(reportServiceOptions(reportManagementBaseUrl))
        : null,
      requestContentDetail: settings.requestContentDetail,
      setStatus: settings.setStatus,
      viewerUrlForDocument: settings.viewerUrlForDocument
    });
  }

  var parent = parentTarget(settings);
  var collectionConfig = configuredCollection(settings, collection);
  var contribution = Promise.all([
    loadDocsViewerCollectionContribution(settings, parent, collectionConfig, {
      onPreparePackage: settings.managementContext && reportManagementBaseUrl
        ? function (request, context) {
            return openCollectionPreparePackage(settings, request, context);
          }
        : null
    }),
    import("./docs-viewer-management-collection-list.js")
  ]).then(function (loaded) {
    loaded[0].createListManagement = loaded[1].createDocsViewerManagementCollectionList;
    return loaded[0];
  });
  return mountDocsViewerReport({
    appContext: settings.appContext,
    workspaceConfig: settings.workspaceConfigState.activeConfig,
    checkGeneratedDataReadCapability: settings.checkGeneratedDataReadCapability,
    content: settings.content,
    registerRetainedView: settings.registerRetainedView,
    doc: settings.doc,
    mediaRoot: settings.mediaRoot,
    viewerBaseUrl: settings.viewerBaseUrl,
    documentMountGeneration: settings.documentMountGeneration,
    managementContext: Boolean(settings.managementContext),
    managementService: managementService,
    payload: payload,
    mountRelatedLinks: settings.mountRelatedLinks,
    reportPresentationAdapter: settings.reportPresentationAdapter,
    openMediaPresentation: settings.openMediaPresentation,
    openMediaTarget: settings.openMediaTarget,
    loadMediaTarget: settings.loadMediaTarget,
    onCollectionDocumentState: settings.onCollectionDocumentState,
    publicPreviewBase: cleanString(routeContext.publicPreviewBase),
    selectedUrl: settings.workspaceConfigState.activeConfig.selectedUrl,
    studioBaseUrl: cleanString(routeContext.studioBaseUrl),
    reportRegistryUrl: cleanString(routeContext.reportRegistryUrl),
    reportService: reportManagementBaseUrl
      ? createDocsViewerReportService(reportServiceOptions(reportManagementBaseUrl))
      : null,
    requestContentDetail: settings.requestContentDetail,
    setStatus: settings.setStatus,
    collectionReportContributionPromise: contribution,
    collectionConfig: collectionConfig,
    collectionProvider: settings.collectionProvider,
    openDocument: settings.openDocument,
    routeContext: routeContext,
    viewerUrlForDocument: settings.viewerUrlForDocument
  });
}
