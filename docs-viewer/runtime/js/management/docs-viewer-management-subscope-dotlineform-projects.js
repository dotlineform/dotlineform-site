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
  normalizeDocsViewerAuthoringSubject
} from "./docs-viewer-management-document-subject.js";

const CUSTOMISATION_ID = "dotlineform_projects";
const AUTHORING_SUBJECT_GROUP_ID = "authoring_subject";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function exactCollection(value) {
  var keys = Object.keys(value || {}).sort();
  var scope = cleanString(value && value.scope).toLowerCase();
  var subScope = cleanString(value && value.sub_scope).toLowerCase();
  if (keys.length !== 2 || keys[0] !== "scope" || keys[1] !== "sub_scope" || !scope || !subScope) {
    throw new Error("Projects customisation collection target is invalid.");
  }
  return Object.freeze({ scope: scope, sub_scope: subScope });
}

function authoringSubject(documentRecord) {
  return normalizeDocsViewerAuthoringSubject(
    documentRecord && documentRecord.authoring_subject,
    {
      errorMessage: "Projects document authoring_subject must be a normalized object."
    }
  );
}

function folderPath(documentRecord) {
  var subject = authoringSubject(documentRecord);
  return subject.state === "valid" && subject.kind === "folder" ? subject.key : "";
}

function publicationTargets(documentRecord) {
  var customisation = documentRecord && documentRecord.customisation;
  var targets = customisation && customisation.publication_targets;
  return Array.isArray(targets) ? targets.map(function (target) {
    var editorial = target && target.editorial;
    return {
      available: target && target.available === true,
      docId: cleanString(editorial && editorial.doc_id),
      publicUrl: cleanString(target && target.publication && target.publication.public_url),
      scope: cleanString(editorial && editorial.scope).toLowerCase(),
      subScope: cleanString(editorial && editorial.sub_scope).toLowerCase(),
      title: cleanString(target && target.title),
      viewerUrl: cleanString(target && target.viewer_url)
    };
  }).filter(function (target) {
    return target.scope && target.subScope && target.docId;
  }) : [];
}

function publicationStage(target) {
  if (!target.available) return "unavailable";
  return target.publicUrl ? "published" : "pre-publish";
}

function publicationStageLabel(stage) {
  return ({
    "pre-publish": "Pre-publish",
    published: "Published",
    unavailable: "Unavailable"
  })[stage] || "Working";
}

function publicationIdentity(target) {
  return target.scope + "/" + target.subScope + "/" + target.docId;
}

function publicationAccessibleLabel(target) {
  var stage = publicationStage(target);
  var identity = publicationIdentity(target);
  var targetLabel = target.title ? target.title + " (" + identity + ")" : identity;
  return publicationStageLabel(stage) + ": " + targetLabel;
}

function renderPublicationCues(context) {
  var settings = context || {};
  var host = settings.trailingHost;
  if (!host) return { accessibleLabels: [] };
  var targets = publicationTargets(settings.document);
  var group = host.ownerDocument.createElement("span");
  group.className = "docsViewerReport__projectPublicationCues";
  if (!targets.length) {
    var working = host.ownerDocument.createElement("span");
    working.className = "docsViewerReport__projectPublicationCue";
    working.dataset.projectPublicationStage = "working";
    working.textContent = "Working";
    group.appendChild(working);
    host.appendChild(group);
    return { accessibleLabels: ["Working"] };
  }
  var labels = targets.map(function (target) {
    var stage = publicationStage(target);
    var label = publicationAccessibleLabel(target);
    var cue = host.ownerDocument.createElement(target.available ? "a" : "span");
    cue.className = "docsViewerReport__projectPublicationCue";
    cue.dataset.projectPublicationStage = stage;
    cue.dataset.projectPublicationTarget = publicationIdentity(target);
    cue.textContent = ({ "pre-publish": "🟠", published: "🟢" })[stage] || "⚠️";
    cue.title = label;
    cue.setAttribute("aria-label", label);
    if (target.available) cue.href = target.viewerUrl;
    group.appendChild(cue);
    return label;
  });
  host.appendChild(group);
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
    capability: path ? true : { available: false, reason: "This document has no valid Folder subject." },
    emptyState: "disabled",
    refreshEffect: "none",
    handler: function () {
      if (!path) throw new Error("This document has no valid Folder subject.");
      var encodedPath = encodeDecodedLocalTarget(path);
      if (!encodedPath) throw new Error("This document has an invalid Folder subject.");
      if (typeof options.openLocalTarget !== "function") throw new Error("Open in Finder is unavailable.");
      return options.openLocalTarget(encodedPath, options.clientOptions || {}).then(function (response) {
        if (typeof options.setStatus === "function") {
          options.setStatus(cleanString(response && response.summary_text) || "Local target opened.", false);
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
  var button = host.ownerDocument.createElement("button");
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
        fetch: options.fetch,
        readMetadata: options.readMetadata,
        restoreFocus: button,
        root: options.root,
        target: target
      }).then(function (result) {
        if (!result || result.confirmed !== true) return result;
        var refresh = actionContext && actionContext.refreshDocument;
        var refreshed = typeof refresh === "function" ? refresh(target) : Promise.resolve(target);
        return Promise.resolve(refreshed).then(function () {
          return result.payload;
        });
      });
    }
  });
  if (registration.hidden) return;
  button.className = "docsViewerReport__button docsReportDetail__iconButton docsReportDetail__assignSubject";
  button.type = "button";
  button.dataset.docsProjectsAssignSubject = "true";
  button.textContent = "Subject";
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
  if (subject.state === "valid") {
    return {
      detail: subject.key,
      id: AUTHORING_SUBJECT_GROUP_ID,
      label: "Subject",
      state: subject.kind,
      value: ({ folder: "Folder", work: "Work", series: "Series" })[subject.kind]
    };
  }
  if (subject.state === "malformed") {
    var field = subject.fields[0];
    return {
      detail: "Malformed " + field + " declaration: " + JSON.stringify(subject.evidence[field]),
      id: AUTHORING_SUBJECT_GROUP_ID,
      label: "Subject",
      state: "warning",
      value: "Authoring warning"
    };
  }
  if (subject.state === "conflicting") {
    var declarations = subject.fields.map(function (field) {
      return field + "=" + JSON.stringify(subject.evidence[field]);
    }).join(", ");
    return {
      detail: "Conflicting declarations: " + declarations,
      id: AUTHORING_SUBJECT_GROUP_ID,
      label: "Subject",
      state: "warning",
      value: "Authoring warning"
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
  var publicationFields = publicationTargets(settings.document).map(function (publication, index) {
    var stage = publicationStage(publication);
    return Object.freeze({
      detail: publicationIdentity(publication),
      id: "publication_" + (index + 1),
      label: "Publication",
      state: stage,
      value: (
        ({ "pre-publish": "🟠", published: "🟢", unavailable: "⚠️" })[stage]
        + " " + publicationStageLabel(stage)
        + (publication.title ? " — " + publication.title : "")
      )
    });
  });
  if (!publicationFields.length) {
    publicationFields.push(Object.freeze({
      detail: "No editorial copy",
      id: "publication",
      label: "Publication",
      state: "working",
      value: "Working"
    }));
  }
  return Object.freeze({
    actions: Object.freeze({ assignSubject: assignSubjectAvailable }),
    fields: Object.freeze([
      Object.freeze(subjectInfoField(authoringSubject(settings.document)))
    ].concat(publicationFields))
  });
}

export function createDocsViewerManagementSubscopeDotlineformProjects(options = {}) {
  var descriptorId = cleanString(options.descriptor && options.descriptor.id);
  if (descriptorId !== CUSTOMISATION_ID) {
    throw new Error("Projects customisation identity did not match its registry entry.");
  }
  exactCollection(options.collection);
  var assignSubjectAvailable = hasDocsViewerAssignableFieldGroup(options.descriptor, AUTHORING_SUBJECT_GROUP_ID);
  return {
    id: CUSTOMISATION_ID,
    projectDetailInfo: function (context) { return projectDetailInfo(context, assignSubjectAvailable); },
    renderDetailToolbar: function (context) {
      renderAssignSubject(context, options, assignSubjectAvailable);
      renderOpenInFinder(context, options);
    },
    renderRow: renderPublicationCues
  };
}
