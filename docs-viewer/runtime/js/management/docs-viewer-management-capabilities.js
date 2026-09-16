import {
  DOCS_MANAGEMENT_UNAVAILABLE_MESSAGE,
  readManagementCapabilities
} from "./docs-viewer-management-client.js";

function collectionLifecycleCapabilities(capabilities) {
  return capabilities && capabilities.collection_lifecycle && typeof capabilities.collection_lifecycle === "object"
    ? capabilities.collection_lifecycle
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

/** Read capabilities for one explicit lifecycle stage. */
export function stageManagementCapabilities(capabilities, stage) {
  return capabilities && capabilities.stages && capabilities.stages[stage] || null;
}

export function stagePrePublishSupported(capabilities, stage) {
  var stageCaps = stageManagementCapabilities(capabilities, stage);
  var operation = stageCaps && stageCaps.pre_publish;
  return Boolean(capabilities && capabilities.docs_management && stageCaps && stageCaps.available
    && operation && operation.preview && operation.apply);
}

export function collectionCreateSupported(capabilities, stage) {
  var lifecycle = collectionLifecycleCapabilities(capabilities);
  var stageCaps = stageManagementCapabilities(capabilities, stage);
  var collectionLifecycle = stageCaps && stageCaps.collection_lifecycle && typeof stageCaps.collection_lifecycle === "object"
    ? stageCaps.collection_lifecycle
    : null;
  return Boolean(
    lifecycle &&
    lifecycle.create_preview &&
    lifecycle.create_apply &&
    stageCaps &&
    stageCaps.available &&
    collectionLifecycle &&
    collectionLifecycle.create_eligible
  );
}

export function collectionDeleteSupported(capabilities, stage) {
  var lifecycle = collectionLifecycleCapabilities(capabilities);
  var stageCaps = stageManagementCapabilities(capabilities, stage);
  return Boolean(
    lifecycle &&
    lifecycle.delete_preview &&
    lifecycle.delete_apply &&
    stageCaps &&
    stageCaps.available &&
    stageCaps.collection_lifecycle &&
    stageCaps.collection_lifecycle.delete_eligible
  );
}

export function stagePublishSupported(capabilities, stage) {
  var stageCaps = stageManagementCapabilities(capabilities, stage);
  var publishing = capabilities && capabilities.publishing && typeof capabilities.publishing === "object"
    ? capabilities.publishing
    : null;
  var stagePublishing = stageCaps && stageCaps.publishing && typeof stageCaps.publishing === "object"
    ? stageCaps.publishing
    : null;
  return Boolean(
    publishing &&
    publishing.confirm &&
    publishing.apply &&
    stageCaps &&
    stageCaps.available &&
    stagePublishing &&
    stagePublishing.confirm &&
    stagePublishing.apply
  );
}

export function stageDeployRepoCapability(capabilities, stage) {
  var stageCaps = stageManagementCapabilities(capabilities, stage);
  var service = capabilities && capabilities.deploy_repo && typeof capabilities.deploy_repo === "object"
    ? capabilities.deploy_repo
    : null;
  var stageCapability = stageCaps && stageCaps.deploy_repo && typeof stageCaps.deploy_repo === "object"
    ? stageCaps.deploy_repo
    : null;
  if (!service || service.preview !== true || service.apply !== true) {
    return {
      available: false,
      reason: "Deploy Repo requires a writable local management service."
    };
  }
  if (
    !stageCaps
    || stageCaps.available !== true
    || !stageCapability
    || stageCapability.available !== true
    || stageCapability.preview !== true
    || stageCapability.apply !== true
  ) {
    return {
      available: false,
      reason: String(
        stageCapability && stageCapability.reason
        || "Deploy Repo is unavailable for this stage."
      ).trim()
    };
  }
  return { available: true, reason: "" };
}

export function stagePublishWorkflowSupported(capabilities, stage) {
  return stagePublishSupported(capabilities, stage)
    || stageDeployRepoCapability(capabilities, stage).available;
}

export function stageStaticHtmlExportCapability(capabilities, stage) {
  var stageCaps = stageManagementCapabilities(capabilities, stage);
  if (stage !== undefined && stageCaps && String(stageCaps.stage || "") !== String(stage || "")) stageCaps = null;
  var exportCapabilities = capabilities && capabilities.static_html_export && typeof capabilities.static_html_export === "object"
    ? capabilities.static_html_export
    : null;
  var stageExport = stageCaps && stageCaps.static_html_export && typeof stageCaps.static_html_export === "object"
    ? stageCaps.static_html_export
    : null;
  if (!exportCapabilities || exportCapabilities.preview !== true || exportCapabilities.apply !== true) {
    return {
      available: false,
      reason: String(exportCapabilities && exportCapabilities.error || "Snapshot Export is unavailable.").trim()
    };
  }
  if (!stageExport || stageExport.preview !== true || stageExport.apply !== true) {
    return {
      available: false,
      reason: String(stageExport && stageExport.error || "Snapshot Export is unavailable for this stage.").trim()
    };
  }
  return { available: true, reason: "" };
}

export function collectionLifecycleDeleteTargets(capabilities, stage) {
  var stageCaps = stageManagementCapabilities(capabilities, stage);
  var lifecycle = stageCaps && stageCaps.collection_lifecycle && typeof stageCaps.collection_lifecycle === "object"
    ? stageCaps.collection_lifecycle
    : null;
  var records = lifecycle && Array.isArray(lifecycle.collections) ? lifecycle.collections : [];
  return records.map(function (record) {
    var collection = String(record && record.collection || "").trim();
    return {
      collection: collection,
      title: String(record && record.title || "").trim(),
      source: String(record && record.source || "").trim()
    };
  }).filter(function (record) {
    return Boolean(record.collection);
  });
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
    var stageCaps = stageManagementCapabilities(capabilities, managementClientOptions().stage);
    management.managementCapabilities = capabilities;
    management.managementCapabilityError = "";
    management.managementChecked = true;
    management.managementAvailable = Boolean(capabilities && capabilities.docs_management && stageCaps && stageCaps.available);
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
