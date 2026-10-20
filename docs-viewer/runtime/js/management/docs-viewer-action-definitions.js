export const DOCS_VIEWER_ACTION_IDS = Object.freeze({
  COPY_LINK: "copy-link",
  DELETE: "delete",
  EDIT_DOCUMENT: "edit-document",
  EXPORT_DOCS: "export-docs",
  IMPORT: "import",
  IMPORT_DOC: "import-doc",
  MARKDOWN_SAVE: "markdown-save",
  SOURCE_ADD_CATALOGUE_IMAGE: "source-add-catalogue-image",
  SOURCE_ADD_MEDIA_VIEW_LINK: "source-add-media-view-link",
  SOURCE_ADD_FILE: "source-add-file",
  SOURCE_ADD_IMAGE: "source-add-image",
  SOURCE_ASSIGN_SUBJECT: "source-assign-subject",
  SOURCE_INSERT_DOC_LINK: "source-insert-doc-link",
  NEW: "new",
  NEW_CHILD: "new-child",
  NEW_SIBLING: "new-sibling",
  OPEN: "open",
  OPEN_VSCODE: "open-vscode",
  POSITION: "position",
  PREPARE_DOCUMENT_PACKAGE: "prepare-document-package",
  PUBLISH: "publish",
  REFRESH_DISCOVERY: "refresh-discovery",
  REBUILD_DOCUMENT: "rebuild-document",
  SET_DRAFT: "set-draft",
  SET_SELECTED: "set-selected",
  SORT_CHILDREN: "sort-children"
});

export const DOCS_VIEWER_ACTION_TARGETS = Object.freeze({
  ACTIVE_DOCUMENT: "active-document",
  COLLECTION: "collection",
  COLLECTION_SELECTION: "collection-selection",
  DOCUMENT_SUBTREE: "document-subtree",
  DOCUMENT: "document",
  WORKSPACE: "workspace"
});

function actionDefinition(id, target) {
  return Object.freeze({ id: id, target: target });
}

var TARGETS = DOCS_VIEWER_ACTION_TARGETS;
var IDS = DOCS_VIEWER_ACTION_IDS;

// Product availability belongs with the actions, independently of local services.
// Explicit private-report identities leave future public reports unrestricted.
var PRIVATE_REPORT_DOC_IDS = new Set([
  "d-20260426-164043-e14f49", "d-20260810-222148-99daec", "d-20261006-160017-e6589d",
  "d-20260812-212735-6d9cf3", "d-20261004-202223-1e2205", "d-20261005-153252-541ac3",
  "d-20260910-214604-f9e841", "d-20260805-155400-4c341f", "d-20260810-150346-bc7cdc",
  "d-20260807-175649-62020b", "d-20260909-140121-53c381", "d-20260807-163356-b376d7",
  "d-20261005-234748-d69c84", "d-20260909-160530-224efe"
]);
var CATALOGUE_ACTION_IDS = new Set([IDS.SET_SELECTED, IDS.COPY_LINK, IDS.EXPORT_DOCS]);
var STRUCTURAL_DOCUMENT_ACTION_IDS = new Set([IDS.DELETE, IDS.SET_SELECTED, IDS.SET_DRAFT]);

function documentActionRestriction(actionId, target, collectionHostDocIds) {
  if (!target) return "";
  if (target.collection === "catalogue" && !CATALOGUE_ACTION_IDS.has(actionId)) {
    return "Catalogue Work documents are managed through Work edits and Regenerate.";
  }
  if (!target.collection && STRUCTURAL_DOCUMENT_ACTION_IDS.has(actionId)) {
    if (collectionHostDocIds.includes(target.doc_id)) {
      return "Collection hosts are maintained parts of the site structure.";
    }
    if (PRIVATE_REPORT_DOC_IDS.has(target.doc_id)) {
      return "Private reports are maintained parts of the local site structure.";
    }
  }
  return "";
}

export const DOCS_VIEWER_ACTION_DEFINITIONS = Object.freeze({
  [IDS.COPY_LINK]: actionDefinition(IDS.COPY_LINK, TARGETS.DOCUMENT),
  [IDS.DELETE]: actionDefinition(IDS.DELETE, TARGETS.DOCUMENT_SUBTREE),
  [IDS.EDIT_DOCUMENT]: actionDefinition(IDS.EDIT_DOCUMENT, TARGETS.ACTIVE_DOCUMENT),
  [IDS.EXPORT_DOCS]: actionDefinition(IDS.EXPORT_DOCS, TARGETS.COLLECTION_SELECTION),
  [IDS.IMPORT]: actionDefinition(IDS.IMPORT, TARGETS.COLLECTION),
  [IDS.IMPORT_DOC]: actionDefinition(IDS.IMPORT_DOC, TARGETS.COLLECTION),
  [IDS.MARKDOWN_SAVE]: actionDefinition(IDS.MARKDOWN_SAVE, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SOURCE_ADD_CATALOGUE_IMAGE]: actionDefinition(IDS.SOURCE_ADD_CATALOGUE_IMAGE, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SOURCE_ADD_MEDIA_VIEW_LINK]: actionDefinition(IDS.SOURCE_ADD_MEDIA_VIEW_LINK, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SOURCE_ADD_FILE]: actionDefinition(IDS.SOURCE_ADD_FILE, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SOURCE_ADD_IMAGE]: actionDefinition(IDS.SOURCE_ADD_IMAGE, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SOURCE_ASSIGN_SUBJECT]: actionDefinition(IDS.SOURCE_ASSIGN_SUBJECT, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SOURCE_INSERT_DOC_LINK]: actionDefinition(IDS.SOURCE_INSERT_DOC_LINK, TARGETS.ACTIVE_DOCUMENT),
  [IDS.NEW]: actionDefinition(IDS.NEW, TARGETS.WORKSPACE),
  [IDS.NEW_CHILD]: actionDefinition(IDS.NEW_CHILD, TARGETS.DOCUMENT),
  [IDS.NEW_SIBLING]: actionDefinition(IDS.NEW_SIBLING, TARGETS.DOCUMENT),
  [IDS.OPEN]: actionDefinition(IDS.OPEN, TARGETS.DOCUMENT),
  [IDS.OPEN_VSCODE]: actionDefinition(IDS.OPEN_VSCODE, TARGETS.DOCUMENT),
  [IDS.POSITION]: actionDefinition(IDS.POSITION, TARGETS.DOCUMENT),
  [IDS.PREPARE_DOCUMENT_PACKAGE]: actionDefinition(IDS.PREPARE_DOCUMENT_PACKAGE, TARGETS.COLLECTION_SELECTION),
  [IDS.PUBLISH]: actionDefinition(IDS.PUBLISH, TARGETS.WORKSPACE),
  [IDS.REFRESH_DISCOVERY]: actionDefinition(IDS.REFRESH_DISCOVERY, TARGETS.WORKSPACE),
  [IDS.REBUILD_DOCUMENT]: actionDefinition(IDS.REBUILD_DOCUMENT, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SET_DRAFT]: actionDefinition(IDS.SET_DRAFT, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SET_SELECTED]: actionDefinition(IDS.SET_SELECTED, TARGETS.ACTIVE_DOCUMENT),
  [IDS.SORT_CHILDREN]: actionDefinition(IDS.SORT_CHILDREN, TARGETS.DOCUMENT)
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
  return {
    documentTarget: options.documentTarget || null,
    subtreeDocIds: normalizeIds(options.subtreeDocIds),
    collectionHostDocIds: normalizeIds(options.collectionHostDocIds)
  };
}

export function resolveDocsViewerAction(actionId, context = {}) {
  var definition = getDocsViewerActionDefinition(actionId);
  if (!definition) {
    throw new Error("Unknown Docs Viewer action: " + normalizeId(actionId));
  }

  var documentTarget = context.documentTarget;
  var documentId = normalizeId(documentTarget && documentTarget.doc_id);
  var subtreeDocIds = normalizeIds(context.subtreeDocIds);
  var targetDocIds = [];
  var disabledReason = "";

  if (definition.target === TARGETS.ACTIVE_DOCUMENT) {
    if (documentId) targetDocIds = [documentId];
    else disabledReason = "No active document.";
  } else if (definition.target === TARGETS.DOCUMENT) {
    if (documentId) targetDocIds = [documentId];
    else disabledReason = "No document.";
  } else if (definition.target === TARGETS.DOCUMENT_SUBTREE) {
    if (documentTarget && documentTarget.collection) {
      targetDocIds = documentId ? [documentId] : normalizeIds(documentTarget.doc_ids);
      if (!targetDocIds.length) disabledReason = "Select one or more documents.";
    } else if (!documentId || subtreeDocIds.indexOf(documentId) === -1) {
      disabledReason = "No Index target document.";
    } else targetDocIds = subtreeDocIds;
  } else if (definition.target === TARGETS.COLLECTION) {
    if (!(documentTarget && documentTarget.collection)) disabledReason = "Open a collection.";
  } else if (definition.target === TARGETS.COLLECTION_SELECTION) {
    if (documentTarget && documentTarget.collection) targetDocIds = normalizeIds(documentTarget.doc_ids);
    if (!targetDocIds.length) disabledReason = "Select one or more collection documents.";
  }

  var restriction = definition.target !== TARGETS.WORKSPACE || [IDS.NEW, IDS.IMPORT_DOC].includes(definition.id)
    ? documentActionRestriction(definition.id, documentTarget, normalizeIds(context.collectionHostDocIds)) : "";
  if (restriction) disabledReason = restriction;
  return {
    actionId: definition.id,
    disabledReason: disabledReason,
    disabled: Boolean(disabledReason),
    enabled: !disabledReason,
    hidden: Boolean(restriction) || ([TARGETS.COLLECTION, TARGETS.COLLECTION_SELECTION].includes(definition.target) && !(documentTarget && documentTarget.collection)),
    target: definition.target,
    targetDocIds: targetDocIds
  };
}
