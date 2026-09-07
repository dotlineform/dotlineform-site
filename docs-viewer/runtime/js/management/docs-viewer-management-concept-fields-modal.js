import {
  escapeHtml,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";
import {
  managedDocumentTargetsEqual,
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

const CONCEPT_FIELDS_GROUP_ID = "concept_fields";
const CONCEPT_ID_PATTERN = /^[a-z0-9][a-z0-9-]*$/;

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function exactGroups(values) {
  if (!Array.isArray(values) || !values.length) {
    throw new Error("Concept fields require configured group choices.");
  }
  var seen = new Set();
  return Object.freeze(values.map(function (rawValue) {
    var value = cleanString(rawValue).toLowerCase();
    if (
      value !== rawValue
      || !/^[a-z0-9][a-z0-9_-]*$/.test(value)
      || seen.has(value)
    ) {
      throw new Error("Concept fields contain an invalid configured group choice.");
    }
    seen.add(value);
    return value;
  }));
}

function assertResponseTarget(response, target, message) {
  var candidate = {
    scope: response && response.scope,
    stage: response && response.stage,
    sub_scope: response && response.sub_scope,
    doc_id: response && response.doc_id
  };
  if (!managedDocumentTargetsEqual(candidate, target)) {
    throw new Error(message);
  }
}

function conceptDeclaration(rawValue) {
  if (
    typeof rawValue === "string"
    && rawValue
    && rawValue === cleanString(rawValue)
    && CONCEPT_ID_PATTERN.test(rawValue)
  ) {
    return { rawValue: rawValue, state: "valid", conceptId: rawValue };
  }
  if (rawValue == null || rawValue === "") {
    return { rawValue: "", state: "none", conceptId: "" };
  }
  return { rawValue: rawValue, state: "malformed", conceptId: "" };
}

function loadedConceptFields(response, target, groups) {
  if (!response || typeof response !== "object" || Array.isArray(response)) {
    throw new Error("Concept fields metadata could not be loaded.");
  }
  assertResponseTarget(
    response,
    target,
    "Loaded Concept fields metadata did not match its exact target."
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
    || !Object.prototype.hasOwnProperty.call(customisation, "concept_id")
    || typeof group !== "string"
    || group !== cleanString(group).toLowerCase()
    || (group && !groups.includes(group))
  ) {
    throw new Error("Loaded Concept fields record is invalid.");
  }
  var sourceRevision = cleanString(response.source_revision);
  if (!/^sha256:[0-9a-f]{64}$/.test(sourceRevision)) {
    throw new Error("Concept fields source revision could not be loaded.");
  }
  return Object.freeze({
    group: group,
    sourceRevision: sourceRevision,
    concept: Object.freeze(conceptDeclaration(customisation.concept_id))
  });
}

function assignedConceptFields(response, target, groups) {
  if (!response || typeof response !== "object" || Array.isArray(response)) {
    throw new Error("Concept fields assignment returned an invalid response.");
  }
  if (!managedDocumentTargetsEqual(response.target, target)) {
    throw new Error("Concept fields assignment did not match its exact target.");
  }
  var fields = response.fields;
  var group = fields && fields.group;
  var concept = conceptDeclaration(fields && fields.concept_id);
  if (
    cleanString(response.field_group) !== CONCEPT_FIELDS_GROUP_ID
    || !fields
    || typeof fields !== "object"
    || Array.isArray(fields)
    || Object.keys(fields).sort().join(",") !== "concept_id,group"
    || typeof group !== "string"
    || group !== cleanString(group).toLowerCase()
    || (group && !groups.includes(group))
    || !["none", "valid", "malformed"].includes(concept.state)
    || !/^sha256:[0-9a-f]{64}$/.test(cleanString(response.source_revision))
  ) {
    throw new Error("Concept fields assignment response is invalid.");
  }
  return response;
}

function conceptInputValue(loaded) {
  if (loaded.concept.state === "none") return "";
  var value = loaded.concept.rawValue;
  return typeof value === "string" ? value : JSON.stringify(value);
}

function modalBody(groups, loaded) {
  var groupOptions = [{ value: "", label: "No group" }].concat(groups.map(function (group) {
    return { value: group, label: group };
  }));
  return '<label class="docsViewer__field" for="docsViewerConceptFieldsGroup">' +
    '<span class="docsViewer__fieldLabel">Group</span>' +
    '<select class="docsViewer__fieldInput" id="docsViewerConceptFieldsGroup" data-docs-concept-fields-group>' +
      groupOptions.map(function (option) {
        return '<option value="' + escapeHtml(option.value) + '"' +
          (option.value === loaded.group ? " selected" : "") + '>' +
          escapeHtml(option.label) + '</option>';
      }).join("") +
    '</select></label>' +
    '<label class="docsViewer__field" for="docsViewerConceptFieldsId">' +
      '<span class="docsViewer__fieldLabel">Concept ID</span>' +
      '<input class="docsViewer__fieldInput" id="docsViewerConceptFieldsId" ' +
        'data-docs-concept-fields-id type="text" value="' + escapeHtml(conceptInputValue(loaded)) + '" ' +
        'placeholder="None" autocomplete="off" spellcheck="false">' +
    '</label>';
}

function openConceptFieldsModal(options, target, groups, loaded) {
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Concept fields",
    size: "compact",
    bodyHtml: modalBody(groups, loaded),
    focusSelector: "[data-docs-concept-fields-group]",
    actions: [
      { role: "modal-primary", label: "OK" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onSubmit: function (api) {
      var input = api.host.querySelector("[data-docs-concept-fields-group]");
      var group = cleanString(input && input.value).toLowerCase();
      var conceptInput = api.host.querySelector("[data-docs-concept-fields-id]");
      var value = String(conceptInput && conceptInput.value || "");
      var unchangedMalformed = loaded.concept.state === "malformed" && value === conceptInputValue(loaded);
      if (group && !groups.includes(group)) {
        api.setStatus("Choose a configured group or No group.");
        return false;
      }
      if (value && !unchangedMalformed && !CONCEPT_ID_PATTERN.test(value)) {
        api.setStatus("Use lowercase letters, numbers and hyphens for the Concept ID, or leave it empty.");
        return false;
      }
      var conceptId = unchangedMalformed ? loaded.concept.rawValue : value;
      return options.assignFieldGroup(target, {
        source_revision: loaded.sourceRevision,
        field_group: CONCEPT_FIELDS_GROUP_ID,
        fields: { group: group, concept_id: conceptId },
        confirm: true
      }).then(function (response) {
        return {
          confirmed: true,
          payload: assignedConceptFields(response, target, groups)
        };
      });
    }
  });
}

export function openDocsViewerConceptFieldsModal(options = {}) {
  var target = normalizeManagedDocumentTarget(options.target);
  if (!target.sub_scope) {
    return Promise.reject(new Error("Concept fields require a sub-scope document target."));
  }
  if (
    typeof options.readMetadata !== "function"
    || typeof options.assignFieldGroup !== "function"
  ) {
    return Promise.reject(new Error("Concept fields service is unavailable."));
  }
  var groups;
  try {
    groups = exactGroups(options.groups);
  } catch (error) {
    return Promise.reject(error);
  }
  return Promise.resolve(options.readMetadata(target)).then(function (response) {
    var loaded = loadedConceptFields(response, target, groups);
    return openConceptFieldsModal(options, target, groups, loaded);
  });
}
