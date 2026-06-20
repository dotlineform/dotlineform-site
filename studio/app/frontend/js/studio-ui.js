function freezeMap(map) {
  return Object.freeze({ ...map });
}

function selectorMap(roleMap) {
  return freezeMap(
    Object.fromEntries(
      Object.entries(roleMap).map(([key, value]) => [key, `[data-role="${value}"]`])
    )
  );
}

export function createUiContract({ role, className = {}, state = {} }) {
  const frozenRole = freezeMap(role);
  return Object.freeze({
    role: frozenRole,
    selector: selectorMap(frozenRole),
    className: freezeMap(className),
    state: freezeMap(state)
  });
}

export const studioWorksUi = createUiContract({
  role: {
    pageRoot: "studio-works",
    sortButton: "sort-button"
  },
  state: {
    active: "active"
  }
});
