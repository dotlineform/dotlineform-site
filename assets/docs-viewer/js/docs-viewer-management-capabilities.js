import {
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

export function scopeArchiveAvailable(capabilities, scope) {
  var scopeCaps = scopeManagementCapabilities(capabilities, scope);
  return Boolean(scopeCaps && scopeCaps.archive_available);
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

  function markUnavailable() {
    state.managementCapabilities = null;
    state.managementChecked = true;
    state.managementAvailable = false;
    renderManagementUi();
  }

  function applyCapabilities(payload) {
    var capabilities = payload && payload.capabilities ? payload.capabilities : null;
    var scopeCaps = scopeManagementCapabilities(capabilities, viewerScope());
    state.managementCapabilities = capabilities;
    state.generatedDataReadAvailable = scopeSupportsGeneratedDataReads(capabilities, viewerScope());
    state.generatedDataReadChecked = true;
    state.managementChecked = true;
    state.managementAvailable = Boolean(scopeCaps && scopeCaps.available);
    renderManagementUi();
    renderSidebar();
  }

  function checkManagementCapabilities(attempt, checkId) {
    readManagementCapabilities(managementClientOptions())
      .then(function (payload) {
        if (checkId !== state.managementCapabilityCheckId) return;
        applyCapabilities(payload);
      })
      .catch(function () {
        if (checkId !== state.managementCapabilityCheckId) return;
        if (attempt < context.MANAGEMENT_CAPABILITY_RETRY_ATTEMPTS - 1) {
          window.setTimeout(function () {
            checkManagementCapabilities(attempt + 1, checkId);
          }, context.MANAGEMENT_CAPABILITY_RETRY_DELAY_MS);
          return;
        }
        markUnavailable();
      });
  }

  function startCapabilityCheck() {
    state.managementCapabilityCheckId += 1;
    checkManagementCapabilities(0, state.managementCapabilityCheckId);
  }

  function initialize() {
    state.managementMode = context.getCurrentMode() === context.MANAGEMENT_MODE;
    renderManagementUi();
    if (!state.managementMode) return;

    if (!context.managementBaseUrl) {
      markUnavailable();
      return;
    }

    startCapabilityCheck();
  }

  function refresh() {
    if (!state.managementMode || !context.managementBaseUrl) return;
    startCapabilityCheck();
  }

  return {
    initialize: initialize,
    refresh: refresh
  };
}
