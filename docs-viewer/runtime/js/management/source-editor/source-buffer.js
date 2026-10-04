/** Locate the Markdown body without interpreting front-matter fields. Unclosed headers stay literal. */
export function sourceBodyStart(source) {
  var text = String(source || "");
  var opening = /^---[ \t]*\r?\n/.exec(text);
  if (!opening) return 0;
  var closing = /^---[ \t]*(?:\r?\n|$)/m.exec(text.slice(opening[0].length));
  return closing ? opening[0].length + closing.index + closing[0].length : text.length;
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
