function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

export function selectedTextForToken(value) {
  return cleanString(value).replace(/\s+/g, " ");
}

export function buildSemanticReferenceToken(target, selectedText) {
  var kind = cleanString(target && target.kind);
  var id = cleanString(target && target.id);
  var label = selectedTextForToken(selectedText);
  if (!kind || !id || !label || label.indexOf("]]") >= 0) return "";
  return "[[ref:" + kind + ":" + id + "|" + label + "]]";
}
