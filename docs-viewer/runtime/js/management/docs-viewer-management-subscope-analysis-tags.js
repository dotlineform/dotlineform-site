import {
  hasDocsViewerAssignableFieldGroup
} from "../shared/docs-viewer-config-controller.js";
import {
  openDocsViewerTagFieldsModal
} from "./docs-viewer-management-tag-fields-modal.js";

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

function renderTagFields(context, options, tagFieldsAvailable) {
  var settings = context || {};
  var host = settings.host;
  if (!host || !tagFieldsAvailable || typeof settings.registerAction !== "function") return;
  var groups = normalizedGroups(settings.data);
  var servicesAvailable = (
    typeof options.readMetadata === "function"
    && typeof options.assignFieldGroup === "function"
  );
  var capability = servicesAvailable && groups.length
    ? true
    : {
        available: false,
        reason: groups.length
          ? "Tag fields service is unavailable."
          : "Configured Tag groups are unavailable."
      };
  var button = host.ownerDocument.createElement("button");
  var registration = settings.registerAction({
    id: "assign-tag-fields",
    placement: "detail-toolbar",
    targetKind: "validated-detail",
    capability: capability,
    emptyState: "omitted",
    refreshEffect: "none",
    handler: function (target, actionContext) {
      return openDocsViewerTagFieldsModal({
        assignFieldGroup: options.assignFieldGroup,
        groups: groups,
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
          return result.payload;
        });
      });
    }
  });
  if (registration.hidden) return;
  button.className = "docsViewerReport__button docsReportDetail__iconButton docsReportDetail__tagFields";
  button.type = "button";
  button.dataset.docsTagFields = "true";
  button.textContent = "Tag fields";
  button.disabled = !registration.enabled;
  if (registration.disabledReason) button.title = registration.disabledReason;
  button.addEventListener("click", function () {
    if (button.disabled) return;
    button.disabled = true;
    registration.invoke().catch(function (error) {
      if (typeof options.setStatus === "function") {
        options.setStatus(
          error && error.message ? error.message : "Tag fields assignment failed.",
          true
        );
      }
    }).finally(function () {
      if (button.isConnected) button.disabled = !registration.enabled;
    });
  });
  host.appendChild(button);
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
    },
    renderDetailToolbar: function (context) {
      renderTagFields(context, options, tagFieldsAvailable);
    }
  };
}
