import {
  escapeHtml,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";
import {
  managedDocumentTargetsEqual,
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";

const TAG_FIELDS_GROUP_ID = "tag_fields";
const CURRENT_MALFORMED_TAG_VALUE = "__current_malformed_tag__";
const TAG_ID_PATTERN = /^[a-z0-9][a-z0-9-]*$/;

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

function tagDeclaration(rawValue) {
  if (
    typeof rawValue === "string"
    && rawValue
    && rawValue === cleanString(rawValue)
    && TAG_ID_PATTERN.test(rawValue)
  ) {
    return { rawValue: rawValue, state: "valid", tagId: rawValue };
  }
  if (rawValue === "") {
    return { rawValue: "", state: "none", tagId: "" };
  }
  return { rawValue: rawValue, state: "malformed", tagId: "" };
}

function exactCanonicalTags(payload) {
  var rows = payload && Array.isArray(payload.tags) ? payload.tags : null;
  if (!rows) throw new Error("Canonical Tags could not be loaded.");
  var seen = new Set();
  return Object.freeze(rows.map(function (row) {
    var tagId = row && row.tag_id;
    var group = row && row.group;
    if (
      typeof tagId !== "string"
      || tagId !== cleanString(tagId)
      || !TAG_ID_PATTERN.test(tagId)
      || seen.has(tagId)
      || typeof group !== "string"
      || group !== cleanString(group).toLowerCase()
      || !group
    ) {
      throw new Error("Canonical Tags contain an invalid record.");
    }
    seen.add(tagId);
    return Object.freeze({ group: group, tagId: tagId });
  }).sort(function (left, right) {
    return left.tagId.localeCompare(right.tagId);
  }));
}

function registryUrl(studioBaseUrl) {
  var base = cleanString(studioBaseUrl).replace(/\/+$/, "");
  var studio;
  try {
    studio = new URL(base);
  } catch (error) {
    throw new Error("Local Studio is not configured.", { cause: error });
  }
  if (
    studio.protocol !== "http:"
    || !["127.0.0.1", "localhost", "::1", "[::1]"].includes(studio.hostname)
    || studio.username
    || studio.password
    || studio.pathname !== "/"
    || studio.search
    || studio.hash
  ) {
    throw new Error("Local Studio is not configured.");
  }
  return new URL("/studio/api/tags/tag-registry", studio.origin).toString();
}

function loadCanonicalTags(options) {
  if (typeof options.loadTags === "function") {
    return Promise.resolve(options.loadTags()).then(exactCanonicalTags);
  }
  var url;
  try {
    url = registryUrl(options.studioBaseUrl);
  } catch (error) {
    return Promise.reject(error);
  }
  return window.fetch(url, {
    cache: "no-store",
    headers: { Accept: "application/json" }
  }).then(function (response) {
    if (!response.ok) throw new Error("Canonical Tags could not be loaded.");
    return response.json();
  }).then(exactCanonicalTags);
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
    || !Object.prototype.hasOwnProperty.call(customisation, "tag_id")
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
  return Object.freeze({
    group: group,
    sourceRevision: sourceRevision,
    tag: Object.freeze(tagDeclaration(customisation.tag_id))
  });
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
  var tag = tagDeclaration(fields && fields.tag_id);
  if (
    cleanString(response.field_group) !== TAG_FIELDS_GROUP_ID
    || !fields
    || typeof fields !== "object"
    || Array.isArray(fields)
    || Object.keys(fields).sort().join(",") !== "group,tag_id"
    || typeof group !== "string"
    || group !== cleanString(group).toLowerCase()
    || (group && !groups.includes(group))
    || !["none", "valid", "malformed"].includes(tag.state)
    || !/^sha256:[0-9a-f]{64}$/.test(cleanString(response.source_revision))
  ) {
    throw new Error("Tag fields assignment response is invalid.");
  }
  return response;
}

function modalBody(groups, tags, loaded) {
  var groupOptions = [{ value: "", label: "No group" }].concat(groups.map(function (group) {
    return { value: group, label: group };
  }));
  var tagOptions = [{ value: "", label: "No tag" }];
  if (loaded.tag.state === "malformed") {
    tagOptions.push({
      value: CURRENT_MALFORMED_TAG_VALUE,
      label: "Malformed current value"
    });
  } else if (
    loaded.tag.state === "valid"
    && !tags.some(function (tag) { return tag.tagId === loaded.tag.tagId; })
  ) {
    tagOptions.push({
      value: loaded.tag.tagId,
      label: loaded.tag.tagId + " — Unavailable"
    });
  }
  tags.forEach(function (tag) {
    tagOptions.push({
      value: tag.tagId,
      label: tag.tagId + " — " + tag.group
    });
  });
  var selectedTag = loaded.tag.state === "malformed"
    ? CURRENT_MALFORMED_TAG_VALUE
    : loaded.tag.tagId;
  return '<label class="docsViewer__field" for="docsViewerTagFieldsGroup">' +
    '<span class="docsViewer__fieldLabel">Group</span>' +
    '<select class="docsViewer__fieldInput" id="docsViewerTagFieldsGroup" ' +
      'data-docs-tag-fields-group>' +
      groupOptions.map(function (option) {
        return '<option value="' + escapeHtml(option.value) + '"' +
          (option.value === loaded.group ? " selected" : "") + '>' +
          escapeHtml(option.label) +
        "</option>";
      }).join("") +
    "</select>" +
  "</label>" +
  '<label class="docsViewer__field" for="docsViewerTagFieldsTag">' +
    '<span class="docsViewer__fieldLabel">Tag</span>' +
    '<select class="docsViewer__fieldInput" id="docsViewerTagFieldsTag" ' +
      'data-docs-tag-fields-tag>' +
      tagOptions.map(function (option) {
        return '<option value="' + escapeHtml(option.value) + '"' +
          (option.value === selectedTag ? " selected" : "") + '>' +
          escapeHtml(option.label) +
        "</option>";
      }).join("") +
    "</select>" +
  "</label>";
}

function openTagFieldsModal(options, target, groups, tags, loaded) {
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Tag fields",
    size: "compact",
    bodyHtml: modalBody(groups, tags, loaded),
    focusSelector: "[data-docs-tag-fields-group]",
    actions: [
      { role: "modal-primary", label: "OK" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onSubmit: function (api) {
      var input = api.host.querySelector("[data-docs-tag-fields-group]");
      var group = cleanString(input && input.value).toLowerCase();
      var tagInput = api.host.querySelector("[data-docs-tag-fields-tag]");
      var selectedTag = String(tagInput && tagInput.value || "");
      if (group && !groups.includes(group)) {
        api.setStatus("Choose a configured group or No group.");
        return false;
      }
      if (
        selectedTag
        && selectedTag !== CURRENT_MALFORMED_TAG_VALUE
        && !tags.some(function (tag) { return tag.tagId === selectedTag; })
        && !(loaded.tag.state === "valid" && loaded.tag.tagId === selectedTag)
      ) {
        api.setStatus("Choose a canonical Tag or No tag.");
        return false;
      }
      var tagId = selectedTag === CURRENT_MALFORMED_TAG_VALUE
        ? loaded.tag.rawValue
        : selectedTag;
      return options.assignFieldGroup(target, {
        source_revision: loaded.sourceRevision,
        field_group: TAG_FIELDS_GROUP_ID,
        fields: { group: group, tag_id: tagId },
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
    || (!cleanString(options.studioBaseUrl) && typeof options.loadTags !== "function")
  ) {
    return Promise.reject(new Error("Tag fields service is unavailable."));
  }
  var groups;
  try {
    groups = exactGroups(options.groups);
  } catch (error) {
    return Promise.reject(error);
  }
  return Promise.all([
    Promise.resolve(options.readMetadata(target)),
    loadCanonicalTags(options)
  ]).then(function (responses) {
    var loaded = loadedTagFields(responses[0], target, groups);
    return openTagFieldsModal(
      options,
      target,
      groups,
      responses[1],
      loaded
    );
  });
}
