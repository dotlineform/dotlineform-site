import { importNativeDoc } from "./docs-viewer-management-client.js";
import { escapeHtml, openDocsViewerManagementModal } from "./docs-viewer-management-modal-shell.js";

const DOCUMENT_TYPES = {
  ".docx": "Word", ".html": "HTML", ".htm": "HTML",
  ".md": "Markdown", ".markdown": "Markdown", ".txt": "Text"
};
const MAX_DOCUMENT_BYTES = 64 * 1024 * 1024;

/** Own native selection and one pending File; the service owns conversion/persistence. */
export function createDocsViewerImportDocWorkflow(options) {
  async function confirmFile(file, settings) {
    var extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    var kind = DOCUMENT_TYPES[extension];
    if (!kind) throw new Error("Choose a Word, HTML, Markdown or text file.");
    if (!file.size || file.size > MAX_DOCUMENT_BYTES) throw new Error("Choose a nonempty document of at most 64 MiB.");
    options.setMessage("", false);
    options.render();
    try {
      var outcome = await openDocsViewerManagementModal({
        root: options.root,
        restoreFocus: settings.restoreFocus,
        title: "Import doc",
        bodyHtml:
          '<p class="docsViewer__modalNote">' + escapeHtml(file.name) + '</p>' +
          '<p class="docsViewer__modalNote muted small">For separate local images or attachments, use Import docs with the complete folder.</p>',
        actions: [{ role: "modal-cancel", label: "Cancel" }, { role: "modal-primary", label: "Import" }],
        onSubmit: async function () {
          options.setBusy(true);
          options.render();
          try {
            var result = await importNativeDoc(file, settings.destination, kind === "HTML", options.clientOptions());
            return { confirmed: true, result: result };
          } catch (error) {
            options.setBusy(false);
            options.render();
            throw error;
          }
        }
      });
      file = null;
      if (outcome.confirmed) {
        try {
          await options.onCommittedResult(outcome.result);
          await options.onComplete(outcome.result);
          var warnings = outcome.result.warnings;
          if (warnings.length) options.setMessage("Document imported. " + warnings.join(" "), false);
        } catch (error) {
          options.setMessage("Document imported, but display failed: " + error.message, true);
        }
      }
    } finally {
      file = null;
      options.setBusy(false);
      options.render();
    }
  }

  /** Invoke synchronously from the action click, preserving browser user activation. */
  function open(settings) {
    var input = options.root.ownerDocument.createElement("input");
    input.type = "file";
    input.accept = Object.keys(DOCUMENT_TYPES).join(",");
    input.multiple = false;
    input.hidden = true;
    input.addEventListener("cancel", function () { input.remove(); }, { once: true });
    input.addEventListener("change", function () {
      var file = input.files[0];
      input.remove();
      if (!file) return;
      confirmFile(file, settings).catch(function (error) {
        options.setMessage(error.message || "Import doc failed.", true);
      });
    }, { once: true });
    options.root.appendChild(input);
    input.click();
  }

  return { open: open };
}
