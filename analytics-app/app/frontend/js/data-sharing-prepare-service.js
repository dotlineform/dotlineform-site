import { getAnalyticsText } from "./analytics-config.js";
import {
  DATA_SHARING_ENDPOINTS,
  postJson
} from "./analytics-transport.js";
import {
  buildPreparePackageRequest,
  usesPrepareDocumentSelection
} from "./data-sharing-prepare-workflow.js";

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
    config,
    targetFormat,
    selectedIds: state.selectedIds,
    usesDocumentSelection,
    missingSummaryOnlyAvailable: !state.missingSummaryOnlyWrap.hidden,
    missingSummaryOnly: state.missingSummaryOnly.checked
  });
  if (usesDocumentSelection && !request.select_all && !request.doc_ids.length) {
    return prepareValidationError(
      state,
      "error",
      "data_sharing_prepare.selection_required",
      "Select at least one document."
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
