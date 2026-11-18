---
draft: false
doc_id: d-20260720-101826-994dd0
title: Processing
added_date: "2026-07-20 10:18:26"
last_updated: "2026-11-18"
summary: Project-owned documentation entry point, source/media boundaries and explicit website handoff.
parent_id: ""

---
# Processing

This folder owns documentation for the separate Java/Processing project. Its source sketchbook lives under [processing/](../../processing/); the website workflow does not own its build, test or render lifecycle.

## Current Project Owners

| Question | Owner |
| --- | --- |
| How is the sketchbook arranged and run? | [Project README](../../processing/README.md) |
| How does InkEngine load presets and export? | [InkEngine README](../../processing/projects/InkEngine/README.md) and its source |
| Where are recovered experiments? | [processing/recovered](../../processing/recovered/) |
| Why were source, presets and external masters separated? | [Setup and design record](Project_Setup.md) |

The current project READMEs record Processing/Java mode and pinned ControlP5 requirements. The setup record preserves incorporation, rendering/preset ideas and recovery evidence; its incomplete sequence and old scope terminology are dated material.

## Project Media And Website Handoff

Work media and print masters belong beneath `$DOTLINEFORM_PROJECTS_BASE_DIR/processing/<project-id>/`. A GUI sketch receives its external base through its explicit ignored project-local configuration. InkEngine's [example](../../processing/projects/InkEngine/output-config.example.json) has `projects_base_dir` and exact `project_id: ink-engine`; [OutputWorkspace.java](../../processing/projects/InkEngine/OutputWorkspace.java) owns validation and confined output. Missing/unavailable configuration fails visibly with no sketch/repository fallback.

Tracked sketch assets and presets remain project source. External generated artwork has its own storage/recovery needs; retiring repository preview copies did not establish a backup or byte-equivalence guarantee.

A Catalogue Work can select the pipeline's `processing` media-source identity. Studio owns the exact Work selection and required media preparation, Refresh prepares Working output, Regenerate adopts Catalogue documents and Publish transfers completed selections. [Media-source configuration](../reference/Catalogue_Media_Pipeline_Config.md#work-media-sources) · [Catalogue workflow](../reference/Catalogue_Save_And_Refresh.md)

Docs source and managed attachments use their own configured Docs workspace and explicit collection ownership. The current workspace registry has no Processing collection; the former scope/Copy to Analysis/public-document-location instructions are retired. This does not change the separate Processing project or its media root. The [instruction naming follow-up](../_working/Documentation_Code_Follow_Ups.md#code-and-file-follow-ups) remains open.

## Review Boundary

Use project-owned requirements and agreed evidence when changing a sketch, helper or export. This documentation move ran no Processing compile, Java check, GUI export or media operation. Website test profiles and release commands do not become Processing lifecycle requirements.
