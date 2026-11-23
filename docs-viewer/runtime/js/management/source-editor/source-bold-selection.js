import MarkdownIt from "../vendor/markdown-it/markdown-it.mjs";
import { parseImageToken } from "./image-token-parser.js";
import { sourceBodyStart } from "./source-buffer.js";
import { parseCatalogueToken, parseSourceTokens } from "./source-token-parser.js";

const markdown = new MarkdownIt("commonmark").enable("table");
const emphasisPositions = new WeakMap();
const tableRowRanges = new WeakMap();

// Markdown-it 15 has block line maps, but no column maps for table cells or emphasis.
// Collect positions from the existing rules before they discard those offsets.
const emphasis = markdown.inline.ruler.__rules__.find(rule => rule.name === "emphasis").fn;
markdown.inline.ruler.at("emphasis", (state, silent) => {
  const position = state.pos;
  const firstDelimiter = state.delimiters.length;
  if (!emphasis(state, silent)) return false;
  for (let index = firstDelimiter; index < state.delimiters.length; index += 1) {
    const token = state.tokens[state.delimiters[index].token];
    emphasisPositions.set(token, position + index - firstDelimiter);
  }
  return true;
});

const { fn: table, alt: tableAlternatives } = markdown.block.ruler.__rules__.find(rule => rule.name === "table");
markdown.block.ruler.at("table", (state, startLine, endLine, silent) => {
  const firstToken = state.tokens.length;
  if (!table(state, startLine, endLine, silent)) return false;
  for (let index = firstToken; index < state.tokens.length; index += 1) {
    const token = state.tokens[index];
    if (token.type !== "tr_open") continue;
    const [line] = token.map;
    tableRowRanges.set(token, [state.bMarks[line] + state.tShift[line], state.eMarks[line]]);
  }
  return true;
}, { alt: tableAlternatives });

function lineOffsets(source) {
  const starts = [0];
  for (const newline of source.matchAll(/\n/g)) starts.push(newline.index + 1);
  starts.push(source.length + 1);
  return starts;
}

function textPositions(source, starts, inline) {
  const positions = [];
  const lines = inline.content.split("\n");
  for (const [index, content] of lines.entries()) {
    const line = inline.map[0] + index;
    const start = starts[line];
    const raw = source.slice(start, starts[line + 1] - 1);
    const offset = raw.lastIndexOf(content);
    if (offset < 0) return null;
    if (index) positions.push(start - 1);
    for (let column = 0; column < content.length; column += 1) {
      positions.push(start + offset + column);
    }
  }
  return positions;
}

function tableCells(source, [start, end]) {
  const row = source.slice(start, end).trimEnd();
  const cells = [];
  let cellStart = 0;
  for (let column = 0; column <= row.length; column += 1) {
    if (column < row.length && (row[column] !== "|" || row[column - 1] === "\\")) continue;
    if (column !== 0 && cellStart !== row.length) {
      let content = "";
      const positions = [];
      const raw = row.slice(cellStart, column);
      const trimmed = raw.trim();
      const offset = start + cellStart + raw.length - raw.trimStart().length;
      for (let index = 0; index < trimmed.length; index += 1) {
        if (trimmed[index] === "\\" && trimmed[index + 1] === "|") index += 1;
        positions.push(offset + index);
        content += trimmed[index];
      }
      cells.push({ content, positions });
    }
    cellStart = column + 1;
  }
  return cells;
}

function collectBoldSpans(children, positions, spans) {
  const openings = [];
  let htmlCode = 0;
  for (const token of children) {
    if (token.type === "html_inline") {
      if (/^<code(?:\s|>)/i.test(token.content)) htmlCode += 1;
      if (/^<\/code\s*>/i.test(token.content)) htmlCode = Math.max(0, htmlCode - 1);
    }
    if (token.type === "strong_open") {
      openings.push({ position: positions[emphasisPositions.get(token) - 1], htmlCode });
    } else if (token.type === "strong_close") {
      const opening = openings.pop();
      const end = positions[emphasisPositions.get(token) + 1] + 1;
      if (!opening.htmlCode && !htmlCode) spans.push({ start: opening.position, end });
    }
  }
}

function maskMediaTokens(body, media) {
  if (!media.length) return body;
  const chunks = [];
  let offset = 0;
  for (const token of media) {
    const masked = token.presentation === "image"
      ? "<!--" + "x".repeat(token.raw.length - 7) + "-->" : "x".repeat(token.raw.length);
    chunks.push(body.slice(offset, token.start), masked);
    offset = token.end;
  }
  chunks.push(body.slice(offset));
  return chunks.join("");
}

function markdownRegions(body, start, end) {
  const media = /\[\[(?:image|catalogue):/.test(body) ? parseSourceTokens(body, (raw, location) =>
    parseImageToken(raw, location) || parseCatalogueToken(raw, location)) : [];
  const source = maskMediaTokens(body, media);
  const blocks = [];
  const environment = {};
  markdown.block.parse(source, markdown, environment, blocks);
  const starts = lineOffsets(source);
  const spans = [];
  let containingRegion = false;
  let cells = [];
  let cellIndex = 0;
  for (const token of blocks) {
    if (token.type === "tr_open") {
      const range = tableRowRanges.get(token);
      cells = range[0] < end && range[1] > start ? tableCells(source, range) : [];
      cellIndex = 0;
    }
    if (token.type !== "inline") continue;
    let positions;
    if (token.map) {
      const [first, after] = token.map;
      if (starts[first] >= end || starts[after] <= start) continue;
      positions = textPositions(source, starts, token);
    } else {
      const cell = cells[cellIndex++];
      if (cell?.content === token.content) positions = cell.positions;
    }
    if (!positions?.length || positions[0] >= end || positions.at(-1) < start) continue;
    containingRegion ||= positions[0] <= start && positions.at(-1) + 1 >= end;
    markdown.inline.parse(token.content, markdown, environment, token.children);
    collectBoldSpans(token.children, positions, spans);
  }
  return {
    spans,
    mayWrap: containingRegion && !media.some(token => token.start < end && token.end > start)
  };
}

/** Return Markdown for the selected range, or null when it cannot be toggled. */
export function toggleBoldInSelection(source, capture) {
  const bodyStart = sourceBodyStart(source);
  const body = source.slice(bodyStart);
  const selection = source.slice(capture.start, capture.end);
  if (!selection.trim() || capture.end <= bodyStart) return null;
  const start = capture.start - bodyStart;
  const end = capture.end - bodyStart;
  const innerStart = start + selection.length - selection.trimStart().length;
  const innerEnd = start + selection.trimEnd().length;
  const current = markdownRegions(body, innerStart, innerEnd);
  const complete = current.spans.filter(span => span.start >= start && span.end <= end);
  if (complete.length) {
    const markers = complete.flatMap(span => [span.start - start, span.end - start - 2]).sort((a, b) => a - b);
    const chunks = [];
    let offset = 0;
    for (const marker of markers) {
      chunks.push(selection.slice(offset, marker));
      offset = marker + 2;
    }
    chunks.push(selection.slice(offset));
    return chunks.join("");
  }
  if (!current.mayWrap || current.spans.some(span => span.start < end && span.end > start)) return null;

  const proposed = body.slice(0, innerStart) + "**" + body.slice(innerStart, innerEnd) + "**" + body.slice(innerEnd);
  const proposedEnd = innerEnd + 4;
  // Verify the new delimiters pair in context, including beside existing Markdown syntax.
  const { spans } = markdownRegions(proposed, innerStart, proposedEnd);
  if (!spans.some(span => span.start === innerStart && span.end === proposedEnd)) return null;
  return selection.slice(0, innerStart - start) + "**" + selection.slice(innerStart - start, innerEnd - start)
    + "**" + selection.slice(innerEnd - start);
}
