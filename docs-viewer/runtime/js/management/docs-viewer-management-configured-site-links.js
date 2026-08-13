const RESOLUTION_ORIGIN = "http://docs-viewer.local";

function cleanText(value) {
  return String(value == null ? "" : value).trim();
}

function normalizedPathPrefix(value) {
  var rawPrefix = cleanText(value);
  if (!rawPrefix.startsWith("/") || rawPrefix.startsWith("//")) return "";
  var expectedPrefix = rawPrefix.endsWith("/") ? rawPrefix : rawPrefix + "/";
  var url;
  try {
    url = new URL(rawPrefix, RESOLUTION_ORIGIN);
  } catch (_error) {
    return "";
  }
  if (
    url.origin !== RESOLUTION_ORIGIN
    || url.pathname !== expectedPrefix
    || url.search
    || url.hash
  ) {
    return "";
  }
  return expectedPrefix;
}

function configuredOrigin(value) {
  var rawBaseUrl = cleanText(value);
  if (!rawBaseUrl) return "";
  var url;
  try {
    url = new URL(rawBaseUrl);
  } catch (_error) {
    return "";
  }
  if (
    !["http:", "https:"].includes(url.protocol)
    || !url.hostname
    || url.username
    || url.password
    || url.pathname !== "/"
    || url.search
    || url.hash
  ) {
    return "";
  }
  return url.origin;
}

export function resolveManagedConfiguredSiteHref(href, routes = []) {
  var rawHref = cleanText(href);
  if (!rawHref.startsWith("/") || rawHref.startsWith("//")) return "";
  var configuredRoutes = Array.isArray(routes) ? routes : [];

  var targetUrl;
  try {
    targetUrl = new URL(rawHref, RESOLUTION_ORIGIN);
  } catch (_error) {
    return "";
  }
  if (targetUrl.origin !== RESOLUTION_ORIGIN) return "";

  for (var index = 0; index < configuredRoutes.length; index += 1) {
    var route = configuredRoutes[index] || {};
    var pathPrefix = normalizedPathPrefix(route.pathPrefix);
    var baseOrigin = configuredOrigin(route.baseUrl);
    if (!pathPrefix || !baseOrigin || !targetUrl.pathname.startsWith(pathPrefix)) continue;
    return new URL(
      targetUrl.pathname + targetUrl.search + targetUrl.hash,
      baseOrigin
    ).toString();
  }
  return "";
}

export function mountManagedConfiguredSiteLinks(root, routes = []) {
  if (!root || typeof root.querySelectorAll !== "function") return 0;
  var mounted = 0;
  root.querySelectorAll("a[href]").forEach(function (link) {
    var managedHref = resolveManagedConfiguredSiteHref(
      link.getAttribute("href"),
      routes
    );
    if (!managedHref) return;
    link.setAttribute("href", managedHref);
    mounted += 1;
  });
  return mounted;
}
