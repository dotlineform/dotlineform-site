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
  createDocsViewerManagementSubscopeContribution
} from "./docs-viewer-management-subscope-contribution.js";

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
    subdocTarget: subdocTarget
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

function openSubscopeImportAction(settings) {
  var actions = settings && settings.managementDocumentActions;
  return actions && typeof actions.openSubscopeImport === "function"
    ? actions.openSubscopeImport
    : null;
}

function configuredSubScopeLabel(settings, scope, subScope) {
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
  var childTitle = cleanString(child && child.title) || normalizedSubScope;
  return normalizedScope + " / " + childTitle;
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

function openSubscopeImport(settings, parent, subScope, request, context) {
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
      "Sub-scope Import collection did not match the mounted report."
    ));
  }
  var actionContext = context || {};
  var refreshAndOpenDocument = typeof actionContext.refreshAndOpenDocument === "function"
    ? actionContext.refreshAndOpenDocument
    : null;
  var refreshCollection = typeof actionContext.refreshCollection === "function"
    ? actionContext.refreshCollection
    : null;
  if (!refreshAndOpenDocument || !refreshCollection) {
    return Promise.reject(new Error(
      "Sub-scope Import report refresh is unavailable."
    ));
  }
  var action = openSubscopeImportAction(settings);
  if (!action) {
    return Promise.reject(new Error("Sub-scope document Import is unavailable."));
  }
  return action(
    {
      scope: parent.scope,
      sub_scope: subScope
    },
    {
      destinationLabel: configuredSubScopeLabel(
        settings,
        parent.scope,
        subScope
      ),
      restoreFocus: actionContext.restoreFocus,
      onComplete: function (detail) {
        if (detail && detail.result && detail.result.collection === true) {
          var collectionTarget = normalizeManagedDocumentCollectionTarget(
            detail.target
          );
          if (
            collectionTarget.scope !== parent.scope
            || collectionTarget.sub_scope !== subScope
          ) {
            throw new Error(
              "Imported package target did not match the mounted sub-scope report."
            );
          }
          return refreshCollection(collectionTarget);
        }
        var target = normalizeManagedDocumentTarget(detail && detail.target);
        if (
          target.scope !== parent.scope
          || target.sub_scope !== subScope
        ) {
          throw new Error(
            "Imported document target did not match the mounted sub-scope report."
          );
        }
        return refreshAndOpenDocument(target);
      }
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
        subdocTarget: null
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
  var importAction = openSubscopeImportAction(settings);
  var contribution = createDocsViewerManagementSubscopeContribution({
    clientOptions: managementClientOptions(settings),
    managementContext: Boolean(settings.managementContext),
    nonViewableEmoji: cleanString(scopeConfig.docNonViewableEmoji),
    onCreateDocument: (
      settings.managementContext
      && reportManagementBaseUrl
      && createAction
    )
      ? function (request, context) {
          return openSubscopeCreate(
            settings,
            parent,
            subScope,
            request,
            context
          );
        }
      : null,
    onLifecycleEvent: function (event) {
      if (event && event.type === "state") {
        publishReportState(settings, parent, subScope, event);
      }
    },
    onImportDocument: (
      settings.managementContext
      && reportManagementBaseUrl
      && importAction
    )
      ? function (request, context) {
          return openSubscopeImport(
            settings,
            parent,
            subScope,
            request,
            context
          );
        }
      : null,
    onPreparePackage: reportManagementBaseUrl
      ? function (request, context) {
          return openSubScopePreparePackage(settings, request, context);
        }
      : null,
    root: managementModalRoot(settings),
    setStatus: settings.setStatus,
    uiStatusByValue: scopeConfig.uiStatusByValue instanceof Map
      ? scopeConfig.uiStatusByValue
      : new Map()
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
    subscopeReportContribution: contribution,
    viewerScope: currentViewerScope(settings),
    viewerUrlForScope: settings.viewerUrlForScope
  });
}
