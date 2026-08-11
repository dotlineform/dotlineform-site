import {
  hasDocsViewerAssignableFieldGroup
} from "../shared/docs-viewer-config-controller.js";

const CUSTOMISATION_ID = "analysis_tags";
const TAG_FIELDS_GROUP_ID = "tag_fields";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeFilterValue(value) {
  return cleanString(value).normalize("NFKC").replace(/\s+/g, " ").toLowerCase();
}

function normalizedGroups(data) {
  var values = data && Array.isArray(data.groups) ? data.groups : [];
  var seen = new Set();
  return values.map(normalizeFilterValue).filter(function (value) {
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  });
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
    throw new Error("Analysis/Tags customisation collection target is invalid.");
  }
  return Object.freeze({ scope: scope, sub_scope: subScope });
}

function assertCollection(value, expected) {
  var collection = exactCollection(value);
  if (collection.scope !== expected.scope || collection.sub_scope !== expected.sub_scope) {
    throw new Error("Analysis/Tags customisation collection did not match its registry entry.");
  }
}

function groupInfoField(documentRecord, groups) {
  var customisation = documentRecord && documentRecord.customisation;
  if (
    customisation != null
    && (typeof customisation !== "object" || Array.isArray(customisation))
  ) {
    return {
      detail: "Metadata projection unavailable",
      id: TAG_FIELDS_GROUP_ID,
      label: "Group",
      state: "unavailable",
      value: "Unavailable"
    };
  }
  var group = normalizeFilterValue(customisation && customisation.group);
  if (!group) {
    return {
      detail: "",
      id: TAG_FIELDS_GROUP_ID,
      label: "Group",
      state: "unassigned",
      value: "Unassigned"
    };
  }
  if (!groups.includes(group)) {
    return {
      detail: group,
      id: TAG_FIELDS_GROUP_ID,
      label: "Group",
      state: "unavailable",
      value: "Unavailable"
    };
  }
  return {
    detail: "",
    id: TAG_FIELDS_GROUP_ID,
    label: "Group",
    state: "assigned",
    value: group
  };
}

function projectDetailInfo(context, collection, tagFieldsAvailable) {
  var settings = context || {};
  assertCollection(settings.collection, collection);
  var target = settings.target || {};
  var targetKeys = Object.keys(target).sort();
  var documentRecord = settings.document || {};
  if (
    targetKeys.length !== 3
    || targetKeys[0] !== "doc_id"
    || targetKeys[1] !== "scope"
    || targetKeys[2] !== "sub_scope"
    || cleanString(target.scope).toLowerCase() !== collection.scope
    || cleanString(target.sub_scope).toLowerCase() !== collection.sub_scope
    || !cleanString(target.doc_id)
    || cleanString(target.doc_id) !== cleanString(documentRecord.doc_id)
  ) {
    throw new Error("Analysis/Tags metadata target is invalid.");
  }
  return Object.freeze({
    actions: Object.freeze({ tagFields: tagFieldsAvailable }),
    fields: Object.freeze([
      Object.freeze(groupInfoField(documentRecord, normalizedGroups(settings.data)))
    ])
  });
}

function groupFilter(groups) {
  return {
    id: "group",
    initialValue: "",
    matches: function (context) {
      var value = normalizeFilterValue(context && context.value);
      var documentRecord = context && context.document;
      var customisation = documentRecord && documentRecord.customisation;
      return !value || normalizeFilterValue(customisation && customisation.group) === value;
    },
    render: function (context) {
      var settings = context || {};
      var host = settings.host;
      if (!host || typeof settings.setValue !== "function") return;
      var activeValue = normalizeFilterValue(settings.value);
      host.setAttribute("role", "group");
      host.setAttribute("aria-label", "Filter Tags by group");
      ["", ...groups].forEach(function (group) {
        var button = host.ownerDocument.createElement("button");
        button.className = "docsViewerReport__filter";
        button.type = "button";
        button.dataset.docsSubscopeGroup = group;
        button.textContent = group || "all";
        button.setAttribute("aria-pressed", group === activeValue ? "true" : "false");
        button.addEventListener("click", function () {
          settings.setValue(group);
        });
        host.appendChild(button);
      });
    }
  };
}

export function createDocsViewerManagementSubscopeAnalysisTags(options = {}) {
  var descriptorId = cleanString(options.descriptor && options.descriptor.id);
  if (descriptorId !== CUSTOMISATION_ID) {
    throw new Error("Analysis/Tags customisation identity did not match its registry entry.");
  }
  var collection = exactCollection(options.collection);
  var tagFieldsAvailable = hasDocsViewerAssignableFieldGroup(
    options.descriptor,
    TAG_FIELDS_GROUP_ID
  );
  return {
    id: CUSTOMISATION_ID,
    createFilters: function (context) {
      assertCollection(context && context.collection, collection);
      var groups = normalizedGroups(context && context.data);
      if (!groups.length) {
        throw new Error("Analysis/Tags customisation requires manifest groups.");
      }
      return [groupFilter(groups)];
    },
    projectDetailInfo: function (context) {
      return projectDetailInfo(context, collection, tagFieldsAvailable);
    }
  };
}
