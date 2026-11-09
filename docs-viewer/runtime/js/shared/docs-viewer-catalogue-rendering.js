/** Render portable Catalogue references from the loaded document. */
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

function iconMarkup(name) {
  var url = new URL("../../../static/icons/" + name + ".svg", import.meta.url).href;
  return '<span class="docsViewer__inlineIcon" data-docs-icon="' + name + '" aria-hidden="true" style="display:inline-block;width:1em;height:1em;vertical-align:-0.125em;background-color:currentColor;mask-position:center;mask-size:contain;mask-repeat:no-repeat;mask-image:url(' + escape(url) + ');"></span>';
}

function mediaTargetAttributes(target) {
  return 'data-docs-content-detail="media" data-docs-media-kind="' + escape(target.kind)
    + '" data-docs-media-id="' + escape(target.id) + '"';
}

function mediaTextLink(target, label) {
  return '<span ' + mediaTargetAttributes(target) + '><button type="button" class="docsViewer__mediaTextLink" data-docs-media-open>'
    + escape(label) + "</button></span>";
}

function galleryListMarkup(galleries) {
  var rows = galleries.map(function (gallery) {
    var target = { kind: "catalogue-gallery", id: gallery.id };
    return "<li>" + iconMarkup("images") + " " + mediaTextLink(target, gallery.label) + "</li>";
  }).join("");
  return "<ul>" + rows + "</ul>";
}

function galleryLinksMarkup(galleries) {
  if (!galleries.length) return "";
  var firstRelated = galleries.findIndex(function (gallery) { return gallery.relation === "series"; });
  var heading = firstRelated === 0 ? "related galleries" : "galleries";
  var lists = firstRelated > 0
    ? galleryListMarkup(galleries.slice(0, firstRelated)) + "<p>related:</p>" + galleryListMarkup(galleries.slice(firstRelated))
    : galleryListMarkup(galleries);
  return '<section class="docsViewerCatalogueEntry__galleries"><h2>' + heading + "</h2>" + lists + "</section>";
}

function catalogueReferenceMarkup(reference, presentation, downloadUrl) {
  var options = reference.options;
  if (reference.presentation === "media") return mediaTextLink(reference.target, options.label);
  var attrs = mediaTargetAttributes(reference.target);
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
    var url = resource.kind === "download" ? downloadUrl(resource.identity) : resourceUrl(resource.url);
    var icon = resource.kind === "download" ? "file" : "link";
    return "<li>" + iconMarkup(icon) + ' <a href="' + escape(url) + '" target="_blank" rel="noopener noreferrer">' + escape(resource.label) + "</a></li>";
  }).join("");
  return '<article class="docsViewerCatalogueEntry"><div class="docsViewerCatalogueEntry__record"><h1>' + escape(presentation.label)
    + '</h1><figure class="docsViewerCatalogueEntry__image" ' + attrs + ">" + image + '</figure><p class="docsViewerCatalogueEntry__metadata">'
    + entry.metadata_lines.map(escape).join("<br>") + "</p></div>"
    + (rows ? '<div class="docsViewerCatalogueEntry__resources"><section data-catalogue-resource="links"><ul>' + rows + "</ul></section></div>" : "")
    + galleryLinksMarkup(presentation.galleries) + "</article>";
}

/** Mount the prepared display data before any Media View target is selected. */
export function mountCatalogueDocument(context) {
  var catalogue = context.payload.catalogue;
  catalogue.references.forEach(function (reference) {
    var slot = context.content.querySelector('[data-docs-catalogue-ref="' + reference.reference_id + '"]');
    if (!slot) return;
    try {
      var presentation = null;
      if (reference.presentation !== "media") {
        var work = reference.presentation === "entry" ? catalogue.work : null;
        var image = context.image(work ? work.image : reference.render);
        presentation = { label: image.alt, image: image, entry: work && work.entry, galleries: work && work.galleries };
      }
      slot.innerHTML = catalogueReferenceMarkup(reference, presentation, context.downloadUrl);
      context.bind(slot, presentation && {
        src: image.src, srcset: image.srcset, alt: image.alt,
        widthPx: image.width_px, heightPx: image.height_px
      });
    } catch (error) {
      slot.setAttribute("role", "status");
      slot.textContent = error.message;
    }
  });
}
