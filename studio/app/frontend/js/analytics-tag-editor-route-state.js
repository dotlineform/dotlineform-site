import {
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";

export function getAnalyticsTagEditorRouteRoot(state) {
  return state && state.routeRoot instanceof Element ? state.routeRoot : null;
}

export function buildAnalyticsTagEditorRouteStateDetail(state) {
  return {
    route: "series-tag-editor",
    mode: state && state.selectedWorkId ? "single" : "edit",
    service: state && state.saveMode === "post" ? "available" : "unavailable",
    recordLoaded: Boolean(state && state.seriesId)
  };
}

export function syncAnalyticsTagEditorRouteBusyState(state) {
  setStudioRouteBusy(getAnalyticsTagEditorRouteRoot(state), Boolean(state && state.isBusy), buildAnalyticsTagEditorRouteStateDetail(state));
}

export function markAnalyticsTagEditorRouteReady(state, ready) {
  setStudioRouteReady(getAnalyticsTagEditorRouteRoot(state), ready, buildAnalyticsTagEditorRouteStateDetail(state));
}
