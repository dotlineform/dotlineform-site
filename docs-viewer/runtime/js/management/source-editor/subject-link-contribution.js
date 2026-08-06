import { DOCS_VIEWER_ACTION_IDS } from "../docs-viewer-action-definitions.js";
import { normalizeDocsViewerAuthoringSubject } from "../docs-viewer-management-document-subject.js";
import {
  managedDocumentTargetsEqual,
  normalizeManagedDocumentTarget
} from "../docs-viewer-management-document-target.js";
import {
  findCatalogueTargetByIdentity,
  loadCatalogueTargetSupport
} from "./catalogue-token-targets.js";
import { serializeCatalogueToken } from "./catalogue-token-parser.js";
import { createLocalFolderLink } from "./local-folder-links.js";

export const SUBJECT_LINK_CONTROL_ID = "source-insert-subject-link";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function failure(state, message) {
  return Object.freeze({ ok: false, state: state, message: message, value: "" });
}

function ready(value) {
  return Object.freeze({ ok: true, state: "ready", message: "", value: value });
}

function catalogueLabel(kind) {
  return kind === "work" ? "Work" : "Series";
}

export function subjectFromMetadataResponse(response, target) {
  var normalizedTarget = normalizeManagedDocumentTarget(target);
  var responseTarget = response && typeof response === "object" && !Array.isArray(response)
    ? { scope: response.scope, doc_id: response.doc_id }
    : null;
  if (responseTarget && Object.prototype.hasOwnProperty.call(response, "sub_scope")) {
    responseTarget.sub_scope = response.sub_scope;
  }
  var exactTarget;
  try {
    exactTarget = Boolean(responseTarget && managedDocumentTargetsEqual(responseTarget, normalizedTarget));
  } catch (_error) {
    exactTarget = false;
  }
  var record = response && response.record;
  if (
    !exactTarget
    || !record
    || typeof record !== "object"
    || Array.isArray(record)
    || cleanString(record.doc_id) !== normalizedTarget.doc_id
  ) throw new Error("Document subject metadata did not match the active document.");
  if (!Object.prototype.hasOwnProperty.call(record, "authoring_subject")) {
    throw new Error("This document does not expose subject metadata.");
  }
  return normalizeDocsViewerAuthoringSubject(record.authoring_subject, {
    errorMessage: "Document subject metadata is invalid."
  });
}

export function createSubjectLinkInsertionPlan(options = {}) {
  var subject;
  try {
    subject = normalizeDocsViewerAuthoringSubject(options.subject, {
      errorMessage: "Document subject metadata is invalid."
    });
  } catch (_error) {
    return failure("invalid", "Document subject metadata is invalid.");
  }
  var nonValidMessages = {
    none: "This document has no subject link to insert.",
    malformed: "The document subject is malformed.",
    conflicting: "The document has conflicting subject fields."
  };
  if (subject.state !== "valid") {
    return failure(subject.state, nonValidMessages[subject.state] || "Document subject metadata is invalid.");
  }
  if (subject.kind === "folder") {
    var localLink = createLocalFolderLink(subject.key);
    if (!localLink) return failure("invalid-folder", "The Folder subject path is invalid.");
    if (options.localTargetValidated !== true) {
      return failure(
        "unavailable-folder",
        cleanString(options.unavailableMessage) || "The Folder subject target is unavailable."
      );
    }
    return ready(localLink.markdown);
  }
  if (subject.kind !== "work" && subject.kind !== "series") {
    return failure("invalid", "Document subject metadata is invalid.");
  }
  var target = options.catalogueTarget;
  var label = catalogueLabel(subject.kind);
  if (
    !target
    || cleanString(target.family) !== "catalogue"
    || cleanString(target.targetType) !== subject.kind
    || cleanString(target.targetId) !== subject.key
    || !cleanString(target.href)
  ) return failure("unavailable-catalogue", "The " + label + " subject target is unavailable.");
  var serialized = serializeCatalogueToken({
    registry: options.registry,
    targetType: subject.kind,
    targetId: subject.key,
    title: target.title
  });
  return serialized
    ? ready(serialized)
    : failure("invalid-catalogue", "The " + label + " subject target is invalid.");
}

function setActionStatus(context, adapter, message, isError) {
  if (adapter && typeof adapter.setStatus === "function") {
    adapter.setStatus(message, isError);
  } else {
    var services = context.sourceEditorServices || {};
    var owner = typeof services.setStatus === "function" ? services : context;
    if (typeof owner.setStatus === "function") owner.setStatus(message, isError);
  }
}

async function prepareSubjectLink(subject, services, adapter, options) {
  if (subject.state !== "valid") return createSubjectLinkInsertionPlan({ subject: subject });
  if (subject.kind === "work" || subject.kind === "series") {
    try {
      var loadSupport = options.loadCatalogueTargetSupport || loadCatalogueTargetSupport;
      var support = await loadSupport({ allowedTargetTypes: [subject.kind] });
      return createSubjectLinkInsertionPlan({
        subject: subject,
        registry: support.registry,
        catalogueTarget: findCatalogueTargetByIdentity(support, {
          family: "catalogue",
          targetType: subject.kind,
          targetId: subject.key
        })
      });
    } catch (_error) {
      return failure(
        "unavailable-catalogue",
        "The " + catalogueLabel(subject.kind) + " subject target is unavailable."
      );
    }
  }
  if (subject.kind !== "folder") return createSubjectLinkInsertionPlan({ subject: subject });
  var link = createLocalFolderLink(subject.key);
  var capability = typeof services.localFolderLinksCapability === "function"
    ? services.localFolderLinksCapability()
    : null;
  if (!link || !capability || capability.authoring !== true || typeof adapter.validateLocalTarget !== "function") {
    return createSubjectLinkInsertionPlan({ subject: subject });
  }
  try {
    var payload = await adapter.validateLocalTarget(link.encodedTarget);
    return createSubjectLinkInsertionPlan({
      subject: subject,
      localTargetValidated: Boolean(
        payload
        && payload.ok === true
        && payload.state === "valid"
        && cleanString(payload.target) === link.encodedTarget
      )
    });
  } catch (error) {
    return createSubjectLinkInsertionPlan({
      subject: subject,
      localTargetValidated: false,
      unavailableMessage: cleanString(error && error.message)
    });
  }
}

export async function insertSubjectLink(context, options = {}) {
  var services = context.sourceEditorServices || {};
  var adapter = typeof services.getActiveSourceEditorContextAdapter === "function"
    ? services.getActiveSourceEditorContextAdapter()
    : null;
  if (!adapter || typeof adapter.getDocumentTarget !== "function" || typeof adapter.readDocumentMetadata !== "function") {
    setActionStatus(context, adapter, "Insert subject link is available while editing managed Markdown source.", true);
    return false;
  }
  var target;
  try {
    target = normalizeManagedDocumentTarget(adapter.getDocumentTarget());
  } catch (_error) {
    setActionStatus(context, adapter, "The active managed document target is unavailable.", true);
    return false;
  }
  if (!target.sub_scope) {
    setActionStatus(context, adapter, "This document does not expose subject metadata.", true);
    return false;
  }
  var stopBusy = typeof services.startBusy === "function" ? services.startBusy() : function () {};
  try {
    var subject = subjectFromMetadataResponse(await adapter.readDocumentMetadata(), target);
    var plan = await prepareSubjectLink(subject, services, adapter, options);
    if (!plan.ok) {
      setActionStatus(context, adapter, plan.message, true);
      return false;
    }
    if (typeof adapter.replaceSelection !== "function" || !adapter.replaceSelection(plan.value)) {
      setActionStatus(context, adapter, "Subject link could not be inserted.", true);
      return false;
    }
    setActionStatus(context, adapter, "", false);
    return true;
  } catch (error) {
    setActionStatus(context, adapter, cleanString(error && error.message) || "Subject link could not be prepared.", true);
    return false;
  } finally {
    stopBusy();
  }
}

export function subjectLinkControlDefinition() {
  return {
    id: SUBJECT_LINK_CONTROL_ID,
    actionId: DOCS_VIEWER_ACTION_IDS.SOURCE_INSERT_SUBJECT_LINK,
    label: "Insert subject link",
    ownerType: "view",
    ownerViewId: "rendered-document",
    modeIds: ["markdown-source"],
    surfaceId: "main-view",
    appKinds: ["manage"],
    features: ["source-editing"],
    renderer: "source-insert-subject-link"
  };
}

export function subjectLinkControlRenderer(context) {
  var button = context.existingRoot;
  if (!button || button.tagName !== "BUTTON") {
    button = context.document.createElement("button");
    button.className = "docsViewer__documentActionButton";
    button.id = "docsViewerManageSourceInsertSubjectLinkButton";
    button.type = "button";
  }
  button.textContent = "🔗";
  return button;
}

export function createSubjectLinkMainViewControlHandlers(options = {}) {
  return {
    [SUBJECT_LINK_CONTROL_ID]: function (context) {
      return insertSubjectLink(context, options);
    }
  };
}
