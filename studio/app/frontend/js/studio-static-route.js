import {
  initializeStudioRouteState,
  setStudioRouteReady
} from "./studio-route-state.js";

function initStaticStudioRoutes() {
  document.querySelectorAll("[data-studio-static-route]").forEach((root) => {
    const route = String(root.dataset.studioStaticRoute || "").trim();
    const mode = String(root.dataset.studioMode || "static").trim() || "static";
    initializeStudioRouteState(root, {
      route,
      mode,
      recordLoaded: true
    });
    setStudioRouteReady(root, true, {
      route,
      mode,
      recordLoaded: true
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initStaticStudioRoutes);
} else {
  initStaticStudioRoutes();
}
