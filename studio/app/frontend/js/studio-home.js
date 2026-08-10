import { loadStudioConfig } from "./studio-config.js";
import { getStudioSiteBase } from "./studio-navigation.js";
import { findStudioRoute } from "./studio-route-registry.js";

const HOME_COLUMNS = Object.freeze([
  Object.freeze({
    label: "catalogue",
    links: Object.freeze([
      Object.freeze({ routeId: "catalogue_status" }),
      Object.freeze({ routeId: "catalogue_series_editor" }),
      Object.freeze({ routeId: "catalogue_work_editor" }),
      Object.freeze({ routeId: "bulk_add_work" }),
      Object.freeze({ routeId: "catalogue_field_registry" }),
      Object.freeze({
        href: "/docs/?scope=dotlineform&doc=d-20260810-222148-99daec",
        label: "works",
        siteKey: "docs_viewer"
      })
    ])
  }),
  Object.freeze({
    label: "tags",
    links: Object.freeze([
      Object.freeze({ routeId: "tag_groups" }),
      Object.freeze({ routeId: "tag_registry" }),
      Object.freeze({ routeId: "tag_aliases" }),
      Object.freeze({ routeId: "series_tags" }),
      Object.freeze({ routeId: "series_tag_editor" })
    ])
  })
]);

async function init() {
  const root = document.getElementById("studioHomeRoot");
  const linksNode = document.getElementById("studioHomeLinks");
  if (!root || !linksNode) return;
  try {
    const config = await loadStudioConfig();
    linksNode.innerHTML = HOME_COLUMNS.map((column) => renderHomeColumn(config, column)).join("\n");
  } catch (error) {
    console.warn("studio_home: init failed", error);
  }
}

function renderHomeColumn(config, column) {
  const links = column.links
    .map((link) => renderHomeLink(config, link))
    .filter(Boolean)
    .join("\n");
  return `<section class="studioHomeLinks__column">
    <h3>${escapeHtml(column.label)}</h3>
    <ul class="studioHomeLinks__pills">
      ${links}
    </ul>
  </section>`;
}

function renderHomeLink(config, link) {
  if (link.href) {
    let href = link.href;
    if (link.siteKey) {
      const base = getStudioSiteBase(config, link.siteKey);
      if (!base) return "";
      href = new URL(String(link.href), `${base}/`).href;
    }
    return `<li><a class="studioHomeLinks__pill studioLinkList__item" href="${escapeHtml(href, true)}">${escapeHtml(link.label || link.href)}</a></li>`;
  }
  const route = findStudioRoute(config, link.routeId);
  if (!route) return "";
  const href = appendRouteParams(route.path, link.params);
  return `<li><a class="studioHomeLinks__pill studioLinkList__item" href="${escapeHtml(href, true)}">${escapeHtml(route.label)}</a></li>`;
}

function appendRouteParams(path, params) {
  if (!path || !params || typeof params !== "object") return path || "";
  const url = new URL(String(path), currentOrigin());
  for (const [key, value] of Object.entries(params)) {
    if (!key || value == null || value === "") continue;
    url.searchParams.set(key, String(value));
  }
  return url.origin === currentOrigin() ? `${url.pathname}${url.search}${url.hash}` : url.href;
}

function currentOrigin() {
  return typeof window !== "undefined" && window.location && window.location.origin
    ? window.location.origin
    : "http://127.0.0.1";
}

function escapeHtml(value, attribute = false) {
  const text = String(value == null ? "" : value);
  const escaped = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return attribute
    ? escaped.replace(/"/g, "&quot;").replace(/'/g, "&#39;")
    : escaped;
}

init();
