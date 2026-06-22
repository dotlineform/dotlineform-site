import "./analytics-navigation.js";
import { resolveCurrentAnalyticsRoute, getAnalyticsRouteEntries } from "./analytics-route-registry.js";
import { appendAssetVersion, loadAnalyticsRouteTemplate, mountAnalyticsRouteTemplate, readAssetVersion } from "./analytics-route-templates.js";

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initAnalyticsApp);
} else {
  initAnalyticsApp();
}

async function initAnalyticsApp() {
  const outlet = document.querySelector("[data-analytics-route-outlet]");
  const status = document.querySelector("[data-analytics-shell-status]");
  try {
    if (!outlet) {
      throw new Error("Analytics route outlet is missing");
    }
    const { config, route } = await resolveCurrentAnalyticsRoute();
    renderNavigation(config, route.id);
    renderShellTitle(route);
    const fragment = await loadAnalyticsRouteTemplate(route);
    mountAnalyticsRouteTemplate(outlet, fragment);
    if (status) status.hidden = true;
    if (route.script) {
      await import(appendAssetVersion(route.script, readAssetVersion()));
    }
  } catch (error) {
    console.error("analytics_app: failed to initialize route", error);
    if (status) {
      status.hidden = false;
      status.textContent = "Analytics route failed to load.";
      status.setAttribute("data-state", "error");
    }
  }
}

function renderShellTitle(route) {
  const title = typeof route.title === "string" && route.title.trim() ? route.title.trim() : "Analytics";
  document.title = route.id === "analytics_home"
    ? "dotlineform Analytics"
    : `${title} | dotlineform Analytics`;
  document.querySelectorAll("[data-analytics-page-title]").forEach((node) => {
    node.textContent = title;
  });
  const heading = document.querySelector("[data-analytics-shell-heading]");
  if (heading) heading.hidden = route.id === "analytics_home";
}

function renderNavigation(config, activeRouteId) {
  const nav = document.querySelector("[data-analytics-nav]");
  if (!nav) return;
  const routes = getAnalyticsRouteEntries(config).filter((route) => route.nav === true);
  nav.replaceChildren(...routes.map((route) => {
    const link = document.createElement("a");
    link.className = `nav-item${route.id === activeRouteId ? " is-active" : ""}`;
    link.href = route.path;
    link.dataset.analyticsNavigate = route.id;
    link.textContent = route.label || route.title || route.id;
    return link;
  }));
}
