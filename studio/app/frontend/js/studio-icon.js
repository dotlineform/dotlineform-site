/** Create decorative saved SVG artwork; the owning control supplies its accessible name and state. */
export function createStudioIcon(documentRef, artwork) {
  const icon = documentRef.createElement("span");
  icon.className = `studioUi__icon studioUi__icon--${artwork}`;
  icon.setAttribute("aria-hidden", "true");
  return icon;
}
