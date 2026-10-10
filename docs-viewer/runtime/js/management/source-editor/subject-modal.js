import { mountSearchField } from "/shared/frontend/js/search-field.js";
import {
  escapeHtml,
  openDocsViewerManagementModal
} from "../docs-viewer-management-modal-shell.js";
import {
  AUTHORING_SUBJECT_FIELDS,
  classifyDocsDocumentSubject
} from "../../shared/docs-document-subject.js";
import {
  collectCatalogueTargetMatches,
  findCatalogueTargetByIdentity,
  loadCatalogueTargetSupport
} from "./catalogue-token-targets.js";
import {
  createCatalogueTargetPickerList
} from "./catalogue-target-picker.js";

const SEARCH_INPUT_ID = "docsViewerProjectSubjectCatalogueSearch";
const RESULTS_ID = "docsViewerProjectSubjectCatalogueResults";

function radio(value, label, selected) {
  return '<label class="docsViewer__field docsViewer__field--checkbox">' +
    '<input class="docsViewer__checkboxInput" type="radio" name="docs-project-subject" value="' + value + '"' +
      (selected === value ? " checked" : "") + ">" +
    '<span class="docsViewer__fieldLabel">' + label + "</span>" +
  "</label>";
}

function modalBody(subject, folderSupported) {
  var selected = subject.kind;
  var folderValue = subject.kind === "folder" ? subject.key : "";
  return "" +
    '<fieldset class="docsViewer__fieldGroup" data-project-subject-options>' +
      '<legend class="visually-hidden">Subject</legend>' +
      radio("none", "None", subject.kind) +
      (folderSupported ? radio("folder", "Folder", subject.kind) : "") +
      radio("work", "Work", subject.kind) +
    "</fieldset>" +
    '<label class="docsViewer__field" data-project-subject-folder' +
      (selected === "folder" ? "" : " hidden") + ">" +
      '<span class="docsViewer__fieldLabel">Folder path or file URL</span>' +
      '<input class="docsViewer__fieldInput" data-project-subject-folder-input type="text" ' +
        'autocomplete="off" spellcheck="false" value="' + escapeHtml(folderValue) + '">' +
    "</label>" +
    '<section class="docsViewerProjectSubjectModal__catalogue" data-project-subject-catalogue' +
      (selected === "work" ? "" : " hidden") + ">" +
      '<div class="docsViewer__field">' +
        '<label class="docsViewer__fieldLabel" for="' + SEARCH_INPUT_ID + '">Search Catalogue</label>' +
        '<input class="docsViewer__fieldInput" id="' + SEARCH_INPUT_ID + '" type="search" role="combobox" aria-autocomplete="list" aria-controls="' + RESULTS_ID + '" aria-expanded="false" autocomplete="off" spellcheck="false" disabled>' +
      "</div>" +
      '<p class="docsViewerCatalogueTokenModal__searchStatus muted small" data-project-subject-search-status hidden></p>' +
      '<div class="docsViewerCatalogueTargetPicker__results docsViewerCatalogueTokenModal__results" id="' + RESULTS_ID + '" role="listbox" aria-label="Work targets" data-project-subject-results tabindex="0" hidden></div>' +
    "</section>";
}

function openSubjectModal(options, snapshot, loaded) {
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
    title: "Assign Subject",
    size: "document",
    bodyHtml: modalBody(loaded.subject, loaded.folderSupported),
    focusSelector: 'input[name="docs-project-subject"]:checked',
    actions: [
      { role: "modal-primary", label: "Apply" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var folderField = api.host.querySelector("[data-project-subject-folder]");
      var folderInput = api.host.querySelector("[data-project-subject-folder-input]");
      var catalogue = api.host.querySelector("[data-project-subject-catalogue]");
      var searchInput = api.host.querySelector("#" + SEARCH_INPUT_ID);
      mountSearchField(searchInput);
      var results = api.host.querySelector("[data-project-subject-results]");
      var searchStatus = api.host.querySelector("[data-project-subject-search-status]");
      function chosenKind() {
        var chosen = api.host.querySelector('input[name="docs-project-subject"]:checked');
        return chosen ? chosen.value : "";
      }

      function showResults(visible) {
        if (results) results.hidden = !visible;
        if (searchInput) searchInput.setAttribute("aria-expanded", visible ? "true" : "false");
      }

      function clearSearchStatus() {
        if (!searchStatus) return;
        searchStatus.classList.remove("is-error");
        searchStatus.textContent = "";
        searchStatus.hidden = true;
      }

      function selectCatalogueTarget(targetRecord, focusInput) {
        state.selectedTarget = targetRecord || null;
        if (!targetRecord) return;
        if (searchInput) searchInput.value = targetRecord.title;
        if (state.list) state.list.setTargets([]);
        showResults(false);
        clearSearchStatus();
        if (focusInput && searchInput) searchInput.focus();
      }

      function updateMatches() {
        if (!state.list || !state.support || !searchInput || chosenKind() !== "work") return;
        state.selectedTarget = null;
        var matches = collectCatalogueTargetMatches(state.support, searchInput.value, 20);
        state.list.setTargets(matches);
        showResults(true);
        if (searchStatus) {
          searchStatus.classList.remove("is-error");
          searchStatus.textContent = searchInput.value.trim() && !matches.length
            ? "No matching Work targets."
            : "";
          searchStatus.hidden = !searchStatus.textContent;
        }
      }

      function restoreCurrentTarget() {
        var subject = loaded.subject;
        if (
          subject.kind !== "work"
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
        if (found) {
          selectCatalogueTarget(found, false);
        } else if (searchStatus) {
          if (searchInput) searchInput.value = subject.kind + ":" + subject.key;
          state.list.setTargets([]);
          state.selectedTarget = null;
          showResults(false);
          searchStatus.textContent = "Current Work " + subject.key + " is unavailable. Choose a current target or another subject.";
          searchStatus.hidden = false;
        }
      }

      function loadSupport() {
        if (state.supportPromise) return state.supportPromise;
        clearSearchStatus();
        state.supportPromise = loadCatalogueTargetSupport(options.catalogueProvider, {
          fetch: options.fetch,
          allowedTargetTypes: ["work"]
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
        var form = api.host.querySelector("form");
        var busy = Boolean(form && form.dataset.busy === "true");
        var folderSelected = kind === "folder";
        var catalogueSelected = kind === "work";
        if (folderField) folderField.hidden = !folderSelected;
        if (folderInput) folderInput.disabled = busy || !folderSelected;
        if (catalogue) catalogue.hidden = !catalogueSelected;
        if (searchInput) searchInput.disabled = busy || !catalogueSelected || !state.support;
        if (catalogueSelected) {
          if (state.support) {
            if (!state.selectedTarget || state.selectedTarget.targetType !== kind) updateMatches();
          } else {
            loadSupport();
          }
        } else {
          state.selectedTarget = null;
          showResults(false);
        }
      }

      state.list = createCatalogueTargetPickerList(results, {
        layout: "id-title",
        onActiveChange: function (_target, optionId) {
          [searchInput, results].filter(Boolean).forEach(function (owner) {
            if (optionId) owner.setAttribute("aria-activedescendant", optionId);
            else owner.removeAttribute("aria-activedescendant");
          });
        },
        kind: function (record) { return record.targetType; },
        id: function (record) { return record.targetId; },
        title: function (record) { return record.title; },
        onSelect: function (record) { selectCatalogueTarget(record, true); }
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
      if (!selected) {
        api.setStatus("Choose a subject or None.");
        return false;
      }
      var fields = Object.fromEntries(AUTHORING_SUBJECT_FIELDS.map(function (field) { return [field, ""]; }));
      if (selected.value === "folder") {
        var folderInput = api.host.querySelector("[data-project-subject-folder-input]");
        fields.folder_path = folderInput ? folderInput.value : "";
        if (!fields.folder_path.trim()) {
          api.setStatus("Paste a folder path or file URL.");
          if (folderInput) folderInput.focus();
          return false;
        }
      }
      if (selected.value === "work") {
        if (!state.selectedTarget || state.selectedTarget.targetType !== selected.value) {
          api.setStatus("Choose a current Work target.");
          return false;
        }
        fields.work_id = state.selectedTarget.targetId;
      }
      return options.adapter.readSubjectAssignment(snapshot, fields).then(function (response) {
        if (typeof response.source_text !== "string") throw new Error("Subject source could not be prepared.");
        if (!options.adapter.applySubjectSource(snapshot, response.source_text)) {
          throw new Error("Markdown source changed while this modal was open. Cancel and try again.");
        }
        return { confirmed: true };
      });
    }
  });
  return modalPromise.then(function (result) {
    state.disposed = true;
    if (state.list) state.list.destroy();
    return result;
  });
}

/** Edit the captured Source buffer's Subject; the editor's Save owns persistence. */
export function openSourceSubjectModal(options = {}) {
  var adapter = options.adapter;
  if (!adapter || !adapter.canAssignSubject()) {
    return Promise.reject(new Error("Subject assignment is unavailable for this document."));
  }
  var snapshot = adapter.getBufferSnapshot();
  return adapter.readSubjectAssignment(snapshot).then(function (response) {
    if (typeof response.folder_subject_supported !== "boolean") {
      throw new Error("Folder subject capability could not be loaded.");
    }
    return openSubjectModal(Object.assign({}, options, {
      catalogueProvider: adapter,
      restoreFocus: function () { adapter.focus(); }
    }), snapshot, {
      subject: classifyDocsDocumentSubject(response, { folderSupported: response.folder_subject_supported }),
      folderSupported: response.folder_subject_supported
    });
  });
}

