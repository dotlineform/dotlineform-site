function identity(value) {
  if (!value || !/^[a-z][a-z0-9-]*$/.test(value.scope)
    || typeof value.sub_scope !== "string" || !/^(?:[a-z][a-z0-9-]*)?$/.test(value.sub_scope)
    || !/^d-\d{8}-\d{6}-[a-f0-9]{6}$/.test(value.doc_id)) {
    throw new Error("Links requires an exact document identity.");
  }
  return { scope: value.scope, sub_scope: value.sub_scope, doc_id: value.doc_id };
}

function sameTarget(left, right) {
  return left.scope === right.scope && left.sub_scope === right.sub_scope && left.doc_id === right.doc_id;
}

/** Validate a prepared document summary and apply the explicit local viewing stage.
 * Preserve collection and Subject metadata for consumers' document presentation.
 */
export function docsViewerLinksDocumentSummary(value, invokingTarget) {
  var target = identity(value && value.target);
  if (typeof value.title !== "string" || !value.title.trim()) throw new Error("Links document title is missing.");
  var href = value.href;
  if (typeof href !== "string" || !href.startsWith("/") || href.startsWith("//") || /[\\\s]/.test(href)) {
    throw new Error("Links document navigation is invalid.");
  }
  var url = new URL(href, "https://docs.invalid");
  var params = url.searchParams;
  if ((params.has("scope") && params.get("scope") !== target.scope)
    || (target.sub_scope
      ? !params.get("doc") || params.get("subdoc") !== target.doc_id
      : params.get("doc") !== target.doc_id || params.has("subdoc"))) {
    throw new Error("Links navigation does not match its document identity.");
  }
  if (invokingTarget.stage && target.scope === invokingTarget.scope) params.set("stage", invokingTarget.stage);
  return {
    target: target, title: value.title, href: url.pathname + url.search + url.hash,
    subject: value.subject || null
  };
}

function category(document) {
  if (document.target.scope === "analysis" && document.target.sub_scope === "concepts") return "Concepts";
  if (document.subject && document.subject.state === "valid" && document.subject.kind === "work") return "Works";
  if (!document.target.sub_scope) return "References";
  return "";
}

/** Validate one complete version-1 response and project shallow, title-sorted sections.
 * Combine both directions by exact identity; keep the supplied directional data unchanged.
 * Runtime stage navigation is separate from the stage-free stored href.
 */
export function docsViewerLinksPresentation(payload, target) {
  var expected = identity(target);
  if (!payload || payload.schema_version !== 1 || !Array.isArray(payload.outgoing) || !Array.isArray(payload.incoming)) {
    throw new Error("Unsupported Links data. Expected schema version 1.");
  }
  var self = docsViewerLinksDocumentSummary(payload.self, target);
  if (!sameTarget(self.target, expected)) throw new Error("Links data does not match the displayed document.");
  var sections = new Map(["Concepts", "Works", "References"].map(function (label) { return [label, []]; }));
  var documents = new Map();
  ["outgoing", "incoming"].forEach(function (direction) {
    var seen = new Set();
    payload[direction].forEach(function (entry) {
      var document = docsViewerLinksDocumentSummary(entry && entry.document, target);
      var key = JSON.stringify(document.target);
      if (seen.has(key) || !Array.isArray(entry.occurrences) || !entry.occurrences.length) {
        throw new Error("Links contains an invalid counterpart entry.");
      }
      seen.add(key);
      if (!documents.has(key)) documents.set(key, document);
    });
  });
  documents.forEach(function (document) {
    var label = category(document);
    if (label) sections.get(label).push({ document: document });
  });
  return {
    title: self.title,
    sections: Array.from(sections, function ([label, entries]) {
      entries.sort(function (a, b) {
        return a.document.title.localeCompare(b.document.title, "en", { sensitivity: "base" })
          || JSON.stringify(a.document.target).localeCompare(JSON.stringify(b.document.target));
      });
      return { label: label, entries: entries };
    }).filter(function (section) { return section.entries.length; })
  };
}
