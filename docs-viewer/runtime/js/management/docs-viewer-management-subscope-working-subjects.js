import {
  encodeDecodedLocalTarget
} from "./docs-viewer-management-client.js";
import {
  hasDocsViewerAssignableFieldGroup
} from "../shared/docs-viewer-config-controller.js";
import {
  openDocsViewerProjectSubjectModal
} from "./docs-viewer-management-project-subject-modal.js";
import {
  normalizeDocsViewerAuthoringSubject
} from "./docs-viewer-management-document-subject.js";
import {
  appendProjectSubjectIcon
} from "../reports/project-subject-icons.js";
import {
  loadCatalogueTargetSupport
} from "./source-editor/catalogue-token-targets.js";

const WORKS_CUSTOMISATION_ID = "working_works";
const PROCESSING_CUSTOMISATION_ID = "working_processing";
const AUTHORING_SUBJECT_GROUP_ID = "authoring_subject";
const PROJECT_SORT_MODES = Object.freeze([
  "title-asc",
  "title-desc",
  "subject-asc",
  "subject-desc"
]);

function cleanString(value) {
  return String(value == null ? "" : value).trim();
}

function exactCollection(value) {
  var keys = Object.keys(value || {}).sort();
  var scope = cleanString(value && value.scope).toLowerCase();
  var subScope = cleanString(value && value.sub_scope).toLowerCase();
  if (keys.length !== 2 || keys[0] !== "scope" || keys[1] !== "sub_scope" || !scope || !subScope) {
    throw new Error("Working subject customisation collection target is invalid.");
  }
  return Object.freeze({ scope: scope, sub_scope: subScope });
}

function authoringSubject(documentRecord) {
  return normalizeDocsViewerAuthoringSubject(
    documentRecord && documentRecord.authoring_subject,
    {
      errorMessage: "Working document authoring_subject must be a normalized object."
    }
  );
}

function subjectTargetIdentity(kind, key) {
  return cleanString(kind) + ":" + cleanString(key);
}

function subjectTargetTitles(support) {
  var titles = new Map();
  var targets = support && Array.isArray(support.searchableTargets)
    ? support.searchableTargets
    : [];
  targets.forEach(function (target) {
    var kind = cleanString(target && target.targetType);
    var key = cleanString(target && target.targetId);
    var title = cleanString(target && target.title);
    if (!["work", "series"].includes(kind) || !key || !title) return;
    titles.set(subjectTargetIdentity(kind, key), title);
  });
  return titles;
}

function loadSubjectTargetTitles(options) {
  return loadCatalogueTargetSupport({
    fetch: options.fetch,
    allowedTargetTypes: ["work", "series"]
  }).then(function (support) {
    return {
      available: true,
      titles: subjectTargetTitles(support)
    };
  }).catch(function () {
    return {
      available: false,
      titles: new Map()
    };
  });
}

export function projectDocsViewerWorkingSubject(documentRecord, targetLookup) {
  var subject = authoringSubject(documentRecord);
  if (subject.state === "valid") {
    var targetTitles = targetLookup && targetLookup.titles instanceof Map
      ? targetLookup.titles
      : new Map();
    var targetTitle = targetTitles.get(subjectTargetIdentity(subject.kind, subject.key)) || "";
    var targetUnavailable = (
      ["work", "series"].includes(subject.kind)
      && targetLookup
      && targetLookup.available === true
      && !targetTitle
    );
    return {
      kind: subject.kind,
      key: subject.key,
      label: targetTitle || subject.key,
      state: targetUnavailable ? "unavailable" : "valid",
      targetTitle: targetTitle
    };
  }
  if (["malformed", "conflicting"].includes(subject.state)) {
    return {
      kind: subject.kind,
      key: "",
      label: "Subject warning",
      state: "warning",
      targetTitle: ""
    };
  }
  return {
    kind: "none",
    key: "",
    label: "",
    state: "none",
    targetTitle: ""
  };
}

function previewSubjectHref(options, subject) {
  var base = cleanString(options.publicPreviewBase).replace(/\/+$/, "");
  if (!base) throw new Error("Working subject preview is not configured.");
  var path = subject.kind === "work"
    ? "/works/?work=" + encodeURIComponent(subject.key)
    : "/series/?series=" + encodeURIComponent(subject.key);
  return new URL(path, base + "/").toString();
}

function subjectAccessibleLabel(subject) {
  var kindLabel = ({ folder: "Folder", work: "Work", series: "Series", detail: "Detail" })[subject.kind];
  if (!kindLabel) return "";
  if (subject.targetTitle) {
    return kindLabel + " subject " + subject.targetTitle + ", " + subject.key;
  }
  return kindLabel + " subject " + subject.key
    + (subject.state === "unavailable" ? ", unavailable" : "");
}

function renderSubjectCell(context, options, targetLookup) {
  var settings = context || {};
  var host = settings.trailingHost;
  if (!host) return;
  var subject = projectDocsViewerWorkingSubject(settings.document, targetLookup);
  var cell = host.ownerDocument.createElement("span");
  cell.className = "docsViewerReport__projectSubjectCell";
  cell.dataset.projectSubjectState = subject.state;
  if (subject.state === "none") {
    cell.textContent = "—";
    cell.setAttribute("aria-label", "No subject");
    host.appendChild(cell);
    return;
  }
  if (subject.state === "warning") {
    cell.textContent = "⚠️ Subject warning";
    host.appendChild(cell);
    return;
  }
  if (subject.state === "unavailable") {
    var unavailable = host.ownerDocument.createElement("span");
    unavailable.className = "docsViewerReport__projectSubjectUnavailable";
    unavailable.dataset.projectSubjectKind = subject.kind;
    unavailable.dataset.projectSubjectKey = subject.key;
    appendProjectSubjectIcon(unavailable, subject.kind);
    var unavailableLabel = host.ownerDocument.createElement("span");
    unavailableLabel.className = "docsViewerReport__projectSubjectUnavailableLabel";
    unavailableLabel.textContent = subject.label;
    unavailable.appendChild(unavailableLabel);
    unavailable.setAttribute("aria-label", subjectAccessibleLabel(subject));
    unavailable.title = subjectAccessibleLabel(subject);
    cell.appendChild(unavailable);
    host.appendChild(cell);
    return;
  }
  var link = host.ownerDocument.createElement(subject.kind === "detail" ? "span" : "a");
  link.className = subject.kind === "detail"
    ? "docsViewerReport__projectSubjectLink"
    : "docsViewerReport__cellLink docsViewerReport__projectSubjectLink";
  link.dataset.projectSubjectKind = subject.kind;
  link.dataset.projectSubjectKey = subject.key;
  appendProjectSubjectIcon(link, subject.kind);
  var label = host.ownerDocument.createElement("span");
  label.textContent = subject.label;
  link.appendChild(label);
  link.setAttribute("aria-label", subjectAccessibleLabel(subject));
  if (subject.kind === "folder") {
    var encodedPath = encodeDecodedLocalTarget(subject.key);
    if (!encodedPath) throw new Error("Working document Folder subject is invalid.");
    link.href = "#";
    link.dataset.docsViewerLocalTarget = encodedPath;
    link.title = "Open " + subject.key + " in Finder";
  } else if (subject.kind !== "detail") {
    link.href = previewSubjectHref(options, subject);
    link.title = "Open " + subjectAccessibleLabel(subject) + " in local preview";
  }
  cell.appendChild(link);
  host.appendChild(cell);
}

function compareText(collator, left, right) {
  return collator.compare(cleanString(left), cleanString(right));
}

function compareProjectDocuments(context, targetLookup, collator) {
  var settings = context || {};
  var sortMode = cleanString(settings.sortMode);
  if (!PROJECT_SORT_MODES.includes(sortMode)) {
    throw new Error("Works list sort mode is invalid: " + sortMode);
  }
  var direction = sortMode.endsWith("-desc") ? -1 : 1;
  var left = settings.left || {};
  var right = settings.right || {};
  var comparison;
  if (sortMode.startsWith("subject-")) {
    var leftSubject = projectDocsViewerWorkingSubject(left, targetLookup);
    var rightSubject = projectDocsViewerWorkingSubject(right, targetLookup);
    var stateOrder = { valid: 0, unavailable: 1, warning: 2, none: 3 };
    comparison = stateOrder[leftSubject.state] - stateOrder[rightSubject.state];
    if (comparison) return comparison;
    comparison = compareText(collator, leftSubject.label, rightSubject.label) * direction;
    if (comparison) return comparison;
    comparison = compareText(collator, leftSubject.kind, rightSubject.kind) * direction;
    if (comparison) return comparison;
    comparison = compareText(collator, leftSubject.key, rightSubject.key) * direction;
    if (comparison) return comparison;
  } else {
    comparison = compareText(collator, left.title, right.title) * direction;
    if (comparison) return comparison;
  }
  comparison = compareText(collator, left.title, right.title);
  if (comparison) return comparison;
  return compareText(collator, left.doc_id, right.doc_id);
}

function listSortButton(context, key, label) {
  var settings = context || {};
  var sort = settings.sort || {};
  var active = cleanString(sort.mode).startsWith(key + "-");
  var ascending = cleanString(sort.mode) === key + "-asc";
  var button = settings.host.ownerDocument.createElement("button");
  button.className = "docsViewerReport__sortButton";
  button.type = "button";
  button.dataset.projectSort = key;
  button.textContent = label;
  if (active) button.dataset.state = "active";
  var indicator = settings.host.ownerDocument.createElement("span");
  indicator.className = "docsViewerReport__sortIndicator";
  indicator.setAttribute("aria-hidden", "true");
  indicator.textContent = active ? (ascending ? "▲" : "▼") : "";
  button.appendChild(indicator);
  button.setAttribute(
    "aria-label",
    "Sort by " + label + (active ? (ascending ? " descending" : " ascending") : " ascending")
  );
  button.addEventListener("click", function () {
    sort.setMode(key + (active && ascending ? "-desc" : "-asc"));
  });
  return button;
}

function renderListHead(context) {
  var settings = context || {};
  var host = settings.host;
  if (!host || !settings.sort || typeof settings.sort.setMode !== "function") return;
  var selection = host.ownerDocument.createElement("span");
  selection.className = "docsViewerReport__projectSelectionHead";
  selection.setAttribute("aria-hidden", "true");
  host.appendChild(selection);
  host.appendChild(listSortButton(settings, "title", "Doc title"));
  host.appendChild(listSortButton(settings, "subject", "Subject"));

}

function folderPath(documentRecord) {
  var subject = authoringSubject(documentRecord);
  return subject.state === "valid" && subject.kind === "folder" ? subject.key : "";
}

function renderWorkingSubjectRow(context, options, targetLookup) {
  renderSubjectCell(context, options, targetLookup);
  return { accessibleLabels: [] };
}

function renderOpenInFinder(context, options) {
  var settings = context || {};
  var host = settings.host;
  if (!host || typeof settings.registerAction !== "function") return;
  var path = folderPath(settings.document);
  var registration = settings.registerAction({
    id: "open-project-folder",
    placement: "detail-toolbar",
    targetKind: "validated-detail",
    capability: path ? true : { available: false, reason: "This document has no valid Folder subject." },
    emptyState: "disabled",
    refreshEffect: "none",
    handler: function () {
      if (!path) throw new Error("This document has no valid Folder subject.");
      var encodedPath = encodeDecodedLocalTarget(path);
      if (!encodedPath) throw new Error("This document has an invalid Folder subject.");
      if (typeof options.openLocalTarget !== "function") throw new Error("Open in Finder is unavailable.");
      return options.openLocalTarget(encodedPath, options.clientOptions || {}).then(function (response) {
        if (typeof options.setStatus === "function") {
          options.setStatus(cleanString(response && response.summary_text) || "Local target opened.", false);
        }
        return response;
      });
    }
  });
  var button = host.ownerDocument.createElement("button");
  button.className = "docsViewerReport__button docsReportDetail__iconButton docsReportDetail__openProjectFolder";
  button.type = "button";
  button.dataset.docsProjectsOpenFolder = "true";
  button.textContent = "Open in Finder";
  button.disabled = !registration.enabled;
  if (registration.disabledReason) button.title = registration.disabledReason;
  button.addEventListener("click", function () {
    registration.invoke().catch(function (error) {
      if (typeof options.setStatus === "function") {
        options.setStatus(error && error.message ? error.message : "Open in Finder failed.", true);
      }
    });
  });
  host.appendChild(button);
}

function renderAssignSubject(context, options, assignSubjectAvailable) {
  var settings = context || {};
  var host = settings.host;
  if (!host || !assignSubjectAvailable || typeof settings.registerAction !== "function") return;
  var serviceAvailable = typeof options.readMetadata === "function" && typeof options.assignFieldGroup === "function";
  var button = host.ownerDocument.createElement("button");
  var registration = settings.registerAction({
    id: "assign-subject",
    placement: "detail-toolbar",
    targetKind: "validated-detail",
    capability: serviceAvailable ? true : { available: false, reason: "Subject assignment service is unavailable." },
    emptyState: "omitted",
    refreshEffect: "none",
    handler: function (target, actionContext) {
      return openDocsViewerProjectSubjectModal({
        assignFieldGroup: options.assignFieldGroup,
        fetch: options.fetch,
        readMetadata: options.readMetadata,
        restoreFocus: button,
        root: options.root,
        target: target
      }).then(function (result) {
        if (!result || result.confirmed !== true) return result;
        var refresh = actionContext && actionContext.refreshDocument;
        var refreshed = typeof refresh === "function" ? refresh(target) : Promise.resolve(target);
        return Promise.resolve(refreshed).then(function () {
          return result.payload;
        });
      });
    }
  });
  if (registration.hidden) return;
  button.className = "docsViewerReport__button docsReportDetail__iconButton docsReportDetail__assignSubject";
  button.type = "button";
  button.dataset.docsProjectsAssignSubject = "true";
  button.textContent = "Subject";
  button.disabled = !registration.enabled;
  if (registration.disabledReason) button.title = registration.disabledReason;
  button.addEventListener("click", function () {
    if (button.disabled) return;
    button.disabled = true;
    registration.invoke().catch(function (error) {
      if (typeof options.setStatus === "function") {
        options.setStatus(error && error.message ? error.message : "Subject assignment failed.", true);
      }
    }).finally(function () {
      if (button.isConnected) button.disabled = !registration.enabled;
    });
  });
  host.appendChild(button);
}

function subjectInfoField(subject) {
  if (subject.state === "valid") {
    return {
      detail: subject.key,
      id: AUTHORING_SUBJECT_GROUP_ID,
      label: "Subject",
      state: subject.kind,
      value: ({ folder: "Folder", work: "Work", series: "Series", detail: "Detail" })[subject.kind]
    };
  }
  if (subject.state === "malformed") {
    var field = subject.fields[0];
    return {
      detail: "Malformed " + field + " declaration: " + JSON.stringify(subject.evidence[field]),
      id: AUTHORING_SUBJECT_GROUP_ID,
      label: "Subject",
      state: "warning",
      value: "Authoring warning"
    };
  }
  if (subject.state === "conflicting") {
    var declarations = subject.fields.map(function (field) {
      return field + "=" + JSON.stringify(subject.evidence[field]);
    }).join(", ");
    return {
      detail: "Conflicting declarations: " + declarations,
      id: AUTHORING_SUBJECT_GROUP_ID,
      label: "Subject",
      state: "warning",
      value: "Authoring warning"
    };
  }
  return {
    detail: "",
    id: AUTHORING_SUBJECT_GROUP_ID,
    label: "Subject",
    state: "none",
    value: "None"
  };
}

function workingSubjectDetailInfo(context, assignSubjectAvailable) {
  var settings = context || {};
  var collection = exactCollection(settings.collection);
  var target = settings.target || {};
  if (
    cleanString(target.scope).toLowerCase() !== collection.scope
    || cleanString(target.sub_scope).toLowerCase() !== collection.sub_scope
    || cleanString(target.doc_id) !== cleanString(settings.document && settings.document.doc_id)
  ) {
    throw new Error("Working subject information target is invalid.");
  }
  return Object.freeze({
    actions: Object.freeze({ assignSubject: assignSubjectAvailable }),
    fields: Object.freeze([
      Object.freeze(subjectInfoField(authoringSubject(settings.document)))
    ])
  });
}

function createDocsViewerManagementWorkingSubjects(options, definition) {
  var descriptorId = cleanString(options.descriptor && options.descriptor.id);
  if (descriptorId !== definition.customisationId) {
    throw new Error("Working subject customisation identity did not match its registry entry.");
  }
  exactCollection(options.collection);
  var assignSubjectAvailable = hasDocsViewerAssignableFieldGroup(options.descriptor, AUTHORING_SUBJECT_GROUP_ID);
  var collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });
  return loadSubjectTargetTitles(options).then(function (targetLookup) {
    var contribution = {
      id: definition.customisationId,
      notify: function (event) {
        if (!event || event.type !== "mount") return;
        var reportRoot = event.root;
        if (!reportRoot || !reportRoot.dataset) {
          throw new Error("Working subject report mount root is invalid.");
        }
        reportRoot.dataset.workingSubjectColumns = "subject";
      },
      compareListDocuments: function (context) {
        return compareProjectDocuments(context, targetLookup, collator);
      },
      projectDetailInfo: function (context) {
        return workingSubjectDetailInfo(
          context,
          assignSubjectAvailable
        );
      },
      renderDetailToolbar: function (context) {
        renderAssignSubject(context, options, assignSubjectAvailable);
        renderOpenInFinder(context, options);
      },
      renderListHead: function (context) {
        renderListHead(context);
      },
      renderRow: function (context) {
        return renderWorkingSubjectRow(
          context,
          options,
          targetLookup
        );
      }
    };
    return contribution;
  });
}

export function createDocsViewerManagementSubscopeWorkingWorks(options = {}) {
  return createDocsViewerManagementWorkingSubjects(options, {
    customisationId: WORKS_CUSTOMISATION_ID
  });
}

export function createDocsViewerManagementSubscopePrePublishWorks(options = {}) {
  return createDocsViewerManagementWorkingSubjects(options, {
    customisationId: "pre_publish_works"
  });
}

export function createDocsViewerManagementSubscopeWorkingProcessing(options = {}) {
  return createDocsViewerManagementWorkingSubjects(options, {
    customisationId: PROCESSING_CUSTOMISATION_ID
  });
}
