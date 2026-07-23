const root = document.querySelector("#adminUiWorkbenchFrameRoot");
const fixture = document.querySelector("#adminUiWorkbenchFixture");
const params = new URLSearchParams(window.location.search);
const appId = text(params.get("app"));
const entrypoint = normalizeEntrypoint(params.get("entrypoint"));
const specimenId = text(params.get("specimen"));
const theme = params.get("theme") === "dark" ? "dark" : "light";

function text(value) {
  return String(value == null ? "" : value).trim();
}

function normalizeEntrypoint(value) {
  const path = text(value);
  if (!path.startsWith("/docs-viewer/tests/workbench/") || !path.endsWith(".js")) {
    throw new Error("UI Workbench frame requires an app-owned workbench entrypoint");
  }
  return path;
}

function notify(type, payload = {}) {
  if (window.parent === window) return;
  window.parent.postMessage({
    source: "admin-ui-workbench-frame",
    type,
    appId,
    payload
  }, window.location.origin);
}

function loadStyles(styles) {
  return Promise.all(styles.map((href) => new Promise((resolve, reject) => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = text(href);
    link.addEventListener("load", resolve, { once: true });
    link.addEventListener("error", () => reject(new Error(`Could not load Workbench style: ${href}`)), {
      once: true
    });
    document.head.append(link);
  })));
}

async function boot() {
  if (!root || !fixture || !specimenId) throw new Error("UI Workbench frame is missing its specimen");
  document.documentElement.dataset.theme = theme;
  const packModule = await import(entrypoint);
  const pack = packModule.docsViewerWorkbenchPackRecord?.();
  if (!pack || pack.appId !== appId) throw new Error("UI Workbench frame loaded the wrong app pack");
  await loadStyles(Array.isArray(pack.styles) ? pack.styles : []);
  const specimen = await packModule.mountDocsViewerWorkbenchSpecimen(specimenId, {
    document,
    root: fixture
  });
  root.dataset.workbenchFrameReady = "true";
  root.dataset.workbenchFrameBusy = "false";
  root.dataset.workbenchFrameSpecimen = specimen.id;
  notify("mounted", { specimenId: specimen.id });
}

void boot().catch((error) => {
  const message = error instanceof Error ? error.message : "UI Workbench specimen failed to mount.";
  if (root) {
    root.dataset.workbenchFrameReady = "true";
    root.dataset.workbenchFrameBusy = "false";
    root.dataset.workbenchFrameError = message;
  }
  if (fixture) fixture.textContent = message;
  notify("error", { specimenId, message });
  console.error("admin_ui_workbench_frame: specimen mount failed", error);
});
