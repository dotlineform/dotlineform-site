import {
  getDemoteTagMatches as getRegistryDemoteTagMatches,
  getDemoteValidation as getRegistryDemoteValidation,
  getNewTagValidation as getRegistryNewTagValidation,
  normalize
} from "./tag-registry-domain.js";
import {
  applyTagRegistryCreateProjection,
  applyTagRegistryDeleteProjection,
  applyTagRegistryDemoteProjection,
  applyTagRegistryEditProjection
} from "./tag-registry-state.js";
import {
  closeTagRegistryDeleteModal,
  closeTagRegistryDemoteModal,
  closeTagRegistryEditModal,
  closeTagRegistryNewModal,
  openTagRegistryDeleteModal,
  openTagRegistryDemoteModal,
  openTagRegistryEditModal,
  openTagRegistryNewModal,
  renderTagRegistryDemoteSelectionState,
  renderTagRegistryDemoteTagPopup,
  renderTagRegistryNewTagModalState,
  setTagRegistryDeleteImpactStatus
} from "./tag-registry-modals.js";
import {
  setStatusText
} from "./tag-modal-shell.js";

function callback(options, name, ...args) {
  if (options && typeof options[name] === "function") {
    return options[name](...args);
  }
  return undefined;
}

function text(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  if (!tokens) return fallback;
  return Object.entries(tokens).reduce((value, [token, replacement]) => {
    return value.replace(new RegExp(`\\{${token}\\}`, "g"), () => replacement == null ? "" : String(replacement));
  }, fallback);
}

export function openTagRegistryEditWorkflow(state, tagId, options = {}) {
  const tag = callback(options, "findTagById", tagId);
  if (!tag) return;
  callback(options, "clearImportResult");
  openTagRegistryEditModal(state, tag);
  callback(options, "syncRouteBusyState");
}

export function closeTagRegistryEditWorkflow(state, options = {}) {
  closeTagRegistryEditModal(state);
  callback(options, "syncRouteBusyState");
}

export function setTagRegistryEditStatus(state, kind, message) {
  setStatusText(state.refs.editStatus, kind, message);
}

export function applyTagRegistryEditResult(state, {
  tagId,
  description,
  result
} = {}, options = {}) {
  setTagRegistryEditStatus(state, "success", result && result.message);
  callback(options, "setImportResult", "success", result && result.summary);
  applyTagRegistryEditProjection(state, {
    tagId,
    description,
    response: result && result.response
  });
  callback(options, "renderControls");
  callback(options, "renderList");
  closeTagRegistryEditWorkflow(state, options);
}

export function openTagRegistryNewWorkflow(state, options = {}) {
  callback(options, "clearImportResult");
  openTagRegistryNewModal(state);
  callback(options, "syncRouteBusyState");
}

export function closeTagRegistryNewWorkflow(state, options = {}) {
  closeTagRegistryNewModal(state);
  callback(options, "syncRouteBusyState");
}

export function setTagRegistryNewStatus(state, kind, message) {
  setStatusText(state.refs.newTagStatus, kind, message);
}

export function getTagRegistryNewValidation(state, options = {}) {
  return getRegistryNewTagValidation({
    newTagState: state.newTagState,
    slugInput: state.refs.newTagSlug.value,
    descriptionInput: state.refs.newTagDescription.value,
    tags: state.tags,
    tagSlugRe: options.tagSlugRe,
    studioGroups: options.studioGroups || [],
    text: (key, fallback, tokens) => text(options, key, fallback, tokens)
  });
}

export function updateTagRegistryNewWorkflow(state, options = {}) {
  if (!state.newTagState) return null;
  const slug = normalize(state.refs.newTagSlug.value);
  if (state.refs.newTagSlug.value !== slug) {
    state.refs.newTagSlug.value = slug;
  }
  state.newTagState.slug = slug;
  state.newTagState.description = String(state.refs.newTagDescription.value || "").trim();
  const validation = getTagRegistryNewValidation(state, options);
  renderTagRegistryNewTagModalState(state, validation);
  return validation;
}

export function applyTagRegistryCreatePostResult(state, {
  validation,
  result
} = {}, options = {}) {
  closeTagRegistryNewWorkflow(state, options);
  callback(options, "setImportResult", "success", result && result.summary);
  applyTagRegistryCreateProjection(state, {
    validation,
    response: result && result.response
  });
  callback(options, "renderControls");
  callback(options, "renderList");
}

export function applyTagRegistryCreatePatchResult(state, {
  result,
  patchResult
} = {}, options = {}) {
  if (result && result.switchToPatch) {
    callback(options, "applyPatchFallback");
    callback(options, "renderImportAvailability");
    setTagRegistryNewStatus(state, "error", result.message);
  }
  closeTagRegistryNewWorkflow(state, options);
  callback(options, "setImportResult", patchResult && patchResult.kind, patchResult && patchResult.message);
  callback(options, "openPatchModal", patchResult && patchResult.snippet);
}

export function openTagRegistryDeleteWorkflow(state, tagId, options = {}) {
  callback(options, "clearImportResult");
  const tag = callback(options, "findTagById", tagId);
  if (!tag) {
    callback(options, "setImportResult", "error", text(options, "selected_tag_missing", "Selected tag is no longer available."));
    return;
  }
  openTagRegistryDeleteModal(state, tag);
  callback(options, "syncRouteBusyState");

  if (state.saveMode !== "post") {
    setTagRegistryDeleteStatus(state, "error", text(options, "local_delete_required", "Local server is required for delete."));
    setTagRegistryDeleteImpactStatus(state, "error", text(options, "delete_impact_unavailable_local", "Delete impact: unavailable (local server required)."));
    return;
  }

  callback(options, "refreshDeleteImpactPreview");
}

export function closeTagRegistryDeleteWorkflow(state, options = {}) {
  closeTagRegistryDeleteModal(state);
  callback(options, "syncRouteBusyState");
}

export function setTagRegistryDeleteStatus(state, kind, message) {
  setStatusText(state.refs.deleteStatus, kind, message);
}

export function applyTagRegistryDeleteResult(state, {
  tagId,
  result
} = {}, options = {}) {
  closeTagRegistryDeleteWorkflow(state, options);
  callback(options, "setImportResult", "success", result && result.summary);
  applyTagRegistryDeleteProjection(state, {
    tagId,
    response: result && result.response
  });
  callback(options, "renderControls");
  callback(options, "renderList");
}

export function openTagRegistryDemoteWorkflow(state, tagId, options = {}) {
  callback(options, "clearImportResult");
  const tag = callback(options, "findTagById", tagId);
  if (!tag) {
    callback(options, "setImportResult", "error", text(options, "selected_tag_missing", "Selected tag is no longer available."));
    return;
  }
  const aliasKey = tag.tagId.split(":")[1] || tag.tagId;
  if (state.aliasKeys.has(aliasKey)) {
    callback(
      options,
      "setImportResult",
      "error",
      text(options, "alias_exists_demote_error", "Alias already exists: {alias_key}. Demotion overwrite is not permitted.", { alias_key: aliasKey })
    );
    return;
  }

  openTagRegistryDemoteModal(state, { tag, aliasKey });
  updateTagRegistryDemoteWorkflow(state, options);
  callback(options, "syncRouteBusyState");
}

export function closeTagRegistryDemoteWorkflow(state, options = {}) {
  closeTagRegistryDemoteModal(state);
  callback(options, "syncRouteBusyState");
}

export function setTagRegistryDemoteStatus(state, kind, message) {
  setStatusText(state.refs.demoteStatus, kind, message);
}

export function getTagRegistryDemoteValidation(state, options = {}) {
  return getRegistryDemoteValidation({
    demoteState: state.demoteState,
    tags: state.tags,
    maxAliasTags: options.maxAliasTags,
    text: (key, fallback, tokens) => text(options, key, fallback, tokens)
  });
}

export function updateTagRegistryDemoteWorkflow(state, options = {}) {
  if (!state.demoteState) return null;
  const validation = getTagRegistryDemoteValidation(state, options);
  let statusKind = "";
  let statusMessage = "";
  if (validation.warning) {
    const emptyWarning = text(options, "demote_select_target_warning", "Select at least one target tag.");
    statusKind = validation.warning === emptyWarning ? "" : "error";
    statusMessage = validation.warning;
  }
  const selectedItems = state.demoteState.tags.map((tagId) => {
    const info = callback(options, "findTagById", tagId);
    return {
      tagId,
      group: info && (options.studioGroups || []).includes(info.group) ? info.group : "warning",
      label: info ? info.label : tagId
    };
  });
  renderTagRegistryDemoteSelectionState(state, {
    selectedItems,
    canConfirm: validation.valid,
    statusKind,
    statusMessage
  });
  return validation;
}

export function getTagRegistryDemoteMatches(state, query, options = {}) {
  return getRegistryDemoteTagMatches({
    query,
    demoteState: state.demoteState,
    registryOptions: state.registryOptions,
    cap: options.cap
  });
}

export function renderTagRegistryDemoteWorkflowPopup(state, options = {}) {
  if (!state.demoteState) return;
  const result = getTagRegistryDemoteMatches(state, state.refs.demoteTagSearch.value, options);
  renderTagRegistryDemoteTagPopup(state, result);
}

export function addTagRegistryDemoteTag(state, tagId, options = {}) {
  if (!state.demoteState) return;
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId) return;
  const tag = callback(options, "findTagById", normalizedTagId);
  if (!tag) return;
  if (normalizedTagId === state.demoteState.tagId) {
    setTagRegistryDemoteStatus(state, "error", text(options, "demote_target_includes_self", "Target list must not include the demoted tag."));
    return;
  }
  if (state.demoteState.tags.includes(normalizedTagId)) return;
  if (state.demoteState.tags.length >= options.maxAliasTags) {
    setTagRegistryDemoteStatus(state, "error", text(options, "demote_max_tags_warning", "Select up to {max_tags} tags.", { max_tags: options.maxAliasTags }));
    return;
  }
  const nextGroup = tag.group;
  const groupConflict = state.demoteState.tags.some((item) => {
    const existing = callback(options, "findTagById", item);
    return Boolean(existing && existing.group === nextGroup);
  });
  if (groupConflict) {
    setTagRegistryDemoteStatus(
      state,
      "error",
      text(options, "demote_one_per_group_warning", "Only one target tag per group is allowed ({group}).", { group: nextGroup })
    );
    return;
  }
  state.demoteState.tags.push(normalizedTagId);
}

export function applyTagRegistryDemotePostResult(state, {
  tagId,
  aliasKey,
  result
} = {}, options = {}) {
  closeTagRegistryDemoteWorkflow(state, options);
  callback(options, "setImportResult", "success", result && result.summary);
  applyTagRegistryDemoteProjection(state, {
    tagId,
    aliasKey,
    response: result && result.response
  });
  callback(options, "renderControls");
  callback(options, "renderList");
}

export function applyTagRegistryDemotePatchResult(state, {
  patchResult
} = {}, options = {}) {
  closeTagRegistryDemoteWorkflow(state, options);
  callback(options, "setImportResult", patchResult && patchResult.kind, patchResult && patchResult.message);
  callback(options, "openPatchModal", patchResult && patchResult.snippet);
}
