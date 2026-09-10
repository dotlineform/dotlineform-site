function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

export function selectedTextForCatalogueTitle(value) {
  return cleanString(value).replace(/\s+/g, " ");
}
