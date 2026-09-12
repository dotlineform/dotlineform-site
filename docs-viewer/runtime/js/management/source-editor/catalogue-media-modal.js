import { escapeHtml, openDocsViewerManagementModal } from "../docs-viewer-management-modal-shell.js";
import { selectedTextForCatalogueTitle } from "./catalogue-token-contract.js";
import { catalogueMediaLinkLabel, loadCatalogueMediaSupport, readCatalogueTokenPresentation } from "./catalogue-media-support.js";
import { collectSemanticTokenTargetMatches } from "./semantic-token-targets.js";
import { parseCatalogueToken, serializeCatalogueImageToken, serializeCatalogueMediaToken } from "./catalogue-token-parser.js";
import { createCatalogueTargetPickerList } from "./catalogue-target-picker.js";
import { catalogueWorkDetails } from "../../shared/docs-viewer-catalogue-media.js";
import {
  bindImagePresentation, hydrateImagePresentation, imagePresentationHtml, readImagePresentation
} from "./source-editor-image-presentation.js";

var SEARCH_INPUT_ID = "docsViewerCatalogueImageSearch";
var RESULTS_ID = "docsViewerCatalogueImageResults";
var ALT_INPUT_ID = "docsViewerCatalogueImageAlt";
var DETAIL_INPUT_ID = "docsViewerCatalogueImageDetailId";

function modalBody(searchQuery, alt, imageMode) {
  return (
    '<div class="docsViewerCatalogueTokenModal docsViewerCatalogueImageModal">' +
      '<label class="docsViewer__field" for="' + SEARCH_INPUT_ID + '">' +
        '<span class="docsViewer__fieldLabel">Search Catalogue</span>' +
        '<input class="docsViewer__fieldInput" id="' + SEARCH_INPUT_ID + '" type="search" role="combobox" aria-autocomplete="list" aria-controls="' + RESULTS_ID + '" aria-expanded="false" autocomplete="off" spellcheck="false" value="' + escapeHtml(searchQuery) + '" disabled>' +
      "</label>" +
      '<p class="docsViewerCatalogueTokenModal__searchStatus muted small" data-role="catalogue-search-status">Loading Catalogue…</p>' +
      '<div class="docsViewerCatalogueTargetPicker__results docsViewerCatalogueTokenModal__results" id="' + RESULTS_ID + '" role="listbox" aria-label="' + (imageMode ? "Catalogue Works" : "Catalogue Works and Series") + '" data-role="catalogue-results" tabindex="0" hidden></div>' +
      '<label class="docsViewer__field" data-role="catalogue-image-choice" for="' + DETAIL_INPUT_ID + '">' +
        '<span class="docsViewer__fieldLabel">Image</span>' +
        '<select class="docsViewer__fieldInput" id="' + DETAIL_INPUT_ID + '" disabled><option value="">Primary image</option></select>' +
      "</label>" +
      '<label class="docsViewer__field" for="' + ALT_INPUT_ID + '">' +
        '<span class="docsViewer__fieldLabel">' + (imageMode ? "Alt text" : "Link text") + '</span>' +
        '<input class="docsViewer__fieldInput" id="' + ALT_INPUT_ID + '" type="text" autocomplete="off" value="' + escapeHtml(alt) + '" required>' +
      "</label>" +
      (imageMode ? imagePresentationHtml({ idPrefix: "docsViewerCatalogueImage" }) : "") +
    "</div>"
  );
}

/** Share Catalogue selection while keeping image presentation and text-link authoring distinct. */
export function openCatalogueMediaModal(options = {}) {
  var imageMode = options.presentation === "image";
  var adapter = options.adapter;
  var capture = options.capture;
  var initialToken = !imageMode && parseCatalogueToken(capture && capture.text);
  if (initialToken && initialToken.presentation !== "media") initialToken = null;
  var selectionText = initialToken ? initialToken.title : selectedTextForCatalogueTitle(capture && capture.text);
  var state = { disposed: false, request: 0, list: null, support: null, target: null,
    details: [], workTitle: "", captionDefault: "", altDefault: "", replaceDefaults: null };
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: adapter && typeof adapter.focus === "function" ? { focus: function () { adapter.focus(); } } : null,
    title: imageMode ? "Add Catalogue image" : "Add Media View link",
    size: "document",
    bodyHtml: modalBody(initialToken ? initialToken.targetType + ":" + initialToken.targetId : selectionText, selectionText, imageMode),
    focusSelector: "#" + SEARCH_INPUT_ID,
    actions: [
      { role: "modal-primary", label: imageMode ? "Add image" : "Add link", disabled: true },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var modalRoot = api.host.querySelector('[data-role="docs-viewer-management-modal"]');
      var search = api.host.querySelector("#" + SEARCH_INPUT_ID);
      var detail = api.host.querySelector("#" + DETAIL_INPUT_ID);
      var alt = api.host.querySelector("#" + ALT_INPUT_ID);
      var caption = api.host.querySelector('[data-role="staged-media-caption-text"]');
      var results = api.host.querySelector('[data-role="catalogue-results"]');
      var status = api.host.querySelector('[data-role="catalogue-search-status"]');
      var primary = api.host.querySelector('[data-role="modal-primary"]');
      if (modalRoot) modalRoot.id = imageMode ? "catalogue-image-add-modal" : "catalogue-media-link-modal";
      if (imageMode) {
        bindImagePresentation(api.host);
        hydrateImagePresentation(api.host, { addCaption: true, caption: selectionText, placement: "full", fillWidth: true });
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
        if (!imageMode) {
          alt.value = catalogueMediaLinkLabel({ title: title }, alt.value, { title: state.altDefault }, Boolean(selectionText));
          state.altDefault = title;
          return;
        }
        [[caption, "captionDefault"], [alt, "altDefault"]].forEach(function (entry) {
          if (!entry[0].value || entry[0].value === state[entry[1]]) entry[0].value = title;
          state[entry[1]] = title;
        });
      };
      function chooseImage() {
        var selected = state.details.find(function (item) { return item.detail_id === detail.value; });
        state.replaceDefaults(selected ? selected.title : state.workTitle);
        primary.disabled = detail.selectedIndex < 0;
      }
      async function selectTarget(target, initialDetailId = "") {
        var request = ++state.request;
        state.target = target;
        state.details = [];
        primary.disabled = true;
        detail.disabled = true;
        detail.replaceChildren();
        api.host.querySelector('[data-role="catalogue-image-choice"]').hidden = target.targetType === "series";
        search.value = target.title;
        state.list.setTargets([]);
        showResults(false);
        message(target.targetType === "series" ? "Loading Series…" : "Loading Work images…");
        try {
          if (target.targetType === "series") {
            var series = await readCatalogueTokenPresentation(adapter, target);
            if (state.disposed || request !== state.request) return;
            state.replaceDefaults(series.label);
            primary.disabled = false;
            message("");
            return;
          }
          var payload = await adapter.readCatalogueWork(target.targetId);
          var details = catalogueWorkDetails(payload, target.targetId);
          if (state.disposed || request !== state.request) return;
          state.details = details;
          state.workTitle = payload.work.title;
          var documentRef = api.host.ownerDocument;
          var option = documentRef.createElement("option");
          option.value = "";
          option.textContent = "Primary image";
          detail.appendChild(option);
          details.forEach(function (item) {
            var option = documentRef.createElement("option");
            option.value = item.detail_id;
            option.textContent = item.detail_id + " — " + item.title;
            detail.appendChild(option);
          });
          detail.disabled = !details.length;
          detail.value = initialDetailId;
          if (initialDetailId && !details.some(function (item) { return item.detail_id === initialDetailId; })) {
            throw new Error("The selected Detail is unavailable. Choose an image.");
          }
          chooseImage();
          primary.disabled = false;
          message("");
        } catch (error) {
          if (!state.disposed && request === state.request) message(error.message || "Work images are unavailable.", true);
        }
      }
      function updateMatches() {
        if (!state.support) return;
        state.request += 1;
        state.target = null;
        primary.disabled = true;
        detail.disabled = true;
        detail.replaceChildren();
        var targets = imageMode ? state.support.targets.filter(function (target) { return target.targetType === "work"; }) : state.support.targets;
        var matches = collectSemanticTokenTargetMatches(targets, search.value, state.support.registry, 20);
        state.list.setTargets(matches);
        showResults(true);
        message(search.value.trim() && !matches.length ? (imageMode ? "No matching Catalogue Works." : "No matching Catalogue Works or Series.") : "");
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
      detail.addEventListener("change", chooseImage);
      loadCatalogueMediaSupport(adapter, { fetch: options.fetch }).then(function (support) {
        if (state.disposed) return;
        state.support = support;
        search.disabled = false;
        updateMatches();
        if (initialToken) {
          var target = support.targets.find(function (item) {
            return item.targetType === initialToken.targetType && item.targetId === initialToken.targetId;
          });
          if (target) selectTarget(target, initialToken.detailId);
          else message("The selected Catalogue target is unavailable.", true);
        }
        search.focus();
      }).catch(function (error) {
        if (!state.disposed) message(error.message || "Catalogue images are unavailable.", true);
      });
    },
    onSubmit: async function (api) {
      if (!state.target) { api.setStatus("Choose a Catalogue target."); return false; }
      var detail = api.host.querySelector("#" + DETAIL_INPUT_ID);
      var detailId = state.target.targetType === "series" ? "" : detail.value;
      // Revalidate current media before writing source, including Details removed while the modal was open.
      var current = await readCatalogueTokenPresentation(adapter, state.target, detailId);
      state.replaceDefaults(current.label);
      var alt = String(api.host.querySelector("#" + ALT_INPUT_ID).value || "").trim();
      if (!alt) { api.setStatus(imageMode ? "Enter alt text." : "Enter link text."); return false; }
      var presentation = imageMode ? readImagePresentation(api.host) : null;
      if (presentation && presentation.addCaption && !presentation.caption) {
        api.setStatus("Enter caption text or turn off Add caption.");
        return false;
      }
      var fields = { registry: state.support.registry, targetType: state.target.targetType, targetId: state.target.targetId, detailId: detailId, alt: alt, title: alt };
      if (presentation && presentation.addCaption) {
        Object.assign(fields, { caption: presentation.caption, summary: presentation.summary,
          placement: presentation.placement, fillWidth: presentation.fillWidth });
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
