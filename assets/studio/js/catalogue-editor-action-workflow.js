import { utcTimestamp } from "./tag-studio-save.js";

export const CATALOGUE_ACTION_OUTCOME = Object.freeze({
  UNCHANGED: "unchanged",
  SAVED: "saved",
  SAVED_UNPUBLISHED: "saved_unpublished",
  SAVED_AND_UPDATED: "saved_and_updated",
  SAVED_UPDATE_FAILED: "saved_update_failed"
});

function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeBuildTargets(value) {
  return Array.isArray(value) ? value : [];
}

function responseStamp(response, build) {
  return normalizeText((build && build.completed_at_utc) || (response && response.saved_at_utc)) || utcTimestamp();
}

function buildSkippedReason(response) {
  const buildSkipped = response && response.build_skipped && typeof response.build_skipped === "object"
    ? response.build_skipped
    : null;
  return normalizeText(buildSkipped && buildSkipped.reason);
}

function normalizePresentationLabel(value) {
  if (value && typeof value === "object") {
    return {
      text: normalizeText(value.text),
      tone: normalizeText(value.tone)
    };
  }
  return {
    text: normalizeText(value),
    tone: ""
  };
}

function presentationLabel(labels, key) {
  return normalizePresentationLabel(labels && labels[key]);
}

export function projectCatalogueActionPresentation({
  resultKey = "",
  statusKey = "",
  resultLabels = {},
  statusLabels = {}
} = {}) {
  const result = presentationLabel(resultLabels, resultKey);
  const status = presentationLabel(statusLabels, statusKey);
  return {
    resultText: result.text,
    resultTone: result.tone,
    statusText: status.text,
    statusTone: status.tone
  };
}

export function resolveCataloguePendingBuildTargets({
  rebuildPending = false,
  pendingTargets = [],
  fallbackTargets = []
} = {}) {
  const normalizedPendingTargets = normalizeBuildTargets(pendingTargets);
  if (rebuildPending && normalizedPendingTargets.length) {
    return normalizedPendingTargets;
  }
  return normalizeBuildTargets(fallbackTargets);
}

export function resolveCatalogueSaveBuildOutcome({
  response,
  isPublished,
  buildTargets = [],
  fallbackBuildTargets = [],
  unpublishedKind = CATALOGUE_ACTION_OUTCOME.SAVED_UNPUBLISHED
} = {}) {
  const build = response && response.build && typeof response.build === "object" ? response.build : null;
  const changed = Boolean(response && response.changed);
  const savedStamp = responseStamp(response, null);
  if (!isPublished) {
    return {
      kind: changed ? unpublishedKind : CATALOGUE_ACTION_OUTCOME.UNCHANGED,
      stamp: savedStamp,
      rebuildPending: false,
      buildTargets: []
    };
  }
  if (!response || !response.build_requested || !build) {
    return {
      kind: changed ? CATALOGUE_ACTION_OUTCOME.SAVED : CATALOGUE_ACTION_OUTCOME.UNCHANGED,
      stamp: savedStamp,
      rebuildPending: changed && buildSkippedReason(response) !== "no_public_build_artifacts",
      buildTargets: normalizeBuildTargets(buildTargets)
    };
  }
  if (build.ok) {
    return {
      kind: CATALOGUE_ACTION_OUTCOME.SAVED_AND_UPDATED,
      stamp: responseStamp(response, build),
      rebuildPending: false,
      buildTargets: []
    };
  }
  return {
    kind: CATALOGUE_ACTION_OUTCOME.SAVED_UPDATE_FAILED,
    stamp: savedStamp,
    error: normalizeText(build.error),
    rebuildPending: true,
    buildTargets: normalizeBuildTargets(build.remaining_targets).length
      ? normalizeBuildTargets(build.remaining_targets)
      : normalizeBuildTargets(fallbackBuildTargets)
  };
}

export function projectCatalogueSaveOutcomePresentation({
  outcome,
  changed = false,
  resultLabels = {},
  statusLabels = {}
} = {}) {
  const kind = normalizeText(outcome && outcome.kind);
  const resultKey = kind === CATALOGUE_ACTION_OUTCOME.SAVED_AND_UPDATED
    ? "savedAndUpdated"
    : kind === CATALOGUE_ACTION_OUTCOME.SAVED_UPDATE_FAILED
      ? "savedUpdateFailed"
      : kind === CATALOGUE_ACTION_OUTCOME.SAVED_UNPUBLISHED
        ? "savedUnpublished"
        : changed || kind === CATALOGUE_ACTION_OUTCOME.SAVED
          ? "saved"
          : "unchanged";
  const statusKey = kind === CATALOGUE_ACTION_OUTCOME.SAVED_AND_UPDATED
    ? "savedAndUpdated"
    : kind === CATALOGUE_ACTION_OUTCOME.SAVED_UPDATE_FAILED
      ? "savedUpdateFailed"
      : "loaded";
  const result = presentationLabel(resultLabels, resultKey);
  const status = presentationLabel(statusLabels, statusKey);
  return projectCatalogueActionPresentation({
    resultKey,
    statusKey,
    resultLabels: { [resultKey]: result },
    statusLabels: { [statusKey]: status }
  });
}

export function extractCatalogueActionPreview(response) {
  return response && response.preview && typeof response.preview === "object" ? response.preview : null;
}

export function getCataloguePreviewBlocker(preview, {
  includeValidationErrors = false,
  fallback = ""
} = {}) {
  const blockers = Array.isArray(preview && preview.blockers) ? preview.blockers : [];
  const validationErrors = includeValidationErrors && Array.isArray(preview && preview.validation_errors)
    ? preview.validation_errors
    : [];
  if ((preview && preview.blocked) || blockers.length || validationErrors.length) {
    return normalizeText(blockers[0] || validationErrors[0] || fallback);
  }
  return "";
}
