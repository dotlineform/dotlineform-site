import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";

/**
 * @typedef {Object} RelatedLinksCapture
 * @property {{collection: string, doc_id: string}} target Exact loaded document identity.
 * @property {string} title Captured payload title, used by the panel shell.
 * @property {string} summary Optional plain-text payload summary.
 * @property {HTMLElement} [list] Detached copy of the generated list, with resolved routes and icons.
 */

/**
 * Add pins only to generated, non-empty lists mounted in a reader.
 * Each activation copies the loaded document context; exports/Review keep their
 * static content, and the capture survives disposal of this document mount.
 * @param {Object} options Loaded content, payload, exact target and capture callback.
 * @param {HTMLElement} options.content Mounted rendered document body.
 * @param {Object} options.payload Already loaded by-ID document payload.
 * @param {{collection?: string, doc_id: string}} options.documentTarget Exact mount owner.
 * @param {function(RelatedLinksCapture): void} options.onPin Panel-owned capture action.
 * @param {function(): boolean} [options.isCurrentDocument] Reject stale collection detail mounts.
 */
export function mountDocsViewerRelatedLinks(options) {
  var settings = options || {};
  var content = settings.content;
  var payload = settings.payload || {};
  var target = settings.documentTarget || {};
  if (!content || typeof settings.onPin !== "function") return;
  if (!target.doc_id || target.doc_id !== payload.doc_id) {
    throw new Error("Related-links pin requires the exact loaded document target.");
  }
  content.querySelectorAll("section[data-docs-related-links]").forEach(function (section) {
    var list = section.querySelector(":scope > ul");
    if (!list || !list.querySelector("a[data-docs-related-link]") || section.querySelector("[data-docs-related-pin]")) return;
    var documentRef = content.ownerDocument;
    var heading = section.querySelector(":scope > h2, :scope > h3");
    var header = documentRef.createElement("div");
    header.className = "docsViewer__relatedLinksHeader";
    var button = documentRef.createElement("button");
    button.type = "button";
    button.className = "docsViewer__toolbarIconButton";
    button.setAttribute("data-docs-related-pin", "true");
    button.setAttribute("aria-label", "Pin related links");
    button.title = "Pin related links";
    button.appendChild(createDocsViewerToolbarIcon(documentRef, "docsViewer__icon--pin"));
    button.addEventListener("click", function () {
      if (!section.isConnected || (settings.isCurrentDocument && !settings.isCurrentDocument())) return;
      settings.onPin(Object.freeze({
        target: Object.freeze({ collection: target.collection || "", doc_id: target.doc_id }),
        title: String(payload.title || ""),
        summary: String(payload.summary || "").replace(/\r\n?/g, "\n").trim(),
        list: list.cloneNode(true)
      }));
    });
    if (heading) header.appendChild(heading);
    header.appendChild(button);
    section.insertBefore(header, list);
  });
}

/**
 * Render only the captured optional summary and generated list, with no reads or
 * main-document subscription. The shell owns the title and Close control.
 * @returns {Object} Synchronous panel lifecycle; unmount releases its DOM.
 */
export function createDocsViewerRelatedLinksView() {
  function render(context) {
    var mount = context.mount;
    var capture = context.capture;
    mount.replaceChildren();
    if (!capture) return;
    var body = mount.ownerDocument.createElement("div");
    body.className = "docsViewer__relatedLinksBody";
    if (capture.summary) {
      capture.summary.split(/\n[ \t]*\n+/).forEach(function (paragraph) {
        var summary = mount.ownerDocument.createElement("p");
        paragraph.split("\n").forEach(function (line, index) {
          if (index) summary.appendChild(mount.ownerDocument.createElement("br"));
          summary.appendChild(mount.ownerDocument.createTextNode(line));
        });
        body.appendChild(summary);
      });
    }
    if (capture.list) body.appendChild(capture.list.cloneNode(true));
    if (body.childNodes.length) mount.appendChild(body);
  }
  return {
    mount: render,
    unmount: function (context) { context.mount.replaceChildren(); },
    dispose: function (context) { context.mount.replaceChildren(); }
  };
}
