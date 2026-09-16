import { openDocsViewerManagementModal } from "./docs-viewer-management-modal-shell.js";

/** Collect both Catalogue document fields before the single create request. */
export function openDocsViewerCatalogueCreateModal(options = {}) {
  return openDocsViewerManagementModal({
    root: options.root,
    title: "New",
    size: "compact",
    bodyHtml:
      '<label class="docsViewer__field docsViewer__field--compactLabel">' +
        '<span class="docsViewer__fieldLabel">work_id</span>' +
        '<input class="docsViewer__fieldInput" data-catalogue-create-work-id type="text" inputmode="numeric" autocomplete="off" spellcheck="false" required>' +
      '</label>' +
      '<label class="docsViewer__field docsViewer__field--compactLabel">' +
        '<span class="docsViewer__fieldLabel">title</span>' +
        '<input class="docsViewer__fieldInput" data-catalogue-create-title type="text" autocomplete="off" required>' +
      '</label>',
    focusSelector: "[data-catalogue-create-work-id]",
    actions: [
      { role: "modal-primary", label: "Create" },
      { role: "modal-cancel", label: "Cancel" }
    ],
    onSubmit: function (api) {
      var workIdInput = api.host.querySelector("[data-catalogue-create-work-id]");
      var titleInput = api.host.querySelector("[data-catalogue-create-title]");
      var workId = workIdInput.value.trim();
      var title = titleInput.value.trim();
      if (!/^[0-9]{5}$/.test(workId)) {
        api.setStatus("Enter a five-digit work_id.");
        workIdInput.focus();
        return false;
      }
      if (!title) {
        api.setStatus("Enter a title.");
        titleInput.focus();
        return false;
      }
      return { confirmed: true, fields: { work_id: workId, title: title } };
    }
  });
}
