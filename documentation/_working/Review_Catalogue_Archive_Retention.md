---
draft: false
doc_id: d-20261118-235500-32b6d9
title: Review Catalogue Archive Retention
added_date: "2026-11-18 23:50:00"
last_updated: "2026-11-18"
summary: Choose the future of the frozen Catalogue artifact and copied media before any withdrawal.
parent_id: d-20261118-235100-64ad2e
ui_status: proposed
---
# Review Catalogue Archive Retention

Decide whether the legacy Catalogue should remain publicly served, remain only as recoverable Git history, or be removed from the tracked deploy artifact. Decide retention of copied R2 media separately from HTML/JSON/runtime files.

- [ ] Review the frozen reader's present value and remaining inbound links.
- [ ] Use [Catalogue Archive](../deliveries/Catalogue_Archive.md) for behaviour, snapshot revisions, remote copy scope and local acceptance; its historical deployment/copy evidence is not a fresh remote inventory.
- [ ] Inspect the required-file entries in [site validation config](../../site-tools/config/site-tools.json), remaining runtime/data/media dependencies and an explicit recovery point before selecting withdrawal.
- [ ] Agree a concrete removal/retention set and its validation/release scope. Remote object deletion needs its own explicit authority.

The documentation cleanup changed none of `site/archive/`, configured archive media prefixes or deployment. This proposal authorises no artifact withdrawal or remote deletion.
