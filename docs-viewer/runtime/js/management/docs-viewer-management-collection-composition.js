function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function frozenIds(values) {
  var seen = new Set();
  return Object.freeze((Array.isArray(values) ? values : []).map(cleanString).filter(function (value) {
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  }));
}

function capabilityState(value) {
  if (value == null || value === true) return { available: true, reason: "" };
  if (value === false) return { available: false, reason: "Action capability is unavailable." };
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Collection action capability must be boolean or an availability object.");
  }
  return {
    available: value.available === true,
    reason: cleanString(value.reason) || "Action capability is unavailable."
  };
}

function actionTarget(targetKind, context) {
  var actions = context.actionContext;
  var collection = actions.collectionTarget;
  if (targetKind === "collection") return collection;
  if (targetKind === "selection") {
    var selected = frozenIds(context.selection && context.selection.checkedDocIds);
    if (!selected.length) return null;
    return Object.freeze({
      collection: collection.collection,
      doc_ids: selected
    });
  }
  if (targetKind === "validated-detail") {
    var target = actions.documentTarget;
    if (!target || target.collection !== collection.collection) {
      throw new Error("Collection action requires the resolved detail target.");
    }
    return target;
  }
  throw new Error("Unknown collection action target kind: " + targetKind);
}

function actionRegistrar(context, placement) {
  return function registerAction(definition) {
    var record = definition && typeof definition === "object" ? definition : {};
    var actionId = cleanString(record.id);
    var declaredPlacement = cleanString(record.placement);
    var targetKind = cleanString(record.targetKind);
    var emptyState = cleanString(record.emptyState);
    var refreshEffect = cleanString(record.refreshEffect);
    if (!actionId) throw new Error("Collection action id is required.");
    if (declaredPlacement !== placement) {
      throw new Error("Collection action placement did not match its contribution host.");
    }
    if (!["enabled", "disabled", "omitted"].includes(emptyState)) {
      throw new Error("Collection action emptyState is invalid: " + emptyState);
    }
    if (![
      "none",
      "collection",
      "open-created-document",
      "commit-deleted-document"
    ].includes(refreshEffect)) {
      throw new Error("Collection action refreshEffect is invalid: " + refreshEffect);
    }
    if (typeof record.handler !== "function") {
      throw new Error("Collection action handler is required: " + actionId);
    }
    var capability = capabilityState(record.capability);
    var target = actionTarget(targetKind, context);
    var targetMissing = target == null;
    var hidden = targetMissing && emptyState === "omitted";
    var disabledReason = capability.available
      ? (targetMissing ? "Select one or more documents." : "")
      : capability.reason;
    return Object.freeze({
      actionId: actionId,
      disabledReason: disabledReason,
      enabled: capability.available && !targetMissing,
      hidden: hidden,
      invoke: function () {
        if (!capability.available || targetMissing) {
          return Promise.reject(new Error(disabledReason || "Collection action is unavailable."));
        }
        try {
          return Promise.resolve(record.handler(target, {
            refreshCollection: context.refreshCollection,
            refreshDocument: context.refreshAndOpenDocument,
            refreshEffect: refreshEffect
          }));
        } catch (error) {
          return Promise.reject(error);
        }
      },
      placement: placement,
      refreshEffect: refreshEffect,
      target: target,
      targetKind: targetKind
    });
  };
}

function createHost(parent, elementName, owner, position) {
  var host = parent.ownerDocument.createElement(elementName);
  host.dataset.reportContributionOwner = owner;
  host.dataset.reportContributionPosition = position;
  return host;
}

function appendWhenPopulated(parent, host) {
  if (host.childNodes.length) parent.appendChild(host);
}

export function createDocsViewerManagementCollectionContribution(options) {
  var defaultContribution = options.defaultContribution;
  function renderRow(context) {
    var leading = createHost(context.leadingHost, "span", "default", "row-leading");
    var titlePrefix = createHost(context.titlePrefixHost, "span", "default", "row-title-prefix");
    var trailing = createHost(context.trailingHost, "span", "default", "row-trailing");
    var result = defaultContribution.renderRow(Object.assign({}, context, {
      access: "manage",
      leadingHost: leading,
      titlePrefixHost: titlePrefix,
      trailingHost: trailing
    }));
    appendWhenPopulated(context.leadingHost, leading);
    appendWhenPopulated(context.titlePrefixHost, titlePrefix);
    appendWhenPopulated(context.trailingHost, trailing);
    return result;
  }

  function renderListToolbar(context) {
    var child = createHost(context.host, "div", "default", "list-toolbar");
    var actions = createHost(context.actionHost, "div", "default", "list-actions");
    defaultContribution.renderListToolbar(Object.assign({}, context, {
      access: "manage",
      host: child,
      actionHost: actions,
      registerAction: actionRegistrar({
        actionContext: context.actionContext,
        refreshAndOpenDocument: context.refreshAndOpenDocument,
        refreshCollection: context.refreshCollection
      }, "list-toolbar"),
      registerSelectionAction: function (definition, snapshot) {
        return actionRegistrar({
          actionContext: context.actionContext,
          refreshAndOpenDocument: context.refreshAndOpenDocument,
          refreshCollection: context.refreshCollection,
          selection: snapshot
        }, "selection")(definition);
      }
    }));
    appendWhenPopulated(context.host, child);
    appendWhenPopulated(context.actionHost, actions);
  }

  function renderDetailToolbar(context) {
    var child = createHost(context.host, "div", "default", "detail-toolbar");
    defaultContribution.renderDetailToolbar(Object.assign({}, context, {
      access: "manage",
      host: child,
      registerAction: actionRegistrar({
        actionContext: context.actionContext,
        refreshAndOpenDocument: context.refreshAndOpenDocument,
        refreshCollection: context.refreshCollection
      }, "detail-toolbar")
    }));
    appendWhenPopulated(context.host, child);
  }

  return {
    captureListState: defaultContribution.captureListState,
    restoreListState: defaultContribution.restoreListState,
    notify: defaultContribution.notify,
    renderDetailToolbar: renderDetailToolbar,
    renderListToolbar: renderListToolbar,
    renderRow: renderRow
  };
}
