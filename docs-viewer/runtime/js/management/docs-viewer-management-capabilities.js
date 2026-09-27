import {
  DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE,
  readManagementCapabilities
} from "./docs-viewer-management-client.js";

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

/** Read capabilities for the configured authoring workspace. */
export function workspaceManagementCapabilities(capabilities) {
  return capabilities && capabilities.workspace || null;
}

export function publishCapability(capabilities) {
  var publication = capabilities && capabilities.publish;
  if (!capabilities || !capabilities.docs_management || !publication || !publication.available) {
    return { available: false, reason: publication && publication.reason || "Publish is unavailable." };
  }
  return { available: true, reason: "" };
}

export function publishSupported(capabilities) {
  return publishCapability(capabilities).available;
}

export function staticHtmlExportCapability(capabilities) {
  var workspaceCaps = workspaceManagementCapabilities(capabilities);
  var exportCapabilities = capabilities && capabilities.static_html_export && typeof capabilities.static_html_export === "object"
    ? capabilities.static_html_export
    : null;
  var workspaceExport = workspaceCaps && workspaceCaps.static_html_export && typeof workspaceCaps.static_html_export === "object"
    ? workspaceCaps.static_html_export
    : null;
  if (!exportCapabilities || exportCapabilities.preview !== true || exportCapabilities.apply !== true) {
    return {
      available: false,
      reason: String(exportCapabilities && exportCapabilities.error || "Snapshot Export is unavailable.").trim()
    };
  }
  if (!workspaceExport || workspaceExport.preview !== true || workspaceExport.apply !== true) {
    return {
      available: false,
      reason: String(workspaceExport && workspaceExport.error || "Snapshot Export is unavailable in this workspace.").trim()
    };
  }
  return { available: true, reason: "" };
}

export function createDocsViewerManagementCapabilityController(options) {
  var management = options.management || {};
  var routeSession = options.routeSession || {};
  var context = options.context;
  var callbacks = options.callbacks || {};

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
    var workspaceCaps = workspaceManagementCapabilities(capabilities);
    management.managementCapabilities = capabilities;
    management.managementCapabilityError = "";
    management.managementChecked = true;
    management.managementAvailable = Boolean(capabilities && capabilities.docs_management && workspaceCaps && workspaceCaps.available);
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
