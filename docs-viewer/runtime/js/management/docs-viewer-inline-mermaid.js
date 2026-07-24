const INLINE_MERMAID_ASSET_URL = "/docs-viewer/runtime/vendor/mermaid/11.16.0/mermaid.min.js";
const INLINE_MERMAID_ASSET_VERSION = "11.16.0";
const LIGHT_THEME = "light";
const DARK_THEME = "dark";

export const INLINE_MERMAID_ERROR_MESSAGE = "Diagram could not be rendered. Mermaid source is shown below.";

function normalizeTheme(value) {
  return value === DARK_THEME ? DARK_THEME : LIGHT_THEME;
}

function currentTheme(context, selectedTheme) {
  var documentRef = context.document;
  var documentElement = documentRef ? documentRef.documentElement : null;
  var attributeTheme = documentElement ? documentElement.getAttribute("data-theme") : "";
  if (attributeTheme === LIGHT_THEME || attributeTheme === DARK_THEME) {
    return attributeTheme;
  }
  return normalizeTheme(selectedTheme);
}

function viewerStyleRoot(context) {
  if (context.viewerRoot) return context.viewerRoot;
  var content = context.content;
  if (content && typeof content.closest === "function") {
    var viewerRoot = content.closest(".docsViewer");
    if (viewerRoot) return viewerRoot;
  }
  return content || (context.document ? context.document.documentElement : null);
}

function resolvedSemanticValue(style, propertyName) {
  var value = style ? String(style.getPropertyValue(propertyName) || "").trim() : "";
  if (!value || value.indexOf("var(") !== -1) {
    throw new Error("Inline Mermaid requires a resolved Docs Viewer semantic token: " + propertyName);
  }
  return value;
}

function resolveThemeVariables(context, selectedTheme) {
  var windowRef = context.window;
  var styleRoot = viewerStyleRoot(context);
  if (!windowRef || typeof windowRef.getComputedStyle !== "function" || !styleRoot) {
    throw new Error("Inline Mermaid requires the mounted Docs Viewer style context.");
  }
  var style = windowRef.getComputedStyle(styleRoot);
  var panel = resolvedSemanticValue(style, "--docs-viewer-panel");
  var subtlePanel = resolvedSemanticValue(style, "--docs-viewer-panel-2");
  var primaryText = resolvedSemanticValue(style, "--docs-viewer-text");
  var strongBorder = resolvedSemanticValue(style, "--docs-viewer-border-strong");
  var mutedText = resolvedSemanticValue(style, "--docs-viewer-muted");
  var selectionSurface = resolvedSemanticValue(style, "--docs-viewer-selection-bg");
  var selectionText = resolvedSemanticValue(style, "--docs-viewer-selection-text");
  var canvas = resolvedSemanticValue(style, "--docs-viewer-bg");
  var fontFamily = resolvedSemanticValue(style, "--docs-viewer-font-sans");
  return {
    background: panel,
    primaryColor: subtlePanel,
    mainBkg: subtlePanel,
    primaryTextColor: primaryText,
    textColor: primaryText,
    nodeTextColor: primaryText,
    titleColor: primaryText,
    actorTextColor: primaryText,
    primaryBorderColor: strongBorder,
    nodeBorder: strongBorder,
    actorBorder: strongBorder,
    noteBorderColor: strongBorder,
    lineColor: mutedText,
    arrowheadColor: mutedText,
    secondaryColor: selectionSurface,
    activationBkgColor: selectionSurface,
    noteBkgColor: selectionSurface,
    secondaryTextColor: selectionText,
    noteTextColor: selectionText,
    tertiaryColor: canvas,
    clusterBkg: canvas,
    fontFamily: fontFamily,
    darkMode: currentTheme(context, selectedTheme) === DARK_THEME
  };
}

function mermaidInitializationConfig(context, selectedTheme) {
  return {
    startOnLoad: false,
    suppressErrorRendering: true,
    theme: "base",
    themeVariables: resolveThemeVariables(context, selectedTheme),
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
  var selectedTheme = LIGHT_THEME;

  function handleThemeChange(theme) {
    selectedTheme = normalizeTheme(theme);
  }

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
        return renderer;
      });
    }
    return rendererPromise;
  }

  function renderSequentially(renderer, renderId, source, mountContext) {
    var renderTask = renderQueue.then(function () {
      renderer.initialize(mermaidInitializationConfig(mountContext, selectedTheme));
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

        var rendered = await renderSequentially(renderer, renderId, code.textContent || "", {
          content: root,
          document: documentRef,
          viewerRoot: context.viewerRoot,
          window: windowRef
        });
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
        var detailAdapter = context.diagramDetailAdapter;
        if (detailAdapter && typeof detailAdapter.registerInlineDiagram === "function") {
          try {
            detailAdapter.registerInlineDiagram({
              content: root,
              doc: context.doc,
              document: documentRef,
              host: host,
              mountGeneration: context.mountGeneration,
              viewerScope: context.viewerScope,
              window: windowRef
            });
          } catch (detailError) {
            warn("docs_viewer: inline Mermaid detail registration unavailable", detailError);
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
    handleThemeChange: handleThemeChange,
    mountDocument: mountDocument
  };
}

export const docsViewerInlineMermaidAdapter = createDocsViewerInlineMermaidAdapter();
