---
doc_id: "_tmp"
title: tmp
added_date: 2026-05-20
last_updated: "2026-05-20 19:37"
parent_id: ""
sort_order: 40000
viewable: false
---
# tmp

we are working on _docs/site-request-studio-source-tree-reorganization.md
please review the spec and suggest areas for clarification

the essential purpose of this is:

in simple terms, i want the studio files to be physically located under a repo folder studio/.
by studio, I mean:
- the canonical data for the website
- the workflows and editors that manage that data
- all studio config
- the studio front end
- the studio servers and services
- all studio assets including css

this means that the rest of the repo is purely what is needed to publish the site using GitHub Pages and Jekyll.

so, if you were visiting the repo, you would see all the infrastructure you would expect to see for a GitHub Jekyll site, but you wouldn't know how the data got there. you just see the layouts, the javascript that reads the json into the pages, the site css and assets like thumbnails.

to understand where the data actually comes from, and the infrastructure to maintain it, you would need to look into studio/.

in a real sense, this is 'shuffling files around'. but conceptually, it is completely separating studio from the Jekyll site. Studio generates the published data, but it does not hold it, the site does.

---

normal development should use:

- `bin/local-studio` for Studio
- `bin/public-site-preview` for public Jekyll preview
- `bin/public-site-preview --livereload`



---

<https://developers.openai.com/codex/migrate?utm_campaign=ML_MIX_GWT_AW_codexnewsletter_OF_EX_MAY_18&utm_content=utm_content&utm_medium=email&utm_source=sendgrid&utm_term=utm_term>

<https://developers.openai.com/codex/skills>

---