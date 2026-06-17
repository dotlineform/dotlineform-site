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
    summaryNode: "catalogueWorkSummary",
    readinessNode: "catalogueWorkReadiness",
    runtimeStateNode: "catalogueWorkRuntimeState",
    buildImpactNode: "catalogueWorkBuildImpact",
    detailBrowserPanelNode: "catalogueWorkDetailBrowserPanel",
    detailBrowserSearchNode: "catalogueWorkDetailBrowserSearch",
    detailBrowserSearchClearNode: "catalogueWorkDetailBrowserSearchClear",
    detailBrowserActionsNode: "catalogueWorkDetailBrowserActions",
    detailBrowserSectionActionsNode: "catalogueWorkDetailBrowserSectionActions",
    detailBrowserSectionsNode: "catalogueWorkDetailBrowserSections",
    detailBrowserImagesNode: "catalogueWorkDetailBrowserImages",
    resourcesPanelNode: "catalogueWorkResourcesPanel",
    resourcesActionsNode: "catalogueWorkResourcesActions",
    resourcesMetaNode: "catalogueWorkResourcesMeta",
    resourcesResultsNode: "catalogueWorkResourcesResults",
    searchNode: "catalogueWorkSearch",
    popupNode: "catalogueWorkPopup",
    popupListNode: "catalogueWorkPopupList",
    openButton: "catalogueWorkOpen",
    newButton: "catalogueWorkNew",
    saveButton: "catalogueWorkSave",
    publicationButton: "catalogueWorkPublication",
    deleteButton: "catalogueWorkDelete",
    statusNode: "catalogueWorkStatus",
    metaNode: "catalogueWorkMeta"
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
    openButton,
    newButton,
    saveButton,
    publicationButton,
    deleteButton,
    statusNode,
    previewNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    detailBrowserPanelNode,
    detailBrowserSearchNode,
    detailBrowserSearchClearNode,
    detailBrowserActionsNode,
    detailBrowserSectionActionsNode,
    detailBrowserSectionsNode,
    detailBrowserImagesNode,
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
    mediaPreviewVersion: "",
    detailBrowserSelectedSectionId: "",
    detailBrowserSelectedDetailUid: "",
    detailBrowserSectionsController: null,
    detailBrowserImagesController: null,
    detailBrowserActionsController: null,
    detailBrowserSectionActionsController: null,
    isSaving: false,
    isBuilding: false,
    isDeleting: false,
    serverAvailable: false,
    modalHost: modalHostFactory({ root }),
    activeModalController: null,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    messageController: null,
    readonlyNodes: new Map(),
    fieldsNode,
    readonlyNode,
    searchNode,
    popupNode,
    popupListNode,
    openButton,
    newButton,
    saveButton,
    publicationButton,
    deleteButton,
    statusNode,
    warningNode: createCatalogueEditorMessageRoleNode("catalogueWorkWarning", "warning"),
    resultNode: createCatalogueEditorMessageRoleNode("catalogueWorkResult", "result"),
    previewNode,
    summaryNode,
    readinessNode,
    runtimeStateNode,
    buildImpactNode,
    detailBrowserPanelNode,
    detailBrowserSearchNode,
    detailBrowserSearchClearNode,
    detailBrowserActionsNode,
    detailBrowserSectionActionsNode,
    detailBrowserSectionsNode,
    detailBrowserImagesNode,
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
