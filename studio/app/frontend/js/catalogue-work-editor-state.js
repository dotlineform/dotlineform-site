import {
  collectRequiredElements,
  createCatalogueEditorRouteStateOptions
} from "./catalogue-editor-route-boot.js";
import {
  loadCatalogueMediaConfig
} from "./catalogue-media-preview.js";
import {
  createStudioModalHost
} from "./studio-modal.js";

export const WORK_ROUTE_STATE = createCatalogueEditorRouteStateOptions({
  route: "catalogue-work",
  bulkIdsKey: "bulkWorkIds",
  busyKeys: ["isSaving", "isBuilding", "isPreviewingBuild", "isDeleting"]
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
    statusNode: "catalogueWorkStatus",
    warningNode: "catalogueWorkWarning",
    resultNode: "catalogueWorkResult",
    metaNode: "catalogueWorkMeta"
  });
}

export function createWorkEditorState(elements, options = {}) {
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
    isSaving: false,
    isBuilding: false,
    isPreviewingBuild: false,
    isDeleting: false,
    serverAvailable: false,
    modalHost: modalHostFactory({ root }),
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
