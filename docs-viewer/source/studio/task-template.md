---
doc_id: task-template
title: Task Template
added_date: "2026-06-04 20:59"
last_updated: 2026-07-14
ui_status: planned
parent_id: dev-home
---
# [Task Title]

This is the specification for task [#] in [link to tasks tracker document].

Use a child task note only for an exceptional handoff inside one bounded request. If this task has an independently useful outcome or separate priority, promote it to the roadmap and give it its own request instead.

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

[update the request's named durable documentation owner; create another durable document only when it has a genuinely separate subject]

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

[to be completed during the task]

- keep only work required to complete the current request here
- move independently finishable follow-on outcomes to the roadmap

## task close

- add a handoff note to the following task.
- set the status of this task in the top section and front matter `ui_status`.
