import {
  setStudioRouteBusy,
  setStudioRouteReady
} from "./studio-route-state.js";

export function getTagStudioRouteRoot(state) {
  return state && state.routeRoot instanceof Element ? state.routeRoot : null;
}

export function buildTagStudioRouteStateDetail(state) {
  return {
    route: "series-tag-editor",
    mode: state && state.selectedWorkId ? "single" : "edit",
    service: state && state.saveMode === "post" ? "available" : "unavailable",
    recordLoaded: Boolean(state && state.seriesId)
  };
}

export function syncTagStudioRouteBusyState(state) {
  setStudioRouteBusy(getTagStudioRouteRoot(state), Boolean(state && state.isBusy), buildTagStudioRouteStateDetail(state));
}

export function markTagStudioRouteReady(state, ready) {
  setStudioRouteReady(getTagStudioRouteRoot(state), ready, buildTagStudioRouteStateDetail(state));
}
