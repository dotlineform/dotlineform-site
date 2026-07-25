const PERSISTENT_DIAGRAM_SELECTOR = [
  'img[data-docs-viewer-diagram-kind="persistent-svg"]',
  'img[data-docs-viewer-diagram-kind="themed-mermaid"]'
].join(", ");
const INLINE_DIAGRAM_SELECTOR = '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]';
const DIAGRAM_FRAME_SELECTOR = ".docsViewer__diagramFrame";
const DETAIL_CONTROL_LABEL = "Open diagram in new tab";
const SVG_NAMESPACE = "http://www.w3.org/2000/svg";

function defaultWarning(message, error) {
  if (typeof console !== "undefined" && typeof console.warn === "function") {
    console.warn(message, error);
  }
}

function persistentDiagramTarget(diagram) {
  return String(diagram && diagram.getAttribute ? diagram.getAttribute("src") || "" : "").trim();
}

function createDetailControl(documentRef, target, kind) {
  var control = documentRef.createElement("a");
  control.className = "docsViewer__diagramDetailControl";
  control.dataset.docsViewerDiagramDetailKind = kind;
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

function decorateDiagramSurface(documentRef, surface, target, kind) {
  if (surface.closest(DIAGRAM_FRAME_SELECTOR)) return null;
  var elementName = kind === "inline-mermaid" ? "div" : "span";
  var frame = documentRef.createElement(elementName);
  frame.className = "docsViewer__diagramFrame";
  frame.dataset.docsViewerDiagramFrame = kind;

  var viewport = documentRef.createElement(elementName);
  viewport.className = "docsViewer__diagramViewport";

  surface.before(frame);
  viewport.appendChild(surface);
  frame.appendChild(viewport);
  var control = createDetailControl(documentRef, target, kind);
  frame.appendChild(control);
  return { control: control, frame: frame, viewport: viewport };
}

function decoratePersistentDiagram(documentRef, diagram) {
  var target = persistentDiagramTarget(diagram);
  var kind = String(diagram.dataset ? diagram.dataset.docsViewerDiagramKind || "" : "").trim();
  return target ? decorateDiagramSurface(documentRef, diagram, target, kind) : null;
}

function directInlineSvg(host) {
  if (!host || !host.matches || !host.matches(INLINE_DIAGRAM_SELECTOR)) return null;
  if (host.children.length !== 1) return null;
  var svg = host.firstElementChild;
  return svg && svg.namespaceURI === SVG_NAMESPACE && svg.localName === "svg" ? svg : null;
}

function standaloneSvgMarkup(windowRef, svg) {
  if (!windowRef || typeof windowRef.XMLSerializer !== "function") {
    throw new Error("Inline diagram detail requires XML serialization support.");
  }
  if (!String(svg.getAttribute("viewBox") || "").trim()) {
    throw new Error("Inline diagram detail requires a responsive SVG viewBox.");
  }
  var title = svg.querySelector("title");
  var description = svg.querySelector("desc");
  if (!title || !title.textContent.trim() || !description || !description.textContent.trim()) {
    throw new Error("Inline diagram detail requires SVG title and description metadata.");
  }

  var standalone = svg.cloneNode(true);
  if (!standalone.getAttribute("xmlns")) standalone.setAttribute("xmlns", SVG_NAMESPACE);
  var serialized = new windowRef.XMLSerializer().serializeToString(standalone);
  return '<?xml version="1.0" encoding="UTF-8"?>\n' + serialized;
}

function defaultCreateObjectUrl(markup, context) {
  var windowRef = context.window;
  if (
    !windowRef
    || typeof windowRef.Blob !== "function"
    || !windowRef.URL
    || typeof windowRef.URL.createObjectURL !== "function"
  ) {
    throw new Error("Inline diagram detail requires Blob URL support.");
  }
  return windowRef.URL.createObjectURL(new windowRef.Blob([markup], { type: "image/svg+xml" }));
}

function defaultRevokeObjectUrl(target, context) {
  var windowRef = context.window;
  if (windowRef && windowRef.URL && typeof windowRef.URL.revokeObjectURL === "function") {
    windowRef.URL.revokeObjectURL(target);
  }
}

export function createDocsViewerDiagramDetailAdapter(options) {
  var settings = options || {};
  var createObjectUrl = typeof settings.createObjectUrl === "function"
    ? settings.createObjectUrl
    : defaultCreateObjectUrl;
  var revokeObjectUrl = typeof settings.revokeObjectUrl === "function"
    ? settings.revokeObjectUrl
    : defaultRevokeObjectUrl;
  var warn = typeof settings.warn === "function" ? settings.warn : defaultWarning;
  var resourcesByRoot = new WeakMap();
  var persistentByRoot = new WeakMap();

  function trackResource(root, host, control, target, windowRef) {
    var resources = resourcesByRoot.get(root) || new Map();
    resources.set(host, {
      control: control,
      host: host,
      target: target,
      window: windowRef
    });
    resourcesByRoot.set(root, resources);
  }

  function revokeResource(resource) {
    try {
      revokeObjectUrl(resource.target, { window: resource.window });
    } catch (error) {
      warn("docs_viewer: inline diagram detail resource cleanup unavailable", error);
    }
  }

  function trackPersistent(root, diagram, control) {
    var records = persistentByRoot.get(root) || new Map();
    records.set(diagram, {
      control: control,
      diagram: diagram
    });
    persistentByRoot.set(root, records);
  }

  function releaseDocument(releaseContext) {
    var context = releaseContext || {};
    var root = context.content;
    if (!root || typeof root !== "object") return { released: 0 };
    var resources = resourcesByRoot.get(root) || new Map();
    resourcesByRoot.delete(root);
    persistentByRoot.delete(root);
    resources.forEach(revokeResource);
    return { released: resources.size };
  }

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
      var decoration = decoratePersistentDiagram(documentRef, diagram);
      if (!decoration) return count;
      trackPersistent(root, diagram, decoration.control);
      return count + 1;
    }, 0);
    return {
      found: diagrams.length,
      decorated: decorated,
      skipped: diagrams.length - decorated
    };
  }

  function refreshPersistentDiagram(refreshContext) {
    var context = refreshContext || {};
    var root = context.content;
    var diagram = context.diagram;
    if (!root || !diagram) return { refreshed: false, reason: "missing-context" };
    var records = persistentByRoot.get(root);
    var current = records ? records.get(diagram) : null;
    if (!current || !current.control) {
      return { refreshed: false, reason: "not-registered" };
    }
    var target = persistentDiagramTarget(diagram);
    if (!target) return { refreshed: false, reason: "missing-target" };
    current.control.setAttribute("href", target);
    return { refreshed: true, reason: "", target: target };
  }

  function registerInlineDiagram(registrationContext) {
    var context = registrationContext || {};
    var root = context.content;
    var host = context.host;
    if (!root || typeof root.contains !== "function" || !host || !root.contains(host)) {
      return { decorated: false, reason: "outside-document" };
    }
    if (host.closest(DIAGRAM_FRAME_SELECTOR)) {
      return { decorated: false, reason: "already-decorated" };
    }
    var svg = directInlineSvg(host);
    if (!svg) return { decorated: false, reason: "unsupported-host" };

    var documentRef = context.document || root.ownerDocument;
    var windowRef = context.window || (documentRef ? documentRef.defaultView : null);
    var target = "";
    try {
      var markup = standaloneSvgMarkup(windowRef, svg);
      target = String(createObjectUrl(markup, {
        document: documentRef,
        host: host,
        svg: svg,
        window: windowRef
      }) || "").trim();
      if (!target) throw new Error("Inline diagram detail did not create a browser resource.");
      var decoration = decorateDiagramSurface(documentRef, host, target, "inline-mermaid");
      if (!decoration) {
        revokeResource({ target: target, window: windowRef });
        return { decorated: false, reason: "already-decorated" };
      }
      trackResource(root, host, decoration.control, target, windowRef);
      return { decorated: true, reason: "", target: target };
    } catch (error) {
      if (target) revokeResource({ target: target, window: windowRef });
      warn("docs_viewer: inline diagram detail target unavailable", error);
      return { decorated: false, reason: "target-unavailable" };
    }
  }

  function refreshInlineDiagram(refreshContext) {
    var context = refreshContext || {};
    var root = context.content;
    var host = context.host;
    if (!root || !host) return { refreshed: false, reason: "missing-context" };
    var resources = resourcesByRoot.get(root);
    var current = resources ? resources.get(host) : null;
    if (!current || !current.control) {
      return { refreshed: false, reason: "not-registered" };
    }

    var svg = directInlineSvg(host);
    if (!svg) return { refreshed: false, reason: "unsupported-host" };
    var documentRef = context.document || root.ownerDocument;
    var windowRef = context.window || (documentRef ? documentRef.defaultView : null);
    var target = "";
    try {
      var markup = standaloneSvgMarkup(windowRef, svg);
      target = String(createObjectUrl(markup, {
        document: documentRef,
        host: host,
        svg: svg,
        window: windowRef
      }) || "").trim();
      if (!target) throw new Error("Inline diagram detail did not create a browser resource.");
      current.control.setAttribute("href", target);
      trackResource(root, host, current.control, target, windowRef);
      revokeResource(current);
      return { refreshed: true, reason: "", target: target };
    } catch (error) {
      if (target) revokeResource({ target: target, window: windowRef });
      warn("docs_viewer: inline diagram detail refresh unavailable", error);
      return { refreshed: false, reason: "target-unavailable" };
    }
  }

  return {
    mountDocument: mountDocument,
    refreshInlineDiagram: refreshInlineDiagram,
    refreshPersistentDiagram: refreshPersistentDiagram,
    registerInlineDiagram: registerInlineDiagram,
    releaseDocument: releaseDocument
  };
}

export const docsViewerDiagramDetailAdapter = createDocsViewerDiagramDetailAdapter();
