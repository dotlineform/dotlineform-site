/** Present a Docs Media thumbnail in Content Detail or delegate an authored image. */
export function createDocsViewerManagedImageDetailAdapter(documentImageDetail) {
  return {
    mountPresentation(context) {
      const { reportImageKey } = context.targetContext;
      if (!reportImageKey) return documentImageDetail.mountPresentation(context);

      // Resolve the saved identity against the live report after entering Content Detail.
      const thumbnail = context.content.querySelector(`[data-docs-media-image="${CSS.escape(reportImageKey)}"]`);
      const image = thumbnail?.firstElementChild;
      if (!image) throw new Error("The selected report image is unavailable.");
      const label = image.alt;
      const root = context.document.createElement("section");
      root.className = "docsViewer__contentDetail docsViewer__contentDetail--image";
      root.dataset.docsContentDetailView = "image";

      const viewport = context.document.createElement("div");
      viewport.className = "docsViewer__imageDetailViewport";
      viewport.tabIndex = 0;
      viewport.setAttribute("role", "region");
      viewport.setAttribute("aria-label", label);
      viewport.appendChild(image);
      root.appendChild(viewport);

      return {
        focusTarget: viewport,
        invocationControl: thumbnail,
        label,
        newTabTarget: image.src,
        root,
        release() {
          thumbnail.appendChild(image);
          root.remove();
        }
      };
    }
  };
}
