var LEXICAL_KEY_PATTERN = /^[a-z][a-z0-9-]*$/;
var LEXICAL_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
var IMAGE_FIELDS = new Set(["alt", "detail_id", "caption", "summary", "placement", "fill_width"]);
var IMAGE_PLACEMENTS = new Set(["full", "left", "right"]);

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function plainText(value) {
  return cleanString(value).replace(/\s+/g, " ");
}

function summaryText(value) {
  return String(value == null ? "" : value)
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .map(function (line) { return line.trim().replace(/\s+/g, " "); })
    .join("\n")
    .trim();
}

function encodeImageValue(value) {
  return encodeURIComponent(value).replace(/[!'()*]/g, function (character) {
    return "%" + character.charCodeAt(0).toString(16).toUpperCase();
  });
}

function decodeImageValue(value) {
  try {
    var decoded = decodeURIComponent(value);
    return encodeImageValue(decoded) === value ? decoded : null;
  } catch (_error) {
    return null;
  }
}

export function normalizeCatalogueDetailId(value) {
  var raw = cleanString(value);
  if (!raw) return "";
  if (!/^\d+$/.test(raw)) return null;
  var significant = raw.replace(/^0+/, "");
  if (!significant) return null;
  return significant.padStart(3, "0");
}

function escapedTitle(value) {
  return value.replace(/\\/g, "\\\\").replace(/\|/g, "\\|").replace(/\]/g, "\\]");
}

function unescapeTitle(value) {
  var output = "";
  var index = 0;
  while (index < value.length) {
    if (value[index] !== "\\") {
      output += value[index];
      index += 1;
      continue;
    }
    var escaped = value[index + 1];
    if (escaped !== "\\" && escaped !== "|" && escaped !== "]") return null;
    output += escaped;
    index += 2;
  }
  return cleanString(output) || null;
}

function targetDefinition(registry, family, targetType) {
  var familyDefinition = registry && registry.familiesById
    ? registry.familiesById.get(family)
    : null;
  return familyDefinition && familyDefinition.targetTypesById
    ? familyDefinition.targetTypesById.get(targetType)
    : null;
}

export function semanticTokenClosingIndex(text, start) {
  var index = start;
  while (index < text.length - 1) {
    if (text[index] === "\\") {
      index += 2;
      continue;
    }
    if (text.slice(index, index + 2) === "]]") return index;
    index += 1;
  }
  return -1;
}

export function serializeCatalogueToken(options = {}) {
  var targetType = cleanString(options.targetType);
  var targetId = cleanString(options.targetId);
  var title = cleanString(options.title);
  if (
    !LEXICAL_KEY_PATTERN.test(targetType)
    || !LEXICAL_ID_PATTERN.test(targetId)
    || !title
    || /[\r\n]/.test(title)
  ) return "";
  var definition = targetDefinition(options.registry, "catalogue", targetType);
  if (definition && definition.idPolicy.canonicalPattern) {
    var canonicalPattern = new RegExp(definition.idPolicy.canonicalPattern);
    if (!canonicalPattern.test(targetId)) return "";
  }
  return "[[catalogue:" + targetType + ":" + targetId + "|" + escapedTitle(title) + "]]";
}

export function serializeCatalogueImageToken(options = {}) {
  var targetType = cleanString(options.targetType);
  var targetId = cleanString(options.targetId);
  var alt = plainText(options.alt);
  if (
    !LEXICAL_KEY_PATTERN.test(targetType)
    || !LEXICAL_ID_PATTERN.test(targetId)
    || !alt
  ) return "";
  var definition = targetDefinition(options.registry, "catalogue", targetType);
  if (definition && definition.idPolicy.canonicalPattern) {
    var canonicalPattern = new RegExp(definition.idPolicy.canonicalPattern);
    if (!canonicalPattern.test(targetId)) return "";
  }
  var caption = plainText(options.caption);
  var summary = summaryText(options.summary);
  var placement = cleanString(options.placement).toLowerCase();
  var fields = [["alt", alt]];
  var detailId = normalizeCatalogueDetailId(options.detailId);
  if (detailId === null || (detailId && targetType !== "work")) return "";
  if (detailId) fields.push(["detail_id", detailId]);
  if (caption) {
    if (!IMAGE_PLACEMENTS.has(placement) || typeof options.fillWidth !== "boolean") return "";
    fields.push(["caption", caption]);
    if (summary) fields.push(["summary", summary]);
    fields.push(["placement", placement]);
    fields.push(["fill_width", options.fillWidth ? "true" : "false"]);
  } else if (summary || placement || typeof options.fillWidth === "boolean") {
    return "";
  }
  var query = fields.map(function (field) {
    return field[0] + "=" + encodeImageValue(field[1]);
  }).join("&");
  return "[[catalogue:image:" + targetType + ":" + targetId + "|" + query + "]]";
}

function parseCatalogueImageFields(rawQuery, options) {
  if (!rawQuery) return null;
  var fields = {};
  var pairs = rawQuery.split("&");
  for (var index = 0; index < pairs.length; index += 1) {
    var separator = pairs[index].indexOf("=");
    if (separator < 1) return null;
    var key = pairs[index].slice(0, separator);
    var encodedValue = pairs[index].slice(separator + 1);
    if (!IMAGE_FIELDS.has(key) || Object.prototype.hasOwnProperty.call(fields, key) || !encodedValue) {
      return null;
    }
    var value = decodeImageValue(encodedValue);
    if (value === null) return null;
    fields[key] = value;
  }
  if (!fields.alt) return null;
  var fillWidth;
  if (Object.prototype.hasOwnProperty.call(fields, "fill_width")) {
    if (fields.fill_width !== "true" && fields.fill_width !== "false") return null;
    fillWidth = fields.fill_width === "true";
  }
  var serialized = serializeCatalogueImageToken({
    registry: options.registry,
    targetType: options.targetType,
    targetId: options.targetId,
    alt: fields.alt,
    detailId: fields.detail_id || "",
    caption: fields.caption || "",
    summary: fields.summary || "",
    placement: fields.placement || "",
    fillWidth: typeof fillWidth === "boolean" ? fillWidth : null
  });
  if (!serialized || serialized.slice(serialized.indexOf("|") + 1, -2) !== rawQuery) return null;
  return {
    alt: plainText(fields.alt),
    detailId: normalizeCatalogueDetailId(fields.detail_id),
    caption: plainText(fields.caption),
    summary: summaryText(fields.summary),
    placement: cleanString(fields.placement),
    fillWidth: typeof fillWidth === "boolean" ? fillWidth : null
  };
}

export function parseCatalogueToken(raw, options = {}) {
  var source = String(raw || "");
  if (!source.startsWith("[[") || !source.endsWith("]]") || /[\r\n]/.test(source)) return null;
  var body = source.slice(2, -2);
  var separator = body.indexOf("|");
  if (separator < 0) return null;
  var identity = body.slice(0, separator).split(":");
  var imagePresentation = identity.length === 4 && identity[1] === "image";
  if (identity.length !== 3 && !imagePresentation) return null;
  var family = identity[0];
  var targetType = identity[identity.length - 2];
  var targetId = identity[identity.length - 1];
  var rawFields = body.slice(separator + 1);
  var imageFields = imagePresentation
    ? parseCatalogueImageFields(rawFields, {
        registry: options.registry,
        targetType: targetType,
        targetId: targetId
      })
    : null;
  var title = imagePresentation
    ? imageFields && (imageFields.caption || imageFields.alt)
    : unescapeTitle(rawFields);
  if (
    family !== "catalogue"
    || !LEXICAL_KEY_PATTERN.test(family)
    || !LEXICAL_KEY_PATTERN.test(targetType)
    || !LEXICAL_ID_PATTERN.test(targetId)
    || !title
  ) return null;
  var definition = targetDefinition(options.registry, family, targetType);
  var supported = Boolean(definition);
  if (supported && definition.idPolicy.canonicalPattern) {
    var canonicalPattern = new RegExp(definition.idPolicy.canonicalPattern);
    if (!canonicalPattern.test(targetId)) return null;
  }
  var start = Number.isInteger(options.start) ? options.start : 0;
  return {
    raw: source,
    family: family,
    targetType: targetType,
    targetId: targetId,
    title: title,
    start: start,
    end: start + source.length,
    supported: supported,
    activatable: supported,
    presentation: imagePresentation ? "image" : "text",
    alt: imageFields ? imageFields.alt : "",
    caption: imageFields ? imageFields.caption : "",
    summary: imageFields ? imageFields.summary : "",
    placement: imageFields ? imageFields.placement : "",
    fillWidth: imageFields ? imageFields.fillWidth : null,
    detailId: imageFields ? imageFields.detailId : ""
  };
}

function outsideInlineCodeRanges(text, start, end) {
  var ranges = [];
  var index = start;
  while (index < end) {
    var match = /`+/.exec(text.slice(index, end));
    if (!match) {
      ranges.push([index, end]);
      break;
    }
    var tickStart = index + match.index;
    var tickEnd = tickStart + match[0].length;
    if (tickStart > index) ranges.push([index, tickStart]);
    var close = text.indexOf(match[0], tickEnd);
    if (close < 0 || close >= end) break;
    index = close + match[0].length;
  }
  return ranges;
}

function outsideCommentRanges(text, start, end, inComment) {
  var ranges = [];
  var index = start;
  var comment = Boolean(inComment);
  while (index < end) {
    if (comment) {
      var close = text.indexOf("-->", index);
      if (close < 0 || close >= end) return { ranges: ranges, inComment: true };
      index = close + 3;
      comment = false;
      continue;
    }
    var opening = text.indexOf("<!--", index);
    var segmentEnd = opening < 0 || opening >= end ? end : opening;
    ranges = ranges.concat(outsideInlineCodeRanges(text, index, segmentEnd));
    if (segmentEnd === end) return { ranges: ranges, inComment: false };
    index = opening + 4;
    comment = true;
  }
  return { ranges: ranges, inComment: comment };
}

export function semanticTokenTextRanges(markdown) {
  var ranges = [];
  var lines = String(markdown || "").match(/[^\n]*\n|[^\n]+$/g) || [];
  var offset = 0;
  var inFence = false;
  var fenceCharacter = "";
  var inComment = false;
  lines.forEach(function (line) {
    var fence = /^ {0,3}(`{3,}|~{3,})/.exec(line);
    if (fence) {
      if (inFence && fence[1][0] === fenceCharacter) {
        inFence = false;
        fenceCharacter = "";
      } else if (!inFence) {
        inFence = true;
        fenceCharacter = fence[1][0];
      }
    } else if (!inFence) {
      var result = outsideCommentRanges(markdown, offset, offset + line.length, inComment);
      ranges = ranges.concat(result.ranges);
      inComment = result.inComment;
    }
    offset += line.length;
  });
  return ranges;
}

export function parseCatalogueTokens(markdown, options = {}) {
  var source = String(markdown || "");
  if (source.indexOf("[[catalogue:") < 0) return [];
  var tokens = [];
  semanticTokenTextRanges(source).forEach(function (range) {
    var index = range[0];
    while (index < range[1]) {
      var opening = source.indexOf("[[catalogue:", index);
      if (opening < 0 || opening >= range[1]) break;
      var closing = semanticTokenClosingIndex(source, opening + 2);
      if (closing < 0 || closing + 2 > range[1]) break;
      var token = parseCatalogueToken(source.slice(opening, closing + 2), {
        registry: options.registry,
        start: opening
      });
      if (token) tokens.push(token);
      index = closing + 2;
    }
  });
  return tokens;
}

export function catalogueTokenAtSelection(tokens, selection) {
  var start = Number(selection && selection.start);
  var end = Number(selection && selection.end);
  var active = (Array.isArray(tokens) ? tokens : []).filter(function (token) {
    if (!token.activatable) return false;
    if (start === end) return token.start < start && start < token.end;
    return token.start === start && token.end === end;
  });
  return active.length === 1 ? active[0] : null;
}
