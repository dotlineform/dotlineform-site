import { createDocsViewerEditMenuItem } from "./docs-viewer-management-edit-menu.js";
import {
  encodeDecodedLocalTarget
} from "./docs-viewer-management-client.js";
import {
  hasDocsViewerAssignableFieldGroup
} from "../shared/docs-viewer-config-controller.js";
import {
  openDocsViewerProjectSubjectModal
} from "./docs-viewer-management-project-subject-modal.js";
import {
  classifyDocsDocumentSubject
} from "../shared/docs-document-subject.js";
import {
  normalizeManagedDocumentCollectionTarget
} from "./docs-viewer-management-document-target.js";

const WORKS_CUSTOMISATION_ID = "working_works";
const AUTHORING_SUBJECT_GROUP_ID = "authoring_subject";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function exactCollection(value) {
  var collection = normalizeManagedDocumentCollectionTarget(value);
  if (!collection.collection) {
    throw new Error("Working subject customisation collection target is invalid.");
  }
  return collection;
}

function authoringSubject(documentRecord) {
  return classifyDocsDocumentSubject(
    documentRecord,
    {
      folderSupported: true,
      errorMessage: "Working document subject must be an optional scalar string."
    }
  );
}

function folderPath(documentRecord) {
  var subject = authoringSubject(documentRecord);
  return subject.kind === "folder" ? subject.key : "";
}

function renderOpenInFinder(context, options) {
  var settings = context || {};
  var host = settings.host;
  if (!host || typeof settings.registerAction !== "function") return;
  var path = folderPath(settings.document);
  var registration = settings.registerAction({
    id: "open-project-folder",
    placement: "detail-toolbar",
    targetKind: "validated-detail",
    capability: path ? true : { available: false, reason: "This document has no valid Folder subject." },
    emptyState: "disabled",
    refreshEffect: "none",
    handler: function () {
      if (!path) throw new Error("This document has no valid Folder subject.");
      var encodedPath = encodeDecodedLocalTarget(path);
      if (!encodedPath) throw new Error("This document has an invalid Folder subject.");
      if (typeof options.openLocalTarget !== "function") throw new Error("Open in Finder is unavailable.");
      return options.openLocalTarget(encodedPath, options.clientOptions || {});
    }
  });
  var button = createDocsViewerEditMenuItem(host.ownerDocument, {
    actionId: "open-project-folder", label: "Open in Finder",
    artwork: "docsViewer__icon--folder-open", contribution: true
  });
  button.dataset.docsProjectsOpenFolder = "true";
  button.setAttribute("aria-label", "Open in Finder");
  button.title = "Open in Finder";
  button.disabled = !registration.enabled;
  if (registration.disabledReason) button.title = registration.disabledReason;
  button.addEventListener("click", function () {
    registration.invoke().catch(function (error) {
      if (typeof options.setStatus === "function") {
        options.setStatus(error && error.message ? error.message : "Open in Finder failed.", true);
      }
    });
  });
  host.appendChild(button);
}

function renderAssignSubject(context, options, assignSubjectAvailable) {
  var settings = context || {};
  var host = settings.host;
  if (!host || !assignSubjectAvailable || typeof settings.registerAction !== "function") return;
  var serviceAvailable = typeof options.readMetadata === "function" && typeof options.assignFieldGroup === "function";
  var assigned = authoringSubject(settings.document).kind !== "none";
  var button = createDocsViewerEditMenuItem(host.ownerDocument, {
    actionId: "assign-subject", label: "Assign Subject",
    artwork: assigned ? "docsViewer__icon--dlf-subject-assigned" : "docsViewer__icon--dlf-subject", contribution: true
  });
  var registration = settings.registerAction({
    id: "assign-subject",
    placement: "detail-toolbar",
    targetKind: "validated-detail",
    capability: serviceAvailable ? true : { available: false, reason: "Subject assignment service is unavailable." },
    emptyState: "omitted",
    refreshEffect: "none",
    handler: function (target, actionContext) {
      return openDocsViewerProjectSubjectModal({
        assignFieldGroup: options.assignFieldGroup,
        catalogueProvider: options.catalogueProvider,
        fetch: options.fetch,
        readMetadata: options.readMetadata,
        restoreFocus: function () { return options.root?.querySelector("#docsViewerManageEditButton"); },
        root: options.root,
        target: target
      }).then(function (result) {
        if (!result || result.confirmed !== true) return result;
        var refresh = actionContext && actionContext.refreshDocument;
        var refreshed = typeof refresh === "function" ? refresh(target, result.payload) : Promise.resolve(target);
        return Promise.resolve(refreshed).then(function () {
          return result.payload;
        });
      });
    }
  });
  if (registration.hidden) return;
  button.dataset.docsProjectsAssignSubject = "true";
  button.setAttribute("aria-label", assigned ? "Change Subject" : "Assign Subject");
  button.title = button.getAttribute("aria-label");
  button.disabled = !registration.enabled;
  if (registration.disabledReason) button.title = registration.disabledReason;
  button.addEventListener("click", function () {
    if (button.disabled) return;
    button.disabled = true;
    registration.invoke().catch(function (error) {
      if (typeof options.setStatus === "function") {
        options.setStatus(error && error.message ? error.message : "Subject assignment failed.", true);
      }
    }).finally(function () {
      if (button.isConnected) button.disabled = !registration.enabled;
    });
  });
  host.appendChild(button);
}

function subjectInfoField(subject) {
  if (subject.kind !== "none") {
    return {
      detail: subject.key,
      id: AUTHORING_SUBJECT_GROUP_ID,
      label: "Subject",
      state: subject.kind,
      value: ({ folder: "Folder", work: "Work" })[subject.kind]
    };
  }
  return {
    detail: "",
    id: AUTHORING_SUBJECT_GROUP_ID,
    label: "Subject",
    state: "none",
    value: "None"
  };
}

function workingSubjectDetailInfo(context, assignSubjectAvailable) {
  var settings = context || {};
  var collection = exactCollection(settings.collection);
  var target = settings.target || {};
  if (
    cleanString(target.collection).toLowerCase() !== collection.collection
    || cleanString(target.doc_id) !== cleanString(settings.document && settings.document.doc_id)
  ) {
    throw new Error("Working subject information target is invalid.");
  }
  return Object.freeze({
    actions: Object.freeze({ assignSubject: assignSubjectAvailable }),
    fields: Object.freeze([
      Object.freeze(subjectInfoField(authoringSubject(settings.document)))
    ])
  });
}

/** Provide Working subject information and detail actions without list metadata reads. */
export function createDocsViewerManagementCollectionWorkingWorks(options = {}) {
  var descriptorId = cleanString(options.descriptor && options.descriptor.id);
  if (descriptorId !== WORKS_CUSTOMISATION_ID) {
    throw new Error("Working subject customisation identity did not match its registry entry.");
  }
  exactCollection(options.collection);
  var assignSubjectAvailable = hasDocsViewerAssignableFieldGroup(options.descriptor, AUTHORING_SUBJECT_GROUP_ID);
  return {
    id: WORKS_CUSTOMISATION_ID,
    projectDetailInfo: function (context) {
      return workingSubjectDetailInfo(context, assignSubjectAvailable);
    },
    renderDetailToolbar: function (context) {
      renderAssignSubject(context, options, assignSubjectAvailable);
      renderOpenInFinder(context, options);
    }
  };
}
