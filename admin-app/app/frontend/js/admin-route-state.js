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
    setOptionalDatasetValue(root, "adminRoute", detail.route);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "mode")) {
    setOptionalDatasetValue(root, "adminMode", detail.mode);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "service")) {
    setOptionalDatasetValue(root, "adminService", detail.service);
  }
  if (Object.prototype.hasOwnProperty.call(detail, "recordLoaded")) {
    setOptionalBooleanDatasetValue(root, "adminRecordLoaded", detail.recordLoaded);
  }
}

function buildEventDetail(root, ready) {
  return {
    ready,
    busy: root.dataset.adminBusy === "true",
    route: root.dataset.adminRoute || "",
    mode: root.dataset.adminMode || "",
    service: root.dataset.adminService || "",
    recordLoaded: root.dataset.adminRecordLoaded === "true"
  };
}

export function initializeAdminRouteState(target, detail = {}) {
  const root = resolveRoot(target);
  if (!root) return;
  applyRouteDetail(root, detail);
  root.dataset.adminReady = "false";
  root.dataset.adminBusy = "false";
}

export function setAdminRouteBusy(target, busy, detail = {}) {
  const root = resolveRoot(target);
  if (!root) return;
  applyRouteDetail(root, detail);
  root.dataset.adminBusy = busy ? "true" : "false";
}

export function setAdminRouteReady(target, ready, detail = {}) {
  const root = resolveRoot(target);
  if (!root) return;
  const nextReady = Boolean(ready);
  applyRouteDetail(root, detail);
  root.dataset.adminReady = nextReady ? "true" : "false";
  root.dispatchEvent(new CustomEvent("admin:ready", {
    bubbles: true,
    detail: buildEventDetail(root, nextReady)
  }));
}
