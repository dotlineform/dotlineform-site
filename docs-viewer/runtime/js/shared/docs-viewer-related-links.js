import { createDocsViewerToolbarIcon } from "./docs-viewer-toolbar-icon.js";

/**
 * @typedef {Object} RelatedLinksCapture
 * @property {{collection: string, doc_id: string}} target Exact loaded document identity.
 * @property {string} title Captured payload title, used by the panel shell.
 * @property {string} [summaryHtml] Optional builder-rendered Summary paragraphs.
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
    if (!list || !list.querySelector("[data-docs-related-link]") || section.querySelector("[data-docs-related-pin]")) return;
    // Capture the generated controls before Media View adds per-mount feedback and busy state.
    var galleryList = list.querySelector("[data-docs-media-open]") ? list.cloneNode(true) : null;
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
        summaryHtml: payload.summary_html,
        list: galleryList || list.cloneNode(true)
      }));
    });
    if (heading) header.appendChild(heading);
    header.appendChild(button);
    section.insertBefore(header, list);
  });
}

/** Render the captured summary and list, binding gallery controls for this panel mount. */
export function createDocsViewerRelatedLinksView() {
  var releaseMediaLinks;
  function unmount(context) {
    if (releaseMediaLinks) releaseMediaLinks();
    releaseMediaLinks = null;
    context.mount.replaceChildren();
  }

  function render(context) {
    var mount = context.mount;
    var capture = context.capture;
    unmount(context);
    if (!capture) return;
    var body = mount.ownerDocument.createElement("div");
    body.className = "docsViewer__relatedLinksBody";
    if (capture.summaryHtml) body.innerHTML = capture.summaryHtml;
    var list = capture.list && capture.list.cloneNode(true);
    if (list) body.appendChild(list);
    if (body.childNodes.length) mount.appendChild(body);
    if (list?.querySelector("[data-docs-media-open]")) releaseMediaLinks = context.mountMediaLinks?.(list);
  }
  return {
    mount: render,
    unmount: unmount,
    dispose: unmount
  };
}
