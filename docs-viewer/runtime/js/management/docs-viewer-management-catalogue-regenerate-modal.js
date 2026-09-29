import {
  escapeHtml,
  openDocsViewerManagementModal
} from "./docs-viewer-management-modal-shell.js";

/** Let the user choose one mode, then keep the modal busy through Run and report refresh. */
export function openCatalogueRegenerateModal(options) {
  var result = null;
  var phase = "ready";
  var api;
  var primary;
  var closeButton;
  var content;
  var choices;

  function setBusy(busy) {
    api.setBusy(busy);
    options.onBusyChange(busy);
  }

  function finish() {
    setBusy(false);
    choices.forEach(function (choice) { choice.disabled = true; });
    closeButton.hidden = true;
    primary.textContent = "Close";
    primary.disabled = false;
  }

  function run() {
    phase = "running";
    api.setStatus("");
    setBusy(true);
    content.textContent = "Reconciling Catalogue documents…";
    var mode = api.host.querySelector('[name="catalogue-regenerate-mode"]:checked').value;
    options.run(mode).then(function (payload) {
      result = payload;
      phase = "result";
      var counts = payload.counts;
      content.innerHTML = "<div>" + escapeHtml("Updated " + counts.updated) + "</div>"
        + "<div>" + escapeHtml("Created " + counts.create) + "</div>"
        + "<div>" + escapeHtml("Deleted " + counts.delete) + "</div>";
    }).catch(function (error) {
      phase = "error";
      result = { ...error.payload, ok: false, error: error.message };
      if (error.payload?.ok) {
        content.textContent = "Catalogue documents were updated, but the report could not refresh.";
      } else if (result.committed_source_operations) {
        content.textContent = "Source operations completed: " + result.committed_source_operations + ". Inspect the error before retrying.";
      } else {
        content.textContent = "Regenerate stopped before completing.";
      }
      api.setStatus(error.message);
    }).finally(finish);
  }

  return openDocsViewerManagementModal({
    root: options.root,
    restoreFocus: options.restoreFocus,
    title: "Regenerate Catalogue",
    bodyHtml: '<fieldset class="docsViewer__fieldGroup"><legend class="visually-hidden">Catalogue regeneration mode</legend>'
      + '<label class="docsViewer__field docsViewer__field--checkbox"><input class="docsViewer__checkboxInput" type="radio" name="catalogue-regenerate-mode" value="pending" checked><span class="docsViewer__fieldLabel">Pending updates</span></label>'
      + '<label class="docsViewer__field docsViewer__field--checkbox"><input class="docsViewer__checkboxInput" type="radio" name="catalogue-regenerate-mode" value="full"><span class="docsViewer__fieldLabel">Full reconciliation</span></label>'
      + '</fieldset>'
      + '<div data-regenerate-result aria-live="polite"></div>',
    actions: [
      { role: "modal-primary", label: "Run" },
      { role: "modal-cancel", label: "Close" }
    ],
    focusSelector: '[name="catalogue-regenerate-mode"][value="pending"]',
    onOpen: function (modalApi) {
      api = modalApi;
      api.host.querySelector('[data-role="docs-viewer-management-modal"]').dataset.suppressBusyCursor = "true";
      primary = api.host.querySelector('[data-role="modal-primary"]');
      closeButton = api.host.querySelector('button[data-role="modal-cancel"]');
      content = api.host.querySelector("[data-regenerate-result]");
      choices = Array.from(api.host.querySelectorAll('[name="catalogue-regenerate-mode"]'));
    },
    onSubmit: function () {
      if (phase === "result" || phase === "error") return { confirmed: true };
      if (phase === "ready") run();
      return false;
    }
  }).then(function () { return result; });
}
