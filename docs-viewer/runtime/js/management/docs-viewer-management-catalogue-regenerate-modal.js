import {
  escapeHtml,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";

function recordsHtml(records) {
  return '<ul class="docsViewerScopeLifecycle__list">' + records.map(function (record) {
    return "<li>" + escapeHtml(record.work_id + " — " + record.title + " (" + record.operation + ")") + "</li>";
  }).join("") + "</ul>";
}

/** Present one preview/apply flow; source and report operations are supplied by the workflow. */
export function openCatalogueRegenerateModal(options) {
  var preview = null;
  var result = null;
  var phase = "previewing";
  var api;
  var checkbox;
  var primary;
  var closeButton;
  var content;

  function setBusy(busy) {
    api.setBusy(busy);
    options.onBusyChange(busy);
  }

  function ready() {
    setBusy(false);
    checkbox.disabled = phase === "result";
    primary.disabled = false;
    closeButton.hidden = phase === "result" || Boolean(preview && preview.counts.selected === 0);
    primary.textContent = closeButton.hidden
      ? "Close" : phase === "preview-error" ? "Preview" : "Regenerate";
  }

  function refreshPreview() {
    phase = "previewing";
    preview = null;
    api.setStatus("");
    setBusy(true);
    content.textContent = "Reading Catalogue Works…";
    return options.preview(checkbox.checked).then(function (payload) {
      preview = payload;
      phase = "preview";
      var counts = payload.counts;
      content.innerHTML = "<p>" + escapeHtml(
        "Create: " + counts.create + ". Regenerate: " + counts.regenerate + ". Skip: " + counts.skip + "."
      ) + "</p>" + (counts.selected
        ? (checkbox.checked ? "" : "<p>Existing document bodies will be replaced.</p>")
          + "<details><summary>Selected Works (" + counts.selected + ")</summary>"
          + recordsHtml(payload.records) + "</details>"
        : "<p>No documents to create.</p>");
    }).catch(function (error) {
      phase = "preview-error";
      content.textContent = "Preview unavailable.";
      api.setStatus(error.message);
    }).finally(ready);
  }

  function apply() {
    phase = "applying";
    api.setStatus("");
    setBusy(true);
    content.textContent = "Regenerating documents…";
    return options.apply(preview).then(function (payload) {
      phase = "result";
      result = payload;
      content.textContent = payload.summary_text;
    }).catch(function (error) {
      if (error.status === 409) {
        phase = "preview-error";
        preview = null;
        content.textContent = "Preview again before applying.";
      } else {
        phase = "result";
        result = { ...error.payload, ok: false, error: error.message };
        var completed = Array.isArray(result.completed_records) ? result.completed_records : [];
        content.innerHTML = "<p>" + escapeHtml("Sources written: " + completed.length + ".") + "</p>"
          + (completed.length ? "<details><summary>Written documents</summary>" + recordsHtml(completed) + "</details>" : "");
      }
      api.setStatus(error.message);
    }).finally(ready);
  }

  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Regenerate Catalogue",
    bodyHtml: '<label class="docsViewer__field"><span><input type="checkbox" data-regenerate-new-only checked> Only create new docs</span></label>'
      + '<div data-regenerate-preview aria-live="polite"></div>',
    actions: [
      { role: "modal-primary", label: "Regenerate", disabled: true },
      { role: "modal-cancel", label: "Close" }
    ],
    focusSelector: "[data-regenerate-new-only]",
    onOpen: function (modalApi) {
      api = modalApi;
      checkbox = api.host.querySelector("[data-regenerate-new-only]");
      primary = api.host.querySelector('[data-role="modal-primary"]');
      closeButton = api.host.querySelector('button[data-role="modal-cancel"]');
      content = api.host.querySelector("[data-regenerate-preview]");
      checkbox.addEventListener("change", refreshPreview);
      refreshPreview();
    },
    onSubmit: function () {
      if (phase === "result" || (preview && preview.counts.selected === 0)) return { confirmed: true };
      if (phase === "preview-error") refreshPreview();
      else if (phase === "preview") apply();
      return false;
    }
  }).then(function () { return result; });
}
