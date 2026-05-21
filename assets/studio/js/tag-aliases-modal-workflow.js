import {
  findAliasEntry,
  getAliasEditValidation,
  getEditTagMatches,
  isCreateAliasFlow,
  normalize
} from "./tag-aliases-domain.js";
import {
  closeTagAliasesDemoteModal,
  closeTagAliasesEditModal,
  closeTagAliasesPromotionModal,
  openTagAliasesCreateModal,
  openTagAliasesDemoteModal,
  openTagAliasesEditModal,
  openTagAliasesPromotionModal,
  renderTagAliasesDemoteSelectionState,
  renderTagAliasesDemoteTagPopup,
  renderTagAliasesEditTagPopup,
  renderTagAliasesEditModalState,
  setTagAliasesDemoteStatus,
  setTagAliasesEditStatus,
  setTagAliasesPromotionStatus
} from "./tag-aliases-modals.js";

const ALIAS_RE = /^[a-z0-9][a-z0-9-]*$/;
const MAX_ALIAS_TAGS = 4;
const EDIT_TAG_MATCH_CAP = 12;
const DEMOTE_TAG_MATCH_CAP = 12;
const DEFAULT_STUDIO_GROUPS = ["subject", "domain", "form", "theme"];

export function openAliasPromotionModal(state, aliasKey, suggestedGroup, options = {}) {
  openTagAliasesPromotionModal(state, aliasKey, suggestedGroup);
  syncRouteBusyState(options, state);
}

export function closeAliasPromotionModal(state, options = {}) {
  closeTagAliasesPromotionModal(state);
  syncRouteBusyState(options, state);
}

export function setAliasPromotionStatus(state, kind, message) {
  setTagAliasesPromotionStatus(state, kind, message);
}

export function openAliasDemoteModal(state, tagId, options = {}) {
  clearImportResult(options, state);
  const canonicalTagId = normalize(tagId);
  if (!canonicalTagId) return;
  const tagInfo = state.registryById.get(canonicalTagId);
  if (!tagInfo) {
    setImportResult(
      options,
      state,
      "error",
      text(options, "unknown_tag_selected", "Unknown tag selected: {tag_id}", { tag_id: canonicalTagId })
    );
    return;
  }

  openTagAliasesDemoteModal(state, {
    canonicalTagId,
    aliasKey: canonicalTagId.split(":", 2)[1] || canonicalTagId
  });
  syncRouteBusyState(options, state);
}

export function closeAliasDemoteModal(state, options = {}) {
  closeTagAliasesDemoteModal(state);
  syncRouteBusyState(options, state);
}

export function setAliasDemoteStatus(state, kind, message) {
  setTagAliasesDemoteStatus(state, kind, message);
}

export function getAliasDemoteValidation(state, options = {}) {
  if (!state.demoteState) return { valid: false, warning: "", tags: [] };
  const selectedTags = Array.isArray(state.demoteState.tags) ? state.demoteState.tags.slice() : [];
  let warning = "";

  if (!selectedTags.length) {
    warning = text(options, "target_tag_required", "At least one canonical target tag is required.");
  } else if (selectedTags.length > maxAliasTags(options)) {
    warning = text(options, "target_tags_max", "At most {max_tags} target tags are allowed.", { max_tags: maxAliasTags(options) });
  } else {
    const seenGroups = new Set();
    for (const tagId of selectedTags) {
      if (tagId === state.demoteState.tagId) {
        warning = text(options, "demotion_target_self", "Target list must not include the demoted tag.");
        break;
      }
      const info = state.registryById.get(tagId);
      if (!info) {
        warning = text(options, "unknown_tag_selected", "Unknown tag selected: {tag_id}", { tag_id: tagId });
        break;
      }
      if (seenGroups.has(info.group)) {
        warning = text(options, "target_tags_one_per_group", "Only one target tag per group is allowed ({group}).", { group: info.group });
        break;
      }
      seenGroups.add(info.group);
    }
  }

  return {
    valid: !warning,
    warning,
    tags: selectedTags
  };
}

export function updateAliasDemoteUi(state, options = {}) {
  if (!state.demoteState) return;
  const validation = getAliasDemoteValidation(state, options);
  let statusKind = "";
  let statusMessage = "";
  if (validation.warning) {
    const emptyWarning = text(options, "target_tag_required", "At least one canonical target tag is required.");
    statusKind = validation.warning === emptyWarning ? "" : "error";
    statusMessage = validation.warning;
  }
  renderTagAliasesDemoteSelectionState(state, {
    canConfirm: validation.valid,
    statusKind,
    statusMessage
  });
}

export function getAliasDemoteTagMatches(state, query, options = {}) {
  const normalizedQuery = normalize(query);
  if (!normalizedQuery || !state.demoteState) {
    return { matches: [], truncated: false };
  }
  const selected = new Set(state.demoteState.tags || []);
  const allMatches = state.registryOptions.filter((item) => {
    if (selected.has(item.tagId)) return false;
    if (item.tagId === state.demoteState.tagId) return false;
    const slug = item.tagId.split(":", 2)[1] || "";
    return (
      normalize(item.label).startsWith(normalizedQuery) ||
      normalize(slug).startsWith(normalizedQuery)
    );
  });
  const cap = demoteTagMatchCap(options);
  return {
    matches: allMatches.slice(0, cap),
    truncated: allMatches.length > cap
  };
}

export function renderAliasDemoteTagPopup(state, options = {}) {
  if (!state.demoteState) return;
  const result = getAliasDemoteTagMatches(state, state.refs.demoteTagSearch.value, options);
  renderTagAliasesDemoteTagPopup(state, result);
}

export function addAliasDemoteTag(state, tagId, options = {}) {
  if (!state.demoteState) return;
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId || !state.registryById.has(normalizedTagId)) return;
  if (normalizedTagId === state.demoteState.tagId) {
    setAliasDemoteStatus(state, "error", text(options, "demotion_target_self", "Target list must not include the demoted tag."));
    return;
  }
  if (state.demoteState.tags.includes(normalizedTagId)) return;
  if (state.demoteState.tags.length >= maxAliasTags(options)) {
    setAliasDemoteStatus(state, "error", text(options, "target_tags_max", "At most {max_tags} target tags are allowed.", { max_tags: maxAliasTags(options) }));
    return;
  }

  const nextGroup = normalizedTagId.split(":", 1)[0];
  const groupConflict = state.demoteState.tags.some((item) => item.split(":", 1)[0] === nextGroup);
  if (groupConflict) {
    setAliasDemoteStatus(state, "error", text(options, "target_tags_one_per_group", "Only one target tag per group is allowed ({group}).", { group: nextGroup }));
    return;
  }

  state.demoteState.tags.push(normalizedTagId);
}

export function removeAliasDemoteTag(state, tagId) {
  if (!state.demoteState) return;
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId) return;
  state.demoteState.tags = state.demoteState.tags.filter((item) => item !== normalizedTagId);
}

export function findTagAliasEntry(state, aliasKey) {
  return findAliasEntry(state.aliases, aliasKey);
}

export function isAliasCreateFlow(state) {
  return isCreateAliasFlow(state.editState);
}

export function openAliasEditWorkflowModal(state, aliasKey, options = {}) {
  clearImportResult(options, state);
  const entry = findTagAliasEntry(state, aliasKey);
  if (!entry) {
    setImportResult(options, state, "error", text(options, "alias_not_found", "Alias not found: {alias_key}", { alias_key: aliasKey }));
    return;
  }

  openTagAliasesEditModal(state, entry);
  updateAliasEditUi(state, options);
  syncRouteBusyState(options, state);
}

export function openAliasCreateWorkflowModal(state, options = {}) {
  clearImportResult(options, state);
  openTagAliasesCreateModal(state);
  updateAliasEditUi(state, options);
  syncRouteBusyState(options, state);
}

export function closeAliasEditWorkflowModal(state, options = {}) {
  closeTagAliasesEditModal(state);
  syncRouteBusyState(options, state);
}

export function getAliasWorkflowEditValidation(state, options = {}) {
  return getAliasEditValidation({
    editState: state.editState,
    aliasInput: state.refs.editAliasName.value,
    descriptionInput: state.refs.editAliasDescription.value,
    aliases: state.aliases,
    registryById: state.registryById,
    aliasRe: ALIAS_RE,
    maxAliasTags: maxAliasTags(options),
    text: (key, fallback, tokens) => text(options, key, fallback, tokens)
  });
}

export function setAliasEditStatus(state, kind, message) {
  setTagAliasesEditStatus(state, kind, message);
}

export function updateAliasEditUi(state, options = {}) {
  if (!state.editState) return;
  const validation = getAliasWorkflowEditValidation(state, options);
  state.refs.editAliasName.value = normalize(state.refs.editAliasName.value);
  let statusKind = "";
  let statusMessage = "";
  if (validation.tagsWarning) {
    statusKind = "error";
    statusMessage = validation.tagsWarning;
  }
  renderTagAliasesEditModalState(state, {
    warning: validation.warning || "",
    canSave: validation.valid && validation.changed,
    statusKind,
    statusMessage
  });
}

export function getAliasEditTagMatches(state, query, options = {}) {
  return getEditTagMatches({
    query,
    editState: state.editState,
    registryOptions: state.registryOptions,
    cap: editTagMatchCap(options)
  });
}

export function renderAliasEditTagPopup(state, options = {}) {
  if (!state.editState) return;
  const query = state.refs.editTagSearch.value;
  const result = getAliasEditTagMatches(state, query, options);
  renderTagAliasesEditTagPopup(state, result);
}

export function addAliasEditTag(state, tagId, options = {}) {
  if (!state.editState) return;
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId || !state.registryById.has(normalizedTagId)) return;
  if (state.editState.tags.includes(normalizedTagId)) return;
  if (state.editState.tags.length >= maxAliasTags(options)) {
    setAliasEditStatus(state, "error", text(options, "max_tags_warning", "Select up to {max_tags} tags.", { max_tags: maxAliasTags(options) }));
    return;
  }

  const nextGroup = normalizedTagId.split(":", 1)[0];
  const groupConflict = state.editState.tags.some((item) => item.split(":", 1)[0] === nextGroup);
  if (groupConflict) {
    setAliasEditStatus(state, "error", text(options, "one_tag_per_group_warning", "Only one tag per group is allowed ({group}).", { group: nextGroup }));
    return;
  }

  state.editState.tags.push(normalizedTagId);
}

export function removeAliasEditTag(state, tagId) {
  if (!state.editState) return;
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId) return;
  state.editState.tags = state.editState.tags.filter((item) => item !== normalizedTagId);
}

function syncRouteBusyState(options, state) {
  if (typeof options.syncRouteBusyState === "function") options.syncRouteBusyState(state);
}

function setImportResult(options, state, kind, message) {
  if (typeof options.setImportResult === "function") options.setImportResult(state, kind, message);
}

function clearImportResult(options, state) {
  if (typeof options.clearImportResult === "function") options.clearImportResult(state);
}

function text(options, key, fallback, tokens) {
  return typeof options.text === "function" ? options.text(key, fallback, tokens) : fallback;
}

function maxAliasTags(options) {
  const value = Number(options.maxAliasTags);
  return Number.isInteger(value) && value > 0 ? value : MAX_ALIAS_TAGS;
}

function editTagMatchCap(options) {
  const value = Number(options.editTagMatchCap);
  return Number.isInteger(value) && value > 0 ? value : EDIT_TAG_MATCH_CAP;
}

function demoteTagMatchCap(options) {
  const value = Number(options.demoteTagMatchCap);
  return Number.isInteger(value) && value > 0 ? value : DEMOTE_TAG_MATCH_CAP;
}

export function getAliasWorkflowStudioGroups(state) {
  return Array.isArray(state && state.studioGroups) && state.studioGroups.length
    ? state.studioGroups
    : DEFAULT_STUDIO_GROUPS;
}
