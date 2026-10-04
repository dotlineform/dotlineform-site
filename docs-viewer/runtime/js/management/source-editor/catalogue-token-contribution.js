import {
  sourceTokenAtSelection,
  parseCatalogueTokens
} from "./catalogue-token-parser.js";
import { sourceBodyStart } from "./source-buffer.js";

/** Capture the corresponding body occurrence before opening a modal or doing asynchronous reads. */
export function captureCatalogueTokenAction(adapter, selection, presentation) {
  var snapshot = adapter.getBufferSnapshot();
  var bodyStart = sourceBodyStart(snapshot.value);
  var tokens = parseCatalogueTokens(snapshot.value.slice(bodyStart)).map(function (token) {
    return Object.assign({}, token, { start: token.start + bodyStart, end: token.end + bodyStart });
  });
  var token = sourceTokenAtSelection(tokens, selection);
  if (token && token.presentation !== presentation) token = null;
  return {
    snapshot: snapshot,
    token: token,
    capture: token ? { start: token.start, end: token.end, text: token.raw, revision: snapshot.revision } : selection
  };
}
