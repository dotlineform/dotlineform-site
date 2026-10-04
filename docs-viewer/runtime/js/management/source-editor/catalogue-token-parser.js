var LEXICAL_KEY_PATTERN = /^[a-z][a-z0-9-]*$/;
var LEXICAL_ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;
var IMAGE_FIELDS = new Set(["use_work_title_caption", "include_work_metadata", "summary", "placement", "fill_width"]);
var IMAGE_PLACEMENTS = new Set(["full", "left", "right"]);
var MEDIA_TARGET_PATTERNS = { work: /^[0-9]{5}$/, gallery: /^(?:[0-9]{3}|[1-9][0-9]{3,})$/ };

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function summaryText(value) {
  return String(value == null ? "" : value)
    .replace(/\r\n?/g, "\n")
    .split("\n")
    .map(function (line) { return line.trim().replace(/\s+/g, " "); })
    .join("\n")
    .trim();
}

export function encodeImageValue(value) {
  return encodeURIComponent(value).replace(/[!'()*]/g, function (character) {
    return "%" + character.charCodeAt(0).toString(16).toUpperCase();
  });
}

export function decodeImageValue(value) {
  try {
    var decoded = decodeURIComponent(value);
    return encodeImageValue(decoded) === value ? decoded : null;
  } catch (_error) {
    return null;
  }
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

export function serializeCatalogueMediaToken(options = {}) {
  var targetType = cleanString(options.targetType);
  var targetId = cleanString(options.targetId);
  var title = cleanString(options.title);
  if (!title || /[\r\n]/.test(title)) return "";
  if (
    !LEXICAL_KEY_PATTERN.test(targetType)
    || !LEXICAL_ID_PATTERN.test(targetId)
  ) return "";
  var definition = targetDefinition(options.registry, "catalogue", targetType);
  if (definition && definition.idPolicy.canonicalPattern) {
    var canonicalPattern = new RegExp(definition.idPolicy.canonicalPattern);
    if (!canonicalPattern.test(targetId)) return "";
  }
  var targetPattern = Object.prototype.hasOwnProperty.call(MEDIA_TARGET_PATTERNS, targetType) ? MEDIA_TARGET_PATTERNS[targetType] : null;
  if (!targetPattern || !targetPattern.test(targetId)) return "";
  return "[[catalogue:media:" + targetType + ":" + targetId + "|" + escapedTitle(title) + "]]";
}

export function serializeCatalogueImageToken(options = {}) {
  var targetType = cleanString(options.targetType);
  var targetId = cleanString(options.targetId);
  if (targetType !== "work" || !/^\d{5}$/.test(targetId)) return "";
  if (
    !LEXICAL_KEY_PATTERN.test(targetType)
    || !LEXICAL_ID_PATTERN.test(targetId)
    || typeof options.useWorkTitleCaption !== "boolean"
    || typeof options.includeWorkMetadata !== "boolean"
    || typeof options.fillWidth !== "boolean"
    || (options.summary !== undefined && typeof options.summary !== "string")
  ) return "";
  var definition = targetDefinition(options.registry, "catalogue", targetType);
  if (definition && definition.idPolicy.canonicalPattern) {
    var canonicalPattern = new RegExp(definition.idPolicy.canonicalPattern);
    if (!canonicalPattern.test(targetId)) return "";
  }
  var summary = summaryText(options.summary);
  var placement = cleanString(options.placement).toLowerCase();
  if (!IMAGE_PLACEMENTS.has(placement)) return "";
  var fields = [
    ["use_work_title_caption", options.useWorkTitleCaption ? "true" : "false"],
    ["include_work_metadata", options.includeWorkMetadata ? "true" : "false"]
  ];
  if (summary) fields.push(["summary", summary]);
  fields.push(["placement", placement], ["fill_width", options.fillWidth ? "true" : "false"]);
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
  if (["use_work_title_caption", "include_work_metadata", "placement", "fill_width"].some(function (key) {
    return !Object.prototype.hasOwnProperty.call(fields, key);
  })) return null;
  if (["use_work_title_caption", "include_work_metadata", "fill_width"].some(function (key) {
    return fields[key] !== "true" && fields[key] !== "false";
  })) return null;
  var serialized = serializeCatalogueImageToken({
    registry: options.registry,
    targetType: options.targetType,
    targetId: options.targetId,
    useWorkTitleCaption: fields.use_work_title_caption === "true",
    includeWorkMetadata: fields.include_work_metadata === "true",
    summary: fields.summary || "",
    placement: fields.placement,
    fillWidth: fields.fill_width === "true"
  });
  if (!serialized || serialized.slice(serialized.indexOf("|") + 1, -2) !== rawQuery) return null;
  return {
    useWorkTitleCaption: fields.use_work_title_caption === "true",
    includeWorkMetadata: fields.include_work_metadata === "true",
    summary: summaryText(fields.summary),
    placement: cleanString(fields.placement),
    fillWidth: fields.fill_width === "true"
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
  var mediaPresentation = identity.length === 4 && identity[1] === "media";
  if (!imagePresentation && !mediaPresentation) return null;
  var family = identity[0];
  var targetType = identity[2];
  var targetId = identity[3];
  var rawFields = body.slice(separator + 1);
  var imageFields = imagePresentation
    ? parseCatalogueImageFields(rawFields, {
        registry: options.registry,
        targetType: targetType,
        targetId: targetId
      })
    : null;
  var title = imagePresentation
    ? ""
    : unescapeTitle(rawFields);
  if (mediaPresentation && !serializeCatalogueMediaToken({ targetType: targetType, targetId: targetId, title: title })) return null;
  if (
    family !== "catalogue"
    || !LEXICAL_KEY_PATTERN.test(family)
    || !LEXICAL_KEY_PATTERN.test(targetType)
    || !LEXICAL_ID_PATTERN.test(targetId)
    || (!imagePresentation && !title)
    || (imagePresentation && !imageFields)
  ) return null;
  var definition = targetDefinition(options.registry, family, targetType);
  var supported = options.registry ? Boolean(definition)
    : imagePresentation ? targetType === "work" : Object.prototype.hasOwnProperty.call(MEDIA_TARGET_PATTERNS, targetType);
  if (definition && definition.idPolicy.canonicalPattern) {
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
    presentation: imagePresentation ? "image" : "media",
    useWorkTitleCaption: imageFields ? imageFields.useWorkTitleCaption : null,
    includeWorkMetadata: imageFields ? imageFields.includeWorkMetadata : null,
    summary: imageFields ? imageFields.summary : "",
    placement: imageFields ? imageFields.placement : "",
    fillWidth: imageFields ? imageFields.fillWidth : null
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

function outsideLiteralRanges(text, start, end, inLiteral) {
  var ranges = [];
  var index = start;
  var literal = inLiteral;
  while (index < end) {
    if (literal) {
      var close = (literal === "comment" ? /-->/ : /<\/pre\s*>/i).exec(text.slice(index, end));
      if (!close) return { ranges: ranges, inLiteral: literal };
      index += close.index + close[0].length;
      literal = "";
      continue;
    }
    var codeRanges = outsideInlineCodeRanges(text, index, end);
    var opening = null;
    for (var range of codeRanges) {
      var marker = /<!--|<pre\b/i.exec(text.slice(range[0], range[1]));
      if (marker) {
        opening = { index: range[0] + marker.index, kind: marker[0] === "<!--" ? "comment" : "pre" };
        if (opening.index > range[0]) ranges.push([range[0], opening.index]);
        break;
      }
      ranges.push(range);
    }
    if (!opening) return { ranges: ranges, inLiteral: "" };
    index = opening.index + 4;
    literal = opening.kind;
  }
  return { ranges: ranges, inLiteral: literal };
}

function tokenOpeningIsEscaped(source, opening) {
  var escapes = /\\+$/.exec(source.slice(0, opening));
  return Boolean(escapes && escapes[0].length % 2);
}

/** Authored token fields are plain text; their punctuation cannot open Markdown literal contexts. */
function tokenContextSource(markdown) {
  var source = String(markdown || "");
  var parts = [];
  var start = 0;
  var index = 0;
  while (index < source.length) {
    var opening = source.indexOf("[[catalogue:", index);
    if (opening < 0) break;
    var closing = semanticTokenClosingIndex(source, opening + 2);
    if (closing < 0) break;
    var end = closing + 2;
    if (!tokenOpeningIsEscaped(source, opening) && parseCatalogueToken(source.slice(opening, end))) {
      parts.push(source.slice(start, opening), "x".repeat(end - opening));
      start = end;
    }
    index = end;
  }
  return parts.join("") + source.slice(start);
}

export function semanticTokenTextRanges(markdown) {
  var contextSource = tokenContextSource(markdown);
  var ranges = [];
  var lines = contextSource.match(/[^\n]*\n|[^\n]+$/g) || [];
  var offset = 0;
  var inFence = false;
  var fenceCharacter = "";
  var inLiteral = "";
  var fenceLength = 0;
  lines.forEach(function (line) {
    var fence = /^ {0,3}(`{3,}|~{3,})/.exec(line);
    if (fence && !inLiteral) {
      if (inFence && fence[1][0] === fenceCharacter && fence[1].length >= fenceLength
        && /^[ \t\r\n]*$/.test(line.slice(fence[0].length))) {
        inFence = false;
        fenceCharacter = "";
      } else if (!inFence) {
        inFence = true;
        fenceCharacter = fence[1][0];
        fenceLength = fence[1].length;
      }
    } else if (!inFence && (inLiteral || !/^(?: {4}|\t)/.test(line))) {
      var result = outsideLiteralRanges(contextSource, offset, offset + line.length, inLiteral);
      ranges = ranges.concat(result.ranges);
      inLiteral = result.inLiteral;
    }
    offset += line.length;
  });
  return ranges;
}

/** Scan any semantic family through the shared inactive-source boundaries. */
export function parseSourceTokens(markdown, parseToken, options = {}) {
  var source = String(markdown || "");
  if (source.indexOf("[[") < 0) return [];
  var tokens = [];
  semanticTokenTextRanges(source).forEach(function (range) {
    var index = range[0];
    while (index < range[1]) {
      var opening = source.indexOf("[[", index);
      if (opening < 0 || opening >= range[1]) break;
      if (tokenOpeningIsEscaped(source, opening)) { index = opening + 2; continue; }
      var closing = semanticTokenClosingIndex(source, opening + 2);
      if (closing < 0 || closing + 2 > range[1]) break;
      var token = parseToken(source.slice(opening, closing + 2), {
        registry: options.registry,
        start: opening
      });
      if (token) tokens.push(token);
      index = closing + 2;
    }
  });
  return tokens;
}

export function parseCatalogueTokens(markdown, options = {}) {
  return parseSourceTokens(markdown, parseCatalogueToken, options);
}

/** Activate an exact occurrence selection or a caret strictly inside one supported token. */
export function sourceTokenAtSelection(tokens, selection) {
  var start = Number(selection && selection.start);
  var end = Number(selection && selection.end);
  var active = (Array.isArray(tokens) ? tokens : []).filter(function (token) {
    if (!token.activatable) return false;
    if (start === end) return token.start < start && start < token.end;
    return token.start === start && token.end === end;
  });
  return active.length === 1 ? active[0] : null;
}
