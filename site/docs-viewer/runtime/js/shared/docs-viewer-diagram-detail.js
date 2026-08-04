const PERSISTENT_DIAGRAM_SELECTOR = [
  'img[data-docs-viewer-diagram-kind="persistent-svg"]',
  'img[data-docs-viewer-diagram-kind="themed-mermaid"]'
].join(", ");
const INLINE_DIAGRAM_SELECTOR = '.docsViewer__diagram[data-docs-viewer-diagram-kind="inline-mermaid"]';
const DIAGRAM_FRAME_SELECTOR = ".docsViewer__diagramFrame";
const DETAIL_CONTROL_LABEL = "Open diagram";
const SVG_NAMESPACE = "http://www.w3.org/2000/svg";

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function positiveInteger(value) {
  var number = Number(value);
  return Number.isInteger(number) && number > 0 ? number : 0;
}

function sameDocumentTarget(left, right) {
  var first = left || {};
  var second = right || {};
  return cleanString(first.scope) === cleanString(second.scope)
    && cleanString(first.subScope) === cleanString(second.subScope)
    && cleanString(first.docId) === cleanString(second.docId);
}

function immutableTargetContext(state, record) {
  return Object.freeze({
    documentTarget: Object.freeze(Object.assign({}, state.documentTarget)),
    documentMountGeneration: state.documentMountGeneration,
    kind: "diagram",
    adapterTargetId: record.id,
    occurrence: record.occurrence
  });
}

function defaultWarning(message, error) {
  if (typeof console !== "undefined" && typeof console.warn === "function") {
    console.warn(message, error);
  }
}

function persistentDiagramTarget(diagram) {
  return cleanString(diagram && diagram.getAttribute ? diagram.getAttribute("src") : "");
}

function directInlineSvg(host) {
  if (!host || !host.matches || !host.matches(INLINE_DIAGRAM_SELECTOR)) return null;
  if (host.children.length !== 1) return null;
  var svg = host.firstElementChild;
  return svg && svg.namespaceURI === SVG_NAMESPACE && svg.localName === "svg" ? svg : null;
}

function diagramLabel(surface, occurrence, kind) {
  var label = "";
  if (kind === "inline-mermaid") {
    var svg = directInlineSvg(surface);
    var title = svg && svg.querySelector ? svg.querySelector("title") : null;
    label = cleanString(title ? title.textContent : "");
  } else if (surface && typeof surface.getAttribute === "function") {
    label = cleanString(surface.getAttribute("alt")) || cleanString(surface.getAttribute("title"));
  }
  return label || "Diagram " + occurrence;
}

function createDetailControl(documentRef, kind) {
  var control = documentRef.createElement("button");
  control.className = "docsViewer__diagramDetailControl";
  control.type = "button";
  control.dataset.docsViewerDiagramDetailKind = kind;
  control.setAttribute("aria-label", DETAIL_CONTROL_LABEL);
  control.setAttribute("title", DETAIL_CONTROL_LABEL);
  control.innerHTML = [
    '<svg class="docsViewer__diagramDetailIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
    '  <path d="M14 5h5v5M19 5l-8 8M19 13v6H5V5h6"></path>',
    "</svg>"
  ].join("");
  return control;
}

function decorateDiagramSurface(documentRef, surface, kind) {
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
  var control = createDetailControl(documentRef, kind);
  frame.appendChild(control);
  return { control: control, frame: frame, viewport: viewport };
}

function standaloneSvgMarkup(windowRef, svg) {
  if (!windowRef || typeof windowRef.XMLSerializer !== "function") {
    throw new Error("Inline diagram detail requires XML serialization support.");
  }
  if (!cleanString(svg.getAttribute("viewBox"))) {
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

/** Own exact persistent and managed-inline diagram targets for one document mount. */
export function createDocsViewerDiagramDetailAdapter(options) {
  var settings = options || {};
  var createObjectUrl = typeof settings.createObjectUrl === "function"
    ? settings.createObjectUrl
    : defaultCreateObjectUrl;
  var revokeObjectUrl = typeof settings.revokeObjectUrl === "function"
    ? settings.revokeObjectUrl
    : defaultRevokeObjectUrl;
  var warn = typeof settings.warn === "function" ? settings.warn : defaultWarning;
  var stateByRoot = new WeakMap();

  function createState(root, context) {
    var doc = context.doc || {};
    var state = {
      documentMountGeneration: positiveInteger(
        context.documentMountGeneration || context.mountGeneration
      ),
      documentTarget: {
        scope: cleanString(context.viewerScope),
        subScope: "",
        docId: cleanString(doc.doc_id)
      },
      inlineByHost: new Map(),
      nextOccurrence: 0,
      persistentByDiagram: new Map(),
      presentations: new Set(),
      records: new Map(),
      requestContentDetail: typeof context.requestContentDetail === "function"
        ? context.requestContentDetail
        : function () { return false; },
      root: root
    };
    stateByRoot.set(root, state);
    return state;
  }

  function stateFor(root, context) {
    return stateByRoot.get(root) || createState(root, context || {});
  }

  function revokeResource(record) {
    if (!record || record.diagramKind !== "inline-mermaid" || !record.target) return;
    try {
      revokeObjectUrl(record.target, { window: record.window });
    } catch (error) {
      warn("docs_viewer: inline diagram detail resource cleanup unavailable", error);
    }
  }

  function projectPresentationTarget(presentation, target) {
    presentation.newTabTarget = target;
    if (typeof presentation.projectNewTabTarget !== "function") return;
    try {
      presentation.projectNewTabTarget(target);
    } catch (error) {
      warn("docs_viewer: diagram detail toolbar target refresh unavailable", error);
    }
  }

  function updateRecordTarget(record, target) {
    record.target = target;
    record.presentations.forEach(function (presentation) {
      projectPresentationTarget(presentation, target);
    });
  }

  function resolveRecord(root, targetContext) {
    var target = targetContext || {};
    var state = root ? stateByRoot.get(root) : null;
    if (
      !state
      || !state.documentMountGeneration
      || !state.documentTarget.scope
      || !state.documentTarget.docId
      || cleanString(target.kind) !== "diagram"
      || positiveInteger(target.documentMountGeneration) !== state.documentMountGeneration
      || !sameDocumentTarget(target.documentTarget, state.documentTarget)
    ) {
      return null;
    }
    var record = state.records.get(cleanString(target.adapterTargetId)) || null;
    return record && root.contains(record.surface) ? { record: record, state: state } : null;
  }

  function registerRecord(state, surface, decoration, target, kind, windowRef) {
    state.nextOccurrence += 1;
    var occurrence = state.nextOccurrence;
    var record = {
      control: decoration.control,
      diagramKind: kind,
      handleClick: null,
      id: "diagram-" + (occurrence - 1),
      label: diagramLabel(surface, occurrence, kind),
      occurrence: occurrence,
      presentations: new Set(),
      sourceViewport: decoration.viewport,
      surface: surface,
      target: target,
      window: windowRef
    };
    record.handleClick = function () {
      var targetContext = immutableTargetContext(state, record);
      if (!resolveRecord(state.root, targetContext)) return;
      state.requestContentDetail(targetContext);
    };
    record.control.addEventListener("click", record.handleClick);
    state.records.set(record.id, record);
    return record;
  }

  function releaseState(root, state) {
    if (!state) return { released: 0 };
    Array.from(state.presentations).forEach(function (presentation) {
      presentation.release();
    });
    var released = 0;
    state.records.forEach(function (record) {
      record.control.removeEventListener("click", record.handleClick);
      record.control.remove();
      if (record.diagramKind === "inline-mermaid") {
        released += 1;
        revokeResource(record);
      }
    });
    state.records.clear();
    state.inlineByHost.clear();
    state.persistentByDiagram.clear();
    stateByRoot.delete(root);
    return { released: released };
  }

  function releaseDocument(releaseContext) {
    var context = releaseContext || {};
    var root = context.content;
    if (!root || typeof root !== "object") return { released: 0 };
    return releaseState(root, stateByRoot.get(root));
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

    var state = stateFor(root, context);
    var diagrams = Array.from(root.querySelectorAll(PERSISTENT_DIAGRAM_SELECTOR));
    var decorated = diagrams.reduce(function (count, diagram) {
      var target = persistentDiagramTarget(diagram);
      var kind = cleanString(diagram.dataset ? diagram.dataset.docsViewerDiagramKind : "");
      if (!target) return count;
      var decoration = decorateDiagramSurface(documentRef, diagram, kind);
      if (!decoration) return count;
      var record = registerRecord(
        state,
        diagram,
        decoration,
        target,
        kind,
        context.window || documentRef.defaultView
      );
      state.persistentByDiagram.set(diagram, record);
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
    var state = stateByRoot.get(root);
    var current = state ? state.persistentByDiagram.get(diagram) : null;
    if (!current) return { refreshed: false, reason: "not-registered" };
    var target = persistentDiagramTarget(diagram);
    if (!target) return { refreshed: false, reason: "missing-target" };
    updateRecordTarget(current, target);
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

    var state = stateFor(root, context);
    var expectedGeneration = positiveInteger(context.mountGeneration || context.documentMountGeneration);
    var expectedTarget = {
      scope: cleanString(context.viewerScope),
      subScope: "",
      docId: cleanString(context.doc && context.doc.doc_id)
    };
    if (
      expectedGeneration
      && state.documentMountGeneration
      && (
        expectedGeneration !== state.documentMountGeneration
        || !sameDocumentTarget(expectedTarget, state.documentTarget)
      )
    ) {
      return { decorated: false, reason: "stale-document" };
    }

    var documentRef = context.document || root.ownerDocument;
    var windowRef = context.window || (documentRef ? documentRef.defaultView : null);
    var target = "";
    try {
      var markup = standaloneSvgMarkup(windowRef, svg);
      target = cleanString(createObjectUrl(markup, {
        document: documentRef,
        host: host,
        svg: svg,
        window: windowRef
      }));
      if (!target) throw new Error("Inline diagram detail did not create a browser resource.");
      var decoration = decorateDiagramSurface(documentRef, host, "inline-mermaid");
      if (!decoration) {
        revokeResource({ diagramKind: "inline-mermaid", target: target, window: windowRef });
        return { decorated: false, reason: "already-decorated" };
      }
      var record = registerRecord(
        state,
        host,
        decoration,
        target,
        "inline-mermaid",
        windowRef
      );
      state.inlineByHost.set(host, record);
      return { decorated: true, reason: "", target: target };
    } catch (error) {
      if (target) revokeResource({ diagramKind: "inline-mermaid", target: target, window: windowRef });
      warn("docs_viewer: inline diagram detail target unavailable", error);
      return { decorated: false, reason: "target-unavailable" };
    }
  }

  function refreshInlineDiagram(refreshContext) {
    var context = refreshContext || {};
    var root = context.content;
    var host = context.host;
    if (!root || !host) return { refreshed: false, reason: "missing-context" };
    var state = stateByRoot.get(root);
    var current = state ? state.inlineByHost.get(host) : null;
    if (!current) return { refreshed: false, reason: "not-registered" };

    var svg = directInlineSvg(host);
    if (!svg) return { refreshed: false, reason: "unsupported-host" };
    var documentRef = context.document || root.ownerDocument;
    var windowRef = context.window || (documentRef ? documentRef.defaultView : null);
    var target = "";
    try {
      var markup = standaloneSvgMarkup(windowRef, svg);
      target = cleanString(createObjectUrl(markup, {
        document: documentRef,
        host: host,
        svg: svg,
        window: windowRef
      }));
      if (!target) throw new Error("Inline diagram detail did not create a browser resource.");
      var previousTarget = current.target;
      updateRecordTarget(current, target);
      current.window = windowRef;
      revokeResource({
        diagramKind: "inline-mermaid",
        target: previousTarget,
        window: windowRef
      });
      return { refreshed: true, reason: "", target: target };
    } catch (error) {
      if (target) revokeResource({ diagramKind: "inline-mermaid", target: target, window: windowRef });
      warn("docs_viewer: inline diagram detail refresh unavailable", error);
      return { refreshed: false, reason: "target-unavailable" };
    }
  }

  function mountPresentation(presentationContext) {
    var context = presentationContext || {};
    var root = context.content;
    var resolved = resolveRecord(root, context.targetContext);
    if (!resolved) throw new Error("Diagram detail target is stale or unavailable.");

    var record = resolved.record;
    var state = resolved.state;
    if (record.presentations.size || record.surface.parentElement !== record.sourceViewport) {
      throw new Error("Diagram detail target is already active or unavailable.");
    }
    var documentRef = context.document || root.ownerDocument;
    var section = documentRef.createElement("section");
    section.className = "docsViewer__contentDetail docsViewer__contentDetail--diagram";
    section.setAttribute("data-docs-content-detail-view", "diagram");

    var viewport = documentRef.createElement("div");
    viewport.className = "docsViewer__diagramDetailViewport";
    viewport.tabIndex = 0;
    viewport.setAttribute("role", "region");
    viewport.setAttribute("aria-label", record.label);
    viewport.appendChild(record.surface);
    section.appendChild(viewport);

    var released = false;
    var presentation = {
      activate: function (activationContext) {
        presentation.projectNewTabTarget = activationContext
          && typeof activationContext.projectNewTabTarget === "function"
          ? activationContext.projectNewTabTarget
          : null;
        projectPresentationTarget(presentation, record.target);
      },
      focusTarget: viewport,
      invocationControl: record.control,
      label: record.label,
      newTabTarget: record.target,
      projectNewTabTarget: null,
      root: section,
      release: function () {
        if (released) return;
        released = true;
        presentation.projectNewTabTarget = null;
        if (record.sourceViewport) record.sourceViewport.appendChild(record.surface);
        section.remove();
        record.presentations.delete(presentation);
        state.presentations.delete(presentation);
      }
    };
    record.presentations.add(presentation);
    state.presentations.add(presentation);
    return presentation;
  }

  return {
    mountDocument: mountDocument,
    mountPresentation: mountPresentation,
    refreshInlineDiagram: refreshInlineDiagram,
    refreshPersistentDiagram: refreshPersistentDiagram,
    registerInlineDiagram: registerInlineDiagram,
    releaseDocument: releaseDocument
  };
}

export const docsViewerDiagramDetailAdapter = createDocsViewerDiagramDetailAdapter();
