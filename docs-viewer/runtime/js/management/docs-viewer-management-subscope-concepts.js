import { hasDocsViewerAssignableFieldGroup } from "../shared/docs-viewer-config-controller.js";
import { managedDocumentTargetsEqual, normalizeManagedDocumentCollectionTarget, normalizeManagedDocumentTarget } from "./docs-viewer-management-document-target.js";
import { documentIdentityInfoField, documentIdentityMetadataRevision, renderDocumentIdentityControl } from "./docs-viewer-management-document-identity.js";

const GROUP_ID = "concept_group";

function normalizeFilterValue(value) {
  return String(value == null ? "" : value).trim().normalize("NFKC").replace(/\s+/g, " ").toLowerCase();
}

function normalizedGroups(data) {
  return [...new Set((data && Array.isArray(data.groups) ? data.groups : []).map(normalizeFilterValue).filter(Boolean))];
}

function assertCollection(value, expected) {
  var collection = normalizeManagedDocumentCollectionTarget(value);
  if (collection.scope !== expected.scope || collection.stage !== expected.stage || collection.sub_scope !== expected.sub_scope) {
    throw new Error("Concept customisation collection did not match its registry entry.");
  }
}

function groupInfoField(record, groups) {
  var group = normalizeFilterValue(record && record.customisation && record.customisation.group);
  return {
    id: GROUP_ID, label: "Group", detail: group && !groups.includes(group) ? group : "",
    state: !group ? "unassigned" : groups.includes(group) ? "assigned" : "unavailable",
    value: !group ? "Unassigned" : groups.includes(group) ? group : "Unavailable"
  };
}

function renderConceptGroup(context, options) {
  var host = context.host;
  var groups = normalizedGroups(context.data);
  if (!host || !groups.length || typeof context.registerAction !== "function") return;
  var select = host.ownerDocument.createElement("select");
  select.className = "docsViewer__fieldInput";
  select.setAttribute("aria-label", "Concept group");
  ["", ...groups].forEach(function (group) {
    var option = host.ownerDocument.createElement("option");
    option.value = group;
    option.textContent = group || "No group";
    select.appendChild(option);
  });
  var current = normalizeFilterValue(context.document && context.document.customisation && context.document.customisation.group);
  select.value = current;
  var registration = context.registerAction({
    id: "assign-concept-group", placement: "detail-toolbar", targetKind: "validated-detail",
    capability: typeof options.readMetadata === "function" && typeof options.assignFieldGroup === "function",
    emptyState: "omitted", refreshEffect: "none",
    handler: async function (target, actionContext) {
      var group = select.value;
      var metadata = await options.readMetadata(target);
      var response = await options.assignFieldGroup(target, {
        source_revision: documentIdentityMetadataRevision(metadata, target), confirm: true,
        field_group: GROUP_ID, fields: { group: group }
      });
      if (!response || response.ok !== true || !managedDocumentTargetsEqual(response.target, target)
        || response.field_group !== GROUP_ID || !response.fields || response.fields.group !== group
        || Object.keys(response.fields).join(",") !== "group") {
        throw new Error("Concept group assignment returned an invalid response.");
      }
      current = group;
      if (actionContext && typeof actionContext.refreshDocument === "function") await actionContext.refreshDocument(target);
      return response;
    }
  });
  if (registration.hidden) return;
  select.disabled = !registration.enabled;
  select.addEventListener("change", function () {
    if (select.disabled) return;
    select.disabled = true;
    registration.invoke().catch(function (error) {
      select.value = current;
      if (typeof options.setStatus === "function") options.setStatus(error.message || "Concept group assignment failed.", true);
    }).finally(function () {
      if (select.isConnected) select.disabled = !registration.enabled;
    });
  });
  host.appendChild(select);
}

function groupFilter(groups) {
  return {
    id: "group", initialValue: "",
    matches: function (context) {
      var value = normalizeFilterValue(context && context.value);
      var record = context && context.document;
      return !value || normalizeFilterValue(record && record.customisation && record.customisation.group) === value;
    },
    render: function (context) {
      var host = context && context.host;
      if (!host || typeof context.setValue !== "function") return;
      var active = normalizeFilterValue(context.value);
      host.setAttribute("role", "group");
      host.setAttribute("aria-label", "Filter Concepts by group");
      ["", ...groups].forEach(function (group) {
        var button = host.ownerDocument.createElement("button");
        button.className = "docsViewerReport__filter";
        button.type = "button";
        button.dataset.docsSubscopeGroup = group;
        button.textContent = group || "all";
        button.setAttribute("aria-pressed", group === active ? "true" : "false");
        button.addEventListener("click", function () { context.setValue(group); });
        host.appendChild(button);
      });
    }
  };
}

/** Expose independent numeric Concept allocation and inline group assignment in Working. */
export function createDocsViewerManagementSubscopeConcepts(options = {}) {
  var collection = normalizeManagedDocumentCollectionTarget(options.collection);
  if (options.descriptor.id !== "concepts" || options.descriptor.capabilities.identityKind !== "concept"
    || !collection.sub_scope || collection.stage !== "working") {
    throw new Error("Concept identity requires its configured Working collection.");
  }
  var groupAvailable = hasDocsViewerAssignableFieldGroup(options.descriptor, GROUP_ID);
  return {
    id: "concepts",
    createFilters: function (context) {
      assertCollection(context.collection, collection);
      var groups = normalizedGroups(context.data);
      if (!groups.length) throw new Error("Concept customisation requires manifest groups.");
      return [groupFilter(groups)];
    },
    projectDetailInfo: function (context) {
      assertCollection(context.collection, collection);
      var target = normalizeManagedDocumentTarget(context.target);
      if (target.scope !== collection.scope || target.stage !== collection.stage
        || target.sub_scope !== collection.sub_scope || target.doc_id !== context.document.doc_id) {
        throw new Error("Concept identity target did not match its collection.");
      }
      return {
        actions: { conceptGroup: groupAvailable },
        fields: [groupInfoField(context.document, normalizedGroups(context.data)), documentIdentityInfoField(context.document, "concept")]
      };
    },
    renderDetailToolbar: function (context) {
      renderDocumentIdentityControl(context, options, "concept");
      if (groupAvailable) renderConceptGroup(context, options);
    }
  };
}
