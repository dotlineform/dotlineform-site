import {
  createDocsViewerReportService
} from "../reports/docs-viewer-report-service.js";
import {
  mountDocsViewerReport
} from "../reports/docs-viewer-reports.js";
import {
  normalizeManagedDocumentCollectionTarget,
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

function cleanString(value) {
  return String(value || "").trim();
}

function reportServiceOptions(baseUrl) {
  return {
    baseUrl: baseUrl
  };
}

function currentViewerStage(context) {
  return cleanString(context && context.viewerStage);
}

function stageConfigs(context) {
  var workspaceConfig = context && context.workspaceConfigState ? context.workspaceConfigState : {};
  return Array.isArray(workspaceConfig.stageConfigs) ? workspaceConfig.stageConfigs : [];
}

function fetchDocsIndexTreeForStage(context, stage) {
  var targetStage = cleanString(stage || currentViewerStage(context));
  return context.collectionProvider.readIndex({
    stage: targetStage
  });
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
    ...(settings.routeContext && settings.routeContext.viewerStage ? { stage: settings.routeContext.viewerStage } : {}),
    doc_id: cleanString(settings && settings.doc && settings.doc.doc_id)
  });
}

function exactSubdocRecord(value, target) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Docs collection report detail record is invalid.");
  }
  if (cleanString(value.doc_id) !== target.doc_id) {
    throw new Error("Docs collection report detail record did not match its target.");
  }
  return Object.freeze(Object.assign({}, value, { doc_id: target.doc_id }));
}

function optionalSubdocInfo(value) {
  if (value == null) return null;
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Docs collection report detail information is invalid.");
  }
  return Object.freeze(Object.assign({}, value));
}

function publishReportState(settings, parent, collection, state) {
  if (typeof settings.publishCollectionReportState !== "function") return;
  var detail = state && typeof state === "object" ? state : {};
  var collectionTarget = normalizeManagedDocumentCollectionTarget({
    ...(parent.stage ? { stage: parent.stage } : {}),
    collection: collection
  });
  var subdocTarget = detail.target
    ? normalizeManagedDocumentTarget(detail.target)
    : null;
  if (
    subdocTarget
    && (
      cleanString(subdocTarget.stage) !== cleanString(parent.stage)
      || subdocTarget.collection !== collection
    )
  ) {
    throw new Error("Docs collection report published a target outside its mounted collection.");
  }
  var detailRecord = subdocTarget
    ? exactSubdocRecord(detail.record, subdocTarget)
    : null;
  var detailInfo = subdocTarget ? optionalSubdocInfo(detail.info) : null;
  var published = {
    state: cleanString(detail.state) || "inactive",
    reason: cleanString(detail.reason),
    parentTarget: parent,
    collectionTarget: collectionTarget,
    collectionLabel: configuredCollectionLabel(
      settings,
      parent.stage,
      collection
    ),
    subdocTarget: subdocTarget,
    subdocRecord: detailRecord,
    subdocInfo: detailInfo,
    refreshDocument: typeof detail.refreshDocument === "function"
      ? detail.refreshDocument
      : null,
    refreshCollection: typeof detail.refreshCollection === "function"
      ? detail.refreshCollection
      : null
  };
  if (Number.isInteger(settings.documentMountGeneration)) {
    published.documentMountGeneration = settings.documentMountGeneration;
  }
  settings.publishCollectionReportState(published);
}

function managementClientOptions(settings) {
  var managementService = settings.managementService || null;
  return {
    baseUrl: cleanString(managementService && managementService.baseUrl),
    stage: cleanString(settings.routeContext && settings.routeContext.viewerStage)
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

function configuredCollectionLabel(settings, stage, collection) {
  var child = configuredCollection(settings, stage, collection);
  var selectedStage = cleanString(stage);
  var normalizedCollection = cleanString(collection).toLowerCase();
  var childTitle = cleanString(child && child.title) || normalizedCollection;
  return selectedStage + " / " + childTitle;
}

function configuredCollection(settings, stage, collection) {
  var selectedStage = cleanString(stage);
  var normalizedCollection = cleanString(collection).toLowerCase();
  var parentConfig = stageConfigs(settings).find(function (config) {
    return cleanString(config && config.stage).toLowerCase()
      === selectedStage;
  });
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
    cleanString(normalized.stage) !== cleanString(parent.stage)
    || normalized.collection !== collection
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
  var collectionConfig = configuredCollection(settings, parent.stage, collection);
  if (!collectionConfig) {
    return Promise.reject(new Error(
      "Docs collection is not configured: " + parent.stage + "/" + collection
    ));
  }
  var descriptor = collectionConfig.collectionCustomisation;
  var workingCustomisationAvailable = parent.stage === "working"
    && hasDocsViewerAssignableFieldGroup(descriptor, "authoring_subject");
  var mutationAvailable = Boolean(
    (!parent.stage || workingCustomisationAvailable)
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
      onToggleDraft: settings.managementContext && parent.stage === "working"
        && cleanString(clientOptions.baseUrl)
        ? settings.managementDocumentActions?.toggleCollectionDocumentDraft
        : null,
      onLifecycleEvent: contributionOptions.onLifecycleEvent,
      onPreparePackage: contributionOptions.onPreparePackage,
      root: managementModalRoot(settings),
      setStatus: settings.setStatus,
      uiStatusByValue: contributionOptions.uiStatusByValue
    });
    if (parent.stage && !workingCustomisationAvailable) {
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
        collection: { ...(parent.stage ? { stage: parent.stage } : {}), collection: collection },
        openLocalTarget: openLocalTarget,
        publicPreviewBase: cleanString(settings.routeContext && settings.routeContext.publicPreviewBase),
        studioBaseUrl: cleanString(settings.routeContext && settings.routeContext.studioBaseUrl),
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
    keys.length !== 2
    || keys[0] !== "collection"
    || keys[1] !== "stage"
    || cleanString(target.collection).toLowerCase() !== collectionId
    || cleanString(target.stage) !== cleanString(parent.stage)
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
      ...(parent.stage ? { stage: parent.stage } : {}),
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
      stage: cleanString(request && request.stage),
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
  if (!payloadHasReport(payload)) {
    if (typeof settings.publishCollectionReportState === "function") {
      var inactive = {
        state: "inactive",
        reason: "non-report-document",
        parentTarget: null,
        collectionTarget: null,
        collectionLabel: "",
        subdocTarget: null,
        subdocRecord: null,
        subdocInfo: null,
        refreshDocument: null,
        refreshCollection: null
      };
      if (Number.isInteger(settings.documentMountGeneration)) {
        inactive.documentMountGeneration = settings.documentMountGeneration;
      }
      settings.publishCollectionReportState(inactive);
    }
    return Promise.resolve(false);
  }

  var managementService = settings.managementService || null;
  var reportManagementBaseUrl = cleanString(managementService && managementService.baseUrl);
  var collection = reportCollection(payload);
  if (!collection) {
    return mountDocsViewerReport({
      appContext: settings.appContext,
      checkGeneratedDataReadCapability: settings.checkGeneratedDataReadCapability,
      content: settings.content,
      doc: settings.doc,
      documentMountGeneration: settings.documentMountGeneration,
      fetchDocsIndexTree: function (stage) {
        return fetchDocsIndexTreeForStage(settings, stage);
      },
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
      studioBaseUrl: cleanString(routeContext.studioBaseUrl),
      reportRegistryUrl: cleanString(routeContext.reportRegistryUrl),
      reportService: reportManagementBaseUrl
        ? createDocsViewerReportService(reportServiceOptions(reportManagementBaseUrl))
        : null,
      requestContentDetail: settings.requestContentDetail,
      setStatus: settings.setStatus,
      stageConfigs: stageConfigs(settings).slice(),
      viewerStage: cleanString(settings.routeContext && settings.routeContext.viewerStage),
      viewerUrlForDocument: settings.viewerUrlForDocument
    });
  }

  var parent = parentTarget(settings);
  publishReportState(settings, parent, collection, {
    state: "loading",
    reason: "report-mount"
  });
  var workspaceConfig = settings.workspaceConfigState || {};
  var createAction = createCollectionDocumentAction(settings);
  var contribution = loadDocsViewerCollectionContribution(settings, parent, collection, {
    onCreateDocument: (
      settings.managementContext
      && (!parent.stage || parent.stage === "working")
      && reportManagementBaseUrl
      && createAction
    )
      ? function (request, context) {
          return openCollectionCreate(settings, parent, collection, request, context);
        }
      : null,
    onLifecycleEvent: function (event) {
      if (event && event.type === "state") {
        publishReportState(settings, parent, collection, event);
      }
    },
    onPreparePackage: !parent.stage && reportManagementBaseUrl
      ? function (request, context) {
          return openCollectionPreparePackage(settings, request, context);
        }
      : null,
    uiStatusByValue: workspaceConfig.uiStatusByValue instanceof Map
      ? workspaceConfig.uiStatusByValue
      : new Map()
  }).catch(function (error) {
    publishReportState(settings, parent, collection, {
      state: "error",
      reason: "customisation-resolution-failed"
    });
    throw error;
  });
  return mountDocsViewerReport({
    appContext: settings.appContext,
    checkGeneratedDataReadCapability: settings.checkGeneratedDataReadCapability,
    content: settings.content,
    doc: settings.doc,
    documentMountGeneration: settings.documentMountGeneration,
    fetchDocsIndexTree: function (stage) {
      return fetchDocsIndexTreeForStage(settings, stage);
    },
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
    studioBaseUrl: cleanString(routeContext.studioBaseUrl),
    reportRegistryUrl: cleanString(routeContext.reportRegistryUrl),
    reportService: reportManagementBaseUrl
      ? createDocsViewerReportService(reportServiceOptions(reportManagementBaseUrl))
      : null,
    requestContentDetail: settings.requestContentDetail,
    setStatus: settings.setStatus,
    stageConfigs: stageConfigs(settings).slice(),
    collectionReportContributionPromise: contribution,
    viewerStage: cleanString(settings.routeContext && settings.routeContext.viewerStage),
    viewerUrlForDocument: settings.viewerUrlForDocument
  });
}
