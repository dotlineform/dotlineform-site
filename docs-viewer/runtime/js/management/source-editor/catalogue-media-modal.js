import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { catalogueWorkThumbnail } from "../../shared/docs-viewer-catalogue-media.js";
import { escapeHtml, openDocsViewerManagementModal } from "../docs-viewer-management-modal-shell.js";
import { selectedTextForCatalogueTitle } from "./catalogue-token-contract.js";
import { collectCatalogueMediaTargetMatches, loadCatalogueMediaTargets } from "./catalogue-media-targets.js";
import { serializeCatalogueImageToken, serializeCatalogueMediaToken } from "./source-token-parser.js";
import { createCatalogueTargetPickerList } from "./catalogue-target-picker.js";
import {
  catalogueImagePresentationHtml,
  hydrateCatalogueImagePresentation, readCatalogueImagePresentation
} from "./catalogue-image-presentation.js";

const SEARCH_INPUT_ID = "docsViewerCatalogueImageSearch";
const RESULTS_ID = "docsViewerCatalogueImageResults";
const CATALOGUE_ENTRY = "catalogue-entry";

function modalBody(searchQuery) {
  return `<div class="docsViewerCatalogueTokenModal docsViewerCatalogueImageModal">
    <div class="docsViewerCatalogueTokenModal__selection">
      <label class="docsViewer__fieldLabel" for="${SEARCH_INPUT_ID}">Search Catalogue</label>
      <input class="docsViewer__fieldInput" id="${SEARCH_INPUT_ID}" type="search" role="combobox" aria-autocomplete="list" aria-controls="${RESULTS_ID}" aria-expanded="false" autocomplete="off" spellcheck="false" value="${escapeHtml(searchQuery)}" disabled>
    </div>
    <p class="docsViewerCatalogueTokenModal__searchStatus muted small" data-role="catalogue-search-status" hidden></p>
    <div class="docsViewerCatalogueTargetPicker__results docsViewerCatalogueTokenModal__results" id="${RESULTS_ID}" role="listbox" aria-label="Catalogue Works and Galleries" data-role="catalogue-results" tabindex="0" hidden></div>
    <label class="docsViewer__field docsViewer__field--listbox" hidden><span class="docsViewer__fieldLabel" data-role="destination-label">Opens</span>
      <select class="docsViewer__fieldInput" data-role="destination" size="4"></select>
    </label>
    <div class="docsViewer__field" data-role="display" role="radiogroup" aria-labelledby="docsViewerCatalogueDisplayLabel" hidden>
      <span class="docsViewer__fieldLabel" id="docsViewerCatalogueDisplayLabel">Display</span>
      <div class="docsViewer__fieldGroup">
        <label class="docsViewer__field docsViewer__field--checkbox">
          <input class="docsViewer__checkboxInput" type="radio" name="catalogueDisplay" value="image"><span class="docsViewer__fieldLabel">Image</span>
        </label>
        <label class="docsViewer__field docsViewer__field--checkbox">
          <input class="docsViewer__checkboxInput" type="radio" name="catalogueDisplay" value="media"><span class="docsViewer__fieldLabel">Inline link</span>
        </label>
        <label class="docsViewer__field docsViewer__field--checkbox">
          <input class="docsViewer__checkboxInput" type="radio" name="catalogueDisplay" value="hidden"><span class="docsViewer__fieldLabel">Hidden</span>
        </label>
      </div>
    </div>
    <div data-role="image-options" hidden>${catalogueImagePresentationHtml({ idPrefix: "docsViewerCatalogueImage" })}</div>
    <label class="docsViewer__field" hidden><span class="docsViewer__fieldLabel">Link text</span>
      <input class="docsViewer__fieldInput" data-role="link-text" type="text" autocomplete="off">
    </label>
  </div>`;
}

/** Own the primary selection, its opening destination and one buffered occurrence. */
export function openCatalogueMediaModal({ root, action, adapter }) {
  const { capture, token, label } = action;
  const selectedText = token ? token.title : selectedTextForCatalogueTitle(capture.text);
  let authoredLabel = Boolean(selectedText);
  let target = null;
  let galleryLabel = "";
  let disposed = false;
  let list;
  return openDocsViewerManagementModal({
    root,
    restoreFocus: { focus: () => adapter.focus() },
    title: label,
    size: "document",
    bodyHtml: modalBody(token ? token.targetType + ":" + token.targetId : selectedText),
    focusSelector: "#" + SEARCH_INPUT_ID,
    actions: [
      { role: "modal-primary", label: token ? "Apply" : "Add", disabled: true },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen(api) {
      const role = (name) => api.host.querySelector('[data-role="' + name + '"]');
      const search = api.host.querySelector("#" + SEARCH_INPUT_ID);
      const results = role("catalogue-results");
      const status = role("catalogue-search-status");
      const primary = role("modal-primary");
      const destination = role("destination");
      const destinationLabel = role("destination-label");
      const workOption = new Option("This Work in Media View", "");
      const entryOption = new Option("Catalogue entry", CATALOGUE_ENTRY);
      const display = role("display");
      const displayOptions = destination.form.elements.namedItem("catalogueDisplay");
      const imageOption = display.querySelector('input[value="image"]');
      const imageOptions = role("image-options");
      const linkText = role("link-text");
      const galleries = new Map();
      let choices;
      let thumbnailSettings;
      mountSearchField(search).clearButton.tabIndex = -1;
      hydrateCatalogueImagePresentation(imageOptions, token?.presentation === "image" ? token : {
        useWorkTitleCaption: true, placement: "full", fillWidth: true
      });
      linkText.value = selectedText;
      function showResults(visible) {
        results.hidden = !visible;
        search.setAttribute("aria-expanded", String(visible));
      }
      function message(text, error = false) {
        status.textContent = text;
        status.hidden = !text;
        status.classList.toggle("is-error", error);
      }
      function showControls() {
        destination.closest("label").hidden = target?.targetType !== "work";
        display.hidden = !target;
        const imageSelected = imageOption.checked;
        entryOption.hidden = !imageSelected;
        entryOption.disabled = !imageSelected;
        if (!imageSelected && destination.value === CATALOGUE_ENTRY) destination.value = "";
        const hidden = displayOptions.value === "hidden";
        destinationLabel.textContent = hidden ? "Associate with" : "Opens";
        workOption.text = hidden ? "This Work" : "This Work in Media View";
        imageOptions.hidden = !target || !imageSelected;
        linkText.closest("label").hidden = !target || imageSelected;
        primary.disabled = !target || (!imageSelected && !linkText.value.trim());
      }
      function applyDestination(saved) {
        const id = destination.value === CATALOGUE_ENTRY ? "" : destination.value;
        const currentGalleryTitle = galleries.get(id)?.title;
        galleryLabel = saved?.galleryLabel || currentGalleryTitle || "";
        imageOption.disabled = target.targetType !== "work" || Boolean(id && !galleryLabel);
        if (!authoredLabel) linkText.value = id ? (currentGalleryTitle || galleryLabel) : target.title;
        showControls();
      }
      function selectTarget(next, saved) {
        target = next;
        search.value = next.title;
        list.setTargets([]);
        showResults(false);
        destination.replaceChildren();
        message("");
        if (next.targetType === "work") {
          destination.add(workOption);
          destination.add(entryOption);
          const members = choices.galleryIdsByWork[next.targetId] || [];
          for (const id of members) destination.add(new Option(id + " · " + galleries.get(id).title, id));
          if (saved?.galleryId && !members.includes(saved.galleryId)) {
            const id = saved.galleryId;
            const title = galleries.get(id)?.title || saved.galleryLabel || saved.title;
            const option = new Option(id + " · " + title + " (saved destination)", id);
            option.disabled = true;
            destination.add(option);
            message("The saved Gallery is no longer a direct membership. Keep it or choose another destination.");
          }
          destination.value = saved?.openEntry ? CATALOGUE_ENTRY : saved?.galleryId || "";
        }
        displayOptions.value = saved ? (saved.visible ? saved.presentation : "hidden") : next.targetType === "work" ? "image" : "media";
        applyDestination(saved);
      }
      destination.addEventListener("change", () => { applyDestination(); message(""); });
      display.addEventListener("change", showControls);
      linkText.addEventListener("input", () => { authoredLabel = true; showControls(); });
      function updateMatches() {
        if (!choices) return;
        target = null;
        showControls();
        const matches = collectCatalogueMediaTargetMatches(choices.targets, search.value, 20);
        list.setTargets(matches);
        showResults(matches.length > 0);
        if (search.value.trim() && !matches.length) message("No matching Catalogue Works or Galleries.");
        else if (!thumbnailSettings && matches.some((item) => item.targetType === "work")) message("Work thumbnails are unavailable.", true);
        else message("");
      }
      list = createCatalogueTargetPickerList(results, {
        layout: "id-title",
        thumbnailSrc: (item) => thumbnailSettings && item.targetType === "work"
          ? catalogueWorkThumbnail(item.targetId, item.title, thumbnailSettings).src : "",
        onActiveChange(_item, optionId) {
          for (const owner of [search, results]) {
            if (optionId) owner.setAttribute("aria-activedescendant", optionId);
            else owner.removeAttribute("aria-activedescendant");
          }
        },
        kind: (item) => item.targetType, id: (item) => item.targetId, title: (item) => item.title,
        onSelect(item) { selectTarget(item); search.focus(); }
      });
      search.addEventListener("input", updateMatches);
      for (const owner of [search, results]) {
        owner.addEventListener("keydown", (event) => {
          if (!event.isComposing) list.handleKeydown(event);
        });
      }
      for (const field of [search, linkText]) {
        field.addEventListener("keydown", (event) => {
          if (event.key !== "Enter" || event.defaultPrevented || event.isComposing || primary.disabled) return;
          event.preventDefault();
          if (!event.repeat) primary.click();
        });
      }
      Promise.all([
        loadCatalogueMediaTargets(() => adapter.readCatalogueMediaTargets()),
        adapter.readCatalogueThumbnailSettings().catch(() => null)
      ]).then(([loaded, thumbnails]) => {
        if (disposed) return;
        choices = loaded;
        thumbnailSettings = thumbnails;
        for (const item of choices.targets) if (item.targetType === "gallery") galleries.set(item.targetId, item);
        search.disabled = false;
        if (token) {
          const saved = choices.targets.find((item) => item.targetType === token.targetType && item.targetId === token.targetId);
          if (saved) selectTarget(saved, token);
          else message("The selected Catalogue target is unavailable.", true);
        } else updateMatches();
        search.focus();
      }).catch((error) => { if (!disposed) message(error.message || "Catalogue targets are unavailable.", true); });
    },
    onSubmit(api) {
      if (!adapter.isCurrent()) { api.setStatus("The Source editor was replaced. Cancel and try again."); return false; }
      if (!target) { api.setStatus("Choose a Catalogue target."); return false; }
      const destination = api.host.querySelector('[data-role="destination"]').value;
      const openEntry = destination === CATALOGUE_ENTRY;
      const fields = { targetType: target.targetType, targetId: target.targetId,
        galleryId: openEntry ? "" : destination };
      const display = api.host.querySelector('input[name="catalogueDisplay"]:checked').value;
      const source = display === "image"
        ? serializeCatalogueImageToken({ ...fields, openEntry, galleryLabel, ...readCatalogueImagePresentation(api.host) })
        : serializeCatalogueMediaToken({ ...fields, title: api.host.querySelector('[data-role="link-text"]').value, visible: display !== "hidden" });
      if (!source) { api.setStatus("Enter the required fields for this Catalogue reference."); return false; }
      if (!adapter.replaceCapturedSelection(capture, source)) {
        api.setStatus("Markdown source changed while this modal was open. Cancel and try again.");
        return false;
      }
      return { confirmed: true };
    }
  }).finally(() => {
    disposed = true;
    list?.destroy();
    adapter.focus();
  });
}
