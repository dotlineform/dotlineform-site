import { findStudioRoute } from "./studio-route-registry.js";

const HOME_COLUMNS = Object.freeze([
  Object.freeze({
    label: "catalogue",
    links: Object.freeze([
      Object.freeze({ routeId: "catalogue_status" }),
      Object.freeze({ routeId: "catalogue_series_editor" }),
      Object.freeze({ routeId: "catalogue_work_editor" }),
      Object.freeze({ routeId: "catalogue_work_detail_editor" }),
      Object.freeze({ routeId: "bulk_add_work" }),
      Object.freeze({ routeId: "catalogue_moment_editor" }),
      Object.freeze({ routeId: "studio_works", params: Object.freeze({ sort: "cat", dir: "asc" }) }),
      Object.freeze({ routeId: "project_state" })
    ])
  }),
  Object.freeze({
    label: "admin",
    links: Object.freeze([
      Object.freeze({ routeId: "studio_audits" }),
      Object.freeze({ routeId: "activity" }),
      Object.freeze({ routeId: "catalogue_field_registry" })
    ])
  })
]);

export function renderStudioHomeShell(config) {
  return `<div id="studioHomeRoot" data-studio-ready="true" data-studio-busy="false">
      <section class="studioHomeLinks" aria-label="Studio home links">
        ${HOME_COLUMNS.map((column) => renderHomeColumn(config, column)).join("\n        ")}
      </section>
    </div>`;
}

function renderHomeColumn(config, column) {
  const links = column.links
    .map((link) => renderHomeLink(config, link))
    .filter(Boolean)
    .join("\n          ");
  return `<section class="studioHomeLinks__column">
        <h3>${escapeHtml(column.label)}</h3>
        <ul class="studioHomeLinks__pills">
          ${links}
        </ul>
      </section>`;
}

function renderHomeLink(config, link) {
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
