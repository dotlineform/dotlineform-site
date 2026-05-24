import {
  buildManualPatchForCreateTag,
  buildManualPatchForDemote,
  buildManualPatchForNewTags
} from "./tag-registry-save.js";
import {
  previewDeleteImpact,
  previewTagDemote,
  readImportRegistryFromFile,
  submitCreateTag,
  submitDeleteTag,
  submitRegistryImport,
  submitTagDemote,
  submitTagEdit
} from "./tag-registry-service.js";
import {
  applyTagRoutePatchFallback
} from "./tag-route-save-session.js";

export function applyTagRegistryPatchFallback(state) {
  applyTagRoutePatchFallback(state, { syncImportAvailable: true });
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
    await submitCreateTag({
      ...options,
      importMode: "add"
    }),
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

export async function importTagRegistryTags(options) {
  const { patchContext, importRegistry } = options || {};
  return ensurePatchResult(
    await submitRegistryImport({
      ...options,
      state: patchContext
    }),
    () => buildManualPatchForNewTags(patchContext, importRegistry)
  );
}

export async function readTagRegistryImportFromFile(file, groups) {
  return readImportRegistryFromFile(file, groups);
}

function ensurePatchResult(result, buildPatchResult) {
  if (!result || result.mode !== "patch" || result.patchResult) return result;
  return {
    ...result,
    patchResult: buildPatchResult()
  };
}
