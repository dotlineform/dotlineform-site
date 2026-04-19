---
doc_id: catalogue-new-work-link-editor
title: "New Catalogue Work Link"
last_updated: 2026-04-18
parent_id: studio
sort_order: 170
---
# New Catalogue Work Link

Route:

- `/studio/catalogue-new-work-link/`
- current work may be preselected with `?work=<work_id>`

This page creates one draft `WorkLinks` source record in `assets/studio/data/catalogue/work_links.json`.

## Current Scope

The first implementation covers:

- enter parent `work_id`
- enter `url`
- enter `label`
- create one draft work-link record through the local catalogue write service
- redirect into the focused work-link editor after create

It does not validate external link targets beyond normal field presence checks.

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Catalogue Work Link Editor](/docs/?scope=studio&doc=catalogue-work-link-editor)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
