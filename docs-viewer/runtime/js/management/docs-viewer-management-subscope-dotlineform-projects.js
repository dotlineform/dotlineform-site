import {
  encodeDecodedLocalTarget
} from "./docs-viewer-management-client.js";

const CUSTOMISATION_ID = "dotlineform_projects";

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

function folderPath(documentRecord, options = {}) {
  var customisation = documentRecord && documentRecord.customisation;
  if (customisation == null) {
    if (options.required) {
      throw new Error("Projects metadata customisation is missing.");
    }
    return "";
  }
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

function mountMetadataEditor(context) {
  var settings = context || {};
  var host = settings.host;
  if (!host) throw new Error("Projects metadata editor host is unavailable.");
  exactCollection({
    scope: settings.target && settings.target.scope,
    sub_scope: settings.target && settings.target.sub_scope
  });
  var path = folderPath(settings.record, { required: true });
  host.replaceChildren();
  var label = host.ownerDocument.createElement("label");
  label.className = "docsViewer__field docsViewer__field--projectsFolder";
  var labelText = host.ownerDocument.createElement("span");
  labelText.className = "docsViewer__fieldLabel";
  labelText.textContent = "Folder Link";
  var input = host.ownerDocument.createElement("input");
  input.className = "docsViewer__fieldInput";
  input.name = "folder_path";
  input.type = "text";
  input.autocomplete = "off";
  input.spellcheck = false;
  input.value = path;
  label.appendChild(labelText);
  label.appendChild(input);
  host.appendChild(label);
  host.hidden = false;
  return {
    read: function () {
      return { folder_path: input.value };
    },
    destroy: function () {
      host.replaceChildren();
      host.hidden = true;
    }
  };
}

export function createDocsViewerManagementSubscopeDotlineformProjects(options = {}) {
  var descriptorId = cleanString(options.descriptor && options.descriptor.id);
  if (descriptorId !== CUSTOMISATION_ID) {
    throw new Error("Projects customisation identity did not match its registry entry.");
  }
  exactCollection(options.collection);
  return {
    id: CUSTOMISATION_ID,
    mountMetadataEditor: mountMetadataEditor,
    renderDetailToolbar: function (context) {
      renderOpenInFinder(context, options);
    },
    renderRow: renderFolderState
  };
}
