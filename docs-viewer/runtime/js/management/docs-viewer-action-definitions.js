export const DOCS_VIEWER_ACTION_IDS = Object.freeze({
  BOOKMARK: "bookmark",
  COPY_LINK: "copy-link",
  DELETE: "delete",
  DELETE_SCOPE: "delete-scope",
  DELETE_SUB_SCOPE: "delete-sub-scope",
  EDIT_METADATA: "edit-metadata",
  EXPORT_DOCS: "export-docs",
  IMPORT: "import",
  INFO: "info",
  MARKDOWN_SAVE: "markdown-save",
  MARKDOWN_SOURCE: "markdown-source",
  MOVE: "move",
  NEW: "new",
  NEW_CHILD: "new-child",
  NEW_SCOPE: "new-scope",
  NEW_SIBLING: "new-sibling",
  NEW_SUB_SCOPE: "new-sub-scope",
  OPEN: "open",
  OPEN_VSCODE: "open-vscode",
  PUBLISH_DOCS: "publish-docs",
  REBUILD_DOCS: "rebuild-docs",
  RENAME_SCOPE: "rename-scope",
  SETTINGS: "settings",
  SHOW: "show",
  SHOW_NON_VIEWABLE: "show-non-viewable"
});

export const DOCS_VIEWER_ACTION_TARGETS = Object.freeze({
  ACTIVE_DOCUMENT: "active-document",
  SCOPE: "scope",
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
  [IDS.COPY_LINK]: actionDefinition(IDS.COPY_LINK, TARGETS.SELECTION, POLICIES.PRIMARY),
  [IDS.DELETE]: actionDefinition(IDS.DELETE, TARGETS.SELECTION, POLICIES.EXACTLY_ONE),
  [IDS.DELETE_SCOPE]: actionDefinition(IDS.DELETE_SCOPE, TARGETS.SCOPE),
  [IDS.DELETE_SUB_SCOPE]: actionDefinition(IDS.DELETE_SUB_SCOPE, TARGETS.SCOPE),
  [IDS.EDIT_METADATA]: actionDefinition(IDS.EDIT_METADATA, TARGETS.SELECTION, POLICIES.PRIMARY),
  [IDS.EXPORT_DOCS]: actionDefinition(IDS.EXPORT_DOCS, TARGETS.SCOPE),
  [IDS.IMPORT]: actionDefinition(IDS.IMPORT, TARGETS.SCOPE),
  [IDS.INFO]: actionDefinition(IDS.INFO, TARGETS.SELECTION, POLICIES.PRIMARY),
  [IDS.MARKDOWN_SAVE]: actionDefinition(IDS.MARKDOWN_SAVE, TARGETS.ACTIVE_DOCUMENT),
  [IDS.MARKDOWN_SOURCE]: actionDefinition(IDS.MARKDOWN_SOURCE, TARGETS.ACTIVE_DOCUMENT),
  [IDS.MOVE]: actionDefinition(IDS.MOVE, TARGETS.SELECTION, POLICIES.ALL),
  [IDS.NEW]: actionDefinition(IDS.NEW, TARGETS.SCOPE),
  [IDS.NEW_CHILD]: actionDefinition(IDS.NEW_CHILD, TARGETS.SELECTION, POLICIES.PRIMARY),
  [IDS.NEW_SCOPE]: actionDefinition(IDS.NEW_SCOPE, TARGETS.SCOPE),
  [IDS.NEW_SIBLING]: actionDefinition(IDS.NEW_SIBLING, TARGETS.SELECTION, POLICIES.PRIMARY),
  [IDS.NEW_SUB_SCOPE]: actionDefinition(IDS.NEW_SUB_SCOPE, TARGETS.SCOPE),
  [IDS.OPEN]: actionDefinition(IDS.OPEN, TARGETS.SELECTION, POLICIES.PRIMARY),
  [IDS.OPEN_VSCODE]: actionDefinition(IDS.OPEN_VSCODE, TARGETS.SELECTION, POLICIES.PRIMARY),
  [IDS.PUBLISH_DOCS]: actionDefinition(IDS.PUBLISH_DOCS, TARGETS.SCOPE),
  [IDS.REBUILD_DOCS]: actionDefinition(IDS.REBUILD_DOCS, TARGETS.SCOPE),
  [IDS.RENAME_SCOPE]: actionDefinition(IDS.RENAME_SCOPE, TARGETS.SCOPE),
  [IDS.SETTINGS]: actionDefinition(IDS.SETTINGS, TARGETS.SCOPE),
  [IDS.SHOW]: actionDefinition(IDS.SHOW, TARGETS.SELECTION, POLICIES.EXACTLY_ONE),
  [IDS.SHOW_NON_VIEWABLE]: actionDefinition(IDS.SHOW_NON_VIEWABLE, TARGETS.SCOPE)
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

export function createDocsViewerSingleDocumentActionContext(options = {}) {
  var activeDocId = normalizeId(options.activeDocId);
  var targetDocId = Object.prototype.hasOwnProperty.call(options, "targetDocId")
    ? normalizeId(options.targetDocId)
    : activeDocId;
  return {
    activeDocId: activeDocId,
    primaryDocId: targetDocId,
    selectedDocIds: targetDocId ? [targetDocId] : []
  };
}

export function resolveDocsViewerAction(actionId, context = {}) {
  var definition = getDocsViewerActionDefinition(actionId);
  if (!definition) {
    throw new Error("Unknown Docs Viewer action: " + normalizeId(actionId));
  }

  var activeDocId = normalizeId(context.activeDocId);
  var primaryDocId = normalizeId(context.primaryDocId);
  var selectedDocIds = normalizeIds(context.selectedDocIds);
  var targetDocIds = [];
  var disabledReason = "";

  if (definition.target === TARGETS.ACTIVE_DOCUMENT) {
    if (activeDocId) targetDocIds = [activeDocId];
    else disabledReason = "No active document.";
  } else if (definition.target === TARGETS.SELECTION) {
    if (definition.selectionPolicy === POLICIES.PRIMARY) {
      if (!primaryDocId) disabledReason = "No primary document.";
      else if (selectedDocIds.indexOf(primaryDocId) === -1) disabledReason = "Primary document is not selected.";
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
