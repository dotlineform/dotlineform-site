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
