import {
  getStudioGroups,
  getStudioRoute,
  getStudioText,
  loadStudioConfig
} from "./studio-config.js";
import {
  buildAnalyticsGroupDescriptionMap,
  getAnalyticsAssignmentsSeries,
  loadAnalyticsAssignmentsJson,
  loadAnalyticsAliasesJson,
  loadAnalyticsGroupsJson,
  loadAnalyticsRegistryJson,
  loadStudioSeriesSearchJson
} from "./studio-tag-data.js";
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
  bindDocumentLocationPicker
} from "/shared/frontend/js/document-location-picker.js";
import {
  createDocumentLocationProvider
} from "/shared/frontend/js/document-location-provider.js";
import {
  appendTagRegistryDocumentUrl,
  attachTagRegistryDocuments,
  loadTagRegistryDocumentLocations,
  removeTagRegistryDocumentUrl,
  setTagRegistryDocumentLocation
} from "./tag-registry-documents.js";
import {
  applyTagRegistryPatchFallback,
  createTagRegistryTag,
  deleteTagRegistryTag,
  demoteTagRegistryTag,
  previewTagRegistryDeleteImpact,
  previewTagRegistryDemote,
  saveTagRegistryEdit
} from "./tag-registry-workflow.js";
import {
  openConfirmDetailModal
} from "./studio-modal.js";
import {
  clearTagRegistryRouteResult,
  collectTagRegistryModalRefs,
  renderTagRegistryDeleteImpactPreview,
  renderTagRegistryEditDocuments,
  renderTagRegistryModals,
  setTagRegistryRouteResult,
  setTagRegistryDeleteImpactStatus,
  showTagRegistryPatchModal,
  wireTagRegistryModalEvents
} from "./tag-registry-modals.js";
import {
  initializeStudioRouteState,
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";
import {
  bindTagSaveModeReprobe,
  probeTagRouteSaveMode,
  tagRouteServiceState,
  withTagRouteBusy
} from "./tag-route-save-session.js";
import {
  tagRegistryUi
} from "./tag-ui.js";
import {
  addTagRegistryDemoteTag,
  applyTagRegistryCreatePatchResult,
  applyTagRegistryCreatePostResult,
  applyTagRegistryDeleteResult,
  applyTagRegistryDemotePatchResult,
  applyTagRegistryDemotePostResult,
  applyTagRegistryEditResult,
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
let GROUP_INFO_PAGE_PATH = "/studio/tag-groups/";
const UI = tagRegistryUi;
const { className: UI_CLASS, selector: UI_SELECTOR } = UI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTagRegistryPage);
} else {
  initTagRegistryPage();
}

function routeStateDetail(state) {
  return {
    route: "tag-registry",
    mode: state.editTagId || state.newTagState || state.demoteState || state.deleteTagId ? "edit" : "list",
    service: tagRouteServiceState(state),
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
  return withTagRouteBusy(state, task, { syncRouteBusyState });
}

async function initTagRegistryPage() {
  const mount = document.getElementById("tag-registry");
  if (!mount) return;
  initializeStudioRouteState(mount, { route: "tag-registry", mode: "list" });

  let config;
  try {
    config = await loadStudioConfig();
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
    sortKey: "tag",
    sortDir: "asc",
    saveMode: "patch",
    patchSnippet: "",
    editTagId: "",
    editTagGroup: "",
    editTagDocUrls: [],
    editTagPendingDocument: null,
    newTagState: null,
    demoteState: null,
    aliasKeys: new Set(),
    groupDescriptions: new Map(),
    deleteTagId: "",
    deletePreview: "",
    deletePreviewSeq: 0,
    registryOptions: [],
    documentLocationProvider: createDocumentLocationProvider(),
    documentLocationsByUrl: new Map(),
    documentLocationError: "",
    documentPicker: null,
    refs: null,
    registryUpdatedAt: "",
    assignmentsSeries: {},
    seriesMetaById: new Map()
  };
  state.isBusy = false;

  renderShell(state);
  bindRegistryDocumentPicker(state);
  wireEvents(state);

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
        "Failed to load tag data from /studio/api/tags/tag-registry and /studio/api/tags/tag-aliases."
      )
    );
    markRouteReady(state, true);
    return;
  }

  bindTagSaveModeReprobe(() => {
    void probeSaveMode(state);
  });
  void probeSaveMode(state);
}

function renderShell(state) {
  const newTagButtonLabel = registryText(state.config, "new_tag_button", "New tag");
  const searchLabel = registryText(state.config, "search_label", "Search tags");
  const searchPlaceholder = registryText(state.config, "search_placeholder", "search");
  const refs = {
    openNewTag: state.mount.querySelector(UI_SELECTOR.openNewTag),
    routeResult: state.mount.querySelector(UI_SELECTOR.routeResult),
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

  refs.openNewTag.textContent = newTagButtonLabel;
  refs.searchLabel.textContent = searchLabel;
  refs.search.setAttribute("placeholder", searchPlaceholder);
  refs.modalHost.innerHTML = renderTagRegistryModals(state);

  state.refs = {
    ...refs,
    ...collectTagRegistryModalRefs(state.mount)
  };
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
    if (!["tag", "documents", "updated"].includes(nextSortKey)) return;
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
    onPatchCopy: () => {
      void copyPatchSnippet(state);
    },
    onEditSave: () => {
      void withRouteBusy(state, () => handleTagEdit(state));
    },
    onEditGroupInput: () => setTagRegistryEditStatus(state, "", ""),
    onEditDocumentAdd: () => {
      const record = state.editTagPendingDocument;
      if (!state.editTagId || !record || state.editTagDocUrls.includes(record.url)) {
        return;
      }
      setTagRegistryDocumentLocation(state, record);
      state.editTagDocUrls = appendTagRegistryDocumentUrl(
        state.editTagDocUrls,
        record
      );
      state.editTagPendingDocument = null;
      state.refs.editDocumentSearch.value = "";
      renderTagRegistryEditDocuments(state);
      void state.documentPicker?.refresh?.();
      setTagRegistryEditStatus(state, "", "");
    },
    onEditDocumentDirectRemove: (url) => {
      if (!state.editTagDocUrls.includes(url)) return;
      state.editTagDocUrls = removeTagRegistryDocumentUrl(
        state.editTagDocUrls,
        url
      );
      renderTagRegistryEditDocuments(state);
      void state.documentPicker?.refresh?.();
      setTagRegistryEditStatus(state, "", "");
    },
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

function bindRegistryDocumentPicker(state) {
  state.documentPicker = bindDocumentLocationPicker(
    state.refs.editDocumentSearch,
    state.refs.editDocumentPopup,
    {
      scopeIds: ["analysis"],
      provider: state.documentLocationProvider,
      excludedUrls: () => state.editTagDocUrls,
      maxOptions: 500,
      persistent: true,
      showReport: false,
      onTransientInput: () => {
        state.editTagPendingDocument = null;
        renderTagRegistryEditDocuments(state);
      },
      onCommit: (record) => {
        if (!state.editTagId || state.editTagDocUrls.includes(record.url)) return;
        state.editTagPendingDocument = record;
        renderTagRegistryEditDocuments(state);
        setTagRegistryEditStatus(state, "", "");
      }
    }
  );
}

async function probeSaveMode(state) {
  await probeTagRouteSaveMode(state, {
    onRouteStateChange: () => syncRouteBusyState(state)
  });
}

async function loadRegistry(state, options = {}) {
  const [registryData, aliasesData] = await Promise.all([
    loadAnalyticsRegistryJson(state.config, options),
    loadAnalyticsAliasesJson(state.config, options)
  ]);
  const [assignmentsResult, seriesSearchResult] = await Promise.allSettled([
    loadAnalyticsAssignmentsJson(state.config, options),
    loadStudioSeriesSearchJson(state.config, options)
  ]);
  let groupsData;
  try {
    groupsData = await loadAnalyticsGroupsJson(state.config, options);
  } catch (error) {
    groupsData = null;
  }
  state.registryUpdatedAt = normalizeTimestamp(registryData && registryData.updated_at_utc);
  state.tags = normalizeRegistryTags(registryData, state.registryUpdatedAt);
  const documentLocations = await loadTagRegistryDocumentLocations(state.tags, {
    provider: state.documentLocationProvider
  });
  state.documentLocationsByUrl = documentLocations.locationsByUrl;
  state.documentLocationError = documentLocations.error;
  state.tags = attachTagRegistryDocuments(
    state.tags,
    state.documentLocationsByUrl
  );
  state.aliasKeys = buildAliasKeySet(aliasesData);
  state.assignmentsSeries = assignmentsResult.status === "fulfilled"
    ? getAnalyticsAssignmentsSeries(assignmentsResult.value)
    : {};
  state.seriesMetaById = seriesSearchResult.status === "fulfilled"
    ? buildTagRegistrySeriesMetaById(state.config, seriesSearchResult.value)
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
    clearRouteResult: () => clearRouteResult(state),
    setRouteResult: (kind, message) => setRouteResult(state, kind, message),
    syncRouteBusyState: () => syncRouteBusyState(state),
    refreshDeleteImpactPreview: () => refreshDeleteImpactPreview(state),
    renderControls: () => renderControls(state),
    renderList: () => renderList(state),
    applyPatchFallback: () => applyTagRegistryPatchFallback(state),
    openPatchModal: (snippet) => openPatchModal(state, snippet)
  };
}

function openEditModal(state, tagId) {
  openTagRegistryEditWorkflow(state, tagId, modalWorkflowOptions(state));
}

function openNewTagModal(state) {
  openTagRegistryNewWorkflow(state, modalWorkflowOptions(state));
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
  let result;
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
  state.refs.confirmDeleteTag.disabled = true;
  setTagRegistryDeleteImpactStatus(state, "error", result.message);
}

async function handleTagEdit(state) {
  if (!state.editTagId) return;
  const tagId = state.editTagId;
  const group = normalize(state.editTagGroup);
  const docUrl = state.editTagDocUrls.slice();
  const result = await saveTagRegistryEdit({
    saveMode: state.saveMode,
    tag: findTagById(state, tagId),
    group,
    docUrl,
    config: state.config
  });
  if (!result.ok) {
    setTagRegistryEditStatus(state, result.code === "no_changes" ? "" : "error", result.message);
    return;
  }

  applyTagRegistryEditResult(state, {
    tagId,
    group,
    docUrl,
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
    group: validation.group
  };

  const result = await createTagRegistryTag({
    saveMode: state.saveMode,
    newTagRow,
    config: state.config
  });
  if (result.ok && result.mode === "post") {
    await loadRegistry(state, { cache: "no-store" });
    applyTagRegistryCreatePostResult(state, {
      validation,
      result
    }, modalWorkflowOptions(state));
    return;
  }
  if (!result.ok && !result.switchToPatch) {
    setTagRegistryNewStatus(state, "error", result.message);
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
    if (result.code === "request_failed") {
      await refreshDeleteImpactPreview(state);
    }
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
    setRouteResult(state, "error", message);
    return;
  }

  const aliasKey = tag.tagId;
  if (state.aliasKeys.has(aliasKey)) {
    const message = registryText(
      state.config,
      "alias_exists_demote_error",
      "Alias already exists: {alias_key}. Demotion overwrite is not permitted.",
      { alias_key: aliasKey }
    );
    setTagRegistryDemoteStatus(state, "error", message);
    setRouteResult(state, "error", message);
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
      setRouteResult(state, "error", message);
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
      setRouteResult(state, "error", message);
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
      clearRouteResult(state);
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
    setRouteResult(state, "error", result.message);
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

function openPatchModal(state, snippet) {
  showTagRegistryPatchModal(state, snippet);
}

function setRouteResult(state, kind, message) {
  setTagRegistryRouteResult(state, kind, message);
}

function clearRouteResult(state) {
  clearTagRegistryRouteResult(state);
}

async function copyPatchSnippet(state) {
  if (!state.patchSnippet) return;
  try {
    await navigator.clipboard.writeText(state.patchSnippet);
    setRouteResult(state, "success", registryText(state.config, "patch_copy_success", "Patch snippet copied to clipboard."));
  } catch (error) {
    setRouteResult(state, "error", registryText(state.config, "patch_copy_failed", "Copy failed. Select and copy the snippet manually."));
  }
}

function registryText(config, key, fallback, tokens) {
  return getStudioText(config, `tag_registry.${key}`, fallback, tokens);
}

function renderError(state, message) {
  renderTagRegistryError(state, message);
}
