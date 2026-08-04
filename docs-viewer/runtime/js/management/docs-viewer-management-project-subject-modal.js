import {
  escapeHtml,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";
import {
  managedDocumentTargetsEqual,
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

const AUTHORING_SUBJECT_GROUP_ID = "authoring_subject";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function exactResponseTarget(response, target) {
  var candidate = {
    scope: response && response.scope,
    sub_scope: response && response.sub_scope,
    doc_id: response && response.doc_id
  };
  if (!managedDocumentTargetsEqual(candidate, target)) {
    throw new Error("Loaded subject metadata did not match its exact target.");
  }
}

function folderPath(record) {
  var customisation = record && record.customisation;
  if (customisation == null) return "";
  if (
    typeof customisation !== "object"
    || Array.isArray(customisation)
    || Object.keys(customisation).length !== 1
    || !Object.prototype.hasOwnProperty.call(customisation, "folder_path")
    || typeof customisation.folder_path !== "string"
  ) {
    throw new Error("Loaded Projects subject metadata is invalid.");
  }
  return cleanString(customisation.folder_path);
}

function loadedSubject(response, target) {
  if (!response || typeof response !== "object" || Array.isArray(response)) {
    throw new Error("Projects subject metadata could not be loaded.");
  }
  exactResponseTarget(response, target);
  if (
    !response.record
    || typeof response.record !== "object"
    || Array.isArray(response.record)
    || cleanString(response.record.doc_id) !== target.doc_id
  ) {
    throw new Error("Loaded Projects subject record did not match its target.");
  }
  var revision = cleanString(response.source_revision);
  if (!/^sha256:[0-9a-f]{64}$/.test(revision)) {
    throw new Error("Projects subject source revision could not be loaded.");
  }
  return Object.freeze({
    folderPath: folderPath(response.record),
    sourceRevision: revision
  });
}

function assignedSubject(response, target) {
  if (!response || typeof response !== "object" || Array.isArray(response)) {
    throw new Error("Projects subject assignment returned an invalid response.");
  }
  if (!managedDocumentTargetsEqual(response.target, target)) {
    throw new Error("Projects subject assignment did not match its exact target.");
  }
  if (
    cleanString(response.field_group) !== AUTHORING_SUBJECT_GROUP_ID
    || !response.fields
    || typeof response.fields !== "object"
    || Array.isArray(response.fields)
    || Object.keys(response.fields).length !== 1
    || typeof response.fields.folder_path !== "string"
    || !/^sha256:[0-9a-f]{64}$/.test(cleanString(response.source_revision))
  ) {
    throw new Error("Projects subject assignment response is invalid.");
  }
  return response;
}

function modalBody(target, currentPath) {
  var selected = currentPath ? "folder" : "none";
  return "" +
    '<p class="docsViewer__modalNote muted small">Assign the authoring subject for <code>' +
      escapeHtml(target.doc_id) + "</code>.</p>" +
    '<fieldset class="docsViewer__fieldGroup" data-project-subject-options>' +
      '<legend class="docsViewer__fieldLabel">Subject</legend>' +
      '<label class="docsViewer__field docsViewer__field--checkbox">' +
        '<input class="docsViewer__checkboxInput" type="radio" name="docs-project-subject" value="none"' +
          (selected === "none" ? " checked" : "") + ">" +
        '<span class="docsViewer__fieldLabel">None</span>' +
      "</label>" +
      '<label class="docsViewer__field docsViewer__field--checkbox">' +
        '<input class="docsViewer__checkboxInput" type="radio" name="docs-project-subject" value="folder"' +
          (selected === "folder" ? " checked" : "") + ">" +
        '<span class="docsViewer__fieldLabel">Folder</span>' +
      "</label>" +
    "</fieldset>" +
    '<label class="docsViewer__field" data-project-subject-folder' +
      (selected === "folder" ? "" : " hidden") + ">" +
      '<span class="docsViewer__fieldLabel">Folder path or file URL</span>' +
      '<input class="docsViewer__fieldInput" data-project-subject-folder-input type="text" ' +
        'autocomplete="off" spellcheck="false" value="' + escapeHtml(currentPath) + '">' +
    "</label>";
}

function openSubjectModal(options, target, loaded) {
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Assign subject",
    size: "compact",
    bodyHtml: modalBody(target, loaded.folderPath),
    focusSelector: 'input[name="docs-project-subject"]:checked',
    actions: [
      { role: "modal-primary", label: "Save subject" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var field = api.host.querySelector("[data-project-subject-folder]");
      var input = api.host.querySelector("[data-project-subject-folder-input]");
      function projectChoice() {
        var selected = api.host.querySelector(
          'input[name="docs-project-subject"]:checked'
        );
        var folderSelected = selected && selected.value === "folder";
        var form = field && field.closest("form");
        var busy = Boolean(form && form.dataset.busy === "true");
        if (field) field.hidden = !folderSelected;
        if (input) input.disabled = busy || !folderSelected;
      }
      api.host.querySelectorAll('input[name="docs-project-subject"]').forEach(function (radio) {
        radio.addEventListener("change", projectChoice);
      });
      api.host.addEventListener("docs-viewer-modal-busy-change", projectChoice);
      projectChoice();
    },
    onSubmit: function (api) {
      var selected = api.host.querySelector(
        'input[name="docs-project-subject"]:checked'
      );
      var input = api.host.querySelector("[data-project-subject-folder-input]");
      if (!selected) {
        api.setStatus("Choose None or Folder.");
        return false;
      }
      var value = selected.value === "folder" && input ? input.value : "";
      if (selected.value === "folder" && !cleanString(value)) {
        api.setStatus("Paste a folder path or file URL.");
        if (input) input.focus();
        return false;
      }
      return options.assignFieldGroup(target, {
        source_revision: loaded.sourceRevision,
        field_group: AUTHORING_SUBJECT_GROUP_ID,
        fields: { folder_path: value },
        confirm: true
      }).then(function (response) {
        return {
          confirmed: true,
          payload: assignedSubject(response, target)
        };
      });
    }
  });
}

export function openDocsViewerProjectSubjectModal(options = {}) {
  var target = normalizeManagedDocumentTarget(options.target);
  if (!target.sub_scope) {
    return Promise.reject(new Error(
      "Projects subject assignment requires a sub-scope document target."
    ));
  }
  if (
    typeof options.readMetadata !== "function"
    || typeof options.assignFieldGroup !== "function"
  ) {
    return Promise.reject(new Error("Projects subject assignment service is unavailable."));
  }
  return Promise.resolve(options.readMetadata(target))
    .then(function (response) {
      return openSubjectModal(options, target, loadedSubject(response, target));
    });
}
