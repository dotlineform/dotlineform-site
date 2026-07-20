const INLINE_MERMAID_ASSET_URL = "/docs-viewer/runtime/vendor/mermaid/11.16.0/mermaid.min.js";
const INLINE_MERMAID_ASSET_VERSION = "11.16.0";

export const INLINE_MERMAID_ERROR_MESSAGE = "Diagram could not be rendered. Mermaid source is shown below.";

function mermaidInitializationConfig() {
  return {
    startOnLoad: false,
    theme: "neutral",
    securityLevel: "strict",
    htmlLabels: false,
    flowchart: {
      htmlLabels: false
    }
  };
}

function defaultWarning(message, error) {
  if (typeof console !== "undefined" && typeof console.warn === "function") {
    console.warn(message, error);
  }
}

function loadCheckedMermaidAsset(context) {
  var documentRef = context.document;
  var windowRef = context.window;
  var assetUrl = context.assetUrl;

  if (windowRef && windowRef.mermaid) return Promise.resolve(windowRef.mermaid);
  if (!documentRef || !windowRef) {
    return Promise.reject(new Error("Inline Mermaid requires a browser document and window."));
  }

  return new Promise(function (resolve, reject) {
    var script = documentRef.querySelector("script[data-docs-viewer-inline-mermaid-runtime]");

    function resolveRuntime() {
      if (!windowRef.mermaid) {
        reject(new Error("The checked Mermaid asset loaded without exposing its browser runtime."));
        return;
      }
      resolve(windowRef.mermaid);
    }

    function rejectRuntime() {
      reject(new Error("The checked Mermaid browser asset could not be loaded."));
    }

    if (script) {
      if (script.getAttribute("src") !== assetUrl) {
        reject(new Error("A different inline Mermaid browser asset is already present."));
        return;
      }
      if (windowRef.mermaid) {
        resolveRuntime();
        return;
      }
      script.addEventListener("load", resolveRuntime, { once: true });
      script.addEventListener("error", rejectRuntime, { once: true });
      return;
    }

    script = documentRef.createElement("script");
    script.async = true;
    script.src = assetUrl;
    script.dataset.docsViewerInlineMermaidRuntime = INLINE_MERMAID_ASSET_VERSION;
    script.addEventListener("load", resolveRuntime, { once: true });
    script.addEventListener("error", rejectRuntime, { once: true });
    documentRef.head.appendChild(script);
  });
}

function appendDescribedBy(element, id) {
  var describedBy = String(element.getAttribute("aria-describedby") || "").trim().split(/\s+/).filter(Boolean);
  if (describedBy.indexOf(id) === -1) describedBy.push(id);
  element.setAttribute("aria-describedby", describedBy.join(" "));
}

function createDiagramHost(documentRef, svgMarkup) {
  var template = documentRef.createElement("template");
  template.innerHTML = String(svgMarkup || "").trim();
  var svg = template.content.querySelector("svg");
  if (!svg || svg.namespaceURI !== "http://www.w3.org/2000/svg") {
    throw new Error("Mermaid did not return an SVG document.");
  }

  var title = svg.querySelector("title");
  var description = svg.querySelector("desc");
  if (!title || !title.textContent.trim() || !description || !description.textContent.trim()) {
    throw new Error("Inline Mermaid SVG requires a non-empty title and description.");
  }

  var host = documentRef.createElement("div");
  host.className = "docsViewer__diagram";
  host.dataset.docsViewerDiagramKind = "inline-mermaid";
  host.appendChild(svg);
  return host;
}

function releaseStaleFence(root, pre) {
  if (!root.contains(pre)) return;
  pre.removeAttribute("aria-busy");
  delete pre.dataset.docsViewerInlineMermaidState;
}

function showDiagramFailure(documentRef, pre, renderId) {
  var status = documentRef.createElement("p");
  status.className = "docsViewer__diagramError";
  status.id = renderId + "-status";
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  status.textContent = INLINE_MERMAID_ERROR_MESSAGE;
  pre.before(status);
  pre.dataset.docsViewerInlineMermaidState = "error";
  pre.setAttribute("aria-busy", "false");
  appendDescribedBy(pre, status.id);
}

export function createDocsViewerInlineMermaidAdapter(options) {
  var settings = options || {};
  var assetUrl = String(settings.assetUrl || INLINE_MERMAID_ASSET_URL);
  var loadMermaid = typeof settings.loadMermaid === "function" ? settings.loadMermaid : loadCheckedMermaidAsset;
  var warn = typeof settings.warn === "function" ? settings.warn : defaultWarning;
  var rendererPromise = null;
  var renderQueue = Promise.resolve();
  var renderSequence = 0;

  function rendererForMount(mountContext) {
    if (!rendererPromise) {
      rendererPromise = Promise.resolve().then(function () {
        return loadMermaid({
          assetUrl: assetUrl,
          document: mountContext.document,
          window: mountContext.window
        });
      }).then(function (renderer) {
        if (!renderer || typeof renderer.initialize !== "function" || typeof renderer.render !== "function") {
          throw new Error("The Mermaid browser runtime does not expose the required API.");
        }
        renderer.initialize(mermaidInitializationConfig());
        return renderer;
      });
    }
    return rendererPromise;
  }

  function renderSequentially(renderer, renderId, source) {
    var renderTask = renderQueue.then(function () {
      return renderer.render(renderId, source);
    });
    renderQueue = renderTask.then(function () {}, function () {});
    return renderTask;
  }

  async function mountDocument(mountContext) {
    var context = mountContext || {};
    var root = context.content;
    if (!root || typeof root.querySelectorAll !== "function") {
      return { found: 0, rendered: 0, failed: 0, stale: false };
    }

    var documentRef = context.document || root.ownerDocument;
    var windowRef = context.window || (documentRef ? documentRef.defaultView : null);
    var isCurrentMount = typeof context.isCurrentMount === "function" ? context.isCurrentMount : function () { return true; };
    var fences = Array.from(root.querySelectorAll("pre > code.language-mermaid")).filter(function (code) {
      var pre = code.parentElement;
      return pre && !pre.dataset.docsViewerInlineMermaidState;
    });
    var result = { found: fences.length, rendered: 0, failed: 0, stale: false };
    if (!fences.length) return result;

    for (var index = 0; index < fences.length; index += 1) {
      var code = fences[index];
      var pre = code.parentElement;
      if (!isCurrentMount() || !root.contains(pre)) {
        result.stale = true;
        break;
      }

      var renderId = "docs-viewer-inline-mermaid-" + String(++renderSequence);
      pre.dataset.docsViewerInlineMermaidState = "rendering";
      pre.setAttribute("aria-busy", "true");

      try {
        var renderer = await rendererForMount({ document: documentRef, window: windowRef });
        if (!isCurrentMount() || !root.contains(pre)) {
          releaseStaleFence(root, pre);
          result.stale = true;
          break;
        }

        var rendered = await renderSequentially(renderer, renderId, code.textContent || "");
        if (!isCurrentMount() || !root.contains(pre)) {
          releaseStaleFence(root, pre);
          result.stale = true;
          break;
        }

        var host = createDiagramHost(documentRef, rendered && rendered.svg);
        pre.replaceWith(host);
        result.rendered += 1;
        if (rendered && typeof rendered.bindFunctions === "function") {
          try {
            rendered.bindFunctions(host);
          } catch (bindingError) {
            warn("docs_viewer: inline Mermaid bindings unavailable", bindingError);
          }
        }
      } catch (error) {
        if (!isCurrentMount() || !root.contains(pre)) {
          releaseStaleFence(root, pre);
          result.stale = true;
          break;
        }
        showDiagramFailure(documentRef, pre, renderId);
        result.failed += 1;
        warn("docs_viewer: inline Mermaid diagram unavailable", error);
      }
    }

    return result;
  }

  return {
    mountDocument: mountDocument
  };
}

export const docsViewerInlineMermaidAdapter = createDocsViewerInlineMermaidAdapter();
