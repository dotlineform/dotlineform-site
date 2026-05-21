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
  collectTagAliasesModalRefs,
  renderTagAliasesModals,
  setTagAliasesImportResult,
  showTagAliasesPatchModal,
  wireTagAliasesModalEvents
} from "./tag-aliases-modals.js";
import {
  addAliasDemoteTag,
  addAliasEditTag,
  closeAliasDemoteModal,
  closeAliasEditWorkflowModal,
  closeAliasPromotionModal,
  findTagAliasEntry,
  getAliasDemoteValidation,
  getAliasWorkflowEditValidation,
  getAliasWorkflowStudioGroups,
  isAliasCreateFlow,
  openAliasCreateWorkflowModal,
  openAliasDemoteModal,
  openAliasEditWorkflowModal,
  openAliasPromotionModal,
  removeAliasDemoteTag,
  removeAliasEditTag,
  renderAliasDemoteTagPopup,
  renderAliasEditTagPopup,
  setAliasDemoteStatus,
  setAliasEditStatus,
  setAliasPromotionStatus,
  updateAliasDemoteUi,
  updateAliasEditUi
} from "./tag-aliases-modal-workflow.js";
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
const MAX_ALIAS_TAGS = 4;
const EDIT_TAG_MATCH_CAP = 12;
const DEMOTE_TAG_MATCH_CAP = 12;
const UI = tagAliasesUi;
const { className: UI_CLASS, selector: UI_SELECTOR } = UI;

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
    openAliasCreateWorkflowModal(state, modalWorkflowCallbacks());
  });

  state.mount.addEventListener("click", (event) => {
    const demoteButton = event.target.closest("button[data-demote-tag-id]");
    if (demoteButton) {
      const tagId = normalize(demoteButton.getAttribute("data-demote-tag-id"));
      if (tagId) openAliasDemoteModal(state, tagId, modalWorkflowCallbacks());
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
      if (alias) openAliasEditWorkflowModal(state, alias, modalWorkflowCallbacks());
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
    onDemoteSearch: () => renderAliasDemoteTagPopup(state, modalWorkflowCallbacks()),
    onDemoteTagSelect: (tagId) => {
      addAliasDemoteTag(state, tagId, modalWorkflowCallbacks());
      updateAliasDemoteUi(state, modalWorkflowCallbacks());
    },
    onDemoteTagRemove: (tagId) => {
      removeAliasDemoteTag(state, tagId);
      updateAliasDemoteUi(state, modalWorkflowCallbacks());
    },
    onDemoteSubmit: () => {
      void withRouteBusy(state, () => handleTagDemoteFromAliases(state));
    },
    onEditInput: () => updateAliasEditUi(state, modalWorkflowCallbacks()),
    onEditSearch: () => renderAliasEditTagPopup(state, modalWorkflowCallbacks()),
    onEditTagSelect: (tagId) => {
      addAliasEditTag(state, tagId, modalWorkflowCallbacks());
      updateAliasEditUi(state, modalWorkflowCallbacks());
    },
    onEditTagRemove: (tagId) => {
      removeAliasEditTag(state, tagId);
      updateAliasEditUi(state, modalWorkflowCallbacks());
    },
    onEditSave: () => {
      void withRouteBusy(state, () => saveAliasEdit(state));
    }
  });
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

async function saveAliasEdit(state) {
  if (!state.editState) return;
  const validation = getAliasWorkflowEditValidation(state, modalWorkflowCallbacks());
  if (!validation.valid || !validation.changed) return;
  const isCreate = isAliasCreateFlow(state);
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
    closeAliasEditWorkflowModal(state, modalWorkflowCallbacks());
    return;
  }

  if (result.switchToPatch) {
    applyTagAliasesPatchFallback(state);
    renderImportAvailability(state);
    setAliasEditStatus(state, "error", result.message);
  }

  const patchResult = result.patchResult;
  closeAliasEditWorkflowModal(state, modalWorkflowCallbacks());
  openPatchModal(state, patchResult.snippet);
}

async function handleAliasPromote(state, alias) {
  const aliasKey = normalize(alias);
  if (!aliasKey) return;
  clearImportResult(state);

  const entry = findTagAliasEntry(state, aliasKey);
  if (!entry) {
    setImportResult(state, "error", aliasesText(state.config, "alias_not_found", "Alias not found: {alias_key}", { alias_key: aliasKey }));
    return;
  }

  const suggestedGroup = entry && Array.isArray(entry.groups) && entry.groups.length ? entry.groups[0] : "subject";
  openAliasPromotionModal(state, aliasKey, suggestedGroup, modalWorkflowCallbacks());
}

async function submitAliasPromotion(state) {
  if (!state.promotionState) return;
  const aliasKey = normalize(state.promotionState.aliasKey);
  const group = normalize(state.promotionState.group);
  if (!aliasKey) return;
  if (!group) {
    setAliasPromotionStatus(state, "", aliasesText(state.config, "promotion_group_required", "Choose a group."));
    return;
  }
  if (!getAliasWorkflowStudioGroups(state).includes(group)) {
    setAliasPromotionStatus(
      state,
      "error",
      aliasesText(state.config, "promotion_group_invalid", "Promotion group must be one of: subject, domain, form, theme.")
    );
    return;
  }
  closeAliasPromotionModal(state, modalWorkflowCallbacks());

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
  const validation = getAliasDemoteValidation(state, modalWorkflowCallbacks());
  if (!validation.valid) {
    setAliasDemoteStatus(state, "error", validation.warning || aliasesText(state.config, "invalid_target_tags", "Invalid target tags."));
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
      setAliasDemoteStatus(state, "error", preview.message);
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
    setAliasDemoteStatus(state, "error", message);
    setImportResult(state, "error", message);
    return;
  }
  if (result.mode === "post") {
    closeAliasDemoteModal(state, modalWorkflowCallbacks());
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
  closeAliasDemoteModal(state, modalWorkflowCallbacks());
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

function modalWorkflowCallbacks() {
  return {
    clearImportResult,
    demoteTagMatchCap: DEMOTE_TAG_MATCH_CAP,
    editTagMatchCap: EDIT_TAG_MATCH_CAP,
    maxAliasTags: MAX_ALIAS_TAGS,
    setImportResult,
    syncRouteBusyState,
    text: (key, fallback, tokens) => aliasesText(null, key, fallback, tokens)
  };
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
