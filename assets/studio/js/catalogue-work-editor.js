import {
  getStudioText
} from "./studio-config.js";
import {
  loadStudioLookupRecordJson
} from "./studio-data.js";
import {
  collectRequiredElements,
  configureCatalogueEditorRouteRuntime,
  createCatalogueEditorRouteStateOptions,
  loadCatalogueEditorLookupMaps,
  revealCatalogueEditorRoute,
  setCatalogueEditorTextWithState as setTextWithState,
  showCatalogueEditorInitError
} from "./catalogue-editor-route-boot.js";
import {
  catalogueDeleteDisabled,
  catalogueDirtyWarningText,
  catalogueDraftChangedFieldNames,
  catalogueDraftHasChanges,
  catalogueSaveDisabled
} from "./catalogue-editor-dirty-state.js";
import {
  WORK_DOWNLOAD_FIELDS as DOWNLOAD_FIELDS,
  WORK_LINK_FIELDS as LINK_FIELDS,
  validateWorkEmbeddedItems
} from "./catalogue-editor-embedded-items.js";
import {
  confirmWorkEmbeddedDeleteModal,
  openWorkBuildPreviewModal,
  openWorkEmbeddedEntryModal
} from "./catalogue-work-editor-modals.js";
import {
  renderWorkCurrentPreview,
  renderWorkReadiness,
  updateWorkDetailSections,
  updateWorkSummary
} from "./catalogue-work-sections.js";
import {
  applyDraftToInputs,
  applyReadonly,
  applyWorkFormText,
  clearReadonlyFields,
  getFieldNodeValue,
  renderWorkEditorFields,
  setFieldNodeValue,
  setModeFieldAvailability,
  updateFieldMessages
} from "./catalogue-work-form.js";
import {
  initializeWorkRouteState,
  setEmptySearchMode,
  setLoadedBulkWorks,
  setLoadedWorkRecord,
  setNewWorkMode,
  syncWorkRouteBusyState
} from "./catalogue-work-route-state.js";
import {
  applyPublicationChange,
  bulkPublishedBuildTargets,
  bulkSelectionHasPublishedRecords,
  currentWorkIsDraft,
  currentWorkIsPublished,
  deleteCurrentWork,
  importWorkProse,
  parseBulkSeriesOperation,
  previewCurrentBuildImpact,
  refreshBuildPreview,
  refreshWorkMedia,
  saveCurrentWork
} from "./catalogue-work-actions.js";
import {
  applyInitialWorkRouteSelection,
  bindWorkSelectionControls,
  openWorkById,
  setWorkSelectionPopupVisibility
} from "./catalogue-work-selection.js";
import {
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";
import {
  createStudioModalHost
} from "./studio-modal.js";
import {
  WORK_DATE_RE as DATE_RE,
  WORK_DIMENSION_FIELD_KEYS,
  WORK_EDITABLE_FIELDS as EDITABLE_FIELDS,
  WORK_SERIES_ID_RE as SERIES_ID_RE,
  WORK_STATUS_OPTIONS as STATUS_OPTIONS,
  canonicalizeWorkScalar as canonicalizeScalar,
  embeddedEntriesEqual,
  normalizeSeriesId,
  normalizeText,
  normalizeWorkId,
  parseSeriesIds,
  suggestNextWorkId
} from "./catalogue-work-fields.js";

const REQUIRED_WORK_FIELDS = ["title", "year", "year_display", "series_ids"];
const WORK_ROUTE_STATE = createCatalogueEditorRouteStateOptions({
  route: "catalogue-work",
  bulkIdsKey: "bulkWorkIds",
  busyKeys: ["isSaving", "isBuilding", "isPreviewingBuild", "isDeleting"]
});

function changedWorkFieldNames(state) {
  if (state.mode !== "single" || !state.baselineDraft) return [];
  return catalogueDraftChangedFieldNames({
    fields: EDITABLE_FIELDS,
    draft: state.draft,
    baselineDraft: state.baselineDraft,
    canonicalizeScalar,
    extraComparisons: [
      {
        key: "downloads",
        changed: ({ draft, baselineDraft }) => !embeddedEntriesEqual(draft.downloads, baselineDraft.downloads, DOWNLOAD_FIELDS)
      },
      {
        key: "links",
        changed: ({ draft, baselineDraft }) => !embeddedEntriesEqual(draft.links, baselineDraft.links, LINK_FIELDS)
      }
    ]
  });
}

function setOpenInputMode(state) {
  state.searchNode.placeholder = t(state, "search_placeholder", "find work id(s): 00001, 00003-00005");
  state.searchNode.setAttribute("aria-label", t(state, "search_label", "Find work by id"));
}

async function loadWorkLookupRecord(state, workId) {
  return loadStudioLookupRecordJson(state.config, "catalogue_lookup_work_base", workId, {
    cache: "no-store",
    catalogueServerAvailable: state.serverAvailable
  });
}

async function openEmbeddedEntryModal(state, kind, index = null) {
  const result = await openWorkEmbeddedEntryModal(state, kind, index, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  });
  if (!result || !result.confirmed) return;
  state.draft[result.entriesKey] = result.entries;
  updateEditorState(state);
}

async function deleteEmbeddedEntry(state, kind, index) {
  const result = await confirmWorkEmbeddedDeleteModal(state, kind, index, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  });
  if (!result || !result.confirmed) return;
  state.draft[result.entriesKey] = result.entries;
  updateEditorState(state);
}

function openBuildPreviewModal(state, response, changedFields) {
  openWorkBuildPreviewModal(state, response, changedFields, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  });
}

function draftHasChanges(state) {
  return catalogueDraftHasChanges({
    mode: state.mode,
    fields: EDITABLE_FIELDS,
    draft: state.draft,
    baselineDraft: state.baselineDraft,
    touchedFields: state.bulkTouchedFields,
    canonicalizeScalar,
    newModeChanged: () => Boolean(
      normalizeWorkId(state.draft.work_id) ||
      EDITABLE_FIELDS.some((field) => normalizeText(state.draft[field.key]))
    ),
    extraComparisons: [
      {
        key: "downloads",
        changed: ({ draft, baselineDraft }) => !embeddedEntriesEqual(draft.downloads, baselineDraft.downloads, DOWNLOAD_FIELDS)
      },
      {
        key: "links",
        changed: ({ draft, baselineDraft }) => !embeddedEntriesEqual(draft.links, baselineDraft.links, LINK_FIELDS)
      }
    ]
  });
}

function validateDraft(state) {
  if (state.mode === "new") {
    const errors = new Map();
    const workId = normalizeWorkId(state.draft.work_id);
    if (!workId) {
      errors.set("work_id", t(state, "field_required_work_id", "Enter a work id."));
    } else if (state.workSearchById.has(workId) || state.sourceWorkRecordsById.has(workId)) {
      errors.set("work_id", t(state, "field_duplicate_work_id", "Work id already exists."));
    }

    REQUIRED_WORK_FIELDS.forEach((fieldKey) => {
      if (fieldKey === "series_ids") {
        if (!parseSeriesIds(state.draft.series_ids).length) {
          errors.set("series_ids", t(state, "field_required_series_ids", "Enter at least one series id."));
        }
        return;
      }
      if (!normalizeText(state.draft[fieldKey])) {
        const label = fieldKey.replace(/_/g, " ");
        errors.set(fieldKey, t(state, `field_required_${fieldKey}`, "Enter {field}.", { field: label }));
      }
    });

    const year = normalizeText(state.draft.year);
    if (year && !/^-?\d+$/.test(year)) {
      errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
    }

    WORK_DIMENSION_FIELD_KEYS.forEach((fieldKey) => {
      const value = normalizeText(state.draft[fieldKey]);
      if (value && !Number.isFinite(Number(value))) {
        errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));
      }
    });

    const seriesText = normalizeText(state.draft.series_ids);
    if (seriesText) {
      const parts = seriesText.split(",").map((item) => normalizeText(item)).filter(Boolean);
      for (const part of parts) {
        if (!SERIES_ID_RE.test(part)) {
          errors.set("series_ids", t(state, "field_invalid_series_id", "Use comma-separated numeric series ids."));
          break;
        }
        const normalizedId = normalizeSeriesId(part);
        if (!state.seriesById.has(normalizedId)) {
          errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {series_id}.", { series_id: normalizedId }));
          break;
        }
      }
    }
    return errors;
  }

  if (state.mode === "bulk") {
    const errors = new Map();
    if (state.bulkTouchedFields.has("status")) {
      const status = normalizeText(state.draft.status).toLowerCase();
      if (!STATUS_OPTIONS.has(status)) {
        errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
      }
    }

    if (state.bulkTouchedFields.has("published_date")) {
      const publishedDate = normalizeText(state.draft.published_date);
      if (publishedDate && !DATE_RE.test(publishedDate)) {
        errors.set("published_date", t(state, "field_invalid_date", "Use YYYY-MM-DD or leave blank."));
      }
    }

    if (state.bulkTouchedFields.has("year")) {
      const year = normalizeText(state.draft.year);
      if (year && !/^-?\d+$/.test(year)) {
        errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
      }
    }

    WORK_DIMENSION_FIELD_KEYS.forEach((fieldKey) => {
      if (!state.bulkTouchedFields.has(fieldKey)) return;
      const value = normalizeText(state.draft[fieldKey]);
      if (value && !Number.isFinite(Number(value))) {
        errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));
      }
    });

    if (state.bulkTouchedFields.has("series_ids")) {
      try {
        const operation = parseBulkSeriesOperation(state.draft.series_ids);
        const seriesIds = operation.mode === "replace"
          ? operation.series_ids
          : [...operation.add_series_ids, ...operation.remove_series_ids];
        for (const seriesId of seriesIds) {
          if (!state.seriesById.has(seriesId)) {
            errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {series_id}.", { series_id: seriesId }));
            break;
          }
        }
      } catch (error) {
        errors.set(
          "series_ids",
          normalizeText(error && error.message) || t(state, "field_invalid_series_id", "Use comma-separated numeric series ids.")
        );
      }
    }

    return errors;
  }

  const errors = new Map();
  const status = normalizeText(state.draft.status).toLowerCase();
  if (!STATUS_OPTIONS.has(status)) {
    errors.set("status", t(state, "field_invalid_status", "Use blank, draft, or published."));
  }

  const publishedDate = normalizeText(state.draft.published_date);
  if (publishedDate && !DATE_RE.test(publishedDate)) {
    errors.set("published_date", t(state, "field_invalid_date", "Use YYYY-MM-DD or leave blank."));
  }

  const year = normalizeText(state.draft.year);
  if (year && !/^-?\d+$/.test(year)) {
    errors.set("year", t(state, "field_invalid_year", "Use a whole year or leave blank."));
  }

  WORK_DIMENSION_FIELD_KEYS.forEach((fieldKey) => {
    const value = normalizeText(state.draft[fieldKey]);
    if (value && !Number.isFinite(Number(value))) {
      errors.set(fieldKey, t(state, "field_invalid_number", "Use a number or leave blank."));
    }
  });

  const seriesText = normalizeText(state.draft.series_ids);
  if (seriesText) {
    const parts = seriesText.split(",").map((item) => normalizeText(item)).filter(Boolean);
    for (const part of parts) {
      if (!SERIES_ID_RE.test(part)) {
        errors.set("series_ids", t(state, "field_invalid_series_id", "Use comma-separated numeric series ids."));
        break;
      }
      const normalizedId = normalizeSeriesId(part);
      if (!state.seriesById.has(normalizedId)) {
        errors.set("series_ids", t(state, "field_unknown_series_id", "Unknown series id: {series_id}.", { series_id: normalizedId }));
        break;
      }
    }
  }

  validateWorkEmbeddedItems(state.draft, {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens)
  }).forEach((message, key) => {
    errors.set(key, message);
  });

  return errors;
}

function updatePublishControls(state, { hasRecord, dirty, errors }) {
  const canPublish = state.mode === "single" && hasRecord && currentWorkIsDraft(state);
  const canUnpublish = state.mode === "single" && hasRecord && currentWorkIsPublished(state);
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

function updateEditorState(state) {
  const hasRecord = state.mode === "new" ? true : state.mode === "bulk" ? state.bulkWorkIds.length > 0 : Boolean(state.currentRecord);
  const errors = hasRecord ? validateDraft(state) : new Map();
  state.validationErrors = errors;
  updateFieldMessages(state, errors, workFormOptions(state));
  setModeFieldAvailability(state);
  updateSummary(state);
  if (!hasRecord) {
    setTextWithState(state.buildImpactNode, "");
  } else if (state.mode === "bulk") {
    const previewTargets = state.rebuildPending && state.bulkBuildTargets.length
      ? state.bulkBuildTargets
      : bulkPublishedBuildTargets(state);
    setTextWithState(
      state.buildImpactNode,
      t(state, "bulk_build_preview", "Public update preview: {count} published work scope(s) will be updated.", {
        count: String(previewTargets.length)
      })
    );
  }

  const dirty = hasRecord && draftHasChanges(state);
  setTextWithState(state.warningNode, catalogueDirtyWarningText({
    dirty,
    mode: state.mode,
    message: t(state, "dirty_warning", "Unsaved source changes.")
  }));
  if (state.mode === "new" && !state.resultNode.textContent) {
    setTextWithState(
      state.statusNode,
      state.serverAvailable ? "" : t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."),
      state.serverAvailable ? "" : "warn"
    );
  } else if (!dirty && !errors.size && !state.resultNode.textContent && hasRecord) {
    setTextWithState(
      state.statusNode,
      state.mode === "bulk"
        ? t(state, "bulk_status_loaded", "Loaded {count} work records.", { count: String(state.bulkWorkIds.length) })
        : t(state, "save_status_loaded", "Loaded work {work_id}.", { work_id: state.currentWorkId })
    );
  }

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
  renderReadiness(state);
  syncWorkRouteBusyState(state);
}

function onFieldInput(state, fieldKey) {
  const node = state.fieldNodes.get(fieldKey);
  if (!node) return;
  if (state.mode === "new" && fieldKey === "status") {
    state.draft.status = "draft";
    setFieldNodeValue(node, "draft");
    updateEditorState(state);
    return;
  }
  if (state.mode === "new" && fieldKey === "published_date") {
    state.draft.published_date = "";
    setFieldNodeValue(node, "");
    updateEditorState(state);
    return;
  }
  state.draft[fieldKey] = getFieldNodeValue(node);
  if (state.mode === "bulk") {
    state.bulkTouchedFields.add(fieldKey);
  }
  updateEditorState(state);
}

function t(state, key, fallback, tokens = null) {
  return getStudioText(state.config, `catalogue_work_editor.${key}`, fallback, tokens);
}

function workFormOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    onFieldInput: (fieldKey) => onFieldInput(state, fieldKey),
    onStateChange: () => updateEditorState(state)
  };
}

function workRouteStateOptions(state, overrides = {}) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState,
    setOpenInputMode: () => setOpenInputMode(state),
    setPopupVisibility: (visible) => setWorkSelectionPopupVisibility(state, visible),
    applyDraftToInputs: () => applyDraftToInputs(state, workFormOptions(state)),
    applyReadonly: () => applyReadonly(state),
    clearReadonlyFields: () => clearReadonlyFields(state),
    updateEditorState: () => updateEditorState(state),
    ...overrides
  };
}

function workSelectionOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    loadWorkLookupRecord: (workId) => loadWorkLookupRecord(state, workId),
    setLoadedBulkWorks: (workIds, recordsById, recordHashes) => {
      setLoadedBulkWorks(state, workIds, recordsById, recordHashes, workRouteStateOptions(state));
    },
    setLoadedWorkRecord: (workId, record, options = {}) => {
      setLoadedWorkRecord(state, workId, record, workRouteStateOptions(state, options));
    },
    refreshBuildPreview: () => refreshBuildPreview(state, workActionOptions(state)),
    updateEditorState: () => updateEditorState(state),
    saveCurrentWork: () => saveCurrentWork(state, workActionOptions(state)),
    setTextWithState,
    setEmptySearchMode: (overrides = {}) => setEmptySearchMode(state, workRouteStateOptions(state, overrides)),
    setNewWorkMode: () => setNewWorkMode(state, workRouteStateOptions(state))
  };
}

function workActionOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    setTextWithState,
    validateDraft: () => validateDraft(state),
    updateFieldMessages: (errors) => updateFieldMessages(state, errors, workFormOptions(state)),
    draftHasChanges: () => draftHasChanges(state),
    changedWorkFieldNames: () => changedWorkFieldNames(state),
    updateEditorState: () => updateEditorState(state),
    loadWorkLookupRecord: (workId) => loadWorkLookupRecord(state, workId),
    workRouteStateOptions: (overrides = {}) => workRouteStateOptions(state, overrides),
    renderCurrentPreview: () => renderCurrentPreview(state),
    renderReadiness: () => renderReadiness(state),
    openBuildPreviewModal: (response, changedFields) => openBuildPreviewModal(state, response, changedFields),
    openWorkById: (workId) => openWorkById(state, workId, workSelectionOptions(state))
  };
}

function workSectionOptions(state) {
  return {
    text: (key, fallback, tokens) => t(state, key, fallback, tokens),
    changedWorkFieldNames,
    draftHasChanges,
    isCurrentWorkPublished: currentWorkIsPublished,
    onPreviewBuildImpact: () => previewCurrentBuildImpact(state, workActionOptions(state)),
    setTextWithState
  };
}

function renderCurrentPreview(state) {
  renderWorkCurrentPreview(state, workSectionOptions(state));
}

function renderReadiness(state) {
  renderWorkReadiness(state, workSectionOptions(state));
}

function updateDetailSections(state) {
  updateWorkDetailSections(state, workSectionOptions(state));
}

function updateSummary(state) {
  updateWorkSummary(state, workSectionOptions(state));
}

function collectWorkEditorElements() {
  return collectRequiredElements({
    root: "catalogueWorkRoot",
    loadingNode: "catalogueWorkLoading",
    emptyNode: "catalogueWorkEmpty",
    fieldsNode: "catalogueWorkFields",
    readonlyNode: "catalogueWorkReadonly",
    previewNode: "catalogueWorkPreview",
    summaryNode: "catalogueWorkSummary",
    readinessNode: "catalogueWorkReadiness",
    runtimeStateNode: "catalogueWorkRuntimeState",
    buildImpactNode: "catalogueWorkBuildImpact",
    detailsHeadingNode: "catalogueWorkDetailsHeading",
    newDetailLinkNode: "catalogueWorkNewDetailLink",
    detailSearchRowNode: "catalogueWorkDetailsSearchRow",
    detailSearchNode: "catalogueWorkDetailSearch",
    detailsMetaNode: "catalogueWorkDetailsMeta",
    detailsResultsNode: "catalogueWorkDetailsResults",
    filesHeadingNode: "catalogueWorkFilesHeading",
    newFileLinkNode: "catalogueWorkNewFileLink",
    filesMetaNode: "catalogueWorkFilesMeta",
    filesResultsNode: "catalogueWorkFilesResults",
    linksHeadingNode: "catalogueWorkLinksHeading",
    newLinkLinkNode: "catalogueWorkNewLinkLink",
    linksMetaNode: "catalogueWorkLinksMeta",
    linksResultsNode: "catalogueWorkLinksResults",
    searchNode: "catalogueWorkSearch",
    popupNode: "catalogueWorkPopup",
    popupListNode: "catalogueWorkPopupList",
    openButton: "catalogueWorkOpen",
    newButton: "catalogueWorkNew",
    saveButton: "catalogueWorkSave",
    publicationButton: "catalogueWorkPublication",
    deleteButton: "catalogueWorkDelete",
    saveModeNode: "catalogueWorkSaveMode",
    contextNode: "catalogueWorkContext",
    statusNode: "catalogueWorkStatus",
    warningNode: "catalogueWorkWarning",
    resultNode: "catalogueWorkResult",
    metaNode: "catalogueWorkMeta"
  });
}

function createWorkEditorState(elements) {
  const {
    root,
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    newButton,
    saveButton,
    publicationButton,
    deleteButton,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    previewNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    detailSearchRowNode,
    detailSearchNode,
    detailsMetaNode,
    detailsResultsNode,
    newDetailLinkNode,
    filesMetaNode,
    filesResultsNode,
    newFileLinkNode,
    linksMetaNode,
    linksResultsNode,
    newLinkLinkNode,
    metaNode
  } = elements;

  return {
    root,
    config: null,
    mode: "single",
    workSearchById: new Map(),
    seriesById: new Map(),
    sourceWorkRecordsById: new Map(),
    currentLookup: null,
    currentWorkId: "",
    currentRecord: null,
    currentRecordHash: "",
    nextSuggestedWorkId: "",
    bulkWorkIds: [],
    bulkRecords: new Map(),
    bulkRecordHashes: new Map(),
    bulkMixedFields: new Set(),
    bulkTouchedFields: new Set(),
    bulkBuildTargets: [],
    baselineDraft: null,
    draft: {},
    validationErrors: new Map(),
    mediaConfig: loadCatalogueMediaConfig(root),
    rebuildPending: false,
    pendingBuildExtraSeriesIds: [],
    buildPreview: null,
    isSaving: false,
    isBuilding: false,
    isPreviewingBuild: false,
    isDeleting: false,
    serverAvailable: false,
    modalHost: createStudioModalHost({ root }),
    activeModalController: null,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    newButton,
    saveButton,
    publicationButton,
    deleteButton,
    saveModeNode,
    contextNode,
    statusNode,
    warningNode,
    resultNode,
    previewNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    detailSearchRowNode,
    detailSearchNode,
    detailsMetaNode,
    detailsResultsNode,
    detailsPanelNode: detailsResultsNode.closest("section"),
    newDetailLinkNode,
    filesMetaNode,
    filesResultsNode,
    filesPanelNode: filesResultsNode.closest("section"),
    newFileLinkNode,
    linksMetaNode,
    linksResultsNode,
    linksPanelNode: linksResultsNode.closest("section"),
    newLinkLinkNode,
    metaNode
  };
}

function applyWorkEditorText(state, elements) {
  setOpenInputMode(state);
  applyWorkFormText(state, workFormOptions(state));
  elements.detailsHeadingNode.textContent = t(state, "details_heading", "work details");
  elements.newDetailLinkNode.textContent = t(state, "details_new_link", "new work detail →");
  elements.detailSearchNode.placeholder = t(state, "details_search_placeholder", "find detail by id");
  elements.filesHeadingNode.textContent = t(state, "files_heading", "downloads");
  elements.newFileLinkNode.textContent = t(state, "files_add_button", "Add file");
  elements.linksHeadingNode.textContent = t(state, "links_heading", "links");
  elements.newLinkLinkNode.textContent = t(state, "links_add_button", "Add link");
  elements.openButton.textContent = t(state, "open_button", "Open");
  elements.newButton.textContent = t(state, "new_button", "New");
  elements.saveButton.textContent = t(state, "save_button", "Save");
  elements.publicationButton.textContent = t(state, "publish_button", "Publish");
  elements.deleteButton.textContent = t(state, "delete_button", "Delete");
}

async function configureWorkEditorRuntime(state, elements) {
  return configureCatalogueEditorRouteRuntime(state, {
    namespace: "catalogue_work_editor",
    saveModeNode: state.saveModeNode,
    applyText: () => applyWorkEditorText(state, elements)
  });
}

async function loadInitialWorkEditorData(state) {
  await loadCatalogueEditorLookupMaps(state, [
    {
      configKey: "catalogue_lookup_work_search",
      target: state.workSearchById,
      normalizeKey: (record) => normalizeWorkId(record.work_id),
      afterItems: (items) => {
        state.nextSuggestedWorkId = suggestNextWorkId(items);
      }
    },
    {
      configKey: "catalogue_lookup_series_search",
      target: state.seriesById,
      normalizeKey: (record) => normalizeSeriesId(record.series_id)
    }
  ]);
}

function bindWorkEditorEvents(state) {
  bindWorkSelectionControls(state, workSelectionOptions(state));

  state.detailSearchNode.addEventListener("input", () => {
    updateDetailSections(state);
  });

  state.newFileLinkNode.addEventListener("click", () => {
    openEmbeddedEntryModal(state, "download").catch((error) => {
      console.warn("catalogue_work_editor: failed to open download modal", error);
    });
  });
  state.newLinkLinkNode.addEventListener("click", () => {
    openEmbeddedEntryModal(state, "link").catch((error) => {
      console.warn("catalogue_work_editor: failed to open link modal", error);
    });
  });

  state.filesResultsNode.addEventListener("click", (event) => {
    const editButton = event.target && event.target.closest ? event.target.closest("[data-download-edit]") : null;
    if (editButton) {
      openEmbeddedEntryModal(state, "download", Number(editButton.getAttribute("data-download-edit"))).catch((error) => {
        console.warn("catalogue_work_editor: failed to edit download", error);
      });
      return;
    }
    const deleteButtonNode = event.target && event.target.closest ? event.target.closest("[data-download-delete]") : null;
    if (deleteButtonNode) {
      deleteEmbeddedEntry(state, "download", Number(deleteButtonNode.getAttribute("data-download-delete"))).catch((error) => {
        console.warn("catalogue_work_editor: failed to delete download", error);
      });
    }
  });

  state.linksResultsNode.addEventListener("click", (event) => {
    const editButton = event.target && event.target.closest ? event.target.closest("[data-link-edit]") : null;
    if (editButton) {
      openEmbeddedEntryModal(state, "link", Number(editButton.getAttribute("data-link-edit"))).catch((error) => {
        console.warn("catalogue_work_editor: failed to edit link", error);
      });
      return;
    }
    const deleteButtonNode = event.target && event.target.closest ? event.target.closest("[data-link-delete]") : null;
    if (deleteButtonNode) {
      deleteEmbeddedEntry(state, "link", Number(deleteButtonNode.getAttribute("data-link-delete"))).catch((error) => {
        console.warn("catalogue_work_editor: failed to delete link", error);
      });
    }
  });

  state.newButton.addEventListener("click", () => {
    setNewWorkMode(state, workRouteStateOptions(state));
  });
  state.readinessNode.addEventListener("click", (event) => {
    const mediaButton = event.target && event.target.closest ? event.target.closest("[data-media-refresh]") : null;
    if (mediaButton) {
      refreshWorkMedia(state, workActionOptions(state)).catch((error) => {
        console.warn("catalogue_work_editor: unexpected media refresh failure", error);
      });
      return;
    }
    const proseButton = event.target && event.target.closest ? event.target.closest("[data-prose-import]") : null;
    if (!proseButton) return;
    importWorkProse(state, workActionOptions(state)).catch((error) => {
      console.warn("catalogue_work_editor: unexpected prose import failure", error);
    });
  });
  state.saveButton.addEventListener("click", () => saveCurrentWork(state, workActionOptions(state)).catch((error) => {
    console.warn("catalogue_work_editor: unexpected save failure", error);
  }));
  state.publicationButton.addEventListener("click", () => applyPublicationChange(state, workActionOptions(state)).catch((error) => {
    console.warn("catalogue_work_editor: unexpected publication failure", error);
  }));
  state.deleteButton.addEventListener("click", () => deleteCurrentWork(state, workActionOptions(state)).catch((error) => {
    console.warn("catalogue_work_editor: unexpected delete failure", error);
  }));

}

function markWorkEditorLoaded(state, elements) {
  revealCatalogueEditorRoute(state, {
    loadingNode: elements.loadingNode,
    routeState: WORK_ROUTE_STATE
  });
}

async function init() {
  const elements = collectWorkEditorElements();
  if (!elements) return;

  initializeWorkRouteState(elements.root);
  const state = createWorkEditorState(elements);
  renderWorkEditorFields(state, elements, workFormOptions(state));

  try {
    const serverAvailable = await configureWorkEditorRuntime(state, elements);
    if (!serverAvailable) {
      setTextWithState(state.statusNode, t(state, "save_mode_unavailable_hint", "Local catalogue server unavailable. Save is disabled."), "warn");
      updateEditorState(state);
      markWorkEditorLoaded(state, elements);
      return;
    }

    await loadInitialWorkEditorData(state);
    bindWorkEditorEvents(state);
    await applyInitialWorkRouteSelection(state, workSelectionOptions(state));
    markWorkEditorLoaded(state, elements);
  } catch (error) {
    console.warn("catalogue_work_editor: init failed", error);
    await showCatalogueEditorInitError(
      elements.loadingNode,
      "catalogue_work_editor",
      "Failed to load catalogue source data for the work editor."
    );
  }
}

init();
