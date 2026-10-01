/** Locate the Markdown body without interpreting front-matter fields. Unclosed headers stay literal. */
export function sourceBodyStart(source) {
  var text = String(source || "");
  var opening = /^---[ \t]*\r?\n/.exec(text);
  if (!opening) return 0;
  var closing = /^---[ \t]*(?:\r?\n|$)/m.exec(text.slice(opening[0].length));
  return closing ? opening[0].length + closing.index + closing[0].length : text.length;
}
