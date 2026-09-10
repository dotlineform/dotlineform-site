import {
  catalogueTokenAtSelection,
  parseCatalogueTokens
} from "./catalogue-token-parser.js";
import {
  loadSemanticTokenRegistry
} from "./semantic-token-registry.js";

export function createCatalogueTokenInfoViewResolver(options = {}) {
  var registryPromise = null;
  function loadRegistry() {
    if (!registryPromise) {
      registryPromise = loadSemanticTokenRegistry({ fetch: options.fetch });
    }
    return registryPromise;
  }
  return function (adapter) {
    if (
      !adapter
      || typeof adapter.getBufferSnapshot !== "function"
      || typeof adapter.getSelection !== "function"
    ) return Promise.resolve("metadata-info");
    return loadRegistry()
      .then(function (registry) {
        var snapshot = adapter.getBufferSnapshot();
        var selection = adapter.getSelection();
        var tokens = parseCatalogueTokens(snapshot.value, { registry: registry });
        return catalogueTokenAtSelection(tokens, selection)
          ? "catalogue-token-info"
          : "metadata-info";
      })
      .catch(function () {
        return "metadata-info";
      });
  };
}
