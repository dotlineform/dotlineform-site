import {
  sourceTokenAtSelection,
  parseCatalogueTokens
} from "./source-token-parser.js";
import { sourceBodyStart } from "./source-buffer.js";

/** Resolve the menu label and modal selection together when Directives opens. */
export function captureCatalogueTokenAction(snapshot, selection) {
  var bodyStart = sourceBodyStart(snapshot.value);
  var tokens = parseCatalogueTokens(snapshot.value.slice(bodyStart)).map(function (token) {
    return Object.assign({}, token, { start: token.start + bodyStart, end: token.end + bodyStart });
  });
  var token = sourceTokenAtSelection(tokens, selection);
  return {
    label: token ? "Edit Media View link" : "Add Media View link",
    token: token,
    capture: token ? { start: token.start, end: token.end, text: token.raw, revision: snapshot.revision } : selection
  };
}
