import { getAnalyticsText } from "./analytics-config.js";
import { openNoticeModal } from "./analytics-modal.js";
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
      ? getAnalyticsText(state.config, "data_sharing_prepare.result_title_failed", "Package preparation failed")
      : getAnalyticsText(state.config, "data_sharing_prepare.result_title", "Package result"),
    bodyHtml: renderDataSharingPrepareResultBody(state, payload),
    closeLabel: getAnalyticsText(state.config, "data_sharing_prepare.result_close", "Close")
  });
}
