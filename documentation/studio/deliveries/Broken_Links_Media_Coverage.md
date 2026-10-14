---
draft: false
doc_id: d-20261014-163056-5b71c2
title: Broken Links Media Coverage
added_date: "2026-10-14 16:30:56"
last_updated: "2026-10-14 16:30:56"
parent_id: d-20260428-000000-f5ff18
---
# Broken Links Media Coverage

Parent: [Planned Features](../Planned_Features.md). Durable owner: [Broken Links Script](../Broken_Links_Script.md). The user approved this report extension and bounded optimisation on 2026-10-14 after Rebuild correctly rejected eleven missing Context attachments whose source references remained.

## Agreed Result

Broken Links diagnoses missing registered Docs-owned images, SVGs, attachments, HTML media and assigned thumbnails across ordinary documents and configured collections, including drafts. The server reads configured local sources and generated destinations, performs diagnosis and saves one completed report. The browser owns sorting, presentation and exact correction links. Rebuild, document sources, media bytes and the saved report are outside this implementation's write boundary.

Carry one resolved workspace through Refresh, read each source once, share parsed metadata/tokens with reference extraction, and reuse each distinct media/document/Catalogue target result only during the scan. Remove unrelated authoring/model validation, repeated output validation, duplicate server sorting and unnecessary browser table reconstruction. Preserve existing document/Catalogue diagnosis, shared owner-local media matching, parsing, identity, confinement and safe saved-report reads. No source cleanup, remote crawl, persistent cache, automatic refresh, compatibility alias or test migration is included.

## Completion Gates

- [x] Readiness: confirmed the source, audit, saved-report and browser owners and the report's missing-media gap; user approved the bounded change set.
- [x] Implement local media findings and scan input/result reuse, including source diagnosis when generated HTML is unavailable.
- [x] Complete focused lint, Python compilation and the existing read-only CLI audit; its current Working result contains exactly the eleven reported missing attachments and no unavailable generated sources.
- [x] Complete distinct code review, including the mandatory Redundancy And Defensive Behavior Review: preserved shared media matching and existing Catalogue diagnosis, confirmed both audit callers carry configuration, removed the remaining source existence preflight and unused parent-map construction, and retained parsing/identity/confinement/saved-read safety. Affected lint, compilation and the final read-only audit passed; durable findings and evidence limits are recorded in the report owner.
- [x] Update durable report documentation and guardrails; no changed file belongs to the public projection inventory.
- [ ] User manual acceptance after restarting the local service, force-reloading Docs Viewer and selecting Broken Links Refresh: check missing-media rows and correction links, sorting, retained rows during Refresh and failed-refresh feedback.

Existing Broken Links tests use retired scope/workspace contracts and remain untouched and unrun under [Test Contract Discipline](../Test_Contract_Discipline.md). The CLI evidence exercises current local diagnosis without writing a report, document, media, Search or publication output. Saved Refresh persistence, failure branches and browser presentation remain manual evidence gates.
