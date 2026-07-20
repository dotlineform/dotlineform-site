const PERSISTENT_DIAGRAM_SELECTOR = 'img[data-docs-viewer-diagram-kind="persistent-svg"]';
const DIAGRAM_FRAME_SELECTOR = ".docsViewer__diagramFrame";
const DETAIL_CONTROL_LABEL = "Open diagram in new tab";

function persistentDiagramTarget(diagram) {
  return String(diagram && diagram.getAttribute ? diagram.getAttribute("src") || "" : "").trim();
}

function createDetailControl(documentRef, target) {
  var control = documentRef.createElement("a");
  control.className = "docsViewer__diagramDetailControl";
  control.setAttribute("href", target);
  control.setAttribute("target", "_blank");
  control.setAttribute("rel", "noopener");
  control.setAttribute("aria-label", DETAIL_CONTROL_LABEL);
  control.setAttribute("title", DETAIL_CONTROL_LABEL);
  control.innerHTML = [
    '<svg class="docsViewer__diagramDetailIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
    '  <path d="M14 5h5v5M19 5l-8 8M19 13v6H5V5h6"></path>',
    "</svg>"
  ].join("");
  return control;
}

function decoratePersistentDiagram(documentRef, diagram) {
  if (diagram.closest(DIAGRAM_FRAME_SELECTOR)) return false;
  var target = persistentDiagramTarget(diagram);
  if (!target) return false;

  var frame = documentRef.createElement("span");
  frame.className = "docsViewer__diagramFrame";
  frame.dataset.docsViewerDiagramFrame = "persistent-svg";

  var viewport = documentRef.createElement("span");
  viewport.className = "docsViewer__diagramViewport";

  diagram.before(frame);
  viewport.appendChild(diagram);
  frame.appendChild(viewport);
  frame.appendChild(createDetailControl(documentRef, target));
  return true;
}

export function createDocsViewerDiagramDetailAdapter() {
  function mountDocument(mountContext) {
    var context = mountContext || {};
    var root = context.content;
    if (!root || typeof root.querySelectorAll !== "function") {
      return { found: 0, decorated: 0, skipped: 0 };
    }

    var documentRef = context.document || root.ownerDocument;
    if (!documentRef || typeof documentRef.createElement !== "function") {
      return { found: 0, decorated: 0, skipped: 0 };
    }

    var diagrams = Array.from(root.querySelectorAll(PERSISTENT_DIAGRAM_SELECTOR));
    var decorated = diagrams.reduce(function (count, diagram) {
      return count + (decoratePersistentDiagram(documentRef, diagram) ? 1 : 0);
    }, 0);
    return {
      found: diagrams.length,
      decorated: decorated,
      skipped: diagrams.length - decorated
    };
  }

  return {
    mountDocument: mountDocument
  };
}

export const docsViewerDiagramDetailAdapter = createDocsViewerDiagramDetailAdapter();
