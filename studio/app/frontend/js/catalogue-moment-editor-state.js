import {
  collectRequiredElements,
  createCatalogueEditorRouteStateOptions
} from "./catalogue-editor-route-boot.js";
import {
  createCatalogueEditorMessageRoleNode
} from "./catalogue-editor-message-controller.js";

export const MOMENT_ROUTE_STATE = createCatalogueEditorRouteStateOptions({
  route: "catalogue-moment",
  importModeKey: "isImportMode",
  busyKeys: ["isSaving", "isBuilding", "isDeleting", "importIsBusy"]
});

export function collectMomentEditorElements() {
  return collectRequiredElements({
    root: "catalogueMomentRoot",
    loadingNode: "catalogueMomentLoading",
    emptyNode: "catalogueMomentEmpty",
    searchNode: "catalogueMomentSearch",
    popupNode: "catalogueMomentPopup",
    popupListNode: "catalogueMomentPopupList",
    openButton: "catalogueMomentOpen",
    newButton: "catalogueMomentNew",
    statusNode: "catalogueMomentStatus",
    saveButton: "catalogueMomentSave",
    publicationButton: "catalogueMomentPublication",
    deleteButton: "catalogueMomentDelete",
    fieldsNode: "catalogueMomentFields",
    readonlyNode: "catalogueMomentReadonly",
    sideHeadingNode: "catalogueMomentSideHeading",
    summaryNode: "catalogueMomentSummary",
    readinessNode: "catalogueMomentReadiness",
    runtimeStateNode: "catalogueMomentRuntimeState",
    buildImpactNode: "catalogueMomentBuildImpact",
    importSourceNode: "catalogueMomentImportSource",
    importFileLabelNode: "catalogueMomentImportFileLabel",
    importFileNode: "catalogueMomentImportFile",
    importFileDescriptionNode: "catalogueMomentImportFileDescription",
    importSourceSummaryNode: "catalogueMomentImportSourceSummary",
    importImageGuidanceNode: "catalogueMomentImportImageGuidance",
    importPreviewButton: "catalogueMomentImportPreview",
    importApplyButton: "catalogueMomentImportApply"
  });
}

export function createMomentEditorState(elements) {
  return {
    config: null,
    root: elements.root,
    loadingNode: elements.loadingNode,
    emptyNode: elements.emptyNode,
    searchNode: elements.searchNode,
    popupNode: elements.popupNode,
    popupListNode: elements.popupListNode,
    openButton: elements.openButton,
    newButton: elements.newButton,
    contextNode: createCatalogueEditorMessageRoleNode("catalogueMomentContext", "context"),
    statusNode: elements.statusNode,
    warningNode: createCatalogueEditorMessageRoleNode("catalogueMomentWarning", "warning"),
    resultNode: createCatalogueEditorMessageRoleNode("catalogueMomentResult", "result"),
    saveButton: elements.saveButton,
    publicationButton: elements.publicationButton,
    deleteButton: elements.deleteButton,
    fieldsNode: elements.fieldsNode,
    readonlyNode: elements.readonlyNode,
    sideHeadingNode: elements.sideHeadingNode,
    summaryNode: elements.summaryNode,
    readinessNode: elements.readinessNode,
    runtimeStateNode: elements.runtimeStateNode,
    buildImpactNode: elements.buildImpactNode,
    importSourceNode: elements.importSourceNode,
    importStatusNode: elements.statusNode,
    importWarningNode: createCatalogueEditorMessageRoleNode("catalogueMomentImportWarning", "warning"),
    importResultNode: createCatalogueEditorMessageRoleNode("catalogueMomentImportResult", "result"),
    importFileLabelNode: elements.importFileLabelNode,
    importFileNode: elements.importFileNode,
    importFileDescriptionNode: elements.importFileDescriptionNode,
    importSourceSummaryNode: elements.importSourceSummaryNode,
    importImageGuidanceNode: elements.importImageGuidanceNode,
    importPreviewButton: elements.importPreviewButton,
    importApplyButton: elements.importApplyButton,
    fieldNodes: new Map(),
    fieldStatusNodes: new Map(),
    messageController: null,
    readonlyNodes: new Map(),
    moments: new Map(),
    momentRows: [],
    currentMomentId: "",
    currentRecord: null,
    expectedRecordHash: "",
    preview: null,
    previewReadiness: null,
    buildPreview: null,
    importPreview: null,
    importBuild: null,
    importSteps: [],
    needsBuild: false,
    serverAvailable: false,
    isSaving: false,
    isDeleting: false,
    isBuilding: false,
    importIsBusy: false,
    isImportMode: false
  };
}
