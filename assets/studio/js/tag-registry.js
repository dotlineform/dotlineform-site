import {
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfigWithText
} from "./studio-config.js";
import {
  buildStudioGroupDescriptionMap,
  getStudioAssignmentsSeries,
  loadSiteSeriesIndexJson,
  loadStudioAssignmentsJson,
  loadStudioAliasesJson,
  loadStudioGroupsJson,
  loadStudioRegistryJson
} from "./studio-data.js";
import {
  buildAliasKeySet,
  buildRegistryOptions,
  configureTagRegistryDomain,
  findTagById as findRegistryTagById,
  getDemoteTagMatches as getRegistryDemoteTagMatches,
  getDemoteValidation as getRegistryDemoteValidation,
  getNewTagValidation as getRegistryNewTagValidation,
  normalize,
  normalizeRegistryTags,
  normalizeTimestamp
} from "./tag-registry-domain.js";
import {
  applyTagRegistryCreateProjection,
  applyTagRegistryDeleteProjection,
  applyTagRegistryDemoteProjection,
  applyTagRegistryEditProjection,
  buildTagRegistrySeriesMetaById,
  getTagRegistryDeleteImpactSeries
} from "./tag-registry-state.js";
import {
  renderTagRegistryControls,
  renderTagRegistryError,
  renderTagRegistryList
} from "./tag-registry-render.js";
import {
  applyTagRegistryPatchFallback,
  createTagRegistryTag,
  deleteTagRegistryTag,
  demoteTagRegistryTag,
  importTagRegistryTags,
  previewTagRegistryDeleteImpact,
  previewTagRegistryDemote,
  readTagRegistryImportFromFile,
  saveTagRegistryEdit
} from "./tag-registry-workflow.js";
import {
  openConfirmDetailModal
} from "./studio-modal.js";
import {
  clearTagRegistryImportResult,
  collectTagRegistryModalRefs,
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
  renderTagRegistryDeleteImpactPreview,
  renderTagRegistryNewTagModalState,
  renderTagRegistryModals,
  setTagRegistryImportResult,
  setTagRegistryDeleteImpactStatus,
  showTagRegistryPatchModal,
  wireTagRegistryModalEvents
} from "./tag-registry-modals.js";
import {
  probeTagRegistryImportMode,
  renderTagRegistryImportAvailability,
  syncTagRegistryImportModeFromControl as syncImportModeFromControl
} from "./tag-registry-import-mode.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  tagRegistryUi
} from "./studio-ui.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const MAX_ALIAS_TAGS = 4;
const DEMOTE_TAG_MATCH_CAP = 12;
const TAG_SLUG_RE = /^[a-z0-9][a-z0-9-]*$/;
let GROUP_INFO_PAGE_PATH = "/studio/analytics/tag-groups/";
const UI = tagRegistryUi;
const { className: UI_CLASS, selector: UI_SELECTOR, state: UI_STATE } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagRegistryPage);
} else {
  initTagRegistryPage();
}

function routeStateDetail(state) {
  return {
    route: "tag-registry",
    mode: state.importModalOpen ? "import" : state.editTagId || state.newTagState || state.demoteState || state.deleteTagId ? "edit" : "list",
    service: state.saveMode === "post" ? "available" : "unavailable",
    recordLoaded: Boolean(state.tags && state.tags.length)
  };
}

function syncRouteBusyState(state) {
  setStudioRouteBusy(state.mount, Boolean(state.isBusy), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setStudioRouteReady(state.mount, ready, routeStateDetail(state));
}

async function withRouteBusy(state, task) {
  state.isBusy = true;
  syncRouteBusyState(state);
  try {
    return await task();
  } finally {
    state.isBusy = false;
    syncRouteBusyState(state);
  }
}

async function initTagRegistryPage() {
  const mount = document.getElementById("tag-registry");
  if (!mount) return;
  initializeStudioRouteState(mount, { route: "tag-registry", mode: "list" });

  let config = null;
  try {
    config = await loadStudioConfigWithText("tag_registry");
  } catch (error) {
    mount.innerHTML = `<div class="${UI_CLASS.error}">Failed to load tag registry config.</div>`;
    setStudioRouteReady(mount, true, {
      route: "tag-registry",
      mode: "empty",
      service: "unavailable",
      recordLoaded: false
    });
    return;
  }
  STUDIO_GROUPS = getStudioGroups(config);
  configureTagRegistryDomain({ groups: STUDIO_GROUPS });
  GROUP_INFO_PAGE_PATH = getStudioRoute(config, "tag_groups");

  const state = {
    mount,
    config,
    studioGroups: STUDIO_GROUPS,
    groupInfoPagePath: GROUP_INFO_PAGE_PATH,
    tags: [],
    filterGroup: "all",
    searchQuery: "",
    sortKey: "label",
    sortDir: "asc",
    importMode: "add",
    saveMode: "patch",
    importAvailable: false,
    selectedFile: null,
    importModalOpen: false,
    patchSnippet: "",
    editTagId: "",
    newTagState: null,
    demoteState: null,
    aliasKeys: new Set(),
    groupDescriptions: new Map(),
    deleteTagId: "",
    deletePreview: "",
    deletePreviewSeq: 0,
    registryOptions: [],
    refs: null,
    registryUpdatedAt: "",
    assignmentsSeries: {},
    seriesMetaById: new Map()
  };
  state.isBusy = false;

  renderShell(state);
  wireEvents(state);
  syncImportModeFromControl(state);

  try {
    await loadRegistry(state);
    renderControls(state);
    renderList(state);
    markRouteReady(state, true);
  } catch (error) {
    renderError(
      state,
      registryText(
        state.config,
        "load_failed_error",
        "Failed to load tag data from /assets/studio/data/tag_registry.json and /assets/studio/data/tag_aliases.json."
      )
    );
    markRouteReady(state, true);
    return;
  }

  void probeImportMode(state);
}

function renderShell(state) {
  const importButtonLabel = registryText(state.config, "import_button", "Import");
  const newTagButtonLabel = registryText(state.config, "new_tag_button", "New tag");
  const searchLabel = registryText(state.config, "search_label", "Search tags");
  const searchPlaceholder = registryText(state.config, "search_placeholder", "search");
  const refs = {
    openImportModal: state.mount.querySelector(UI_SELECTOR.openImportModal),
    openNewTag: state.mount.querySelector(UI_SELECTOR.openNewTag),
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
      registryText(state.config, "missing_template_shell_error", "Tag Registry error: missing template shell markup.")
    );
    return;
  }

  refs.openImportModal.textContent = importButtonLabel;
  refs.openNewTag.textContent = newTagButtonLabel;
  refs.searchLabel.textContent = searchLabel;
  refs.search.setAttribute("placeholder", searchPlaceholder);
  refs.modalHost.innerHTML = renderTagRegistryModals(state);

  state.refs = {
    ...refs,
    ...collectTagRegistryModalRefs(state.mount)
  };
  renderImportAvailability(state);
}

function wireEvents(state) {
  state.refs.search.addEventListener("input", () => {
    state.searchQuery = normalize(state.refs.search.value);
    renderList(state);
  });

  state.refs.openNewTag.addEventListener("click", () => {
    openNewTagModal(state);
  });

  state.mount.addEventListener("click", (event) => {
    const groupButton = event.target.closest("button[data-group]");
    if (groupButton) {
      const group = normalize(groupButton.getAttribute("data-group"));
      if (!group || group === "all") {
        state.filterGroup = "all";
        state.searchQuery = "";
        state.refs.search.value = "";
      } else {
        state.filterGroup = group;
      }
      renderControls(state);
      renderList(state);
      return;
    }

    const tagButton = event.target.closest("button[data-tag-id]");
    const demoteButton = event.target.closest("button[data-demote-tag-id]");
    const deleteButton = event.target.closest("button[data-delete-tag-id]");
    if (demoteButton) {
      const tagId = normalize(demoteButton.getAttribute("data-demote-tag-id"));
      if (tagId) openDemoteModal(state, tagId);
      return;
    }
    if (deleteButton) {
      const tagId = normalize(deleteButton.getAttribute("data-delete-tag-id"));
      if (tagId) openDeleteModal(state, tagId);
      return;
    }

    if (tagButton) {
      const tagId = normalize(tagButton.getAttribute("data-tag-id"));
      if (tagId) openEditModal(state, tagId);
      return;
    }

    const sortButton = event.target.closest("button[data-sort-key]");
    if (!sortButton) return;
    const nextSortKey = normalize(sortButton.getAttribute("data-sort-key"));
    if (!["label", "description"].includes(nextSortKey)) return;
    if (state.sortKey === nextSortKey) {
      state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
    } else {
      state.sortKey = nextSortKey;
      state.sortDir = "asc";
    }
    renderList(state);
  });

  wireTagRegistryModalEvents(state, {
    onModalStateChange: () => syncRouteBusyState(state),
    onImportModeChange: () => syncImportModeFromControl(state),
    onImportSubmit: () => {
      void withRouteBusy(state, () => handleImport(state));
    },
    onPatchCopy: () => {
      void copyPatchSnippet(state);
    },
    onEditSave: () => {
      void withRouteBusy(state, () => handleTagEdit(state));
    },
    onEditDescriptionInput: () => setEditStatus(state, "", ""),
    onNewTagInput: () => updateNewTagUi(state),
    onCreateTag: () => {
      void withRouteBusy(state, () => handleCreateTag(state));
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
      void withRouteBusy(state, () => handleTagDemote(state));
    },
    onDeleteConfirm: () => {
      void withRouteBusy(state, () => handleDeleteFromModal(state));
    }
  });
}

async function probeImportMode(state) {
  await probeTagRegistryImportMode(state, {
    onImportAvailabilityChange: () => renderImportAvailability(state),
    onRouteStateChange: () => syncRouteBusyState(state)
  });
}

function renderImportAvailability(state) {
  renderTagRegistryImportAvailability(state, {
    onModalStateChange: () => syncRouteBusyState(state)
  });
}

async function loadRegistry(state, options = {}) {
  const [registryData, aliasesData] = await Promise.all([
    loadStudioRegistryJson(state.config, options),
    loadStudioAliasesJson(state.config, options)
  ]);
  const [assignmentsResult, seriesIndexResult] = await Promise.allSettled([
    loadStudioAssignmentsJson(state.config, options),
    loadSiteSeriesIndexJson(state.config, options)
  ]);
  let groupsData = null;
  try {
    groupsData = await loadStudioGroupsJson(state.config, options);
  } catch (error) {
    groupsData = null;
  }
  state.registryUpdatedAt = normalizeTimestamp(registryData && registryData.updated_at_utc);
  state.tags = normalizeRegistryTags(registryData, state.registryUpdatedAt);
  state.aliasKeys = buildAliasKeySet(aliasesData);
  state.assignmentsSeries = assignmentsResult.status === "fulfilled"
    ? getStudioAssignmentsSeries(assignmentsResult.value)
    : {};
  state.seriesMetaById = seriesIndexResult.status === "fulfilled"
    ? buildTagRegistrySeriesMetaById(state.config, seriesIndexResult.value)
    : new Map();
  state.groupDescriptions = buildStudioGroupDescriptionMap(groupsData, STUDIO_GROUPS);
  state.registryOptions = buildRegistryOptions(state.tags);
}

function renderControls(state) {
  renderTagRegistryControls(state);
}

function renderList(state) {
  renderTagRegistryList(state);
}

function findTagById(state, tagId) {
  return findRegistryTagById(state.tags, tagId);
}

function openEditModal(state, tagId) {
  const tag = findTagById(state, tagId);
  if (!tag) return;
  clearImportResult(state);
  openTagRegistryEditModal(state, tag);
  syncRouteBusyState(state);
}

function closeEditModal(state) {
  closeTagRegistryEditModal(state);
  syncRouteBusyState(state);
}

function openNewTagModal(state) {
  clearImportResult(state);
  openTagRegistryNewModal(state);
  syncRouteBusyState(state);
}

function closeNewTagModal(state) {
  closeTagRegistryNewModal(state);
  syncRouteBusyState(state);
}

function setNewTagStatus(state, kind, message) {
  setStatusText(state.refs.newTagStatus, kind, message);
}

function getNewTagValidation(state) {
  return getRegistryNewTagValidation({
    newTagState: state.newTagState,
    slugInput: state.refs.newTagSlug.value,
    descriptionInput: state.refs.newTagDescription.value,
    tags: state.tags,
    tagSlugRe: TAG_SLUG_RE,
    studioGroups: STUDIO_GROUPS,
    text: (key, fallback, tokens) => registryText(state.config, key, fallback, tokens)
  });
}

function updateNewTagUi(state) {
  if (!state.newTagState) return;
  const slug = normalize(state.refs.newTagSlug.value);
  if (state.refs.newTagSlug.value !== slug) {
    state.refs.newTagSlug.value = slug;
  }
  state.newTagState.slug = slug;
  state.newTagState.description = String(state.refs.newTagDescription.value || "").trim();

  const validation = getNewTagValidation(state);
  renderTagRegistryNewTagModalState(state, validation);
}

function setEditStatus(state, kind, message) {
  setStatusText(state.refs.editStatus, kind, message);
}

async function refreshDeleteImpactPreview(state) {
  const seq = ++state.deletePreviewSeq;
  state.isBusy = true;
  syncRouteBusyState(state);
  let result = null;
  try {
    result = await previewTagRegistryDeleteImpact({
      saveMode: state.saveMode,
      tagId: state.deleteTagId,
      config: state.config
    });
  } finally {
    state.isBusy = false;
    syncRouteBusyState(state);
  }
  if (seq !== state.deletePreviewSeq || state.refs.deleteModal.hidden) return;
  if (result.ok) {
    state.deletePreview = result.summary;
    renderTagRegistryDeleteImpactPreview(state, {
      response: result.response,
      affectedSeries: getTagRegistryDeleteImpactSeries(state, state.deleteTagId)
    });
    return;
  }
  setTagRegistryDeleteImpactStatus(state, "error", result.message);
}

async function handleTagEdit(state) {
  if (!state.editTagId) return;
  const tagId = state.editTagId;
  const description = String(state.refs.editDescription.value || "").trim();
  const result = await saveTagRegistryEdit({
    saveMode: state.saveMode,
    tag: findTagById(state, tagId),
    description,
    config: state.config
  });
  if (!result.ok) {
    setEditStatus(state, result.code === "no_changes" ? "" : "error", result.message);
    return;
  }

  setEditStatus(state, "success", result.message);
  setImportResult(state, "success", result.summary);
  applyTagRegistryEditProjection(state, {
    tagId,
    description,
    response: result.response
  });
  renderControls(state);
  renderList(state);
  closeEditModal(state);
}

async function handleCreateTag(state) {
  if (!state.newTagState) return;
  const validation = getNewTagValidation(state);
  if (!validation.valid) {
    state.refs.newTagWarning.textContent = validation.warning || "";
    return;
  }

  const newTagRow = {
    tag_id: validation.tagId,
    group: validation.group,
    label: validation.slug,
    status: "active",
    description: validation.description
  };

  const result = await createTagRegistryTag({
    saveMode: state.saveMode,
    newTagRow,
    config: state.config
  });
  if (result.ok && result.mode === "post") {
    closeNewTagModal(state);
    setImportResult(state, "success", result.summary);
    applyTagRegistryCreateProjection(state, {
      validation,
      response: result.response
    });
    renderControls(state);
    renderList(state);
    return;
  }

  if (result.switchToPatch) {
    applyTagRegistryPatchFallback(state);
    renderImportAvailability(state);
    setNewTagStatus(state, "error", result.message);
  }

  const patchResult = result.patchResult;
  closeNewTagModal(state);
  setImportResult(state, patchResult.kind, patchResult.message);
  openPatchModal(state, patchResult.snippet);
}

function setDeleteStatus(state, kind, message) {
  setStatusText(state.refs.deleteStatus, kind, message);
}

function openDeleteModal(state, tagId) {
  clearImportResult(state);
  const tag = findTagById(state, tagId);
  if (!tag) {
    setImportResult(state, "error", registryText(state.config, "selected_tag_missing", "Selected tag is no longer available."));
    return;
  }
  openTagRegistryDeleteModal(state, tag);
  syncRouteBusyState(state);

  if (state.saveMode !== "post") {
    setDeleteStatus(state, "error", registryText(state.config, "local_delete_required", "Local server is required for delete."));
    setTagRegistryDeleteImpactStatus(state, "error", registryText(state.config, "delete_impact_unavailable_local", "Delete impact: unavailable (local server required)."));
    return;
  }

  void refreshDeleteImpactPreview(state);
}

function closeDeleteModal(state) {
  closeTagRegistryDeleteModal(state);
  syncRouteBusyState(state);
}

async function handleDeleteFromModal(state) {
  if (!state.deleteTagId) return;
  const deletedTagId = state.deleteTagId;
  const result = await deleteTagRegistryTag({
    saveMode: state.saveMode,
    tag: findTagById(state, deletedTagId),
    config: state.config
  });
  if (!result.ok) {
    setDeleteStatus(state, "error", result.message);
    return;
  }

  closeDeleteModal(state);
  setImportResult(state, "success", result.summary);
  applyTagRegistryDeleteProjection(state, {
    tagId: deletedTagId,
    response: result.response
  });
  renderControls(state);
  renderList(state);
}

function openDemoteModal(state, tagId) {
  clearImportResult(state);
  const tag = findTagById(state, tagId);
  if (!tag) {
    setImportResult(state, "error", registryText(state.config, "selected_tag_missing", "Selected tag is no longer available."));
    return;
  }
  const aliasKey = tag.tagId.split(":")[1] || tag.tagId;
  if (state.aliasKeys.has(aliasKey)) {
    setImportResult(
      state,
      "error",
      registryText(
        state.config,
        "alias_exists_demote_error",
        "Alias already exists: {alias_key}. Demotion overwrite is not permitted.",
        { alias_key: aliasKey }
      )
    );
    return;
  }

  openTagRegistryDemoteModal(state, { tag, aliasKey });
  updateDemoteUi(state);
  syncRouteBusyState(state);
}

function closeDemoteModal(state) {
  closeTagRegistryDemoteModal(state);
  syncRouteBusyState(state);
}

function setDemoteStatus(state, kind, message) {
  setStatusText(state.refs.demoteStatus, kind, message);
}

function getDemoteValidation(state) {
  return getRegistryDemoteValidation({
    demoteState: state.demoteState,
    tags: state.tags,
    maxAliasTags: MAX_ALIAS_TAGS,
    text: (key, fallback, tokens) => registryText(state.config, key, fallback, tokens)
  });
}

function updateDemoteUi(state) {
  if (!state.demoteState) return;
  const validation = getDemoteValidation(state);
  let statusKind = "";
  let statusMessage = "";
  if (validation.warning) {
    const emptyWarning = registryText(state.config, "demote_select_target_warning", "Select at least one target tag.");
    statusKind = validation.warning === emptyWarning ? "" : "error";
    statusMessage = validation.warning;
  }
  const selectedItems = state.demoteState.tags.map((tagId) => {
    const info = findTagById(state, tagId);
    return {
      tagId,
      group: info && STUDIO_GROUPS.includes(info.group) ? info.group : "warning",
      label: info ? info.label : tagId
    };
  });
  renderTagRegistryDemoteSelectionState(state, {
    selectedItems,
    canConfirm: validation.valid,
    statusKind,
    statusMessage
  });
}

function getDemoteTagMatches(state, query) {
  return getRegistryDemoteTagMatches({
    query,
    demoteState: state.demoteState,
    registryOptions: state.registryOptions,
    cap: DEMOTE_TAG_MATCH_CAP
  });
}

function renderDemoteTagPopup(state) {
  if (!state.demoteState) return;
  const result = getDemoteTagMatches(state, state.refs.demoteTagSearch.value);
  renderTagRegistryDemoteTagPopup(state, result);
}

function addDemoteTag(state, tagId) {
  if (!state.demoteState) return;
  const normalizedTagId = normalize(tagId);
  if (!normalizedTagId) return;
  const tag = findTagById(state, normalizedTagId);
  if (!tag) return;
  if (normalizedTagId === state.demoteState.tagId) {
    setDemoteStatus(state, "error", registryText(state.config, "demote_target_includes_self", "Target list must not include the demoted tag."));
    return;
  }
  if (state.demoteState.tags.includes(normalizedTagId)) return;
  if (state.demoteState.tags.length >= MAX_ALIAS_TAGS) {
    setDemoteStatus(state, "error", registryText(state.config, "demote_max_tags_warning", "Select up to {max_tags} tags.", { max_tags: MAX_ALIAS_TAGS }));
    return;
  }
  const nextGroup = tag.group;
  const groupConflict = state.demoteState.tags.some((item) => {
    const existing = findTagById(state, item);
    return Boolean(existing && existing.group === nextGroup);
  });
  if (groupConflict) {
    setDemoteStatus(
      state,
      "error",
      registryText(state.config, "demote_one_per_group_warning", "Only one target tag per group is allowed ({group}).", { group: nextGroup })
    );
    return;
  }
  state.demoteState.tags.push(normalizedTagId);
}

async function handleTagDemote(state) {
  if (!state.demoteState) return;
  const tag = findTagById(state, state.demoteState.tagId);
  if (!tag) {
    const message = registryText(state.config, "selected_tag_missing", "Selected tag is no longer available.");
    setDemoteStatus(state, "error", message);
    setImportResult(state, "error", message);
    return;
  }

  const aliasKey = tag.tagId.split(":")[1] || tag.tagId;
  if (state.aliasKeys.has(aliasKey)) {
    const message = registryText(
      state.config,
      "alias_exists_demote_error",
      "Alias already exists: {alias_key}. Demotion overwrite is not permitted.",
      { alias_key: aliasKey }
    );
    setDemoteStatus(state, "error", message);
    setImportResult(state, "error", message);
    return;
  }

  const validation = getDemoteValidation(state);
  if (!validation.valid) {
    setDemoteStatus(state, "error", validation.warning || registryText(state.config, "demote_invalid_targets", "Invalid target tags."));
    return;
  }

  const aliasTargets = validation.tags.slice().sort((a, b) => a.localeCompare(b));

  if (state.saveMode === "post") {
    const preview = await previewTagRegistryDemote({
      tagId: tag.tagId,
      aliasTargets,
      config: state.config
    });
    if (!preview.ok) {
      const message = preview.message;
      setDemoteStatus(state, "error", message);
      setImportResult(state, "error", message);
      return;
    }

    const previewSummary = preview.summary;
    if (Number(preview.response && preview.response.demoted_alias_overwritten || 0) > 0) {
      const message = registryText(
        state.config,
        "alias_exists_demote_error",
        "Alias already exists: {alias_key}. Demotion overwrite is not permitted.",
        { alias_key: aliasKey }
      );
      setDemoteStatus(state, "error", message);
      setImportResult(state, "error", message);
      return;
    }
    const confirmResult = await openConfirmDetailModal({
      root: state.mount,
      title: registryText(state.config, "demote_confirm_title", "Confirm Tag Demotion"),
      body: registryText(
        state.config,
        "demote_confirm_template",
        "Demote \"{tag_id}\" to alias \"{alias_key}\"?\n\nTargets: {targets}",
        {
          tag_id: tag.tagId,
          alias_key: aliasKey,
          targets: aliasTargets.join(", ")
        }
      ),
      impact: previewSummary,
      primaryLabel: registryText(state.config, "demote_confirm_button", "Demote"),
      cancelLabel: registryText(state.config, "demote_cancel_button", "Cancel")
    });
    if (!confirmResult.confirmed) {
      clearImportResult(state);
      return;
    }
  }

  const result = await demoteTagRegistryTag({
    saveMode: state.saveMode,
    tagId: tag.tagId,
    aliasTargets,
    config: state.config
  });
  if (!result.ok) {
    setDemoteStatus(state, "error", result.message);
    setImportResult(state, "error", result.message);
    return;
  }
  if (result.mode === "post") {
    closeDemoteModal(state);
    setImportResult(state, "success", result.summary);
    applyTagRegistryDemoteProjection(state, {
      tagId: tag.tagId,
      aliasKey,
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

async function handleImport(state) {
  if (!state.selectedFile) {
    setImportResult(state, "error", registryText(state.config, "choose_import_file_error", "Choose an import file first."));
    return;
  }

  let importRegistry = null;
  try {
    importRegistry = await readImportRegistryFromFile(state.selectedFile);
  } catch (error) {
    setImportResult(state, "error", String(error.message || registryText(state.config, "invalid_import_file", "Invalid import file.")));
    return;
  }

  const result = await importTagRegistryTags({
    saveMode: state.saveMode,
    importMode: state.importMode,
    importRegistry,
    filename: state.selectedFile ? String(state.selectedFile.name || "") : "",
    config: state.config,
    patchContext: state
  });
  if (result.ok && result.mode === "post") {
    setImportResult(state, "success", result.summary);
    await loadRegistry(state, { cache: "no-store" });
    renderControls(state);
    renderList(state);
    return;
  }

  if (result.switchToPatch) {
    applyTagRegistryPatchFallback(state);
    renderImportAvailability(state);
    setImportResult(state, "error", result.message);
  }

  const patchResult = result.patchResult;
  setImportResult(state, patchResult.kind, patchResult.message);
  if (patchResult.snippet) {
    openPatchModal(state, patchResult.snippet);
  }
}

async function readImportRegistryFromFile(file) {
  return readTagRegistryImportFromFile(file, STUDIO_GROUPS);
}

function openPatchModal(state, snippet) {
  showTagRegistryPatchModal(state, snippet);
}

function setImportResult(state, kind, message) {
  setTagRegistryImportResult(state, kind, message);
}

function clearImportResult(state) {
  clearTagRegistryImportResult(state);
}

async function copyPatchSnippet(state) {
  if (!state.patchSnippet) return;
  try {
    await navigator.clipboard.writeText(state.patchSnippet);
    setImportResult(state, "success", registryText(state.config, "patch_copy_success", "Patch snippet copied to clipboard."));
  } catch (error) {
    setImportResult(state, "error", registryText(state.config, "patch_copy_failed", "Copy failed. Select and copy the snippet manually."));
  }
}

function registryText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_registry.${key}`, fallback, tokens);
}

function renderError(state, message) {
  renderTagRegistryError(state, message);
}

function setSelectOptionLabel(select, value, label) {
  if (!select) return;
  const option = select.querySelector(`option[value="${value}"]`);
  if (option) option.textContent = label;
}

function setStatusText(target, kind, message, baseClass = UI_CLASS.formStatus) {
  if (!target) return;
  target.textContent = message || "";
  target.className = baseClass;
  if (kind) {
    target.dataset.state = kind;
    return;
  }
  delete target.dataset.state;
}
