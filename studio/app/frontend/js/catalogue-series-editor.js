import {
  getStudioText
} from "./studio-config.js";
import { loadStudioLookupRecordJson } from "./studio-data.js";
import {
  configureCatalogueEditorRouteRuntime,
  initializeCatalogueEditorRoute,
  loadCatalogueEditorLookupMaps,
  revealCatalogueEditorRoute,
  setCatalogueEditorTextWithState as setNodeTextWithState,
  showCatalogueEditorInitError,
  syncCatalogueEditorRouteBusyState
} from "./catalogue-editor-route-boot.js";
import {
  catalogueDeleteDisabled,
  catalogueDirtyWarningText,
  catalogueDraftHasChanges,
  catalogueSaveDisabled
} from "./catalogue-editor-dirty-state.js";
import {
  SERIES_EDITABLE_FIELDS as EDITABLE_FIELDS,
  buildSeriesDraftFromRecord,
  getSeriesTypeOptions,
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId,
  suggestNextSeriesId,
  validateCreateSeriesDraft,
  validateSeriesDraft
} from "./catalogue-series-fields.js";
import {
  applySeriesDraftToInputs,
  getSeriesFieldNodeValue,
  refreshSeriesTypeOptions,
  renderSeriesEditorFields,
  setSeriesFieldNodeValue,
  setSeriesModeFieldAvailability
} from "./catalogue-series-form.js";
import {
  addSeriesMember,
  getCurrentSeriesMemberEntries,
  initializeSeriesMembershipState,
  makeSeriesMemberPrimary,
  removeSeriesMember,
  seriesMembershipHasChanges,
  updateSeriesMemberList
} from "./catalogue-series-membership.js";
import {
  applyPublicationChange,
  currentSeriesIsDraft,
  currentSeriesIsPublished,
  deleteCurrentSeries,
  refreshBuildPreview as refreshSeriesActionBuildPreview,
  saveCurrentSeries
} from "./catalogue-series-actions.js";
import {
  applyInitialSeriesRouteSelection,
  bindSeriesSelectionControls,
  openSeriesById as openSeriesSelectionById,
  setSeriesSelectionPopupVisibility
} from "./catalogue-series-selection.js";
import {
  renderSeriesPrimaryWorkPreview
} from "./catalogue-series-sections.js";
import {
  bindSeriesEditorEvents
} from "./catalogue-series-editor-events.js";
import {
  clearCatalogueFieldStatusMessages,
  createCatalogueEditorMessageController,
  firstCatalogueValidationMessage
} from "./catalogue-editor-message-controller.js";
import {
  SERIES_ROUTE_STATE,
  collectSeriesEditorElements,
  createSeriesEditorState
} from "./catalogue-series-editor-state.js";

function syncRouteBusyState(state) {
  syncCatalogueEditorRouteBusyState(state, SERIES_ROUTE_STATE);
}

function setOpenInputMode(state) {
  state.searchNode.placeholder = t(state, "search_placeholder", "find series by title");
  state.searchNode.setAttribute("aria-label", t(state, "search_label", "Find series by title"));
}

function setNewInputMode(state) {
  state.searchNode.placeholder = t(state, "new_series_id_placeholder", "new series id");
  state.searchNode.setAttribute("aria-label", t(state, "new_series_id_label", "New series id"));
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_series_editor.${key}`, fallback, tokens);
}

function membershipOptions(state) {
  return {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens),
    setTextWithState: setNodeTextWithState,
    setFieldNodeValue: setSeriesFieldNodeValue
  };
}

async function loadSeriesLookupRecord(state, seriesId) {
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_series_base", seriesId, {
    cache: "no-store",
    catalogueServerAvailable: state.serverAvailable
  });
}

function draftHasChanges(state) {
  return catalogueDraftHasChanges({
    mode: state.mode,
    fields: EDITABLE_FIELDS,
    draft: state.draft,
    baselineDraft: state.baselineDraft,
    extraComparisons: [
      {
        key: "members",
        changed: () => seriesMembershipHasChanges(state)
      }
    ]
  });
}

function validateDraft(state) {
  if (state.mode === "new") {
    return validateCreateSeriesDraft(
      { ...state.draft, series_id: state.searchNode.value },
      {
        seriesById: state.seriesById,
        seriesTypeOptions: state.seriesTypeOptions,
        t: (key, fallback, tokens = null) => t(state, key, fallback, tokens)
      }
    );
  }
  return validateSeriesDraft(state.draft, {
    currentMemberWorkIds: new Set(getCurrentSeriesMemberEntries(state).map((entry) => entry.workId)),
    t: (key, fallback, tokens = null) => t(state, key, fallback, tokens)
  });
}

function updatePublishControls(state, { hasRecord, dirty, errors }) {
  const canPublish = hasRecord && state.mode !== "new" && currentSeriesIsDraft(state);
  const canUnpublish = hasRecord && state.mode !== "new" && currentSeriesIsPublished(state);
  const label = canUnpublish
    ? t(state, "unpublish_button", "Unpublish")
    : t(state, "publish_button", "Publish");
  state.publicationButton.textContent = label;
  state.publicationButton.hidden = !(canPublish || canUnpublish);
  state.publicationButton.disabled = !(canPublish || canUnpublish)
    || (canPublish && dirty)
    || (canPublish && errors.size > 0)
    || state.isSaving
    || state.isBuilding
    || state.isDeleting
    || !state.serverAvailable;
}

function syncUrl(seriesId, mode = "") {
  const url = new URL(window.location.href);
  if (seriesId) url.searchParams.set("series", seriesId);
  else url.searchParams.delete("series");
  if (mode) url.searchParams.set("mode", mode);
  else url.searchParams.delete("mode");
  window.history.replaceState({}, "", url.toString());
}

function updateEditorState(state) {
  const hasRecord = state.mode === "new" ? true : Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  clearCatalogueFieldStatusMessages(state.fieldStatusNodes, setNodeTextWithState);
  setSeriesModeFieldAvailability(state);
  renderSeriesPrimaryWorkPreview(state, {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens)
  });
  updateSeriesMemberList(state, membershipOptions(state));
  const dirty = hasRecord && draftHasChanges(state);
  state.messageController.render({
    busy: state.isSaving || state.isBuilding || state.isDeleting,
    validationMessage: firstCatalogueValidationMessage(errors),
    dirtyMessage: catalogueDirtyWarningText({
      dirty,
      mode: state.mode,
      message: t(state, "dirty_warning", "Unsaved source changes.")
    })
  });

  state.saveButton.textContent = state.mode === "new"
    ? t(state, "create_button", "Create")
    : t(state, "save_button", "Save");
  state.saveButton.disabled = catalogueSaveDisabled({
    hasRecord,
    isSaving: state.isSaving,
    hasErrors: errors.size > 0,
    dirty,
    serverAvailable: state.serverAvailable
  });
  state.deleteButton.disabled = catalogueDeleteDisabled({
    hasRecord: Boolean(state.currentRecord),
    mode: state.mode,
    isSaving: state.isSaving,
    isBuilding: state.isBuilding,
    isDeleting: state.isDeleting,
    serverAvailable: state.serverAvailable
  });
  updatePublishControls(state, { hasRecord, dirty, errors });
  syncRouteBusyState(state);
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  state.messageController.clearActionMessages();
  if (state.mode === "new" && fieldKey === "status") {
    state.draft.status = "draft";
    setSeriesFieldNodeValue(node, "draft");
    updateEditorState(state);
    return;
  }
  if (state.mode === "new" && (fieldKey === "published_date" || fieldKey === "primary_work_id")) {
    state.draft[fieldKey] = "";
    setSeriesFieldNodeValue(node, "");
    updateEditorState(state);
    return;
  }
  state.draft[fieldKey] = getSeriesFieldNodeValue(node);
  updateEditorState(state);
}

function setLoadedSeries(state, seriesId, record, options = {}) {
  state.mode = "single";
  state.currentSeriesId = seriesId;
  state.currentRecord = record;
  state.currentLookup = options.lookup || state.currentLookup;
  state.currentRecordHash = normalizeText(options.recordHash || state.currentRecordHash);
  state.baselineDraft = buildSeriesDraftFromRecord(record);
  state.draft = { ...state.baselineDraft };
  initializeSeriesMembershipState(state, seriesId);
  applySeriesDraftToInputs(state);
  syncUrl(seriesId);
  state.memberSearchNode.value = "";
  state.memberAddNode.value = "";
  state.pendingBuildExtraWorkIds = Array.isArray(options.pendingBuildExtraWorkIds) ? options.pendingBuildExtraWorkIds.slice() : [];
  setNodeTextWithState(state.membersStatusNode, "");
  setOpenInputMode(state);
  state.messageController.setRouteTextWithState(state.contextNode, t(state, "context_loaded", "Editing source metadata for series {series_id}.", { series_id: seriesId }));
  state.messageController.setRouteTextWithState(state.statusNode, "");
  state.messageController.setRouteTextWithState(state.warningNode, "");
  if (!options.keepResult) state.messageController.setRouteTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function setNewSeriesMode(state, options = {}) {
  state.mode = "new";
  state.currentSeriesId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.baselineDraft = {};
  state.draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.draft.series_id = normalizeSeriesId(options.seriesId) || state.nextSuggestedSeriesId || suggestNextSeriesId(Array.from(state.seriesById.values()));
  state.draft.series_type = state.seriesTypeOptions[0] || "primary";
  state.draft.status = "draft";
  state.draft.published_date = "";
  state.draft.primary_work_id = "";
  state.memberSeriesIdsByWorkId = new Map();
  state.baselineMemberSeriesIdsByWorkId = new Map();
  state.pendingBuildExtraWorkIds = [];
  state.rebuildPending = false;
  state.buildPreview = null;
  state.searchNode.value = state.draft.series_id;
  setNewInputMode(state);
  applySeriesDraftToInputs(state);
  setSeriesSelectionPopupVisibility(state, false);
  syncUrl("", "new");
  state.memberSearchNode.value = "";
  state.memberAddNode.value = "";
  setNodeTextWithState(state.membersStatusNode, "");
  state.messageController.setRouteTextWithState(state.contextNode, t(state, "new_context_loaded", "Creating a draft series source record."));
  state.messageController.setRouteTextWithState(state.statusNode, "");
  state.messageController.setRouteTextWithState(state.warningNode, "");
  if (!options.keepResult) state.messageController.setRouteTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function setEmptySearchMode(state, options = {}) {
  state.mode = "single";
  state.currentSeriesId = "";
  state.currentRecord = null;
  state.currentLookup = null;
  state.currentRecordHash = "";
  state.baselineDraft = null;
  state.draft = {};
  EDITABLE_FIELDS.forEach((field) => {
    state.draft[field.key] = "";
  });
  state.memberSeriesIdsByWorkId = new Map();
  state.baselineMemberSeriesIdsByWorkId = new Map();
  state.pendingBuildExtraWorkIds = [];
  state.rebuildPending = false;
  state.buildPreview = null;
  setOpenInputMode(state);
  if (!options.keepSearchValue) state.searchNode.value = "";
  applySeriesDraftToInputs(state);
  setSeriesSelectionPopupVisibility(state, false);
  syncUrl("");
  state.memberSearchNode.value = "";
  state.memberAddNode.value = "";
  setNodeTextWithState(state.membersStatusNode, "");
  state.messageController.setRouteTextWithState(state.contextNode, t(state, "missing_series_param", "Search for a series by title."));
  state.messageController.setRouteTextWithState(state.warningNode, "");
  if (!options.keepResult) state.messageController.setRouteTextWithState(state.resultNode, "");
  updateEditorState(state);
}

function buildSeriesActionContext(state) {
  return {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens),
    setTextWithState: (node, text, tone) => state.messageController.setActionTextWithState(node, text, tone),
    draftHasChanges: () => draftHasChanges(state),
    validateDraft: () => validateDraft(state),
    updateFieldMessages: () => clearCatalogueFieldStatusMessages(state.fieldStatusNodes, setNodeTextWithState),
    updateEditorState: () => updateEditorState(state),
    syncRouteBusyState: () => syncRouteBusyState(state),
    renderReadiness: () => undefined,
    setLoadedSeries: (seriesId, record, options = {}) => {
      setLoadedSeries(state, seriesId, record, options);
    },
    openSeriesById: (seriesId) => openSeriesById(state, seriesId)
  };
}

function refreshBuildPreview(state) {
  return refreshSeriesActionBuildPreview(state, buildSeriesActionContext(state));
}

function buildSeriesSelectionContext(state) {
  return {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens),
    loadSeriesLookupRecord: (seriesId) => loadSeriesLookupRecord(state, seriesId),
    setLoadedSeries: (seriesId, record, options = {}) => {
      setLoadedSeries(state, seriesId, record, options);
    },
    refreshBuildPreview: () => refreshBuildPreview(state),
    updateEditorState: () => updateEditorState(state),
    saveCurrentSeries: () => saveCurrentSeries(state, buildSeriesActionContext(state)),
    setEmptySearchMode: (options = {}) => setEmptySearchMode(state, options),
    setNewSeriesMode: (options = {}) => setNewSeriesMode(state, options),
    setTextWithState: (node, text, tone) => state.messageController.setActionTextWithState(node, text, tone)
  };
}

function openSeriesById(state, requestedSeriesId) {
  return openSeriesSelectionById(state, requestedSeriesId, buildSeriesSelectionContext(state));
}

async function init() {
  const elements = collectSeriesEditorElements();
  if (!elements) return;
  const {
    root,
    loadingNode,
    fieldsNode,
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    newButton,
    saveButton,
    publicationButton,
    deleteButton,
    membersHeadingNode,
    memberSearchRowNode,
    memberSearchNode,
    memberSearchMetaNode,
    memberAddNode,
    memberAddButton,
    membersMetaNode,
    membersStatusNode,
    membersResultsNode
  } = elements;

  const state = createSeriesEditorState(elements);
  state.messageController = createCatalogueEditorMessageController({
    statusNode: state.statusNode,
    setTextWithState: setNodeTextWithState
  });
  initializeCatalogueEditorRoute(root, "catalogue-series");

  renderSeriesEditorFields(fieldsNode, state, {
    text: (key, fallback, tokens = null) => t(state, key, fallback, tokens),
    onFieldInput: (fieldKey) => onFieldInput(state, fieldKey)
  });
  try {
    await configureCatalogueEditorRouteRuntime(state, {
      namespace: "catalogue_series_editor",
      applyText: (config) => {
        state.seriesTypeOptions = getSeriesTypeOptions();
        refreshSeriesTypeOptions(state);
        searchNode.placeholder = t(state, "search_placeholder", "find series by title");
        openButton.textContent = t(state, "open_button", "Open");
        newButton.textContent = t(state, "new_button", "New");
        saveButton.textContent = t(state, "save_button", "Save");
        publicationButton.textContent = t(state, "publish_button", "Publish");
        deleteButton.textContent = t(state, "delete_button", "Delete");
        membersHeadingNode.textContent = t(state, "members_heading", "member works");
        memberSearchNode.placeholder = t(state, "members_search_placeholder", "find member work by id");
        memberAddNode.placeholder = t(state, "members_add_placeholder", "add work by id");
        memberAddButton.textContent = t(state, "members_add_button", "Add");
      }
    });
    if (!state.serverAvailable) {
      updateEditorState(state);
      revealCatalogueEditorRoute(state, {
        loadingNode,
        routeState: SERIES_ROUTE_STATE
      });
      return;
    }

    await loadCatalogueEditorLookupMaps(state, [
      {
        configKey: "catalogue_lookup_series_search",
        target: state.seriesById,
        normalizeKey: (record) => normalizeSeriesId(record.series_id),
        afterItems: (items) => {
          state.nextSuggestedSeriesId = suggestNextSeriesId(items);
        }
      },
      {
        configKey: "catalogue_lookup_work_search",
        target: state.workSearchById,
        normalizeKey: (record) => normalizeWorkId(record.work_id)
      }
    ]);
    bindSeriesEditorEvents(state, {
      bindSelectionControls: () => bindSeriesSelectionControls(state, buildSeriesSelectionContext(state)),
      setNewSeriesMode: () => setNewSeriesMode(state),
      saveCurrentSeries: () => saveCurrentSeries(state, buildSeriesActionContext(state)),
      applyPublicationChange: () => applyPublicationChange(state, buildSeriesActionContext(state)),
      deleteCurrentSeries: () => deleteCurrentSeries(state, buildSeriesActionContext(state)),
      updateMemberList: () => updateSeriesMemberList(state, membershipOptions(state)),
      addMember: () => {
        if (addSeriesMember(state, membershipOptions(state))) {
          state.messageController.clearActionMessages();
          updateEditorState(state);
        }
      },
      makeMemberPrimary: (workId) => {
        if (makeSeriesMemberPrimary(state, normalizeWorkId(workId))) {
          state.messageController.clearActionMessages();
          updateEditorState(state);
        }
      },
      removeMember: (workId) => {
        if (removeSeriesMember(state, normalizeWorkId(workId), membershipOptions(state))) {
          state.messageController.clearActionMessages();
          updateEditorState(state);
        }
      }
    });

    await applyInitialSeriesRouteSelection(state, buildSeriesSelectionContext(state));

    revealCatalogueEditorRoute(state, {
      loadingNode,
      routeState: SERIES_ROUTE_STATE
    });
  } catch (error) {
    console.warn("catalogue_series_editor: init failed", error);
    await showCatalogueEditorInitError(
      loadingNode,
      "catalogue_series_editor",
      "Failed to load catalogue source data for the series editor."
    );
  }
}

init();
