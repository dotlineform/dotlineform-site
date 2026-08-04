import {
  escapeHtml,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";
import {
  managedDocumentTargetsEqual,
  normalizeManagedDocumentTarget
} from "./docs-viewer-management-document-target.js";
import {
  AUTHORING_SUBJECT_FIELDS,
  normalizeDocsViewerAuthoringSubject
} from "./docs-viewer-management-document-subject.js";
import {
  collectCatalogueTargetMatches,
  findCatalogueTargetByIdentity,
  loadCatalogueTargetSupport
} from "./source-editor/catalogue-token-targets.js";
import {
  createCatalogueTargetPickerList
} from "./source-editor/catalogue-target-picker.js";

const AUTHORING_SUBJECT_GROUP_ID = "authoring_subject";
const SEARCH_INPUT_ID = "docsViewerProjectSubjectCatalogueSearch";
const RESULTS_ID = "docsViewerProjectSubjectCatalogueResults";

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

function normalizedSubject(record) {
  return normalizeDocsViewerAuthoringSubject(
    record && record.authoring_subject,
    {
      errorMessage: "Loaded Projects subject metadata is invalid."
    }
  );
}

function exactSubjectFields(fields) {
  return (
    fields
    && typeof fields === "object"
    && !Array.isArray(fields)
    && Object.keys(fields).sort().join(",")
      === AUTHORING_SUBJECT_FIELDS.slice().sort().join(",")
    && AUTHORING_SUBJECT_FIELDS.every(function (field) {
      return typeof fields[field] === "string";
    })
  );
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
    subject: normalizedSubject(response.record),
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
  var fields = response.fields;
  if (
    cleanString(response.field_group) !== AUTHORING_SUBJECT_GROUP_ID
    || !exactSubjectFields(fields)
    || !/^sha256:[0-9a-f]{64}$/.test(cleanString(response.source_revision))
  ) {
    throw new Error("Projects subject assignment response is invalid.");
  }
  return response;
}

function selectedKind(subject) {
  return subject.state === "valid" ? subject.kind : (subject.state === "none" ? "none" : "");
}

function evidenceText(subject) {
  if (subject.state === "malformed") {
    return "The current " + subject.fields[0] + " declaration " + JSON.stringify(subject.evidence[subject.fields[0]]) + " is malformed. Choose a replacement or None.";
  }
  if (subject.state === "conflicting") {
    var declarations = subject.fields.map(function (field) {
      return field + "=" + JSON.stringify(subject.evidence[field]);
    }).join(", ");
    return "The current declarations conflict: " + declarations + ". Choose one replacement or None.";
  }
  return "";
}

function radio(value, label, selected) {
  return '<label class="docsViewer__field docsViewer__field--checkbox">' +
    '<input class="docsViewer__checkboxInput" type="radio" name="docs-project-subject" value="' + value + '"' +
      (selected === value ? " checked" : "") + ">" +
    '<span class="docsViewer__fieldLabel">' + label + "</span>" +
  "</label>";
}

function modalBody(target, subject) {
  var selected = selectedKind(subject);
  var folderValue = subject.state === "valid" && subject.kind === "folder" ? subject.key : "";
  var evidence = evidenceText(subject);
  return "" +
    '<p class="docsViewer__modalNote muted small">Assign the authoring subject for <code>' +
      escapeHtml(target.doc_id) + "</code>.</p>" +
    (evidence ? '<p class="docsViewer__modalNote docsViewerProjectSubjectModal__warning small" data-project-subject-evidence>' + escapeHtml(evidence) + "</p>" : "") +
    '<fieldset class="docsViewer__fieldGroup" data-project-subject-options>' +
      '<legend class="docsViewer__fieldLabel">Subject</legend>' +
      radio("none", "None", selected) +
      radio("folder", "Folder", selected) +
      radio("work", "Work", selected) +
      radio("series", "Series", selected) +
    "</fieldset>" +
    '<label class="docsViewer__field" data-project-subject-folder' +
      (selected === "folder" ? "" : " hidden") + ">" +
      '<span class="docsViewer__fieldLabel">Folder path or file URL</span>' +
      '<input class="docsViewer__fieldInput" data-project-subject-folder-input type="text" ' +
        'autocomplete="off" spellcheck="false" value="' + escapeHtml(folderValue) + '">' +
    "</label>" +
    '<section class="docsViewerProjectSubjectModal__catalogue" data-project-subject-catalogue' +
      (["work", "series"].includes(selected) ? "" : " hidden") + ">" +
      '<label class="docsViewer__field" for="' + SEARCH_INPUT_ID + '">' +
        '<span class="docsViewer__fieldLabel">Search Catalogue</span>' +
        '<input class="docsViewer__fieldInput" id="' + SEARCH_INPUT_ID + '" type="search" role="combobox" aria-autocomplete="list" aria-controls="' + RESULTS_ID + '" aria-expanded="true" autocomplete="off" spellcheck="false" disabled>' +
      "</label>" +
      '<p class="docsViewerCatalogueTokenModal__searchStatus muted small" data-project-subject-search-status>Choose Work or Series to load Catalogue targets.</p>' +
      '<div class="docsViewerCatalogueTargetPicker__results docsViewerCatalogueTokenModal__results" id="' + RESULTS_ID + '" role="listbox" aria-label="Work and Series targets" data-project-subject-results tabindex="0"></div>' +
      '<div class="docsViewerCatalogueTokenModal__selected" data-project-subject-selected hidden></div>' +
    "</section>";
}

function targetSummary(target) {
  return [target.targetType, target.targetId, target.title].concat(target.meta || []).filter(Boolean).join(" · ");
}

function openSubjectModal(options, target, loaded) {
  var state = {
    disposed: false,
    list: null,
    selectedTarget: null,
    support: null,
    supportPromise: null
  };
  var modalPromise = openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Assign subject",
    size: "document",
    bodyHtml: modalBody(target, loaded.subject),
    focusSelector: 'input[name="docs-project-subject"]:checked, input[name="docs-project-subject"]',
    actions: [
      { role: "modal-primary", label: "Save subject" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var folderField = api.host.querySelector("[data-project-subject-folder]");
      var folderInput = api.host.querySelector("[data-project-subject-folder-input]");
      var catalogue = api.host.querySelector("[data-project-subject-catalogue]");
      var searchInput = api.host.querySelector("#" + SEARCH_INPUT_ID);
      var results = api.host.querySelector("[data-project-subject-results]");
      var searchStatus = api.host.querySelector("[data-project-subject-search-status]");
      var selectedHost = api.host.querySelector("[data-project-subject-selected]");

      function chosenKind() {
        var chosen = api.host.querySelector('input[name="docs-project-subject"]:checked');
        return chosen ? chosen.value : "";
      }

      function renderSelected(targetRecord) {
        state.selectedTarget = targetRecord || null;
        if (!selectedHost) return;
        selectedHost.textContent = targetRecord ? targetSummary(targetRecord) : "";
        selectedHost.hidden = !targetRecord;
      }

      function supportFor(kind) {
        return {
          registry: state.support.registry,
          targetTypes: new Set([kind]),
          searchableTargets: state.support.searchableTargets.filter(function (record) {
            return record.targetType === kind;
          })
        };
      }

      function updateMatches() {
        var kind = chosenKind();
        if (!state.list || !state.support || !searchInput || !["work", "series"].includes(kind)) return;
        renderSelected(null);
        var matches = collectCatalogueTargetMatches(supportFor(kind), searchInput.value, 20);
        state.list.setTargets(matches);
        if (searchStatus) {
          searchStatus.classList.remove("is-error");
          searchStatus.textContent = searchInput.value.trim() && !matches.length
            ? "No matching " + (kind === "work" ? "Work" : "Series") + " targets."
            : "";
          searchStatus.hidden = !searchStatus.textContent;
        }
      }

      function restoreCurrentTarget() {
        var subject = loaded.subject;
        if (
          subject.state !== "valid"
          || !["work", "series"].includes(subject.kind)
          || chosenKind() !== subject.kind
        ) {
          updateMatches();
          return;
        }
        var found = findCatalogueTargetByIdentity(state.support, {
          family: "catalogue",
          targetType: subject.kind,
          targetId: subject.key
        });
        if (searchInput) searchInput.value = subject.kind + ":" + subject.key;
        state.list.setTargets(found ? [found] : []);
        renderSelected(null);
        if (found) {
          state.list.selectTarget(found);
          if (searchStatus) searchStatus.hidden = true;
        } else if (searchStatus) {
          searchStatus.textContent = "Current " + (subject.kind === "work" ? "Work" : "Series") + " " + subject.key + " is unavailable. Choose a current target or another subject.";
          searchStatus.hidden = false;
        }
      }

      function loadSupport() {
        if (state.supportPromise) return state.supportPromise;
        if (searchStatus) {
          searchStatus.textContent = "Loading Catalogue…";
          searchStatus.hidden = false;
        }
        state.supportPromise = loadCatalogueTargetSupport({
          fetch: options.fetch,
          allowedTargetTypes: ["work", "series"]
        }).then(function (support) {
          if (state.disposed) return support;
          state.support = support;
          if (searchInput) searchInput.disabled = false;
          restoreCurrentTarget();
          return support;
        }).catch(function (error) {
          if (!state.disposed && searchStatus) {
            searchStatus.textContent = error && error.message ? error.message : "Catalogue targets are unavailable.";
            searchStatus.hidden = false;
            searchStatus.classList.add("is-error");
          }
          return null;
        });
        return state.supportPromise;
      }

      function projectChoice() {
        var kind = chosenKind();
        var form = folderField && folderField.closest("form");
        var busy = Boolean(form && form.dataset.busy === "true");
        var folderSelected = kind === "folder";
        var catalogueSelected = ["work", "series"].includes(kind);
        if (folderField) folderField.hidden = !folderSelected;
        if (folderInput) folderInput.disabled = busy || !folderSelected;
        if (catalogue) catalogue.hidden = !catalogueSelected;
        if (catalogueSelected) {
          if (state.support) updateMatches();
          else loadSupport();
        } else {
          renderSelected(null);
        }
      }

      state.list = createCatalogueTargetPickerList(results, {
        onActiveChange: function (_target, optionId) {
          [searchInput, results].filter(Boolean).forEach(function (owner) {
            if (optionId) owner.setAttribute("aria-activedescendant", optionId);
            else owner.removeAttribute("aria-activedescendant");
          });
        },
        kind: function (record) { return record.targetType; },
        id: function (record) { return record.targetId; },
        title: function (record) { return record.title; },
        meta: function (record) { return record.meta; },
        onSelect: renderSelected
      });
      api.host.querySelectorAll('input[name="docs-project-subject"]').forEach(function (radioNode) {
        radioNode.addEventListener("change", projectChoice);
      });
      api.host.addEventListener("docs-viewer-modal-busy-change", projectChoice);
      if (searchInput) {
        searchInput.addEventListener("input", updateMatches);
        searchInput.addEventListener("keydown", function (event) {
          if (state.list) state.list.handleKeydown(event);
        });
      }
      if (results) {
        results.addEventListener("keydown", function (event) {
          if (state.list) state.list.handleKeydown(event);
        });
      }
      projectChoice();
    },
    onSubmit: function (api) {
      var selected = api.host.querySelector('input[name="docs-project-subject"]:checked');
      var folderInput = api.host.querySelector("[data-project-subject-folder-input]");
      if (!selected) {
        api.setStatus("Choose None, Folder, Work, or Series.");
        return false;
      }
      var fields = { folder_path: "", work_id: "", series_id: "" };
      if (selected.value === "folder") {
        fields.folder_path = folderInput ? folderInput.value : "";
        if (!cleanString(fields.folder_path)) {
          api.setStatus("Paste a folder path or file URL.");
          if (folderInput) folderInput.focus();
          return false;
        }
      }
      if (["work", "series"].includes(selected.value)) {
        if (!state.selectedTarget || state.selectedTarget.targetType !== selected.value) {
          api.setStatus("Choose a current " + (selected.value === "work" ? "Work" : "Series") + " target.");
          return false;
        }
        fields[selected.value + "_id"] = state.selectedTarget.targetId;
      }
      return options.assignFieldGroup(target, {
        source_revision: loaded.sourceRevision,
        field_group: AUTHORING_SUBJECT_GROUP_ID,
        fields: fields,
        confirm: true
      }).then(function (response) {
        return { confirmed: true, payload: assignedSubject(response, target) };
      });
    }
  });
  return modalPromise.then(function (result) {
    state.disposed = true;
    if (state.list) state.list.destroy();
    return result;
  });
}

export function openDocsViewerProjectSubjectModal(options = {}) {
  var target = normalizeManagedDocumentTarget(options.target);
  if (!target.sub_scope) {
    return Promise.reject(new Error("Projects subject assignment requires a sub-scope document target."));
  }
  if (typeof options.readMetadata !== "function" || typeof options.assignFieldGroup !== "function") {
    return Promise.reject(new Error("Projects subject assignment service is unavailable."));
  }
  return Promise.resolve(options.readMetadata(target)).then(function (response) {
    return openSubjectModal(options, target, loadedSubject(response, target));
  });
}
