function normalizeText(value) {
  return String(value == null ? "" : value).trim();
}

function interpolateText(template, tokens = null) {
  let text = normalizeText(template);
  if (!tokens || typeof tokens !== "object") return text;
  Object.entries(tokens).forEach(([key, value]) => {
    text = text.replaceAll(`{${key}}`, String(value == null ? "" : value));
  });
  return text;
}

function lookupText(options, key, fallback, tokens = null) {
  if (options && typeof options.text === "function") {
    return options.text(key, fallback, tokens);
  }
  return interpolateText(fallback, tokens);
}

export function formatCatalogueDeletePreview(preview, options = {}) {
  return normalizeText(preview && preview.summary)
    || lookupText(options, "delete_confirm_default", options.defaultText || "Delete this source record?");
}
