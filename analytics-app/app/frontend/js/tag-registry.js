import {
  getAnalyticsGroups,
  getAnalyticsRoute,
  getAnalyticsText,
  loadAnalyticsConfigWithText
} from "./analytics-config.js";
import {
  buildAnalyticsGroupDescriptionMap,
  getAnalyticsAssignmentsSeries,
  loadSiteSeriesIndexJson,
  loadAnalyticsAssignmentsJson,
  loadAnalyticsAliasesJson,
  loadAnalyticsGroupsJson,
  loadAnalyticsRegistryJson
} from "./analytics-data.js";
import {
  buildAliasKeySet,
  buildRegistryOptions,
  configureTagRegistryDomain,
  findTagById as findRegistryTagById,
  normalize,
  normalizeRegistryTags,
  normalizeTimestamp
} from "./tag-registry-domain.js";
import {
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
} from "./analytics-modal.js";
import {
  clearTagRegistryImportResult,
  collectTagRegistryModalRefs,
  renderTagRegistryDeleteImpactPreview,
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
  initializeAnalyticsRouteState,
  setAnalyticsRouteBusy,
  setAnalyticsRouteReady
} from "./analytics-route-state.js";
import {
  bindTagSaveModeReprobe,
  tagRouteServiceState,
  withTagRouteBusy
} from "./tag-route-save-session.js";
import {
  tagRegistryUi
} from "./analytics-ui.js";
import {
  addTagRegistryDemoteTag,
  applyTagRegistryCreatePatchResult,
  applyTagRegistryCreatePostResult,
  applyTagRegistryDeleteResult,
  applyTagRegistryDemotePatchResult,
  applyTagRegistryDemotePostResult,
  applyTagRegistryEditResult,
  closeTagRegistryDeleteWorkflow,
  closeTagRegistryDemoteWorkflow,
  closeTagRegistryEditWorkflow,
  closeTagRegistryNewWorkflow,
  getTagRegistryDemoteValidation,
  getTagRegistryNewValidation,
  openTagRegistryDeleteWorkflow,
  openTagRegistryDemoteWorkflow,
  openTagRegistryEditWorkflow,
  openTagRegistryNewWorkflow,
  renderTagRegistryDemoteWorkflowPopup,
  setTagRegistryDeleteStatus,
  setTagRegistryDemoteStatus,
  setTagRegistryEditStatus,
  setTagRegistryNewStatus,
  updateTagRegistryDemoteWorkflow,
  updateTagRegistryNewWorkflow
} from "./tag-registry-modal-workflow.js";

let STUDIO_GROUPS = ["subject", "domain", "form", "theme"];
const MAX_ALIAS_TAGS = 4;
const DEMOTE_TAG_MATCH_CAP = 12;
const TAG_SLUG_RE = /^[a-z0-9][a-z0-9-]*$/;
let GROUP_INFO_PAGE_PATH = "/analytics/tag-groups/";
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
    service: tagRouteServiceState(state),
    recordLoaded: Boolean(state.tags && state.tags.length)
  };
}

function syncRouteBusyState(state) {
  setAnalyticsRouteBusy(state.mount, Boolean(state.isBusy), routeStateDetail(state));
}

function markRouteReady(state, ready) {
  setAnalyticsRouteReady(state.mount, ready, routeStateDetail(state));
}

async function withRouteBusy(state, task) {
  return withTagRouteBusy(state, task, { syncRouteBusyState });
}

async function initTagRegistryPage() {
  const mount = document.getElementById("tag-registry");
  if (!mount) return;
  initializeAnalyticsRouteState(mount, { route: "tag-registry", mode: "list" });

  let config = null;
  try {
    config = await loadAnalyticsConfigWithText("tag_registry");
  } catch (error) {
    mount.innerHTML = `<div class="${UI_CLASS.error}">Failed to load tag registry config.</div>`;
    setAnalyticsRouteReady(mount, true, {
      route: "tag-registry",
      mode: "empty",
      service: "unavailable",
      recordLoaded: false
    });
    return;
  }
  STUDIO_GROUPS = getAnalyticsGroups(config);
  configureTagRegistryDomain({ groups: STUDIO_GROUPS });
  GROUP_INFO_PAGE_PATH = getAnalyticsRoute(config, "tag_groups");

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
        "Failed to load tag data from /analytics/data/canonical/tag-registry.json and /analytics/data/canonical/tag-aliases.json."
      )
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
    loadAnalyticsRegistryJson(state.config, options),
    loadAnalyticsAliasesJson(state.config, options)
  ]);
  const [assignmentsResult, seriesIndexResult] = await Promise.allSettled([
    loadAnalyticsAssignmentsJson(state.config, options),
    loadSiteSeriesIndexJson(state.config, options)
  ]);
  let groupsData = null;
  try {
    groupsData = await loadAnalyticsGroupsJson(state.config, options);
  } catch (error) {
    groupsData = null;
  }
  state.registryUpdatedAt = normalizeTimestamp(registryData && registryData.updated_at_utc);
  state.tags = normalizeRegistryTags(registryData, state.registryUpdatedAt);
  state.aliasKeys = buildAliasKeySet(aliasesData);
  state.assignmentsSeries = assignmentsResult.status === "fulfilled"
    ? getAnalyticsAssignmentsSeries(assignmentsResult.value)
    : {};
  state.seriesMetaById = seriesIndexResult.status === "fulfilled"
    ? buildTagRegistrySeriesMetaById(state.config, seriesIndexResult.value)
    : new Map();
  state.groupDescriptions = buildAnalyticsGroupDescriptionMap(groupsData, STUDIO_GROUPS);
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

function modalWorkflowOptions(state) {
  return {
    text: (key, fallback, tokens) => registryText(state.config, key, fallback, tokens),
    tagSlugRe: TAG_SLUG_RE,
    studioGroups: STUDIO_GROUPS,
    maxAliasTags: MAX_ALIAS_TAGS,
    cap: DEMOTE_TAG_MATCH_CAP,
    findTagById: (tagId) => findTagById(state, tagId),
    clearImportResult: () => clearImportResult(state),
    setImportResult: (kind, message) => setImportResult(state, kind, message),
    syncRouteBusyState: () => syncRouteBusyState(state),
    refreshDeleteImpactPreview: () => refreshDeleteImpactPreview(state),
    renderControls: () => renderControls(state),
    renderList: () => renderList(state),
    applyPatchFallback: () => applyTagRegistryPatchFallback(state),
    renderImportAvailability: () => renderImportAvailability(state),
    openPatchModal: (snippet) => openPatchModal(state, snippet)
  };
}

function openEditModal(state, tagId) {
  openTagRegistryEditWorkflow(state, tagId, modalWorkflowOptions(state));
}

function closeEditModal(state) {
  closeTagRegistryEditWorkflow(state, modalWorkflowOptions(state));
}

function openNewTagModal(state) {
  openTagRegistryNewWorkflow(state, modalWorkflowOptions(state));
}

function closeNewTagModal(state) {
  closeTagRegistryNewWorkflow(state, modalWorkflowOptions(state));
}

function getNewTagValidation(state) {
  return getTagRegistryNewValidation(state, modalWorkflowOptions(state));
}

function updateNewTagUi(state) {
  updateTagRegistryNewWorkflow(state, modalWorkflowOptions(state));
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
    setTagRegistryEditStatus(state, result.code === "no_changes" ? "" : "error", result.message);
    return;
  }

  applyTagRegistryEditResult(state, {
    tagId,
    description,
    result
  }, modalWorkflowOptions(state));
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
    applyTagRegistryCreatePostResult(state, {
      validation,
      result
    }, modalWorkflowOptions(state));
    return;
  }

  applyTagRegistryCreatePatchResult(state, {
    result,
    patchResult: result.patchResult
  }, modalWorkflowOptions(state));
}

function openDeleteModal(state, tagId) {
  openTagRegistryDeleteWorkflow(state, tagId, modalWorkflowOptions(state));
}

function closeDeleteModal(state) {
  closeTagRegistryDeleteWorkflow(state, modalWorkflowOptions(state));
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
    setTagRegistryDeleteStatus(state, "error", result.message);
    return;
  }

  applyTagRegistryDeleteResult(state, {
    tagId: deletedTagId,
    result
  }, modalWorkflowOptions(state));
}

function openDemoteModal(state, tagId) {
  openTagRegistryDemoteWorkflow(state, tagId, modalWorkflowOptions(state));
}

function closeDemoteModal(state) {
  closeTagRegistryDemoteWorkflow(state, modalWorkflowOptions(state));
}

function getDemoteValidation(state) {
  return getTagRegistryDemoteValidation(state, modalWorkflowOptions(state));
}

function updateDemoteUi(state) {
  updateTagRegistryDemoteWorkflow(state, modalWorkflowOptions(state));
}

function renderDemoteTagPopup(state) {
  renderTagRegistryDemoteWorkflowPopup(state, modalWorkflowOptions(state));
}

function addDemoteTag(state, tagId) {
  addTagRegistryDemoteTag(state, tagId, modalWorkflowOptions(state));
}

async function handleTagDemote(state) {
  if (!state.demoteState) return;
  const tag = findTagById(state, state.demoteState.tagId);
  if (!tag) {
    const message = registryText(state.config, "selected_tag_missing", "Selected tag is no longer available.");
    setTagRegistryDemoteStatus(state, "error", message);
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
    setTagRegistryDemoteStatus(state, "error", message);
    setImportResult(state, "error", message);
    return;
  }

  const validation = getDemoteValidation(state);
  if (!validation.valid) {
    setTagRegistryDemoteStatus(state, "error", validation.warning || registryText(state.config, "demote_invalid_targets", "Invalid target tags."));
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
      setTagRegistryDemoteStatus(state, "error", message);
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
      setTagRegistryDemoteStatus(state, "error", message);
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
    setTagRegistryDemoteStatus(state, "error", result.message);
    setImportResult(state, "error", result.message);
    return;
  }
  if (result.mode === "post") {
    applyTagRegistryDemotePostResult(state, {
      tagId: tag.tagId,
      aliasKey,
      result
    }, modalWorkflowOptions(state));
    return;
  }

  applyTagRegistryDemotePatchResult(state, {
    patchResult: result.patchResult
  }, modalWorkflowOptions(state));
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
  return getAnalyticsText(config, `tag_registry.${key}`, fallback, tokens);
}

function renderError(state, message) {
  renderTagRegistryError(state, message);
}

function setSelectOptionLabel(select, value, label) {
  if (!select) return;
  const option = select.querySelector(`option[value="${value}"]`);
  if (option) option.textContent = label;
}
