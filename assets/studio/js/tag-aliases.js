import {
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import {
  loadStudioAliasesJson,
  loadStudioGroupsJson,
  loadStudioRegistryJson
} from "./studio-data.js";
import {
  buildGroupDescriptionMap,
  buildRegistryLookup,
  buildRegistryOptions,
  configureTagAliasesDomain,
  findAliasEntry as findNormalizedAliasEntry,
  getAliasEditValidation as getNormalizedAliasEditValidation,
  getEditTagMatches as getNormalizedEditTagMatches,
  isCreateAliasFlow as isCreateNormalizedAliasFlow,
  normalize,
  normalizeAliases,
  normalizeTimestamp
} from "./tag-aliases-domain.js";
import {
  applyTagAliasesDeleteProjection,
  applyTagAliasesDemoteProjection,
  applyTagAliasesEditProjection,
  applyTagAliasesPromoteProjection
} from "./tag-aliases-state.js";
import {
  applyTagAliasesPatchFallback,
  deleteTagAlias,
  demoteTagAliasFromAliases,
  importTagAliases,
  previewTagAliasPromote,
  previewTagAliasesTagDemote,
  promoteTagAlias,
  readTagAliasesImportFromFile,
  saveTagAliasEdit
} from "./tag-aliases-workflow.js";
import {
  openConfirmDetailModal,
  openConfirmModal
} from "./studio-modal.js";
import {
  clearTagAliasesImportResult,
  closeTagAliasesDemoteModal,
  closeTagAliasesEditModal,
  closeTagAliasesPromotionModal,
  collectTagAliasesModalRefs,
  openTagAliasesCreateModal,
  openTagAliasesDemoteModal,
  openTagAliasesEditModal,
  openTagAliasesPromotionModal,
  renderTagAliasesModals,
  renderTagAliasesDemoteSelectionState,
  renderTagAliasesDemoteTagPopup,
  renderTagAliasesEditTagPopup,
  renderTagAliasesEditModalState,
  setTagAliasesDemoteStatus,
  setTagAliasesEditStatus,
  setTagAliasesImportResult,
  setTagAliasesPromotionStatus,
  showTagAliasesPatchModal,
  wireTagAliasesModalEvents
} from "./tag-aliases-modals.js";
import {
  probeTagAliasesImportMode,
  renderTagAliasesImportAvailability,
  syncTagAliasesImportModeFromControl as syncImportModeFromControl
} from "./tag-aliases-import-mode.js";
import {
  renderTagAliasesControls as renderControls,
  renderTagAliasesError as renderError,
  renderTagAliasesList as renderList
} from "./tag-aliases-render.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  bindTagSaveModeReprobe,
  tagRouteServiceState,
  withTagRouteBusy
} from "./tag-route-save-session.js";
import {
  tagAliasesUi
} from "./studio-ui.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const ALIAS_RE = /^[a-z0-9][a-z0-9-]*$/;
const MAX_ALIAS_TAGS = 4;
const EDIT_TAG_MATCH_CAP = 12;
const DEMOTE_TAG_MATCH_CAP = 12;
const UI = tagAliasesUi;
const { className: UI_CLASS, selector: UI_SELECTOR, state: UI_STATE } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagAliasesPage);
} else {
  initTagAliasesPage();
}

function routeStateDetail(state) {
  return {
    route: "tag-aliases",
    mode: state.importModalOpen ? "import" : state.editState || state.promotionState || state.demoteState ? "edit" : "list",
    service: tagRouteServiceState(state),
    recordLoaded: Boolean(state.aliases && state.aliases.length)
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(state.mount, Boolean(state.isBusy), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.mount, ready, routeStateDetail(state));
}

async function withRouteBusy(state, task) {
  return withTagRouteBusy(state, task, { syncRouteBusyState });
}

async function initTagAliasesPage() {
  const mount = document.getElementById("tag-aliases");
  if (!mount) return;
  initializeStudioRouteState(mount, { route: "tag-aliases", mode: "list" });

  let config = null;
  try {
    config = await loadStudioConfigWithText("tag_aliases");
  } catch (error) {
    mount.innerHTML = `<div class="${UI_CLASS.error}">Failed to load tag aliases config.</div>`;
    setStudioRouteReady(mount, true, {
      route: "tag-aliases",
      mode: "empty",
      service: "unavailable",
      recordLoaded: false
    });
    return;
  }
  STUDIO_GROUPS = getStudioGroups(config);
  configureTagAliasesDomain({
    groups: STUDIO_GROUPS,
    maxAliasTags: MAX_ALIAS_TAGS
  });
  const groupInfoPagePath = getStudioRoute(config, "tag_groups");

  const state = {
    mount,
    config,
    aliases: [],
    registryById: new Map(),
    aliasesUpdatedAt: "",
    searchQuery: "",
    filterGroup: "all",
    sortKey: "alias",
    sortDir: "asc",
    studioGroups: STUDIO_GROUPS,
    groupInfoPagePath,
    importMode: "add",
    saveMode: "patch",
    importAvailable: false,
    selectedFile: null,
    importModalOpen: false,
    patchSnippet: "",
    registryOptions: [],
    groupDescriptions: new Map(),
    promotionState: null,
    demoteState: null,
    editState: null,
    refs: null,
    isBusy: false
  };

  renderShell(state);
  wireEvents(state);
  syncImportModeFromControl(state);

  try {
    await loadData(state);
    renderControls(state);
    renderList(state);
    markRouteReady(state, true);
  } catch (error) {
    renderError(
      state,
      aliasesText(state.config, "load_failed_error", "Failed to load aliases from /assets/studio/data/tag_aliases.json.")
    );
    markRouteReady(state, true);
    return;
  }

  bindTagSaveModeReprobe(() => {
    void probeImportMode(state);
  });
  void probeImportMode(state);
}

function renderShell(state) {
  const importButtonLabel = aliasesText(state.config, "import_button", "Import");
  const newAliasButtonLabel = aliasesText(state.config, "new_alias_button", "New alias");
  const searchLabel = aliasesText(state.config, "search_label", "Search aliases");
  const searchPlaceholder = aliasesText(state.config, "search_placeholder", "search");
  const refs = {
    openImportModal: state.mount.querySelector(UI_SELECTOR.openImportModal),
    openNewAlias: state.mount.querySelector(UI_SELECTOR.openNewAlias),
    key: state.mount.querySelector(UI_SELECTOR.key),
    searchLabel: state.mount.querySelector(UI_SELECTOR.searchLabel),
    search: state.mount.querySelector(UI_SELECTOR.search),
    list: state.mount.querySelector(UI_SELECTOR.list),
    modalHost: state.mount.querySelector(UI_SELECTOR.modalHost)
  };

  const missingRef = Object.entries(refs).find(([, value]) => !value);
  if (missingRef) {
    renderError(
      state,
      aliasesText(state.config, "missing_template_shell_error", "Tag Aliases error: missing template shell markup.")
    );
    return;
  }

  refs.openImportModal.textContent = importButtonLabel;
  refs.openNewAlias.textContent = newAliasButtonLabel;
  refs.searchLabel.textContent = searchLabel;
  refs.search.setAttribute("placeholder", searchPlaceholder);
  refs.modalHost.innerHTML = renderTagAliasesModals(state);

  state.refs = {
    ...refs,
    ...collectTagAliasesModalRefs(state.mount)
  };
  renderImportAvailability(state);
}

function wireEvents(state) {
  state.refs.search.addEventListener("input", () => {
    state.searchQuery = normalize(state.refs.search.value);
    renderList(state);
  });

  state.refs.openNewAlias.addEventListener("click", () => {
    openAliasCreateModal(state);
  });

  state.mount.addEventListener("click", (event) => {
    const demoteButton = event.target.closest("button[data-demote-tag-id]");
    if (demoteButton) {
      const tagId = normalize(demoteButton.getAttribute("data-demote-tag-id"));
      if (tagId) openDemoteModal(state, tagId);
      return;
    }

    const promoteButton = event.target.closest("button[data-promote-alias]");
    if (promoteButton) {
      const alias = normalize(promoteButton.getAttribute("data-promote-alias"));
      if (alias) void handleAliasPromote(state, alias);
      return;
    }

    const deleteButton = event.target.closest("button[data-delete-alias]");
    if (deleteButton) {
      const alias = normalize(deleteButton.getAttribute("data-delete-alias"));
      if (alias) void withRouteBusy(state, () => handleAliasDelete(state, alias));
      return;
    }

    const editButton = event.target.closest("button[data-edit-alias]");
    if (editButton) {
      const alias = normalize(editButton.getAttribute("data-edit-alias"));
      if (alias) openAliasEditModal(state, alias);
      return;
    }

    const groupButton = event.target.closest("button[data-group]");
    if (groupButton) {
      const group = normalize(groupButton.getAttribute("data-group"));
      const isAllGroups = !group || group === "all";
      state.filterGroup = isAllGroups ? "all" : group;
      if (isAllGroups) {
        state.searchQuery = "";
        state.refs.search.value = "";
      }
      renderControls(state);
      renderList(state);
      return;
    }

    const sortButton = event.target.closest("button[data-sort-key]");
    if (sortButton) {
      const key = normalize(sortButton.getAttribute("data-sort-key"));
      if (key !== "alias" && key !== "tags") return;
      if (state.sortKey === key) {
        state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = key;
        state.sortDir = "asc";
      }
      renderList(state);
      return;
    }
  });

  wireTagAliasesModalEvents(state, {
    onModalStateChange: () => syncRouteBusyState(state),
    onImportModeChange: () => syncImportModeFromControl(state),
    onImportSubmit: () => {
      void withRouteBusy(state, () => handleImport(state));
    },
    onPatchCopy: () => {
      void copyPatchSnippet(state);
    },
    onPromotionSubmit: () => {
      void withRouteBusy(state, () => submitAliasPromotion(state));
    },
    onDemoteSearch: () => renderDemoteTagPopup(state),
    onDemoteTagSelect: (tagId) => {
      addDemoteTag(state, tagId);
      updateDemoteUi(state);
    },
    onDemoteTagRemove: (tagId) => {
      if (!state.demoteState) return;
      const normalizedTagId = normalize(tagId);
      if (!normalizedTagId) return;
      state.demoteState.tags = state.demoteState.tags.filter((item) => item !== normalizedTagId);
      updateDemoteUi(state);
    },
    onDemoteSubmit: () => {
      void withRouteBusy(state, () => handleTagDemoteFromAliases(state));
    },
    onEditInput: () => updateAliasEditUi(state),
    onEditSearch: () => renderEditTagPopup(state),
    onEditTagSelect: (tagId) => {
      addEditTag(state, tagId);
      updateAliasEditUi(state);
    },
    onEditTagRemove: (tagId) => {
      if (!state.editState) return;
      const normalizedTagId = normalize(tagId);
      if (!normalizedTagId) return;
      state.editState.tags = state.editState.tags.filter((item) => item !== normalizedTagId);
      updateAliasEditUi(state);
    },
    onEditSave: () => {
      void withRouteBusy(state, () => saveAliasEdit(state));
    }
  });
}

function openPromotionModal(state, aliasKey, suggestedGroup) {
  openTagAliasesPromotionModal(state, aliasKey, suggestedGroup);
  syncRouteBusyState(state);
}

function closePromotionModal(state) {
  closeTagAliasesPromotionModal(state);
  syncRouteBusyState(state);
}

function openDemoteModal(state, tagId) {
  clearImportResult(state);
  const canonicalTagId = normalize(tagId);
  if (!canonicalTagId) return;
  const tagInfo = state.registryById.get(canonicalTagId);
  if (!tagInfo) {
    setImportResult(
      state,
      "error",
      aliasesText(state.config, "unknown_tag_selected", "Unknown tag selected: {tag_id}", { tag_id: canonicalTagId })
    );
    return;
  }

  openTagAliasesDemoteModal(state, {
    canonicalTagId,
    aliasKey: canonicalTagId.split(":", 2)[1] || canonicalTagId
  });
  syncRouteBusyState(state);
}

function closeDemoteModal(state) {
  closeTagAliasesDemoteModal(state);
  syncRouteBusyState(state);
}

function setDemoteStatus(state, kind, message) {
  setTagAliasesDemoteStatus(state, kind, message);
}

function getDemoteValidation(state) {
  if (!state.demoteState) return { valid: false, warning: "", tags: [] };
  const selectedTags = Array.isArray(state.demoteState.tags) ? state.demoteState.tags.slice() : [];
  let warning = "";

  if (!selectedTags.length) {
    warning = aliasesText(state.config, "target_tag_required", "At least one canonical target tag is required.");
  } else if (selectedTags.length > MAX_ALIAS_TAGS) {
    warning = aliasesText(state.config, "target_tags_max", "At most {max_tags} target tags are allowed.", { max_tags: MAX_ALIAS_TAGS });
  } else {
    const seenGroups = new Set();
    for (const tagId of selectedTags) {
      if (tagId === state.demoteState.tagId) {
        warning = aliasesText(state.config, "demotion_target_self", "Target list must not include the demoted tag.");
        break;
      }
      const info = state.registryById.get(tagId);
      if (!info) {
        warning = aliasesText(state.config, "unknown_tag_selected", "Unknown tag selected: {tag_id}", { tag_id: tagId });
        break;
      }
      if (seenGroups.has(info.group)) {
        warning = aliasesText(state.config, "target_tags_one_per_group", "Only one target tag per group is allowed ({group}).", { group: info.group });
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

function updateDemoteUi(state) {
  if (!state.demoteState) return;
  const validation = getDemoteValidation(state);
  let statusKind = "";
  let statusMessage = "";
  if (validation.warning) {
    const emptyWarning = aliasesText(state.config, "target_tag_required", "At least one canonical target tag is required.");
    statusKind = validation.warning === emptyWarning ? "" : "error";
    statusMessage = validation.warning;
  }
  renderTagAliasesDemoteSelectionState(state, {
    canConfirm: validation.valid,
    statusKind,
    statusMessage
  });
}

function getDemoteTagMatches(state, query) {
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
  return {
    matches: allMatches.slice(0, DEMOTE_TAG_MATCH_CAP),
    truncated: allMatches.length > DEMOTE_TAG_MATCH_CAP
  };
}

function renderDemoteTagPopup(state) {
  if (!state.demoteState) return;
  const result = getDemoteTagMatches(state, state.refs.demoteTagSearch.value);
  renderTagAliasesDemoteTagPopup(state, result);
}

function addDemoteTag(state, tagId) {
  if (!state.demoteState) return;
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId || !state.registryById.has(normalizedTagId)) return;
  if (normalizedTagId === state.demoteState.tagId) {
    setDemoteStatus(state, "error", aliasesText(state.config, "demotion_target_self", "Target list must not include the demoted tag."));
    return;
  }
  if (state.demoteState.tags.includes(normalizedTagId)) return;
  if (state.demoteState.tags.length >= MAX_ALIAS_TAGS) {
    setDemoteStatus(state, "error", aliasesText(state.config, "target_tags_max", "At most {max_tags} target tags are allowed.", { max_tags: MAX_ALIAS_TAGS }));
    return;
  }

  const nextGroup = normalizedTagId.split(":", 1)[0];
  const groupConflict = state.demoteState.tags.some((item) => item.split(":", 1)[0] === nextGroup);
  if (groupConflict) {
    setDemoteStatus(state, "error", aliasesText(state.config, "target_tags_one_per_group", "Only one target tag per group is allowed ({group}).", { group: nextGroup }));
    return;
  }

  state.demoteState.tags.push(normalizedTagId);
}

function setPromotionStatus(state, kind, message) {
  setTagAliasesPromotionStatus(state, kind, message);
}

async function loadData(state) {
  const [registryData, aliasesData] = await Promise.all([
    loadStudioRegistryJson(state.config),
    loadStudioAliasesJson(state.config)
  ]);
  let groupsData = null;
  try {
    groupsData = await loadStudioGroupsJson(state.config);
  } catch (error) {
    groupsData = null;
  }
  state.registryById = buildRegistryLookup(registryData);
  state.registryOptions = buildRegistryOptions(state.registryById);
  state.groupDescriptions = buildGroupDescriptionMap(groupsData);
  state.aliasesUpdatedAt = normalizeTimestamp(aliasesData && aliasesData.updated_at_utc);
  state.aliases = normalizeAliases(
    aliasesData,
    state.aliasesUpdatedAt,
    state.registryById,
    (key, fallback, tokens) => aliasesText(null, key, fallback, tokens)
  );
}

function renderImportAvailability(state) {
  renderTagAliasesImportAvailability(state, {
    onModalStateChange: () => syncRouteBusyState(state)
  });
}

async function probeImportMode(state) {
  await probeTagAliasesImportMode(state, {
    onImportAvailabilityChange: () => renderImportAvailability(state),
    onRouteStateChange: () => syncRouteBusyState(state)
  });
}

async function handleImport(state) {
  if (!state.selectedFile) {
    setImportResult(state, "error", aliasesText(state.config, "choose_import_file_error", "Choose an import file first."));
    return;
  }

  let importAliases = null;
  try {
    importAliases = await readTagAliasesImportFromFile(state.selectedFile);
  } catch (error) {
    setImportResult(state, "error", String(error.message || aliasesText(state.config, "invalid_import_file", "Invalid import file.")));
    return;
  }

  const result = await importTagAliases({
    saveMode: state.saveMode,
    importMode: state.importMode,
    importAliases,
    filename: state.selectedFile ? String(state.selectedFile.name || "") : "",
    config: state.config,
    patchContext: state
  });
  if (result.ok && result.mode === "post") {
    setImportResult(state, "success", result.summary);
    await loadData(state);
    renderControls(state);
    renderList(state);
    return;
  }

  if (result.switchToPatch) {
    applyTagAliasesPatchFallback(state);
    renderImportAvailability(state);
    setImportResult(state, "error", result.message);
  }

  const patchResult = result.patchResult;
  setImportResult(state, patchResult.kind, patchResult.message);
  if (patchResult.snippet) {
    openPatchModal(state, patchResult.snippet);
  }
}

async function handleAliasDelete(state, alias) {
  const aliasKey = normalize(alias);
  if (!aliasKey) return;

  const modalResult = await openConfirmModal({
    root: state.mount,
    title: aliasesText(state.config, "delete_modal_title", "Delete Alias"),
    body: aliasesText(state.config, "delete_confirm_template", "Delete alias \"{alias_key}\"?", { alias_key: aliasKey }),
    primaryLabel: aliasesText(state.config, "delete_confirm_button", "Delete"),
    cancelLabel: aliasesText(state.config, "delete_cancel_button", "Cancel")
  });
  if (!modalResult.confirmed) {
    clearImportResult(state);
    return;
  }

  const result = await deleteTagAlias({
    saveMode: state.saveMode,
    aliasKey,
    config: state.config
  });
  if (result.ok && result.mode === "post") {
    setImportResult(state, "success", result.summary);
    applyTagAliasesDeleteProjection(state, { aliasKey, response: result.response });
    renderControls(state);
    renderList(state);
    return;
  }

  if (result.switchToPatch) {
    applyTagAliasesPatchFallback(state);
    renderImportAvailability(state);
    setImportResult(state, "error", result.message);
  }

  const patchResult = result.patchResult;
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

function findAliasEntry(state, aliasKey) {
  return findNormalizedAliasEntry(state.aliases, aliasKey);
}

function isCreateAliasFlow(state) {
  return isCreateNormalizedAliasFlow(state.editState);
}

function openAliasEditModal(state, aliasKey) {
  clearImportResult(state);
  const entry = findAliasEntry(state, aliasKey);
  if (!entry) {
    setImportResult(state, "error", aliasesText(state.config, "alias_not_found", "Alias not found: {alias_key}", { alias_key: aliasKey }));
    return;
  }

  openTagAliasesEditModal(state, entry);
  updateAliasEditUi(state);
  syncRouteBusyState(state);
}

function openAliasCreateModal(state) {
  clearImportResult(state);
  openTagAliasesCreateModal(state);
  updateAliasEditUi(state);
  syncRouteBusyState(state);
}

function closeAliasEditModal(state) {
  closeTagAliasesEditModal(state);
  syncRouteBusyState(state);
}

function getAliasEditValidation(state) {
  return getNormalizedAliasEditValidation({
    editState: state.editState,
    aliasInput: state.refs.editAliasName.value,
    descriptionInput: state.refs.editAliasDescription.value,
    aliases: state.aliases,
    registryById: state.registryById,
    aliasRe: ALIAS_RE,
    maxAliasTags: MAX_ALIAS_TAGS,
    text: (key, fallback, tokens) => aliasesText(state.config, key, fallback, tokens)
  });
}

function setAliasEditStatus(state, kind, message) {
  setTagAliasesEditStatus(state, kind, message);
}

function updateAliasEditUi(state) {
  if (!state.editState) return;
  const validation = getAliasEditValidation(state);
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

function getEditTagMatches(state, query) {
  return getNormalizedEditTagMatches({
    query,
    editState: state.editState,
    registryOptions: state.registryOptions,
    cap: EDIT_TAG_MATCH_CAP
  });
}

function renderEditTagPopup(state) {
  if (!state.editState) return;
  const query = state.refs.editTagSearch.value;
  const result = getEditTagMatches(state, query);
  renderTagAliasesEditTagPopup(state, result);
}

function addEditTag(state, tagId) {
  if (!state.editState) return;
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId || !state.registryById.has(normalizedTagId)) return;
  if (state.editState.tags.includes(normalizedTagId)) return;
  if (state.editState.tags.length >= MAX_ALIAS_TAGS) {
    setAliasEditStatus(state, "error", aliasesText(state.config, "max_tags_warning", "Select up to {max_tags} tags.", { max_tags: MAX_ALIAS_TAGS }));
    return;
  }

  const nextGroup = normalizedTagId.split(":", 1)[0];
  const groupConflict = state.editState.tags.some((item) => item.split(":", 1)[0] === nextGroup);
  if (groupConflict) {
    setAliasEditStatus(state, "error", aliasesText(state.config, "one_tag_per_group_warning", "Only one tag per group is allowed ({group}).", { group: nextGroup }));
    return;
  }

  state.editState.tags.push(normalizedTagId);
}

async function saveAliasEdit(state) {
  if (!state.editState) return;
  const validation = getAliasEditValidation(state);
  if (!validation.valid || !validation.changed) return;
  const isCreate = isCreateAliasFlow(state);
  const result = await saveTagAliasEdit({
    saveMode: state.saveMode,
    isCreate,
    originalAlias: state.editState.originalAlias,
    validation,
    config: state.config
  });
  if (result.ok && result.mode === "post") {
    if (result.summary) {
      setImportResult(state, "success", result.summary);
    }
    applyTagAliasesEditProjection(state, {
      validation,
      originalAlias: state.editState.originalAlias,
      response: result.response
    });
    renderControls(state);
    renderList(state);
    closeAliasEditModal(state);
    return;
  }

  if (result.switchToPatch) {
    applyTagAliasesPatchFallback(state);
    renderImportAvailability(state);
    setAliasEditStatus(state, "error", result.message);
  }

  const patchResult = result.patchResult;
  closeAliasEditModal(state);
  openPatchModal(state, patchResult.snippet);
}

async function handleAliasPromote(state, alias) {
  const aliasKey = normalize(alias);
  if (!aliasKey) return;
  clearImportResult(state);

  const entry = findAliasEntry(state, aliasKey);
  if (!entry) {
    setImportResult(state, "error", aliasesText(state.config, "alias_not_found", "Alias not found: {alias_key}", { alias_key: aliasKey }));
    return;
  }

  const suggestedGroup = entry && Array.isArray(entry.groups) && entry.groups.length ? entry.groups[0] : "subject";
  openPromotionModal(state, aliasKey, suggestedGroup);
}

async function submitAliasPromotion(state) {
  if (!state.promotionState) return;
  const aliasKey = normalize(state.promotionState.aliasKey);
  const group = normalize(state.promotionState.group);
  if (!aliasKey) return;
  if (!group) {
    setPromotionStatus(state, "", aliasesText(state.config, "promotion_group_required", "Choose a group."));
    return;
  }
  if (!STUDIO_GROUPS.includes(group)) {
    setPromotionStatus(
      state,
      "error",
      aliasesText(state.config, "promotion_group_invalid", "Promotion group must be one of: subject, domain, form, theme.")
    );
    return;
  }
  closePromotionModal(state);

  if (state.saveMode === "post") {
    const preview = await previewTagAliasPromote({
      aliasKey,
      group,
      config: state.config
    });
    if (!preview.ok) {
      setImportResult(state, "error", preview.message);
      return;
    }
  }

  const result = await promoteTagAlias({
    saveMode: state.saveMode,
    state,
    aliasKey,
    group
  });
  if (!result.ok) {
    setImportResult(state, "error", result.message);
    return;
  }
  if (result.mode === "post") {
    setImportResult(state, "success", result.summary);
    applyTagAliasesPromoteProjection(state, { aliasKey, group, response: result.response });
    renderControls(state);
    renderList(state);
    return;
  }

  const patchResult = result.patchResult;
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

async function handleTagDemoteFromAliases(state) {
  if (!state.demoteState) return;
  const canonicalTagId = normalize(state.demoteState.tagId);
  if (!canonicalTagId) return;
  const validation = getDemoteValidation(state);
  if (!validation.valid) {
    setDemoteStatus(state, "error", validation.warning || aliasesText(state.config, "invalid_target_tags", "Invalid target tags."));
    return;
  }
  const aliasTargets = validation.tags.slice().sort((a, b) => a.localeCompare(b));

  if (state.saveMode === "post") {
    const preview = await previewTagAliasesTagDemote({
      canonicalTagId,
      aliasTargets,
      config: state.config
    });
    if (!preview.ok) {
      setDemoteStatus(state, "error", preview.message);
      setImportResult(state, "error", preview.message);
      return;
    }
    const previewSummary = preview.summary;
    const aliasKey = canonicalTagId.split(":")[1] || canonicalTagId;
    const confirmResult = await openConfirmDetailModal({
      root: state.mount,
      title: aliasesText(state.config, "demotion_confirm_title", "Confirm Tag Demotion"),
      body: aliasesText(
        state.config,
        "demotion_confirm_template",
        "Demote \"{tag_id}\" to alias \"{alias_key}\"?\n\nTargets: {targets}",
        {
          tag_id: canonicalTagId,
          alias_key: aliasKey,
          targets: aliasTargets.join(", ")
        }
      ),
      impact: previewSummary,
      primaryLabel: aliasesText(state.config, "demotion_confirm_button", "Demote"),
      cancelLabel: aliasesText(state.config, "demotion_cancel_button", "Cancel")
    });
    if (!confirmResult.confirmed) {
      return;
    }
  }

  const result = await demoteTagAliasFromAliases({
    saveMode: state.saveMode,
    canonicalTagId,
    aliasTargets
  });
  if (!result.ok) {
    const message = result.message || aliasesText(state.config, "demotion_failed", "Demotion failed.");
    setDemoteStatus(state, "error", message);
    setImportResult(state, "error", message);
    return;
  }
  if (result.mode === "post") {
    closeDemoteModal(state);
    setImportResult(state, "success", String(result.response.summary_text || aliasesText(state.config, "demoted_success", "Demoted.")));
    applyTagAliasesDemoteProjection(state, {
      canonicalTagId,
      aliasTargets,
      response: result.response
    });
    renderControls(state);
    renderList(state);
    return;
  }

  const patchResult = result.patchResult;
  closeDemoteModal(state);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

function openPatchModal(state, snippet) {
  showTagAliasesPatchModal(state, snippet);
}

function setImportResult(state, kind, message) {
  setTagAliasesImportResult(state, kind, message);
}

function clearImportResult(state) {
  clearTagAliasesImportResult(state);
}

async function copyPatchSnippet(state) {
  if (!state.patchSnippet) return;
  try {
    await navigator.clipboard.writeText(state.patchSnippet);
    setImportResult(state, "success", aliasesText(state.config, "patch_copy_success", "Patch snippet copied to clipboard."));
  } catch (error) {
    setImportResult(state, "error", aliasesText(state.config, "patch_copy_failed", "Copy failed. Select and copy the snippet manually."));
  }
}

function aliasesText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_aliases.${key}`, fallback, tokens);
}
