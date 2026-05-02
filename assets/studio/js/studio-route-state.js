function resolveRoot(target) {
  if (!target) return null;
  if (target instanceof Element) return target;
  return target.root instanceof Element ? target.root : null;
}

function normalizeAttributeValue(value) {
  return typeof value === "string" ? value.trim() : "";
}

function setOptionalDatasetValue(root, key, value) {
  const normalized = normalizeAttributeValue(value);
  if (normalized) {
    root.dataset[key] = normalized;
  } else {
    delete root.dataset[key];
  }
}

function setOptionalBooleanDatasetValue(root, key, value) {
  if (typeof value === "boolean") {
    root.dataset[key] = value ? "true" : "false";
  } else {
    delete root.dataset[key];
  }
}

function applyRouteDetail(root, detail = {}) {
  if (Object.prototype.hasOwnProperty.call(detail, "route")) {
    setOptionalDatasetValue(root, "studioRoute", detail.route);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "mode")) {
    setOptionalDatasetValue(root, "studioMode", detail.mode);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "service")) {
    setOptionalDatasetValue(root, "studioService", detail.service);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "recordLoaded")) {
    setOptionalBooleanDatasetValue(root, "studioRecordLoaded", detail.recordLoaded);
  }
}

function buildEventDetail(root, ready) {
  return {
    ready,
    busy: root.dataset.studioBusy === "true",
    route: root.dataset.studioRoute || "",
    mode: root.dataset.studioMode || "",
    service: root.dataset.studioService || "",
    recordLoaded: root.dataset.studioRecordLoaded === "true"
  };
}

export function initializeStudioRouteState(target, detail = {}) {
  const root = resolveRoot(target);
  if (!root) return;
  applyRouteDetail(root, detail);
  root.dataset.studioReady = "false";
  root.dataset.studioBusy = "false";
}

export function setStudioRouteBusy(target, busy, detail = {}) {
  const root = resolveRoot(target);
  if (!root) return;
  applyRouteDetail(root, detail);
  root.dataset.studioBusy = busy ? "true" : "false";
}

export function setStudioRouteReady(target, ready, detail = {}) {
  const root = resolveRoot(target);
  if (!root) return;
  const nextReady = Boolean(ready);
  applyRouteDetail(root, detail);
  root.dataset.studioReady = nextReady ? "true" : "false";
  root.dispatchEvent(new CustomEvent("studio:ready", {
    bubbles: true,
    detail: buildEventDetail(root, nextReady)
  }));
}
