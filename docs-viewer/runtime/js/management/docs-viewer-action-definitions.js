export const DOCS_VIEWER_ACTION_IDS = Object.freeze({
  BOOKMARK: "bookmark",
  COPY_LINK: "copy-link",
  DELETE: "delete",
  DELETE_COLLECTION: "delete-collection",
  EDIT_DOCUMENT: "edit-document",
  EXPORT_DOCS: "export-docs",
  EXPORT_WORKSPACE: "export-workspace",
  IMPORT: "import",
  INFO: "info",
  MARKDOWN_SAVE: "markdown-save",
  SOURCE_ADD_CATALOGUE_IMAGE: "source-add-catalogue-image",
  SOURCE_ADD_MEDIA_VIEW_LINK: "source-add-media-view-link",
  SOURCE_ADD_FILE: "source-add-file",
  SOURCE_ADD_IMAGE: "source-add-image",
  SOURCE_INSERT_DOC_LINK: "source-insert-doc-link",
  NEW: "new",
  NEW_CHILD: "new-child",
  NEW_SIBLING: "new-sibling",
  NEW_COLLECTION: "new-collection",
  OPEN: "open",
  OPEN_VSCODE: "open-vscode",
  PREPARE_DOCUMENT_PACKAGE: "prepare-document-package",
  DEPLOY_REPO: "deploy-repo",
  PREPARE_PREVIEW: "prepare-preview",
  REBUILD_DOCS: "rebuild-docs",
  SETTINGS: "settings"
});

export const DOCS_VIEWER_ACTION_TARGETS = Object.freeze({
  ACTIVE_DOCUMENT: "active-document",
  DOCUMENT: "document",
  WORKSPACE: "workspace",
  SELECTION: "selection"
});

export const DOCS_VIEWER_SELECTION_POLICIES = Object.freeze({
  ALL: "all",
  EXACTLY_ONE: "exactly-one",
  PRIMARY: "primary"
});

function actionDefinition(id, target, selectionPolicy) {
  var definition = { id: id, target: target };
  if (selectionPolicy) definition.selectionPolicy = selectionPolicy;
  return Object.freeze(definition);
}

var TARGETS = DOCS_VIEWER_ACTION_TARGETS;
var POLICIES = DOCS_VIEWER_SELECTION_POLICIES;
var IDS = DOCS_VIEWER_ACTION_IDS;

export const DOCS_VIEWER_ACTION_DEFINITIONS = Object.freeze({
  [IDS.BOOKMARK]: actionDefinition(IDS.BOOKMARK, TARGETS.ACTIVE_DOCUMENT),
  [IDS.COPY_LINK]: actionDefinition(IDS.COPY_LINK, TARGETS.DOCUMENT),
  [IDS.DELETE]: actionDefinition(IDS.DELETE, TARGETS.SELECTION, POLICIES.ALL),
  [IDS.DELETE_COLLECTION]: actionDefinition(IDS.DELETE_COLLECTION, TARGETS.WORKSPACE),
  [IDS.EDIT_DOCUMENT]: actionDefinition(IDS.EDIT_DOCUMENT, TARGETS.ACTIVE_DOCUMENT),
  [IDS.EXPORT_WORKSPACE]: actionDefinition(IDS.EXPORT_WORKSPACE, TARGETS.WORKSPACE),
  [IDS.EXPORT_DOCS]: actionDefinition(IDS.EXPORT_DOCS, TARGETS.SELECTION, POLICIES.ALL),
  [IDS.IMPORT]: actionDefinition(IDS.IMPORT, TARGETS.WORKSPACE),
  [IDS.INFO]: actionDefinition(IDS.INFO, TARGETS.ACTIVE_DOCUMENT),
  [IDS.MARKDOWN_SAVE]: actionDefinition(IDS.MARKDOWN_SAVE, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SOURCE_ADD_CATALOGUE_IMAGE]: actionDefinition(IDS.SOURCE_ADD_CATALOGUE_IMAGE, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SOURCE_ADD_MEDIA_VIEW_LINK]: actionDefinition(IDS.SOURCE_ADD_MEDIA_VIEW_LINK, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SOURCE_ADD_FILE]: actionDefinition(IDS.SOURCE_ADD_FILE, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SOURCE_ADD_IMAGE]: actionDefinition(IDS.SOURCE_ADD_IMAGE, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SOURCE_INSERT_DOC_LINK]: actionDefinition(IDS.SOURCE_INSERT_DOC_LINK, TARGETS.ACTIVE_DOCUMENT),
  [IDS.NEW]: actionDefinition(IDS.NEW, TARGETS.WORKSPACE),
  [IDS.NEW_CHILD]: actionDefinition(IDS.NEW_CHILD, TARGETS.DOCUMENT),
  [IDS.NEW_SIBLING]: actionDefinition(IDS.NEW_SIBLING, TARGETS.DOCUMENT),
  [IDS.NEW_COLLECTION]: actionDefinition(IDS.NEW_COLLECTION, TARGETS.WORKSPACE),
  [IDS.OPEN]: actionDefinition(IDS.OPEN, TARGETS.DOCUMENT),
  [IDS.OPEN_VSCODE]: actionDefinition(IDS.OPEN_VSCODE, TARGETS.DOCUMENT),
  [IDS.PREPARE_DOCUMENT_PACKAGE]: actionDefinition(IDS.PREPARE_DOCUMENT_PACKAGE, TARGETS.SELECTION, POLICIES.ALL),
  [IDS.DEPLOY_REPO]: actionDefinition(IDS.DEPLOY_REPO, TARGETS.WORKSPACE),
  [IDS.PREPARE_PREVIEW]: actionDefinition(IDS.PREPARE_PREVIEW, TARGETS.WORKSPACE),
  [IDS.REBUILD_DOCS]: actionDefinition(IDS.REBUILD_DOCS, TARGETS.WORKSPACE),
  [IDS.SETTINGS]: actionDefinition(IDS.SETTINGS, TARGETS.WORKSPACE)
});

function normalizeId(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeIds(values) {
  var seen = new Set();
  return (Array.isArray(values) ? values : []).map(normalizeId).filter(function (id) {
    if (!id || seen.has(id)) return false;
    seen.add(id);
    return true;
  });
}

export function getDocsViewerActionDefinition(actionId) {
  return DOCS_VIEWER_ACTION_DEFINITIONS[normalizeId(actionId)] || null;
}

export function listDocsViewerActionDefinitions() {
  return Object.keys(DOCS_VIEWER_ACTION_DEFINITIONS).map(function (actionId) {
    return DOCS_VIEWER_ACTION_DEFINITIONS[actionId];
  });
}

export function createDocsViewerActionContext(options = {}) {
  var activeDocId = normalizeId(options.activeDocId);
  var selectedDocIds = normalizeIds(options.selectedDocIds);
  var invocationDocId = normalizeId(options.invocationDocId);
  var primaryDocId = invocationDocId || normalizeId(options.primaryDocId);
  if (!primaryDocId && selectedDocIds.length === 1) primaryDocId = selectedDocIds[0];
  return {
    activeDocId: activeDocId,
    invocationDocId: invocationDocId,
    primaryDocId: primaryDocId,
    selectedDocIds: selectedDocIds
  };
}

export function resolveDocsViewerAction(actionId, context = {}) {
  var definition = getDocsViewerActionDefinition(actionId);
  if (!definition) {
    throw new Error("Unknown Docs Viewer action: " + normalizeId(actionId));
  }

  var activeDocId = normalizeId(context.activeDocId);
  var invocationDocId = normalizeId(context.invocationDocId);
  var primaryDocId = normalizeId(context.primaryDocId);
  var selectedDocIds = normalizeIds(context.selectedDocIds);
  var targetDocIds = [];
  var disabledReason = "";

  if (definition.target === TARGETS.ACTIVE_DOCUMENT) {
    if (activeDocId) targetDocIds = [activeDocId];
    else disabledReason = "No active document.";
  } else if (definition.target === TARGETS.DOCUMENT) {
    var documentId = invocationDocId || activeDocId;
    if (documentId) targetDocIds = [documentId];
    else disabledReason = "No document.";
  } else if (definition.target === TARGETS.SELECTION) {
    if (definition.selectionPolicy === POLICIES.PRIMARY) {
      if (!primaryDocId) disabledReason = "No primary document.";
      else targetDocIds = [primaryDocId];
    } else if (definition.selectionPolicy === POLICIES.ALL) {
      if (!selectedDocIds.length) disabledReason = "Select one or more documents.";
      else targetDocIds = selectedDocIds;
    } else if (definition.selectionPolicy === POLICIES.EXACTLY_ONE) {
      if (selectedDocIds.length === 1) targetDocIds = selectedDocIds;
      else if (!selectedDocIds.length) disabledReason = "Select one document.";
      else disabledReason = "Available for one document only.";
    }
  }

  return {
    actionId: definition.id,
    disabledReason: disabledReason,
    enabled: !disabledReason,
    selectionPolicy: definition.selectionPolicy || "",
    target: definition.target,
    targetDocIds: targetDocIds
  };
}
