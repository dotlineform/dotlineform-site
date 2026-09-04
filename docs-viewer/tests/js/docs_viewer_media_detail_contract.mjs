import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const mediaDetail = await import(pathToFileURL(path.join(
  repoRoot,
  "docs-viewer/runtime/js/shared/docs-viewer-media-detail.js"
)));

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

const normalized = mediaDetail.normalizeDocsViewerMediaPresentation(suppliedPayload);
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
assert.equal(mediaDetail.docsViewerSafeMediaTarget("/catalogue/thumbs/00523.webp?v=1"), "/catalogue/thumbs/00523.webp?v=1");
assert.equal(mediaDetail.docsViewerSafeMediaTarget("http://media.dotlineform.com/00523.webp"), "");
assert.equal(mediaDetail.docsViewerSafeMediaTarget("https://user:secret@media.dotlineform.com/00523.webp"), "");
assert.equal(mediaDetail.docsViewerSafeMediaTarget("javascript:alert(1)"), "");

function rejected(change, expected) {
  var candidate = structuredClone(suppliedPayload);
  change(candidate);
  assert.throws(
    () => mediaDetail.normalizeDocsViewerMediaPresentation(candidate),
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

console.log("Docs Viewer Media View JavaScript contract OK");
