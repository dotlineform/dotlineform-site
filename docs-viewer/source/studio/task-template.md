---
doc_id: task-template
title: Task Template
added_date: "2026-06-04 20:59"
last_updated: "2026-06-04 20:59"
ui_status: planned
parent_id: dev-home
---
# [Task Title]

This is the specification for task [#] in [link to tasks tracker document].

Status: `planned` | `in progress` | `done` | `deferred`

## Steer for this task

- this is written as a handoff note from the previous task.
- bullet points stating:
    - what concerns or risks need to be addressed
    - what technical details are important to be considered
    - relationship to previous / next tasks

## Purpose

- state the aims and purpose of this task

## Deliverables

[any deliverables that need ongoing revision or should become part of durable documentation should be created as sibling documents that are linked to from this document]

- state the expected deliverables:
    - changed or new functionality
    - changed or new scripts, config, setup files
    - documentation

## Implementation and policy guidance

- explain the key drivers from the parent request specification that are relevant to this task:
    - expected design
    - how it should be implemented
    - what policies it must adhere to
- if guidance has already been provided in a previous task, include a brief summary here and link to the previous task.

## Proposed verification set

- list any specific verification or testing needed for this task
- to be run only when the touched area warrants it.

## completed verification

- list what was completed

## follow-on tasks

[to be conmpleted during the task]

- list any follow-on tasks that need to be created
- list any issues that were found during this task which need to be addressed

## task close

- add a handoff note to the following task.
- set the status of this task in the top section and front matter `ui_status`.