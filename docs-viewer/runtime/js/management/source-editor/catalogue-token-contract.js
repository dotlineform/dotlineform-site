var CATALOGUE_TARGET_ID_PATTERNS = Object.freeze({
  work: /^\d{5}$/,
  series: /^[a-z0-9][a-z0-9-]*$/,
  moment: /^[a-z0-9][a-z0-9-]*$/
});

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

export function selectedTextForCatalogueTitle(value) {
  return cleanString(value).replace(/\s+/g, " ");
}

export function buildCatalogueToken(options = {}) {
  var targetType = cleanString(options.targetType);
  var targetId = cleanString(options.targetId);
  var title = cleanString(options.title);
  var idPattern = CATALOGUE_TARGET_ID_PATTERNS[targetType];
  if (!idPattern || !idPattern.test(targetId) || !title || /[\r\n]/.test(title)) return "";
  return serializeCatalogueToken({
    targetType: targetType,
    targetId: targetId,
    title: title
  });
}
import {
  serializeCatalogueToken
} from "./catalogue-token-parser.js";
