import {
  createDocsViewerReportService
} from "../reports/docs-viewer-report-service.js";
import {
  mountDocsViewerReport
} from "../reports/docs-viewer-reports.js";
import {
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";
import {
  assignManagedDocFieldGroup,
  openLocalTarget,
  readManagedDocMetadata
} from "./docs-viewer-management-client.js";
import {
  hasDocsViewerAssignableFieldGroup
} from "../shared/docs-viewer-config-controller.js";

/** Adapt the Working manifest's declared authoring field to public-safe browsing input. */
function catalogueWorkIdForDocument(record) {
  var docId = cleanString(record && record.doc_id);
  if (!/^[0-9]{5}$/.test(docId) || Object.prototype.hasOwnProperty.call(record, "work_id")) {
    throw new Error("Catalogue list document requires one exact Work ID as doc_id.");
  }
  return docId;
}

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

function createCollectionDocumentAction(settings) {
  var actions = settings && settings.managementDocumentActions;
  return actions && typeof actions.createCollectionDocument === "function"
    ? actions.createCollectionDocument
    : null;
}

function configuredCollection(settings,  collection) {
  var normalizedCollection = cleanString(collection).toLowerCase();
  var parentConfig = settings.workspaceConfigState.activeConfig;
  var children = parentConfig && Array.isArray(parentConfig.collections)
    ? parentConfig.collections
    : [];
  var child = children.find(function (record) {
    return cleanString(record && record.collection).toLowerCase()
      === normalizedCollection;
  });
  return child || null;
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
  var base = settings.viewerUrlForDocument(parent.doc_id, { manage: false });
  if (!cleanString(base)) throw new Error("Copy Link viewer URL is unavailable.");
  var url = new URL(base, "http://docs.local");
  url.searchParams.set("subdoc", normalized.doc_id);
  var title = escapeMarkdownLinkText(
    cleanString(documentRecord && documentRecord.title) || normalized.doc_id
  );
  return "[" + title + "](" + url.pathname + url.search + url.hash + ")";
}

export function loadDocsViewerCollectionContribution(settings, parent, collection, options) {
  var contributionOptions = options || {};
  var clientOptions = managementClientOptions(settings);
  var collectionConfig = configuredCollection(settings,  collection);
  if (!collectionConfig) {
    return Promise.reject(new Error(
      "Docs collection is not configured: " + collection
    ));
  }
  var descriptor = collectionConfig.collectionCustomisation;
  var workingCustomisationAvailable = settings.managementContext
    && hasDocsViewerAssignableFieldGroup(descriptor, "authoring_subject");
  var mutationAvailable = Boolean(
    workingCustomisationAvailable
    && settings.managementContext
    && cleanString(clientOptions.baseUrl)
  );
  return Promise.all([
    import("./docs-viewer-management-collection-default-contribution.js"),
    import("./docs-viewer-management-collection-composition.js"),
    import("./docs-viewer-management-collection-customisation-registry.js")
  ]).then(function (modules) {
    var defaultContribution = modules[0].createDocsViewerManagementCollectionDefaultContribution({
      clientOptions: clientOptions,
      managementContext: Boolean(settings.managementContext),
      markdownLinkForDocument: function (target, documentRecord) {
        return markdownLinkForCollectionDocument(
          settings,
          parent,
          collection,
          target,
          documentRecord
        );
      },
      onCreateDocument: contributionOptions.onCreateDocument,
      allowDelete: collection !== "catalogue",
      onRegenerateCatalogue: settings.managementContext
        && collection === "catalogue" && cleanString(clientOptions.baseUrl)
        ? settings.managementDocumentActions?.regenerateCatalogue
        : null,
      onToggleDraft: settings.managementContext
        && cleanString(clientOptions.baseUrl)
        ? settings.managementDocumentActions?.toggleCollectionDocumentDraft
        : null,
      onPreparePackage: contributionOptions.onPreparePackage,
      root: managementModalRoot(settings),
      setStatus: settings.setStatus
    });
    if (!workingCustomisationAvailable) {
      return modules[1].composeDocsViewerManagementCollectionContributions({
        defaultContribution: defaultContribution
      });
    }
    return modules[2].resolveManagementDocsCollectionCustomisation(
      collectionConfig.collectionCustomisation,
      {
        assignFieldGroup: mutationAvailable
          ? function (target, payload) {
              return assignManagedDocFieldGroup(target, payload, clientOptions);
            }
          : null,
        clientOptions: clientOptions,
        catalogueProvider: settings.collectionProvider,
        collection: {  collection: collection },
        content: settings.content,
        documentTarget: {  collection: "", docId: parent.doc_id },
        openMediaTarget: settings.openMediaTarget,
        openLocalTarget: openLocalTarget,
        publicPreviewBase: cleanString(settings.routeContext && settings.routeContext.publicPreviewBase),
        studioBaseUrl: cleanString(settings.routeContext && settings.routeContext.studioBaseUrl),
        workspaceConfig: settings.workspaceConfigState.activeConfig,
        readMetadata: mutationAvailable
          ? function (target) {
              return readManagedDocMetadata(target, clientOptions);
            }
          : null,
        root: managementModalRoot(settings),
        setStatus: settings.setStatus
      }
    ).then(function (customisationContribution) {
      return modules[1].composeDocsViewerManagementCollectionContributions({
        customisationContribution: customisationContribution,
        defaultContribution: defaultContribution
      });
    });
  });
}

function openCollectionCreate(settings, parent, collectionId, request, context) {
  var target = request && typeof request === "object" ? request : {};
  var keys = Object.keys(target).sort();
  if (
    keys.length !== 1
    || keys[0] !== "collection"
    || cleanString(target.collection).toLowerCase() !== collectionId
  ) {
    return Promise.reject(new Error(
      "Collection create target did not match the mounted report."
    ));
  }
  var refreshAndOpenDocument = context
    && typeof context.refreshAndOpenDocument === "function"
    ? context.refreshAndOpenDocument
    : null;
  if (!refreshAndOpenDocument) {
    return Promise.reject(new Error(
      "Collection create report refresh is unavailable."
    ));
  }
  var action = createCollectionDocumentAction(settings);
  if (!action) {
    return Promise.reject(new Error("Collection document creation is unavailable."));
  }
  return action(
    {
      collection: collectionId
    },
    {
      refreshAndSelect: refreshAndOpenDocument
    }
  );
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
  return loadPreparePackageWorkflow().then(function (module) {
    return module.openDocumentPackagePrepareWorkflow({
      root: managementModalRoot(settings),
      collection: cleanString(request && request.collection).toLowerCase(),
      checkedDocIds: Array.isArray(request && request.doc_ids)
        ? request.doc_ids.slice()
        : [],
      restoreFocus: actionContext.restoreFocus,
      callbacks: {
        setMessage: settings.setStatus
      }
    });
  });
}

export function mountDocsViewerManageDocumentExtras(context) {
  var settings = context || {};
  var payload = settings.payload || {};
  var routeContext = settings.routeContext || {};
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
      doc: settings.doc,
      mediaRoot: settings.mediaRoot,
      viewerBaseUrl: settings.viewerBaseUrl,
      documentMountGeneration: settings.documentMountGeneration,
      managementContext: Boolean(settings.managementContext),
      managementService: managementService,
      payload: payload,
      mountThemedDiagrams: settings.mountThemedDiagrams,
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
      viewerUrlForDocument: settings.viewerUrlForDocument
    });
  }

  var parent = parentTarget(settings);
  var createAction = createCollectionDocumentAction(settings);
  var contribution = loadDocsViewerCollectionContribution(settings, parent, collection, {
    onCreateDocument: (
      settings.managementContext
      && collection !== "catalogue"
      && reportManagementBaseUrl
      && createAction
    )
      ? function (request, context) {
          return openCollectionCreate(settings, parent, collection, request, context);
        }
      : null,
    onPreparePackage: settings.managementContext && reportManagementBaseUrl
      ? function (request, context) {
          return openCollectionPreparePackage(settings, request, context);
        }
      : null
  });
  return mountDocsViewerReport({
    appContext: settings.appContext,
    workspaceConfig: settings.workspaceConfigState.activeConfig,
    checkGeneratedDataReadCapability: settings.checkGeneratedDataReadCapability,
    content: settings.content,
    doc: settings.doc,
    mediaRoot: settings.mediaRoot,
    viewerBaseUrl: settings.viewerBaseUrl,
    documentMountGeneration: settings.documentMountGeneration,
    managementContext: Boolean(settings.managementContext),
    managementService: managementService,
    payload: payload,
    mountThemedDiagrams: settings.mountThemedDiagrams,
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
    collectionProvider: settings.collectionProvider,
    routeContext: routeContext,
    catalogueWorkIdForDocument: collection === "catalogue" && settings.managementContext
      ? catalogueWorkIdForDocument : undefined,
    viewerUrlForDocument: settings.viewerUrlForDocument
  });
}
