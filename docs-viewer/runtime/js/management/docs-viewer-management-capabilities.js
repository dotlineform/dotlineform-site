import {
  DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE,
  readManagementCapabilities
} from "./docs-viewer-management-client.js";
import {
  normalizeManagedDocumentCollectionTarget
} from "./docs-viewer-management-document-target.js";

function normalizeScopeId(scope) {
  return String(scope || "").trim();
}

function scopeLifecycleCapabilities(capabilities) {
  return capabilities && capabilities.scope_lifecycle && typeof capabilities.scope_lifecycle === "object"
    ? capabilities.scope_lifecycle
    : null;
}

export function documentPackagePrepareCapability(capabilities) {
  var documentPackages = capabilities && capabilities.document_packages;
  if (!documentPackages || typeof documentPackages !== "object") {
    return {
      available: false,
      reason: "Prepare package capability is unavailable."
    };
  }
  if (documentPackages.available !== true) {
    return {
      available: false,
      reason: String(documentPackages.message || "The document-package workspace is unavailable.").trim()
    };
  }
  if (documentPackages.prepare !== true) {
    return {
      available: false,
      reason: "Prepare package capability is unavailable."
    };
  }
  return { available: true, reason: "" };
}

export function scopeManagementCapabilities(capabilities, scope) {
  var scopeId = normalizeScopeId(scope);
  if (!capabilities || !capabilities.scopes || !scopeId) return null;
  return capabilities.scopes[scopeId] || null;
}

export function scopeCreateSupported(capabilities) {
  var lifecycle = scopeLifecycleCapabilities(capabilities);
  return Boolean(lifecycle && lifecycle.create_preview && lifecycle.create_apply);
}

export function scopeDeleteSupported(capabilities) {
  var lifecycle = scopeLifecycleCapabilities(capabilities);
  return Boolean(lifecycle && lifecycle.delete_preview && lifecycle.delete_apply);
}

export function scopeDeleteNavigationTarget(payload, activeScope) {
  if (!payload || payload.action !== "delete_scope") return "";
  if (normalizeScopeId(payload.scope_id) !== normalizeScopeId(activeScope)) return "";
  return normalizeScopeId(payload.fallback_scope_id);
}

export function scopeRenameSupported(capabilities) {
  var lifecycle = scopeLifecycleCapabilities(capabilities);
  return Boolean(lifecycle && lifecycle.rename_preview && lifecycle.rename_apply);
}

export function subScopeCreateSupported(capabilities, scope) {
  var lifecycle = scopeLifecycleCapabilities(capabilities);
  var scopeCaps = scopeManagementCapabilities(capabilities, scope);
  var subScopeLifecycle = scopeCaps && scopeCaps.sub_scope_lifecycle && typeof scopeCaps.sub_scope_lifecycle === "object"
    ? scopeCaps.sub_scope_lifecycle
    : null;
  return Boolean(
    lifecycle &&
    lifecycle.sub_scope_create_preview &&
    lifecycle.sub_scope_create_apply &&
    scopeCaps &&
    scopeCaps.available &&
    subScopeLifecycle &&
    subScopeLifecycle.create_eligible
  );
}

export function subScopeDeleteSupported(capabilities, scope) {
  var lifecycle = scopeLifecycleCapabilities(capabilities);
  var scopeCaps = scopeManagementCapabilities(capabilities, scope);
  return Boolean(
    lifecycle &&
    lifecycle.sub_scope_delete_preview &&
    lifecycle.sub_scope_delete_apply &&
    scopeCaps &&
    scopeCaps.available
  );
}

export function scopePublishSupported(capabilities, scope) {
  var scopeCaps = scopeManagementCapabilities(capabilities, scope);
  var publishing = capabilities && capabilities.publishing && typeof capabilities.publishing === "object"
    ? capabilities.publishing
    : null;
  var scopePublishing = scopeCaps && scopeCaps.publishing && typeof scopeCaps.publishing === "object"
    ? scopeCaps.publishing
    : null;
  return Boolean(
    publishing &&
    publishing.confirm &&
    publishing.apply &&
    scopeCaps &&
    scopeCaps.available &&
    scopeCaps.publishable &&
    scopePublishing &&
    scopePublishing.confirm &&
    scopePublishing.apply
  );
}

export function scopeStaticHtmlExportCapability(capabilities, scope) {
  var scopeCaps = scopeManagementCapabilities(capabilities, scope);
  var exportCapabilities = capabilities && capabilities.static_html_export && typeof capabilities.static_html_export === "object"
    ? capabilities.static_html_export
    : null;
  var scopeExport = scopeCaps && scopeCaps.static_html_export && typeof scopeCaps.static_html_export === "object"
    ? scopeCaps.static_html_export
    : null;
  if (!exportCapabilities || exportCapabilities.preview !== true || exportCapabilities.apply !== true) {
    return {
      available: false,
      reason: String(exportCapabilities && exportCapabilities.error || "Snapshot Export is unavailable.").trim()
    };
  }
  if (!scopeExport || scopeExport.preview !== true || scopeExport.apply !== true) {
    return {
      available: false,
      reason: String(scopeExport && scopeExport.error || "Snapshot Export is unavailable for this scope.").trim()
    };
  }
  return { available: true, reason: "" };
}

export function documentTransferSupported(capabilities) {
  var documentTransfer = capabilities && capabilities.document_transfer && typeof capabilities.document_transfer === "object"
    ? capabilities.document_transfer
    : null;
  return Boolean(documentTransfer && documentTransfer.preview && documentTransfer.apply);
}

function documentTransferCollectionKey(target) {
  var normalized = normalizeManagedDocumentCollectionTarget(target);
  return normalized.scope + "\u0000" + String(normalized.sub_scope || "");
}

function documentTransferCollectionRecords(capabilities) {
  var scopes = capabilities && capabilities.scopes && typeof capabilities.scopes === "object"
    ? capabilities.scopes
    : {};
  var records = [];
  Object.keys(scopes).sort().forEach(function (scopeId) {
    var scopeCaps = scopes[scopeId] || {};
    var transfer = scopeCaps.document_transfer && typeof scopeCaps.document_transfer === "object"
      ? scopeCaps.document_transfer
      : null;
    var collections = transfer && Array.isArray(transfer.collections)
      ? transfer.collections
      : [];
    collections.forEach(function (record) {
      try {
        var target = normalizeManagedDocumentCollectionTarget(record && record.target);
        records.push({
          target: target,
          label: String(record && record.label || "").trim(),
          copySource: record && record.copy_source === true,
          moveSource: record && record.move_source === true,
          copyTarget: record && record.copy_target === true,
          moveTarget: record && record.move_target === true
        });
      } catch (_error) {
        return;
      }
    });
  });
  return records;
}

export function documentTransferSourceSupported(capabilities, source, mode) {
  var sourceKey;
  try {
    sourceKey = documentTransferCollectionKey(source);
  } catch (_error) {
    return false;
  }
  var normalizedMode = String(mode || "").trim().toLowerCase();
  if (!documentTransferSupported(capabilities)) return false;
  var record = documentTransferCollectionRecords(capabilities).find(function (candidate) {
    return documentTransferCollectionKey(candidate.target) === sourceKey;
  });
  if (!record) return false;
  if (normalizedMode === "copy") return record.copySource;
  if (normalizedMode === "move") return record.moveSource;
  return false;
}

export function documentTransferTargets(capabilities, source, mode) {
  var sourceKey;
  try {
    sourceKey = documentTransferCollectionKey(source);
  } catch (_error) {
    return [];
  }
  var normalizedMode = String(mode || "").trim().toLowerCase();
  return documentTransferCollectionRecords(capabilities).filter(function (record) {
    if (documentTransferCollectionKey(record.target) === sourceKey) return false;
    if (normalizedMode === "copy") return record.copyTarget;
    if (normalizedMode === "move") return record.moveTarget;
    return false;
  }).map(function (record) {
    return {
      target: record.target,
      label: record.label
    };
  });
}

export function scopeLifecycleDeleteTargets(capabilities) {
  var scopes = capabilities && capabilities.scopes && typeof capabilities.scopes === "object"
    ? capabilities.scopes
    : {};
  return Object.keys(scopes).sort().map(function (scopeId) {
    var scopeCaps = scopes[scopeId] || {};
    var lifecycle = scopeCaps.scope_lifecycle || {};
    return {
      scopeId: scopeId,
      root: String(scopeCaps.root || "").trim(),
      deleteEligible: lifecycle.delete_eligible === true
    };
  }).filter(function (record) {
    return record.deleteEligible;
  });
}

export function scopeLifecycleRenameTargets(capabilities) {
  var scopes = capabilities && capabilities.scopes && typeof capabilities.scopes === "object"
    ? capabilities.scopes
    : {};
  return Object.keys(scopes).sort().map(function (scopeId) {
    var scopeCaps = scopes[scopeId] || {};
    var lifecycle = scopeCaps.scope_lifecycle || {};
    return {
      scopeId: scopeId,
      root: String(scopeCaps.root || "").trim(),
      renameEligible: lifecycle.rename_eligible === true
    };
  }).filter(function (record) {
    return record.renameEligible;
  });
}

export function subScopeLifecycleDeleteTargets(capabilities, scope) {
  var scopeCaps = scopeManagementCapabilities(capabilities, scope);
  var lifecycle = scopeCaps && scopeCaps.sub_scope_lifecycle && typeof scopeCaps.sub_scope_lifecycle === "object"
    ? scopeCaps.sub_scope_lifecycle
    : null;
  var records = lifecycle && Array.isArray(lifecycle.sub_scopes) ? lifecycle.sub_scopes : [];
  return records.map(function (record) {
    var subScope = String(record && record.sub_scope || "").trim();
    return {
      parentScope: normalizeScopeId(scope),
      subScope: subScope,
      title: String(record && record.title || "").trim(),
      source: String(record && record.source || "").trim()
    };
  }).filter(function (record) {
    return record.parentScope && record.subScope;
  });
}

export function createDocsViewerManagementCapabilityController(options) {
  var management = options.management || {};
  var routeSession = options.routeSession || {};
  var context = options.context;
  var callbacks = options.callbacks || {};

  function viewerScope() {
    return callbacks.viewerScope ? callbacks.viewerScope() : "";
  }

  function managementClientOptions() {
    return callbacks.managementClientOptions ? callbacks.managementClientOptions() : {};
  }

  function renderManagementUi() {
    if (callbacks.renderManagementUi) callbacks.renderManagementUi();
  }

  function renderSidebar() {
    if (callbacks.renderSidebar) callbacks.renderSidebar();
  }

  function capabilityErrorMessage(error) {
    return error && error.message ? String(error.message) : "";
  }

  function shouldRetryCapabilityError(error) {
    var status = error && typeof error.status === "number" ? error.status : 0;
    if (status >= 400 && status < 500) return false;
    return true;
  }

  function markUnavailable(error) {
    management.managementCapabilities = null;
    management.managementChecked = true;
    management.managementAvailable = false;
    management.managementCapabilityError = capabilityErrorMessage(error);
    renderManagementUi();
  }

  function applyCapabilities(payload) {
    var capabilities = payload && payload.capabilities ? payload.capabilities : null;
    var scopeCaps = scopeManagementCapabilities(capabilities, viewerScope());
    management.managementCapabilities = capabilities;
    management.managementCapabilityError = "";
    management.managementChecked = true;
    management.managementAvailable = Boolean(capabilities && capabilities.docs_management && scopeCaps && scopeCaps.available);
    renderManagementUi();
    renderSidebar();
  }

  function checkManagementCapabilities(attempt, checkId) {
    readManagementCapabilities(managementClientOptions())
      .then(function (payload) {
        if (checkId !== management.managementCapabilityCheckId) return;
        applyCapabilities(payload);
      })
      .catch(function (error) {
        if (checkId !== management.managementCapabilityCheckId) return;
        if (shouldRetryCapabilityError(error) && attempt < context.MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS - 1) {
          window.setTimeout(function () {
            checkManagementCapabilities(attempt + 1, checkId);
          }, context.MANAGEMENT_CAPABILITY_RETRY_DELAY_MS);
          return;
        }
        markUnavailable(error);
      });
  }

  function startCapabilityCheck() {
    management.managementCapabilityCheckId += 1;
    management.managementCapabilityError = "";
    checkManagementCapabilities(0, management.managementCapabilityCheckId);
  }

  function initialize() {
    routeSession.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    renderManagementUi();
    if (!routeSession.managementContext) return;

    if (!context.managementBaseUrl) {
      markUnavailable(new Error(DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE));
      return;
    }

    startCapabilityCheck();
  }

  function refresh() {
    if (!routeSession.managementContext || !context.managementBaseUrl) return;
    startCapabilityCheck();
  }

  return {
    initialize: initialize,
    refresh: refresh
  };
}
