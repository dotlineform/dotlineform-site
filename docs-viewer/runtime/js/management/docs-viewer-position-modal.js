import { mountSearchField } from "/shared/frontend/js/search-field.js";
import { collectDescendantDocIds } from "./docs-viewer-management-action-workflow.js";
import { escapeHtml, openDocsViewerManagementModal } from "./docs-viewer-management-modal-shell.js";

export function openDocsViewerIndexPositionModal(options) {
  var docs = options.docs;
  var excluded = collectDescendantDocIds(docs, options.doc.doc_id);
  excluded.add(options.doc.doc_id);
  var depths = new Map();
  var rootOnly = options.collectionHostDocIds.includes(options.doc.doc_id);
  var rootDestination = { id: "", title: "Root", depth: 0 };
  var destinations = [];
  docs.forEach(function (doc) {
    var depth = doc.parent_id ? (depths.get(doc.parent_id) || 0) + 1 : 0;
    depths.set(doc.doc_id, depth);
    if (!excluded.has(doc.doc_id) && (!rootOnly || !doc.parent_id)) {
      destinations.push({ id: doc.doc_id, title: doc.title, depth: depth });
    }
  });
  var insideDestinations = rootOnly ? [rootDestination] : [rootDestination, ...destinations];
  var besideDestinations = [{ ...rootDestination, disabled: true }, ...destinations];

  return openDocsViewerPositionModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Position " + options.doc.title,
    note: "Document: " + options.doc.title + " (" + options.doc.doc_id + "). Moves this document with all its descendants.",
    insideLabel: rootOnly ? "Inside Root" : "Inside (last child)",
    getDestinations: function (placement) {
      return placement === "inside" ? insideDestinations : besideDestinations;
    },
    onSave: options.onSave
  });
}

export function openDocsViewerPositionModal(options) {
  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: options.title,
    bodyHtml:
      (options.note ? '<p class="docsViewer__modalNote muted small">' + escapeHtml(options.note) + '</p>' : '') +
      '<label class="docsViewer__fieldLabel" for="docsViewerPositionPlacement">Position</label>' +
      '<select class="docsViewer__fieldInput" id="docsViewerPositionPlacement">' +
        '<option value="before">Before</option><option value="after">After</option><option value="inside">' + escapeHtml(options.insideLabel) + '</option>' +
      '</select>' +
      '<label class="docsViewer__fieldLabel" for="docsViewerPositionSearch">Find destination</label>' +
      '<input class="docsViewer__fieldInput" id="docsViewerPositionSearch" type="search" autocomplete="off">' +
      '<label class="docsViewer__fieldLabel" for="docsViewerPositionTarget">Destination</label>' +
      '<select class="docsViewer__fieldInput docsViewer__positionTargets" id="docsViewerPositionTarget" size="9"></select>',
    actions: [
      { role: "modal-cancel", label: "Cancel" },
      { role: "modal-primary", label: "Save" }
    ],
    focusSelector: "#docsViewerPositionSearch",
    onOpen: function (api) {
      var search = api.host.querySelector("#docsViewerPositionSearch");
      mountSearchField(search);
      var placement = api.host.querySelector("#docsViewerPositionPlacement");
      var target = api.host.querySelector("#docsViewerPositionTarget");
      if (options.initialPlacement) placement.value = options.initialPlacement;
      function renderDestinations() {
        var selectedId = target.selectedIndex < 0 ? null : target.value;
        var query = search.value.trim().toLowerCase();
        target.innerHTML = options.getDestinations(placement.value).filter(function (destination) {
          return !destination.id || !query || destination.title.toLowerCase().includes(query);
        }).map(function (destination) {
          var label = "\u00a0\u00a0".repeat(destination.depth) + destination.title;
          return '<option value="' + escapeHtml(destination.id) + '"' + (destination.disabled ? " disabled" : "") + '>' + escapeHtml(label) + '</option>';
        }).join("");
        target.selectedIndex = -1;
        if (selectedId !== null) {
          var selectedOption = Array.from(target.options).find(function (option) {
            return option.value === selectedId && !option.disabled;
          });
          if (selectedOption) selectedOption.selected = true;
        }
      }
      search.addEventListener("input", renderDestinations);
      placement.addEventListener("change", renderDestinations);
      renderDestinations();
    },
    onSubmit: function (api) {
      var target = api.host.querySelector("#docsViewerPositionTarget");
      var placement = api.host.querySelector("#docsViewerPositionPlacement").value;
      if (target.selectedIndex < 0 || target.options[target.selectedIndex].disabled) {
        api.setStatus("Choose a destination.");
        return false;
      }
      return options.onSave(target.value, placement);
    }
  });
}
