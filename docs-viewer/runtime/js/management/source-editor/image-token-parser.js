import { decodeImageValue, encodeImageValue, parseSourceTokens } from "./catalogue-token-parser.js";

var FIELDS = new Set(["alt", "caption", "summary", "placement", "fill_width"]);
var PLACEMENTS = new Set(["full", "left", "right"]);
var TEXT_SPACE = /[\t\n\v\f\r \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+/g;

function imageText(value, multiline) {
  function line(text) {
    return Array.from(text).map(function (character) {
      var code = character.charCodeAt(0);
      return code >= 28 && code <= 31 ? " " : character;
    }).join("").replace(TEXT_SPACE, " ").replace(/^ +| +$/g, "");
  }
  return multiline
    ? value.replace(/\r\n?/g, "\n").split("\n").map(line).join("\n").replace(/^[ \n]+|[ \n]+$/g, "")
    : line(value);
}

function encodePath(value) {
  return value.split("/").map(encodeImageValue).join("/");
}

function validPath(value) {
  return /^docs\/(?:collections\/[a-z0-9][a-z0-9-]*\/)?(?:img|svg)\/.+$/.test(value)
    && !Array.from(value).some(function (character) {
      var code = character.charCodeAt(0);
      return code < 32 || code === 127 || character === "\\";
    })
    && value.split("/").every(function (part) { return part && part !== "." && part !== ".."; });
}

/** Serialize decoded identity and literal authored fields; invalid inputs return empty text. */
export function serializeImageToken(options = {}) {
  var caption = options.caption === undefined ? "" : options.caption;
  var summary = options.summary === undefined ? "" : options.summary;
  if (typeof options.mediaPath !== "string" || !validPath(options.mediaPath)
    || [options.alt, caption, summary, options.placement].some(function (value) { return typeof value !== "string"; })
    || typeof options.fillWidth !== "boolean") return "";
  var alt = imageText(options.alt, false);
  var placement = imageText(options.placement, false).toLowerCase();
  caption = imageText(caption, false);
  summary = imageText(summary, true);
  if (!alt || !PLACEMENTS.has(placement)) return "";
  var fields = [["alt", alt]];
  if (caption) fields.push(["caption", caption]);
  if (summary) fields.push(["summary", summary]);
  fields.push(["placement", placement], ["fill_width", options.fillWidth ? "true" : "false"]);
  try {
    return "[[image:" + encodePath(options.mediaPath) + "|" + fields.map(function (field) {
      return field[0] + "=" + encodeImageValue(field[1]);
    }).join("&") + "]]";
  } catch (_error) {
    return "";
  }
}

/** Parse only the canonical source form, preserving source ranges without applying defaults. */
export function parseImageToken(raw, options = {}) {
  if (typeof raw !== "string" || !raw.startsWith("[[image:") || !raw.endsWith("]]") || /[\r\n]/.test(raw)) return null;
  var separator = raw.indexOf("|", 8);
  if (separator < 0) return null;
  var mediaPath;
  try {
    mediaPath = decodeURIComponent(raw.slice(8, separator));
    if (encodePath(mediaPath) !== raw.slice(8, separator)) return null;
  } catch (_error) { return null; }
  var fields = {};
  for (var pair of raw.slice(separator + 1, -2).split("&")) {
    var split = pair.indexOf("=");
    if (split < 1) return null;
    var key = pair.slice(0, split);
    if (!FIELDS.has(key) || Object.prototype.hasOwnProperty.call(fields, key)) return null;
    var value = decodeImageValue(pair.slice(split + 1));
    if (value === null || !value) return null;
    fields[key] = value;
  }
  if (!["true", "false"].includes(fields.fill_width)) return null;
  var token = {
    mediaPath: mediaPath, alt: fields.alt, caption: fields.caption || "", summary: fields.summary || "",
    placement: fields.placement, fillWidth: fields.fill_width === "true"
  };
  if (serializeImageToken(token) !== raw) return null;
  var start = Number.isInteger(options.start) ? options.start : 0;
  return Object.assign(token, { raw: raw, family: "image", presentation: "image", supported: true,
    activatable: true, start: start, end: start + raw.length });
}

/** Return active canonical occurrences, preserving offsets in the supplied body buffer. */
export function parseImageTokens(markdown) {
  return parseSourceTokens(markdown, parseImageToken);
}
