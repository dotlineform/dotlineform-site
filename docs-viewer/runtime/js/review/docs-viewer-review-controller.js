function createButton(documentRef, label) {
  var button = documentRef.createElement("button");
  button.type = "button";
  button.className = "docsViewer__actionButton";
  button.textContent = label;
  return button;
}

export function createDocsViewerReviewViewDefinitions() {
  return {
    controls: [{
      id: "review-package-controls",
      label: "Review package",
      ownerType: "app",
      surfaceId: "app-viewer",
      appKinds: ["review"],
      renderer: "review-package-controls"
    }]
  };
}

function renderReviewPackageControls(context) {
  var mount = context.existingRoot;
  if (!mount || mount.id !== "docsViewerReviewControlsMount") {
    mount = context.document.createElement("div");
    mount.id = "docsViewerReviewControlsMount";
    mount.className = "docsViewer__reviewControls";
    mount.setAttribute("role", "group");
    mount.setAttribute("aria-label", "Review package controls");

    var select = context.document.createElement("select");
    select.className = "docsViewer__searchInput docsViewer__reviewPackageSelect";
    select.setAttribute("aria-label", "Review package");
    var buildButton = createButton(context.document, "Build");
    buildButton.disabled = true;
    buildButton.setAttribute("data-docs-viewer-review-action", "build");
    var assetsButton = createButton(context.document, "Assets");
    assetsButton.setAttribute("data-docs-viewer-review-action", "assets");
    var openVsCodeButton = context.document.createElement("button");
    openVsCodeButton.id = "docsViewerReviewOpenVsCodeButton";
    openVsCodeButton.className = "docsViewer__documentActionButton";
    openVsCodeButton.type = "button";
    openVsCodeButton.disabled = true;
    openVsCodeButton.title = "Open in VS Code";
    openVsCodeButton.setAttribute("aria-label", "Open in VS Code");
    openVsCodeButton.setAttribute("data-docs-viewer-action", "open-vscode");
    openVsCodeButton.setAttribute("data-docs-viewer-review-action", "open-vscode");
    var openVsCodeIcon = context.document.createElement("img");
    openVsCodeIcon.src = new URL("../management/icons/vscode.svg", import.meta.url).href;
    openVsCodeIcon.alt = "";
    openVsCodeIcon.width = 20;
    openVsCodeIcon.height = 20;
    openVsCodeIcon.setAttribute("aria-hidden", "true");
    openVsCodeButton.replaceChildren(openVsCodeIcon);
    var canonicalLink = context.document.createElement("a");
    canonicalLink.className = "docsViewer__actionButton docsViewer__reviewCanonicalLink";
    canonicalLink.textContent = "Open canonical";
    canonicalLink.target = "_blank";
    canonicalLink.rel = "noopener";
    canonicalLink.hidden = true;
    mount.append(select, buildButton, assetsButton, openVsCodeButton, canonicalLink);
  }
  return { root: mount, interactive: mount.querySelector("select") };
}

export function createDocsViewerReviewControlRenderers() {
  return { "review-package-controls": renderReviewPackageControls };
}

export function reviewCanonicalDocumentHref(packageManifest, docId) {
  var sourceScope = String(packageManifest && packageManifest.source_scope || "").trim();
  var sourceSubScope = String(packageManifest && packageManifest.source_sub_scope || "").trim();
  var selectedDocId = String(docId || "").trim();
  return sourceScope && selectedDocId && !sourceSubScope
    ? "/docs/?scope=" + encodeURIComponent(sourceScope) + "&doc=" + encodeURIComponent(selectedDocId)
    : "";
}

export function createDocsViewerReviewController(options) {
  var settings = options || {};
  var documentRef = settings.document || document;
  var windowRef = settings.window || window;
  var provider = null;
  var manifest = null;
  var canonicalLink = null;
  var openVsCodeButton = null;
  var activeDocId = "";
  var activePackageId = "";
  var building = false;
  var openingSource = false;

  function projectBuildButton(buildButton) {
    if (!buildButton) return;
    buildButton.textContent = "Build";
    buildButton.disabled = building || !provider || !activePackageId;
  }

  function projectOpenVsCodeButton() {
    if (!openVsCodeButton) return;
    openVsCodeButton.disabled = openingSource || !provider || !activeDocId;
  }

  function projectCanonicalLink(docId) {
    if (!canonicalLink || !manifest) return;
    var href = reviewCanonicalDocumentHref(manifest, docId);
    canonicalLink.hidden = !href;
    canonicalLink.href = href;
  }

  function setStatus(message, isError) {
    var status = documentRef.getElementById("docsViewerStatus");
    if (!status) return;
    status.textContent = message || "";
    status.hidden = !message;
    status.classList.toggle("is-error", Boolean(isError));
  }

  function setProvider(value) {
    provider = value;
  }

  function start() {
    var mount = documentRef.getElementById("docsViewerReviewControlsMount");
    if (!mount || !provider) return Promise.resolve(null);
    var select = mount.querySelector("select");
    var buildButton = mount.querySelector('[data-docs-viewer-review-action="build"]');
    var assetsButton = mount.querySelector('[data-docs-viewer-review-action="assets"]');
    canonicalLink = mount.querySelector(".docsViewer__reviewCanonicalLink");
    openVsCodeButton = documentRef.getElementById("docsViewerReviewOpenVsCodeButton");
    if (!select || !buildButton || !assetsButton || !canonicalLink || !openVsCodeButton) {
      return Promise.reject(new Error("Docs Review package controls failed to render."));
    }
    projectBuildButton(buildButton);
    projectOpenVsCodeButton();

    select.addEventListener("change", function () {
      var url = new URL(windowRef.location.href);
      url.searchParams.set("package", select.value);
      url.searchParams.delete("doc");
      url.searchParams.delete("view");
      windowRef.location.assign(url.pathname + url.search);
    });
    buildButton.addEventListener("click", function () {
      if (building || !activePackageId) return;
      var requestedPackageId = activePackageId;
      building = true;
      projectBuildButton(buildButton);
      setStatus("Building review package...", false);
      provider.build(requestedPackageId).then(function (payload) {
        setStatus(payload.summary_text || "Built review package.", false);
        windowRef.location.reload();
      }).catch(function (error) {
        setStatus(error.message || "Review build failed.", true);
        building = false;
        projectBuildButton(buildButton);
      });
    });
    assetsButton.addEventListener("click", function () {
      provider.readAssetInventory().then(function (payload) {
        var names = Object.keys(payload.inventories || {});
        setStatus(names.length ? "Package inventories: " + names.join(", ") + "." : "No package asset inventories.", false);
      }).catch(function (error) {
        setStatus(error.message || "Asset inventory read failed.", true);
      });
    });
    openVsCodeButton.addEventListener("click", function () {
      if (!provider || !activeDocId || openingSource) return;
      var requestedDocId = activeDocId;
      openingSource = true;
      projectOpenVsCodeButton();
      provider.openSource(requestedDocId).then(function (payload) {
        setStatus(payload.summary_text || "Opened review source.", false);
      }).catch(function (error) {
        setStatus(error.message || "Review source could not be opened.", true);
      }).finally(function () {
        openingSource = false;
        projectOpenVsCodeButton();
      });
    });
    return Promise.all([provider.listCollections(), provider.readManifest()]).then(function (results) {
      var packages = results[0];
      manifest = results[1].manifest || {};
      var activePackage = packages.find(function (record) {
        return record.package_id === provider.activeCollectionId();
      });
      activePackageId = String(activePackage && activePackage.package_id || "").trim();
      projectBuildButton(buildButton);
      packages.forEach(function (record) {
        var option = documentRef.createElement("option");
        option.value = record.package_id;
        option.textContent = record.title || record.package_id;
        option.selected = record.package_id === provider.activeCollectionId();
        select.appendChild(option);
      });
      projectCanonicalLink(new URLSearchParams(windowRef.location.search).get("doc"));
      return results;
    }).catch(function (error) {
      setStatus(error.message || "Docs Review package discovery failed.", true);
      return null;
    });
  }

  function mountDocumentExtras(context) {
    var docId = String(context && context.doc && context.doc.doc_id || "").trim();
    activeDocId = docId;
    projectOpenVsCodeButton();
    projectCanonicalLink(docId);
  }

  return {
    mountDocumentExtras: mountDocumentExtras,
    setProvider: setProvider,
    start: start
  };
}
