---
doc_id: catalogue-new-work-editor
title: New Catalogue Work
last_updated: 2026-04-18
parent_id: studio
sort_order: 34
---

# New Catalogue Work

Route:

- `/studio/catalogue-new-work/`

This page creates a new canonical work source record in `assets/studio/data/catalogue/works.json`.

## Current Scope

The first implementation is draft-first:

- create a new `work_id`
- enter core draft metadata
- save the new work with `status = draft`
- keep media placement in the existing folder/filename workflow
- redirect into the main work editor after create

## Media Boundary

This page does not upload or copy media.

It only captures the source metadata fields that point at the existing media/prose conventions such as:

- `project_folder`
- `project_filename`
- `work_prose_file`

## Related References

- [Catalogue Work Editor](/docs/?scope=studio&doc=catalogue-work-editor)
- [Studio Runtime](/docs/?scope=studio&doc=studio-runtime)
- [Catalogue Write Server](/docs/?scope=studio&doc=scripts-catalogue-write-server)
- [Implementation Plan](/docs/?scope=studio&doc=new-pipeline-implementation-plan)
