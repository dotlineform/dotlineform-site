import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { escapeHtml, openDocsViewerManagementModal } from "./docs-viewer-management-modal-shell.js";
import { readCatalogueMediaTargets, setManagedDocThumbnail } from "./docs-viewer-management-client.js";
import { createCatalogueTargetPickerList } from "./source-editor/catalogue-target-picker.js";
import { loadCatalogueMediaSupport } from "./source-editor/catalogue-media-support.js";
import { collectSemanticTokenTargetMatches } from "./source-editor/semantic-token-targets.js";
import { requestUrl } from "../shared/docs-viewer-asset-url.js";

/** Choose copied artwork independently of tokens and Source Save. No Work is retained.
 * @param {Object} options
 * @param {HTMLElement} options.root Management modal owner.
 * @param {{collection: string, doc_id: string}} options.target Exact authored document.
 * @param {{has_thumbnail?: boolean}} options.record Current committed metadata.
 * @param {string} options.mediaRoot Configured document-media URL owner.
 * @param {Object} options.clientOptions Local management transport.
 * @param {function(Object): Error[]} options.commitDocumentChange Retained-view projection.
 */
export function openDocumentThumbModal(options) {
  const target = options.target;
  const state = { disposed: false, busy: false, list: null, support: null, work: null };
  const src = options.record.has_thumbnail
    ? requestUrl(options.mediaRoot.replace(/\/+$/, "") + "/collections/" + encodeURIComponent(target.collection)
      + "/thumbs/" + encodeURIComponent(target.doc_id + "-thumb.webp"), { reloadNonce: Date.now() }) : "";
  async function save(workId) {
    const response = await setManagedDocThumbnail(target, workId, options.clientOptions);
    const failures = options.commitDocumentChange({ target, record: response.record }) || [];
    if (failures.length) throw new Error("Thumbnail saved, but a retained list could not be updated: "
      + failures.map((error) => error.message).join("; "));
    return { confirmed: true };
  }
  return openDocsViewerManagementModal({
    root: options.root, title: "Thumb", size: "document",
    bodyHtml: '<div class="docsViewer__field"><span class="docsViewer__fieldLabel">Current thumbnail</span>'
      + (src ? '<img src="' + escapeHtml(src) + '" alt="Current document thumbnail" width="96" height="96">'
        : '<p class="muted small">No thumbnail.</p>') + '</div>'
      + '<label class="docsViewer__field"><span class="docsViewer__fieldLabel">Search Catalogue Works</span>'
      + '<input class="docsViewer__fieldInput" data-role="thumb-search" type="search" role="combobox" aria-autocomplete="list"'
      + ' aria-controls="docsViewerThumbResults" aria-expanded="false" autocomplete="off" disabled></label>'
      + '<div class="docsViewerCatalogueTargetPicker__results docsViewerCatalogueTokenModal__results" id="docsViewerThumbResults"'
      + ' role="listbox" aria-label="Catalogue Works" data-role="thumb-results" tabindex="0" hidden></div>'
      + '<p class="muted small" data-role="thumb-selection">Choose a Work to copy its current thumbnail.</p>',
    focusSelector: '[data-role="thumb-search"]',
    actions: [
      { role: "modal-delete", label: "Delete thumbnail", disabled: !options.record.has_thumbnail },
      { role: "modal-primary", label: "Apply", disabled: true },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen(api) {
      const search = api.host.querySelector('[data-role="thumb-search"]');
      const results = api.host.querySelector('[data-role="thumb-results"]');
      const primary = api.host.querySelector('[data-role="modal-primary"]');
      const selection = api.host.querySelector('[data-role="thumb-selection"]');
      mountSearchField(search);
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
          primary.disabled = false;
          showResults(false);
        }
      });
      search.addEventListener("input", () => {
        if (!state.support) return;
        state.work = null;
        primary.disabled = true;
        const matches = collectSemanticTokenTargetMatches(state.support.targets, search.value, state.support.registry, 20);
        state.list.setTargets(matches);
        showResults(matches.length > 0);
        selection.textContent = matches.length ? "Choose a Work to copy its current thumbnail." : "No matching Works.";
      });
      [search, results].forEach((node) => node.addEventListener("keydown", (event) => state.list.handleKeydown(event)));
      api.host.querySelector('[data-role="modal-delete"]').addEventListener("click", async () => {
        state.busy = true;
        api.setBusy(true);
        api.setStatus("");
        try {
          const result = await save(null);
          api.close(result);
        } catch (error) {
          api.setStatus(error.message);
        } finally {
          state.busy = false;
          if (!state.disposed) {
            api.setBusy(false);
            search.disabled = !state.support;
          }
        }
      });
      loadCatalogueMediaSupport({
        readCatalogueMediaTargets: () => readCatalogueMediaTargets(options.clientOptions)
      }, { fetch: options.clientOptions.fetch }).then((support) => {
        if (state.disposed) return;
        state.support = { ...support, targets: support.targets.filter((work) => work.targetType === "work") };
        if (!state.busy) { search.disabled = false; search.focus(); }
      }).catch((error) => { if (!state.disposed) api.setStatus(error.message); });
    },
    onSubmit() { return save(state.work.targetId); }
  }).finally(() => {
    state.disposed = true;
    state.list?.destroy();
    state.support = null;
  });
}
