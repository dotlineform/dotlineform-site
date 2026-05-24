import { getStudioText } from "./studio-config.js";
import { openNoticeModal } from "./studio-modal.js";
import { renderDataSharingPrepareResultBody } from "./data-sharing-prepare-render.js";

export function clearDataSharingPrepareResultModal(state) {
  if (state && state.modalHost) state.modalHost.innerHTML = "";
}

export function showDataSharingPrepareResultModal(state, payload, failed = false) {
  if (!state) return Promise.resolve();
  return openNoticeModal({
    root: state.root,
    restoreFocus: state.runButton,
    titleId: "dataSharingPrepareResultModalTitle",
    title: failed
      ? getStudioText(state.config, "data_sharing_prepare.result_title_failed", "Package preparation failed")
      : getStudioText(state.config, "data_sharing_prepare.result_title", "Package result"),
    bodyHtml: renderDataSharingPrepareResultBody(state, payload),
    closeLabel: getStudioText(state.config, "data_sharing_prepare.result_close", "Close")
  });
}
