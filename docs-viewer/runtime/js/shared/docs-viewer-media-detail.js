import {
  docsViewerMediaPresentationForTarget,
  normalizeDocsViewerMediaPresentation
} from "./docs-viewer-media-presentation.js";
import { CONTENT_DETAIL_LABEL_CONTROL_ID } from "./docs-viewer-content-detail-view.js";

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
  return list;
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
    if (presentation.gallery) {
      if (openControl.tagName !== "BUTTON" || openControl.getAttribute("type") !== "button") return null;
    } else if (cleanString(openControl.getAttribute("href")) !== presentation.newTabTarget) {
      return null;
    }
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
    var supplied = record.presentation;
    var documentRef = context.document || root.ownerDocument;
    var section = documentRef.createElement("section");
    section.className = "docsViewer__contentDetail docsViewer__contentDetail--media";
    section.setAttribute("data-docs-content-detail-view", "media");

    var viewport = documentRef.createElement("div");
    viewport.className = "docsViewer__mediaDetailViewport";
    viewport.tabIndex = 0;
    viewport.setAttribute("role", "region");
    section.appendChild(viewport);

    var released = false;
    var controls = null;
    var current = null;

    function imageElement(data, className) {
      var image = documentRef.createElement("img");
      image.className = className;
      image.src = data.src;
      image.alt = data.alt;
      image.width = data.widthPx;
      image.height = data.heightPx;
      return image;
    }

    function titleElement(label) {
      var title = documentRef.createElement("h2");
      title.className = "docsViewer__mediaDetailTitle";
      title.textContent = label;
      return title;
    }

    function targetButton(label, className, target) {
      var button = documentRef.createElement("button");
      button.type = "button";
      button.className = className;
      button.setAttribute("aria-label", label);
      button.addEventListener("click", function () {
        if (released || !viewport.contains(button)) return;
        renderTarget(target);
        viewport.focus({ preventScroll: true });
      });
      return button;
    }

    function renderWork(work) {
      var figure = documentRef.createElement("figure");
      figure.className = "docsViewer__mediaDetailFigure";
      figure.appendChild(imageElement(work.image, "docsViewer__mediaDetailImage"));
      var caption = documentRef.createElement("figcaption");
      caption.className = "docsViewer__mediaDetailCaption";
      caption.appendChild(titleElement(work.label));
      var metadata = appendMetadata(documentRef, caption, work.metadata);
      if (supplied.gallery) {
        var row = documentRef.createElement("div");
        row.className = "docsViewer__mediaDetailMetadataRow";
        var term = documentRef.createElement("dt");
        term.textContent = "Series";
        var description = documentRef.createElement("dd");
        var link = targetButton(
          "Open gallery: " + supplied.gallery.label,
          "docsViewer__mediaDetailSeriesLink",
          supplied.gallery.target
        );
        link.textContent = supplied.gallery.label;
        description.appendChild(link);
        row.appendChild(term);
        row.appendChild(description);
        metadata.appendChild(row);
      }
      figure.appendChild(caption);
      return figure;
    }

    function renderGallery(gallery) {
      var container = documentRef.createElement("div");
      container.appendChild(titleElement(gallery.label));
      var list = documentRef.createElement("ul");
      list.className = "docsViewer__mediaDetailGallery";
      gallery.members.forEach(function (member) {
        var item = documentRef.createElement("li");
        var button = targetButton(
          "Open " + member.work.label + " (" + member.work.target.id + ")",
          "docsViewer__mediaDetailThumbnail",
          member.work.target
        );
        var image = imageElement(member.thumbnail, "docsViewer__mediaDetailThumbnailImage");
        image.loading = "lazy";
        button.appendChild(image);
        var label = documentRef.createElement("span");
        label.textContent = member.work.label;
        button.appendChild(label);
        item.appendChild(button);
        list.appendChild(item);
      });
      container.appendChild(list);
      return container;
    }

    function projectControls() {
      if (!controls) return;
      controls.projectControlState(CONTENT_DETAIL_LABEL_CONTROL_ID, {
        hidden: false,
        label: current.label
      });
      controls.projectNewTabTarget(current.newTabTarget);
    }

    function renderTarget(target) {
      current = docsViewerMediaPresentationForTarget(supplied, target);
      if (!current) throw new Error("Media View target is not in the supplied presentation.");
      viewport.replaceChildren(current.target.kind === "catalogue-series"
        ? renderGallery(current)
        : renderWork(current));
      viewport.setAttribute("aria-label", current.label);
      section.setAttribute("data-docs-media-kind", current.target.kind);
      section.setAttribute("data-docs-media-id", current.target.id);
      presentation.label = current.label;
      presentation.newTabTarget = current.newTabTarget;
      projectControls();
    }

    var presentation = {
      focusTarget: viewport,
      invocationControl: record.openControl,
      label: supplied.label,
      newTabTarget: supplied.newTabTarget,
      root: section,
      activate: function (activationContext) {
        if (released) return;
        controls = activationContext;
        projectControls();
      },
      release: function () {
        if (released) return;
        released = true;
        controls = null;
        viewport.replaceChildren();
        section.remove();
        state.presentations.delete(presentation);
      }
    };
    renderTarget(supplied.target);
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
