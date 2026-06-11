import {
  collectRequiredElements,
  createCatalogueEditorRouteStateOptions
} from "./catalogue-editor-route-boot.js";
import {
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";

export const WORK_DETAIL_ROUTE_STATE = createCatalogueEditorRouteStateOptions({
  route: "catalogue-work-detail",
  bulkIdsKey: "bulkDetailUids"
});

export function collectWorkDetailEditorElements() {
  return collectRequiredElements({
    root: "catalogueWorkDetailRoot",
    loadingNode: "catalogueWorkDetailLoading",
    emptyNode: "catalogueWorkDetailEmpty",
    fieldsNode: "catalogueWorkDetailFields",
    readonlyNode: "catalogueWorkDetailReadonly",
    previewNode: "catalogueWorkDetailPreview",
    summaryNode: "catalogueWorkDetailSummary",
    readinessNode: "catalogueWorkDetailReadiness",
    runtimeStateNode: "catalogueWorkDetailRuntimeState",
    buildImpactNode: "catalogueWorkDetailBuildImpact",
    searchNode: "catalogueWorkDetailSearchGlobal",
    popupNode: "catalogueWorkDetailPopup",
    popupListNode: "catalogueWorkDetailPopupList",
    openButton: "catalogueWorkDetailOpen",
    saveButton: "catalogueWorkDetailSave",
    publicationButton: "catalogueWorkDetailPublication",
    deleteButton: "catalogueWorkDetailDelete",
    contextNode: "catalogueWorkDetailContext",
    statusNode: "catalogueWorkDetailStatus",
    warningNode: "catalogueWorkDetailWarning",
    resultNode: "catalogueWorkDetailResult"
  });
}

export function createWorkDetailEditorState(elements, options = {}) {
  const mediaConfigLoader = options.mediaConfigLoader || loadCatalogueMediaConfig;
  return {
    config: null,
    mode: "single",
    detailSearchByUid: new Map(),
    workSearchById: new Map(),
    currentLookup: null,
    currentDetailUid: "",
    currentWorkId: "",
    currentRecord: null,
    currentRecordHash: "",
    bulkDetailUids: [],
    bulkRecords: new Map(),
    bulkRecordHashes: new Map(),
    bulkMixedFields: new Set(),
    bulkTouchedFields: new Set(),
    bulkBuildTargets: [],
    baselineDraft: null,
    draft: {},
    validationErrors: new Map(),
    mediaConfig: mediaConfigLoader(elements.root),
    rebuildPending: false,
    buildPreview: null,
    isSaving: false,
    isBuilding: false,
    isDeleting: false,
    serverAvailable: false,
    root: elements.root,
    fieldWrappers: new Map(),
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    readonlyNodes: new Map(),
    searchNode: elements.searchNode,
    popupNode: elements.popupNode,
    popupListNode: elements.popupListNode,
    openButton: elements.openButton,
    saveButton: elements.saveButton,
    publicationButton: elements.publicationButton,
    deleteButton: elements.deleteButton,
    contextNode: elements.contextNode,
    statusNode: elements.statusNode,
    warningNode: elements.warningNode,
    resultNode: elements.resultNode,
    previewNode: elements.previewNode,
    summaryNode: elements.summaryNode,
    readinessNode: elements.readinessNode,
    runtimeStateNode: elements.runtimeStateNode,
    buildImpactNode: elements.buildImpactNode
  };
}
