---
draft: false
doc_id: d-20261015-184043-a2c9f7
title: Default Document Configuration
added_date: "2026-10-15 18:40:43"
last_updated: "2026-10-15"
parent_id: d-20260428-000000-f5ff18
---
# Default Document Configuration

Parent: [Planned Features](../Planned_Features.md). Durable owner: [Configuration And Extension Points](../Configuration_And_Extension_Points.md#workspace-and-target-contracts). The user approved this cleanup on 2026-10-15 and confirmed that the existing default is correct, public and intended to remain.

## Agreed Result

One top-level `default_doc_id` in `docs-workspace.json` configures local and public readers, retaining `d-20260426-164043-e14f49`. Workspace schema v8 removes the Working/Preview default settings without aliases or migration. The config-only projector writes both canonical browser JSON files; site-code-update retains ownership of the public site's copy. Public configuration is removed from the Incremental Document Publish queue proposal.

Retire the Settings menu/modal, action definition, client/workflow/callbacks, dedicated server routes/capabilities/service and unused styles/icon. Remove deletion-time default clearing and browser-config projection; Delete retains its exact document/Index/Selected/Links work and completion reporting. Configuration changes are explicit maintainer actions. No new default-membership audit, delete restriction, repair, recovery or publication-time configuration work is introduced.

The browser consumes its configured default at boot and has no authoring control or committed-default callback. Python resolves the single setting and projects its existing browser-safe forms; ordinary server operations do not edit it. Existing full/CLI builds retain their local browser projection owner.

## Completion Gates

- [x] Readiness and approval: traced configuration loading, local/public projection, Settings UI/API/capabilities and Delete's configuration mutation. The user approved the complete cleanup and preservation of the current ID.
- [x] Implement the single setting and config-only projection command, remove Settings and deletion-time config mutation, and reconcile durable docs and the proposed Publish queue.
- [x] Focused verification: lint passed for nine Python and ten JavaScript owners, with affected-owner reruns after removing unused Settings helpers; Python compilation passed. Config-projector, Docs service and document-builder help/import diagnostics passed. The config-only projection reported both canonical JSON files unchanged. The inventory copied only the shared app runtime's seven removed default-edit lines into site; code-update check and site validation passed, as did whitespace and active-reference review.
- [x] Distinct code review, including the mandatory Redundancy And Defensive Behavior Review, completed with no unresolved production findings. Removed the stale Delete default-clear warning/helper and the unused configured-default accessor; corrected configuration-owner documentation and marked historical Settings/default-clear evidence superseded.
- [ ] User manual acceptance after restarting Docs Viewer and force reloading local/public-preview readers: the Settings action is absent, other workspace actions remain available and the same configured document opens from the home/default route. No destructive deletion check is requested or needed for this document.

Verification budget: focused static checks and direct production config/CLI diagnostics are expected to take seconds to a few minutes, without a server/browser or network. The config-only command may update only its two tracked canonical JSON files; site-code-update may update inventory-owned tracked projection files. Site validation reads the deploy artifact. No document/media/Search generation, authoring mutation, Publish, deployment or test work is included. Existing Settings tests and old workspace fixtures remain unreviewed retirement residue under [Test Contract Discipline](../Test_Contract_Discipline.md); they are not changed or run.

## Review And Closeout

Implemented and reviewed; awaiting user manual acceptance. Retain this delivery and its Planned Features link through that gate; the durable owner contains current editing/projection instructions and evidence limits. Incremental Document Publish remains proposed and unimplemented.

The mandatory review traced the single parsed default into both stage records and the existing browser projections, changed/unchanged config writes, removed UI/action/modal/client/service/capability paths, and normal/partial Delete through its carried inputs and exact generation. Configuration loads retain strict schema/identifier parsing and existing configured-root/path/symlink authority. The projector retains positive browser-safe field selection and its existing unchanged-text comparison to avoid unnecessary tracked writes. Delete retains request/target authority, exact source confinement and required generation/completed-effect reporting. Those safeguards stay with their existing owners; no document membership audit, eligibility scan, fallback configuration, compatibility alias, automatic repair or extra authoring/recovery work was added. The config-only command loads once and writes only the two canonical browser projections; the existing inventory remains the sole site-copy owner.

Selected evidence: explicit nine-file `bin/lint-python` and ten-file `bin/lint-js` selections, nine-file `python3 -m py_compile`, config-projector/service/document-builder `--help`, one `python3 docs-viewer/build/build_browser_config.py`, `bin/site-code-update`, exact projected-file diff inspection, `bin/site-code-update --check`, `bin/site-validate`, and `git diff --check`. The four inspected configuration JSON files carry the preserved document ID; the source contains one default setting. Source/reference review found no active Settings endpoint, action, module import, default-mutation callback or deletion-time config write.

No tests, fixtures, harnesses or profiles were changed or run. No browser, service restart, live authoring/Delete, document/media/Search build, Publish, external workspace write, Preview mutation, deployment, commit or push was performed. Public/browser configuration bytes are unchanged; the one tracked site-runtime delta removes retired editing callbacks. Existing Settings/capability/stage test references remain separately scoped work, as recorded by the durable owner.
