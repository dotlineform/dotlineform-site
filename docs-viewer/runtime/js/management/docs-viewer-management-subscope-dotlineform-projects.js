import {
  encodeDecodedLocalTarget
} from "./docs-viewer-management-client.js";
import {
  hasDocsViewerAssignableFieldGroup
} from "../shared/docs-viewer-config-controller.js";
import {
  openDocsViewerProjectSubjectModal
} from "./docs-viewer-management-project-subject-modal.js";

const CUSTOMISATION_ID = "dotlineform_projects";
const AUTHORING_SUBJECT_GROUP_ID = "authoring_subject";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function exactCollection(value) {
  var keys = Object.keys(value || {}).sort();
  var scope = cleanString(value && value.scope).toLowerCase();
  var subScope = cleanString(value && value.sub_scope).toLowerCase();
  if (
    keys.length !== 2
    || keys[0] !== "scope"
    || keys[1] !== "sub_scope"
    || !scope
    || !subScope
  ) {
    throw new Error("Projects customisation collection target is invalid.");
  }
  return Object.freeze({ scope: scope, sub_scope: subScope });
}

function folderPath(documentRecord) {
  var customisation = documentRecord && documentRecord.customisation;
  if (customisation == null) return "";
  if (typeof customisation !== "object" || Array.isArray(customisation)) {
    throw new Error("Projects document customisation must be an object.");
  }
  var keys = Object.keys(customisation).sort();
  if (keys.length !== 1 || keys[0] !== "folder_path") {
    throw new Error("Projects document customisation must contain exactly folder_path.");
  }
  if (typeof customisation.folder_path !== "string") {
    throw new Error("Projects Folder Link must be a string.");
  }
  var path = cleanString(customisation.folder_path);
  return path;
}

function duplicateCount(documents, path) {
  if (!path) return 0;
  return (Array.isArray(documents) ? documents : []).filter(function (record) {
    return folderPath(record) === path;
  }).length;
}

function renderFolderState(context) {
  var settings = context || {};
  var host = settings.trailingHost;
  if (!host) return { accessibleLabels: [] };
  var path = folderPath(settings.document);
  var duplicates = duplicateCount(settings.documents, path);
  var state = host.ownerDocument.createElement("span");
  state.className = "docsViewerReport__projectsFolderState";
  state.dataset.projectsFolderState = path ? (duplicates > 1 ? "duplicate" : "linked") : "unlinked";
  state.textContent = path || "No folder link";
  host.classList.add("docsViewerReport__projectsFolderCell");
  host.appendChild(state);
  var labels = [path ? "Folder Link " + path : "No Folder Link"];
  if (duplicates > 1) {
    var duplicate = host.ownerDocument.createElement("span");
    duplicate.className = "docsViewerReport__projectsFolderDuplicate";
    duplicate.textContent = duplicates + " documents";
    state.appendChild(duplicate);
    labels.push("shared by " + duplicates + " documents");
  }
  return { accessibleLabels: labels };
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
    capability: path
      ? true
      : { available: false, reason: "This Project document has no Folder Link." },
    emptyState: "disabled",
    refreshEffect: "none",
    handler: function () {
      if (!path) throw new Error("This Project document has no Folder Link.");
      var encodedPath = encodeDecodedLocalTarget(path);
      if (!encodedPath) throw new Error("This Project document has an invalid Folder Link.");
      if (typeof options.openLocalTarget !== "function") {
        throw new Error("Open in Finder is unavailable.");
      }
      return options.openLocalTarget(encodedPath, options.clientOptions || {}).then(function (response) {
        if (typeof options.setStatus === "function") {
          options.setStatus(
            cleanString(response && response.summary_text) || "Local target opened.",
            false
          );
        }
        return response;
      });
    }
  });
  var button = host.ownerDocument.createElement("button");
  button.className = "docsViewerReport__button docsReportDetail__iconButton docsReportDetail__openProjectFolder";
  button.type = "button";
  button.dataset.docsProjectsOpenFolder = "true";
  button.textContent = "Open in Finder";
  button.disabled = !registration.enabled;
  if (registration.disabledReason) button.title = registration.disabledReason;
  button.addEventListener("click", function () {
    registration.invoke().catch(function (error) {
      if (typeof options.setStatus === "function") {
        options.setStatus(
          error && error.message ? error.message : "Open in Finder failed.",
          true
        );
      }
    });
  });
  host.appendChild(button);
}

function renderAssignSubject(context, options, assignSubjectAvailable) {
  var settings = context || {};
  var host = settings.host;
  if (
    !host
    || !assignSubjectAvailable
    || typeof settings.registerAction !== "function"
  ) return;
  var serviceAvailable = (
    typeof options.readMetadata === "function"
    && typeof options.assignFieldGroup === "function"
  );
  var button = host.ownerDocument.createElement("button");
  var registration = settings.registerAction({
    id: "assign-subject",
    placement: "detail-toolbar",
    targetKind: "validated-detail",
    capability: serviceAvailable
      ? true
      : { available: false, reason: "Subject assignment service is unavailable." },
    emptyState: "omitted",
    refreshEffect: "none",
    handler: function (target, actionContext) {
      return openDocsViewerProjectSubjectModal({
        assignFieldGroup: options.assignFieldGroup,
        readMetadata: options.readMetadata,
        restoreFocus: button,
        root: options.root,
        target: target
      }).then(function (result) {
        if (!result || result.confirmed !== true) return result;
        var refresh = actionContext && actionContext.refreshDocument;
        var refreshed = typeof refresh === "function"
          ? refresh(target)
          : Promise.resolve(target);
        return Promise.resolve(refreshed).then(function () {
          if (typeof options.setStatus === "function") {
            options.setStatus(
              cleanString(result.payload && result.payload.summary_text)
                || "Subject updated.",
              false
            );
          }
          return result.payload;
        });
      });
    }
  });
  if (registration.hidden) return;
  button.className = "docsViewerReport__button docsReportDetail__iconButton docsReportDetail__assignSubject";
  button.type = "button";
  button.dataset.docsProjectsAssignSubject = "true";
  button.textContent = "Assign subject";
  button.disabled = !registration.enabled;
  if (registration.disabledReason) button.title = registration.disabledReason;
  button.addEventListener("click", function () {
    if (button.disabled) return;
    button.disabled = true;
    registration.invoke().catch(function (error) {
      if (typeof options.setStatus === "function") {
        options.setStatus(
          error && error.message ? error.message : "Subject assignment failed.",
          true
        );
      }
    }).finally(function () {
      if (button.isConnected) button.disabled = !registration.enabled;
    });
  });
  host.appendChild(button);
}

function projectDetailInfo(context, assignSubjectAvailable) {
  var settings = context || {};
  var collection = exactCollection(settings.collection);
  var target = settings.target || {};
  if (
    cleanString(target.scope).toLowerCase() !== collection.scope
    || cleanString(target.sub_scope).toLowerCase() !== collection.sub_scope
    || cleanString(target.doc_id) !== cleanString(settings.document && settings.document.doc_id)
  ) {
    throw new Error("Projects subject information target is invalid.");
  }
  var path = folderPath(settings.document);
  return Object.freeze({
    actions: Object.freeze({
      assignSubject: assignSubjectAvailable
    }),
    fields: Object.freeze([
      Object.freeze({
        detail: path,
        id: AUTHORING_SUBJECT_GROUP_ID,
        label: "Subject",
        state: path ? "folder" : "none",
        value: path ? "Folder" : "None"
      })
    ])
  });
}

export function createDocsViewerManagementSubscopeDotlineformProjects(options = {}) {
  var descriptorId = cleanString(options.descriptor && options.descriptor.id);
  if (descriptorId !== CUSTOMISATION_ID) {
    throw new Error("Projects customisation identity did not match its registry entry.");
  }
  exactCollection(options.collection);
  var assignSubjectAvailable = hasDocsViewerAssignableFieldGroup(
    options.descriptor,
    AUTHORING_SUBJECT_GROUP_ID
  );
  return {
    id: CUSTOMISATION_ID,
    projectDetailInfo: function (context) {
      return projectDetailInfo(context, assignSubjectAvailable);
    },
    renderDetailToolbar: function (context) {
      renderAssignSubject(context, options, assignSubjectAvailable);
      renderOpenInFinder(context, options);
    },
    renderRow: renderFolderState
  };
}
