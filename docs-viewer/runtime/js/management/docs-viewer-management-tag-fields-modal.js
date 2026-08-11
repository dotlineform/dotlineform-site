import {
  escapeHtml,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";
import {
  managedDocumentTargetsEqual,
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

const TAG_FIELDS_GROUP_ID = "tag_fields";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function exactGroups(values) {
  if (!Array.isArray(values) || !values.length) {
    throw new Error("Tag fields require configured group choices.");
  }
  var seen = new Set();
  return Object.freeze(values.map(function (rawValue) {
    var value = cleanString(rawValue).toLowerCase();
    if (
      value !== rawValue
      || !/^[a-z0-9][a-z0-9_-]*$/.test(value)
      || seen.has(value)
    ) {
      throw new Error("Tag fields contain an invalid configured group choice.");
    }
    seen.add(value);
    return value;
  }));
}

function assertResponseTarget(response, target, message) {
  var candidate = {
    scope: response && response.scope,
    sub_scope: response && response.sub_scope,
    doc_id: response && response.doc_id
  };
  if (!managedDocumentTargetsEqual(candidate, target)) {
    throw new Error(message);
  }
}

function loadedTagFields(response, target, groups) {
  if (!response || typeof response !== "object" || Array.isArray(response)) {
    throw new Error("Tag fields metadata could not be loaded.");
  }
  assertResponseTarget(
    response,
    target,
    "Loaded Tag fields metadata did not match its exact target."
  );
  var record = response.record;
  var customisation = record && record.customisation;
  var group = customisation && customisation.group;
  if (
    !record
    || typeof record !== "object"
    || Array.isArray(record)
    || cleanString(record.doc_id) !== target.doc_id
    || !customisation
    || typeof customisation !== "object"
    || Array.isArray(customisation)
    || typeof group !== "string"
    || group !== cleanString(group).toLowerCase()
    || (group && !groups.includes(group))
  ) {
    throw new Error("Loaded Tag fields record is invalid.");
  }
  var sourceRevision = cleanString(response.source_revision);
  if (!/^sha256:[0-9a-f]{64}$/.test(sourceRevision)) {
    throw new Error("Tag fields source revision could not be loaded.");
  }
  return Object.freeze({ group: group, sourceRevision: sourceRevision });
}

function assignedTagFields(response, target, groups) {
  if (!response || typeof response !== "object" || Array.isArray(response)) {
    throw new Error("Tag fields assignment returned an invalid response.");
  }
  if (!managedDocumentTargetsEqual(response.target, target)) {
    throw new Error("Tag fields assignment did not match its exact target.");
  }
  var fields = response.fields;
  var group = fields && fields.group;
  if (
    cleanString(response.field_group) !== TAG_FIELDS_GROUP_ID
    || !fields
    || typeof fields !== "object"
    || Array.isArray(fields)
    || Object.keys(fields).length !== 1
    || typeof group !== "string"
    || group !== cleanString(group).toLowerCase()
    || (group && !groups.includes(group))
    || !/^sha256:[0-9a-f]{64}$/.test(cleanString(response.source_revision))
  ) {
    throw new Error("Tag fields assignment response is invalid.");
  }
  return response;
}

function modalBody(groups, selectedGroup) {
  var options = [{ value: "", label: "No group" }].concat(groups.map(function (group) {
    return { value: group, label: group };
  }));
  return '<label class="docsViewer__field" for="docsViewerTagFieldsGroup">' +
    '<span class="docsViewer__fieldLabel">Group</span>' +
    '<select class="docsViewer__fieldInput" id="docsViewerTagFieldsGroup" ' +
      'data-docs-tag-fields-group>' +
      options.map(function (option) {
        return '<option value="' + escapeHtml(option.value) + '"' +
          (option.value === selectedGroup ? " selected" : "") + '>' +
          escapeHtml(option.label) +
        "</option>";
      }).join("") +
    "</select>" +
  "</label>";
}

function openTagFieldsModal(options, target, groups, loaded) {
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Tag fields",
    size: "compact",
    bodyHtml: modalBody(groups, loaded.group),
    focusSelector: "[data-docs-tag-fields-group]",
    actions: [
      { role: "modal-primary", label: "OK" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onSubmit: function (api) {
      var input = api.host.querySelector("[data-docs-tag-fields-group]");
      var group = cleanString(input && input.value).toLowerCase();
      if (group && !groups.includes(group)) {
        api.setStatus("Choose a configured group or No group.");
        return false;
      }
      return options.assignFieldGroup(target, {
        source_revision: loaded.sourceRevision,
        field_group: TAG_FIELDS_GROUP_ID,
        fields: { group: group },
        confirm: true
      }).then(function (response) {
        return {
          confirmed: true,
          payload: assignedTagFields(response, target, groups)
        };
      });
    }
  });
}

export function openDocsViewerTagFieldsModal(options = {}) {
  var target = normalizeManagedDocumentTarget(options.target);
  if (!target.sub_scope) {
    return Promise.reject(new Error("Tag fields require a sub-scope document target."));
  }
  if (
    typeof options.readMetadata !== "function"
    || typeof options.assignFieldGroup !== "function"
  ) {
    return Promise.reject(new Error("Tag fields service is unavailable."));
  }
  var groups;
  try {
    groups = exactGroups(options.groups);
  } catch (error) {
    return Promise.reject(error);
  }
  return Promise.resolve(options.readMetadata(target)).then(function (response) {
    return openTagFieldsModal(
      options,
      target,
      groups,
      loadedTagFields(response, target, groups)
    );
  });
}
