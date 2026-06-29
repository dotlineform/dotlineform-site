import {
  DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE,
  readManagementCapabilities,
  scopeSupportsGeneratedDataReads
} from "./docs-viewer-management-client.js";

function normalizeScopeId(scope) {
  return String(scope || "").trim();
}

function scopeLifecycleCapabilities(capabilities) {
  return capabilities && capabilities.scope_lifecycle && typeof capabilities.scope_lifecycle === "object"
    ? capabilities.scope_lifecycle
    : null;
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

export function scopeStaticHtmlExportSupported(capabilities, scope) {
  var scopeCaps = scopeManagementCapabilities(capabilities, scope);
  var exportCapabilities = capabilities && capabilities.static_html_export && typeof capabilities.static_html_export === "object"
    ? capabilities.static_html_export
    : null;
  var scopeExport = scopeCaps && scopeCaps.static_html_export && typeof scopeCaps.static_html_export === "object"
    ? scopeCaps.static_html_export
    : null;
  return Boolean(
    exportCapabilities &&
    exportCapabilities.apply &&
    scopeCaps &&
    scopeCaps.available &&
    scopeExport &&
    scopeExport.apply
  );
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
  var state = options.state;
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
    state.managementCapabilities = null;
    state.managementChecked = true;
    state.managementAvailable = false;
    state.managementCapabilityError = capabilityErrorMessage(error);
    renderManagementUi();
  }

  function applyCapabilities(payload) {
    var capabilities = payload && payload.capabilities ? payload.capabilities : null;
    var scopeCaps = scopeManagementCapabilities(capabilities, viewerScope());
    state.managementCapabilities = capabilities;
    state.managementCapabilityError = "";
    state.generatedDataReadAvailable = scopeSupportsGeneratedDataReads(capabilities, viewerScope());
    state.generatedDataReadChecked = true;
    state.managementChecked = true;
    state.managementAvailable = Boolean(capabilities && capabilities.docs_management && scopeCaps && scopeCaps.available);
    renderManagementUi();
    renderSidebar();
  }

  function checkManagementCapabilities(attempt, checkId) {
    readManagementCapabilities(managementClientOptions())
      .then(function (payload) {
        if (checkId !== state.managementCapabilityCheckId) return;
        applyCapabilities(payload);
      })
      .catch(function (error) {
        if (checkId !== state.managementCapabilityCheckId) return;
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
    state.managementCapabilityCheckId += 1;
    state.managementCapabilityError = "";
    checkManagementCapabilities(0, state.managementCapabilityCheckId);
  }

  function initialize() {
    state.managementContext = typeof context.isManagementContext === "function" && context.isManagementContext();
    renderManagementUi();
    if (!state.managementContext) return;

    if (!context.managementBaseUrl) {
      markUnavailable(new Error(DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE));
      return;
    }

    startCapabilityCheck();
  }

  function refresh() {
    if (!state.managementContext || !context.managementBaseUrl) return;
    startCapabilityCheck();
  }

  return {
    initialize: initialize,
    refresh: refresh
  };
}
