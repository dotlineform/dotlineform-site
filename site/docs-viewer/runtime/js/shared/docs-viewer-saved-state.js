const OWNERS = new Set(["public", "manage"]);
export function isSavedStateOwner(owner) {
  return OWNERS.has(owner);
}

export function savedStateOwner(appKind) {
  if (appKind === "review" || OWNERS.has(appKind)) return appKind;
  throw new Error("Saved Docs state requires an explicit application owner.");
}
