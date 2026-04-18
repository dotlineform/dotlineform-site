import { STUDIO_WRITE_ENDPOINTS, postJson } from "./studio-transport.js";

function updateStatus(message, isError = false) {
  const statusNode = document.getElementById("docsViewerStatus");
  if (!statusNode) return;
  statusNode.textContent = message;
  statusNode.classList.toggle("is-error", Boolean(isError));
}

async function initDocsRebuildButton() {
  const button = document.getElementById("docsViewerRebuildButton");
  if (!button) return;

  button.addEventListener("click", async () => {
    button.disabled = true;
    updateStatus("Rebuilding docs...");

    try {
      const payload = await postJson(STUDIO_WRITE_ENDPOINTS.buildDocs, {});
      updateStatus(payload.summary_text || "Docs rebuilt.");
    } catch (error) {
      updateStatus(error.message || "Docs rebuild failed.", true);
    } finally {
      button.disabled = false;
    }
  });
}

initDocsRebuildButton();
