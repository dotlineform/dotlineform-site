// Studio-owned tag alias workflow.
import {
  buildManualPatchForAliasCreate,
  buildManualPatchForAliasDelete,
  buildManualPatchForAliasEdit,
  buildManualPatchForAliasPromote
} from "./tag-aliases-save.js";
import {
  previewAliasPromote,
  previewTagDemoteFromAliases,
  submitAliasDelete,
  submitAliasEdit,
  submitAliasPromote,
  submitTagDemoteFromAliases
} from "./tag-aliases-service.js";
import {
  applyTagRoutePatchFallback
} from "./tag-route-save-session.js";

export function applyTagAliasesPatchFallback(state) {
  applyTagRoutePatchFallback(state);
}

export async function deleteTagAlias(options) {
  const { aliasKey } = options || {};
  return ensurePatchResult(
    await submitAliasDelete(options),
    () => buildManualPatchForAliasDelete(aliasKey)
  );
}

export async function saveTagAliasEdit(options) {
  const {
    isCreate,
    originalAlias,
    validation
  } = options || {};
  return ensurePatchResult(
    await submitAliasEdit(options),
    () => isCreate
      ? buildManualPatchForAliasCreate(
          validation.alias,
          validation.description,
          validation.tags
        )
      : buildManualPatchForAliasEdit(
          originalAlias,
          validation.alias,
          validation.description,
          validation.tags
        )
  );
}

export async function previewTagAliasPromote(options) {
  return previewAliasPromote(options);
}

export async function promoteTagAlias(options) {
  const { state, aliasKey, group } = options || {};
  return ensurePatchResult(
    await submitAliasPromote(options),
    () => buildManualPatchForAliasPromote(state, aliasKey, group)
  );
}

export async function previewTagAliasesTagDemote(options) {
  return previewTagDemoteFromAliases(options);
}

export async function demoteTagAliasFromAliases(options) {
  return submitTagDemoteFromAliases(options);
}

function ensurePatchResult(result, buildPatchResult) {
  if (!result || result.mode !== "patch" || result.patchResult) return result;
  return {
    ...result,
    patchResult: buildPatchResult()
  };
}
