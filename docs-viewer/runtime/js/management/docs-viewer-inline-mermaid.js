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
    darkMode: normalizeTheme(selectedTheme) === DARK_THEME
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

function directSvgChild(svg, localName) {
  for (var index = 0; index < svg.children.length; index += 1) {
    var child = svg.children[index];
    if (child.namespaceURI === "http://www.w3.org/2000/svg" && child.localName === localName) {
      return child;
    }
  }
  return null;
}

function appendAriaReference(element, attributeName, id) {
  var references = String(element.getAttribute(attributeName) || "").trim().split(/\s+/).filter(Boolean);
  if (references.indexOf(id) === -1) references.push(id);
  element.setAttribute(attributeName, references.join(" "));
}

function diagramAccessibilityFallback(context, diagramIndex) {
  var doc = context && context.doc ? context.doc : {};
  var documentTitle = String(doc.title || "").trim();
  var ordinal = Number(diagramIndex) + 1;
  var diagramLabel = "Diagram " + String(ordinal);
  return {
    title: documentTitle ? diagramLabel + " — " + documentTitle : diagramLabel,
    description: documentTitle
      ? "Inline Mermaid diagram " + String(ordinal) + " in " + documentTitle + ". No authored description was provided."
      : "Inline Mermaid diagram " + String(ordinal) + ". No authored description was provided."
  };
}

function createDiagramSvg(documentRef, svgMarkup, background, renderId, accessibilityFallback) {
  var template = documentRef.createElement("template");
  template.innerHTML = String(svgMarkup || "").trim();
  var svg = template.content.querySelector("svg");
  if (!svg || svg.namespaceURI !== "http://www.w3.org/2000/svg") {
    throw new Error("Mermaid did not return an SVG document.");
  }

  var fallback = accessibilityFallback || {};
  var fallbackFields = [];
  var title = directSvgChild(svg, "title");
  if (!title) {
    title = documentRef.createElementNS("http://www.w3.org/2000/svg", "title");
    svg.insertBefore(title, svg.firstChild);
  }
  if (!title.textContent.trim()) {
    title.textContent = String(fallback.title || "Diagram");
    fallbackFields.push("title");
  }

  var description = directSvgChild(svg, "desc");
  if (!description) {
    description = documentRef.createElementNS("http://www.w3.org/2000/svg", "desc");
    svg.insertBefore(description, title.nextSibling);
  }
  if (!description.textContent.trim()) {
    description.textContent = String(
      fallback.description || "Inline Mermaid diagram. No authored description was provided."
    );
    fallbackFields.push("description");
  }

  if (!title.id) title.id = String(renderId || "docs-viewer-inline-mermaid") + "-title";
  if (!description.id) description.id = String(renderId || "docs-viewer-inline-mermaid") + "-description";
  if (!svg.getAttribute("role")) svg.setAttribute("role", "img");
  appendAriaReference(svg, "aria-labelledby", title.id);
  appendAriaReference(svg, "aria-describedby", description.id);
  svg.style.backgroundColor = background;
  return {
    fallbackFields: fallbackFields,
    svg: svg
  };
}

function createDiagramHost(documentRef, svg) {
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
  var recordsByRoot = new Map();

  function recordsForRoot(root) {
    var records = recordsByRoot.get(root);
    if (!records) {
      records = [];
      recordsByRoot.set(root, records);
    }
    return records;
  }

  function registeredRecords() {
    var records = [];
    recordsByRoot.forEach(function (rootRecords) {
      records.push.apply(records, rootRecords);
    });
    return records;
  }

  function releaseDocument(releaseContext) {
    var context = releaseContext || {};
    var root = context.content;
    if (!root || !recordsByRoot.has(root)) return { released: 0 };
    var records = recordsByRoot.get(root) || [];
    recordsByRoot.delete(root);
    return { released: records.length };
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

  function renderSequentially(renderer, renderId, source, mountContext, theme) {
    var renderTask = renderQueue.then(function () {
      var config = mermaidInitializationConfig(mountContext, theme);
      renderer.initialize(config);
      return Promise.resolve(renderer.render(renderId, source)).then(function (rendered) {
        return {
          rendered: rendered,
          themeVariables: config.themeVariables
        };
      });
    });
    renderQueue = renderTask.then(function () {}, function () {});
    return renderTask;
  }

  function applyBindings(rendered, host) {
    if (!rendered || typeof rendered.bindFunctions !== "function") return;
    try {
      rendered.bindFunctions(host);
    } catch (bindingError) {
      warn("docs_viewer: inline Mermaid bindings unavailable", bindingError);
    }
  }

  function commitThemedDiagram(record, svg) {
    var host = record.host;
    var previousSvg = host ? host.firstElementChild : null;
    if (
      !previousSvg
      || host.children.length !== 1
      || previousSvg.namespaceURI !== "http://www.w3.org/2000/svg"
      || previousSvg.localName !== "svg"
    ) {
      throw new Error("Inline Mermaid registered host no longer owns one direct SVG.");
    }
    var detailAdapter = record.diagramDetailAdapter;
    if (!detailAdapter || typeof detailAdapter.refreshInlineDiagram !== "function") {
      throw new Error("Inline Mermaid registered host has no refreshable detail resource.");
    }

    previousSvg.replaceWith(svg);
    try {
      var detailResult = detailAdapter.refreshInlineDiagram({
        content: record.content,
        doc: record.doc,
        document: record.document,
        host: host,
        mountGeneration: record.mountGeneration,
        viewerScope: record.viewerScope,
        window: record.window
      });
      if (!detailResult || !detailResult.refreshed) {
        throw new Error(
          "Inline Mermaid detail refresh did not commit: "
          + String(detailResult && detailResult.reason ? detailResult.reason : "unknown")
        );
      }
    } catch (error) {
      svg.replaceWith(previousSvg);
      throw error;
    }
  }

  async function handleThemeChange(theme) {
    selectedTheme = normalizeTheme(theme);
    var refreshTheme = selectedTheme;
    var records = registeredRecords();
    var result = { found: records.length, rendered: 0, failed: 0 };
    if (!records.length) return result;

    var renderer;
    try {
      renderer = await rendererForMount({
        document: records[0].document,
        window: records[0].window
      });
    } catch (error) {
      result.failed = records.length;
      warn("docs_viewer: inline Mermaid theme refresh unavailable", error);
      return result;
    }

    for (var index = 0; index < records.length; index += 1) {
      var record = records[index];
      var renderId = "docs-viewer-inline-mermaid-" + String(++renderSequence);
      try {
        var themed = await renderSequentially(renderer, renderId, record.source, {
          content: record.content,
          document: record.document,
          viewerRoot: record.viewerRoot,
          window: record.window
        }, refreshTheme);
        var svgResult = createDiagramSvg(
          record.document,
          themed.rendered && themed.rendered.svg,
          themed.themeVariables.background,
          renderId,
          record.accessibilityFallback
        );
        commitThemedDiagram(record, svgResult.svg);
        applyBindings(themed.rendered, record.host);
        result.rendered += 1;
      } catch (error) {
        result.failed += 1;
        warn("docs_viewer: inline Mermaid theme refresh unavailable", error);
      }
    }
    return result;
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
      var accessibilityFallback = diagramAccessibilityFallback(context, index);
      pre.dataset.docsViewerInlineMermaidState = "rendering";
      pre.setAttribute("aria-busy", "true");

      try {
        var renderer = await rendererForMount({ document: documentRef, window: windowRef });
        if (!isCurrentMount() || !root.contains(pre)) {
          releaseStaleFence(root, pre);
          result.stale = true;
          break;
        }

        var source = code.textContent || "";
        var themed = await renderSequentially(renderer, renderId, source, {
          content: root,
          document: documentRef,
          viewerRoot: context.viewerRoot,
          window: windowRef
        }, currentTheme({
          document: documentRef
        }, selectedTheme));
        if (!isCurrentMount() || !root.contains(pre)) {
          releaseStaleFence(root, pre);
          result.stale = true;
          break;
        }

        var svgResult = createDiagramSvg(
          documentRef,
          themed.rendered && themed.rendered.svg,
          themed.themeVariables.background,
          renderId,
          accessibilityFallback
        );
        if (svgResult.fallbackFields.length) {
          var missingDirectives = svgResult.fallbackFields.map(function (field) {
            return field === "title" ? "accTitle" : "accDescr";
          });
          warn(
            "docs_viewer: inline Mermaid accessibility fallback applied",
            new Error("Missing authored Mermaid accessibility metadata: " + missingDirectives.join(", ") + ".")
          );
        }
        var host = createDiagramHost(documentRef, svgResult.svg);
        pre.replaceWith(host);
        result.rendered += 1;
        applyBindings(themed.rendered, host);
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
        recordsForRoot(root).push({
          accessibilityFallback: accessibilityFallback,
          content: root,
          diagramDetailAdapter: detailAdapter,
          doc: context.doc,
          document: documentRef,
          host: host,
          mountGeneration: context.mountGeneration,
          source: source,
          viewerRoot: context.viewerRoot,
          viewerScope: context.viewerScope,
          window: windowRef
        });
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
    mountDocument: mountDocument,
    releaseDocument: releaseDocument
  };
}

export const docsViewerInlineMermaidAdapter = createDocsViewerInlineMermaidAdapter();
