import {
  buildManualPatchForAliasCreate,
  buildManualPatchForAliasDelete,
  buildManualPatchForAliasEdit,
  buildManualPatchForAliasPromote,
  buildManualPatchForDemote,
  buildManualPatchForNewAliases,
  readImportAliasesFromFile
} from "./tag-aliases-save.js";
import {
  previewAliasPromote,
  previewTagDemoteFromAliases,
  submitAliasDelete,
  submitAliasEdit,
  submitAliasPromote,
  submitAliasesImport,
  submitTagDemoteFromAliases
} from "./tag-aliases-service.js";
import {
  applyTagRoutePatchFallback
} from "./tag-route-save-session.js";

export function applyTagAliasesPatchFallback(state) {
  applyTagRoutePatchFallback(state, { syncImportAvailable: true });
}

export async function importTagAliases(options) {
  const { patchContext, importAliases } = options || {};
  return ensurePatchResult(
    await submitAliasesImport({
      ...options,
      state: patchContext
    }),
    () => buildManualPatchForNewAliases(patchContext, importAliases)
  );
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
  const { canonicalTagId, aliasTargets } = options || {};
  return ensurePatchResult(
    await submitTagDemoteFromAliases(options),
    () => buildManualPatchForDemote(canonicalTagId, aliasTargets)
  );
}

export async function readTagAliasesImportFromFile(file) {
  return readImportAliasesFromFile(file);
}

function ensurePatchResult(result, buildPatchResult) {
  if (!result || result.mode !== "patch" || result.patchResult) return result;
  return {
    ...result,
    patchResult: buildPatchResult()
  };
}
