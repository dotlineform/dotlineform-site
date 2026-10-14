export function normalizeDocsCollectionFilterValue(value) {
  return value.trim()
    .normalize("NFKC")
    .replace(/\s+/g, " ")
    .toLowerCase();
}
