function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function callback(owner, name) {
  return owner && typeof owner[name] === "function" ? owner[name] : null;
}

function frozenIds(values) {
  var seen = new Set();
  return Object.freeze((Array.isArray(values) ? values : []).map(cleanString).filter(function (value) {
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  }));
}

function exactCollection(value) {
  var keys = Object.keys(value || {}).sort();
  var scope = cleanString(value && value.scope).toLowerCase();
  var subScope = cleanString(value && value.sub_scope).toLowerCase();
  if (
    keys.length !== 2
    || keys[0] !== "scope"
    || keys[1] !== "sub_scope"
    || !scope
    || !subScope
  ) {
    throw new Error("Sub-scope action collection target is invalid.");
  }
  return Object.freeze({ scope: scope, sub_scope: subScope });
}

function exactDetail(value, collection) {
  var keys = Object.keys(value || {}).sort();
  var docId = cleanString(value && value.doc_id);
  if (
    keys.length !== 3
    || keys[0] !== "doc_id"
    || keys[1] !== "scope"
    || keys[2] !== "sub_scope"
    || cleanString(value && value.scope).toLowerCase() !== collection.scope
    || cleanString(value && value.sub_scope).toLowerCase() !== collection.sub_scope
    || !docId
  ) {
    throw new Error("Sub-scope action detail target is invalid.");
  }
  return Object.freeze({
    scope: collection.scope,
    sub_scope: collection.sub_scope,
    doc_id: docId
  });
}

function capabilityState(value) {
  if (value == null || value === true) return { available: true, reason: "" };
  if (value === false) return { available: false, reason: "Action capability is unavailable." };
  if (typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Sub-scope action capability must be boolean or an availability object.");
  }
  return {
    available: value.available === true,
    reason: cleanString(value.reason) || "Action capability is unavailable."
  };
}

function actionTarget(targetKind, context) {
  var collection = exactCollection(context.collection);
  if (targetKind === "collection") return collection;
  if (targetKind === "selection") {
    var selected = frozenIds(context.selection && context.selection.checkedDocIds);
    if (!selected.length) return null;
    return Object.freeze({
      scope: collection.scope,
      sub_scope: collection.sub_scope,
      doc_ids: selected
    });
  }
  if (targetKind === "validated-detail") {
    return exactDetail(context.target, collection);
  }
  throw new Error("Unknown sub-scope action target kind: " + targetKind);
}

function actionRegistrar(context, placement) {
  return function registerAction(definition) {
    var record = definition && typeof definition === "object" ? definition : {};
    var actionId = cleanString(record.id);
    var declaredPlacement = cleanString(record.placement);
    var targetKind = cleanString(record.targetKind);
    var emptyState = cleanString(record.emptyState);
    var refreshEffect = cleanString(record.refreshEffect);
    if (!actionId) throw new Error("Sub-scope action id is required.");
    if (declaredPlacement !== placement) {
      throw new Error("Sub-scope action placement did not match its contribution host.");
    }
    if (!["enabled", "disabled", "omitted"].includes(emptyState)) {
      throw new Error("Sub-scope action emptyState is invalid: " + emptyState);
    }
    if (![
      "none",
      "collection",
      "open-created-document",
      "commit-deleted-document"
    ].includes(refreshEffect)) {
      throw new Error("Sub-scope action refreshEffect is invalid: " + refreshEffect);
    }
    if (typeof record.handler !== "function") {
      throw new Error("Sub-scope action handler is required: " + actionId);
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
          return Promise.reject(new Error(disabledReason || "Sub-scope action is unavailable."));
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

function contributionId(contribution, fallback) {
  return cleanString(contribution && contribution.id) || fallback;
}

export function composeDocsViewerManagementSubscopeContributions(options = {}) {
  var defaultContribution = options.defaultContribution || null;
  var customisationContribution = options.customisationContribution || null;
  var owners = [defaultContribution, customisationContribution].filter(Boolean);
  var currentList = null;
  var selectionSnapshot = Object.freeze({
    active: false,
    checkedDocIds: Object.freeze([]),
    eligibleDocIds: Object.freeze([])
  });

  function containFailure(error, reason) {
    var handler = currentList
      && currentList.context
      && currentList.context.handleContributionError;
    if (typeof handler !== "function") throw error;
    handler(error, cleanString(reason) || "customisation-callback-failed");
  }

  function normalizedSelection(value) {
    var snapshot = value && typeof value === "object" ? value : {};
    return Object.freeze({
      active: snapshot.active === true,
      checkedDocIds: frozenIds(snapshot.checkedDocIds),
      eligibleDocIds: frozenIds(snapshot.eligibleDocIds)
    });
  }

  function renderSelectionContribution(reason) {
    if (!currentList || !customisationContribution) return;
    var renderSelection = callback(customisationContribution, "renderSelectionToolbar");
    var host = currentList.selectionHost;
    host.replaceChildren();
    if (!renderSelection) return;
    renderSelection({
      access: "manage",
      collection: currentList.context.collection,
      documents: currentList.context.documents,
      host: host,
      reason: cleanString(reason),
      registerAction: actionRegistrar({
        collection: currentList.context.collection,
        refreshAndOpenDocument: currentList.context.refreshAndOpenDocument,
        refreshCollection: currentList.context.refreshCollection,
        selection: selectionSnapshot
      }, "selection"),
      selection: selectionSnapshot
    });
    if (host.childNodes.length && !host.parentNode) {
      currentList.host.appendChild(host);
    } else if (!host.childNodes.length && host.parentNode) {
      host.remove();
    }
  }

  function publishSelection(value, reason) {
    selectionSnapshot = normalizedSelection(value);
    try {
      if (customisationContribution) {
        var notify = callback(customisationContribution, "notify");
        if (notify && currentList) {
          notify({
            type: "selection",
            access: "manage",
            collection: currentList.context.collection,
            selection: selectionSnapshot,
            reason: cleanString(reason) || "selection-projected"
          });
        }
      }
      renderSelectionContribution(reason);
    } catch (error) {
      containFailure(error, "selection-callback-failed");
    }
  }

  function notify(event) {
    owners.forEach(function (owner) {
      var handler = callback(owner, "notify");
      if (handler) handler(event);
    });
    if (event && event.type === "unmount") currentList = null;
  }

  function createFilters(context) {
    var filters = [];
    owners.forEach(function (owner) {
      var create = callback(owner, "createFilters");
      if (!create) return;
      var created = create(context);
      if (!Array.isArray(created)) {
        throw new Error("Sub-scope customisation filters must be an array.");
      }
      filters.push.apply(filters, created);
    });
    return filters;
  }

  function renderRow(context) {
    var accessibleLabels = [];
    owners.forEach(function (owner, index) {
      var render = callback(owner, "renderRow");
      if (!render) return;
      var ownerId = contributionId(owner, index === 0 ? "default" : "customisation");
      var leading = createHost(context.leadingHost, "span", ownerId, "row-leading");
      var titlePrefix = createHost(context.titlePrefixHost, "span", ownerId, "row-title-prefix");
      var trailing = createHost(context.trailingHost, "span", ownerId, "row-trailing");
      var result = render(Object.assign({}, context, {
        access: "manage",
        documents: currentList ? currentList.context.documents : [],
        leadingHost: leading,
        titlePrefixHost: titlePrefix,
        trailingHost: trailing
      })) || {};
      appendWhenPopulated(context.leadingHost, leading);
      appendWhenPopulated(context.titlePrefixHost, titlePrefix);
      appendWhenPopulated(context.trailingHost, trailing);
      if (Array.isArray(result.accessibleLabels)) {
        accessibleLabels.push.apply(
          accessibleLabels,
          result.accessibleLabels.map(cleanString).filter(Boolean)
        );
      }
    });
    return { accessibleLabels: accessibleLabels };
  }

  function renderListToolbar(context) {
    var host = context.host;
    currentList = {
      context: context,
      host: host,
      selectionHost: createHost(host, "div", "customisation", "selection")
    };
    owners.forEach(function (owner, index) {
      var render = callback(owner, "renderListToolbar");
      if (!render) return;
      var ownerId = contributionId(owner, index === 0 ? "default" : "customisation");
      var child = createHost(host, "div", ownerId, "list-toolbar");
      render(Object.assign({}, context, {
        access: "manage",
        host: child,
        publishSelection: publishSelection,
        registerAction: actionRegistrar({
          collection: context.collection,
          refreshAndOpenDocument: context.refreshAndOpenDocument,
          refreshCollection: context.refreshCollection,
          selection: selectionSnapshot
        }, "list-toolbar"),
        registerSelectionAction: function (definition, snapshot) {
          return actionRegistrar({
            collection: context.collection,
            refreshAndOpenDocument: context.refreshAndOpenDocument,
            refreshCollection: context.refreshCollection,
            selection: normalizedSelection(snapshot)
          }, "selection")(definition);
        }
      }));
      appendWhenPopulated(host, child);
    });
    renderSelectionContribution("list-toolbar-rendered");
  }

  function renderDetailToolbar(context) {
    owners.forEach(function (owner, index) {
      var render = callback(owner, "renderDetailToolbar");
      if (!render) return;
      var ownerId = contributionId(owner, index === 0 ? "default" : "customisation");
      var child = createHost(context.host, "div", ownerId, "detail-toolbar");
      render(Object.assign({}, context, {
        access: "manage",
        host: child,
        registerAction: actionRegistrar({
          collection: context.collection,
          refreshAndOpenDocument: context.refreshAndOpenDocument,
          refreshCollection: context.refreshCollection,
          target: context.target
        }, "detail-toolbar")
      }));
      appendWhenPopulated(context.host, child);
    });
  }

  function projectDetailInfo(context) {
    var project = callback(customisationContribution, "projectDetailInfo");
    if (!project) return null;
    return project(Object.assign({}, context, { access: "manage" }));
  }

  return {
    id: "management_composition",
    createFilters: createFilters,
    notify: notify,
    projectDetailInfo: projectDetailInfo,
    renderDetailToolbar: renderDetailToolbar,
    renderListToolbar: renderListToolbar,
    renderRow: renderRow
  };
}
