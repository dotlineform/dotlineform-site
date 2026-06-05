---
doc_id: task-batch-template
title: Task Batch Template
added_date: "2026-06-05 10:36"
last_updated: "2026-06-05 10:36"
ui_status: planned
parent_id: dev-home
---
# [Batch Title]

This is the delivery specification for Batch [#] in [link to tasks tracker document].

[include the task batch table here. Task rows use scoped IDs such as 1.1, 1.2 ...]

example:

### Batch [#]: [Batch title]

Summary: [one-line summary of batch]

| ID | status | action |
| --- | --- | --- |
| 1.1 | planned | description |
| 1.2 | planned | description |

## Steer for these tasks

- this is written as a handoff note from the previous task.
- bullet points stating:
    - what concerns or risks need to be addressed
    - what technical details are important to be considered
    - relationship to previous / next tasks

## Deliverables

[any deliverables that need ongoing revision or should become part of durable documentation should be created as sibling documents that are linked  from this document]

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

- add a handoff note to the following batch.
- set the status of this batch in the top section and front matter `ui_status`.
