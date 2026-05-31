---
doc_id: risks
title: risks
added_date: 2026-05-31
last_updated: 2026-05-31
ui_status: draft
---





---

We need to bring repo context into this because it changes the priorities of the risk definitions themselves. 'change' and 'complexity' are also linked to the purpose of the repo modules themselves.

we also need to be clear that the risk categories are observable indicators, not the actual risks. the risks are:

## risks

- the system will actually break in a significant way
- the breakages might be a single effect or a cumulation of lots of little things
- it will be hard to fix without major effort / refactor
- the system is hard to maintain - it takes too long to work out how it works so it doesn't get maintained which increases the risk of failure
- development strategy is causing a csacade of increasing risks because the fundamental design is wrong or no longer suitable for the current apps.

examples:
- css is too tangled and unstructured, changing one thing breaks another and it is hard to see cause and effect chains.
- backup, var/ files or logs build up over time because they are not manually checked, it is forgotten why they were being generated in the first place, it is not obvious that this is happening
- code is literally too long which makes it costly and inefficient to navigate/search both for humans (time, context switching) and AI (token cost, context switching), which consequently introduces errors, missed changes or opportunities for improvement.
- relying on Jekyll/Ruby for specific libraries because it was originally a design convenience decision to use them, not because it was the best or strategic. it is no longer appropriate, possibly a real blocker to future work, but downstream refactoring effort is now significant.

## risk indicators

let's consolidate. maintenance has some good questions and indicators but these need to be homed under the other categories.

front-end:
- architectural - are the methodology and frameworks introducing risk? are high level design decisions needed? is the architecture stable, has a planned strategy?
- structural - this includes: ownbership boundaries, consistency, code organisation and structure, UI design. does it all fit together effectively? is the current structure introducing risk?
- performance - this is both visible and invisible. if performance is bad but not noticed, that can hide deeper problems.

backend:
- architectural
- structural
- workflow - backend specific
- performance

## repo/app context

repo context:
- what are the fundamental purposes of the repo and the apps within it?
- how important are the risk categories to each app?
- what does change/complexity mean for each app?

### 1. Public Site 

Purpose: A catalogue of art work and text.
Host: GitHub Pages

Key drivers:
- performance / payloads: very important because it is a public site, media heavy, elegant UI. Needs to be responsive and fast.
- architecture: Static site. Jekyll is now a blocker/inconvenience, it is now largely only serving route stubs.
- structure and taxonomy: fairly complex but very stable, unlikely to change significantly. additional features very rare.
- data volumes: new records are <100/month. total records measured in 100's or low 1000's across the schema

### 2. Studio

Purpose: manage the data that is published on the public site.
Host: Local server.
Key drivers:
- performance / payloads: running locally hides most performance problems. not a priority to improve because it won't be especially noticeable. most performance gains have been at dev level e.g. ensuring that local Jekyll is decoupled from dev servers.
- architecture: moving towards a JS app, having come from a large and unmanaged code base.
- structure and taxonomy: constantly growing in complexity but relatively bounded now that docs viewer and analytics modules have been decoupled.
- data volumes: same as public site.

### 3. Analytics

Purpose: manage analytical dimensions layered on top of the catalogue data and provide analytical tools and resources.
Host: Local server.
Key drivers:
- performance / payloads: same as studio.
- architecture: moving towards a JS app, having come from a large and unmanaged code base.
- structure and taxonomy: constantly growing in complexity. significant future work likely, including integration with 3rd party data visualisation libraries, data sharing with LLMs.
- data volumes: same as public site.

### 4. Docs Viewer

Purpose: manage text/media documents for publishing on public site. Increasing support to Analytics app (e.g. data sharing, displaying analytical data).
Host: Local server.
Key drivers:
- performance / payloads: same local server considerations as Studio, but performance is more noticable and important because it gets significantly more frequent user interaction. The read-only docs viewer installs are on the public site and consequently performance/optimisation of the front-end javascript is a key priority.
- architecture: moving towards a JS app, having come from a large and unmanaged code base.
- structure and taxonomy: constantly growing in complexity. UI under constant refinement. significant future work likely, including integration via Analytics app for data visualisation and data sharing with LLMs.
- data volumes: low. documents total <1000.

## next steps

- studio-risk-analysis-policy.md needs to reflect the updated risk mitigation categories
- studio-risk-priority-dashboard.md needs reviewing in light of the categories and repo context
- inventories need to be redesigned and separated so that each app has it's own inventory and consequent priority actions.