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
      rebuildPending: changed,
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
