/** Locate the Markdown body without interpreting front-matter fields. Unclosed headers stay literal. */
export function sourceBodyStart(source) {
  var text = String(source || "");
  var opening = /^---[ \t]*\r?\n/.exec(text);
  if (!opening) return 0;
  var closing = /^---[ \t]*(?:\r?\n|$)/m.exec(text.slice(opening[0].length));
  return closing ? opening[0].length + closing.index + closing[0].length : text.length;
}

/** Give Title authoring feedback locally; the service owns complete header syntax. */
export function sourceTitleError(source) {
  var match = /^---[ \t]*\r?\n([\s\S]*?)\r?\n---[ \t]*(?:\r?\n|$)/.exec(String(source || ""));
  if (!match) return "";
  var titles = [];
  var summaryIndent = null;
  match[1].split(/\r?\n/).forEach(function (line) {
    var trimmed = line.trim();
    var indent = line.length - line.trimStart().length;
    if (summaryIndent !== null) {
      if (!trimmed || indent > summaryIndent) return;
      summaryIndent = null;
    }
    if (!trimmed || trimmed.startsWith("#")) return;
    var pair = /^([^:]+):([\s\S]*)$/.exec(trimmed);
    if (!pair) return;
    var key = pair[1].trim();
    var raw = pair[2].trim();
    if (key === "summary" && /^[|>]/.test(raw)) summaryIndent = indent;
    if (key === "title") titles.push(raw);
  });
  if (!titles.length) return "Enter a nonblank Title in front matter.";
  if (titles.length !== 1) return "";
  var title = titles[0];
  if (title.startsWith('"')) {
    try { title = JSON.parse(title); } catch (_error) { return ""; }
  } else if (title.startsWith("'")) {
    if (title.length < 2 || !title.endsWith("'")) return "";
    title = title.slice(1, -1).replace(/\\'/g, "'");
  } else if (/^(?:true|false|-?\d+)$/i.test(title)) {
    return "Title must be text; quote numeric or boolean titles.";
  }
  return typeof title === "string" && title.trim() ? "" : "Enter a nonblank Title in front matter.";
}

/** Set the canonical assignment without reserializing unrelated front-matter lines. */
export function sourceWithThumbnail(source) {
  var text = String(source || "");
  var end = sourceBodyStart(text);
  var header = text.slice(0, end);
  var newline = text.includes("\r\n") ? "\r\n" : "\n";
  if (/^[ \t]*thumbnail[ \t]*:/m.test(header)) {
    header = header.replace(/^[ \t]*thumbnail[ \t]*:[^\r\n]*/m, "thumbnail: true");
  } else {
    var closing = header.lastIndexOf("---");
    header = header.slice(0, closing) + "thumbnail: true" + newline + header.slice(closing);
  }
  return header + text.slice(end);
}
