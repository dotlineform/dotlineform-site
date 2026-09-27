const OWNERS = new Set(["public", "manage"]);
export function isSavedStateOwner(owner) {
  return OWNERS.has(owner);
}

export function savedStateOwner(appKind) {
  if (appKind === "review" || OWNERS.has(appKind)) return appKind;
  throw new Error("Saved Docs state requires an explicit application owner.");
}

export function indexPanelStorageKey(owner) {
  if (owner === "review") return "dotlineform-docs-viewer-index-panel:review";
  if (!isSavedStateOwner(owner)) throw new Error("Unknown Docs panel owner.");
  return "dotlineform-docs-viewer-index-panel:v2:" + owner;
}

export function convertWorkingPanelState(storage) {
  if (!storage) return;
  const marker = "dotlineform-docs-viewer-manage-state-v4";
  if (storage.getItem(marker) === "complete") return;
  const oldKey = "dotlineform-docs-viewer-index-panel:v2:working";
  const newKey = indexPanelStorageKey("manage");
  const value = storage.getItem(oldKey);
  const existing = storage.getItem(newKey);
  if (value !== null && existing !== null && existing !== value) {
    throw new Error("Docs panel conversion found conflicting saved settings.");
  }
  if (value !== null) {
    storage.setItem(newKey, value);
    storage.removeItem(oldKey);
  }
  storage.setItem(marker, "complete");
}
