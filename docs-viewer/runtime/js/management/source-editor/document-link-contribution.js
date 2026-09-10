import { DOCS_VIEWER_ACTION_IDS } from "../docs-viewer-action-definitions.js";
import { escapeHtml, openDocsViewerManagementModal } from "../docs-viewer-management-modal-shell.js";
import { createCatalogueTargetPickerList } from "./catalogue-target-picker.js";
import { filterDocumentLinkTargets, insertDocumentLink, normalizeDocumentLinkTargets } from "./document-link.js";

export const DOCUMENT_LINK_CONTROL_ID = "source-insert-doc-link";

/** Select one exact document using existing modal/list presentation and the mounted source adapter. */
export function openDocumentLinkModal(options) {
  var adapter = options.adapter;
  var target = adapter.getDocumentTarget();
  var state = { disposed: false, list: null, support: null, selected: null };
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: { focus: function () { if (options.isCurrent()) adapter.focus(); } },
    title: "Insert doc link",
    size: "document",
    focusSelector: "#docsViewerDocumentLinkSearch",
    bodyHtml: '<div class="docsViewerCatalogueTokenModal">'
      + '<label class="docsViewer__field" for="docsViewerDocumentLinkCollection"><span class="docsViewer__fieldLabel">Documents</span>'
      + '<select class="docsViewer__fieldInput" id="docsViewerDocumentLinkCollection" disabled>'
      + '<option value="all">All documents</option><option value="scope">Scope-level documents</option></select></label>'
      + '<label class="docsViewer__field" for="docsViewerDocumentLinkSearch"><span class="docsViewer__fieldLabel">Search documents</span>'
      + '<input class="docsViewer__fieldInput" id="docsViewerDocumentLinkSearch" type="search" role="combobox"'
      + ' aria-autocomplete="list" aria-controls="docsViewerDocumentLinkResults" aria-expanded="true" autocomplete="off" disabled></label>'
      + '<p class="docsViewerCatalogueTokenModal__searchStatus muted small" data-document-link-status>Loading documents…</p>'
      + '<div class="docsViewerCatalogueTargetPicker__results docsViewerCatalogueTokenModal__results"'
      + ' id="docsViewerDocumentLinkResults" role="listbox" aria-label="Documents" tabindex="0"></div></div>',
    actions: [
      { role: "modal-primary", label: "Insert link", disabled: true },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onOpen: function (api) {
      var search = api.host.querySelector("#docsViewerDocumentLinkSearch");
      var collection = api.host.querySelector("#docsViewerDocumentLinkCollection");
      var results = api.host.querySelector("#docsViewerDocumentLinkResults");
      var status = api.host.querySelector("[data-document-link-status]");
      var primary = api.host.querySelector('[data-role="modal-primary"]');
      function refresh() {
        if (!state.support) return;
        state.selected = null;
        primary.disabled = true;
        var filter = collection.value === "all" ? null : collection.value === "scope" ? "" : collection.value.slice(4);
        var matches = filterDocumentLinkTargets(state.support.documents, search.value, filter);
        state.list.setTargets(matches.slice(0, 100));
        status.textContent = !matches.length ? "No matching documents."
          : matches.length > 100 ? "Showing 100 of " + matches.length + " documents. Refine your search." : "";
        status.hidden = !status.textContent;
      }
      state.list = createCatalogueTargetPickerList(results, {
        id: function (record) { return record.target.doc_id; },
        kind: function (record) { return record.target.sub_scope || "Scope-level"; },
        title: function (record) { return record.title; },
        onSelect: function (record) {
          state.selected = record;
          primary.disabled = false;
        },
        onActiveChange: function (_record, optionId) {
          [search, results].forEach(function (element) {
            if (optionId) element.setAttribute("aria-activedescendant", optionId);
            else element.removeAttribute("aria-activedescendant");
          });
        }
      });
      search.addEventListener("input", refresh);
      collection.addEventListener("change", refresh);
      [search, results].forEach(function (element) {
        element.addEventListener("keydown", function (event) { state.list.handleKeydown(event); });
      });
      Promise.resolve().then(function () { return adapter.readDocumentLinkTargets(); }).then(function (payload) {
        if (state.disposed) return;
        if (!options.isCurrent()) throw new Error("The source document is no longer active. Cancel and try again.");
        state.support = normalizeDocumentLinkTargets(payload, target);
        state.support.subScopes.forEach(function (name) {
          collection.insertAdjacentHTML("beforeend", '<option value="sub:' + escapeHtml(name) + '">' + escapeHtml(name) + "</option>");
        });
        search.disabled = false;
        collection.disabled = false;
        refresh();
        search.focus();
      }).catch(function (error) {
        if (!state.disposed) {
          status.hidden = true;
          api.setStatus(error.message || "Document targets are unavailable.");
        }
      });
    },
    onSubmit: function (api) {
      if (!state.selected) {
        api.setStatus("Choose a document.");
        return false;
      }
      insertDocumentLink(adapter, options.capture, state.selected, options.isCurrent);
      return { confirmed: true, target: state.selected.target };
    }
  }).finally(function () {
    state.disposed = true;
    if (state.list) state.list.destroy();
  });
}

export function documentLinkControlDefinition() {
  return {
    id: DOCUMENT_LINK_CONTROL_ID,
    actionId: DOCS_VIEWER_ACTION_IDS.SOURCE_INSERT_DOC_LINK,
    label: "Insert doc link",
    ownerType: "view", ownerViewId: "rendered-document", modeIds: ["markdown-source"],
    surfaceId: "main-view", appKinds: ["manage"], features: ["source-editing"],
    renderer: DOCUMENT_LINK_CONTROL_ID
  };
}

export function documentLinkControlRenderer(context) {
  var button = context.existingRoot || context.document.createElement("button");
  button.className = "docsViewer__documentActionButton";
  button.type = "button";
  button.textContent = "📄";
  return button;
}

export function createDocumentLinkControlHandlers() {
  return {
    [DOCUMENT_LINK_CONTROL_ID]: function (context) {
      var services = context.sourceEditorServices;
      var adapter = services.getActiveSourceEditorContextAdapter();
      return openDocumentLinkModal({
        adapter: adapter, capture: adapter.captureSelection(), root: context.root,
        isCurrent: function () { return services.getActiveSourceEditorContextAdapter() === adapter; }
      });
    }
  };
}
