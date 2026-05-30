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
    setOptionalDatasetValue(root, "analyticsRoute", detail.route);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "mode")) {
    setOptionalDatasetValue(root, "analyticsMode", detail.mode);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "service")) {
    setOptionalDatasetValue(root, "analyticsService", detail.service);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "recordLoaded")) {
    setOptionalBooleanDatasetValue(root, "analyticsRecordLoaded", detail.recordLoaded);
  }
}

function buildEventDetail(root, ready) {
  return {
    ready,
    busy: root.dataset.analyticsBusy === "true",
    route: root.dataset.analyticsRoute || "",
    mode: root.dataset.analyticsMode || "",
    service: root.dataset.analyticsService || "",
    recordLoaded: root.dataset.analyticsRecordLoaded === "true"
  };
}

export function initializeAnalyticsRouteState(target, detail = {}) {
  const root = resolveRoot(target);
  if (!root) return;
  applyRouteDetail(root, detail);
  root.dataset.analyticsReady = "false";
  root.dataset.analyticsBusy = "false";
}

export function setAnalyticsRouteBusy(target, busy, detail = {}) {
  const root = resolveRoot(target);
  if (!root) return;
  applyRouteDetail(root, detail);
  root.dataset.analyticsBusy = busy ? "true" : "false";
}

export function setAnalyticsRouteReady(target, ready, detail = {}) {
  const root = resolveRoot(target);
  if (!root) return;
  const nextReady = Boolean(ready);
  applyRouteDetail(root, detail);
  root.dataset.analyticsReady = nextReady ? "true" : "false";
  root.dispatchEvent(new CustomEvent("analytics:ready", {
    bubbles: true,
    detail: buildEventDetail(root, nextReady)
  }));
}
