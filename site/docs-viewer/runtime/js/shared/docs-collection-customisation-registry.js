function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

const PUBLIC_CUSTOMISATION_LOADERS = Object.freeze({});

export function listPublicDocsCollectionCustomisationIds() {
  return Object.freeze(Object.keys(PUBLIC_CUSTOMISATION_LOADERS).sort());
}

export function resolvePublicDocsCollectionCustomisation(descriptor, options = {}) {
  if (descriptor == null) return Promise.resolve(null);
  var customisationId = cleanString(descriptor && descriptor.id);
  var loader = PUBLIC_CUSTOMISATION_LOADERS[customisationId];
  if (!customisationId || typeof loader !== "function") {
    return Promise.reject(new Error(
      "Public Docs collection customisation is unavailable: "
      + (customisationId || "missing identity")
    ));
  }
  return Promise.resolve(loader()).then(function (factory) {
    if (typeof factory !== "function") {
      throw new Error(
        "Public Docs collection customisation factory is unavailable: "
        + customisationId
      );
    }
    return factory(Object.assign({}, options, { descriptor: descriptor }));
  });
}
