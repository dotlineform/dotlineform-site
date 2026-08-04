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
  openLocalTarget
} from "./docs-viewer-management-client.js";

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

function reportSubScope(payload) {
  if (cleanString(payload && payload.viewer_report) !== "docs_subscope") return "";
  return cleanString(payload && payload.viewer_report_subscope).toLowerCase();
}

function parentTarget(settings) {
  return normalizeManagedDocumentTarget({
    scope: currentViewerScope(settings),
    doc_id: cleanString(settings && settings.doc && settings.doc.doc_id)
  });
}

function publishReportState(settings, parent, subScope, state) {
  if (typeof settings.publishSubscopeReportState !== "function") return;
  var detail = state && typeof state === "object" ? state : {};
  var collectionTarget = normalizeManagedDocumentCollectionTarget({
    scope: parent.scope,
    sub_scope: subScope
  });
  var subdocTarget = detail.target
    ? normalizeManagedDocumentTarget(detail.target)
    : null;
  if (
    subdocTarget
    && (
      subdocTarget.scope !== parent.scope
      || subdocTarget.sub_scope !== subScope
    )
  ) {
    throw new Error("Docs sub-scope report published a target outside its mounted collection.");
  }
  var published = {
    state: cleanString(detail.state) || "inactive",
    reason: cleanString(detail.reason),
    parentTarget: parent,
    collectionTarget: collectionTarget,
    collectionLabel: configuredSubScopeLabel(
      settings,
      parent.scope,
      subScope
    ),
    subdocTarget: subdocTarget,
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
  settings.publishSubscopeReportState(published);
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

function createSubscopeDocumentAction(settings) {
  var actions = settings && settings.managementDocumentActions;
  return actions && typeof actions.createSubscopeDocument === "function"
    ? actions.createSubscopeDocument
    : null;
}

function configuredSubScopeLabel(settings, scope, subScope) {
  var child = configuredSubScope(settings, scope, subScope);
  var normalizedScope = cleanString(scope).toLowerCase();
  var normalizedSubScope = cleanString(subScope).toLowerCase();
  var childTitle = cleanString(child && child.title) || normalizedSubScope;
  return normalizedScope + " / " + childTitle;
}

function configuredSubScope(settings, scope, subScope) {
  var normalizedScope = cleanString(scope).toLowerCase();
  var normalizedSubScope = cleanString(subScope).toLowerCase();
  var parentConfig = scopeConfigs(settings).find(function (config) {
    return cleanString(config && (config.scope_id || config.scopeId)).toLowerCase()
      === normalizedScope;
  });
  var children = parentConfig && Array.isArray(parentConfig.subScopes)
    ? parentConfig.subScopes
    : [];
  var child = children.find(function (record) {
    return cleanString(record && (record.subScope || record.sub_scope)).toLowerCase()
      === normalizedSubScope;
  });
  return child || null;
}

function escapeMarkdownLinkText(value) {
  return String(value == null ? "" : value)
    .replace(/\\/g, "\\\\")
    .replace(/\[/g, "\\[")
    .replace(/\]/g, "\\]");
}

function markdownLinkForSubscopeDocument(settings, parent, subScope, target, documentRecord) {
  var normalized = normalizeManagedDocumentTarget(target);
  if (
    normalized.scope !== parent.scope
    || normalized.sub_scope !== subScope
    || typeof settings.viewerUrlForScope !== "function"
  ) {
    throw new Error("Copy Link target did not match the mounted sub-scope report.");
  }
  var base = settings.viewerUrlForScope(parent.scope, parent.doc_id, { manage: false });
  if (!cleanString(base)) throw new Error("Copy Link viewer URL is unavailable.");
  var url = new URL(base, "http://docs.local");
  url.searchParams.set("subdoc", normalized.doc_id);
  var title = escapeMarkdownLinkText(
    cleanString(documentRecord && documentRecord.title) || normalized.doc_id
  );
  return "[" + title + "](" + url.pathname + url.search + url.hash + ")";
}

function loadSubscopeContribution(settings, parent, subScope, options) {
  var contributionOptions = options || {};
  var subScopeConfig = configuredSubScope(settings, parent.scope, subScope);
  if (!subScopeConfig) {
    return Promise.reject(new Error(
      "Docs sub-scope is not configured: " + parent.scope + "/" + subScope
    ));
  }
  return Promise.all([
    import("./docs-viewer-management-subscope-default-contribution.js"),
    import("./docs-viewer-management-subscope-composition.js"),
    import("./docs-viewer-management-subscope-customisation-registry.js")
  ]).then(function (modules) {
    var defaultContribution = modules[0].createDocsViewerManagementSubscopeDefaultContribution({
      clientOptions: managementClientOptions(settings),
      managementContext: Boolean(settings.managementContext),
      markdownLinkForDocument: function (target, documentRecord) {
        return markdownLinkForSubscopeDocument(
          settings,
          parent,
          subScope,
          target,
          documentRecord
        );
      },
      nonViewableEmoji: contributionOptions.nonViewableEmoji,
      onCreateDocument: contributionOptions.onCreateDocument,
      onLifecycleEvent: contributionOptions.onLifecycleEvent,
      onPreparePackage: contributionOptions.onPreparePackage,
      root: managementModalRoot(settings),
      setStatus: settings.setStatus,
      uiStatusByValue: contributionOptions.uiStatusByValue
    });
    return modules[2].resolveManagementDocsSubscopeCustomisation(
      subScopeConfig.subScopeCustomisation,
      {
        clientOptions: managementClientOptions(settings),
        collection: { scope: parent.scope, sub_scope: subScope },
        openLocalTarget: openLocalTarget,
        setStatus: settings.setStatus
      }
    ).then(function (customisationContribution) {
      return modules[1].composeDocsViewerManagementSubscopeContributions({
        customisationContribution: customisationContribution,
        defaultContribution: defaultContribution
      });
    });
  });
}

function openSubscopeCreate(settings, parent, subScope, request, context) {
  var collection = request && typeof request === "object" ? request : {};
  var keys = Object.keys(collection).sort();
  if (
    keys.length !== 2
    || keys[0] !== "scope"
    || keys[1] !== "sub_scope"
    || cleanString(collection.scope).toLowerCase() !== parent.scope
    || cleanString(collection.sub_scope).toLowerCase() !== subScope
  ) {
    return Promise.reject(new Error(
      "Sub-scope create collection did not match the mounted report."
    ));
  }
  var refreshAndOpenDocument = context
    && typeof context.refreshAndOpenDocument === "function"
    ? context.refreshAndOpenDocument
    : null;
  if (!refreshAndOpenDocument) {
    return Promise.reject(new Error(
      "Sub-scope create report refresh is unavailable."
    ));
  }
  var action = createSubscopeDocumentAction(settings);
  if (!action) {
    return Promise.reject(new Error("Sub-scope document creation is unavailable."));
  }
  return action(
    {
      scope: parent.scope,
      sub_scope: subScope
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

function openSubScopePreparePackage(settings, request, context) {
  var actionContext = context || {};
  return loadPreparePackageWorkflow().then(function (module) {
    return module.openDocumentPackagePrepareWorkflow({
      root: managementModalRoot(settings),
      scope: cleanString(request && request.scope).toLowerCase(),
      subScope: cleanString(request && request.sub_scope).toLowerCase(),
      checkedDocIds: Array.isArray(request && request.doc_ids)
        ? request.doc_ids.slice()
        : [],
      restoreFocus: actionContext.restoreFocus,
      activityContext: {
        page_id: "docs-manage",
        action_id: "prepare-document-package",
        route: "/docs/",
        control_id: "docsViewerSubscopePreparePackageButton",
        control_selector: "#docsViewerSubscopePreparePackageButton",
        correlation_id: "prepare-document-package:" + String(Date.now())
      },
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
    if (typeof settings.publishSubscopeReportState === "function") {
      var inactive = {
        state: "inactive",
        reason: "non-report-document",
        parentTarget: null,
        collectionTarget: null,
        collectionLabel: "",
        subdocTarget: null,
        refreshDocument: null,
        refreshCollection: null
      };
      if (Number.isInteger(settings.documentMountGeneration)) {
        inactive.documentMountGeneration = settings.documentMountGeneration;
      }
      settings.publishSubscopeReportState(inactive);
    }
    return Promise.resolve(false);
  }

  var managementService = settings.managementService || null;
  var reportManagementBaseUrl = cleanString(managementService && managementService.baseUrl);
  var subScope = reportSubScope(payload);
  if (!subScope) {
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

  var parent = parentTarget(settings);
  publishReportState(settings, parent, subScope, {
    state: "loading",
    reason: "report-mount"
  });
  var scopeConfig = settings.scopeConfigState || {};
  var createAction = createSubscopeDocumentAction(settings);
  var contribution = loadSubscopeContribution(settings, parent, subScope, {
    nonViewableEmoji: cleanString(scopeConfig.docNonViewableEmoji),
    onCreateDocument: (
      settings.managementContext
      && reportManagementBaseUrl
      && createAction
    )
      ? function (request, context) {
          return openSubscopeCreate(settings, parent, subScope, request, context);
        }
      : null,
    onLifecycleEvent: function (event) {
      if (event && event.type === "state") {
        publishReportState(settings, parent, subScope, event);
      }
    },
    onPreparePackage: reportManagementBaseUrl
      ? function (request, context) {
          return openSubScopePreparePackage(settings, request, context);
        }
      : null,
    uiStatusByValue: scopeConfig.uiStatusByValue instanceof Map
      ? scopeConfig.uiStatusByValue
      : new Map()
  }).catch(function (error) {
    publishReportState(settings, parent, subScope, {
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
    subscopeReportContributionPromise: contribution,
    viewerScope: currentViewerScope(settings),
    viewerUrlForScope: settings.viewerUrlForScope
  });
}
