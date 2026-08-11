import {
  semanticTokenClosingIndex,
  semanticTokenTextRanges
} from "./catalogue-token-parser.js";

var TAG_ID_PATTERN = /^[a-z0-9][a-z0-9-]*$/;

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function escapedTitle(value) {
  return value.replace(/\\/g, "\\\\").replace(/\|/g, "\\|").replace(/\]/g, "\\]");
}

function unescapeTitle(value) {
  var output = "";
  for (var index = 0; index < value.length; index += 1) {
    if (value[index] !== "\\") {
      output += value[index];
      continue;
    }
    var escaped = value[index + 1];
    if (escaped !== "\\" && escaped !== "|" && escaped !== "]") return null;
    output += escaped;
    index += 1;
  }
  return cleanString(output) || null;
}

function tagDefinition(registry) {
  var family = registry && registry.familiesById
    ? registry.familiesById.get("tag")
    : null;
  return family && family.targetTypesById
    ? family.targetTypesById.get("tag")
    : null;
}

export function selectedTextForTagTitle(value) {
  return cleanString(value).replace(/\s+/g, " ");
}

export function serializeTagToken(options = {}) {
  var targetId = cleanString(options.targetId);
  var title = cleanString(options.title);
  if (!TAG_ID_PATTERN.test(targetId) || !title || /[\r\n]/.test(title)) return "";
  var definition = tagDefinition(options.registry);
  if (
    definition
    && definition.idPolicy.canonicalPattern
    && !(new RegExp(definition.idPolicy.canonicalPattern)).test(targetId)
  ) return "";
  return "[[tag:tag:" + targetId + "|" + escapedTitle(title) + "]]";
}

export function buildTagToken(options = {}) {
  return serializeTagToken(options);
}

export function parseTagToken(raw, options = {}) {
  var source = String(raw || "");
  if (!source.startsWith("[[tag:tag:") || !source.endsWith("]]")) return null;
  if (/[\r\n]/.test(source)) return null;
  var body = source.slice(2, -2);
  var separator = body.indexOf("|");
  var identity = separator < 0 ? [] : body.slice(0, separator).split(":");
  var targetId = identity[2] || "";
  var title = separator < 0 ? null : unescapeTitle(body.slice(separator + 1));
  if (
    identity.length !== 3
    || identity[0] !== "tag"
    || identity[1] !== "tag"
    || !TAG_ID_PATTERN.test(targetId)
    || !title
  ) return null;
  var definition = tagDefinition(options.registry);
  if (
    definition
    && definition.idPolicy.canonicalPattern
    && !(new RegExp(definition.idPolicy.canonicalPattern)).test(targetId)
  ) return null;
  var start = Number.isInteger(options.start) ? options.start : 0;
  return {
    raw: source,
    family: "tag",
    targetType: "tag",
    targetId: targetId,
    title: title,
    start: start,
    end: start + source.length,
    supported: Boolean(definition),
    activatable: Boolean(definition),
    presentation: "text"
  };
}

export function parseTagTokens(markdown, options = {}) {
  var source = String(markdown || "");
  if (source.indexOf("[[tag:tag:") < 0) return [];
  var tokens = [];
  semanticTokenTextRanges(source).forEach(function (range) {
    var index = range[0];
    while (index < range[1]) {
      var opening = source.indexOf("[[tag:tag:", index);
      if (opening < 0 || opening >= range[1]) break;
      var closing = semanticTokenClosingIndex(source, opening + 2);
      if (closing < 0 || closing + 2 > range[1]) break;
      var token = parseTagToken(source.slice(opening, closing + 2), {
        registry: options.registry,
        start: opening
      });
      if (token) tokens.push(token);
      index = closing + 2;
    }
  });
  return tokens;
}

export function tagTokenAtSelection(tokens, selection) {
  var start = Number(selection && selection.start);
  var end = Number(selection && selection.end);
  var active = (Array.isArray(tokens) ? tokens : []).filter(function (token) {
    if (!token.activatable) return false;
    if (start === end) return token.start < start && start < token.end;
    return token.start === start && token.end === end;
  });
  return active.length === 1 ? active[0] : null;
}
