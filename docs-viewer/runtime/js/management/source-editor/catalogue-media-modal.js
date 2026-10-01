import { escapeHtml, openDocsViewerManagementModal } from "../docs-viewer-management-modal-shell.js";
import { selectedTextForCatalogueTitle } from "./catalogue-token-contract.js";
import {
  catalogueDocumentSubjectTarget, catalogueMediaLinkLabel, loadCatalogueMediaSupport,
  readCatalogueTokenPresentation
} from "./catalogue-media-support.js";
import { collectSemanticTokenTargetMatches } from "./semantic-token-targets.js";
import { serializeCatalogueImageToken, serializeCatalogueMediaToken } from "./catalogue-token-parser.js";
import { captureCatalogueTokenAction } from "./catalogue-token-contribution.js";
import { createCatalogueTargetPickerList } from "./catalogue-target-picker.js";
import {
  bindCatalogueImageDerivedTitle, catalogueImagePresentationHtml,
  hydrateCatalogueImagePresentation, readCatalogueImagePresentation
} from "./catalogue-image-presentation.js";

var SEARCH_INPUT_ID = "docsViewerCatalogueImageSearch";
var RESULTS_ID = "docsViewerCatalogueImageResults";
var LINK_INPUT_ID = "docsViewerCatalogueLinkText";
var SUBJECT_INPUT_ID = "docsViewerCatalogueUseDocumentSubject";

function modalBody(searchQuery, linkText, imageMode) {
  return (
    '<div class="docsViewerCatalogueTokenModal docsViewerCatalogueImageModal">' +
      '<label class="docsViewer__field docsViewer__field--checkbox" for="' + SUBJECT_INPUT_ID + '">' +
        '<input class="docsViewer__checkboxInput" id="' + SUBJECT_INPUT_ID + '" type="checkbox" disabled>' +
        '<span class="docsViewer__fieldLabel">Use document subject</span>' +
      '</label>' +
      '<label class="docsViewer__field" for="' + SEARCH_INPUT_ID + '">' +
        '<span class="docsViewer__fieldLabel">Search Catalogue</span>' +
        '<input class="docsViewer__fieldInput" id="' + SEARCH_INPUT_ID + '" type="search" role="combobox" aria-autocomplete="list" aria-controls="' + RESULTS_ID + '" aria-expanded="false" autocomplete="off" spellcheck="false" value="' + escapeHtml(searchQuery) + '" disabled>' +
      "</label>" +
      '<p class="muted small" data-role="document-subject-status" hidden></p>' +
      '<p class="docsViewerCatalogueTokenModal__searchStatus muted small" data-role="catalogue-search-status">Loading Catalogue…</p>' +
      '<div class="docsViewerCatalogueTargetPicker__results docsViewerCatalogueTokenModal__results" id="' + RESULTS_ID + '" role="listbox" aria-label="' + (imageMode ? "Catalogue Works" : "Catalogue Works and Galleries") + '" data-role="catalogue-results" tabindex="0" hidden></div>' +
      (imageMode ? catalogueImagePresentationHtml({ idPrefix: "docsViewerCatalogueImage" }) :
        '<label class="docsViewer__field" for="' + LINK_INPUT_ID + '">' +
          '<span class="docsViewer__fieldLabel">Link text</span>' +
          '<input class="docsViewer__fieldInput" id="' + LINK_INPUT_ID + '" type="text" autocomplete="off" value="' + escapeHtml(linkText) + '" required>' +
        "</label>") +
    "</div>"
  );
}

/** Share Catalogue selection while keeping image presentation and text-link authoring distinct. */
export function openCatalogueMediaModal(options = {}) {
  var imageMode = options.presentation === "image";
  var adapter = options.adapter;
  var action = captureCatalogueTokenAction(adapter, options.capture, imageMode ? "image" : "media");
  var capture = action.capture;
  var initialToken = action.token;
  var subjectTarget = null;
  var selectionText = initialToken ? initialToken.title : selectedTextForCatalogueTitle(capture && capture.text);
  var state = { disposed: false, request: 0, list: null, support: null, target: null,
    linkDefault: "", showDerivedTitle: null, replaceDefaults: null,
    useDocumentSubject: false };
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: adapter && typeof adapter.focus === "function" ? { focus: function () { adapter.focus(); } } : null,
    title: initialToken ? (imageMode ? "Edit Catalogue image" : "Edit Media View link")
      : imageMode ? "Add Catalogue image" : "Add Media View link",
    size: "document",
    bodyHtml: modalBody(initialToken ? initialToken.targetType + ":" + initialToken.targetId : selectionText, selectionText, imageMode),
    focusSelector: "#" + SEARCH_INPUT_ID,
    actions: [
      { role: "modal-primary", label: initialToken ? "Apply" : imageMode ? "Add image" : "Add link", disabled: true },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var modalRoot = api.host.querySelector('[data-role="docs-viewer-management-modal"]');
      var search = api.host.querySelector("#" + SEARCH_INPUT_ID);
      var linkInput = api.host.querySelector("#" + LINK_INPUT_ID);
      var results = api.host.querySelector('[data-role="catalogue-results"]');
      var status = api.host.querySelector('[data-role="catalogue-search-status"]');
      var primary = api.host.querySelector('[data-role="modal-primary"]');
      var subjectCheckbox = api.host.querySelector("#" + SUBJECT_INPUT_ID);
      subjectCheckbox.checked = state.useDocumentSubject;
      if (modalRoot) modalRoot.id = imageMode ? "catalogue-image-add-modal" : "catalogue-media-link-modal";
      if (imageMode) {
        hydrateCatalogueImagePresentation(api.host, initialToken || {
          useWorkTitleCaption: true, includeWorkMetadata: true, placement: "full", fillWidth: true
        });
        state.showDerivedTitle = bindCatalogueImageDerivedTitle(api.host);
      }

      function showResults(visible) {
        results.hidden = !visible;
        search.setAttribute("aria-expanded", visible ? "true" : "false");
      }
      function message(text, error = false) {
        status.textContent = text;
        status.hidden = !text;
        status.classList.toggle("is-error", error);
      }
      state.replaceDefaults = function (title) {
        if (imageMode) {
          state.showDerivedTitle(title);
          return;
        }
        if (initialToken) return;
        linkInput.value = catalogueMediaLinkLabel(
          { title: title }, linkInput.value, { title: state.linkDefault }, Boolean(selectionText)
        );
        state.linkDefault = title;
      };
      async function selectTarget(target) {
        var request = ++state.request;
        state.target = target;
        primary.disabled = true;
        if (imageMode) state.showDerivedTitle("");
        search.value = target.title;
        state.list.setTargets([]);
        showResults(false);
        message(target.targetType === "gallery" ? "Loading Gallery…" : "Loading Work image…");
        try {
          var presentation = await readCatalogueTokenPresentation(adapter, target);
          if (state.disposed || request !== state.request) return;
          state.replaceDefaults(presentation.label);
          primary.disabled = false;
          message("");
        } catch (error) {
          if (!state.disposed && request === state.request) message(error.message || "Catalogue media is unavailable.", true);
        }
      }
      function updateMatches() {
        if (!state.support) return;
        state.request += 1;
        state.target = null;
        primary.disabled = true;
        if (imageMode) state.showDerivedTitle("");
        var targets = imageMode ? state.support.targets.filter(function (target) { return target.targetType === "work"; }) : state.support.targets;
        var matches = collectSemanticTokenTargetMatches(targets, search.value, state.support.registry, 20);
        state.list.setTargets(matches);
        showResults(true);
        message(search.value.trim() && !matches.length ? (imageMode ? "No matching Catalogue Works." : "No matching Catalogue Works or Galleries.") : "");
      }
      function selectSubject() {
        var target = state.support.targets.find(function (item) {
          return item.targetType === subjectTarget.targetType && item.targetId === subjectTarget.targetId;
        });
        if (target) return selectTarget(target);
        state.request += 1;
        state.target = null;
        primary.disabled = true;
        if (imageMode) state.showDerivedTitle("");
        message("The selected Catalogue target is unavailable.", true);
      }
      state.list = createCatalogueTargetPickerList(results, {
        onActiveChange: function (_target, optionId) {
          [search, results].forEach(function (owner) {
            if (optionId) owner.setAttribute("aria-activedescendant", optionId);
            else owner.removeAttribute("aria-activedescendant");
          });
        },
        kind: function (target) { return target.targetType; },
        id: function (target) { return target.targetId; },
        title: function (target) { return target.title; },
        meta: function (target) { return target.meta; },
        onSelect: function (target) { selectTarget(target); }
      });
      search.addEventListener("input", updateMatches);
      [search, results].forEach(function (owner) {
        owner.addEventListener("keydown", function (event) { state.list.handleKeydown(event); });
      });
      subjectCheckbox.addEventListener("change", function () {
        state.useDocumentSubject = subjectCheckbox.checked;
        search.disabled = state.useDocumentSubject;
        if (state.useDocumentSubject) {
          selectSubject();
        } else {
          search.focus();
        }
      });
      loadCatalogueMediaSupport(adapter, { fetch: options.fetch }).then(function (support) {
        if (state.disposed) return;
        state.support = support;
        subjectCheckbox.disabled = !subjectTarget;
        search.disabled = false;
        updateMatches();
        if (initialToken) {
          var target = support.targets.find(function (item) {
            return item.targetType === initialToken.targetType && item.targetId === initialToken.targetId;
          });
          if (target) selectTarget(target);
          else message("The selected Catalogue target is unavailable.", true);
        }
        search.focus();
      }).catch(function (error) {
        if (!state.disposed) message(error.message || "Catalogue images are unavailable.", true);
      });
      adapter.readDocumentSubject(action.snapshot).then(function (subject) {
        if (state.disposed) return;
        subjectTarget = catalogueDocumentSubjectTarget(subject);
        subjectCheckbox.disabled = !subjectTarget || !state.support;
      }).catch(function (error) {
        if (state.disposed) return;
        var note = api.host.querySelector('[data-role="document-subject-status"]');
        note.textContent = "Document subject unavailable: " + error.message;
        note.hidden = false;
      });
    },
    onSubmit: async function (api) {
      if (!adapter.isCurrent()) { api.setStatus("The Source editor was replaced. Cancel and try again."); return false; }
      if (!state.target) { api.setStatus("Choose a Catalogue target."); return false; }
      // Revalidate current media before writing source.
      var current = await readCatalogueTokenPresentation(adapter, state.target);
      state.replaceDefaults(current.label);
      var fields = { registry: state.support.registry, targetType: state.target.targetType, targetId: state.target.targetId };
      if (imageMode) {
        Object.assign(fields, readCatalogueImagePresentation(api.host));
      } else {
        fields.title = String(api.host.querySelector("#" + LINK_INPUT_ID).value || "").trim();
        if (!fields.title) { api.setStatus("Enter link text."); return false; }
      }
      var token = imageMode ? serializeCatalogueImageToken(fields) : serializeCatalogueMediaToken(fields);
      if (!token) { api.setStatus("The selected image and presentation cannot be serialized."); return false; }
      if (!adapter.replaceCapturedSelection(capture, token)) {
        api.setStatus("Markdown source changed while this modal was open. Cancel and try again.");
        return false;
      }
      return { confirmed: true, target: state.target, token: token };
    }
  }).then(function (result) {
    state.disposed = true;
    state.request += 1;
    if (state.list) state.list.destroy();
    if (adapter && typeof adapter.focus === "function") adapter.focus();
    return result;
  });
}
