// Studio-owned tag registry workflow.
import {
  buildManualPatchForCreateTag,
  buildManualPatchForDemote
} from "./tag-registry-save.js";
import {
  previewDeleteImpact,
  previewTagDemote,
  submitCreateTag,
  submitDeleteTag,
  submitTagDemote,
  submitTagEdit
} from "./tag-registry-service.js";
import {
  applyTagRoutePatchFallback
} from "./tag-route-save-session.js";

export function applyTagRegistryPatchFallback(state) {
  applyTagRoutePatchFallback(state);
}

export async function previewTagRegistryDeleteImpact(options) {
  return previewDeleteImpact(options);
}

export async function saveTagRegistryEdit(options) {
  return submitTagEdit(options);
}

export async function createTagRegistryTag(options) {
  const { newTagRow } = options || {};
  return ensurePatchResult(
    await submitCreateTag(options),
    () => buildManualPatchForCreateTag(newTagRow)
  );
}

export async function deleteTagRegistryTag(options) {
  return submitDeleteTag(options);
}

export async function previewTagRegistryDemote(options) {
  return previewTagDemote(options);
}

export async function demoteTagRegistryTag(options) {
  const { tagId, aliasTargets } = options || {};
  return ensurePatchResult(
    await submitTagDemote(options),
    () => buildManualPatchForDemote(tagId, aliasTargets)
  );
}

function ensurePatchResult(result, buildPatchResult) {
  if (!result || result.mode !== "patch" || result.patchResult) return result;
  return {
    ...result,
    patchResult: buildPatchResult()
  };
}
