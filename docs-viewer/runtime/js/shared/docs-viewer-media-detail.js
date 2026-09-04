const MEDIA_DETAIL_SELECTOR = '[data-docs-content-detail="media"]';
const MEDIA_OPEN_SELECTOR = "[data-docs-media-open]";
const MEDIA_PRESENTATION_SELECTOR = [
  'script[type="application/json"]',
  "[data-docs-media-presentation]"
].join("");

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

function sameMediaTarget(left, right) {
  var first = left || {};
  var second = right || {};
  return cleanString(first.kind) === cleanString(second.kind)
    && cleanString(first.id) === cleanString(second.id);
}

/** Return a supported browser media target without resolving or rewriting it. */
export function docsViewerSafeMediaTarget(value) {
  var target = cleanString(value);
  var unsupportedCharacter = Array.from(target).some(function (character) {
    var code = character.charCodeAt(0);
    return character === "\\" || code <= 31 || code === 127;
  });
  if (!target || unsupportedCharacter) return "";
  if (target.startsWith("/") && !target.startsWith("//")) return target;
  try {
    var parsed = new URL(target);
    if (parsed.protocol !== "https:" || !parsed.hostname || parsed.username || parsed.password) {
      return "";
    }
    return target;
  } catch (_error) {
    return "";
  }
}

function normalizedTextField(value, fieldName) {
  var normalized = cleanString(value);
  if (!normalized) throw new Error("Media View requires " + fieldName + ".");
  return normalized;
}

/** Validate and freeze one complete browser-ready Media View presentation. */
export function normalizeDocsViewerMediaPresentation(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Media View requires an object payload.");
  }
  if (cleanString(value.schema_version) !== "docs_media_view_v1") {
    throw new Error("Media View requires schema docs_media_view_v1.");
  }

  var targetSource = value.target;
  if (!targetSource || typeof targetSource !== "object" || Array.isArray(targetSource)) {
    throw new Error("Media View requires an exact target.");
  }
  var targetKind = cleanString(targetSource.kind);
  var targetId = cleanString(targetSource.id);
  if (targetKind !== "catalogue-work" || !/^\d{5}$/.test(targetId)) {
    throw new Error("Media View requires an exact Catalogue Work target.");
  }

  var imageSource = value.image;
  if (!imageSource || typeof imageSource !== "object" || Array.isArray(imageSource)) {
    throw new Error("Media View requires image metadata.");
  }
  var imageSrc = docsViewerSafeMediaTarget(imageSource.src);
  var imageWidth = positiveInteger(imageSource.width_px);
  var imageHeight = positiveInteger(imageSource.height_px);
  if (!imageSrc) throw new Error("Media View image target is unsupported.");
  if (!imageWidth || !imageHeight) throw new Error("Media View image dimensions must be positive integers.");

  if (!Array.isArray(value.metadata)) {
    throw new Error("Media View requires ordered metadata.");
  }
  var metadata = value.metadata.map(function (entry) {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
      throw new Error("Media View metadata entries must be objects.");
    }
    return Object.freeze({
      label: normalizedTextField(entry.label, "a metadata label"),
      value: normalizedTextField(entry.value, "a metadata value")
    });
  });

  var newTabTarget = docsViewerSafeMediaTarget(value.new_tab_target);
  if (!newTabTarget) throw new Error("Media View new-tab target is unsupported.");

  return Object.freeze({
    schemaVersion: "docs_media_view_v1",
    target: Object.freeze({ kind: targetKind, id: targetId }),
    label: normalizedTextField(value.label, "a label"),
    image: Object.freeze({
      src: imageSrc,
      alt: normalizedTextField(imageSource.alt, "image alternative text"),
      widthPx: imageWidth,
      heightPx: imageHeight
    }),
    metadata: Object.freeze(metadata),
    newTabTarget: newTabTarget
  });
}

function immutableTargetContext(state, record) {
  return Object.freeze({
    documentTarget: Object.freeze(Object.assign({}, state.documentTarget)),
    documentMountGeneration: state.documentMountGeneration,
    kind: "media",
    adapterTargetId: record.id,
    occurrence: record.occurrence,
    mediaTarget: Object.freeze(Object.assign({}, record.presentation.target))
  });
}

function appendMetadata(documentRef, parent, metadata) {
  var list = documentRef.createElement("dl");
  list.className = "docsViewer__mediaDetailMetadata";
  metadata.forEach(function (entry) {
    var row = documentRef.createElement("div");
    row.className = "docsViewer__mediaDetailMetadataRow";
    var term = documentRef.createElement("dt");
    term.textContent = entry.label;
    var description = documentRef.createElement("dd");
    description.textContent = entry.value;
    row.appendChild(term);
    row.appendChild(description);
    list.appendChild(row);
  });
  parent.appendChild(list);
}

/** Own exact marked Media View presentations for one rendered-document mount. */
export function createDocsViewerMediaDetailAdapter() {
  var stateByRoot = new WeakMap();

  function releaseState(root, state) {
    if (!state) return { released: 0 };
    Array.from(state.presentations).forEach(function (presentation) {
      presentation.release();
    });
    state.records.forEach(function (record) {
      record.openControl.removeEventListener("click", record.handleClick);
    });
    var released = state.records.size;
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

  function resolveRecord(root, targetContext) {
    var target = targetContext || {};
    var state = root ? stateByRoot.get(root) : null;
    if (
      !state
      || cleanString(target.kind) !== "media"
      || positiveInteger(target.documentMountGeneration) !== state.documentMountGeneration
      || !sameDocumentTarget(target.documentTarget, state.documentTarget)
    ) {
      return null;
    }
    var record = state.records.get(cleanString(target.adapterTargetId)) || null;
    if (
      !record
      || positiveInteger(target.occurrence) !== record.occurrence
      || !sameMediaTarget(target.mediaTarget, record.presentation.target)
      || !root.contains(record.marker)
      || !root.contains(record.openControl)
    ) {
      return null;
    }
    return { record: record, state: state };
  }

  function readRecord(marker, index) {
    var openControl = marker.querySelector(MEDIA_OPEN_SELECTOR);
    var payloadElement = marker.querySelector(MEDIA_PRESENTATION_SELECTOR);
    if (!openControl || !payloadElement) return null;
    var presentation;
    try {
      presentation = normalizeDocsViewerMediaPresentation(JSON.parse(payloadElement.textContent || ""));
    } catch (_error) {
      return null;
    }
    if (cleanString(openControl.getAttribute("href")) !== presentation.newTabTarget) return null;
    return {
      handleClick: null,
      id: "media-" + index,
      marker: marker,
      occurrence: index + 1,
      openControl: openControl,
      presentation: presentation
    };
  }

  function mountDocument(mountContext) {
    var context = mountContext || {};
    var root = context.content;
    if (!root || typeof root.querySelectorAll !== "function") {
      return { found: 0, decorated: 0, skipped: 0 };
    }
    releaseState(root, stateByRoot.get(root));

    var markers = Array.from(root.querySelectorAll(MEDIA_DETAIL_SELECTOR));
    var documentMountGeneration = positiveInteger(context.documentMountGeneration);
    var documentTarget = {
      scope: cleanString(context.viewerScope),
      subScope: "",
      docId: cleanString(context.doc && context.doc.doc_id)
    };
    if (!documentMountGeneration || !documentTarget.scope || !documentTarget.docId) {
      return { found: markers.length, decorated: 0, skipped: markers.length };
    }

    var state = {
      documentMountGeneration: documentMountGeneration,
      documentTarget: documentTarget,
      presentations: new Set(),
      records: new Map(),
      requestContentDetail: typeof context.requestContentDetail === "function"
        ? context.requestContentDetail
        : function () { return false; }
    };
    markers.forEach(function (marker, index) {
      var record = readRecord(marker, index);
      if (!record) return;
      record.handleClick = function (event) {
        var targetContext = immutableTargetContext(state, record);
        if (!resolveRecord(root, targetContext)) return;
        if (state.requestContentDetail(targetContext) === true && event) event.preventDefault();
      };
      record.openControl.addEventListener("click", record.handleClick);
      state.records.set(record.id, record);
    });
    stateByRoot.set(root, state);
    return {
      found: markers.length,
      decorated: state.records.size,
      skipped: markers.length - state.records.size
    };
  }

  function mountPresentation(presentationContext) {
    var context = presentationContext || {};
    var root = context.content;
    var resolved = resolveRecord(root, context.targetContext);
    if (!resolved) throw new Error("Media View target is stale or unavailable.");

    var record = resolved.record;
    var state = resolved.state;
    var presentationData = record.presentation;
    var documentRef = context.document || root.ownerDocument;
    var section = documentRef.createElement("section");
    section.className = "docsViewer__contentDetail docsViewer__contentDetail--media";
    section.setAttribute("data-docs-content-detail-view", "media");

    var viewport = documentRef.createElement("div");
    viewport.className = "docsViewer__mediaDetailViewport";
    viewport.tabIndex = 0;
    viewport.setAttribute("role", "region");
    viewport.setAttribute("aria-label", presentationData.label);

    var figure = documentRef.createElement("figure");
    figure.className = "docsViewer__mediaDetailFigure";
    var image = documentRef.createElement("img");
    image.className = "docsViewer__mediaDetailImage";
    image.src = presentationData.image.src;
    image.alt = presentationData.image.alt;
    image.width = presentationData.image.widthPx;
    image.height = presentationData.image.heightPx;
    figure.appendChild(image);

    var caption = documentRef.createElement("figcaption");
    caption.className = "docsViewer__mediaDetailCaption";
    var title = documentRef.createElement("h2");
    title.className = "docsViewer__mediaDetailTitle";
    title.textContent = presentationData.label;
    caption.appendChild(title);
    appendMetadata(documentRef, caption, presentationData.metadata);
    figure.appendChild(caption);
    viewport.appendChild(figure);
    section.appendChild(viewport);

    var released = false;
    var presentation = {
      focusTarget: viewport,
      invocationControl: record.openControl,
      label: presentationData.label,
      newTabTarget: presentationData.newTabTarget,
      root: section,
      release: function () {
        if (released) return;
        released = true;
        section.remove();
        state.presentations.delete(presentation);
      }
    };
    state.presentations.add(presentation);
    return presentation;
  }

  return {
    mountDocument: mountDocument,
    mountPresentation: mountPresentation,
    releaseDocument: releaseDocument
  };
}

export const docsViewerMediaDetailAdapter = createDocsViewerMediaDetailAdapter();
