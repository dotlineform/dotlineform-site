import {
  createDocsViewerReportService
} from "../reports/docs-viewer-report-service.js";
import {
  mountDocsViewerReport
} from "../reports/docs-viewer-reports.js";
import {
  readManagedSubScopeDocuments
} from "./docs-viewer-management-client.js";
import {
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

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
    subdocTarget: subdocTarget
  };
  if (Number.isInteger(settings.documentMountGeneration)) {
    published.documentMountGeneration = settings.documentMountGeneration;
  }
  settings.publishSubscopeReportState(published);
}

function managementInventory(settings, parent, subScope) {
  var managementService = settings.managementService || null;
  var baseUrl = cleanString(managementService && managementService.baseUrl);
  if (!settings.managementContext || !baseUrl) return Promise.resolve(null);
  return readManagedSubScopeDocuments(parent.scope, subScope, {
    baseUrl: baseUrl
  }).then(function (payload) {
    if (
      !payload
      || cleanString(payload.scope).toLowerCase() !== parent.scope
      || cleanString(payload.sub_scope).toLowerCase() !== subScope
      || !Array.isArray(payload.documents)
    ) {
      throw new Error("Managed sub-scope inventory did not match the mounted report.");
    }
    var scopeConfig = settings.scopeConfigState || {};
    return {
      documents: payload.documents.slice(),
      nonViewableEmoji: cleanString(scopeConfig.docNonViewableEmoji),
      uiStatusByValue: scopeConfig.uiStatusByValue instanceof Map
        ? scopeConfig.uiStatusByValue
        : new Map()
    };
  }).catch(function (error) {
    return {
      documents: [],
      error: error && error.message
        ? error.message
        : "Managed sub-scope inventory could not be loaded.",
      nonViewableEmoji: "",
      uiStatusByValue: new Map()
    };
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
  return managementInventory(settings, parent, subScope).then(function (inventory) {
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
      onSubscopeStateChange: function (state) {
        publishReportState(settings, parent, subScope, state);
      },
      payload: payload,
      reportRegistryUrl: cleanString(routeContext.reportRegistryUrl),
      reportService: reportManagementBaseUrl
        ? createDocsViewerReportService({ baseUrl: reportManagementBaseUrl })
        : null,
      setStatus: settings.setStatus,
      scopeConfigs: scopeConfigs(settings).slice(),
      subscopeManagement: inventory,
      viewerScope: currentViewerScope(settings),
      viewerUrlForScope: settings.viewerUrlForScope
    });
  });
}
