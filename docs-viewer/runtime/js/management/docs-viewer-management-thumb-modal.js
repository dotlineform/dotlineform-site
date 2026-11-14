import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { escapeHtml, openDocsViewerManagementModal } from "./docs-viewer-management-modal-shell.js";
import { readCatalogueMediaTargets, setManagedDocThumbnail } from "./docs-viewer-management-client.js";
import { createCatalogueTargetPickerList } from "./source-editor/catalogue-target-picker.js";
import { loadCatalogueMediaSupport } from "./source-editor/catalogue-media-support.js";
import { collectSemanticTokenTargetMatches } from "./source-editor/semantic-token-targets.js";
import { requestUrl } from "../shared/docs-viewer-asset-url.js";

const THUMBNAIL_MAX_EDGE = 96;
const DOCUMENT_IMAGE_PATH = /^(?:workspace|collections\/[^/]+)\/(?:img|svg)\//;
const CATALOGUE_SELECTION_HINT = "Choose a Work to copy its current thumbnail.";

function documentImages(mount, mediaRoot) {
  const mediaPrefix = mediaRoot.replace(/\/+$/, "") + "/";
  return Array.from(mount.querySelectorAll("img[src]")).filter((image) => {
    const src = image.getAttribute("src");
    return (src.startsWith(mediaPrefix) && DOCUMENT_IMAGE_PATH.test(src.slice(mediaPrefix.length)))
      || image.matches("[data-docs-catalogue-ref] img[data-docs-media-image]");
  });
}

function imageChoices(images) {
  if (!images.length) return '<p class="muted small">This document has no images.</p>';
  return '<fieldset class="docsViewer__fieldGroup docsViewerThumb__images"><legend>Document images</legend>'
    + images.map((image, index) => {
      const label = image.alt.trim() || "Image " + (index + 1);
      return '<label class="docsViewerThumb__image">'
        + '<input type="radio" name="thumb-image">'
        + '<img src="' + escapeHtml(image.currentSrc || image.src) + '" alt="" loading="lazy">'
        + '<span>' + escapeHtml(label) + '</span></label>';
    }).join("") + '</fieldset>';
}

async function thumbnailPixels(image) {
  try {
    image.loading = "eager";
    await image.decode();
    const scale = Math.min(1, THUMBNAIL_MAX_EDGE / Math.max(image.naturalWidth, image.naturalHeight));
    const canvas = image.ownerDocument.createElement("canvas");
    canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
    canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
    const context = canvas.getContext("2d");
    context.imageSmoothingQuality = "high";
    context.drawImage(image, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/png").split(",")[1];
  } catch (error) {
    throw new Error("Could not prepare the selected document image: " + error.message, { cause: error });
  }
}

/** Choose independent artwork from the rendered document or Catalogue Works.
 * @param {Object} options
 * @param {HTMLElement} options.root Management modal owner.
 * @param {{collection: string, doc_id: string}} options.target Exact authored document.
 * @param {{has_thumbnail?: boolean}} options.record Current committed metadata.
 * @param {HTMLElement} options.documentMount Current document's mounted body.
 * @param {string} options.mediaRoot Configured document-media URL owner.
 * @param {Object} options.clientOptions Local management transport.
 * @param {function(Object): Error[]} options.commitDocumentChange Retained-view projection.
 */
export function openDocumentThumbModal(options) {
  const target = options.target;
  const images = documentImages(options.documentMount, options.mediaRoot);
  const showDocument = images.length > 0;
  const state = { disposed: false, list: null, support: null, work: null };
  const src = options.record.has_thumbnail
    ? requestUrl(options.mediaRoot.replace(/\/+$/, "") + "/collections/" + encodeURIComponent(target.collection)
      + "/thumbs/" + encodeURIComponent(target.doc_id + "-thumb.webp"), { reloadNonce: Date.now() }) : "";
  async function save(selection) {
    const response = await setManagedDocThumbnail(target, selection, options.clientOptions);
    const failures = options.commitDocumentChange({ target, record: response.record }) || [];
    if (failures.length) throw new Error("Thumbnail saved, but a retained list could not be updated: "
      + failures.map((error) => error.message).join("; "));
    return { confirmed: true };
  }
  return openDocsViewerManagementModal({
    root: options.root, title: "Thumb", size: "document",
    bodyHtml: '<div class="docsViewer__field"><span class="docsViewer__fieldLabel">Current thumbnail</span>'
      + (src ? '<img class="docsViewerThumb__current" src="' + escapeHtml(src) + '" alt="Current document thumbnail" width="96" height="96">'
        : '<p class="muted small">No thumbnail.</p>') + '</div>'
      + '<label class="docsViewer__field"><span class="docsViewer__fieldLabel">Image source</span>'
      + '<select class="docsViewer__fieldInput" data-role="thumb-source">'
      + '<option value="document"' + (showDocument ? ' selected' : '') + '>From this document</option>'
      + '<option value="catalogue"' + (showDocument ? '' : ' selected') + '>Catalogue Works</option></select></label>'
      + '<div data-role="thumb-document"' + (showDocument ? '' : ' hidden') + '>' + imageChoices(images) + '</div>'
      + '<div data-role="thumb-catalogue"' + (showDocument ? ' hidden' : '') + '>'
      + '<label class="docsViewer__field"><span class="docsViewer__fieldLabel">Search Catalogue Works</span>'
      + '<input class="docsViewer__fieldInput" data-role="thumb-search" type="search" role="combobox" aria-autocomplete="list"'
      + ' aria-controls="docsViewerThumbResults" aria-expanded="false" autocomplete="off" disabled></label>'
      + '<div class="docsViewerCatalogueTargetPicker__results docsViewerCatalogueTokenModal__results" id="docsViewerThumbResults"'
      + ' role="listbox" aria-label="Catalogue Works" data-role="thumb-results" tabindex="0" hidden></div>'
      + '<p class="muted small" data-role="thumb-selection" aria-live="polite">' + CATALOGUE_SELECTION_HINT + '</p></div>',
    focusSelector: '[data-role="thumb-source"]',
    actions: [
      { role: "modal-delete", label: "Delete thumbnail", disabled: !options.record.has_thumbnail },
      { role: "modal-primary", label: "Apply", disabled: true },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen(api) {
      const form = api.host.querySelector('[data-role="modal-form"]');
      const source = api.host.querySelector('[data-role="thumb-source"]');
      const documentChoices = api.host.querySelector('[data-role="thumb-document"]');
      const catalogueChoices = api.host.querySelector('[data-role="thumb-catalogue"]');
      const search = api.host.querySelector('[data-role="thumb-search"]');
      const results = api.host.querySelector('[data-role="thumb-results"]');
      const primary = api.host.querySelector('[data-role="modal-primary"]');
      const selection = api.host.querySelector('[data-role="thumb-selection"]');
      let catalogueRequested = false;
      const { clearButton } = mountSearchField(search);
      function projectSelection() {
        primary.disabled = source.value === "document"
          ? !documentChoices.querySelector('input:checked') : !state.work;
      }
      function loadCatalogue() {
        if (catalogueRequested) return;
        catalogueRequested = true;
        loadCatalogueMediaSupport({
          readCatalogueMediaTargets: () => readCatalogueMediaTargets(options.clientOptions)
        }, { fetch: options.clientOptions.fetch }).then((support) => {
          if (state.disposed) return;
          state.support = { ...support, targets: support.targets.filter((work) => work.targetType === "work") };
          if (!form.dataset.busy) search.disabled = false;
        }).catch((error) => { if (!state.disposed) selection.textContent = error.message; });
      }
      source.addEventListener("change", () => {
        const fromDocument = source.value === "document";
        documentChoices.hidden = !fromDocument;
        catalogueChoices.hidden = fromDocument;
        projectSelection();
        if (!fromDocument) loadCatalogue();
      });
      documentChoices.addEventListener("change", projectSelection);
      form.addEventListener("docs-viewer-modal-busy-change", (event) => {
        catalogueChoices.inert = event.detail.busy;
        clearButton.disabled = event.detail.busy;
        if (!event.detail.busy && state.support) search.disabled = false;
      });
      function showResults(visible) {
        results.hidden = !visible;
        search.setAttribute("aria-expanded", String(visible));
      }
      state.list = createCatalogueTargetPickerList(results, {
        layout: "id-title", kind: (work) => work.targetType,
        id: (work) => work.targetId, title: (work) => work.title,
        onActiveChange(_work, optionId) {
          if (optionId) search.setAttribute("aria-activedescendant", optionId);
          else search.removeAttribute("aria-activedescendant");
        },
        onSelect(work) {
          state.work = work;
          search.value = work.title;
          selection.textContent = work.targetId + " · " + work.title;
          projectSelection();
          showResults(false);
        }
      });
      search.addEventListener("input", () => {
        if (!state.support) return;
        state.work = null;
        projectSelection();
        const matches = collectSemanticTokenTargetMatches(state.support.targets, search.value, state.support.registry, 20);
        state.list.setTargets(matches);
        showResults(matches.length > 0);
        selection.textContent = matches.length ? CATALOGUE_SELECTION_HINT : "No matching Works.";
      });
      [search, results].forEach((node) => node.addEventListener("keydown", (event) => state.list.handleKeydown(event)));
      api.host.querySelector('[data-role="modal-delete"]').addEventListener("click", async () => {
        api.setBusy(true);
        api.setStatus("");
        try {
          const result = await save({ work_id: null });
          api.close(result);
        } catch (error) {
          api.setStatus(error.message);
        } finally {
          if (!state.disposed) api.setBusy(false);
        }
      });
      if (!showDocument) loadCatalogue();
    },
    async onSubmit(api) {
      if (api.host.querySelector('[data-role="thumb-source"]').value === "catalogue") {
        return save({ work_id: state.work.targetId });
      }
      const selected = api.host.querySelector('input[name="thumb-image"]:checked');
      const preview = selected.closest("label").querySelector("img");
      return save({ image_png: await thumbnailPixels(preview) });
    }
  }).finally(() => {
    state.disposed = true;
    state.list?.destroy();
    state.support = null;
  });
}
