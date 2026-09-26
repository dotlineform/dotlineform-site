import { collectDescendantDocIds } from "./docs-viewer-management-action-workflow.js";
import { escapeHtml, openDocsViewerManagementModal } from "./docs-viewer-management-modal-shell.js";

export function openDocsViewerPositionModal(options) {
  var docs = options.docs;
  var excluded = collectDescendantDocIds(docs, options.doc.doc_id);
  excluded.add(options.doc.doc_id);
  var depths = new Map();
  var destinations = [{ doc_id: "", title: "Root", depth: 0 }];
  docs.forEach(function (doc) {
    var depth = doc.parent_id ? (depths.get(doc.parent_id) || 0) + 1 : 0;
    depths.set(doc.doc_id, depth);
    if (!excluded.has(doc.doc_id)) destinations.push({ ...doc, depth: depth });
  });

  return openDocsViewerManagementModal({
    root: options.root,
    title: "Position " + options.doc.title,
    bodyHtml:
      '<label class="docsViewer__fieldLabel" for="docsViewerPositionPlacement">Position</label>' +
      '<select class="docsViewer__fieldInput" id="docsViewerPositionPlacement">' +
        '<option value="before">Before</option><option value="after">After</option><option value="inside">Inside (last child)</option>' +
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
      var placement = api.host.querySelector("#docsViewerPositionPlacement");
      var target = api.host.querySelector("#docsViewerPositionTarget");
      function renderDestinations() {
        var selectedId = target.selectedIndex < 0 ? null : target.value;
        var query = search.value.trim().toLowerCase();
        target.innerHTML = destinations.filter(function (doc) {
          return (!doc.doc_id || !query || doc.title.toLowerCase().includes(query));
        }).map(function (doc) {
          var disabled = !doc.doc_id && placement.value !== "inside";
          var label = "\u00a0\u00a0".repeat(doc.depth) + doc.title;
          return '<option value="' + escapeHtml(doc.doc_id) + '"' + (disabled ? " disabled" : "") + '>' + escapeHtml(label) + '</option>';
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
