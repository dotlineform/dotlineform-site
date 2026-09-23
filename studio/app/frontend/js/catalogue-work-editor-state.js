import {
  collectRequiredElements,
  createCatalogueEditorRouteStateOptions
} from "./catalogue-editor-route-boot.js";
import {
  createCatalogueEditorMessageRoleNode
} from "./catalogue-editor-message-controller.js";
import {
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";
import {
  createStudioModalHost
} from "./studio-modal.js";

export const WORK_ROUTE_STATE = createCatalogueEditorRouteStateOptions({
  route: "catalogue-work",
  bulkIdsKey: "bulkWorkIds",
  busyKeys: ["isSaving", "isBuilding", "isDeleting"]
});

export function collectWorkEditorElements() {
  return collectRequiredElements({
    root: "catalogueWorkRoot",
    loadingNode: "catalogueWorkLoading",
    emptyNode: "catalogueWorkEmpty",
    fieldsNode: "catalogueWorkFields",
    readonlyNode: "catalogueWorkReadonly",
    previewNode: "catalogueWorkPreview",
    summaryPanelNode: "catalogueWorkSummaryPanel",
    summaryNode: "catalogueWorkSummary",
    readinessNode: "catalogueWorkReadiness",
    runtimeStateNode: "catalogueWorkRuntimeState",
    buildImpactNode: "catalogueWorkBuildImpact",
    resourcesPanelNode: "catalogueWorkResourcesPanel",
    resourcesActionsNode: "catalogueWorkResourcesActions",
    resourcesMetaNode: "catalogueWorkResourcesMeta",
    resourcesResultsNode: "catalogueWorkResourcesResults",
    searchNode: "catalogueWorkSearch",
    popupNode: "catalogueWorkPopup",
    popupListNode: "catalogueWorkPopupList",
    newButton: "catalogueWorkNew",
    saveButton: "catalogueWorkSave",
    deleteButton: "catalogueWorkDelete",
    statusNode: "catalogueWorkStatus",
    metaNode: "catalogueWorkMeta",
    editorPane: "catalogueWorkEditorPane",
    listExpandButton: "catalogueWorkListExpand",
    seriesBrowseSearch: "catalogueWorkSeriesBrowseSearch",
    seriesBrowseEdit: "catalogueWorkSeriesBrowseEdit",
    seriesBrowseDelete: "catalogueWorkSeriesBrowseDelete",
    seriesBrowsePopup: "catalogueWorkSeriesBrowsePopup",
    seriesBrowseMembers: "catalogueWorkSeriesBrowseMembers",
    seriesBrowseStatus: "catalogueWorkSeriesBrowseStatus",
    seriesBrowseCount: "catalogueWorkSeriesBrowseCount"
  });
}

export function createWorkEditorState(elements, options = {}) {
  const {
    root,
    fieldsNode,
    readonlyNode,
    searchNode,
    popupNode,
    popupListNode,
    newButton,
    saveButton,
    deleteButton,
    statusNode,
    previewNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    resourcesPanelNode,
    resourcesMetaNode,
    resourcesResultsNode,
    metaNode
  } = elements;
  const mediaConfigLoader = options.mediaConfigLoader || loadCatalogueMediaConfig;
  const modalHostFactory = options.modalHostFactory || createStudioModalHost;

  return {
    root,
    config: null,
    mode: "single",
    workSearchById: new Map(),
    seriesById: new Map(),
    galleriesById: new Map(),
    galleryPicker: null,
    seriesBrowser: null,
    layout: null,
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
    mediaConfig: mediaConfigLoader(root),
    rebuildPending: false,
    pendingBuildExtraSeriesIds: [],
    buildPreview: null,
    workMediaSourceConfig: null,
    isSaving: false,
    isBuilding: false,
    isDeleting: false,
    serverAvailable: false,
    modalHost: modalHostFactory({ root }),
    activeModalController: null,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    mediaSourceWrapper: null,
    mediaSourceButton: null,
    messageController: null,
    readonlyNodes: new Map(),
    fieldsNode,
    readonlyNode,
    searchNode,
    popupNode,
    popupListNode,
    newButton,
    saveButton,
    deleteButton,
    statusNode,
    warningNode: createCatalogueEditorMessageRoleNode("catalogueWorkWarning", "warning"),
    resultNode: createCatalogueEditorMessageRoleNode("catalogueWorkResult", "result"),
    previewNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    resourcesActionsNode: elements.resourcesActionsNode,
    resourcesPanelNode,
    resourcesMetaNode,
    resourcesResultsNode,
    metaNode
  };
}

export function createWorkRouteStateOptions(state, callbacks = {}, overrides = {}) {
  return {
    text: callbacks.text,
    setTextWithState: callbacks.setTextWithState,
    setOpenInputMode: callbacks.setOpenInputMode,
    setPopupVisibility: callbacks.setPopupVisibility,
    applyDraftToInputs: callbacks.applyDraftToInputs,
    applyReadonly: callbacks.applyReadonly,
    clearReadonlyFields: callbacks.clearReadonlyFields,
    updateEditorState: callbacks.updateEditorState,
    ...overrides
  };
}
