const IMAGE_DETAIL_DIRECTIVE = "dotlineform:image-detail";
const IMAGE_FRAME_SELECTOR = ".docsViewer__imageFrame";

function followingImage(marker) {
  var next = marker.nextSibling;
  while (next && next.nodeType === 3 && !next.textContent.trim()) next = next.nextSibling;
  if (!next || next.nodeType !== 1) return null;
  if (next.tagName === "IMG") return next;
  if (next.tagName === "P" && next.children.length === 1 && !next.textContent.trim()) {
    return next.firstElementChild.tagName === "IMG" ? next.firstElementChild : null;
  }
  if (next.matches("figure.docsViewerFigure")) return next.querySelector(":scope > img");
  return null;
}

function directiveImages(root, documentRef) {
  var images = new Set();
  var comments = documentRef.createTreeWalker(root, 128 /* SHOW_COMMENT */);
  for (var marker = comments.nextNode(); marker; marker = comments.nextNode()) {
    if (marker.data.trim() !== IMAGE_DETAIL_DIRECTIVE
      || marker.parentElement.closest("pre, code, script, style, textarea, svg")) continue;
    var image = followingImage(marker);
    if (image) images.add(image);
  }
  return images;
}

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
    kind: "image",
    adapterTargetId: record.id,
    occurrence: record.occurrence
  });
}

function defaultWarning(message, error) {
  if (typeof console !== "undefined" && typeof console.warn === "function") {
    console.warn(message, error);
  }
}

function imageTarget(image) {
  return cleanString(image.currentSrc || image.getAttribute("src"));
}

function imageLabel(surface, occurrence) {
  var label = cleanString(surface.getAttribute("alt")) || cleanString(surface.getAttribute("title"));
  return label || "Image " + occurrence;
}

function createDetailControl(documentRef) {
  var control = documentRef.createElement("button");
  control.className = "docsViewer__toolbarIconButton docsViewer__imageDetailControl";
  control.type = "button";
  control.setAttribute("aria-label", "Open image");
  control.setAttribute("title", "Open image");
  control.innerHTML = [
    '<svg class="docsViewer__contentDetailIcon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">',
    '  <path d="M14 5h5v5M19 5l-8 8M19 13v6H5V5h6"></path>',
    "</svg>"
  ].join("");
  return control;
}

function decorateImageSurface(documentRef, surface) {
  if (surface.closest(IMAGE_FRAME_SELECTOR)) return null;
  var frame = documentRef.createElement("span");
  frame.className = "docsViewer__imageFrame";

  var viewport = documentRef.createElement("span");
  viewport.className = "docsViewer__imageViewport";

  surface.before(frame);
  viewport.appendChild(surface);
  var control = createDetailControl(documentRef);
  frame.append(control, viewport);
  return { control: control, frame: frame, viewport: viewport };
}

/** Own directive-selected raster and SVG images for one document mount. */
export function createDocsViewerImageDetailAdapter(options) {
  var settings = options || {};
  var warn = typeof settings.warn === "function" ? settings.warn : defaultWarning;
  var stateByRoot = new WeakMap();

  function createState(root, context) {
    var state = {
      documentMountGeneration: context.documentMountGeneration,
      documentTarget: {
        collection: context.documentTarget.collection,
        docId: context.documentTarget.doc_id
      },
      nextOccurrence: 0,
      presentations: new Set(),
      records: new Map(),
      requestContentDetail: context.requestContentDetail,
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
      warn("docs_viewer: image detail toolbar target refresh unavailable", error);
    }
  }

  function resolveRecord(root, targetContext) {
    var target = targetContext || {};
    var state = root ? stateByRoot.get(root) : null;
    if (
      !state
      || !state.documentMountGeneration
      || !state.documentTarget.docId
      || cleanString(target.kind) !== "image"
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
      id: "image-" + (occurrence - 1),
      label: imageLabel(surface, occurrence),
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
    if (!root) {
      return { found: 0, decorated: 0, skipped: 0 };
    }

    var documentRef = context.document || root.ownerDocument;
    if (!documentRef || typeof documentRef.createElement !== "function") {
      return { found: 0, decorated: 0, skipped: 0 };
    }

    var state = stateFor(root, context);
    var images = Array.from(directiveImages(root, documentRef));
    var decorated = images.reduce(function (count, image) {
      var target = imageTarget(image);
      if (!target) return count;
      var decoration = decorateImageSurface(documentRef, image);
      if (!decoration) return count;
      registerRecord(state, image, decoration, target);
      return count + 1;
    }, 0);
    return {
      found: images.length,
      decorated: decorated,
      skipped: images.length - decorated
    };
  }

  function mountPresentation(presentationContext) {
    var context = presentationContext || {};
    var root = context.content;
    var resolved = resolveRecord(root, context.targetContext);
    if (!resolved) throw new Error("Image detail target is stale or unavailable.");

    var record = resolved.record;
    var state = resolved.state;
    if (record.presentations.size || record.surface.parentElement !== record.sourceViewport) {
      throw new Error("Image detail target is already active or unavailable.");
    }
    var documentRef = context.document || root.ownerDocument;
    var section = documentRef.createElement("section");
    section.className = "docsViewer__contentDetail docsViewer__contentDetail--image";
    section.setAttribute("data-docs-content-detail-view", "image");

    var viewport = documentRef.createElement("div");
    viewport.className = "docsViewer__imageDetailViewport";
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

export const docsViewerImageDetailAdapter = createDocsViewerImageDetailAdapter();
