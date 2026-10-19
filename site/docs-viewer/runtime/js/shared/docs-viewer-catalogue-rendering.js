/** The browser serialization adapter for live references; prepared markup is bound in place. */
function escape(value) {
  return String(value).replace(/[&<>"']/g, function (character) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character];
  });
}

function resourceUrl(value) {
  if (typeof value !== "string" || !value || Array.from(value).some(function (character) {
    var code = character.charCodeAt(0);
    return /\s/.test(character) || character === "\\" || code <= 31 || code === 127;
  })) throw new Error("Catalogue resource URL is unsafe.");
  if (value.startsWith("/") && !value.startsWith("//")) return value;
  var parsed = new URL(value);
  if (!["http:", "https:"].includes(parsed.protocol) || !parsed.hostname || parsed.username || parsed.password) throw new Error("Catalogue resource URL is unsafe.");
  return value;
}

function imageControl(presentation, entry) {
  var image = presentation.image;
  var title = escape(presentation.label);
  var frame = entry ? " docsViewerCatalogueEntry__frame" : "";
  var ratio = entry ? ' style="aspect-ratio: ' + image.width_px + " / " + image.height_px + ';"' : "";
  return '<button type="button" class="docsViewer__mediaImageLink docsViewerFigure__imageLink' + frame + '"' + ratio
    + ' data-docs-media-open aria-label="Open ' + title + '">'
    + '<img data-docs-media-image alt="' + title + '" width="' + image.width_px + '" height="' + image.height_px + '" decoding="async">'
    + '<span data-docs-media-placeholder hidden>' + title + "</span></button>";
}

function iconMarkup(kind) {
  var name = kind === "download" ? "file" : "link";
  var url = new URL("../../../static/icons/" + name + ".svg", import.meta.url).href;
  return '<span class="docsViewer__inlineIcon" data-docs-icon="' + name + '" aria-hidden="true" style="display:inline-block;width:1em;height:1em;vertical-align:-0.125em;background-color:currentColor;mask-position:center;mask-size:contain;mask-repeat:no-repeat;mask-image:url(' + escape(url) + ');"></span>';
}

export function catalogueReferenceMarkup(reference, presentation) {
  var options = reference.options;
  var attrs = 'data-docs-content-detail="media" data-docs-media-kind="' + escape(reference.target.kind)
    + '" data-docs-media-id="' + escape(reference.target.id) + '"';
  if (reference.presentation === "media") return '<span ' + attrs + '><button type="button" class="docsViewer__mediaTextLink" data-docs-media-open>' + escape(options.label) + "</button></span>";
  var image = imageControl(presentation, reference.presentation === "entry");
  if (reference.presentation === "image") {
    var placement = { full: "docsViewerFigure--full-column", left: "docsViewerFigure--image-left", right: "docsViewerFigure--image-right" }[options.placement];
    var classes = placement + (options.fill_width ? "" : " docsViewerFigure--natural-width");
    var blocks = options.use_work_title_caption ? '<span class="docsViewerFigure__caption">' + escape(presentation.label) + "</span>" : "";
    if (options.summary_html) blocks += '<span class="docsViewerFigure__summary">' + options.summary_html + "</span>";
    return '<figure class="docsViewerFigure ' + classes + '" ' + attrs + ">" + image + (blocks ? "<figcaption>" + blocks + "</figcaption>" : "") + "</figure>";
  }
  var entry = presentation.entry;
  var rows = entry.resources.map(function (resource) {
    return "<li>" + iconMarkup(resource.kind) + ' <a href="' + escape(resourceUrl(resource.url)) + '" target="_blank" rel="noopener noreferrer">' + escape(resource.label) + "</a></li>";
  }).join("");
  return '<article class="docsViewerCatalogueEntry"><div class="docsViewerCatalogueEntry__record"><h1>' + escape(presentation.label)
    + '</h1><figure class="docsViewerCatalogueEntry__image" ' + attrs + ">" + image + '</figure><p class="docsViewerCatalogueEntry__metadata">'
    + entry.metadata_lines.map(escape).join("<br>") + "</p></div>"
    + (rows ? '<div class="docsViewerCatalogueEntry__resources"><section data-catalogue-resource="links"><ul>' + rows + "</ul></section></div>" : "") + "</article>";
}

/** Resolve one activation's references and pass carried presentations into interaction binding. */
export function mountCatalogueDocument(context) {
  var released = false;
  var listeners = [];
  var references = context.payload && context.payload.catalogue && context.payload.catalogue.references || [];
  var operation = context.createOperation();
  references.forEach(function (reference) {
    var slot = context.content.querySelector('[data-docs-catalogue-ref="' + reference.reference_id + '"]');
    if (!slot) return;
    async function mount(selectedOperation) {
      try {
        var presentation = reference.target.kind === "catalogue-work" ? await selectedOperation.readWork(reference.target.id) : null;
        if (released || !context.isCurrent()) return;
        if (selectedOperation.live) slot.innerHTML = catalogueReferenceMarkup(reference, presentation);
        context.bind(slot, presentation);
      } catch (error) {
        if (released || !context.isCurrent()) return;
        var status = slot.ownerDocument.createElement("span");
        status.setAttribute("role", "status");
        status.textContent = error.message + " ";
        var retry = slot.ownerDocument.createElement("button");
        retry.type = "button";
        retry.textContent = "Retry";
        var handleRetry = function () { status.remove(); mount(context.createOperation()); };
        retry.addEventListener("click", handleRetry);
        listeners.push(function () { retry.removeEventListener("click", handleRetry); status.remove(); });
        status.appendChild(retry);
        slot.appendChild(status);
      }
    }
    mount(operation);
  });
  return function () { released = true; listeners.forEach(function (release) { release(); }); };
}
