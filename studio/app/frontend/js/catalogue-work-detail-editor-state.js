import {
  collectRequiredElements,
  createCatalogueEditorRouteStateOptions
} from "./catalogue-editor-route-boot.js";
import {
  createCatalogueEditorMessageRoleNode
} from "./catalogue-editor-message-controller.js";

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
    searchNode: "catalogueWorkDetailSearchGlobal",
    popupNode: "catalogueWorkDetailPopup",
    popupListNode: "catalogueWorkDetailPopupList",
    openButton: "catalogueWorkDetailOpen",
    saveButton: "catalogueWorkDetailSave",
    deleteButton: "catalogueWorkDetailDelete",
    statusNode: "catalogueWorkDetailStatus",
  });
}

export function createWorkDetailEditorState(elements, options = {}) {
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
    rebuildPending: false,
    isSaving: false,
    isBuilding: false,
    isDeleting: false,
    serverAvailable: false,
    root: elements.root,
    fieldWrappers: new Map(),
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    messageController: null,
    searchNode: elements.searchNode,
    popupNode: elements.popupNode,
    popupListNode: elements.popupListNode,
    openButton: elements.openButton,
    saveButton: elements.saveButton,
    deleteButton: elements.deleteButton,
    contextNode: createCatalogueEditorMessageRoleNode("catalogueWorkDetailContext", "context"),
    statusNode: elements.statusNode,
    warningNode: createCatalogueEditorMessageRoleNode("catalogueWorkDetailWarning", "warning"),
    resultNode: createCatalogueEditorMessageRoleNode("catalogueWorkDetailResult", "result")
  };
}
