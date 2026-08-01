import { openLocalTarget } from "../docs-viewer-management-client.js";

var mountedActivationRoots = new WeakSet();
function hasControl(value) { return Array.from(value).some(function (character) { return character.charCodeAt(0) < 32 || character.charCodeAt(0) === 127; }); }

function absoluteParts(value) {
  if (!value.startsWith("/") || value.includes("\\") || hasControl(value)) return null;
  var parts = value.slice(1).split("/");
  return parts.some(function (part) { return !part || part === "." || part === ".."; }) ? null : parts;
}

function shellUnescape(value) {
  var output = "";
  for (var index = 0; index < value.length; index += 1) {
    if (value[index] !== "\\") { output += value[index]; continue; }
    if (index + 1 >= value.length) return null;
    output += value[index += 1];
  }
  return output;
}

function encodedTarget(parts) {
  try {
    return parts.map(function (part) {
      return encodeURIComponent(part).replace(/[!'()*]/g, function (character) {
        return "%" + character.charCodeAt(0).toString(16).toUpperCase();
      });
    }).join("/");
  } catch (_error) { return ""; }
}

export function normalizeLocalFolderPath(value, basePath) {
  if (typeof value !== "string" || !value || value !== value.trim() || hasControl(value)) return null;
  var absolute;
  if (/^file:/i.test(value)) {
    var fileMatch = value.match(/^file:(?:\/\/([^/?#]*))?(\/[^?#]*)$/i);
    if (!fileMatch || !["", "localhost"].includes(String(fileMatch[1] || "").toLowerCase())) return null;
    try {
      absolute = decodeURIComponent(fileMatch[2]);
    } catch (_error) { return null; }
  } else {
    if (!value.startsWith("/") || value.includes("?") || value.includes("#")) return null;
    absolute = shellUnescape(value);
  }
  var candidate = absolute && absoluteParts(absolute);
  var base = typeof basePath === "string" && absoluteParts(basePath);
  if (!candidate || !base || candidate.length === base.length) return null;
  if (!base.every(function (part, index) { return candidate[index] === part; })) return null;
  var relativeParts = candidate.slice(base.length);
  var target = encodedTarget(relativeParts);
  if (!target) return null;
  var label = relativeParts[relativeParts.length - 1];
  var escapedLabel = label.replace(/\\/g, "\\\\").replace(/\[/g, "\\[").replace(/\]/g, "\\]");
  return { target: relativeParts.join("/"), encodedTarget: target, label: label, markdown: "[" + escapedLabel + "](dlf-local:" + target + ")" };
}

export function markdownRangeIsOrdinary(markdown, start, end) {
  var source = String(markdown || "");
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end < start || end > source.length) return false;
  var offset = 0;
  var fence = "";
  var lines = source.split("\n");
  for (var index = 0; index < lines.length; index += 1) {
    var line = lines[index];
    var marker = line.match(/^ {0,3}(`{3,}|~{3,})/);
    var lineEnd = offset + line.length + (index < lines.length - 1 ? 1 : 0);
    var active = start === end ? start >= offset && start <= lineEnd : end > offset && start < lineEnd;
    if (active && (fence || marker || line.startsWith("    ") || line.startsWith("\t"))) return false;
    if (marker) fence = fence && marker[1][0] === fence ? "" : (fence || marker[1][0]);
    offset = lineEnd;
  }
  var prefix = source.slice(0, start);
  var selected = source.slice(start, end);
  var lowerPrefix = prefix.toLowerCase();
  if (prefix.lastIndexOf("<!--") > prefix.lastIndexOf("-->") || lowerPrefix.lastIndexOf("<pre") > lowerPrefix.lastIndexOf("</pre")) return false;
  if (/<!--|-->|<pre\b|<\/pre/i.test(selected) || ((prefix.slice(prefix.lastIndexOf("\n") + 1).match(/`+/g) || []).length % 2) || selected.includes("`")) return false;
  return true;
}

export function localFolderPasteReplacement(options) {
  var settings = options || {};
  var normalized = normalizeLocalFolderPath(settings.text, settings.basePath);
  return normalized && markdownRangeIsOrdinary(settings.markdown, settings.start, settings.end) ? normalized.markdown : "";
}

export function mountLocalFolderLinkActivation(context) {
  var settings = context || {}, content = settings.content;
  if (!content || mountedActivationRoots.has(content)) return;
  mountedActivationRoots.add(content);
  content.addEventListener("click", function (event) {
    var link = event.target && event.target.closest && event.target.closest("[data-docs-viewer-local-target]");
    if (!link || !content.contains(link)) return;
    event.preventDefault();
    var target = String(link.getAttribute("data-docs-viewer-local-target") || "");
    if (!target) return;
    openLocalTarget(target, {
      baseUrl: settings.managementService && settings.managementService.baseUrl,
      fetch: content.ownerDocument.defaultView.fetch.bind(content.ownerDocument.defaultView)
    }).then(function (payload) {
      if (typeof settings.setStatus === "function") settings.setStatus(payload.summary_text || "Local target opened.", false);
    }).catch(function (error) {
      if (typeof settings.setStatus === "function") settings.setStatus(error.message || "Local target could not be opened.", true);
    });
  });
}
