---
draft: false
doc_id: d-20261007-212748-6b92a3
title: Rebuild Displayed Document Delivery
added_date: "2026-10-07 21:27:48"
last_updated: "2026-10-07 21:27:48"
summary: Rebuild and reload the exact displayed Working document without a source edit, Search rebuild or media production.
ui_status: active
parent_id: d-20260428-000000-f5ff18
---
# Rebuild Displayed Document Delivery

Status: implemented and reviewed on 2026-10-07, awaiting user manual menu/reload acceptance, parented to [Planned Features](../Planned_Features.md). This delivers the follow-on identified in [Catalogue Documents And Metadata](../Catalogue_Documents_And_Metadata.md#follow-on).

## Requirements And Deliverables

- Add **Rebuild** to the local **Edit doc** menu for the exact displayed ordinary or named-collection document, including Catalogue. Reuse the existing refresh icon and menu availability rules; Source, loading, invalid and busy views retain their existing unavailable Edit state.
- Send only `{doc_id}` or `{collection, doc_id}` to a dedicated document rebuild service operation. Resolve the existing confined source target, require Working authoring capability and invoke the existing targeted ordinary or collection builder.
- Refresh the document's static Related links and rendered image tokens/captions/metadata/dimensions from current saved source and generated inputs. Preserve source bytes and dates. Actual media generation, Catalogue Refresh, Search, Publish and neighbouring document rendering retain their existing owners.
- Keep the operation busy through the awaited build and fresh reload of the same exact target, replacing the current history entry. A failed build or reload reports its error through the existing management status.
- Ensure an explicit forced reader load reads a fresh payload rather than restoring retained content. Ordinary navigation and Back/Forward continue using their retained records.

## Process

Open a rendered document, choose **Edit doc → Rebuild**, and wait for the current document to reload. No source edit or confirmation is needed. The existing workspace-wide **Rebuild docs and Search** action retains its scope. Restart the Docs Viewer service after implementation and hard-refresh the local reader to adopt the new operation.

## Delivery Steps

### RD-0 Readiness

- [x] Confirm the displayed exact target, Edit menu owner, targeted build helpers and local service route authority.
- [x] Confirm source-preserving document-only scope and existing menu/busy/error behavior.

Record: ready and implementation authorized. Targeted builders already accept exact document IDs and retain incremental Links maintenance. The existing `/docs/rebuild` handler is workspace-wide. Review found forced loads could still restore retained content; the fresh-reload correction belongs to this delivery and touches the existing shared/public route workflow.

### RD-1 Implementation And Evidence

- [x] Add the menu/client/controller action and exact-target service handler.
- [x] Reuse targeted builders and propagate forced fresh reading through the shared route workflow.
- [x] Update durable documentation and perform selected verification.

Verification budget: changed-source Python/JavaScript lint, Python syntax, direct service-dispatch builds for one real ordinary document, Works Context document `d-20260801-073846-e0a9ec` and Catalogue `00008`, bounded source/diff review and whitespace checks. Direct builds write their selected Working payloads and affected indexes/Links through existing owners; source and Search checks use ordinary file hashes. Expected command cost is seconds, with exact build duration unmeasured. Project the changed shared route module through `bin/site-code-update`, inspect its tracked delta, then run projection and site validation. No automated tests, temporary regression scripts, fixtures or browser automation are authorized; menu interaction, busy presentation and browser reload remain user manual checks.

Gate: resolve implementation/static failures within the displayed-document boundary. Do not expand into media generation, full collection/Workspace Build, Search, publication or test work.

Record: changed-source Python lint/syntax and JavaScript lint passed. Fresh-process production service dispatch rebuilt ordinary document `d-20260810-222148-99daec`, Works Context document `d-20260801-073846-e0a9ec` and Catalogue `00008`; each returned status 200, the exact requested target, targeted build scope, no Search build and zero warnings. All three were already current, so the builders wrote no changed document payloads. Before/after source and Search file hashes matched. `bin/site-code-update` projected only the shared route workflow; its exact tracked delta was reviewed, and `bin/site-code-update --check` and `bin/site-validate` passed. Repo and new-file whitespace checks passed. These operations exercised real build dispatch rather than live HTTP transport or browser interaction.

### RD-2 Code Review

- [x] Review exact source/route identity, capability and field validation, source/date preservation, targeted scope, awaited completion, fresh payload reads, history behavior and public isolation.
- [x] Resolve findings and rerun only affected checks.

Gate: no material finding in the bounded final diff; report the remaining manual and failure-scenario evidence limits.

Record: bounded review found no outstanding material issue. The forced-load correction bypasses retained content only when explicitly requested; ordinary navigation and Back/Forward retain their existing behavior. Missing-source, rejected-target and build/reload failure paths were inspected but not executed. Menu dispatch, busy presentation, browser history and fresh browser payload rendering remain manual checks.

### RD-3 Closeout

- [x] Update Runtime, Related Links, the original follow-on and Planned Features with delivered behavior and current state.
- [x] Record implementation/review evidence and the pending user manual outcome.

Gate: code, documentation and selected evidence complete; local menu/reload acceptance remains with the user. Publish, deployment and Git actions remain separate. Retain this delivery for manual acceptance and recent-work lookup; no document deletion is proposed.

Record: Runtime and Related Links own the durable behavior; the Catalogue follow-on and Planned Features link this delivery. Restart the Docs Viewer service and hard-refresh the local reader before manual review. No service restart, automated test, browser check, Publish, commit or push was performed.
