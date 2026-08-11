import {
  escapeHtml,
  openDocsViewerManagementModal
} from "../docs-viewer-management-modal-shell.js";
import {
  buildCatalogueToken,
  selectedTextForCatalogueTitle
} from "./catalogue-token-contract.js";
import {
  collectCatalogueTargetMatches,
  findCatalogueTargetByIdentity,
  loadCatalogueTargetSupport
} from "./catalogue-token-targets.js";
import {
  parseCatalogueToken
} from "./catalogue-token-parser.js";
import {
  createCatalogueTargetPickerList
} from "./catalogue-target-picker.js";

var SEARCH_INPUT_ID = "docsViewerCatalogueTokenSearch";
var RESULTS_ID = "docsViewerCatalogueTokenResults";
var TITLE_INPUT_ID = "docsViewerCatalogueTokenTitle";

export const CATALOGUE_TOKEN_MODAL_ID = "catalogue-token-add-modal";

function modalBody(settings, searchQuery, selectionTitle) {
  return (
    '<div class="docsViewerCatalogueTokenModal">' +
      '<label class="docsViewer__field" for="' + settings.searchInputId + '">' +
        '<span class="docsViewer__fieldLabel">' + escapeHtml(settings.searchLabel) + '</span>' +
        '<input class="docsViewer__fieldInput" id="' + settings.searchInputId + '" type="search" role="combobox" aria-autocomplete="list" aria-controls="' + settings.resultsId + '" aria-expanded="true" autocomplete="off" spellcheck="false" value="' + escapeHtml(searchQuery) + '" disabled>' +
      "</label>" +
      '<p class="docsViewerCatalogueTokenModal__searchStatus muted small" data-role="catalogue-search-status">' + escapeHtml(settings.loadingMessage) + '</p>' +
      '<div class="docsViewerCatalogueTargetPicker__results docsViewerCatalogueTokenModal__results" id="' + settings.resultsId + '" role="listbox" aria-label="' + escapeHtml(settings.resultsLabel) + '" data-role="catalogue-results" tabindex="0"></div>' +
      '<div class="docsViewerCatalogueTokenModal__selected" data-role="catalogue-selected" hidden></div>' +
      '<label class="docsViewer__field" for="' + settings.titleInputId + '">' +
        '<span class="docsViewer__fieldLabel">Title</span>' +
        '<input class="docsViewer__fieldInput" id="' + settings.titleInputId + '" type="text" autocomplete="off" value="' + escapeHtml(selectionTitle) + '" required>' +
      "</label>" +
    "</div>"
  );
}

function targetSummary(target, settings) {
  var parts = [target.targetType, target.targetId, target.title]
    .concat(settings.targetMeta(target));
  return parts.filter(Boolean).join(" · ");
}

export function openSemanticTextTokenModal(settings, options = {}) {
  var adapter = options.adapter || null;
  var capture = options.capture || null;
  var selectedToken = settings.parseToken(capture && capture.text);
  var selectionTitle = selectedToken
    ? selectedToken.title
    : settings.selectedText(capture && capture.text);
  var searchQuery = selectedToken
    ? selectedToken.targetType + ":" + selectedToken.targetId
    : selectionTitle;
  var state = {
    disposed: false,
    initialToken: selectedToken,
    list: null,
    selectedTarget: null,
    support: null
  };

  var modalPromise = openDocsViewerManagementModal({
    root: options.root,
    title: settings.modalTitle,
    size: "document",
    bodyHtml: modalBody(settings, searchQuery, selectionTitle),
    focusSelector: "#" + settings.searchInputId,
    actions: [
      { role: "modal-primary", label: "Add", disabled: true },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var modalRoot = api.host.querySelector('[data-role="docs-viewer-management-modal"]');
      var searchInput = api.host.querySelector("#" + settings.searchInputId);
      var titleInput = api.host.querySelector("#" + settings.titleInputId);
      var results = api.host.querySelector('[data-role="catalogue-results"]');
      var searchStatus = api.host.querySelector('[data-role="catalogue-search-status"]');
      var selected = api.host.querySelector('[data-role="catalogue-selected"]');
      var primary = api.host.querySelector('[data-role="modal-primary"]');
      if (modalRoot) modalRoot.id = settings.modalId;

      function renderSelectedTarget(target) {
        state.selectedTarget = target || null;
        if (!selected) return;
        selected.textContent = target ? targetSummary(target, settings) : "";
        selected.hidden = !target;
      }

      function updateMatches() {
        if (!state.list || !state.support || !searchInput) return;
        renderSelectedTarget(null);
        var matches = settings.collectMatches(state.support, searchInput.value, 20);
        state.list.setTargets(matches);
        if (searchStatus) {
          searchStatus.textContent = searchInput.value.trim() && !matches.length
            ? settings.noMatchesMessage
            : "";
          searchStatus.hidden = !searchStatus.textContent;
        }
      }

      function restoreInitialToken() {
        var target = settings.findByIdentity(state.support, state.initialToken);
        state.list.setTargets(target ? [target] : []);
        renderSelectedTarget(null);
        if (!target) {
          if (searchStatus) {
            searchStatus.textContent = (
              settings.familyLabel + " target "
              + state.initialToken.targetType
              + ":"
              + state.initialToken.targetId
              + " is unavailable."
            );
            searchStatus.hidden = false;
          }
          return;
        }
        state.list.selectTarget(target);
        if (titleInput) titleInput.value = state.initialToken.title;
        if (searchStatus) {
          searchStatus.textContent = "";
          searchStatus.hidden = true;
        }
      }

      state.list = createCatalogueTargetPickerList(results, {
        onActiveChange: function (_target, optionId) {
          [searchInput, results].filter(Boolean).forEach(function (owner) {
            if (optionId) owner.setAttribute("aria-activedescendant", optionId);
            else owner.removeAttribute("aria-activedescendant");
          });
        },
        kind: function (target) { return target.targetType; },
        id: function (target) { return target.targetId; },
        title: function (target) { return target.title; },
        meta: function (target) { return settings.targetMeta(target); },
        onSelect: function (target) {
          renderSelectedTarget(target);
          if (titleInput) {
            titleInput.value = settings.titleOnSelect(target, titleInput.value);
          }
        }
      });
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
      settings.loadSupport({ fetch: options.fetch })
        .then(function (support) {
          if (state.disposed) return;
          state.support = support;
          if (searchInput) searchInput.disabled = false;
          if (primary) primary.disabled = false;
          if (state.initialToken) restoreInitialToken();
          else updateMatches();
          if (searchInput) searchInput.focus();
        })
        .catch(function (error) {
          if (state.disposed) return;
          if (searchStatus) {
            searchStatus.textContent = error && error.message
              ? error.message
              : settings.unavailableMessage;
            searchStatus.hidden = false;
            searchStatus.classList.add("is-error");
          }
        });
    },
    onSubmit: function (api) {
      var titleInput = api.host.querySelector("#" + settings.titleInputId);
      var title = String(titleInput && titleInput.value || "").trim();
      if (!state.selectedTarget) {
        api.setStatus("Choose a current " + settings.familyLabel + " target.");
        return false;
      }
      if (!title) {
        api.setStatus("Enter a Title.");
        if (titleInput) titleInput.focus();
        return false;
      }
      var token = settings.buildToken({
        targetType: state.selectedTarget.targetType,
        targetId: state.selectedTarget.targetId,
        title: title
      });
      if (!token) {
        api.setStatus("The selected target and Title cannot be serialized.");
        return false;
      }
      if (
        !adapter
        || typeof adapter.replaceCapturedSelection !== "function"
        || !adapter.replaceCapturedSelection(capture, token)
      ) {
        api.setStatus("Markdown source changed while this modal was open. Cancel and try again.");
        return false;
      }
      return {
        confirmed: true,
        target: state.selectedTarget,
        title: title,
        token: token
      };
    }
  });

  return modalPromise.then(function (result) {
    state.disposed = true;
    if (state.list) state.list.destroy();
    if (adapter && typeof adapter.focus === "function") adapter.focus();
    return result;
  });
}

var CATALOGUE_TOKEN_MODAL_SETTINGS = {
  buildToken: buildCatalogueToken,
  collectMatches: collectCatalogueTargetMatches,
  familyLabel: "Catalogue",
  findByIdentity: findCatalogueTargetByIdentity,
  loadingMessage: "Loading Catalogue…",
  loadSupport: loadCatalogueTargetSupport,
  modalId: CATALOGUE_TOKEN_MODAL_ID,
  modalTitle: "Add catalogue token",
  noMatchesMessage: "No matching Catalogue targets.",
  parseToken: parseCatalogueToken,
  resultsId: RESULTS_ID,
  resultsLabel: "Catalogue targets",
  searchInputId: SEARCH_INPUT_ID,
  searchLabel: "Search Catalogue",
  selectedText: selectedTextForCatalogueTitle,
  targetMeta: function (target) { return target.meta; },
  titleOnSelect: function (target) { return target.title; },
  titleInputId: TITLE_INPUT_ID,
  unavailableMessage: "Catalogue targets are unavailable."
};

export function openCatalogueTokenModal(options = {}) {
  return openSemanticTextTokenModal(CATALOGUE_TOKEN_MODAL_SETTINGS, options);
}
