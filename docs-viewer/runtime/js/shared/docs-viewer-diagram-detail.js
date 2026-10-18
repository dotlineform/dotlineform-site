const PERSISTENT_DIAGRAM_SELECTOR = 'img[data-docs-viewer-diagram-kind="persistent-svg"]';
const DIAGRAM_FRAME_SELECTOR = ".docsViewer__diagramFrame";
const DETAIL_CONTROL_LABEL = "Open diagram";
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
  return cleanString(first.collection) === cleanString(second.collection)
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

function diagramLabel(surface, occurrence) {
  var label = cleanString(surface.getAttribute("alt")) || cleanString(surface.getAttribute("title"));
  return label || "Diagram " + occurrence;
}

function createDetailControl(documentRef, kind) {
  var control = documentRef.createElement("button");
  control.className = "docsViewer__toolbarIconButton docsViewer__diagramDetailControl";
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
  var frame = documentRef.createElement("span");
  frame.className = "docsViewer__diagramFrame";
  frame.dataset.docsViewerDiagramFrame = kind;

  var viewport = documentRef.createElement("span");
  viewport.className = "docsViewer__diagramViewport";

  surface.before(frame);
  viewport.appendChild(surface);
  frame.appendChild(viewport);
  var control = createDetailControl(documentRef, kind);
  frame.appendChild(control);
  return { control: control, frame: frame, viewport: viewport };
}

/** Own imported SVG targets for one document mount. */
export function createDocsViewerDiagramDetailAdapter(options) {
  var settings = options || {};
  var warn = typeof settings.warn === "function" ? settings.warn : defaultWarning;
  var stateByRoot = new WeakMap();

  function createState(root, context) {
    var doc = context.doc || {};
    var state = {
      documentMountGeneration: positiveInteger(
        context.documentMountGeneration || context.mountGeneration
      ),
      documentTarget: {
          collection: "",
        docId: cleanString(doc.doc_id)
      },
      nextOccurrence: 0,
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

  function projectPresentationTarget(presentation, target) {
    presentation.newTabTarget = target;
    if (typeof presentation.projectNewTabTarget !== "function") return;
    try {
      presentation.projectNewTabTarget(target);
    } catch (error) {
      warn("docs_viewer: diagram detail toolbar target refresh unavailable", error);
    }
  }

  function resolveRecord(root, targetContext) {
    var target = targetContext || {};
    var state = root ? stateByRoot.get(root) : null;
    if (
      !state
      || !state.documentMountGeneration
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

  function registerRecord(state, surface, decoration, target) {
    state.nextOccurrence += 1;
    var occurrence = state.nextOccurrence;
    var record = {
      control: decoration.control,
      handleClick: null,
      id: "diagram-" + (occurrence - 1),
      label: diagramLabel(surface, occurrence),
      occurrence: occurrence,
      presentations: new Set(),
      sourceViewport: decoration.viewport,
      surface: surface,
      target: target
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
      released += 1;
    });
    state.records.clear();
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
      registerRecord(
        state,
        diagram,
        decoration,
        target
      );
      return count + 1;
    }, 0);
    return {
      found: diagrams.length,
      decorated: decorated,
      skipped: diagrams.length - decorated
    };
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
    releaseDocument: releaseDocument
  };
}

export const docsViewerDiagramDetailAdapter = createDocsViewerDiagramDetailAdapter();
