export const DOCS_VIEWER_ACTION_IDS = Object.freeze({
  BOOKMARK: "bookmark",
  COPY_LINK: "copy-link",
  DELETE: "delete",
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
  OPEN: "open",
  OPEN_VSCODE: "open-vscode",
  PREPARE_DOCUMENT_PACKAGE: "prepare-document-package",
  PUBLISH: "publish",
  REBUILD_DOCS: "rebuild-docs",
  SETTINGS: "settings"
});

export const DOCS_VIEWER_ACTION_TARGETS = Object.freeze({
  ACTIVE_DOCUMENT: "active-document",
  DOCUMENT_SUBTREE: "document-subtree",
  DOCUMENT: "document",
  WORKSPACE: "workspace"
});

function actionDefinition(id, target) {
  return Object.freeze({ id: id, target: target });
}

var TARGETS = DOCS_VIEWER_ACTION_TARGETS;
var IDS = DOCS_VIEWER_ACTION_IDS;

export const DOCS_VIEWER_ACTION_DEFINITIONS = Object.freeze({
  [IDS.BOOKMARK]: actionDefinition(IDS.BOOKMARK, TARGETS.ACTIVE_DOCUMENT),
  [IDS.COPY_LINK]: actionDefinition(IDS.COPY_LINK, TARGETS.DOCUMENT),
  [IDS.DELETE]: actionDefinition(IDS.DELETE, TARGETS.DOCUMENT_SUBTREE),
  [IDS.EDIT_DOCUMENT]: actionDefinition(IDS.EDIT_DOCUMENT, TARGETS.ACTIVE_DOCUMENT),
  [IDS.EXPORT_WORKSPACE]: actionDefinition(IDS.EXPORT_WORKSPACE, TARGETS.WORKSPACE),
  [IDS.EXPORT_DOCS]: actionDefinition(IDS.EXPORT_DOCS, TARGETS.DOCUMENT_SUBTREE),
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
  [IDS.OPEN]: actionDefinition(IDS.OPEN, TARGETS.DOCUMENT),
  [IDS.OPEN_VSCODE]: actionDefinition(IDS.OPEN_VSCODE, TARGETS.DOCUMENT),
  [IDS.PREPARE_DOCUMENT_PACKAGE]: actionDefinition(IDS.PREPARE_DOCUMENT_PACKAGE, TARGETS.DOCUMENT_SUBTREE),
  [IDS.PUBLISH]: actionDefinition(IDS.PUBLISH, TARGETS.WORKSPACE),
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
  var invocationDocId = normalizeId(options.invocationDocId);
  return {
    activeDocId: activeDocId,
    invocationDocId: invocationDocId,
    subtreeDocIds: normalizeIds(options.subtreeDocIds)
  };
}

export function resolveDocsViewerAction(actionId, context = {}) {
  var definition = getDocsViewerActionDefinition(actionId);
  if (!definition) {
    throw new Error("Unknown Docs Viewer action: " + normalizeId(actionId));
  }

  var activeDocId = normalizeId(context.activeDocId);
  var invocationDocId = normalizeId(context.invocationDocId);
  var subtreeDocIds = normalizeIds(context.subtreeDocIds);
  var targetDocIds = [];
  var disabledReason = "";

  if (definition.target === TARGETS.ACTIVE_DOCUMENT) {
    if (activeDocId) targetDocIds = [activeDocId];
    else disabledReason = "No active document.";
  } else if (definition.target === TARGETS.DOCUMENT) {
    var documentId = invocationDocId || activeDocId;
    if (documentId) targetDocIds = [documentId];
    else disabledReason = "No document.";
  } else if (definition.target === TARGETS.DOCUMENT_SUBTREE) {
    if (!activeDocId || subtreeDocIds.indexOf(activeDocId) === -1) {
      disabledReason = "No displayed Index document.";
    } else targetDocIds = subtreeDocIds;
  }

  return {
    actionId: definition.id,
    disabledReason: disabledReason,
    enabled: !disabledReason,
    target: definition.target,
    targetDocIds: targetDocIds
  };
}
