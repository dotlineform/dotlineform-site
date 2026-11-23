export const IMAGE_DETAIL_COMMENT = "<!-- dotlineform:image-detail -->";

const IMAGE_DETAIL_COMMENT_PATTERN = /^<!--\s*dotlineform:image-detail\s*-->$/;
const IMAGE_DETAIL_PREFIX = IMAGE_DETAIL_COMMENT + "\n\n";

/** Locate the preceding directive for a standalone image in the captured source. */
export function imageDetailAtOccurrence(source, capture) {
  const lineStart = source.lastIndexOf("\n", capture.start - 1) + 1;
  const nextLine = source.indexOf("\n", capture.end);
  const lineEnd = nextLine < 0 ? source.length : nextLine;
  if (source.slice(lineStart, capture.start).trim() || source.slice(capture.end, lineEnd).trim()) return null;

  const preceding = source.slice(0, lineStart).trimEnd();
  const commentStart = preceding.lastIndexOf("<!--");
  if (commentStart < 0 || !IMAGE_DETAIL_COMMENT_PATTERN.test(preceding.slice(commentStart))) {
    return { lineStart, directiveStart: null };
  }
  const directiveLineStart = preceding.lastIndexOf("\n", commentStart - 1) + 1;
  const indent = preceding.slice(directiveLineStart, commentStart);
  return { lineStart, directiveStart: /^ {0,3}$/.test(indent) ? directiveLineStart : null };
}

/** Update the image and its attached directive as one captured replacement. */
export function planImageDetailReplacement(source, capture, markdown, existingDetail, enabled) {
  if (existingDetail) {
    const { lineStart, directiveStart } = existingDetail;
    const hadDetail = directiveStart !== null;
    if (enabled === hadDetail) return { capture, markdown };

    const start = hadDetail ? directiveStart : lineStart;
    const indent = source.slice(lineStart, capture.start);
    return {
      capture: { ...capture, start, text: source.slice(start, capture.end) },
      markdown: (enabled ? IMAGE_DETAIL_PREFIX : "") + indent + markdown
    };
  }
  if (!enabled) return { capture, markdown };

  const leadingNewlines = source.slice(0, capture.start).match(/\n*$/)[0].length;
  const trailingNewlines = source.slice(capture.end).match(/^\n*/)[0].length;
  return {
    capture,
    markdown: "\n".repeat(capture.start ? Math.max(0, 2 - leadingNewlines) : 0)
      + IMAGE_DETAIL_PREFIX + markdown
      + "\n".repeat(Math.max(0, 2 - trailingNewlines))
  };
}
