const OWNERS = new Set(["public", "working", "pre-publish", "published"]);

// Used only by the one-time storage conversions, never by runtime lookups.
export const RETIRED_ANALYSIS_STATE = Object.freeze({
  analysis: "public",
  "analysis/working": "working",
  "analysis/pre-publish": "pre-publish",
  "analysis/published": "published"
});

export function isSavedStateOwner(owner) {
  return OWNERS.has(owner);
}

export function savedStateOwner(appKind, stage) {
  if (appKind === "public") return "public";
  if (appKind === "review") return "review";
  if (appKind === "manage" && OWNERS.has(stage) && stage !== "public") return stage;
  throw new Error("Saved Docs state requires an explicit route and stage.");
}

export function indexPanelStorageKey(owner) {
  if (owner === "review") return "dotlineform-docs-viewer-index-panel:review";
  if (!isSavedStateOwner(owner)) throw new Error("Unknown Docs panel owner.");
  return "dotlineform-docs-viewer-index-panel:v2:" + owner;
}

export function convertAnalysisPanelState(storage) {
  if (!storage) return;
  const marker = "dotlineform-docs-viewer-analysis-state-v2";
  if (storage.getItem(marker) === "complete") return;
  const changes = Object.entries(RETIRED_ANALYSIS_STATE).map(([legacy, owner]) => {
    const oldKey = "dotlineform-docs-viewer-index-panel:" + legacy;
    const newKey = indexPanelStorageKey(owner);
    const value = storage.getItem(oldKey);
    const existing = storage.getItem(newKey);
    if (value !== null && existing !== null && existing !== value) {
      throw new Error("Docs panel conversion found conflicting saved settings.");
    }
    return { oldKey, newKey, value };
  });
  // Copy before removal. An interrupted conversion can resume with identical values.
  changes.forEach(({ newKey, value }) => {
    if (value !== null) storage.setItem(newKey, value);
  });
  changes.forEach(({ oldKey, value }) => {
    if (value !== null) storage.removeItem(oldKey);
  });
  storage.setItem(marker, "complete");
}
