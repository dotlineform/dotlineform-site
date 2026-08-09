import {
  escapeHtml,
  openDocsViewerManagementModal
} from "../docs-viewer-management-modal-shell.js";
import {
  selectedTextForCatalogueTitle
} from "./catalogue-token-contract.js";
import {
  collectCatalogueTargetMatches,
  loadCatalogueTargetSupport
} from "./catalogue-token-targets.js";
import {
  normalizeCatalogueDetailId,
  serializeCatalogueImageToken
} from "./catalogue-token-parser.js";
import {
  createCatalogueTargetPickerList
} from "./catalogue-target-picker.js";
import {
  loadCatalogueWorkDetailTitle
} from "./catalogue-work-detail-title.js";
import {
  bindImagePresentation,
  hydrateImagePresentation,
  imagePresentationHtml,
  readImagePresentation
} from "./source-editor-image-presentation.js";

var SEARCH_INPUT_ID = "docsViewerCatalogueImageSearch";
var RESULTS_ID = "docsViewerCatalogueImageResults";
var ALT_INPUT_ID = "docsViewerCatalogueImageAlt";
var DETAIL_INPUT_ID = "docsViewerCatalogueImageDetailId";

export const CATALOGUE_IMAGE_MODAL_ID = "catalogue-image-add-modal";

function modalBody(searchQuery, alt) {
  return (
    '<div class="docsViewerCatalogueTokenModal docsViewerCatalogueImageModal">' +
      '<label class="docsViewer__field" for="' + SEARCH_INPUT_ID + '">' +
        '<span class="docsViewer__fieldLabel">Search Catalogue</span>' +
        '<input class="docsViewer__fieldInput" id="' + SEARCH_INPUT_ID + '" type="search" role="combobox" aria-autocomplete="list" aria-controls="' + RESULTS_ID + '" aria-expanded="false" autocomplete="off" spellcheck="false" value="' + escapeHtml(searchQuery) + '" disabled>' +
      "</label>" +
      '<p class="docsViewerCatalogueTokenModal__searchStatus muted small" data-role="catalogue-search-status">Loading Catalogue…</p>' +
      '<div class="docsViewerCatalogueTargetPicker__results docsViewerCatalogueTokenModal__results" id="' + RESULTS_ID + '" role="listbox" aria-label="Catalogue image targets" data-role="catalogue-results" tabindex="0" hidden></div>' +
      '<label class="docsViewer__field" for="' + DETAIL_INPUT_ID + '">' +
        '<span class="docsViewer__fieldLabel">Work Detail ID</span>' +
        '<input class="docsViewer__fieldInput" id="' + DETAIL_INPUT_ID + '" type="text" inputmode="numeric" pattern="[0-9]*" autocomplete="off" disabled>' +
      "</label>" +
      '<label class="docsViewer__field" for="' + ALT_INPUT_ID + '">' +
        '<span class="docsViewer__fieldLabel">Alt text</span>' +
        '<input class="docsViewer__fieldInput" id="' + ALT_INPUT_ID + '" type="text" autocomplete="off" value="' + escapeHtml(alt) + '" required>' +
      "</label>" +
      imagePresentationHtml({ idPrefix: "docsViewerCatalogueImage" }) +
    "</div>"
  );
}

function sourceEditorFocusTarget(adapter) {
  if (!adapter || typeof adapter.focus !== "function") return null;
  return {
    focus: function () {
      adapter.focus();
    }
  };
}

export function openCatalogueImageModal(options = {}) {
  var adapter = options.adapter || null;
  var capture = options.capture || null;
  var selectionText = selectedTextForCatalogueTitle(capture && capture.text);
  var state = {
    disposed: false,
    captionDefault: selectionText,
    detailCaptionRequest: 0,
    detailTitles: new Map(),
    list: null,
    loadDetailTitle: null,
    selectedTarget: null,
    support: null
  };

  var modalPromise = openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: sourceEditorFocusTarget(adapter),
    title: "Add Catalogue image",
    size: "document",
    bodyHtml: modalBody(selectionText, selectionText),
    focusSelector: "#" + SEARCH_INPUT_ID,
    actions: [
      { role: "modal-primary", label: "Add image", disabled: true },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var modalRoot = api.host.querySelector('[data-role="docs-viewer-management-modal"]');
      var searchInput = api.host.querySelector("#" + SEARCH_INPUT_ID);
      var detailInput = api.host.querySelector("#" + DETAIL_INPUT_ID);
      var altInput = api.host.querySelector("#" + ALT_INPUT_ID);
      var captionInput = api.host.querySelector('[data-role="staged-media-caption-text"]');
      var results = api.host.querySelector('[data-role="catalogue-results"]');
      var searchStatus = api.host.querySelector('[data-role="catalogue-search-status"]');
      var primary = api.host.querySelector('[data-role="modal-primary"]');
      if (modalRoot) modalRoot.id = CATALOGUE_IMAGE_MODAL_ID;
      bindImagePresentation(api.host);
      hydrateImagePresentation(api.host, {
        addCaption: true,
        caption: selectionText,
        placement: "full",
        fillWidth: true
      });

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

      function replaceDefaultCaption(value) {
        var nextDefault = String(value || "").trim();
        var previousDefault = state.captionDefault;
        state.captionDefault = nextDefault;
        if (
          captionInput
          && (!captionInput.value || captionInput.value === previousDefault)
        ) captionInput.value = nextDefault;
      }

      function detailTitle(workId, detailId) {
        var detailUid = workId + "-" + detailId;
        if (!state.detailTitles.has(detailUid)) {
          state.detailTitles.set(detailUid, loadCatalogueWorkDetailTitle(workId, detailId, {
            fetch: options.fetch,
            studioBaseUrl: options.studioBaseUrl
          }));
        }
        return state.detailTitles.get(detailUid);
      }
      state.loadDetailTitle = detailTitle;

      function projectDetailCaption() {
        var target = state.selectedTarget;
        var request = state.detailCaptionRequest + 1;
        state.detailCaptionRequest = request;
        if (!target || target.targetType !== "work" || !detailInput) return;
        var detailId = normalizeCatalogueDetailId(detailInput.value);
        if (detailId === null) return;
        replaceDefaultCaption(target.title);
        if (!detailId) return;
        detailTitle(target.targetId, detailId).then(function (title) {
          if (
            state.disposed
            || request !== state.detailCaptionRequest
            || target !== state.selectedTarget
            || detailId !== normalizeCatalogueDetailId(detailInput.value)
          ) return;
          if (title) replaceDefaultCaption(title);
        });
      }

      function selectCatalogueTarget(target) {
        state.selectedTarget = target || null;
        if (!target) return;
        state.detailCaptionRequest += 1;
        if (detailInput) {
          detailInput.value = "";
          detailInput.disabled = target.targetType !== "work" || target.hasDetails !== true;
        }
        if (searchInput) searchInput.value = target.title;
        if (state.list) state.list.setTargets([]);
        showResults(false);
        clearSearchStatus();
        if (altInput) altInput.value = target.title;
        state.captionDefault = target.title;
        if (captionInput) captionInput.value = state.captionDefault;
        if (searchInput) searchInput.focus();
      }

      function updateMatches() {
        if (!state.list || !state.support || !searchInput) return;
        state.selectedTarget = null;
        state.detailCaptionRequest += 1;
        if (detailInput) {
          detailInput.value = "";
          detailInput.disabled = true;
        }
        var matches = collectCatalogueTargetMatches(state.support, searchInput.value, 20);
        state.list.setTargets(matches);
        showResults(true);
        if (searchStatus) {
          searchStatus.classList.remove("is-error");
          searchStatus.textContent = searchInput.value.trim() && !matches.length
            ? "No matching Catalogue images."
            : "";
          searchStatus.hidden = !searchStatus.textContent;
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
        meta: function (target) { return target.meta; },
        onSelect: function (target) {
          selectCatalogueTarget(target);
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
      if (detailInput) detailInput.addEventListener("input", projectDetailCaption);
      loadCatalogueTargetSupport({ fetch: options.fetch, requireImage: true })
        .then(function (support) {
          if (state.disposed) return;
          state.support = support;
          if (searchInput) searchInput.disabled = false;
          if (primary) primary.disabled = false;
          updateMatches();
          if (searchInput) searchInput.focus();
        })
        .catch(function (error) {
          if (state.disposed || !searchStatus) return;
          searchStatus.textContent = error && error.message
            ? error.message
            : "Catalogue images are unavailable.";
          searchStatus.hidden = false;
          searchStatus.classList.add("is-error");
        });
    },
    onSubmit: function (api) {
      var altInput = api.host.querySelector("#" + ALT_INPUT_ID);
      var detailInput = api.host.querySelector("#" + DETAIL_INPUT_ID);
      var alt = String(altInput && altInput.value || "").trim();
      var detailId = normalizeCatalogueDetailId(
        detailInput && !detailInput.disabled ? detailInput.value : ""
      );
      if (!state.selectedTarget || !state.selectedTarget.image) {
        api.setStatus("Choose a current Catalogue image.");
        return false;
      }
      if (!alt) {
        api.setStatus("Enter alt text.");
        if (altInput) altInput.focus();
        return false;
      }
      if (detailId === null) {
        api.setStatus("Enter a positive Work Detail ID using digits only, or leave it blank.");
        if (detailInput) detailInput.focus();
        return false;
      }
      function completeSubmission(detailTitle) {
        var captionInput = api.host.querySelector('[data-role="staged-media-caption-text"]');
        if (
          detailTitle
          && captionInput
          && (!captionInput.value || captionInput.value === state.captionDefault)
        ) {
          captionInput.value = detailTitle;
          state.captionDefault = detailTitle;
        }
        var presentation = readImagePresentation(api.host);
        if (presentation.addCaption && !presentation.caption) {
          api.setStatus("Enter caption text or turn off Add caption.");
          if (captionInput) captionInput.focus();
          return false;
        }
        var serialization = {
          registry: state.support && state.support.registry,
          targetType: state.selectedTarget.targetType,
          targetId: state.selectedTarget.targetId,
          detailId: detailId,
          alt: alt
        };
        if (presentation.addCaption) {
          Object.assign(serialization, {
            caption: presentation.caption,
            summary: presentation.summary,
            placement: presentation.placement,
            fillWidth: presentation.fillWidth
          });
        }
        var token = serializeCatalogueImageToken(serialization);
        if (!token) {
          api.setStatus("The selected image and presentation cannot be serialized.");
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
          token: token
        };
      }
      if (!detailId || typeof state.loadDetailTitle !== "function") {
        return completeSubmission("");
      }
      var selectedTarget = state.selectedTarget;
      return state.loadDetailTitle(selectedTarget.targetId, detailId).then(function (title) {
        return completeSubmission(title);
      });
    }
  });

  return modalPromise.then(function (result) {
    state.disposed = true;
    state.detailCaptionRequest += 1;
    if (state.list) state.list.destroy();
    if (adapter && typeof adapter.focus === "function") adapter.focus();
    return result;
  });
}
