import { getAnalyticsText } from "./analytics-config.js";
import {
  DATA_SHARING_ENDPOINTS,
  postJson
} from "./analytics-transport.js";
import {
  buildPreparePackageRequest,
  usesPrepareDocumentSelection,
  usesPrepareRecordSelection
} from "./data-sharing-prepare-workflow.js";
import {
  currentDataSharingPrepareSelectedIds
} from "./data-sharing-prepare-render.js";

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function prepareValidationError(state, stateKey, textKey, fallback) {
  return {
    ok: false,
    kind: "validation",
    statusState: stateKey,
    statusMessage: getAnalyticsText(state.config, textKey, fallback)
  };
}

export function buildDataSharingPrepareSubmission(state, { config, supportedFormats } = {}) {
  const targetFormat = normalizeText(state.targetFormat);
  const formats = Array.isArray(supportedFormats) ? supportedFormats : [];
  const usesDocumentSelection = usesPrepareDocumentSelection(state.prepareCapability);
  const usesRecordSelection = usesPrepareRecordSelection(state.prepareCapability, config);
  if (!formats.includes(targetFormat)) {
    return prepareValidationError(
      state,
      "error",
      "data_sharing_prepare.format_required",
      "Select a supported package format."
    );
  }
  const request = buildPreparePackageRequest({
    dataDomain: state.dataDomain,
    docsScope: state.docsScope,
    config,
    targetFormat,
    selectedIds: usesRecordSelection ? currentDataSharingPrepareSelectedIds(state) : state.selectedIds,
    usesDocumentSelection,
    usesRecordSelection,
    missingSummaryOnlyAvailable: !state.missingSummaryOnlyWrap.hidden,
    missingSummaryOnly: state.missingSummaryOnly.checked
  });
  const selection = request.selection && typeof request.selection === "object" ? request.selection : {};
  if (usesDocumentSelection && !normalizeText(selection.docs_scope)) {
    return prepareValidationError(
      state,
      "error",
      "data_sharing_prepare.docs_scope_required",
      "Select a Docs Viewer scope."
    );
  }
  if (usesDocumentSelection && !selection.select_all && !selection.doc_ids.length) {
    return prepareValidationError(
      state,
      "error",
      "data_sharing_prepare.selection_required",
      "Select at least one record."
    );
  }
  if (!usesDocumentSelection && usesRecordSelection && !selection.select_all && !selection.record_ids.length) {
    return prepareValidationError(
      state,
      "error",
      "data_sharing_prepare.selection_required",
      "Select at least one record."
    );
  }
  return {
    ok: true,
    request
  };
}

export function dataSharingPrepareRunningMessage(state) {
  return getAnalyticsText(
    state.config,
    "data_sharing_prepare.status_running",
    "Running Data Sharing prepare..."
  );
}

export async function submitDataSharingPreparePackage(request) {
  return postJson(DATA_SHARING_ENDPOINTS.prepare, request);
}

export async function saveDataSharingPrepareContext(state, { config, externalContext } = {}) {
  return postJson(DATA_SHARING_ENDPOINTS.context, {
    data_domain: state.dataDomain,
    config_id: config && config.id,
    external_context: externalContext
  });
}

export function dataSharingPrepareSuccessResult(state, payload) {
  return {
    failed: false,
    payload,
    statusState: "success",
    statusMessage: normalizeText(payload && payload.summary_text)
      || getAnalyticsText(state.config, "data_sharing_prepare.status_success", "Package prepared.")
  };
}

export function dataSharingPrepareFailureResult(state, error) {
  const payload = error && error.payload ? error.payload : {};
  return {
    failed: true,
    payload,
    statusState: "error",
    statusMessage: normalizeText(error && error.message)
      || getAnalyticsText(state.config, "data_sharing_prepare.status_failed", "Package preparation failed.")
  };
}

export async function runDataSharingPreparePackage(state, request) {
  try {
    const payload = await submitDataSharingPreparePackage(request);
    return dataSharingPrepareSuccessResult(state, payload);
  } catch (error) {
    return dataSharingPrepareFailureResult(state, error);
  }
}
