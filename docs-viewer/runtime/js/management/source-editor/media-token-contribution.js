import { parseImageToken } from "./image-token-parser.js";
import {
  parseCatalogueToken,
  parseSourceTokens,
  sourceTokenAtSelection
} from "./source-token-parser.js";
import { sourceBodyStart } from "./source-buffer.js";

/** Resolve both menu labels and their modal selections from the same source snapshot. */
export function captureMediaTokenActions(snapshot, selection) {
  var source = snapshot.value;
  var bodyStart = sourceBodyStart(source);
  var tokens = parseSourceTokens(source.slice(bodyStart), function (raw, location) {
    return parseImageToken(raw, location) || parseCatalogueToken(raw, location);
  });
  var token = sourceTokenAtSelection(tokens, {
    start: selection.start - bodyStart,
    end: selection.end - bodyStart
  });
  var tokenCapture = token && {
    start: token.start + bodyStart,
    end: token.end + bodyStart,
    text: token.raw,
    revision: snapshot.revision
  };
  var imageToken = token?.family === "image" ? token : null;
  var catalogueToken = token?.family === "catalogue" ? token : null;
  return {
    source: source,
    image: {
      label: imageToken ? "Edit image" : "Add image",
      token: imageToken,
      capture: imageToken ? tokenCapture : selection
    },
    catalogue: {
      label: catalogueToken ? "Edit Catalogue reference" : "Add Catalogue reference",
      token: catalogueToken,
      capture: catalogueToken ? tokenCapture : selection
    }
  };
}
