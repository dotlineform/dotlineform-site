function defaultDocumentRef() {
  return typeof document !== "undefined" ? document : null;
}

export function readAssetVersion(ownerDocument) {
  var doc = ownerDocument || defaultDocumentRef();
  if (!doc) return "";
  var meta = doc.querySelector('meta[name="dlf-asset-version"]');
  if (!meta) return "";
  return String(meta.getAttribute("content") || "").trim();
}

export function appendAssetVersion(url, assetVersion) {
  var cleanUrl = String(url || "");
  if (!cleanUrl) return "";

  var version = typeof assetVersion === "string" ? assetVersion : readAssetVersion();
  if (!version) return cleanUrl;

  var separator = cleanUrl.indexOf("?") >= 0 ? "&" : "?";
  return cleanUrl + separator + "v=" + encodeURIComponent(version);
}

export function requestUrl(url, options) {
  var settings = options || {};
  var nextUrl = appendAssetVersion(url, settings.assetVersion);
  if (!settings.reloadNonce) {
    return nextUrl;
  }
  var separator = nextUrl.indexOf("?") >= 0 ? "&" : "?";
  return nextUrl + separator + "reload=" + encodeURIComponent(settings.reloadNonce);
}

export function mountDocsContentHtml(node, htmlText, options) {
  var settings = options || {};
  var mediaRoot = String(settings.mediaRoot || "").replace(/\/+$/, "");
  var viewerBaseUrl = String(settings.viewerBaseUrl || "");
  var template = node.ownerDocument.createElement("template");
  template.innerHTML = String(htmlText || "");
  template.content.querySelectorAll("[src], [href], [data-docs-viewer-diagram-light-src], [data-docs-viewer-diagram-dark-src]").forEach(function (element) {
    ["src", "href", "data-docs-viewer-diagram-light-src", "data-docs-viewer-diagram-dark-src"].forEach(function (attribute) {
      var value = element.getAttribute(attribute);
      if (!value) return;
      if (value.startsWith("docs-media:")) {
        if (!mediaRoot) throw new Error("Docs media root is not configured.");
        var suffix = value.slice("docs-media:".length);
        var parts = suffix.split("/");
        var mediaType = parts[0] === "workspace" ? parts[1] : parts[0] === "collections" ? parts[2] : "";
        if (!/^(img|svg|files|html)$/.test(mediaType)
            || parts.length < (parts[0] === "workspace" ? 3 : 4)
            || parts.some(function (part) { return !part || part === "." || part === ".."; })) {
          throw new Error("Invalid Docs media identity.");
        }
        element.setAttribute(attribute, mediaRoot + "/" + parts.map(encodeURIComponent).join("/"));
      } else if (attribute === "href" && element.tagName === "A" && value.startsWith("?doc=")) {
        if (!viewerBaseUrl) throw new Error("Docs viewer route is not configured.");
        var route = new URL(value, new URL(viewerBaseUrl, node.ownerDocument.baseURI));
        element.setAttribute(attribute, route.href);
      }
    });
  });
  node.replaceChildren(template.content);
}
