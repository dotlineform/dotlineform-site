import { parseImageToken } from "./image-token-parser.js";
import { parseSourceTokens, semanticTokenTextRanges } from "./catalogue-token-parser.js";
import { sourceBodyStart } from "./source-buffer.js";

function sourceMediaPaths(source) {
  const body = source.slice(sourceBodyStart(source));
  const paths = new Set();
  parseSourceTokens(body, (raw, location) => {
    const image = parseImageToken(raw, location);
    if (image) paths.add(image.mediaPath);
    const match = /^\[\[(?:media|html-media):([^\]\s]+)\]\]$/.exec(raw);
    if (match) paths.add(match[1]);
    return null;
  });
  // Retain pending bytes when the author rewrites a token as a Markdown/HTML URL.
  const urls = /(?:\]\(\s*|(?:src|href)\s*=\s*["']?|^\s{0,3}\[[^\]\n]+\]:\s*<?)(docs\/[^\s)\]"'<>?#]+)/gm;
  semanticTokenTextRanges(body).forEach(([start, end]) => {
    for (const match of body.slice(start, end).matchAll(urls)) {
      try { paths.add(decodeURIComponent(match[1])); } catch (_error) { /* Save owns invalid source. */ }
    }
  });
  return paths;
}

function hasThumbnailAssignment(source) {
  return /^thumbnail[ \t]*:[ \t]*true[ \t]*$/mi.test(source.slice(0, sourceBodyStart(source)));
}

/** Mounted Files survive text edits/Undo; only final references/assignment select Save inputs. */
export function createPendingSourceMedia() {
  const files = new Map();
  let thumbnail = null;
  let cachedSource = null;
  let cachedSelection = null;
  return {
    get(mediaPath) { return files.get(mediaPath); },
    check(entry, editedPath) {
      const existing = files.get(entry.mediaPath);
      if (existing && existing.file !== entry.file && editedPath !== entry.mediaPath) {
        throw new Error("Competing pending files for " + entry.mediaPath + ". Edit that reference or choose another filename.");
      }
    },
    add(entry) {
      const existing = files.get(entry.mediaPath);
      if (thumbnail === existing && existing && existing.file === entry.file) thumbnail = entry;
      files.set(entry.mediaPath, entry);
      if (entry.createThumb) thumbnail = entry;
      cachedSelection = null;
    },
    selected(source) {
      if (cachedSelection && cachedSource === source) return cachedSelection;
      if (!files.size && !thumbnail) return [];
      const paths = sourceMediaPaths(source);
      const wantedThumbnail = thumbnail && hasThumbnailAssignment(source) ? thumbnail : null;
      const candidates = new Set(files.values());
      if (wantedThumbnail) candidates.add(wantedThumbnail);
      cachedSelection = Array.from(candidates, (entry) => ({
        file: entry.file,
        media_kind: entry.mediaKind,
        preserve_resolution: entry.preserveResolution,
        replace: entry.replace,
        body: files.get(entry.mediaPath) === entry && paths.has(entry.mediaPath),
        thumbnail: wantedThumbnail === entry
      })).filter((entry) => entry.body || entry.thumbnail);
      cachedSource = source;
      return cachedSelection;
    },
    clear() {
      files.clear();
      thumbnail = null;
      cachedSource = null;
      cachedSelection = null;
    }
  };
}
