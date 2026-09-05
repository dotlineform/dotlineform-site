import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const mediaDetail = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/shared/docs-viewer-media-detail.js"
)));
const mediaPresentation = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/shared/docs-viewer-media-presentation.js"
)));
const { normalizeDocsViewerMediaPresentation, docsViewerSafeMediaTarget } = mediaPresentation;

const mediaTarget = "https://media.dotlineform.com/works/img/00523-primary-1600.webp?v=1";
const suppliedPayload = {
  schema_version: "docs_media_view_v1",
  target: { kind: "catalogue-work", id: "00523" },
  label: "kylie structure 4",
  image: {
    src: mediaTarget,
    alt: "kylie structure 4",
    width_px: 9449,
    height_px: 5315
  },
  metadata: [
    { label: "Year", value: "2023" },
    { label: "Medium", value: "digital c-type print" },
    { label: "Dimensions", value: "45 × 80 cm" }
  ],
  new_tab_target: mediaTarget
};

const normalized = normalizeDocsViewerMediaPresentation(suppliedPayload);
assert.deepEqual(normalized, {
  schemaVersion: "docs_media_view_v1",
  target: { kind: "catalogue-work", id: "00523" },
  label: "kylie structure 4",
  image: {
    src: mediaTarget,
    alt: "kylie structure 4",
    widthPx: 9449,
    heightPx: 5315
  },
  metadata: [
    { label: "Year", value: "2023" },
    { label: "Medium", value: "digital c-type print" },
    { label: "Dimensions", value: "45 × 80 cm" }
  ],
  newTabTarget: mediaTarget
});
assert.equal(Object.isFrozen(normalized), true);
assert.equal(Object.isFrozen(normalized.target), true);
assert.equal(Object.isFrozen(normalized.image), true);
assert.equal(Object.isFrozen(normalized.metadata), true);
assert.equal(Object.isFrozen(normalized.metadata[0]), true);
assert.equal(docsViewerSafeMediaTarget("/catalogue/thumbs/00523.webp?v=1"), "/catalogue/thumbs/00523.webp?v=1");
assert.equal(docsViewerSafeMediaTarget("http://media.dotlineform.com/00523.webp"), "");
assert.equal(docsViewerSafeMediaTarget("https://user:secret@media.dotlineform.com/00523.webp"), "");
assert.equal(docsViewerSafeMediaTarget("javascript:alert(1)"), "");

function rejected(change, expected) {
  var candidate = structuredClone(suppliedPayload);
  change(candidate);
  assert.throws(
    () => normalizeDocsViewerMediaPresentation(candidate),
    expected
  );
}

rejected((value) => { value.schema_version = "docs_media_view_v2"; }, /schema docs_media_view_v1/);
rejected((value) => { value.target.kind = "catalogue-series"; }, /Catalogue Work target/);
rejected((value) => { value.target.id = "523"; }, /Catalogue Work target/);
rejected((value) => { value.image.src = "http://example.com/00523.webp"; }, /image target/);
rejected((value) => { value.image.width_px = 0; }, /dimensions/);
rejected((value) => { value.metadata[0].value = ""; }, /metadata value/);
rejected((value) => { value.new_tab_target = "//example.com/00523.webp"; }, /new-tab target/);

class FakeElement {
  constructor(tagName, documentRef) {
    this.tagName = String(tagName || "").toUpperCase();
    this.ownerDocument = documentRef;
    this.attributes = new Map();
    this.children = [];
    this.parentElement = null;
    this.listeners = new Map();
    this.className = "";
    this.dataset = {};
    this.textContent = "";
    this.tabIndex = -1;
  }

  appendChild(child) {
    if (child.parentElement) {
      child.parentElement.children = child.parentElement.children.filter((item) => item !== child);
    }
    child.parentElement = this;
    this.children.push(child);
    return child;
  }

  replaceChildren(...children) {
    this.children.forEach((child) => { child.parentElement = null; });
    this.children = [];
    children.forEach((child) => this.appendChild(child));
  }

  setAttribute(name, value) {
    this.attributes.set(String(name), String(value));
  }

  getAttribute(name) {
    return this.attributes.has(String(name)) ? this.attributes.get(String(name)) : null;
  }

  addEventListener(name, handler) {
    this.listeners.set(String(name), handler);
  }

  removeEventListener(name, handler) {
    if (this.listeners.get(String(name)) === handler) this.listeners.delete(String(name));
  }

  matches(selector) {
    if (selector === '[data-docs-content-detail="media"]') {
      return this.getAttribute("data-docs-content-detail") === "media";
    }
    if (selector === "[data-docs-media-open]") {
      return this.attributes.has("data-docs-media-open");
    }
    if (selector === 'script[type="application/json"][data-docs-media-presentation]') {
      return this.tagName === "SCRIPT"
        && this.getAttribute("type") === "application/json"
        && this.attributes.has("data-docs-media-presentation");
    }
    if (selector.startsWith(".")) {
      return this.className.split(/\s+/).includes(selector.slice(1));
    }
    return this.tagName === selector.toUpperCase();
  }

  querySelectorAll(selector) {
    var matches = [];
    this.children.forEach(function visit(child) {
      if (child.matches(selector)) matches.push(child);
      child.children.forEach(visit);
    });
    return matches;
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }

  contains(candidate) {
    if (candidate === this) return true;
    return this.children.some((child) => child.contains(candidate));
  }

  remove() {
    if (!this.parentElement) return;
    this.parentElement.children = this.parentElement.children.filter((item) => item !== this);
    this.parentElement = null;
  }

  focus() {
    this.focused = true;
  }

  dispatchClick() {
    var prevented = false;
    var handler = this.listeners.get("click");
    if (handler) {
      handler({ preventDefault() { prevented = true; } });
    }
    return prevented;
  }
}

class FakeDocument {
  createElement(tagName) {
    return new FakeElement(tagName, this);
  }
}

function appendMarker(documentRef, root, payload, href) {
  var marker = documentRef.createElement("figure");
  marker.setAttribute("data-docs-content-detail", "media");
  var openControl = documentRef.createElement("a");
  openControl.setAttribute("data-docs-media-open", "");
  openControl.setAttribute("href", href);
  var script = documentRef.createElement("script");
  script.setAttribute("type", "application/json");
  script.setAttribute("data-docs-media-presentation", "");
  script.textContent = JSON.stringify(payload);
  marker.appendChild(openControl);
  marker.appendChild(script);
  root.appendChild(marker);
  return { marker, openControl };
}

const documentRef = new FakeDocument();
const root = documentRef.createElement("article");
const valid = appendMarker(documentRef, root, suppliedPayload, mediaTarget);
appendMarker(
  documentRef,
  root,
  Object.assign({}, suppliedPayload, { new_tab_target: "http://example.com/unsafe.webp" }),
  "http://example.com/unsafe.webp"
);

const requestedTargets = [];
const adapter = mediaDetail.createDocsViewerMediaDetailAdapter();
assert.deepEqual(adapter.mountDocument({
  content: root,
  doc: { doc_id: "d-20260904-example" },
  document: documentRef,
  documentMountGeneration: 7,
  requestContentDetail(target) {
    requestedTargets.push(target);
    return true;
  },
  viewerScope: "analysis"
}), { found: 2, decorated: 1, skipped: 1 });

assert.equal(valid.openControl.dispatchClick(), true);
assert.equal(requestedTargets.length, 1);
const exactTarget = requestedTargets[0];
assert.equal(Object.isFrozen(exactTarget), true);
assert.equal(Object.isFrozen(exactTarget.documentTarget), true);
assert.equal(Object.isFrozen(exactTarget.mediaTarget), true);
assert.deepEqual(exactTarget, {
  documentTarget: { scope: "analysis", subScope: "", docId: "d-20260904-example" },
  documentMountGeneration: 7,
  kind: "media",
  adapterTargetId: "media-0",
  occurrence: 1,
  mediaTarget: { kind: "catalogue-work", id: "00523" }
});

assert.throws(() => adapter.mountPresentation({
  content: root,
  document: documentRef,
  targetContext: Object.assign({}, exactTarget, { documentMountGeneration: 8 })
}), /stale or unavailable/);
assert.throws(() => adapter.mountPresentation({
  content: root,
  document: documentRef,
  targetContext: Object.assign({}, exactTarget, {
    mediaTarget: { kind: "catalogue-work", id: "00524" }
  })
}), /stale or unavailable/);

const presentation = adapter.mountPresentation({
  content: root,
  document: documentRef,
  targetContext: exactTarget
});
root.appendChild(presentation.root);
assert.equal(presentation.label, "kylie structure 4");
assert.equal(presentation.newTabTarget, mediaTarget);
assert.equal(presentation.invocationControl, valid.openControl);
const detailImage = presentation.root.querySelector(".docsViewer__mediaDetailImage");
assert.equal(detailImage.src, mediaTarget);
assert.equal(detailImage.alt, "kylie structure 4");
assert.equal(detailImage.width, 9449);
assert.equal(detailImage.height, 5315);
const rows = presentation.root.querySelectorAll(".docsViewer__mediaDetailMetadataRow");
assert.deepEqual(rows.map((row) => row.children.map((child) => child.textContent)), [
  ["Year", "2023"],
  ["Medium", "digital c-type print"],
  ["Dimensions", "45 × 80 cm"]
]);

assert.deepEqual(adapter.releaseDocument({ content: root }), { released: 1 });
assert.equal(root.contains(presentation.root), false);
assert.equal(valid.openControl.dispatchClick(), false);
assert.equal(requestedTargets.length, 1);
assert.throws(() => adapter.mountPresentation({
  content: root,
  document: documentRef,
  targetContext: exactTarget
}), /stale or unavailable/);

function galleryWork(id, label) {
  var work = structuredClone(suppliedPayload);
  work.target.id = id;
  work.label = label;
  work.image.src = "https://media.dotlineform.com/works/img/" + id + "-primary-1600.webp?v=1";
  work.image.alt = label;
  work.new_tab_target = work.image.src;
  work.metadata = [{ label: "Catalogue number", value: id }];
  return {
    work: work,
    thumbnail: { src: "/thumbs/" + id + ".webp", alt: label, width_px: 96, height_px: 96 }
  };
}

const galleryPayload = {
  schema_version: "docs_media_gallery_v1",
  target: { kind: "catalogue-series", id: "143" },
  gallery: {
    target: { kind: "catalogue-series", id: "143" },
    label: "simultaneous equations",
    members: [galleryWork("01941", "se1"), galleryWork("01942", "se2")]
  }
};
const gallery = normalizeDocsViewerMediaPresentation(galleryPayload);
assert.equal(gallery.newTabTarget, "");
assert.deepEqual(gallery.gallery.members.map((member) => member.work.target.id), ["01941", "01942"]);
assert.equal(Object.isFrozen(gallery.gallery), true);
assert.equal(Object.isFrozen(gallery.gallery.members), true);
assert.equal(Object.isFrozen(gallery.gallery.members[0]), true);
assert.equal(Object.isFrozen(gallery.gallery.members[0].work), true);
assert.equal(Object.isFrozen(gallery.gallery.members[0].thumbnail), true);

const singleMemberGallery = structuredClone(galleryPayload);
singleMemberGallery.gallery.members.pop();
assert.equal(normalizeDocsViewerMediaPresentation(singleMemberGallery).gallery.members.length, 1);

function rejectGallery(change, expected) {
  var candidate = structuredClone(galleryPayload);
  change(candidate);
  assert.throws(() => normalizeDocsViewerMediaPresentation(candidate), expected);
}
rejectGallery((value) => { value.target.id = "144"; }, /entry target/);
rejectGallery((value) => { value.target = { kind: "catalogue-work", id: "99999" }; }, /entry target/);
rejectGallery((value) => { value.gallery.target.kind = "catalogue-work"; }, /Series target/);
rejectGallery((value) => { value.gallery.target.id = 143; }, /Series target/);
rejectGallery((value) => { value.gallery.members.push(value.gallery.members[0]); }, /duplicate Work/);
rejectGallery((value) => { value.gallery.members[0].thumbnail.src = "javascript:alert(1)"; }, /safe thumbnail/);
rejectGallery((value) => { value.gallery.members[0].work.target.id = "1941"; }, /Work target/);

const galleryRoot = documentRef.createElement("article");
const galleryMarker = appendMarker(documentRef, galleryRoot, galleryPayload, "");
galleryMarker.openControl.tagName = "BUTTON";
galleryMarker.openControl.setAttribute("type", "button");
let galleryInvocation;
let hostRequests = 0;
adapter.mountDocument({
  content: galleryRoot,
  viewerScope: "analysis",
  doc: { doc_id: "d-gallery-proof" },
  documentMountGeneration: 9,
  requestContentDetail(target) { galleryInvocation = target; hostRequests += 1; return true; }
});
galleryMarker.openControl.dispatchClick();
const galleryView = adapter.mountPresentation({ content: galleryRoot, targetContext: galleryInvocation });
galleryRoot.appendChild(galleryView.root);
const stableRoot = galleryView.root;
let activeLabel;
let activeOriginal;
galleryView.activate({
  projectControlState(_id, value) { activeLabel = value.label; },
  projectNewTabTarget(value) { activeOriginal = value; }
});
assert.equal(activeLabel, "simultaneous equations");
assert.equal(activeOriginal, "");
assert.equal(galleryView.root.querySelector(".docsViewer__mediaDetailImage"), null);
assert.deepEqual(galleryView.root.querySelectorAll(".docsViewer__mediaDetailThumbnailImage").map((img) => img.src), [
  "/thumbs/01941.webp", "/thumbs/01942.webp"
]);

// Verify exact record transitions and host ownership, rather than presentation choreography.
const firstThumbnail = galleryView.root.querySelectorAll(".docsViewer__mediaDetailThumbnail")[0];
firstThumbnail.dispatchClick();
assert.equal(galleryView.root, stableRoot);
assert.equal(activeLabel, "se1");
assert.equal(activeOriginal, galleryPayload.gallery.members[0].work.new_tab_target);
assert.equal(galleryView.root.getAttribute("data-docs-media-id"), "01941");
assert.equal(galleryView.root.querySelector(".docsViewer__mediaDetailImage").src, activeOriginal);
assert.equal(galleryView.root.querySelector(".docsViewer__mediaDetailMetadataRow").children[1].textContent, "01941");
assert.equal(galleryView.root.querySelector(".docsViewer__mediaDetailGallery"), null);
galleryView.root.querySelector(".docsViewer__mediaDetailSeriesLink").dispatchClick();
assert.equal(activeOriginal, "");
assert.equal(galleryView.root.getAttribute("data-docs-media-id"), "143");
galleryView.root.querySelectorAll(".docsViewer__mediaDetailThumbnail")[1].dispatchClick();
assert.equal(activeLabel, "se2");
assert.equal(activeOriginal, galleryPayload.gallery.members[1].work.new_tab_target);
assert.equal(galleryView.root.querySelector(".docsViewer__mediaDetailMetadataRow").children[1].textContent, "01942");
assert.equal(galleryView.invocationControl, galleryMarker.openControl);
assert.equal(hostRequests, 1);
firstThumbnail.dispatchClick();
assert.equal(activeLabel, "se2", "detached controls must not change the active target");
const seriesLink = galleryView.root.querySelector(".docsViewer__mediaDetailSeriesLink");
adapter.releaseDocument({ content: galleryRoot });
seriesLink.dispatchClick();
assert.equal(activeLabel, "se2", "released presentations must not update host controls");
assert.equal(galleryRoot.contains(stableRoot), false);

// The same supplied collection may start at an exact Work without opening the gallery first.
const directWorkPayload = structuredClone(galleryPayload);
directWorkPayload.target = { kind: "catalogue-work", id: "01942" };
const directWork = normalizeDocsViewerMediaPresentation(directWorkPayload);
assert.equal(directWork.label, "se2");
assert.equal(directWork.newTabTarget, galleryPayload.gallery.members[1].work.new_tab_target);
galleryMarker.marker.querySelector('script[type="application/json"][data-docs-media-presentation]').textContent = JSON.stringify(directWorkPayload);
adapter.mountDocument({
  content: galleryRoot,
  viewerScope: "analysis",
  doc: { doc_id: "d-gallery-proof" },
  documentMountGeneration: 10,
  requestContentDetail(target) { galleryInvocation = target; return true; }
});
galleryMarker.openControl.dispatchClick();
const directView = adapter.mountPresentation({ content: galleryRoot, targetContext: galleryInvocation });
assert.equal(directView.root.getAttribute("data-docs-media-id"), "01942");
assert.equal(directView.root.querySelector(".docsViewer__mediaDetailGallery"), null);
adapter.releaseDocument({ content: galleryRoot });

console.log("Docs Viewer Media View JavaScript contract OK");
