import "./admin-theme.js";
import { resolveCurrentAdminRoute } from "./admin-route-registry.js";
import { appendAssetVersion, loadAdminRouteTemplate, mountAdminRouteTemplate, readAssetVersion } from "./admin-route-templates.js";

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initAdminApp);
} else {
  initAdminApp();
}

async function initAdminApp() {
  const outlet = document.querySelector("[data-admin-route-outlet]");
  const status = document.querySelector("[data-admin-shell-status]");
  try {
    if (!outlet) {
      throw new Error("Admin route outlet is missing");
    }
    const { route } = await resolveCurrentAdminRoute();
    renderShellTitle(route);
    const fragment = await loadAdminRouteTemplate(route);
    mountAdminRouteTemplate(outlet, fragment);
    if (status) status.hidden = true;
    if (route.script) {
      await import(appendAssetVersion(route.script, readAssetVersion()));
    }
  } catch (error) {
    console.error("admin_app: failed to initialize route", error);
    if (status) {
      status.hidden = false;
      status.textContent = "Admin route failed to load.";
      status.setAttribute("data-state", "error");
    }
  }
}

function renderShellTitle(route) {
  const title = typeof route.title === "string" && route.title.trim() ? route.title.trim() : "Admin";
  document.title = route.id === "admin_home"
    ? "Admin | dotlineform"
    : `${title} | dotlineform Admin`;
  document.querySelectorAll("[data-admin-page-title]").forEach((node) => {
    node.textContent = title;
  });
  document.querySelectorAll("[data-admin-route-section]").forEach((node) => {
    node.dataset.adminPage = route.id ? route.id.replace(/_/g, "-") : "";
  });
  const heading = document.querySelector("[data-admin-route-heading]");
  if (heading) heading.hidden = route.id === "admin_home";
}
