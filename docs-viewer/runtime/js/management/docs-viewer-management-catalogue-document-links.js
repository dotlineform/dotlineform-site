/** Read exact Working Catalogue locations; never choose among multiple Work documents. */
function catalogueDocumentLinks(payload) {
  if (!payload || payload.schema_version !== "docs_subject_associations_v2"
    || payload.stage !== "working" || payload.collection !== "catalogue"
    || !Array.isArray(payload.associations)) {
    throw new Error("Working Catalogue document associations are invalid.");
  }
  const links = new Map();
  payload.associations.forEach((association) => {
    const subject = association && association.subject;
    if (!subject || subject.kind !== "work") return;
    if (typeof subject.key !== "string" || !/^[0-9]{5}$/.test(subject.key)
      || links.has(subject.key) || !Array.isArray(association.documents)
      || association.documents.length !== 1) {
      throw new Error("Catalogue Work association requires one exact document.");
    }
    const document = association.documents[0];
    const target = document && document.target;
    const locations = document && Array.isArray(document.locations)
      ? document.locations.filter((location) => location && location.access === "manage") : [];
    const href = locations.length === 1 && locations[0].url;
    if (!target || target.stage !== "working" || target.collection !== "catalogue"
      || typeof target.doc_id !== "string" || !target.doc_id
      || typeof href !== "string" || !href.startsWith("/") || href.startsWith("//") || /[\\\s]/.test(href)) {
      throw new Error("Catalogue document location is invalid.");
    }
    const params = new URL(href, "https://docs.invalid").searchParams;
    if (params.get("stage") !== target.stage || params.get("subdoc") !== target.doc_id
      || !params.get("doc") || params.has("scope")) {
      throw new Error("Catalogue document location does not match its identity.");
    }
    links.set(subject.key, href);
  });
  return links;
}

/** Load one configured association file and preserve its exact Work-to-document URLs.
 * Missing Work entries remain absent; configuration, read and ambiguous identity errors propagate.
 */
export async function loadWorkingCatalogueDocumentLinks(options) {
  const working = options.stageConfigs.find((config) => config.stage === "working");
  const catalogue = working && working.collections.find((collection) => collection.collection === "catalogue");
  if (!catalogue || !catalogue.manifestUrl) {
    throw new Error("Working Catalogue is not configured.");
  }
  const url = new URL("subject-associations.json", new URL(catalogue.manifestUrl, options.document.baseURI));
  const fetchJson = options.fetch || fetch;
  const response = await fetchJson(url.toString(), { cache: "no-store", headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error("Failed to load Catalogue document associations.");
  return catalogueDocumentLinks(await response.json());
}
